import argparse
import time
from keystroke_transcriber.recorder import KeystrokeRecorder
from keystroke_transcriber.output_writers.digispark import DigisparkOutputWriter
from keystroke_transcriber.output_writer import PlaybackType


class KeystrokeTranscriber(object):
    def __init__(self, playback_type, repeat_count=0, repeat_delay_ms=0, maintain_timing=False,
                 translate_scan_codes=True):
        self.playback_type = playback_type
        self.repeat_count = repeat_count
        self.repeat_delay_ms = repeat_delay_ms
        self.maintain_timing = maintain_timing
        self.translate_scan_codes = translate_scan_codes

        self.recorder = KeystrokeRecorder()
        self.writer = DigisparkOutputWriter()

    def _process_events(self, events):
        return self.writer.generate_output(events, self.playback_type, repeat_count=self.repeat_count,
                                           repeat_delay_ms=self.repeat_delay_ms, maintain_timing=self.maintain_timing,
                                           translate_scan_codes=self.translate_scan_codes)

    def _record_until_ctrlc(self):
        print("Recording keyboard events (Press Ctrl-C to stop recording) ...")
        self.recorder.start()

        try:
            while True:
                time.sleep(0.01)
        except KeyboardInterrupt:
            self.recorder.stop()
            return self.recorder.events[:-2] # Last two events are Ctrl-C

    def transcribe_until_ctrlc(self):
        return self._process_events(self._record_until_ctrlc())


playback_type_map = {
    'oneshot': PlaybackType.ONE_SHOT,
    'repeat-forever': PlaybackType.REPEAT_FOREVER,
    'repeat-n': PlaybackType.REPEAT_N
}

def main():
    parser = argparse.ArgumentParser(description='Record and transcribe keyboard events into various replay formats.')

    parser.add_argument('-t', '--playback-type', help="Set the playback style for recorded keystroke sequences", type=str,
                        dest='playback_type', choices=list(playback_type_map.keys()), default='oneshot')

    parser.add_argument('-n', '--repeat-count', help="Sets the number of times to repeat sequence (only used if playback_type is repeat-n)",
                        type=int, dest='repeat_count', default=1)

    parser.add_argument('-d', '--repeat-delay-ms', help=("Sets delay between repetitions, in milliseconds "
                        "(only used if playback_type is repeat-n or repeat-forever)"), type=int, dest='repeat_delay_ms', default=0)

    parser.add_argument('-m', '--maintain-timing', help="Maintain timing between recorded keystrokes", action='store_true',
                        dest='maintain_timing', default=True)

    parser.add_argument('-s', '--translate-scan-codes', help="Attempt to translate PS/2 scan codes to USB HID usage ID codes",
                        action='store_true', dest='translate_scan_codes', default=True)

    args = parser.parse_args()

    t = KeystrokeTranscriber(playback_type_map[args.playback_type], repeat_count=args.repeat_count,
                             repeat_delay_ms=args.repeat_delay_ms, maintain_timing=args.maintain_timing,
                             translate_scan_codes=args.translate_scan_codes)

    print(t.transcribe_until_ctrlc())

if __name__ == "__main__":
    main()
