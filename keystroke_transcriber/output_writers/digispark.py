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
    %s delay_before_ms;
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

// Replay all keypress events stored in PROGMEM
void replay_key_events()
{
    for (unsigned i = 0u; i < NUM_EVENTS; i++)
    {
        struct key_event event;

        event.key = pgm_read_byte_near(&key_events[i].key);
        event.mods = pgm_read_byte_near(&key_events[i].mods);
        event.delay_before_ms = pgm_read_word_near(&key_events[i].delay_before_ms);

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
        mods_down = 0
        last_event_time = 0
        highest_delay = 0

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
                mods_down += 1 if "down" == e.event_type else -1
            else:
                keys_down += 1 if "down" == e.event_type else -1

            # Ignore key up events if no mod keys are being held down
            if (e.event_type == "up") and (mods_down == 0) and (keys_down > 0):
                continue

            keycode = '0'
            if (not is_mod) and keys_down > 0:
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
                    delay_before_ms = 0
                else:
                   delay_before_s = e.time - last_event_time
                   delay_before_ms = int(delay_before_s * 1000)
            else:
                delay_before_ms = event_delay_ms

            if delay_before_ms > highest_delay:
                highest_delay = delay_before_ms

            last_event_time = e.time

            event_strings.append('{%s, %s, %du}' % (keycode, mods, delay_before_ms))

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

        # Pick smallest possible type that can hold out highest delay value
        if highest_delay <= (2**16):
            delay_dtype = 'uint16_t'
            delay_ctype = 'word'
        else:
            delay_dtype = 'uint32_t'
            delay_ctype = 'dword'

        return c_template % (len(event_strings), delay_dtype, event_array, delay_ctype, setup_text, loop_text)
