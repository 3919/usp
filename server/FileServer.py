import socket
import threading
import hashlib
import struct
import glob
import os

import configparser
import logging

REQUESTS = ['GET', 'GETLIST', 'PING']
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR,'settings','settings.ini')
MAX_REQUEST_LEN = 1024

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=os.path.join(BASE_DIR,'logs','server.log'),
                    filemode='w')

class ConfigError(Exception):
    pass

# CONFIG FIELDS:
# [main]
# shared_path  -> path to shared directory
# shared_name  -> nickname
class FileServer():
    def __init__(self, port = 53025, host = ''):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.config = configparser.ConfigParser()
        self.config.read(SETTINGS_PATH)
        self.checkConfig()

    def listen(self):
        self.socket.listen()
        conn, addr = self.socket.accept()
        logging.info('Got connection from {}:{}'.format(addr[0],addr[1]))
        session = Session(conn, addr, self.config['main']['shared_path'], self.config['main']['shared_name'])
        job = threading.Thread(target=session.handleSession)
        job.start()

    def checkConfig(self):
        # Check main section
        try:
            self.config['main']
        except KeyError:
            msg = 'Error: main section missing in {}'.format(os.path.join('settings','settings.ini'))
            logging.error(msg)
            raise ConfigError(msg)

        # Check shared_path
        try:
            if not os.path.exists(os.path.abspath(self.config['main']['shared_path'])):
                raise ConfigError('Given path in shared_path@main is invalid')
        except KeyError:
            msg = 'Error: shared_path@main missing in {}'.format(os.path.join('settings','settings.ini'))
            logging.error(msg)
            raise ConfigError(msg)

        # Check shared_name
        try:
            self.config['main']['shared_name']
        except KeyError:
            msg = 'Error: shared_name@main missing in {}'.format(os.path.join('settings','settings.ini'))
            logging.error(msg)
            raise ConfigError(msg)


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
            with open(self.filename, 'rb') as f:
                self._filedata = f.read()
                self.header.filesize = len(self._filedata)
                self.header.sha256_hash = hashlib.sha256(self._filedata).digest()
                sock.sendall(self.header.pack())
                f.seek(0)
                sock.sendfile(f)

        # In case of File Not Found only header is sent
        # Header is initialized with filesize = 0 so message
        # is ready to be sent
        except FileNotFoundError:
            logging.info('User requested {}, but file not found.'.format(self.filename))
            self.sendEmpty(sock)

        except PermissionError:
            logging.info('User requested {}, but got permission denied.'.format(self.filename))
            self.sendEmpty(sock)

    def sendEmpty(self, sock):
            # Redundant operation, just for security
            # to be sure initilization of file header class never changes in future
            self.header.filesize = 0
            self.header.sha256_hash = hashlib.sha256().digest()

            sock.sendall(self.header.pack())


class Session():
    def __init__(self, sock, addr, shared_path, shared_name):
        self.socket = sock
        self.socket.settimeout(5)
        self.addr = addr
        self.request = None
        self.args = None
        self.shared_path = shared_path
        self.shared_name = shared_name
        self.calltable = dict(zip(REQUESTS,[self.getResponse, self.getlistResponse, self.pingResponse]))

    def handleSession(self):
        try:
            self.fetchRequest()
            if self.request not in REQUESTS:
                logging.info('Unknown request from {}:{}'.format(self.addr[0],self.addr[1]))
            else:
                self.calltable[self.request]()
                logging.info('{} {} request from {}:{}'.format(self.request,self.args,self.addr[0],self.addr[1]))
            self.socket.close()
        except socket.timeout:
            self.socket.close()
            logging.info('Client timed out from {}:{}'.format(self.addr[0],self.addr[1]))
        except ConnectionResetError as e:
            logging.info('{} from {}:{}'.format(e.__str__(),self.addr[0],self.addr[1]))

    # Reads to first space and stores request
    # with fetched value
    def fetchRequest(self):
        data = recvUntilByte(self.socket, b'\n')
        data = data.decode('utf-8')
        data = data.split(' ')
        self.request = data[0]
        self.args = data[1:]
    
    # Checks requets for path traversal
    def securePaths(self, paths):
        for idx, path in enumerate(paths):
            if not path.startswith('./'):
                paths[idx] = os.path.join(self.shared_path,path)
    
            # path traversal attempt ?
            # alternate way:
            # ''.join('/asdf/../qwer'.split('..')).replace('//','/')
            if path.__contains__('..'):
                return None

        return paths
                
    def getResponse(self):
        self.args = self.securePaths(self.args)
        f = File(self.args[0])
        f.send(self.socket)

    def getlistResponse(self):
        self.args = self.securePaths(self.args)

        filelist = glob.glob(os.path.join(self.shared_path,'**'),recursive=True)
        for f in filelist:
            self.socket.sendall(bytes(os.path.relpath(f,self.shared_path),'utf-8'))
            self.socket.sendall(b'\0')
        self.socket.sendall(b'\n')

    def pingResponse(self):
        self.socket.sendall(b'PONG_USP %s\n' % self.shared_name.encode('utf-8'))

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
        
