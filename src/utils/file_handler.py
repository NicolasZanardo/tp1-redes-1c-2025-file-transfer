from typing import Iterator

class FileReader():
    def __init__(self, file_path: str):
        self.file_path = file_path

    def read_chunks(self, chunk_size: int) -> Iterator[bytes]:
        with open(self.file_path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

class FileWriter():
    def __init__(self, output_path: str):
        self.file = open(output_path, 'wb')

    def write_chunk(self, data: bytes) -> None:
        self.file.write(data)

    def close(self) -> None:
        self.file.close()

class FileChunkReader:
    def __init__(self, file_path: str, chunk_size: int = 1024):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.file = open(file_path, 'rb')

    def __iter__(self):
        return self

    def __next__(self):
        chunk = self.file.read(self.chunk_size)
        if not chunk:
            self.file.close()
            raise StopIteration
        return chunk