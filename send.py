import netifaces, socket

PORT = 7890

def get_all_broadcasr_address():
    ifaces = netifaces.interfaces()
    ifaces_addrs = [netifaces.ifaddresses(x) for x in ifaces]
    for x in ifaces_addrs:
        addr = x.get(netifaces.AF_INET)
        if addr:
            for add in addr:
                broadcast_addr = add.get('broadcast')
                if broadcast_addr: yield broadcast_addr

def send():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
    for i in get_all_broadcasr_address():
        s.sendto("hello", (i, PORT))
    print s.recv(1024)
if __name__ == '__main__':
    send()