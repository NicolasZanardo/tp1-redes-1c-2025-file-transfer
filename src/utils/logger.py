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
    BLUE = "\x1b[34m" # lighter blue
    LIGHT_BLUE = "\x1b[94m"
    CYAN = "\x1b[36m"
    GRAY = "\033[0;37m"
    RESET = "\x1b[0m"

class Logger:
    @classmethod
    def setup_name(cls, name: str):
        cls.logger = logging.getLogger(name)
        if hasattr(cls, 'verbosity'):
            cls.setup_verbosity(cls.verbosity)

    @classmethod
    def setup_verbosity(cls, level: VerbosityLevel):
        cls.verbosity = level

        if level is VerbosityLevel.QUIET:
            cls.logger.setLevel(logging.CRITICAL)
        elif level is VerbosityLevel.VERBOSE:
            cls.logger.setLevel(logging.DEBUG)
        else:
            cls.logger.setLevel(logging.INFO)
    
    @classmethod
    def debug(cls, message, who=None):
        if who:
            message = f"FROM {who}: {message}"
        cls.logger.debug(format_message(message, Colors.GRAY))
    
    @classmethod
    def error(cls, message: str, who=None):
        if who:
            message = f"FROM {who}: {message}"
        cls.logger.error(format_message(message, Colors.RED))
    
    @classmethod
    def info(cls, message: str, who=None):
        if who:
            message = f"FROM {who}: {message}"
        cls.logger.info(format_message(message, Colors.LIGHT_BLUE))


def format_message(message: str, color: Colors):
    return f"{color.value} {message} {Colors.RESET.value}"

Logger.setup_name('')
Logger.setup_verbosity(VerbosityLevel.VERBOSE) # default verbosity level for tests
