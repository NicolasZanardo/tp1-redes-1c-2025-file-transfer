import argparse
import time
from protocol.stop_and_wait import StopAndWaitProtocol
from protocol.server_listener import ServerManager
from protocol.go_back_n import GoBackNProtocol
from utils.logger import Logger, VerbosityLevel

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Upload files to a server.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="Decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument('-p', '--port', type=int, default=12345, help="Server port")
    parser.add_argument('-s', '--src', type=str, default="", help="Source file path")
    parser.add_argument('-n', '--name', type=str, default="", help="File name")
    parser.add_argument('-a', '--algorithm', type=str, default="sw", choices=["sw", "gbn"], help="sw or gbn")
    parser.add_argument('-r', '--protocol', help="error recovery protocol")

    args = parser.parse_args()

    Logger.setup_name('upload.py')
    if args.verbose:
        Logger.setup_verbosity(VerbosityLevel.VERBOSE)
    elif args.quiet:
        Logger.setup_verbosity(VerbosityLevel.QUIET)
    else:
        Logger.setup_verbosity(VerbosityLevel.NORMAL)

    sock = ServerManager.connect_to_server((args.host, args.port))

    if args.algorithm == "sw":
        protocol = StopAndWaitProtocol(sock, (args.host, args.port), args.src)
    elif args.algorithm == "gbn":
        protocol = GoBackNProtocol(sock, (args.host, args.port), args.src)
        
    try:
        protocol.start()
    finally:
        protocol.close()
        Logger.info("Upload completed and connection closed.")
