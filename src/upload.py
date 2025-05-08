import argparse
import os
from protocol.selective_repeat import SelectiveRepeatProtocol
from protocol.stop_and_wait import StopAndWaitProtocol
from protocol.server_listener import ServerManager
from utils import Logger, VerbosityLevel, CustomHelpFormatter, ConnectionConfig

def behaviour(args):
    
    if not os.path.isfile(args.src):
        raise SystemExit(f"No existe el archivo {args.src}")
    
    connection, mode, filename = ServerManager.connect_to_server((args.host, args.port), "upload", args.name)
    Logger.info(f"Handshake completado con servidor en {args.host}:{args.port}, con modo {mode}")

    udp_socket = connection.socket
    
    Logger.debug(f"Nombre de archivo enviado en handshake: {filename}")

    # Check if the protocol is specified
    if args.protocol == "sw":
        protocol = StopAndWaitProtocol(
            sock=udp_socket,
            dest=connection.destination_address,
            file_path=args.src,
            timeout=ConnectionConfig.TIMEOUT
        )
    else:
        protocol = SelectiveRepeatProtocol(
            sock=udp_socket,
            dest=connection.destination_address,
            file_path=args.src,
            timeout=ConnectionConfig.TIMEOUT,
            window_size=ConnectionConfig.SR_WINDOW_SIZE
        )

    try:
        protocol.start()
    finally:
        # Cerrar el protocolo y la conexión
        connection.close()
        Logger.info("Upload completed and connection closed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='upload',
        description="Upload files to a server.",
        formatter_class=CustomHelpFormatter  # preserves your manual spacing
    )

    parser.add_argument('-v', '--verbose'  , action='store_true', help="increase output verbosity")
    parser.add_argument('-q', '--quiet'    , action='store_true', help="decrease output verbosity")
    parser.add_argument('-H', '--host'     , metavar='ADDR'     , type=str, default="127.0.0.1", help="Server IP address")
    parser.add_argument('-p', '--port'     , metavar='PORT'     , type=int, default=12345, help="Server port")
    parser.add_argument('-s', '--src'      , metavar='DIRPATH'  , type=str, default="", help="Source file path")
    parser.add_argument('-n', '--name'     , metavar='FILENAME' , type=str, default="", help="File name")
    parser.add_argument('-r', '--protocol' , metavar='protocol' , choices=["sw","sr"], default="sw" ,help="error recovery protocol")

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

    behaviour(args)


