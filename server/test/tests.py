import socket
import time
import struct
import hashlib

HOST = '192.168.1.5' 
PORT =  53025
PONG_XOR_VAL = 0x13371337
PING_CHECK_VAL_BYTES = b'\x11\x22\x33\x44'
PING_CHECK_VAL = 0x44332211
REQUESTS = ['GET testfile.txt\n', 'GETLIST\n', 'PING \x11\x22\x33\x44\n']

class FileHeader():
    def __init__(self):
        self.filesize = 0
        self.sha256_hash = 0

    def unpack(self, data):
        self.filesize, s1, s2, s3, s4 = struct.unpack('<QQQQQ',data)
        s1 <<= 192
        s2 <<= 128
        s3 <<= 64
        self.sha256_hash = s1 | s2 | s3 | s4

def unpacksha(sha):
    s1, s2, s3, s4 = struct.unpack('QQQQ',hashlib.sha256(sha).digest())
    s1 <<= 192
    s2 <<= 128
    s3 <<= 64
    return s1 | s2 | s3 | s4

def checkFileHash(filename, s1):
    f = open(filename, 'rb')
    s2 = unpacksha(f.read())
    return (s1 == s2)

def recvUntil(untilch):
    data = b''
    ch = b''
    i = 0
    while True:
        ch = s.recv(1)

        if ch == untilch:
            break

        data += ch

    return data

def timeoutTest(s):
    s.sendall(bytes(REQUESTS[0][:4],'utf-8'))
    time.sleep(7)

def getTest(s):
    s.sendall(bytes(REQUESTS[0],'utf-8'))
    
    filehead = FileHeader()
    filehead.unpack(s.recv(40))

    # Displaying info file header
    print("Filesize: {} bytes\nsha256: {}".format(
        filehead.filesize, hex(filehead.sha256_hash)))

    # Saving file
    f = open('out','wb')
    f.write(s.recv(filehead.filesize))
    f.close()
    
    # Checking hash
    print("is ok: ",checkFileHash('out', filehead.sha256_hash))


def getlistTest(s):
    s.sendall(bytes(REQUESTS[1],'utf-8'))
    data = recvUntil(b'\n')
    data = data.split(b'\0')
    for entry in data:
        print(entry.decode('utf-8','ignore'))
    
def pingTest(s):
    s.sendall(bytes(REQUESTS[2],'utf-8'))
    data = recvUntil(b'\n')
    data = data.split(b' ')
    print('MSG: {}'.format(data[0].decode('utf-8')))
    isOk = ((struct.unpack('L', data[1])[0] ^ PONG_XOR_VAL) == PING_CHECK_VAL)
    print(isOk)

def pingTestSimple(s):
    s.sendall(bytes(REQUESTS[2],'utf-8'))
    data = recvUntil(b'\n')
    print('MSG: {}'.format(data.decode('utf-8')))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    print("Sending GET packet test.")
    getTest(s)

    time.sleep(1)
    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    print("\n\nSending GETLIST packet test.")
    getlistTest(s)

    time.sleep(1)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    print("\n\nSending PING packet test.")
    pingTestSimple(s)

    time.sleep(1)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    print("\n\nStarting timeout test.")
    try:
        timeoutTest(s)
    except:
        print('Exception while timeout test occured')



