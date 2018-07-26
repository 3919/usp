import time
import socket

class ClientTimedOut(Exception):
    pass

def recvUntilByte(sock, untilch, timeout=0):
    lastUpdate =  time.time()
    currentTime = lastUpdate
    data_= b''
    data = b''
    ch = b''
    while True:
        data_ = sock.recv(64)

        if len(data_) > 0:
            lastUpdate = time.time()
            currentTime = lastUpdate
        elif currentTime - lastUpdate > timeout:
            sock.shutdown(socket.SHUT_RDWR)
            raise ClientTimedOut("Clinet has timed out.")

        if b'\n' in data_:
            data += data_.split(b'\n')[0]
            break

        data += data_
        currentTime = time.time()

    return data

def recvUntilSize(socket, size, timeout=0):
    lastUpdate =  time.time()
    currentTime = lastUpdate
    data = b''
    ch = b''
    i = 0
    while i < size:
        data_ = socket.recv(size)

        if len(data_) > 0:
            lastUpdate = time.time()
            currentTime = lastUpdate
        elif currentTime - lastUpdate > timeout:
            sock.shutdown(socket.SHUT_RDWR)
            raise ClientTimedOut("Clinet has timed out.")

        i+=len(data_)
        data += data_
        currentTime = time.time()

    return data
