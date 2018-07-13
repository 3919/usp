import socket

class SuperSocket(socket.socket):
    def recvUntilByte(self, endch):
        data = b''
        ch = b''
        i = 0
        while True:
            ch = super().recv(1)

            if ch == endch:
                break

            data += ch

        return data

    def recvUntilSize(self, sz):
        data = b''
        ch = b''
        i = 0
        while i < sz:
            data_ = super().recv(sz)
            i+=len(data_)
            data += data_

        return data

    def accept(self):
        conn, addr = super().accept()

        return conn, addr

socket.socket.recvUntilByte = SuperSocket.recvUntilByte.__get__(socket.socket, socket.socket.__class__)
socket.socket.recvUntilSize = SuperSocket.recvUntilSize.__get__(socket.socket, socket.socket.__class__)
