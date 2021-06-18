from uuid import getnode
from binascii import unhexlify
import socket

def get_mac():
    mac = str(hex(getnode()))
    mac = mac[2:]
    while len(mac) < 12 :
        mac = '0' + mac
    macb = b''
    for i in range(0, 12, 2) :
        m = int(mac[i:i + 2], 16)
        macb += unhexlify(format(m, '02x'))
    return macb

def make_packet(isRequest: bool, seconds:int, transaction_identifier: int, mac_address:bytearray, offered_ip:bytearray= None):
    op_code = (isRequest and 1) or 2 # 1 for a request 2 for response

    packet = b''
    packet += unhexlify(format(op_code, '02x'))
    packet += unhexlify(format(1, '02x')) # Hardware type 1 for ethernet architecture
    packet += unhexlify(format(6, '02x')) # Mac address length 6 for ethernet
    packet += unhexlify(format(0, '02x')) # Hops
    packet += unhexlify(format(transaction_identifier, '08x'))
    packet += unhexlify(format(seconds, '04x')) # Seconds passed
    packet += unhexlify(format(1, '04x')) # Flags set to 1 to indicate broadcast
    packet += b'\x00\x00\x00\x00' #Client IP address: 0.0.0.0
    packet += offered_ip or b'\x00\x00\x00\x00'  #Your (client) IP address: 0.0.0.0
    packet += b'\x00\x00\x00\x00'   #Next server IP address: 0.0.0.0
    packet += b'\x00\x00\x00\x00'   #Relay agent IP address: 0.0.0.0
    packet += mac_address # Client mac address
    packet += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' #Client hardware address padding
    packet += b'\x00' * 67  #Server host name not given
    packet += b'\x00' * 125 #Boot file name not given
    packet += b'\x63\x82\x53\x63'   #Magic cookie: DHCP

    return packet


def create_socket(ip:str, port:int):
    created_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    created_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    created_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    created_socket.bind((ip, port))

    return created_socket


def get_all_interfaces():
    interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
    all_ips = [ip[-1][0] for ip in interfaces]
    all_ips = set(all_ips)
    return(list(all_ips))
