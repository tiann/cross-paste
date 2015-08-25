import socket
import struct

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
# s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
s.bind(('',7890))

print "Listen on the port 12345......"
while True:
    try:
        data, addr = s.recvfrom(8192)
        print "Receive data from:", addr
        s.sendto("I'm here BOSS!",addr)
    except (KeyboardInterrupt,SystemExit):
        raise
    # print e
    # sock.close()

