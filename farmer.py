import socket
import pickle
import time
import random
from Crypto.Hash import SHAKE128
import hashlib

HOST = 'localhost'
PORT = 8888

def get_request(info):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    request = info
    client_socket.send(pickle.dumps(request))

    response = pickle.loads(client_socket.recv(4096))

    client_socket.close()

    return response

while True:

    work = get_request({'type': "get_work", 'method': 'farming', "address": "jerrbearisawsome"})


    if type(work) is dict:

        with open('2719985563', 'r') as f:
            file_size = f.seek(0, 2)  # get the size of the file

            f.seek(work.get("work"))  # move the file pointer to the starting position
            chunk = f.read(32)  # read 32 characters from the starting position

            print("submitting work...")
            print(get_request({'type': "submit_work", 'method': 'farming', "address": "jerrbearisawsome", "submission": chunk}))

    else:
        print(work)

    time.sleep(5)
