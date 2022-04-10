import keyboard

from keystroke_transcriber import utils
from keystroke_transcriber import constants as const
from keystroke_transcriber.utils import scan_code_to_usb_id
from keystroke_transcriber.output_writer import OutputWriter, PlaybackType


c_template = "// " + const.AUTOGEN_COMMENT_TEXT + "\n" + """
#include "DigiKeyboard.h"

#define NUM_EVENTS (%su)

struct key_event
{
    uint8_t key;
    uint8_t mods;
    uint32_t delay_before_ms;
};

const struct key_event key_events[NUM_EVENTS] PROGMEM =
{
%s
};

void send_key_event(const struct key_event *event)
{
    if (0u < event->delay_before_ms)
    {
        DigiKeyboard.delay(event->delay_before_ms);
    }

    DigiKeyboard.sendKeyPress(event->key, event->mods);
}

// Read a single key event from PROGMEM, by array index
void read_key_event_by_index(int index, struct key_event *event)
{
    event->key = pgm_read_byte_near(&key_events[index].key);
    event->mods = pgm_read_byte_near(&key_events[index].mods);
    event->delay_before_ms = pgm_read_dword_near(&key_events[index].delay_before_ms);
}

void replay_key_events()
{
    for (unsigned i = 0u; i < NUM_EVENTS; i++)
    {
        struct key_event event;
        read_key_event_by_index(i, &event);
        send_key_event(&event);
    }
}

void setup()
{
    %s
}

void loop()
{
    %s
    DigiKeyboard.update();
}
"""

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


class DigisparkOutputWriter(OutputWriter):
    """
    Converts a list of KeyboardEvent objects into a Digispark arduino sketch (.ino)
    that generates the same keypress events
    """
    def generate_output(self, keyboard_events, output_type, repeat_count=0, repeat_delay_ms=0,
                        maintain_timing=False, translate_scan_codes=True, event_delay_ms=0):
        event_strings = []

        keys_down = 0
        last_event_time = 0

        # Keeps track of which modifier keys are pressed
        mods_pressed_map = {n: False for n in mod_name_map.values()}

        for e in keyboard_events:
            name = e.name.lower()

            # If this is a modifier key, update the map that tracks which modifier
            # keys are currently being held down
            is_mod = False
            if name in mod_name_map:
                is_mod = True
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
            if keys_down > 0 and not is_mod:
                if translate_scan_codes:
                    scan_code = scan_code_to_usb_id(e.scan_code)
                else:
                    scan_code = e.scan_code

                keycode = '%du' % scan_code

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
                delay_before_ms = str(event_delay_ms) + 'u'

            last_event_time = e.time

            event_strings.append('{%s, %s, %s}' % (keycode, mods, delay_before_ms))

        event_array = utils.list_to_csv_string(event_strings)

        # Decide where to call the function which replays keyboard events,
        # based on the 'output_type' provided
        if output_type == PlaybackType.ONE_SHOT:
            setup_text = 'replay_key_events();'
            loop_text = ''

        elif output_type == PlaybackType.REPEAT_FOREVER:
            setup_text = ''
            loop_text = 'replay_key_events();'

            if repeat_delay_ms > 0:
                loop_text += ' DigiKeyboard.delay(%s);' % repeat_delay_ms

        elif output_type == PlaybackType.REPEAT_N:
            if repeat_delay_ms > 0:
                setup_text = ('for (unsigned i = 0u; i < %du; i++)'
                              '{ replay_key_events(); DigiKeyboard.delay(%s); }'
                              % (repeat_count, repeat_delay_ms))
            else:
                setup_text = 'for (unsigned i = 0u; i < %du; i++) replay_key_events();' % repeat_count

            loop_text = ''
        else:
            raise RuntimeError("Unrecognized output type (%d)" % output_type)

        return c_template % (len(event_strings), event_array, setup_text, loop_text)
