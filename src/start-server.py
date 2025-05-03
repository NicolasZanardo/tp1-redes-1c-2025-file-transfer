import argparse, os
from protocol.server_listener import ServerManager
from protocol.stop_and_wait import StopAndWaitReceiver
from protocol.selective_repeat import SelectiveRepeatReceiver
from utils.logger import Logger, VerbosityLevel

def main():
    parser = argparse.ArgumentParser(description="Upload files to a server.")
    parser.add_argument('-v','--verbose',action='store_true')
    parser.add_argument('-q','--quiet',  action='store_true')
    parser.add_argument('-H','--host',   type=str, required=True)
    parser.add_argument('-p','--port',   type=int, required=True)
    parser.add_argument('-s','--storage',type=str, required=True)
    parser.add_argument('-n','--name',   type=str, required=True)
    parser.add_argument('-a','--algorithm',choices=["sw","sr"],default="sw")
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

                if args.algorithm == "sw":
                    protocol = StopAndWaitReceiver(raw_sock, output_path)
                else:
                    protocol = SelectiveRepeatReceiver(raw_sock, output_path)

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

if __name__ == "__main__":
    main()
