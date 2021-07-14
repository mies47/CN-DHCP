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

def get_DHCP_offer(last_transaction_id: int, waiting_time: int):
    c_socket = m.create_socket('', c.CLIENT_PORT)
    c_socket.settimeout(waiting_time)
    try:
        data, _ = c_socket.recvfrom(c.BUFFER_SIZE)
        offer_transaction_id, _, offered_ip, _ = m.extract_packet(data)
        if offer_transaction_id == last_transaction_id:
            print('Offered IP is ' + offered_ip)
            c_socket.close()
            return offered_ip
    except socket.timeout:
        c_socket.close()
        return 'Time out'

def send_DHCP_request(c_socket: socket.socket, mac_addr:bytes, start_time:float):
    transaction_id = getrandbits(32)
    c_socket.sendto(m.make_packet(True, m.get_passed_time(start_time), transaction_id, mac_addr), ('<broadcast>', c.SERVER_PORT))
    print('DHCP Request broadcasted in network')

    return transaction_id

def get_DHCP_ack(last_transaction_id: int, waiting_time: int, start_time:float):
    c_socket = m.create_socket('', c.CLIENT_PORT)
    c_socket.settimeout(waiting_time - m.get_passed_time(start_time))
    try:
        data, _ = c_socket.recvfrom(c.BUFFER_SIZE)
        offer_transaction_id, _, offered_ip, _ = m.extract_packet(data)
        if offer_transaction_id == last_transaction_id:
            print('Got IP ' + offered_ip)
            c_socket.close()
            exit(0)
    except socket.timeout:
        c_socket.close()
        return 'Time out'

if __name__ == '__main__':
    all_ips = m.get_all_interfaces()
    client_mac = m.get_mac()

    waiting_time = get_waiting_interval(0)
    while True:
        for ip in all_ips:
            c_socket = m.create_socket(ip, 0)
            start = time.time()
            transaction_id = send_DHCP_discover(c_socket, client_mac)
            result = get_DHCP_offer(transaction_id, waiting_time)
            if result and result != 'Time out':
                transaction_id = send_DHCP_request(c_socket, client_mac, start)
                result = get_DHCP_ack(transaction_id, waiting_time, start)
            
            waiting_time = get_waiting_interval(waiting_time)
            break
