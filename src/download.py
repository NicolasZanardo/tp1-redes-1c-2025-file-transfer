from librerias.client import Client
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download files from server.")

    # Optional Arguments
    parser.add_argument('-h', '--help', help='show this help message and exit')
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="Decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, default="localhost", help="Server IP address")
    parser.add_argument('-p', '--port', type=int, default=8080, help="Server port")
    parser.add_argument('-s', '--src', type=str, default="", help="Source file path")
    parser.add_argument('-n', '--name', type=str, default="", help="File name")
    parser.add_argument('-a', '--algorithm', type=str, default="sw", help="sw or sr")
    parser.add_argument('-r', '--protocol', help="error recovery protocol")

    # Parse the arguments
    args = parser.parse_args()

    # Adjust verbosity
    verbose = args.verbose and not args.quiet

    client = Client(args.host, args.port, args.algorithm)
    client.download(args.name, args.algorithm)
    client.close()