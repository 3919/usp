import socket
import threading
import hashlib
import struct
import glob
import os
import stat

import configparser
import logging

from sockethelpers import *

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
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    
        self.socket.bind((host, port))
        self.config = configparser.ConfigParser()
        self.config.read(SETTINGS_PATH)
        self.checkConfig()

    def listen(self):
        self.socket.listen()
        conn, addr = self.socket.accept()
        conn.setblocking(True)
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
        
    def close(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()


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

        # In case of exception when accessing requested file
        # only header is sent with filesize = 0
        # Header is initialized with filesize = 0 so message
        # is ready to be sent
        except FileNotFoundError:
            logging.info('User requested {}, but file not found.'.format(self.filename))
            self.sendEmpty(sock)

        except PermissionError:
            logging.info('User requested {}, but got permission denied.'.format(self.filename))
            self.sendEmpty(sock)

        except IsADirectoryError:
            logging.info('User requested {}, but its directory, not file.'.format(self.filename))
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
                logging.info('Unknown request {} from {}:{}'.format(self.request,self.addr[0],self.addr[1]))
            else:
                self.calltable[self.request]()
                logging.info('{} {} request from {}:{}'.format(self.request,self.args,self.addr[0],self.addr[1]))
            self.socket.shutdown(socket.SHUT_RDWR)
        except socket.timeout:
            self.socket.shutdown(socket.SHUT_RDWR)
            logging.info('Client timed out from {}:{}'.format(self.addr[0],self.addr[1]))
        except ConnectionResetError as e:
            logging.info('{} from {}:{}'.format(e.__str__(),self.addr[0],self.addr[1]))

    # Reads to first space and stores request
    # with fetched value
    def fetchRequest(self):
        data = recvUntilByte(self.socket, b'\n', 2)
        data = data.decode('utf-8')
        idxSplit = data.find(' ')

        # space not found, so no args
        if idxSplit == -1:
            self.request = data
            self.args = None
            return
            
        # args ahead
        self.request = data[:idxSplit]
        self.args = data[idxSplit+1:]
    
    # Checks requets for path traversal
    def securePaths(self, paths):
        for idx, path in enumerate(paths):
            if not path.startswith('./'):
                paths[idx] = os.path.join(self.shared_path,path)
    
            # path traversal attempt ?
            # alternate way:
            # ''.join('/asdf/../qwer'.split('..')).replace('//','/')
            if '..' in path:
                return None

        return paths
                
    def getResponse(self):
        self.args = self.securePaths([self.args])
        for each in glob.glob(self.args[0]):
            f = File(each)
            f.send(self.socket)

    def getlistResponse(self):
        filelist = glob.glob(os.path.join(self.shared_path,'**'),recursive=True)

        for f in filelist:
            if os.path.isdir(f):
                continue

            # Relpath to shared path and also linux path convetion swap 
            relPath = os.path.relpath(f,self.shared_path).replace('\\','/')
            self.socket.sendall(bytes(relPath, 'utf-8'))
            self.socket.sendall(b'\0')
        self.socket.sendall(b'\n')

    def pingResponse(self):
        self.socket.sendall(b'PONG_USP %s\n' % self.shared_name.encode('utf-8'))

if __name__ == '__main__':
    print("This is only a module needed by main program.\n Do not run this directly, call main.py instead.")
