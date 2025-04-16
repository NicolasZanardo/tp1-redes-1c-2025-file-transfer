import argparse
#from lib.server import Server

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Upload files to a server.")

    # Argumentos opcionales
    parser.add_argument('-v', '--verbose', action='store_true', help="Increase output verbosity")
    parser.add_argument('-q', '--quiet', action='store_true', help="Decrease output verbosity")
    parser.add_argument('-H', '--host', type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument('-p', '--port', type=int, default=8080, help="Server port")
    parser.add_argument('-s', '--storage', type=str, default="", help="Storage dir path")
    parser.add_argument('-a', '--algorithm', type=str, default="sw", help="sw or sr")
    parser.add_argument('-r', '--protocol', help="error recovery protocol")