import argparse
from protocol.stop_and_wait import StopAndWaitProtocol
from protocol.selective_repeat import SelectiveRepeatProtocol
from protocol.server_listener import ServerManager
from utils.logger import Logger, VerbosityLevel

def main():
    parser = argparse.ArgumentParser(description="Upload files to a server.")
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-q', '--quiet',   action='store_true')
    parser.add_argument('-H', '--host',    type=str, default="127.0.0.1")
    parser.add_argument('-p', '--port',    type=int, default=3000)
    parser.add_argument('-s', '--src',     type=str, required=True)
    parser.add_argument('-a', '--algorithm', choices=["sw","sr"], default="sw")
    args = parser.parse_args()

    Logger.setup_name('upload.py')
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

if __name__ == "__main__":
    main()
