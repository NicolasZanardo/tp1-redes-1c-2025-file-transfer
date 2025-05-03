import argparse
import time
from src import *

if __name__ == '__main__':
    # Custom help formatter to preserve manual spacing
    parser = argparse.ArgumentParser(
        prog='download',
        description="Download files to a server.",
        formatter_class=CustomHelpFormatter  # preserves your manual spacing
    )

    # Add arguments to the parser
    parser.add_argument('-v', '--verbose'  , action='store_true', help="increase output verbosity")
    parser.add_argument('-q', '--quiet'    , action='store_true', help="decrease output verbosity")
    parser.add_argument('-H', '--host'     , metavar='ADDR'     , type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument('-p', '--port'     , metavar='PORT'     , type=int, default=12345, help="Server port")
    parser.add_argument('-s', '--src'      , metavar='DIRPATH'  , type=str, default="", help="Source file path")
    parser.add_argument('-n', '--name'     , metavar='FILENAME' , type=str, default="", help="File name")
    parser.add_argument('-r', '--protocol' , metavar='protocol' , help="error recovery protocol")

    # Parse the arguments
    args = parser.parse_args()

    # Adjust verbosity
    Logger.setup_name('download.py')
    if args.verbose:
        Logger.setup_verbosity(VerbosityLevel.VERBOSE)
    elif args.quiet:
        Logger.setup_verbosity(VerbosityLevel.QUIET)
    else:
        Logger.setup_verbosity(VerbosityLevel.NORMAL)

    # Connect to the server
    sock = ServerManager.connect_to_server((args.host, args.port))
    
    # Check if the protocol is specified
    if args.algorithm == "sw":
        protocol = StopAndWaitReceiver(sock, args.name)
    elif args.algorithm == "gbn":
        protocol = GoBackNReceiver(sock, args.name)

    # Start the download process
    try:
        protocol.start()
    finally:
        protocol.close()
        Logger.info("Download completed and connection closed.")
