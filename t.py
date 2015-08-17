import pyperclip
import socket
import threading
import multiprocessing
import time
import sys

_PORT = 7890

class Server(object):
    """docstring for Server"""
    def __init__(self):
        super(Server, self).__init__()
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._host = "0.0.0.0"
        
    def __call__(self):
        # start server
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


class Client(object):
    """docstring for Client"""
    def __init__(self):
        super(Client, self).__init__()
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.last_clipboard_txt = pyperclip.paste()
        
    def __call__(self):
        self.socket_client.connect(("172.18.187.12", _PORT))        
        # listen clipboard change
        while True:
            txt = pyperclip.paste()
            if txt and txt != self.last_clipboard_txt:
                print "clipboard changed: %s -> %s" % (self.last_clipboard_txt, txt)
                self.last_clipboard_txt = txt
                self.socket_client.send(self.last_clipboard_txt)
            time.sleep(1)

if __name__ == '__main__':
    # threading.Thread(target=Server()).start()
    threading.Thread(target=Client()).start()