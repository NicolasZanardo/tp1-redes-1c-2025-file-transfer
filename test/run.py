import sys
import unittest
from src.utils.logger import Logger, VerbosityLevel

loader = unittest.TestLoader()
suite = loader.discover('test')

runner = unittest.TextTestRunner(verbosity=2)


custom_args = [arg for arg in sys.argv if arg.startswith("-v")]
print(f"Running with custom arguments: {custom_args}")

for arg in custom_args:
    sys.argv.remove(arg)

Logger.setup_name("test/run.py")
if "-vv" in custom_args:
    Logger.setup_verbosity(VerbosityLevel.VERBOSE)
elif "-vq" in custom_args:
    Logger.setup_verbosity(VerbosityLevel.QUIET)
else:
    Logger.setup_verbosity(VerbosityLevel.NORMAL)


result = runner.run(suite)