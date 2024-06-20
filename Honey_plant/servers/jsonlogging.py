import logging
import logging.handlers
import os


class JsonExtraFormatter(logging.Formatter):

    def __init__(self, fmt=None, datefmt=None, style='%', validate=True):
        super().__init__(fmt, datefmt, style, validate)

    def format(self, record: logging.LogRecord) -> str:
        default_attrs = logging.LogRecord(None, None, None, None, None, None, None).__dict__.keys()
        extras_dict = dict()

        # If using RotatingFileHandler, delete these two attributes that are implicitly added to the record dictionary
        if record.__dict__.__contains__('message'):
            record.__dict__.pop('message')
        if record.__dict__.__contains__('asctime'):
            record.__dict__.pop('asctime')

        for key, value in record.__dict__.items():
            if not default_attrs.__contains__(key):
                extras_dict.update({key: value})

        log_items = ['"timestamp":"%(asctime)s"', '"message": "%(message)s"']
        for attr, value in extras_dict.items():
            log_items += self.jsonParser(attr, value)

        format_str = f'{{{", ".join(log_items)}}},'
        self._style._fmt = format_str
        self.datefmt = '%d-%m-%Y %H:%M:%S'

        return super().format(record)

    def jsonParser(self, attr: str, value: object):
        res = []

        if isinstance(value, str):
            res.append(f'"{attr}": "{value}"')

        elif isinstance(value, dict):
            values_str = ""

            for k, v in value.items():
                values_str += "".join(val for val in self.jsonParser(k, v)) + ", "
            values_str = values_str[0:len(values_str) - 2]

            res.append(f'"{attr}": {{{values_str}}}')

        elif isinstance(value, bytes):
            value = str(value).replace("\\", "\\\\")
            res.append(f'"{attr}": "{value}"')

        else:
            res.append(f'"{attr}": {value}')

        return res


class JsonRotatingFileHandler(logging.handlers.RotatingFileHandler):

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None, delay=False, errors=None):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay, errors)

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering for rollover as described
        in doRollover().
        """
        try:
            # If is the first log created, we add the json list at the beginning
            if self.stream.tell() == 0:
                self.stream.write("{\"data\":[\n")
                self.stream.flush()
            # If it is not the first, but max file size has been reached, we edit format at the end of the current file
            # and add the json list at the beginning of the new file
            if self.shouldRollover(record):
                # Edit end of file (delete comma after last element of the list and add list and curly brace closure)
                with open(self.baseFilename, 'rb+') as fh:
                    fh.seek(-2, 2)
                    fh.truncate()
                    fh.close()
                self.stream.write("\n]}")
                self.stream.flush()

                # Do rollover (change file) and add json list at the beginning
                self.doRollover()
                self.stream.write("{\"data\":[\n")
                self.stream.flush()

            logging.FileHandler.emit(self, record)
        except Exception:
            self.handleError(record)

    def doRollover(self):
        """
        Do a rollover, as described in __init__(). CUSTOMIZED to keep .json extension
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(self.baseFilename.replace(".", "%d." % i))
                dfn = self.rotation_filename(self.baseFilename.replace(".", "%d." % (i + 1)))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(self.baseFilename.replace(".", "1."))
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()


class JsonFileLogger(logging.Logger):

    def __init__(self, name: str):
        super().__init__(name)

        jsonRotatingFileHandler = JsonRotatingFileHandler(filename='logs/Logs.json', backupCount=3,
                                                          maxBytes=10 * 1024, delay=False)
        extraFormatter = JsonExtraFormatter()
        jsonRotatingFileHandler.setFormatter(extraFormatter)
        self.addHandler(jsonRotatingFileHandler)

        self.propagate = False
        self.setLevel(logging.DEBUG)

