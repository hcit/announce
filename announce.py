import sys
import string
import pprint
from scapy.all import *

def detect_dhcp_request(packet):
    pprint(packet)
    print packet

sniff(filter="arp or (udp and (port 67 or 68))", prn=detect_dhcp_request, store=0)
