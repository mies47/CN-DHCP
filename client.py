import socket
import time
import common.constants as c
import common.methods as m 
from random import getrandbits, uniform


def get_waiting_interval(prev_interval: int):
    if prev_interval == 0:
        return c.INITIAL_INTERVAL
    else:
        new_interval = int(prev_interval * (uniform(0.5, 1) * 2))
        if new_interval < c.BACKOFF_CUTOFF:
            return new_interval
        else:
            c.BACKOFF_CUTOFF


def send_DHCP_discover(c_socket: socket.socket, mac_addr:bytes):
    transaction_id = getrandbits(32)
    c_socket.sendto(m.make_packet(True, 0, transaction_id, mac_addr), ('<broadcast>', c.SERVER_PORT))
    print('DHCP Discover broadcasted in network')

    return transaction_id

def send_DHCP_discover(c_socket: socket.socket, mac_addr:bytes):
    transaction_id = getrandbits(32)
    c_socket.sendto(m.make_packet(True, 0, transaction_id, mac_addr), ('<broadcast>', c.SERVER_PORT))
    print('DHCP Request broadcasted in network')

    return transaction_id

if __name__ == '__main__':
    all_ips = m.get_all_interfaces()
    client_mac = m.get_mac()

    waiting_time = get_waiting_interval(0)
    while True:
        for ip in all_ips:
            c_socket = m.create_socket(ip, 0)
            start = time.time()
            transaction_id = send_DHCP_discover(c_socket)
            print(transaction_id)
            l_socket = m.create_socket('', c.CLIENT_PORT)
            l_socket.settimeout(waiting_time)
            try:
                data, info = l_socket.recvfrom(c.BUFFER_SIZE)
                print(info)
                offer_transaction_id, _, offered_ip, _ = m.extract_packet(data)
                if offer_transaction_id == transaction_id:
                    c_socket.sendto(m.make_packet(True, m.get_passed_time(start), transaction_id, m.get_mac()), ('<broadcast>', c.SERVER_PORT))
                    l_socket.settimeout(waiting_time - m.get_passed_time(start))
                    while True:
                        data, info = l_socket.recvfrom(c.BUFFER_SIZE)
                        ack_transaction_id, _, offered_ip, _ = m.extract_packet(data)
                        if ack_transaction_id == transaction_id:
                            print('IP is:')
                            print(offered_ip)
                            exit(0)
            except socket.timeout:
                c_socket.close()
                l_socket.close()
                print('Timeout exceeded. Trying again...')
                waiting_time = get_waiting_interval(waiting_time)
