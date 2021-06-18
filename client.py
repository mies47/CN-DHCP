import socket
import time
import common.constants as c
import common.methods as m 
from random import getrandbits, random


def get_waiting_interval(prev_interval: int):
    if prev_interval == 0:
        return c.INITIAL_INTERVAL
    else:
        new_interval = int(prev_interval * random() * 2)
        return new_interval if new_interval < c.BACKOFF_CUTOFF else c.BACKOFF_CUTOFF


def send_DHCP_discover(c_socket: socket.socket):
    transaction_id = getrandbits(32)
    c_socket.sendto(m.make_packet(True, 0, transaction_id, m.get_mac()), ('<broadcast>', c.SERVER_PORT))
    print('DHCP Discover broadcasted in network')

    return transaction_id

if __name__ == '__main__':
    all_ips = m.get_all_interfaces()

    waiting_time = get_waiting_interval(0)
    while True:
        for ip in all_ips:
            c_socket = m.create_socket(ip, 0)
            start = time.time()
            transaction_id = send_DHCP_discover(c_socket)
            l_socket = m.create_socket('', c.CLIENT_PORT)
            l_socket.settimeout(waiting_time)
            try:
                data, info = l_socket.recvfrom(c.BUFFER_SIZE)
                print(data, info)
            except socket.timeout:
                print('Timeout exceeded. Trying again...')
                waiting_time = get_waiting_interval(waiting_time)
