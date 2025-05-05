import sys
import unittest
import argparse
import random
from src.utils import Logger, VerbosityLevel, CustomHelpFormatter
from test.utils_test import TestParams

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
parser.add_argument('-n', '--noise'    , metavar='NOISE'    , type=int, default=0, help="amount of disruption in net of integration tests (0-10)")
parser.add_argument('-s', '--seed'     , metavar='SEED'     , type=int, default=0, help="specify the seed that the random uses on random tets")
args = parser.parse_args()

if args.seed != 0:
    TestParams.seed = args.seed
else:
    TestParams.seed = random.randint(0, 2**32 - 1)

if args.verbose:
    Logger.setup_verbosity(VerbosityLevel.VERBOSE)
elif args.quiet:
    Logger.setup_verbosity(VerbosityLevel.QUIET)
else:
    Logger.setup_verbosity(VerbosityLevel.NORMAL)

TestParams.noise = args.noise

# Set up the logger for the test
# Needs to be set up after the verbosity level is set
# to ensure the correct level is applied
Logger.setup_name("test/run.py")

result = runner.run(suite)