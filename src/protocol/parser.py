class PackageParser:
    def __init__(self):
        self.address_messages = {}

    def parse(self, address, data: bytes):
        current = self.address_messages.get(address)
        if current is None:
            current = self.address_messages[address] = []
        
        current.append(data)

        if (len(current) > 3):
            msg_size = int16.from_bytes(current[1:2], byteorder='big', signed=False)
            if (len(current) > msg_size):
                package = current[3:msg_size]
                self.address_messages[address] = current[msg_size:]
                return (address, package)
                
        return None
