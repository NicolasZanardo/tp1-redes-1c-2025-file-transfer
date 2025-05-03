import argparse
import time
from protocol.stop_and_wait import StopAndWaitProtocol
from protocol.server_listener import ServerManager
from src.protocol.selective_repeat import SelectiveRepeatProtocol
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
    parser.add_argument('-a', '--algorithm', type=str, default="sw", choices=["sw", "sr"], help="sw or sr")

    args = parser.parse_args()

    Logger.setup_name('download.py')
    if args.verbose:
        Logger.setup_verbosity(VerbosityLevel.VERBOSE)
    elif args.quiet:
        Logger.setup_verbosity(VerbosityLevel.QUIET)
    else:
        Logger.setup_verbosity(VerbosityLevel.NORMAL)

    connection = ServerManager.connect_to_server((args.host, args.port))
    Logger.info(f"Handshake completado con servidor en {args.host}:{args.port}")
    
    udp_socket = connection.socket

    if args.algorithm == "sw":
        protocol = StopAndWaitProtocol(
            sock=udp_socket,
            dest=connection.destination_address,
            file_path=args.src
        )
    else:
        protocol = SelectiveRepeatProtocol(
            sock=udp_socket,
            dest=connection.destination_address,
            file_path=args.src
        )

    try:
        protocol.start()
    finally:
        protocol.close()      
        connection.close()    
        Logger.info("Upload completed and connection closed.")
