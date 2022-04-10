import argparse
import time

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

    def _record_until_ctrlc(self):
        print("Recording keyboard events (Press Ctrl-C to stop recording) ...")
        self.recorder.start()

        try:
            while True:
                time.sleep(0.01)
        except KeyboardInterrupt:
            self.recorder.stop()
            return self.recorder.events[:-2] # Last two events are Ctrl-C

    def _record_fixed_time(self, time_s):
        print("Recording keyboard events for %.2f seconds ..." % time_s)
        self.recorder.start()

        try:
            time.sleep(time_s)
        except KeyboardInterrupt:
            self.recorder.stop()

        return self.recorder.events

    def transcribe_until_ctrlc(self):
        return self._process_events(self._record_until_ctrlc())

    def transcribe_until_time_elapsed(self, seconds):
        return self._process_events(self._record_fixed_time(seconds))


playback_type_map = {
    'oneshot': PlaybackType.ONE_SHOT,
    'repeat-forever': PlaybackType.REPEAT_FOREVER,
    'repeat-n': PlaybackType.REPEAT_N
}

target_type_map = {
    'digispark' : DigisparkOutputWriter
}

parser = argparse.ArgumentParser(description=const.PROGRAM_DESC, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-p', '--playback-type', help="Set the playback style for recorded keystroke sequences", type=str,
                    dest='playback_type', choices=list(playback_type_map.keys()), default='oneshot')

parser.add_argument('-t', '--target-type', help="Set the type of programmable USB HID device to generate output for",
                    type=str, dest='target_type', choices=list(target_type_map.keys()), default='digispark')

parser.add_argument('-o', '--output-file', help="Write output to this file, instead of printing output to the terminal", type=str,
                    dest='output_file', default=None)

parser.add_argument('-n', '--repeat-count', help="Sets the number of times to repeat sequence (only used if playback_type is repeat-n)",
                    type=int, dest='repeat_count', default=1)

parser.add_argument('-D', '--repeat-delay-ms', help=("Sets delay between repetitions, in milliseconds "
                    "(only used if playback_type is repeat-n or repeat-forever)"), type=int, dest='repeat_delay_ms', default=0)

parser.add_argument('-d', '--event-delay-ms', help=("Sets delay between individual keystroke events, in milliseconds "
                    "(only used if maintain_timing is False)"), type=int, dest='event_delay_ms', default=0)

parser.add_argument('-m', '--maintain-timing', help="Maintain timing between recorded keystrokes", action='store_true',
                    dest='maintain_timing', default=False)

parser.add_argument('-r', '--record-seconds', help="Record for this many seconds, instead of recording until Ctrl-C is seen",
                    dest='record_seconds', type=float, default=None)

parser.add_argument('-s', '--translate-scan-codes', help="Attempt to translate PS/2 scan codes to USB HID usage ID codes",
                    action='store_true', dest='translate_scan_codes', default=True)

def main():
    args = parser.parse_args()

    writer_class = target_type_map[args.target_type]

    t = KeystrokeTranscriber(playback_type_map[args.playback_type], repeat_count=args.repeat_count,
                             repeat_delay_ms=args.repeat_delay_ms, maintain_timing=args.maintain_timing,
                             translate_scan_codes=args.translate_scan_codes,
                             event_delay_ms=args.event_delay_ms, output_writer_class=writer_class)

    if args.record_seconds is None:
        output = t.transcribe_until_ctrlc()
    else:
        output = t.transcribe_until_time_elapsed(args.record_seconds)

    if args.output_file is None:
        print()
        print(output)
    else:
        with open(args.output_file, 'w') as fh:
            fh.write(output)

        print("Output written to %s" % args.output_file)

if __name__ == "__main__":
    main()
