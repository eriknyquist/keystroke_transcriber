import time
from keystroke_transcriber.recorder import KeystrokeRecorder
from keystroke_transcriber.output_writers.digispark import DigisparkOutputWriter
from keystroke_transcriber.output_writer import OutputType


r = KeystrokeRecorder()
w = DigisparkOutputWriter()
r.start()
time.sleep(4)
r.stop()
print(w.generate_output(r.events, OutputType.REPEAT_N, repeat_count=12, repeat_delay_ms=1000, maintain_timing=True))
