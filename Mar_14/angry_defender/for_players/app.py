import os
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import OrderedDict

from flask import Flask, abort, request

SECRET = os.environ["FLAG"].encode("ascii")
MAX_DATA_SIZE = 1024 * 1024
CACHE_FOLDER = "c:\\storage"
CACHE_SIZE = 256

class LRU:
    def __init__(self, folder: str, max_size: int) -> None:
        self.folder = Path(folder)
        self.max_size = max_size
        self.queue: List[str, ]  = OrderedDict()

    def write(self, key: str, value: bytes) -> None:
        if self.max_size <= len(self.queue):
            retired_key, _ = self.queue.popitem(last=False)
            (self.folder / retired_key).unlink()
        self.queue[key] = None
        (self.folder / key).write_bytes(value)

    def read(self, key: str) -> bytes:
        self.queue.pop(key)
        self.queue[key] = None
        return (self.folder / key).read_bytes()

app = Flask(__name__)
lru = LRU(CACHE_FOLDER, CACHE_SIZE)


@app.route("/cache", methods=["PUT"])
def put() -> str:
    data = request.data
    if MAX_DATA_SIZE < len(data):
        abort(403)
    id = uuid.uuid4()
    lru.write(id.hex, data + SECRET)
    return str(id)


@app.route("/cache/<key>", methods=["GET"])
def get(key: str) -> bytes:
    id = uuid.UUID(key)
    try:
        blob = lru.read(id.hex)
    except KeyError:
        abort(404)
    data = blob[: -len(SECRET)]
    if data + SECRET != blob:
        abort(500)
    return data


if __name__ == "__main__":
    app.run()
