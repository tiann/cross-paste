
import uuid
import sys
import socket
import time
import struct

from threading import Thread

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900

# SSDP protocol's header, see http://tools.ietf.org/html/draft-cai-ssdp-v1-03
SEARCH_HEADER = "M-SEARCH * HTTP/1.1"
NOTIFY_HEADER = "NOTIFY * HTTP/1.1"
BYE_HEADER = ""
OK_HEADER = "HTTP/1.1 200 OK"

# search target; use cross-paste to indentify us.
_ST = "urn:schemes-upnp-org:device:CROSS-PASTE:1.0"

GUID_FILE = "guid"

GUID = str(uuid.uuid1())

def _build_msg(header, pair):
    '''build ssdp protocol msg, pair must be a key-value pair'''
    header += "\r\n"
    for k, v in pair.iteritems():
        header += "%s: %s\r\n" % (k, v)
    return header

# def _generate_guid():
#     import os
#     global GUID
#     if os.path.exists(GUID_FILE):
#         # guid file exist
#         with open(GUID_FILE) as f:
#             guid = f.readline()
#             if guid:
#                 GUID = guid
#             print "guid:", GUID
#     else:
#         with open(GUID_FILE, "w") as f:
#             f.write(GUID)

class Device(object):
    """ssdp client. send notify msg when add. deal search all msg when requested"""
    def __init__(self):
        super(Device, self).__init__()
        self.uuid = str(uuid.uuid1())
        self.uninstalled = False
        self._build_notify_msg()
        self._build_bye_msg()
        self._build_ok_msg()
        
        self._start_server()

    def _start_server(self):
        """deal the search request!"""
        self.control_thread = Thread(target=self.__server_loop)
        self.control_thread.start()

    def heart_beating(self):
        """announce the presentense of ourselves"""
        heart_thread = Thread(target=self.__heart_loop)
        heart_thread.setDaemon(True)
        heart_thread.start()

    def _build_notify_msg(self):
        headers = {}
        headers['HOST'] = "%s:%d" % (SSDP_ADDR, SSDP_PORT)
        headers['CACHE-CONTROL'] = "max-age=1800"
        headers['LOCATION'] = ""
        headers['NT'] = _ST
        headers['NTS'] = "ssdp:alive"
        headers['SERVER'] = "python/" + str(sys.version_info.major) + "." + str(sys.version_info.minor) + " UPnP/1.0 product/version"  # We should give an actual product and version
        headers['USN'] = "uuid:" + GUID

        self.notify_header = _build_msg(NOTIFY_HEADER, headers)

    def _build_bye_msg(self):
        headers = {}
        headers['HOST'] = "%s:%d" % (SSDP_ADDR, SSDP_PORT)
        headers['CACHE-CONTROL'] = "max-age=1800"
        headers['LOCATION'] = ""
        headers['NT'] = _ST
        headers['NTS'] = "ssdp:byebye"
        headers['SERVER'] = "python/" + str(sys.version_info.major) + "." + str(sys.version_info.minor) + " UPnP/1.0 product/version"  # We should give an actual product and version
        headers['USN'] = "uuid:" + GUID

        self.bye_msg = _build_msg(NOTIFY_HEADER, headers)

    def _build_ok_msg(self):
        headers = {}
        headers['DATE'] = time.time()
        headers['CACHE-CONTROL'] = "max-age=1800"
        headers['LOCATION'] = ""
        headers['ST'] = _ST
        headers['SERVER'] = "python/" + str(sys.version_info.major) + "." + str(sys.version_info.minor) + " UPnP/1.0 product/version"  # We should give an actual product and version
        headers['USN'] = "uuid:" + GUID

        self.ok_msg = _build_msg(OK_HEADER, headers)

    def __server_loop(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind(('', SSDP_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(SSDP_ADDR), socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        while True:
            read, address = self.socket.recvfrom(1024)
            # parse header
            if not read:
                continue

            lines = read.splitlines()

            if not lines[0].startswith(SEARCH_HEADER):
                continue

            header = {}
            for line in lines:
                firstColon = line.find(':') 
                if firstColon is not -1:
                    header[line[:firstColon]] = line[firstColon + 2:]

            st = header['ST']
            if st != _ST:
                continue
            self.socket.sendto(self.ok_msg, (SSDP_ADDR, SSDP_PORT))

    def __heart_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # sock.bind((IFACE, SSDP_PORT))
        while True:
            sock.sendto(self.notify_header, (SSDP_ADDR, SSDP_PORT))
            time.sleep(5)

    def uninstall(self):
        self.uninstalled = True
        # todo:send byebye msg.

class ControlPoint(object):
    """docstring for ControlPoint"""
    def __init__(self):
        super(ControlPoint, self).__init__()
        self._build_search_msg()
        self.uninstalled = False
        self.devices = []
        self._start()

    def _start(self):
        server_thread = Thread(target=self.__server_loop)
        server_thread.start()

    def _build_search_msg(self):
        headers = {}
        headers['HOST'] = "%s:%d" % (SSDP_ADDR, SSDP_PORT)
        headers['MAN'] = "ssdp:discover"
        headers['MX'] = 1
        headers['ST'] = _ST

        self.search_header = _build_msg(SEARCH_HEADER, headers)

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

        while not self.uninstalled:
            read, address = self.socket.recvfrom(1024)
            # parse header
            if not read:
                continue

            lines = read.splitlines()
            if not lines[0].startswith(OK_HEADER):
                continue

            header = {}
            for line in lines:
                firstColon = line.find(':') 
                if firstColon is not -1:
                    header[line[:firstColon]] = line[firstColon + 2:]
            print header
            if header['USN'] != "uuid:%s" % GUID:
                print "found device:", address
                self.devices.append(address)

    def uninstall(self):
        self.uninstalled = True

# _generate_guid()

if __name__ == '__main__':
    c = Device()
    p = ControlPoint()
    p.search_devices()


            