#!/usr/bin/env python
#
# Author: Martin Matusiak <numerodix@gmail.com>
# Licensed under the GNU Public License, version 2.
#
# revision 2 - add hostname lookup


import os, string, re, sys, time, thread


def main():
    network = None
    try:
        netinfo = check_network()
        (ip, mask) = netinfo
        network = ip + "/" + mask
    except Exception, e:
        print e
        print "Warning: No network connection found, scan may fail."

    if len(sys.argv) > 1:
        network = sys.argv[1]

    if not network:
        print "Error: No network range given."
        print "Usage:\t" + sys.argv[0] + " 10.0.0.0/24"
        sys.exit(1)


    if cmd_exists("nmap"):
        nmap_scan(network)
    else:
        print "Warning: nmap not found, falling back on failsafe ping scan method."
        ping_scan(network)


def nmap_scan(network):
    try:
        print "Using network: " + network
        cmd = 'nmap -n -sP -T4 ' + network + ' 2>&1'
        res = invoke(cmd)
        lines = res.split('\n')
        for i in lines:
            m = find('Host\s+\(?([0-9\.]+)\)?\s+appears to be up.', i)
            if m:
                print m, "\t", nslookup(m)
    except: pass


def ping_scan(network):
    iprange = find('(\w+\.\w+\.\w+)', network)
    print "Using network: " + iprange + ".0/24"
    for i in range(1,254):
        host = iprange + '.' + str(i)
        thread.start_new_thread(ping, (host, None))
        time.sleep(1)


def ping(host, dummy):
    try:
        cmd = 'ping -c3 -n -w300 ' + host + ' 2>&1'
        res = invoke(cmd)
        if "bytes from" in res: print host, "\t", nslookup(host)
    except: pass


def nslookup(ip):
    if cmd_exists("host"):
        cmd = 'host ' + ip + ' 2>&1'
        res = invoke(cmd)
        if "domain name pointer" in res:
            return res.split(" ")[4][:-2]
    return ""


def check_network():
    # cmd = "/sbin/ifconfig"
    cmd = "ipconfig"
    res = invoke(cmd)

    iface, ip, mask = None, None, None
    lines = res.split('\n')
    print lines
    for i in lines:
        
        # find interface
        m = find('^(\w+)\s+', i)
        if m: iface = m
        
        # ignore loopback interface
        if iface and iface != "lo":
            
            # find ip address
            m = find('inet addr:([0-9\.]+)\s+', i)
            if m: ip = m
            
            # find net mask
            m = find('Mask:([0-9\.]+)$', i)
            if m: mask = m

    if ip and mask:
        mask = mask_numerical(mask)
        return (ip, mask)


def mask_numerical(mask):
    segs = find('(\w+)\.(\w+)\.(\w+)\.(\w+)', mask)
    mask = 0
    adds = (0, 128, 192, 224, 240, 248, 252, 254, 255)
    for i in segs:
        for j in range(0, len(adds)):
            if int(i) == adds[j]:
                mask += j
    return str( mask )


def find(needle, haystack):
    try:
        match = re.search(needle, haystack)
        if len(match.groups()) > 1:
            return match.groups()
        else: 
            return match.groups()[0]
    except: pass


def invoke(cmd):
    (sin, sout) = os.popen2(cmd)
    return sout.read()


def cmd_exists(cmd):
    if invoke("which " + cmd + " 2>&1").find("no " + cmd) == -1:
        return True
    return False



if __name__ == "__main__":
    main()