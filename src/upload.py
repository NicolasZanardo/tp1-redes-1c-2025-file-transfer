import argparse
import time
from librerias.client import Client
from protocol.server_listener import ServerManager
from utils.logger import Logger, VerbosityLevel

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Upload files to a server.")

    # Optional Arguments
    #parser.add_argument('-h', '--help', help='show this help message and exit')
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="Decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument('-p', '--port', type=int, default=12345, help="Server port")
    parser.add_argument('-s', '--src', type=str, default="", help="Source file path")
    parser.add_argument('-n', '--name', type=str, default="", help="File name")
    parser.add_argument('-a', '--algorithm', type=str, default="sw", help="sw or sr")
    parser.add_argument('-r', '--protocol', help="error recovery protocol")

    # Parse the arguments
    args = parser.parse_args()

    # Adjust verbosity
    Logger.setup_name('upload.py')
    
    if args.verbose:
        Logger.setup_verbosity(VerbosityLevel.VERBOSE)
    elif args.quiet:
        Logger.setup_verbosity(VerbosityLevel.QUIET)
    else:
        Logger.setup_verbosity(VerbosityLevel.NORMAL)


    socket = ServerManager.connect_to_server((args.host, args.port))
    
    while True:
        try:
            time.sleep(10)  # Sleep for a short time to avoid busy waiting
        except KeyboardInterrupt:
            print("  --KeyboardInterrupt--")
            socket.close()
            break
        except Exception as e:
            Logger.error(f"Error accepting client: {e}")
            socket.close()
            break

    Logger.info("Client stopped.")

    #client = Client(args.host, args.port, args.algorithm)
    #client.upload(args.name, args.algorithm)
    #client.close()
