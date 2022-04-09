from keystroke_transcriber.output_writer import OutputWriter, OutputType


c_template ="""
#include "DigiKeyboard.h"

#define NUM_EVENTS (%su)

struct key_event
{
    uint8_t key;
    unsigned long delay_before_ms;
};

struct key_event events[NUM_EVENTS] =
{
    %s
};

void send_key_event(struct key_event *event)
{
    if (0u < event->delay_before_ms)
    {
        DigiKeyboard.delay(event->delay_before_ms);
    }

    DigiKeyboard.sendKeyPress(event->key);
}

void replay_key_events()
{
    for (unsigned i = 0u; i < NUM_EVENTS; i++)
    {
        send_key_event(&events[i]);
    }
}

void setup()
{
    %s
}

void loop()
{
    %s
}
"""

class DigisparkOutputWriter(OutputWriter):
    """
    Converts a list of KeyboardEvent objects into a Digispark arduino sketch (.ino)
    that generates the same keypress events
    """
    def generate_output(self, keyboard_events, output_type, repeat_count=0, maintain_timing=False):
        event_strings = []

        keys_down = 0
        last_event_time = 0

        for e in keyboard_events:
            print(e.to_json())
            name = e.name.lower()

            # Update global counter for how many keys (both regular and modifier keys)
            # Are being held down. We do this in order to send a "release all keys"
            # event when no keys are held down any more, since the digispark keyboard
            # lib doesn't provide a way to release a specific key
            if e.event_type == "down":
                keys_down += 1
            elif e.event_type == "up":
                keys_down -= 1

                # Ignore all key up events unless it's the last key to be released
                if keys_down > 0:
                    continue
            else:
                raise RuntimeError("unrecognized event type '%s'" % e.event_type)

            keycode = '0'
            if keys_down > 0:
                keycode = '%du' % e.scan_code

            # Calculate millisecond delay time
            if maintain_timing:
                if last_event_time == 0:
                    delay_before_ms = '0u'
                else:
                   delay_before_s = e.time - last_event_time
                   delay_before_ms = str(int(delay_before_s * 1000)) + 'u'
            else:
                delay_before_ms = '0u'

            last_event_time = e.time

            event_strings.append('{%s, %s}' % (keycode, delay_before_ms))

        # Decide where to call the function which replays keyboard events,
        # based on the 'output_type' provided
        if output_type == OutputType.ONE_SHOT:
            setup_text = 'replay_key_events();'
            loop_text = ''
        elif output_type == OutputType.REPEAT_FOREVER:
            setup_text = ''
            loop_text = 'replay_key_events();'
        elif output_type == OutputType.REPEAT_N:
            setup_text = 'for (unsigned i = 0u; i < %du; i++) replay_key_events();' % repeat_count
            loop_text = ''
        else:
            raise RuntimeError("Unrecognized output type (%d)" % output_type)

        print("DOWN: " + str(keys_down))
        return c_template % (len(event_strings), ',\n    '.join(event_strings), setup_text, loop_text)
