import argparse
import time
from protocol.stop_and_wait import StopAndWaitReceiver
from protocol.server_listener import ServerManager
from src.protocol.go_back_n import GoBackNReceiver
from utils.logger import Logger, VerbosityLevel

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download files from server.")
    parser.add_argument('-h', '--help', help='show this help message and exit')
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="Decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, default="localhost", help="Server IP address")
    parser.add_argument('-p', '--port', type=int, default=8080, help="Server port")
    parser.add_argument('-s', '--src', type=str, default="", help="Source file path")
    parser.add_argument('-n', '--name', type=str, default="", help="File name")
    parser.add_argument('-a', '--algorithm', type=str, default="sw", choices=["sw", "gbn"], help="sw or gbn")

    args = parser.parse_args()

    Logger.setup_name('download.py')
    if args.verbose:
        Logger.setup_verbosity(VerbosityLevel.VERBOSE)
    elif args.quiet:
        Logger.setup_verbosity(VerbosityLevel.QUIET)
    else:
        Logger.setup_verbosity(VerbosityLevel.NORMAL)

    sock = ServerManager.connect_to_server((args.host, args.port))

    if args.algorithm == "sw":
        protocol = StopAndWaitReceiver(sock, args.name)
    elif args.algorithm == "gbn":
        protocol = GoBackNReceiver(sock, args.name)

    try:
        protocol.start()
    finally:
        protocol.close()
        Logger.info("Download completed and connection closed.")
