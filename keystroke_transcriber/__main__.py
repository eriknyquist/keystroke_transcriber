import time
from keystroke_transcriber.recorder import KeystrokeRecorder
from keystroke_transcriber.output_writers.digispark import DigisparkOutputWriter
from keystroke_transcriber.output_writer import OutputType


r = KeystrokeRecorder()
w = DigisparkOutputWriter()
r.start()
time.sleep(4)
r.stop()
print(w.generate_output(r.events, OutputType.REPEAT_N, 12, True))
