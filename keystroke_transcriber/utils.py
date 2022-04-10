from keystroke_transcriber import constants as const


def scan_code_to_usb_id(code):
    """
    Convert a PS/2 scan code into a USB HID usage ID code. If no translation is
    found for the provided scan code, then the original unchanged code will be
    returned.

    :param int code: PS/2 keyboard scan code

    :return: Equivalent USB HID usage ID code, or the same as the input if no translation is found
    :rtype: int
    """
    if code not in const.SCAN_CODE_TO_USB_ID_MAP:
        return code

    return const.SCAN_CODE_TO_USB_ID_MAP[code]


def list_to_csv_string(items, column_limit=80, indent_spaces=4):
    lines = []
    indent =  ' ' * indent_spaces

    current_line = indent

    for i in range(len(items)):
        item = items[i]
        new_text = item
        if i < (len(items) - 1):
            new_text += ', '

        if len(current_line + new_text) > column_limit:
            # reset line
            lines.append(current_line)
            current_line = indent

        current_line += new_text

    lines.append(current_line)
    return '\n'.join(lines)
