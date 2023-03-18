import random, hashlib
from Crypto.Hash import SHAKE128

def generate(amount, public_key):
    random.seed(hashlib.sha256(public_key.encode('utf-8')).hexdigest())
    plot_index = [random.getrandbits(32) for i in range(amount)]

    for plots in range(0, amount):
        shake = SHAKE128.new()
        shake.update(bytes(plot_index[plots]))

        with open(str(plot_index[plots]), "x") as text_file:
            text_file.write(shake.read(1073741824).hex())

def check_plot_file():
    chunk = random.randint(0, 1073741824 - 32)
    print(shake.read(1073741824).hex()[chunk:chunk + 32])

generate(1, "jerrbearisawsome")
