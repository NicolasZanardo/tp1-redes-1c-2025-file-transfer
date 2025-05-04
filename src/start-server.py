import os
import sys
import argparse
from protocol.selective_repeat import SelectiveRepeatProtocol
from protocol.server_listener import ServerManager
from protocol.stop_and_wait import StopAndWaitProtocol
from utils.custom_help_formatter import CustomHelpFormatter
from utils.logger import VerbosityLevel, Logger

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='start-server',
        description='Start a program to host the file-server.',
        formatter_class=CustomHelpFormatter  # preserves your manual spacing
    )

    parser.add_argument('-v', '--verbose' , action='store_true', help="increase output verbosity")
    parser.add_argument('-q', '--quiet'   , action='store_true', help="decrease output verbosity")
    parser.add_argument('-H', '--host'    , metavar='ADDR'     , type=str, default="127.0.0.1", help="service IP address")
    parser.add_argument('-p', '--port'    , metavar='PORT'     , type=int, default=8080, help="service port")
    parser.add_argument('-s', '--storage' , metavar='DIRPATH'  , type=str, default="", help="storage dir path")
    parser.add_argument('-r', '--protocol', metavar='protocol' , help="error recovery protocol")
    parser.add_argument('-n','--name',   type=str, required=True)
    parser.add_argument('-a','--algorithm',choices=["sw","sr"],default="sw")
    # Parse the arguments
    args = parser.parse_args()

    Logger.setup_name('start-server.py')
    if args.verbose:
        Logger.setup_verbosity(VerbosityLevel.VERBOSE)
    elif args.quiet:
        Logger.setup_verbosity(VerbosityLevel.QUIET)
    else:
        Logger.setup_verbosity(VerbosityLevel.NORMAL)

    if not os.path.isdir(args.storage):
        raise SystemExit(f"{args.storage} no es un directorio válido")

    server = ServerManager.start_server(host=args.host, port=args.port)
    Logger.info(f"Server listening on {args.host}:{args.port}")

    try:
        while True:
            try:
                conn = server.get_client()
                if conn is None:
                    continue

                raw_sock = conn.socket
                output_path = os.path.join(args.storage, args.name)

                # Check if the protocol is specified
                if args.algorithm == "sw":
                    protocol = StopAndWaitProtocol(
                    sock=raw_sock,
                    dest=conn.destination_address,
                    file_path= output_path
                )
                else:
                    protocol = SelectiveRepeatProtocol(
                    sock=raw_sock,
                    dest=conn.destination_address,
                    file_path= output_path
                )

                try:
                    protocol.start() 
                except Exception as e:
                    Logger.error(f"Error durante la transferencia: {e}")
                finally: 
                    try: protocol.close()
                    except OSError:
                        pass
                    conn.close()
                    Logger.info("Conexión con cliente finalizada.")

            except KeyboardInterrupt:
                Logger.info("Keyboard interrupt, shutting down server.")
                break

            except Exception as e:
                Logger.error(f"Error aceptando cliente: {e}")
    finally:
        server.stop()
        Logger.info("Server stopped.")

