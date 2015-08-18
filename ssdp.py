
import uuid
import sys
import socket
import time
import struct

from threading import Thread

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900

class Client(object):
    """ssdp client. send notify msg when add. deal search all msg when requested"""
    def __init__(self):
        super(Client, self).__init__()
        self.uuid = str(uuid.uuid1())
        self.header_nt = "urn:schemes-upnp-org:device:Basic:1.0"
        self._build_notify_header()
        self._build_ok_header()

        self._start()

    def _start(self):
        heart_thread = Thread(target=self.__heart_loop)
        heart_thread.setDaemon(True)
        # heart_thread.start()

        control_thread = Thread(target=self.__server_loop)
        control_thread.setDaemon(True)
        control_thread.start()

    def _build_notify_header(self):
        headers = {}
        headers['HOST'] = "%s:%d" % (SSDP_ADDR, SSDP_PORT)
        headers['CACHE-CONTROL'] = "max-age=1800"
        headers['LOCATION'] = ""
        headers['NT'] = self.header_nt
        headers['NTS'] = "ssdp:alive"
        headers['SERVER'] = "python/" + str(sys.version_info.major) + "." + str(sys.version_info.minor) + " UPnP/1.0 product/version"  # We should give an actual product and version
        headers['USN'] = "uuid:" + self.uuid

        header_str = "NOTIFY * HTTP/1.1\r\n"
        for k, v in headers.iteritems():
            header_str += k + ": " + v + "\r\n"
            header_str += "\r\n"
        self.notify_header = header_str

    def _build_ok_header(self):
        headers = {}
        headers['DATE'] = time.time()
        headers['CACHE-CONTROL'] = "max-age=1800"
        headers['LOCATION'] = ""
        headers['ST'] = 'ssdp:all'
        headers['SERVER'] = "python/" + str(sys.version_info.major) + "." + str(sys.version_info.minor) + " UPnP/1.0 product/version"  # We should give an actual product and version
        headers['USN'] = "uuid:" + self.uuid

        header_str = "HTTP/1.1 200 OK\r\n"
        for k, v in headers.iteritems():
            header_str += "%s: %s\r\n" % (k, v)
            header_str += "\r\n"
        self.ok_header = header_str

    def __server_loop(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind(('', SSDP_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(SSDP_ADDR), socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        while True:
            read = self.socket.recv(1024)
            # parse header
            if not read:
                print "recv none."
                continue

            lines = read.splitlines()
            if len(lines) == 0 or len(lines[0]) < 8:
                print "lines is not proper"
                continue

            if not lines[0].startswith("M-SEARCH"):
                continue

            header = {}
            for line in lines:
                firstColon = line.find(':') 
                if firstColon is not -1:
                    header[line[:firstColon]] = line[firstColon + 2:]

            st = header['ST']
            print "st:", st
            if st != 'ssdp:all':
                print "only support all search now."
                continue
            self.socket.sendto(self.ok_header, (SSDP_ADDR, SSDP_PORT))



    def __heart_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            sock.sendto(self.notify_header, (SSDP_ADDR, SSDP_PORT))
            time.sleep(5)

class ControlPoint(object):
    """docstring for ControlPoint"""
    def __init__(self):
        super(ControlPoint, self).__init__()
        self._build_search_hearder()
        self.devices = []
        self._start()

    def _start(self):
        server_thread = Thread(target=self.__server_loop)
        server_thread.setDaemon(True)
        server_thread.start()

    def _build_search_hearder(self):
        headers = {}
        headers['HOST'] = "%s:%d" % (SSDP_ADDR, SSDP_PORT)
        headers['MAN'] = "ssdp:discover"
        headers['MX'] = 1
        headers['ST'] = "ssdp:all"

        header_str = "M-SEARCH * HTTP/1.1\r\n"
        for k, v in headers.iteritems():
            header_str += "%s: %s\r\n" % (k, v)
            header_str += "\r\n"
        self.search_header = header_str

    def search_devices(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(self.search_header, (SSDP_ADDR, SSDP_PORT))

    def __server_loop(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind(('', SSDP_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(SSDP_ADDR), socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            read = self.socket.recv(1024)
            # parse header
            if not read:
                print "recv none."
                continue

            lines = read.splitlines()
            if len(lines) == 0 or len(lines[0]) < 15:
                print "lines is not proper"
                continue

            if not lines[0].startswith("HTTP/1.1 200 OK"):
                continue

            header = {}
            for line in lines:
                firstColon = line.find(':') 
                if firstColon is not -1:
                    header[line[:firstColon]] = line[firstColon + 2:]

            usn = header['USN']
            print "found device:", usn
            self.devices.append(usn)

if __name__ == '__main__':
    c = Client()
    p = ControlPoint()

    p.search_devices()
    while True:
         time.sleep(10)

            