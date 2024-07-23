import os
import random
import json
import time
import hashlib
from tqdm import tqdm
from colorama import Fore
from Crypto.Hash import SHAKE128
import configparser

import socket
import json
import threading
import signal
import struct
import time

register = False
running = True
submit = False
index = 0

address = ""
directories = []

class Print:
    def success(header, message):
        print(f'[{time.strftime("%H:%M:%S")}] {Fore.GREEN + header + Fore.RESET} {message}')

    def error(header, message):
        print(f'[{time.strftime("%H:%M:%S")}] {Fore.RED + header + Fore.RESET} {message}')

    def neutral(message):
        print(f'[{time.strftime("%H:%M:%S")}] {message}')

    def suspense(message):
        l = len(f"| {message} |")
        print("".join("-" for i in range(0, l)))
        print(f"| {message} |")
        print("".join("-" for i in range(0, l)))
printf = Print

class Farmer:

    def __init__(self, paths):
        self.paths = paths

    def plot(self, data_dict, out, chunk=1024 * 1024):
        data = json.dumps(data_dict, sort_keys=True).encode('utf-8')
        
        shake = SHAKE128.new()
        shake.update(data)
        
        size = int(3.5 * 1024 * 1024 * 1024)  # 3.5 GB

        with open(out, 'wb') as f:
            for _ in tqdm(range(0, size, chunk), unit=" MB"):
                chunk_data = shake.read(chunk)
                if chunk_data is None:
                    raise ValueError("Failed to read from SHAKE128 object.")
                if len(chunk_data) == 0:
                    raise ValueError("Read an empty chunk from SHAKE128 object.")
                f.write(chunk_data)

        print(f"{size / (1024 * 1024 * 1024):.2f} GB plot generated to {out}")

    def extract(self, file, index, n_bits=256):
        n_bytes = n_bits // 8
        size = os.path.getsize(file)
        if size < n_bytes:
            return False

        with open(file, 'rb') as f:
            f.seek(index)
            extracted_bytes = f.read(n_bytes)

        return extracted_bytes.hex(), index

    def proof(self, file, n_bits=256):
        size = os.path.getsize(file)
        index = random.randint(0, size - n_bits // 8)

        data, index = self.extract(file, index)
        return data, index

farmer = Farmer([])

def receive_messages(client):
    global running, submit, index, plots
    while running:
        try:
            raw_msglen = client.recv(4)
            if not raw_msglen:
                break
            msglen = struct.unpack('>I', raw_msglen)[0]
            data = client.recv(msglen)
            if not data:
                break
            try:
                r = json.loads(data.decode())
                if r["type"] == "proof":
                    if r["address"] == address:
                        printf.success("YOU ARE UP!", r["message"])
                        valid_plot = False
                        for plot in plots.list_plots():
                            if plot["seed"] == str(r["seed"]):
                                client.sendall(prepare({"type": "submit", "address": address, "data": farmer.extract(plot["path"], r.get("index"))}))
                                valid_plot = True
                        if valid_plot == False:
                            client.sendall(prepare({"type": "reject", "address": address}))
                    else:
                        printf.neutral(r["message"])
                elif r["type"] == "error":
                    printf.error("Uh Oh!", r["message"])
                    try:
                        if r["break"]:
                            break
                    except Exception:
                        pass
                elif r["type"] == "suspense":
                    printf.suspense(r["message"])
                elif r["type"] == "winner":
                    printf.success("WOOHOO!", r["message"])
                else:
                    printf.neutral(r["message"])
            except json.JSONDecodeError:
                print("Received invalid JSON from server.")
        except Exception as e:
            print(f"Error receiving data: {e}")
            break
    print("Receiving thread stopped.")
    client.close()

def prepare(data):
    json_bytes = json.dumps(data).encode()
    msglen = struct.pack('>I', len(json_bytes))
    return msglen + json_bytes

def send_messages(client):
    global running, index, submit
    while running:
        try:
            pass
        except Exception as e:
            print(f"Error: {e}")
            break
    print("Sending thread stopped.")
    client.close()

def signal_handler(sig, frame):
    global running
    print("\nInterrupt received, stopping client...")
    running = False

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('tinydrive.certificator.ca', 3333))

    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()
    
    send_thread = threading.Thread(target=send_messages, args=(client,))
    send_thread.start()

    return client, receive_thread, send_thread

class Plots:
    def __init__(self, paths):
        self.plots = []
        for path in paths:
            if path == "":
                files = os.listdir(os.path.dirname(os.path.realpath(__file__)))
            else:
                files = os.listdir(path)
            for file in files:
                if file.endswith('.tiny'):
                    self.plots.append({"name": file, "path": os.path.join(path, file), "seed": file.replace(".tiny", "").replace("plot_", "")})

    def list_plots(self):
        seeds = []
        for plot in self.plots:
            if plot["seed"] in seeds:
                printf.error("Uh Oh!", "you have duplicate plots, please ensure that all plot seeds are different!")
            if not int(plot["seed"]) >= 0 and int(plot["seed"]) <= 24:
                printf.error("Uh Oh!", "you have invalid plots!")
        return self.plots
print("retrieving plots...")

plots = Plots(directories)
def update():
    global address, directories, plots

    with open('config.json', 'r') as f:
        user_data = json.load(f)

    address = user_data["username"]
    directories = user_data["directories"]
    plots = Plots(directories)

update()
plots.list_plots()

if address == "":
    username = input("enter your username:")
    with open('config.json', 'w') as f:
        json.dump({"username": username, "directories": directories}, f)


if __name__ == "__main__":
    print(Fore.CYAN + """
 _____ _            ______      _           
|_   _(_)           |  _  \    (_)          
  | |  _ _ __  _   _| | | |_ __ ___   _____ 
  | | | | '_ \| | | | | | | '__| \ \ / / _ \\
  | | | | | | | |_| | |/ /| |  | |\ V /  __/
  \_/ |_|_| |_|\__, |___/ |_|  |_| \_/ \___|
                __/ |                       
               |___/                        
""" + Fore.RESET)
    while True:
        print(f"Welcome {Fore.CYAN}{address}{Fore.RESET}! Enter {Fore.GREEN}'plot'{Fore.RESET} to start / edit plots, or {Fore.GREEN}'farm'{Fore.RESET} to start earning!" + Fore.RESET)
        command = input()
        print()
        if command == "farm":
            if len(plots.list_plots()) <= 0:
                printf.error("Uh Oh!", "you have no plots detected, please plot some files before farming!")
            else:
                signal.signal(signal.SIGINT, signal_handler)
                client, receive_thread, send_thread = start_client()
                print("you have started farming...")
                break
        elif command == "plot":
            dir = input("Enter a directory (eg. D:\\), leave empty for the directory this app is in:\n")
            while True:
                seed = int(input("Enter a seed (should be unique from your other plots) (0 - 12):\n"))
                if seed >= 0 and seed <= 24:
                    break
                else:
                    print(printf.error("Seed must be between or equal to 0 - 12", ""))
            farmer.plot({"address": address, "seed": seed}, f"{dir}{seed}.tiny")

            directories.append(dir)
            with open('config.json', 'w') as f:
                json.dump({"username": address, "directories": directories}, f)
            update()            
