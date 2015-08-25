#! /usr/bin/env python
import json
import base64
import socket
import time
import threading
import multiprocessing
import sys

import netifaces
import pyperclip

_VER = "0.1.0"

PROTOCOL_HEADER = "do not reply! do not reply!!"

PORT = 7890

DISCOVER_PORT = 7891

"""
protocol: json
encode: base64

{
    ver: "0.1.0",
    host: "tianweishu-D1",
    header: "do not reply! do not reply!!",
    msg: "anything you want to say"
}
"""

ALL_IP_ADDR = set()
ALL_BROADCAST_ADDR = set()

def get_all_broadcast_address():
    ifaces = netifaces.interfaces()
    ifaces_addrs = [netifaces.ifaddresses(x) for x in ifaces]
    for x in ifaces_addrs:
        addr = x.get(netifaces.AF_INET)
        if addr:
            for add in addr:
                broadcast_addr = add.get('broadcast')
                ip_addr = add.get('addr')
                if broadcast_addr and ip_addr: yield ip_addr, broadcast_addr

# get all ip addr & broadcast addr

for addr, broadcast in get_all_broadcast_address():
    ALL_IP_ADDR.add(addr)
    ALL_BROADCAST_ADDR.add(broadcast)

def encode(src):
    """
    return a encode str
    """
    src_str = json.dumps(src)
    return base64.encodestring(src_str)

def decode(src):
    src_str = base64.decodestring(src)
    return json.loads(src_str)

def pprint(src):
    print src
    sys.stdout.flush()

class Peer(object):
    """docstring for Peer"""
    def __init__(self, ip, host=None):
        super(Peer, self).__init__()
        self.ip = ip
        self.host = host if not host else self.ip

    def __repr__(self):
        return "ip=%s, host=%s" % (self.ip, self.host)
        

class Client(object):
    """docstring for Server"""
    def __init__(self):
        super(Client, self).__init__()
        self.peers = []
        self.default_peer = None

    def __peer_discovery_loop(self):
        """
        listen to the broadcast addr, find peers
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', DISCOVER_PORT))
        while True:
            raw_data, addr = s.recvfrom(1024)
            if addr[0] in ALL_IP_ADDR:
                # ourself, ignore
                pprint("ourselves")
                continue

            pprint((raw_data, addr))
            data = decode(raw_data)
            header = data.get('header')
            if header and header == PROTOCOL_HEADER:
                # peer found!!
                p = Peer(addr[0], host=data.get('host'))
                self.peers.append(p)

                # if no default peer, set it
                if not self.default_peer:
                    self.default_peer = p
                pprint("peer: %s found." % p)

            time.sleep(10)

    def __call__(self):
        # threading.Thread(target=self.__peer_discovery_loop).start()
        self.__peer_discovery_loop()

class Server(object):
    """docstring for Server"""
    def __init__(self):
        super(Server, self).__init__()
        self.shutdown = False

    def start_server(self):
        print "start server"
        t = threading.Thread(target=self.__server_loop)
        # t.setDaemon(True)
        t.start()

    def __server_loop(self):
        """
        listen to the paste port, comminute with paste client.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
        s.bind(('', PORT))
        s.listen(5)
        while not self.shutdown:
            conn, addr = s.accept()
            print addr, "connected."
            txt = conn.recv(1024)
            if txt:
                txt = txt.strip()
                pyperclip.copy(txt)
            else: print "txt is empty:", txt
        s.close()
        print "shutdown..."

    def __broadcast_us(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = {"ver": _VER, "header": PROTOCOL_HEADER, "host": socket.gethostname(), "msg": "remain"}
        msg_str = encode(msg)
        while True:
            try:
                for broadcast_addr in ALL_BROADCAST_ADDR:
                    print "sendto", broadcast_addr
                    s.sendto(msg_str, (broadcast_addr, DISCOVER_PORT))

                time.sleep(5)
            except KeyboardInterrupt:
                self.shutdown = True
                break
        s.close()
        print "shudown"

    def __call__(self):
        self.__broadcast_us()
        self.start_server()

if __name__ == '__main__':
    # print ALL_BROADCAST_ADDR, ALL_IP_ADDR
    server_process = multiprocessing.Process(target=Server())
    client_process = multiprocessing.Process(target=Client())
    server_process.start()
    client_process.start()

    client_process.join()
    server_process.join()

