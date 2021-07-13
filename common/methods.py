from time import time
from uuid import getnode
from binascii import unhexlify, hexlify
import socket
import common.constants as c

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

def get_mac_str(mac:bytearray):
    mac_str = []
    mac = hexlify(mac).decode(c.ENCODING)
    for mac_index in range(0, 12, 2):
        mac_str.append(str(mac[mac_index:mac_index+2]))

    return ':'.join(mac_str)

def ip_str_to_byte(ip:str):
    ip_str = ''
    for ip_part in ip.split('.'):
        ip_str += format(int(ip_part), '02x')

    return unhexlify(ip_str)

def ip_byte_to_str(ip:bytes):
    ip_b = []
    for ip_index in range(0, 8, 2):
        ip_b.append(str(int(ip[ip_index:ip_index+2], 16)))

    return '.'.join(ip_b)

def make_packet(isRequest: bool, seconds:int, transaction_identifier: int, mac_address:bytearray, offered_ip:bytearray= None):
    op_code = (isRequest and 1) or 2 # 1 for a request 2 for response
    hostname_opcode = unhexlify(format(12, '02x'))
    name = unhexlify(''.join(format(ord(x), '02x') for x in socket.gethostname()))
    name_len = unhexlify(format(len(name), '02x'))

    packet = b''
    packet += unhexlify(format(op_code, '02x'))
    packet += unhexlify(format(1, '02x')) # Hardware type 1 for ethernet architecture
    packet += unhexlify(format(6, '02x')) # Mac address length 6 for ethernet
    packet += unhexlify(format(1, '02x')) # Hops
    packet += unhexlify(format(transaction_identifier, '08x'))
    packet += unhexlify(format(seconds, '04x')) # Seconds passed
    packet += unhexlify(format(1, '04x')) # Flags set to 1 to indicate broadcast
    packet += b'\x00\x00\x00\x00' #Client IP address: 0.0.0.0
    packet += offered_ip or b'\x00\x00\x00\x00'  #Your (client) IP address: 0.0.0.0
    packet += b'\x00\x00\x00\x00'   #Next server IP address: 0.0.0.0
    packet += b'\xc0\xa8\x01\x01'   #Relay agent IP address: 0.0.0.0
    packet += mac_address # Client mac address
    packet += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' #Client hardware address padding
    packet += b'\x00' * 67  #Server host name not given
    packet += b'\x00' * 125 #Boot file name not given
    packet += b'\x63\x82\x53\x63'   #Magic cookie: DHCP
    packet += (isRequest and (hostname_opcode + name_len + name)) or b'' # Hostname of client
    packet += (isRequest and b'\xff') or b'' # End of options

    return packet


def extract_packet(data: bytearray):
    transaction_id = int(hexlify(data[4:8]), 16)
    seconds = int(hexlify(data[8:10]), 16)
    offered_ip = hexlify(data[16:20])
    client_mac_address = data[28:34]
    return transaction_id, seconds, ip_byte_to_str(offered_ip), client_mac_address

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

def get_passed_time(start:float):
    return int(time() - start)
