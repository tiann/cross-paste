#! /usr/bin/env python

import pyperclip
import socket
import threading
import multiprocessing
import time
import sys
import Queue

import ssdp

_PORT = 9990
_SCAN_RANGE = range(2, 255)

class Server(object):
    """docstring for Server"""
    def __init__(self):
        super(Server, self).__init__()
        self.device = ssdp.Device()
        
    def __call__(self):
        # listen broadcast
        # start server
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.bind(('', _PORT))
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
        self.last_clipboard_txt = pyperclip.paste()
        self.control_point = ssdp.ControlPoint()

    def __call__(self):
        # broadcast me
        while len(self.control_point.devices) == 0:
            print "no device found."
            time.sleep(5)
            self.control_point.search_devices()

        default_address = list(self.control_point.devices)[0]
        print "connect to address:", default_address
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = self.socket_client.connect_ex((default_address, _PORT))        
        if result:
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

if __name__ == '__main__':
    threading.Thread(target=Server()).start()
    threading.Thread(target=Client()).start()