import socket
import pickle
import time
import random
from Crypto.Hash import SHAKE128
import hashlib
import psutil
import names

HOST = 'localhost'
PORT = 8888

address = "username"

def get_request(info):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    request = info
    client_socket.send(pickle.dumps(request))

    response = pickle.loads(client_socket.recv(4096))

    client_socket.close()

    return response

while True:

    work = get_request({'type': "get_work", 'method': 'mining', "address": address})
    public_key = work.get("public_key")
    work = work.get("work")

    print(address)

    random.seed(hashlib.sha256(public_key.encode('utf-8')).hexdigest())
    plot_index = [random.getrandbits(32) for i in range(0, 1000)]

    shake = SHAKE128.new()
    
    shake.update(bytes(plot_index[work.get("plot_index")]))

    shake.update(bytes(plot_index[0]))
    t = time.time()

    result = shake.read(1073741824).hex()[work.get("work"):work.get("work") + 32]

    print(f"{60 / (time.time() - t)} hashes per minute ({86400 / (time.time() - t) * 0.001} TiD per day)")

    print(get_request({'type': "submit_work", 'method': 'mining', "public_key": public_key, "submission": result, "address": address}))

    print(f"submitted {result}")
