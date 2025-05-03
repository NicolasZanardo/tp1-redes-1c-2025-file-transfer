import sys
import argparse
from src import *

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

    # Parse the arguments
    args = parser.parse_args()

    # Adjust verbosity
    Logger.setup_name('start-server.py')

    if args.verbose:
        Logger.setup_verbosity(VerbosityLevel.VERBOSE)
    elif args.quiet:
        Logger.setup_verbosity(VerbosityLevel.QUIET)
    else:
        Logger.setup_verbosity(VerbosityLevel.NORMAL)

    server = ServerManager.start_server(host=args.host, port=args.port)
    
    while True:
        try:
            server.get_client()
        except KeyboardInterrupt:
            print(" KeyboardInterrupt.")
            server.stop()
            break
        except Exception as e:
            Logger.error(f"Error accepting client: {e}")
            server.stop()
            break

    Logger.info("Server stopped.")

    