import socket

class Client:
    def __init__(self, host, port, algorithm):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if algorithm == "sw":
            #aca crear protocolo "stop and wait"
            print("Se eligio protocolo stop and wait", algorithm)
            print("host,", host, "port", port)
        elif algorithm == "sr":
            #aca crear protocolo "selective repeat"
            print("Se eligio protocolo selective repeat", algorithm)
            print("host,", host, "port", port)

    def upload(self, file_name, algorithm):
        if algorithm == "sw":
            #aca iniciar algoritmo stop and wait
            print("UPLOAD")
            print("algoritmo stop and wait", algorithm)
        elif algorithm == "sr":
            #aca iniciar algoritmo selective repeat
            print("UPLOAD")
            print("algoritmo selective repeat", algorithm)

    def download(self, file_name, algorithm):
        if algorithm == "sw":
            #aca iniciar algoritmo stop and wait
            print("DOWNLOAD")
            print("algoritmo stop and wait", algorithm)
        elif algorithm == "sr":
            #aca iniciar algoritmo selective repeat
            print("DOWNLOAD")
            print("algoritmo selective repeat", algorithm)

    def close(self):
        self.socket.close()