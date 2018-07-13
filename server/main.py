#! usr/bin/python3
import FileServer
import time

server = FileServer.FileServer()
while True:
    server.listen()
