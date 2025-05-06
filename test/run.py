import sys
import unittest
import argparse
import random
from src.utils import Logger, VerbosityLevel, CustomHelpFormatter
from src.protocol.connection_closing import ConnectionConfig

loader = unittest.TestLoader()
suite = loader.discover('test')

runner = unittest.TextTestRunner(verbosity=2)

# Custom help formatter to preserve manual spacing
parser = argparse.ArgumentParser(
    prog='test.run',
    description="Run all tests discovered with 'unittest'.",
    formatter_class=CustomHelpFormatter  # preserves your manual spacing
)

# Add arguments to the parser
parser.add_argument('-v', '--verbose'  , action='store_true', help="increase output verbosity")
parser.add_argument('-q', '--quiet'    , action='store_true', help="decrease output verbosity")
args = parser.parse_args()

ConnectionConfig.TIMEOUT = 0.125

if args.verbose:
    Logger.setup_verbosity(VerbosityLevel.VERBOSE)
elif args.quiet:
    Logger.setup_verbosity(VerbosityLevel.QUIET)
else:
    Logger.setup_verbosity(VerbosityLevel.NORMAL)

# Set up the logger for the test
# Needs to be set up after the verbosity level is set
# to ensure the correct level is applied
Logger.setup_name("test/run.py")

result = runner.run(suite)