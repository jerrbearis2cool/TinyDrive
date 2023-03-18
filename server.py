import random
import socket
import threading
import pickle
import time
import json
import os

# Define the server host and port
HOST = 'localhost'
PORT = 8888

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind((HOST, PORT))

server_socket.listen()

print(f'Server listening on port {PORT}')

work = {}
def import_user_data(user):
    with open(f'user_data/{user}.json', 'r') as f:
        return json.load(f)

def export_data(data, user):
    with open(f'user_data/{user}.json', 'w') as f:
        return json.dump(data, f)

def pay(username, amount):
    data = import_user_data(username)

    balance = data.get("balance")

    data["balance"] = balance + amount
    export_data(data, username)


def handle_client(client_socket, client_address):
        output = ""

        data = client_socket.recv(4096)
        request = pickle.loads(data)

        if request.get("type") == "get_work":

            if request.get("method") == "farming":
                if os.path.isfile(f"user_data\\{request.get('address')}.json"):
                    if not request.get('address') in list(work.keys()):
                        generated_work = random.randint(0, 1073741824 - 32)
                        plot_index = random.randint(0, 1000)

                        work[request.get("address")] = {"work": generated_work, "submitted": False, "time": time.time(), "validators": {}, "plot_index": plot_index}

                        print(work)
                        output = {"work": generated_work, "plot_index": plot_index}
                    else:
                        output = f"waiting for previous work to be verified ({len(work[request.get('address')].get('validators'))} / 10)"

            elif request.get("method") == "mining":

                key = list(work.keys())[random.randint(0, len(work) - 1)]
                work[key]["validators"][request.get("address")] = ""

                output = {"public_key": key, "work": work[key]}

        elif request.get("type") == "submit_work":

            if request.get("method") == "farming":
                work[request.get("address")]["submitted"] = True

                if (time.time() - work[request.get("address")]["time"]) > 3:
                    output = "your submission speed is too low"
                else:
                    work[request.get("address")]["submission"] = request.get("submission")

                    print(request)

                    output = "your submission is being verified!"

            elif request.get("method") == "mining":

                print(list(work[request.get("public_key")]["validators"].keys()))

                if str(request.get("address")) in list(work[request.get("public_key")]["validators"].keys()):
                    work[request.get("public_key")]["validators"][request.get("address")] = request.get("submission")
                    output = work
                else:
                    output = f"{request.get('address')}, you are not registered to validate this submission"

                if len(work[request.get("public_key")]["validators"]) >= 10:
                    consensus = max(set(list(work[request.get("public_key")]["validators"].values())), key = list(work[request.get("public_key")]["validators"].values()).count)

                    if work[request.get("public_key")]["submission"] == consensus:
                        pay(request.get("public_key"), 0.001)

                    output = {"you have been paid 0.001 for your part of consensus!"}

                    work.pop(request.get("public_key"))

        client_socket.send(pickle.dumps(output))

        client_socket.close()

while True:
    # Accept incoming connections
    client_socket, client_address = server_socket.accept()

    print(f'Accepted connection from {client_address}')

    # Start a new thread to handle the client request
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()
