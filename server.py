import socket
import threading
import json
import struct
import time
import random
from database import Database
from farmer import Farmer
from username import generate_username, announcement
from flask import Flask, render_template

app = Flask(__name__)

farmer = Farmer([])
clients = {}
clients_lock = threading.Lock()
submit_lock = True
submission = ""
winner = ()
skip = False

farmer_database = Database("farmer")
farmer_database.create_table()

wallet_database = Database("wallet")
wallet_database.create_table()

token_database = Database("token")
token_database.create_table()

def broadcast(message):
    try:
        global clients
        json_data = json.dumps(message)
        json_bytes = json_data.encode()
        msglen = struct.pack('>I', len(json_bytes))

        with clients_lock:
            for client in clients:
                try:
                    clients[client]["connection"].sendall(msglen + json_bytes)
                except Exception as e:
                    print(f"Error broadcasting message to a client: {e}")
                    clients[client]["connection"].close()
                    del clients[client]
    except Exception:
        pass
    
def send(message, sender_conn):
    global clients
    json_data = json.dumps(message)
    json_bytes = json_data.encode()
    msglen = struct.pack('>I', len(json_bytes))

    try:
        clients[sender_conn]["connection"].sendall(msglen + json_bytes)
    except Exception as e:
        print(f"Error broadcasting message to a client: {e}")
        clients[sender_conn]["connection"].close()
        del clients[sender_conn]

def check_duplicates(address):
    global clients
    for client in clients:
        if clients[client]["address"] == address:
            return False
    return True

def handle_client(conn, addr):
    global clients, submit_lock, submission, winner, skip
    print(f"New connection from {addr}")
    with clients_lock:

        ips = []
        for client in clients:
            ips.append(client[0])
        if not addr[0] in ips:
            clients[addr] = {"connection": conn, "address": ""}
        else:
            send({"type": "error", "message": "you already have a farmer on this IP!"}, addr)
    
    try:
        while True:
            # Read message length first (4 bytes)
            raw_msglen = conn.recv(4)
            if not raw_msglen:
                break
            msglen = struct.unpack('>I', raw_msglen)[0]
            data = conn.recv(msglen)
            if not data:
                break
            try:
                json_data = json.loads(data.decode())

                user = farmer_database.get_data(addr[0])
                if user == None:
                    farmer_database.insert_data(addr[0], {"username": ""})
                    user = {"username": ""}

                print(addr, winner)

                if user["username"] == "":
                    send({"type": "neutral", "message": f"please register your IP as a farmer in the webwallet, your IP is: {addr[0]}"}, addr)
                else:
                    if addr == winner:
                        if json_data["type"] == "submit":
                            submission = json_data["data"]
                            submit_lock = True

                        elif json_data["type"] == "reject":
                            skip = True
                            submit_lock = True
                        else:
                            send({"type": "error", "message": "Invalid submission!"}, addr)
                    else:
                        send({"type": "error", "message": "there is another IP on your account!"}, addr)

            except json.JSONDecodeError as e:
                print(f"Received invalid JSON from {addr}: {e}")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        print(f"Connection closed by {addr}")
        try:
            with clients_lock:
                clients[addr]["connection"].close()
                del clients[addr]
        except KeyError:
            pass
def start_server():
    global clients
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('10.0.0.250', 3333))
    server.listen(5)
    print("Server listening on port 3333")
    
    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except Exception as e:
        print(f"Error accepting connections: {e}")
    finally:
        server.close()

def loop():
    global submit_lock, clients, submission, winner, skip
    while True:
        try:
            print("getting next client...")
            while True:
                try:
                    winner = random.choice(list(clients.keys()))
                    try:
                        address = farmer_database.get_data(winner[0].replace("\n", ""))["username"]
                        if not address == "" or address == None:
                            break
                    except TypeError:
                        send({"type": "error", "message": f"you must verify your IP in the webwallet! Your IP: {winner[0]}", "break": True}, winner)
                except IndexError:
                    pass

            print(f"client {address} chosen")
            submit_lock = False

            seed = random.randint(0, 12)
            index = random.randint(0, 469762016)

            broadcast({"type": "proof", "address": address, "index": index, "seed": seed, "message": announcement(address)})

            print("awaiting response...")

            t = time.time()
            while time.time() - t < 2:
                if submit_lock:
                    if skip:
                        broadcast({"type": "skipped", "message": f"farmer {address} skipped."})
                        skip = False
                        break
                    else:
                        print("client responded!")
                        broadcast({"type": "suspense", "message": f"farmer {address} responded. Drum-roll please!"})
                        farmer.plot({"address": address, "seed": seed}, "E:\\temp.tiny")
                        print(farmer.extract("E:\\temp.tiny", index), submission)
                        if farmer.extract("E:\\temp.tiny", index)[0] == submission[0]:
                            reward = (len(clients) / 100) * (25 - seed)
                            broadcast({"type": "winner", "message": f"farmer {address} WON THE BLOCK!!! (+{reward} TiD)"})
                        else:
                            broadcast({"type": "error", "message": f"farmer {address} responded with the wrong data"})
                        break
            if submit_lock == False:
                print("client did not respond")
                broadcast({"type": "error", "message": f"farmer {address} did not respond"})
                submit_lock = True
        except Exception as e:
            print(f"server error occured, round restarting: {e}")
            broadcast({"type": "error", "message": f"server error occured, round restarting."})

if __name__ == "__main__":
    concurrent_thread = threading.Thread(target=loop)
    concurrent_thread.daemon = True
    concurrent_thread.start()

    start_server()
