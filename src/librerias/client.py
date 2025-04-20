import socket

class Client:
    def __init__(self, host, port, algorithm):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if algorithm == "sw":
            #here create protocol "stop and wait"
            print("was chosen protocol stop and wait", algorithm)
            print("host,", host, "port", port)
        elif algorithm == "sr":
            #here create protocol "selective repeat"
            print("was chosen protocol selective repeat", algorithm)
            print("host,", host, "port", port)

    def upload(self, file_name, algorithm):
        if algorithm == "sw":
            #here start algorithm stop and wait
            print("UPLOAD")
            print("algorithm stop and wait", algorithm)
        elif algorithm == "sr":
            #here start algorithm selective repeat
            print("UPLOAD")
            print("algorithm selective repeat", algorithm)

    def download(self, file_name, algorithm):
        if algorithm == "sw":
            #here start algorithm stop and wait
            print("DOWNLOAD")
            print("algorithm stop and wait", algorithm)
        elif algorithm == "sr":
            #here start algorithm selective repeat
            print("DOWNLOAD")
            print("algorithm selective repeat", algorithm)

    def close(self):
        self.socket.close()