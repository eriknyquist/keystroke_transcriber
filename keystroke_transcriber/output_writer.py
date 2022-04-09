import keystroke_transcriber.recorder


class OutputType(object):
    ONE_SHOT = 1        # Keystroke sequence is replayed once
    REPEAT_FOREVER = 2  # Keystroke sequence is repeated forever
    REPEAT_N = 3        # Keystroke sequence is repeated a specific number of times


class OutputWriter(object):
    """
    Converts a list of keystroke events to some keystroke simulation script or code
    """
    def generate_output(self, keyboard_events, output_type, repeat_count=0, maintain_timing=False):
        """
        Process a list of keystroke events and return the result

        :param [keyboard_transcriber.recorder.KeyboardEvent] keyboard_events: list of keyboard events to process
        :param OutputType output_type: Type of output to generate
        :param int repeat_count: Number of times to repeat sequence (only used if output_type is REPEAT_N)
        :param bool maintain_timing: If True, timing between keystroke events will be maintained.\
                                     If false, events will be sent as fast as possible.

        :return: result of event processing, some script or code that simulates or injects the ketstroke events
        :rtype: str
        """
        raise NotImplementedError()
