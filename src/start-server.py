import os
import sys
import argparse
import threading
from protocol.selective_repeat import SelectiveRepeatProtocol,SelectiveRepeatReceiver
from protocol.server_listener import ServerManager
from protocol.stop_and_wait import StopAndWaitProtocol, StopAndWaitReceiver
from utils.custom_help_formatter import CustomHelpFormatter
from utils.logger import VerbosityLevel, Logger
from argparse import Namespace
from protocol.connection_clossing import ConnectionClossing


def handle_client(conn, mode, file_path, storage, protocol_choice):
    """Handle a single client connection in a separate thread."""
    try:
        raw_sock = conn.socket
        #output_path = os.path.join(storage, filename)

        # Validar que el nombre del archivo no esté vacío
        if not file_path or file_path.strip() == "":
            Logger.error("El cliente no proporcionó un nombre de archivo válido.")
            return

        # Select protocol based on mode and protocol choice
        if mode == "download":
            if not os.path.isfile(file_path):
                Logger.error(f"No existe el archivo {file_path}")
                return
            if protocol_choice == "sw":
                protocol = StopAndWaitProtocol(
                    sock=raw_sock,
                    dest=conn.destination_address,
                    file_path=file_path
                )
            else:
                protocol = SelectiveRepeatProtocol(
                    sock=raw_sock,
                    dest=conn.destination_address,
                    file_path=file_path
                )
        else:
            # TODO: Avoid overwriting existing file
            if protocol_choice == "sw":
                protocol = StopAndWaitReceiver(
                    sock=raw_sock,
                    output_path=file_path
                )
            else:
                protocol = SelectiveRepeatReceiver(
                    sock=raw_sock,
                    output_path=file_path
                )

        try:
            protocol.start()
        except Exception as e:
            Logger.error(f"Error durante la transferencia: {e}")
    finally:
        try:
            # Realizar el closing handshake
            if ConnectionClossing.respond_to_clossing(raw_sock, conn.destination_address):
               Logger.info(f"Closing handshake completed with {conn.destination_address}")
            else:
                Logger.error(f"Closing handshake failed with {conn.destination_address}")
        except (OSError, NameError):  # NameError if protocol not initialized
            pass
        Logger.info(f"Conexión con cliente {conn.destination_address} finalizada.")

def behaviour(args, stop_event=None):
    """Run the server, stopping when stop_event is set."""
    if not os.path.isdir(args.storage):
        raise SystemExit(f"{args.storage} no es un directorio válido")

    server = ServerManager.start_server(host=args.host, port=args.port)
    Logger.info(f"Server listening on {args.host}:{args.port}")
    clients = []

    if stop_event is None:
        stop_event = Namespace(running=True)

    try:
        while stop_event.running:
            try:
                item = server.get_client()
                if item is None:
                    continue
                conn, mode, filename = item
                
                output_path = os.path.join(args.storage, filename)

                Logger.debug(f"Nombre de archivo recibido: {output_path}")
                
                # Create a new thread for each client
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(conn, mode, output_path, args.storage, args.protocol)
                )
                client_thread.daemon = True  # Threads terminate when main thread exits
                client_thread.start()
                clients.append(client_thread)

            except KeyboardInterrupt:
                stop_event.running = False
                Logger.info("Keyboard interrupt, shutting down server.")

            except Exception as e:
                Logger.error(f"Error aceptando cliente: {e}")
    finally:
        for cli in clients:
            cli.join(timeout=0.25)
        server.stop()
        Logger.info("Server stopped.")


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
    parser.add_argument('-r', '--protocol', metavar='protocol' , choices=["sw","sr"],default="sw", help="error recovery protocol")
    # Parse the arguments
    args = parser.parse_args()

    Logger.setup_name('start-server.py')
    if args.verbose:
        Logger.setup_verbosity(VerbosityLevel.VERBOSE)
    elif args.quiet:
        Logger.setup_verbosity(VerbosityLevel.QUIET)
    else:
        Logger.setup_verbosity(VerbosityLevel.NORMAL)

    behaviour(args)


