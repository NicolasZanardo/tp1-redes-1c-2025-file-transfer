import argparse

import os
import time
from protocol.stop_and_wait import StopAndWaitReceiver
from protocol.selective_repeat import SelectiveRepeatReceiver
from protocol.server_listener import ServerManager
from utils import VerbosityLevel, Logger, CustomHelpFormatter, ConnectionConfig

def behaviour(args):
    connection, mode, filename = ServerManager.connect_to_server((args.host, args.port), "download", args.name)
    Logger.info(f"Handshake completado con servidor en {args.host}:{args.port}, com modo {mode}")
    
    udp_socket = connection.socket
    file_path = args.dst
    
    if args.protocol == "sw":
        protocol = StopAndWaitReceiver(
            sock=udp_socket,
            output_path=args.dst,
            timeout=ConnectionConfig.TIMEOUT
        )
    else:
        protocol = SelectiveRepeatReceiver(
            sock=udp_socket,
            output_path=args.dst,
            timeout=ConnectionConfig.TIMEOUT
        )

    # Start the download process
    try:
        protocol.start()
    finally:
        connection.close()    
        Logger.info("Download completed and connection closed.")

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
    parser.add_argument('-d', '--dst'      , metavar='DIRPATH'  , type=str, default="", help="Destination file path")
    parser.add_argument('-n', '--name'     , metavar='FILENAME' , type=str, default="", help="File name")
    parser.add_argument('-r', '--protocol' , metavar='protocol' , choices=["sw","sr"], default="sw" ,help="error recovery protocol")

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

    behaviour(args)


