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
