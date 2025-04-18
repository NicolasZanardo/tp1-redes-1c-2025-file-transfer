from enum import Enum
import logging

logging.basicConfig(level = logging.INFO, format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")

class LogType(Enum):
    VERBOSE = 1,
    INFO = 2,
    ERROR = 3,

class VerbosityLevel(Enum):
    VERBOSE = 1
    NORMAL = 2
    QUIET = 3

class Colors(Enum):
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    RED = "\x1b[31m"
    PURPLE = "\x1b[35m"
    BLUE = "\x1b[34m"
    CYAN = "\x1b[36m"
    GRAY = "\033[0;37m"
    RESET = "\x1b[0m"

class Logger:

    def __init__(self, name: str, level: VerbosityLevel):
        logger = logging.Logger(name)
        if level is VerbosityLevel.QUIET:
            logger.setLevel(logging.CRITICAL)
        elif level is VerbosityLevel.VERBOSE:
            logger.setLevel(logging.DEBUG)
        self.logger = logger

    @classmethod
    def create_server_logger(cls, level: VerbosityLevel):
        return Logger('Server', level)

    @classmethod
    def create_client_logger(cls, level: VerbosityLevel):
        return Logger('Client', level)

    def log(self, message: str, color: Colors):
        return "{color} {message} {reset}".format(color=color.value, message=message, reset=Colors.RESET.value)

    def debug(self, message):
        self.logger.debug(self.log(message, Colors.GRAY))

    def error(self, message):
        self.logger.error(self.log(message, Colors.RED))

    def info(self, message):
        self.logger.info(self.log(message, Colors.BLUE))
