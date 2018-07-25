import socket
import struct
import hashlib

HOST = '127.0.0.1'
PORT =  53025
PONG_XOR_VAL = 0x13371337
PING_CHECK_VAL_BYTES = b'\x11\x22\x33\x44'
PING_CHECK_VAL = 0x44332211
REQUESTS = ['GET testfile\n', 'GETLIST\n', 'PING \x11\x22\x33\x44\n']

serverFileList = []

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

def recvUntilByte(socket, untilch):
    data = b''
    ch = b''
    i = 0
    while True:
        ch = socket.recv(1)

        if ch == untilch:
            break

        data += ch

    return data

def recvUntilSize(socket, size):
    data = b''
    ch = b''
    i = 0
    while i < size:
        data_ = socket.recv(size)
        i+=len(data_)
        data += data_

    return data

def timeoutTest(s):
    s.sendall(bytes(REQUESTS[0][:4],'utf-8'))
    while True:
        s.recv(1024)

def getTest(s, filename=b'kannakamui.png\n'):
    print('Asking for {}'.format(filename))

    request = filename

    if filename == b'':
        filename = b'empty_name'

    # make sure packet have its end
    if not request.endswith(b'\n'):
       request += b'\n' 

    if not request.startswith(b'GET '):
        request = b'GET ' + request

    s.sendall(request)
    
    filehead = FileHeader()
    filehead.unpack(recvUntilSize(s,40))

    # Displaying info file header
    print("Filesize: {} bytes\nsha256: {}".format(
        filehead.filesize, hex(filehead.sha256_hash)))

    # Saving file
    f = open(filename,'wb')
    i = 0
    while i < filehead.filesize:
        data = recvUntilSize(s, filehead.filesize)
        f.write(data)
        i+=len(data)
    f.close()
    
    # Checking hash
    print("is ok: {}\n".format(checkFileHash(filename, filehead.sha256_hash)))

def getTestAsterix(s):
    print('Not implemented yet')
    return
    s.sendall(bytes(REQUESTS[3],'utf-8'))
    
    filehead = FileHeader()
    filehead.unpack(recvUntilSize(s,40))

    # Displaying info file header
    print("Filesize: {} bytes\nsha256: {}".format(
        filehead.filesize, hex(filehead.sha256_hash)))

    # Saving file
    f = open('tmp','wb')
    i = 0
    while i < filehead.filesize:
        data = recvUntilSize(s, filehead.filesize)
        f.write(data)
        i+=len(data)
    f.close()
    
    # Checking hash
    print("is ok: ",checkFileHash('tmp', filehead.sha256_hash))

def getlistTest(s):
    s.sendall(bytes(REQUESTS[1],'utf-8'))
    data = recvUntilByte(s, b'\n')
    data = data.split(b'\0')
    for entry in data:
        serverFileList.append(entry)
        print(entry.decode('utf-8','ignore'))
    
def pingTest(s):
    s.sendall(bytes(REQUESTS[2],'utf-8'))
    data = recvUntilByte(s, b'\n')
    data = data.split(b' ')
    print('MSG: {}'.format(data[0].decode('utf-8')))
    isOk = ((struct.unpack('L', data[1])[0] ^ PONG_XOR_VAL) == PING_CHECK_VAL)
    print(isOk)

def pingTestSimple(s):
    s.sendall(bytes(REQUESTS[2],'utf-8'))
    data = recvUntilByte(s, b'\n')
    print('MSG: {}'.format(data.decode('utf-8')))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    print("\n\nSending GETLIST packet test.")
    getlistTest(s)

for filename in serverFileList:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        
        print("Sending GET packet test.")
        getTest(s, filename)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    print("\n\nSending PING packet test.")
    pingTestSimple(s)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    
    print("Sending GET packet test with asterix.")
    getTestAsterix(s)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.setblocking(True)
    s.settimeout(1)
    
    print("\n\nStarting timeout test.")
    try:
        timeoutTest(s)
    except socket.timeout:
        print("Ok, got timed out.")

