import argparse
import time
import queue

from keystroke_transcriber import constants as const
from keystroke_transcriber.recorder import KeystrokeRecorder
from keystroke_transcriber.output_writer import PlaybackType

# Output writers for target types
from keystroke_transcriber.output_writers.digispark import DigisparkOutputWriter


class KeystrokeTranscriber(object):
    def __init__(self, playback_type, repeat_count=0, repeat_delay_ms=0, maintain_timing=False,
                 translate_scan_codes=True, event_delay_ms=0, output_writer_class=DigisparkOutputWriter):
        self.playback_type = playback_type
        self.repeat_count = repeat_count
        self.repeat_delay_ms = repeat_delay_ms
        self.maintain_timing = maintain_timing
        self.translate_scan_codes = translate_scan_codes
        self.event_delay_ms = event_delay_ms

        self.recorder = KeystrokeRecorder()
        self.writer = output_writer_class()

    def _process_events(self, events):
        return self.writer.generate_output(events, self.playback_type, repeat_count=self.repeat_count,
                                           repeat_delay_ms=self.repeat_delay_ms, maintain_timing=self.maintain_timing,
                                           translate_scan_codes=self.translate_scan_codes,
                                           event_delay_ms=self.event_delay_ms)

    def _log_keypresses(self, time_s=None):
        start_time_event = None
        start_time_system = time.time()

        ret = []

        try:
            while True:
                if time_s is not None:
                    if (time.time() - start_time_system) >= time_s:
                        # Timeout expired
                        return ret

                try:
                    e = self.recorder.wait_for_next_keypress(False, 0.05)
                except queue.Empty:
                    continue

                ret.append(e)

                if start_time_event is None:
                    start_time_event = e.time

                secs_elapsed = e.time - start_time_event

                print("'%s' %s (scan_code=%d, milliseconds=%d)" %
                      (e.name, "pressed" if e.event_type is "down" else "released",
                  e.scan_code, int(secs_elapsed * 1000)))
        except KeyboardInterrupt:
            pass

        return ret

    def _record_until_ctrlc(self, log_keypresses=True):
        print("Recording keyboard events (Press Ctrl-C to stop recording) ...")
        print()

        self.recorder.start()

        recorded_events = []

        if log_keypresses:
            recorded_events = self._log_keypresses()
        else:
            try:
                while True:
                    time.sleep(0.01)
            except KeyboardInterrupt:
                self.recorder.stop()

            recorded_events = self.recorder.events

        throw_away_last = 2
        i = (len(recorded_events) - 1 - 4) if (len(recorded_events) >= 4) else 0
        start_i = i

        # Look for ctrl down followed by C down, throw away everything after and including that
        while True:
            e = recorded_events[i]
            if e.name.startswith('ctrl') and (e.event_type == 'down'):
                if (i < (len(recorded_events) - 1)):
                    next_event = recorded_events[i + 1]
                    if (next_event.name.lower() == "c") and (next_event.event_type == 'down'):
                        throw_away_last = len(recorded_events) - i
                        break

            i += 1

        return recorded_events[:-throw_away_last] # Last 2-4 events are Ctrl-C

    def _record_fixed_time(self, time_s, log_keypresses=True):
        print("Recording keyboard events for %.2f seconds ..." % time_s)
        print()

        self.recorder.start()

        recorded_events = []

        if log_keypresses:
            recorded_events = self._log_keypresses(time_s)
        else:
            try:
                time.sleep(time_s)
            except KeyboardInterrupt:
                self.recorder.stop()

            recorded_events = self.recorder.events

        return recorded_events

    def transcribe_until_ctrlc(self, log_keypresses=True):
        return self._process_events(self._record_until_ctrlc(log_keypresses))

    def transcribe_until_time_elapsed(self, seconds, log_keypresses=True):
        return self._process_events(self._record_fixed_time(seconds, log_keypresses))


playback_type_map = {
    'oneshot': PlaybackType.ONE_SHOT,
    'repeat-forever': PlaybackType.REPEAT_FOREVER,
    'repeat-n': PlaybackType.REPEAT_N
}

target_type_map = {
    'digispark' : DigisparkOutputWriter
}

parser = argparse.ArgumentParser(prog='keystroke_transcriber',
                                 description=const.PROGRAM_DESC,
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-p', '--playback-type', help="Set the playback style for recorded keystroke sequences", type=str,
                    dest='playback_type', choices=list(playback_type_map.keys()), default='oneshot')

parser.add_argument('-t', '--target-type', help="Set the type of programmable USB HID device to generate output for",
                    type=str, dest='target_type', choices=list(target_type_map.keys()), default='digispark')

parser.add_argument('-o', '--output-file', help="Write output to this file, instead of printing output to the terminal", type=str,
                    dest='output_file', default=None)

parser.add_argument('-n', '--repeat-count', help=("Sets how many times the recorded keystroke sequence should be repeated "
                    "(only used if --playback-type is repeat-n)"), type=int, dest='repeat_count', default=1)

parser.add_argument('-D', '--repeat-delay-ms', help=("Sets delay between recorded keystroke sequence repetitions, in milliseconds "
                    "(only used if --playback-type is repeat-n or repeat-forever)"), type=int, dest='repeat_delay_ms', default=0)

parser.add_argument('-d', '--event-delay-ms', help=("Sets delay between individual keystroke events, in milliseconds "
                    "(only used if --maintain-timing is False)"), type=int, dest='event_delay_ms', default=0)

parser.add_argument('-m', '--maintain-timing', help="Maintain timing between recorded keystrokes", action='store_true',
                    dest='maintain_timing', default=False)

parser.add_argument('-r', '--record-seconds', help="Record for this many seconds, instead of recording until Ctrl-C is seen",
                    dest='record_seconds', type=float, default=None)

parser.add_argument('-s', '--translate-scan-codes', help="Attempt to translate PS/2 scan codes to USB HID usage ID codes",
                    action='store_true', dest='translate_scan_codes', default=True)

parser.add_argument('-q', '--quiet-keypresses', help="Don't print detected keypresses to the terminal", action='store_true',
                    dest='quiet_keypresses', default=False)

def main():
    args = parser.parse_args()

    writer_class = target_type_map[args.target_type]

    t = KeystrokeTranscriber(playback_type_map[args.playback_type], repeat_count=args.repeat_count,
                             repeat_delay_ms=args.repeat_delay_ms, maintain_timing=args.maintain_timing,
                             translate_scan_codes=args.translate_scan_codes,
                             event_delay_ms=args.event_delay_ms, output_writer_class=writer_class)

    if args.record_seconds is None:
        output = t.transcribe_until_ctrlc(not args.quiet_keypresses)
    else:
        output = t.transcribe_until_time_elapsed(args.record_seconds, not args.quiet_keypresses)

    if args.output_file is None:
        print()
        print(output)
    else:
        with open(args.output_file, 'w') as fh:
            fh.write(output)

        print("Output written to %s" % args.output_file)

if __name__ == "__main__":
    main()
