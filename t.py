import pyperclip
import socket
import threading
import multiprocessing
import time
import sys
import Queue

_PORT = 9990
_SCAN_RANGE = range(2, 255)

class Server(object):
    """docstring for Server"""
    def __init__(self):
        super(Server, self).__init__()
        
        
    def __call__(self):
        # listen broadcast
        # start server
        threading.Thread(target=self.recv_broadcast).start()
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._host = "0.0.0.0"
        self.socket_server.bind((self._host, _PORT))
        self.socket_server.listen(5)
        while True:
            conn, address = self.socket_server.accept()
            print address, "connected."
            txt = conn.recv(1024)
            if txt:
                self.txt = txt.strip()
                pyperclip.copy(self.txt)
            else:
                print "txt is empty."

    def recv_broadcast(self):
        addr = ('', _PORT)
        broadcast_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        broadcast_server.bind(addr)
        while True:
            data, addr = broadcast_server.recvfrom(1024)
            print "From addr: '%s', msg: '%s'" % (addr[0], data)
            if "stop" == data:
                break
        broadcast_server.close()

class Client(object):
    """docstring for Client"""
    def __init__(self):
        super(Client, self).__init__()
        self.last_clipboard_txt = pyperclip.paste()
        
    def __call__(self):
        # broadcast me
        self.broadcast_me()
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = self.socket_client.connect_ex(("172.18.187.12", _PORT))        
        if not result:
            print "connect failed."
            return
        # listen clipboard change
        while True:
            txt = pyperclip.paste()
            if txt and txt != self.last_clipboard_txt:
                print "clipboard changed: %s -> %s" % (self.last_clipboard_txt, txt)
                self.last_clipboard_txt = txt
                self.socket_client.send(self.last_clipboard_txt)
            time.sleep(1)

    def broadcast_me(self):
        addr = (("<broadcast>", _PORT))
        broadcast_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        while True:
            broadcast_client.sendto("cross-paste", addr)
            time.sleep(5)
        broadcast_client.close()

if __name__ == '__main__':
    multiprocessing.Process(target=Server()).start()
    multiprocessing.Process(target=Client()).start()
