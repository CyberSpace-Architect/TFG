import logging
import os


class ColorHandler(logging.StreamHandler):

    def emit(self, record):
        # https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
        GRAY8 = "38;5;8"
        GRAY7 = "38;5;7"
        ORANGE = "33"
        RED = "31"
        WHITE = "0"

        # White is not used for any logging, to help distinguish from user print statements
        level_color_map = {
            logging.DEBUG: GRAY8,
            logging.INFO: GRAY7,
            logging.WARNING: ORANGE,
            logging.ERROR: RED,
        }

        csi = f"{chr(27)}["  # control sequence introducer
        color = level_color_map.get(record.levelno, WHITE)

        self.stream.write(f"{csi}{color}m{record.msg}{csi}m\n")


class CustomLogger:

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)

        if not os.environ.get("NO_COLOR"):
            self.logger.addHandler(ColorHandler())
        else:
            self.logger.error(f'Custom colors not available for this OS, check https://no-color.org/')
