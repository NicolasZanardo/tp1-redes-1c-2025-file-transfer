import sys
import unittest
from src.utils import Logger, VerbosityLevel

loader = unittest.TestLoader()
suite = loader.discover('test')

runner = unittest.TextTestRunner(verbosity=2)


custom_args = [arg for arg in sys.argv if arg.startswith("-v")]
print(f"Running with custom arguments: {custom_args}")

for arg in custom_args:
    sys.argv.remove(arg)

if "-vv" in custom_args:
    print("Verbose level is set to VERBOSE")
    Logger.setup_verbosity(VerbosityLevel.VERBOSE)
elif "-vq" in custom_args:
    print("Verbose level is set to QUIET")
    Logger.setup_verbosity(VerbosityLevel.QUIET)
else:
    print("Verbose level is set to NORMAL")
    Logger.setup_verbosity(VerbosityLevel.NORMAL)

# Set up the logger for the test
# Needs to be set up after the verbosity level is set
# to ensure the correct level is applied
Logger.setup_name("test/run.py")


result = runner.run(suite)