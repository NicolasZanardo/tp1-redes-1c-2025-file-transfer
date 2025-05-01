import argparse
from librerias.server import Server
from protocol.server_listener import ServerManager
from utils.logger import Logger, VerbosityLevel

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Upload files to a server.")

    # Optional Arguments
    #parser.add_argument('-h', '--help', help='show this help message and exit')
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="Decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, default="127.0.0.1", help="Server IP address", required=True)
    parser.add_argument('-p', '--port', type=int, default=8080, help="Server port", required=True)
    parser.add_argument('-s', '--storage', type=str, default="", help="Storage dir path", required=True)
    parser.add_argument('-a', '--algorithm', type=str, default="sw", help="sw or sr")
    parser.add_argument('-r', '--protocol', help="error recovery protocol")

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
            server.stop()
            break
        except Exception as e:
            Logger.error(f"Error accepting client: {e}")
            server.stop()
            break

    Logger.info("Server stopped.")

    