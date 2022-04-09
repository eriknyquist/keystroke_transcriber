from keystroke_transcriber.output_writer import OutputWriter, OutputType

# Generate all the alpha chars
alpha_chars = [chr(x) for x in range(ord('a'), ord('z') + 1, 1)]

# Generate all the digits
num_chars = [str(i) for i in range(10)]

# Arrow key names
arrow_names = ['up', 'down', 'left', 'right']

f_key_names = ["f%d" % i for i in range(1, 13, 1)]

key_name_map = {}

# Maps all regular (non-modifier) key names to scan code names in DigiKeyboard lib
key_name_map.update({c: "KEY_%s" % (c.upper()) for c in alpha_chars})
key_name_map.update({c: "KEY_%s" % c for c in num_chars})
key_name_map.update({n: "KEY_ARROW_%s" % n.upper() for n in arrow_names})
key_name_map.update({n: "KEY_%s" % n.upper() for n in f_key_names})
key_name_map.update({'space': 'KEY_SPACE', 'enter': 'KEY_ENTER'})

# Maps all regular (non-modifier) keynames to scan codes that are not defined in DigiKeyboard.h
key_name_map.update({
    '(': '10u',
    ')': '11u',
    '[': '26u',
    ']': '27u',
    '\\': '43u',
    ',': '51u',
    '.': '52u',
    'caps lock': '58u',
    'delete': '83u',
    'esc': '1u',
    'backspace': '14u',
})

# Maps all modifier key names to bitflag names in DigiKeyboard lib
mod_name_map = {
    'ctrl': 'MOD_CONTROL_LEFT',
    'shift': 'MOD_SHIFT_LEFT',
    'alt': 'MOD_ALT_LEFT',
    'left windows': 'MOD_GUI_LEFT',
    'right ctrl': 'MOD_CONTROL_RIGHT',
    'right shift': 'MOD_SHIFT_RIGHT',
    'right alt': 'MOD_ALT_RIGHT',
    'right windows': 'MOD_GUI_RIGHT'
}


c_template ="""
#include "DigiKeyboard.h"

#define NUM_EVENTS (%su)

struct key_event
{
    uint8_t key;
    uint8_t mods;
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

    DigiKeyboard.sendKeyPress(event->key, event->mods);
}

void replay_key_events()
{
    for (unsigned i = 0u; i < NUM_EVENTS; i++)
    {
        send_key_event(events[i]);
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

        # Keeps track of which modifier keys are pressed
        mods_pressed_map = {n: False for n in mod_name_map.values()}

        keys_down = 0
        last_event_time = 0

        for e in keyboard_events:
            print(e.to_json())
            name = e.name.lower()
            if (name not in key_name_map) and (name not in mod_name_map):
                # Unsupported key
                continue

            # If this is a modifier key, update the map that tracks which modifier
            # keys are currently being held down
            if name in mod_name_map:
                mods_pressed_map[mod_name_map[name]] = "down" == e.event_type

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
                if name in key_name_map:
                    keycode = key_name_map[name]

            # Generate string containing OR'd names of modifier keys that are currently down
            mods_pressed = [n for n in mods_pressed_map.keys() if mods_pressed_map[n]]
            if not mods_pressed:
                mods = '0'
            else:
                mods = ' | '.join(mods_pressed)

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

            event_strings.append('{%s, %s, %s}' % (keycode, mods, delay_before_ms))

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
