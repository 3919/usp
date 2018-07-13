from array import array
import socket
import threading
import sys
import hashlib
import struct
import glob

REQUESTS = ['GET', 'GETLIST', 'PING']
MAX_REQUEST_LEN = 1024

class FileServer():
    def __init__(self, port = 53025, host = ''):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))

    def listen(self):
        self.socket.listen()
        conn, addr = self.socket.accept()
        print('New user connected!')
        session = Session(conn)
        job = threading.Thread(target=session.handleSession)
        job.start()


class FileHeader():
    def __init__(self):
        self.filesize = 0
        self.sha256_hash = 0

    def pack(self):
        return struct.pack('<Q',self.filesize) + self.sha256_hash


class File():
    def __init__(self, filename):
        self.header = FileHeader()
        self.filename = filename
        self._filedata = None

    def send(self, sock):
        try:
            f = open(self.filename, 'rb')
            self._filedata = f.read()
            self.header.filesize = len(self._filedata)
            self.header.sha256_hash = hashlib.sha256(self._filedata).digest()
            sock.sendall(self.header.pack())
            sock.sendfile(open(self.filename, 'rb'))

        except FileNotFoundError:
            print('User requested {}, but file not found.'.format(self.filename))


class Session():
    def __init__(self, sock):
        self.socket = sock
        self.request = None
        self.args = None
        self.calltable = dict(zip(REQUESTS,[self.getResponse, self.getlistResponse, self.pingResponse]))

    def handleSession(self):
        try:
            self.fetchRequest()
            if self.request not in REQUESTS:
                print('Unknown request: {}'.format(self.request))
            else:
                self.calltable[self.request]()
        except ConnectionResetError:
            print('Client closed connection')
            return

    # Reads to first space and stores request
    # with fetched value
    def fetchRequest(self):
        data = b''
        ch = ''
        i = 0
        while True:
            ch = self.socket.recv(1)
            i += 1
            if i == MAX_REQUEST_LEN:
                self.request = ['']
                return

            if ch == b'\n':
                break

            data += ch
        data = data.decode('utf-8', 'ignore')
        data = data.split(' ')
        self.request = data[0]
        self.args = data[1:]
    
    # Checks requets for path traversal
    def securePaths(self, paths):
        for idx, path in enumerate(paths):
            if not path.startswith('./'):
                paths[idx] = './' + path
    
            # path traversal attempt ?
            # alternate way:
            # ''.join('/asdf/../qwer'.split('..')).replace('//','/')
            if path.__contains__('..'):
                paths[idx] = ''

        return paths
                
    def getResponse(self):
        self.args = self.securePaths(self.args)
        f = File(self.args[0])
        f.send(self.socket)
        self.socket.close()

    def getlistResponse(self):
        self.args = self.securePaths(self.args)

        filelist = glob.glob('*')
        for f in filelist:
            self.socket.sendall(bytes(f,'utf-8'))
            self.socket.sendall(b'\0')
        self.socket.sendall(b'\n')
        self.socket.close()

    def pingResponse(self):
        self.socket.sendall(b'PONG_USP\n')

    def logRequest(self):
        pass
