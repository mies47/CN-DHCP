import socket
import time
import common.constants as c
import common.methods as m 
from random import getrandbits, uniform

ALL_IPS = m.get_all_interfaces()

def get_waiting_interval(prev_interval: int):
    if prev_interval == 0:
        return c.INITIAL_INTERVAL
    else:
        new_interval = int(prev_interval * (uniform(0.5, 1) * 2))
        if new_interval < c.BACKOFF_CUTOFF:
            return new_interval
        else:
            c.BACKOFF_CUTOFF


def send_DHCP_discover(mac_addr:bytes):
    transaction_id = getrandbits(32)
    for ip in ALL_IPS:
        c_socket = m.create_socket(ip, 0)
        c_socket.sendto(m.make_packet(True, 0, transaction_id, mac_addr), ('<broadcast>', c.SERVER_PORT))
    print('DHCP Discover broadcasted in network')

    return transaction_id

def get_DHCP_offer(last_transaction_id: int, waiting_time: int):
    c_socket = m.create_socket('', c.CLIENT_PORT)
    c_socket.settimeout(waiting_time)
    try:
        data, _ = c_socket.recvfrom(c.BUFFER_SIZE)
        offer_transaction_id, _, offered_ip, _, _, server_ip = m.extract_packet(data)
        if offer_transaction_id == last_transaction_id:
            print('Offered IP is ' + offered_ip)
            c_socket.close()
            return offered_ip, server_ip
        else:
            get_DHCP_offer(last_transaction_id, waiting_time)
    except socket.timeout:
        c_socket.close()
        return 'Time out', None

def send_DHCP_request(mac_addr:bytes, server_ip:str , start_time:float):
    transaction_id = getrandbits(32)
    for ip in ALL_IPS:
        c_socket = m.create_socket(ip, 0)
        c_socket.sendto(m.make_packet(True, m.get_passed_time(start_time), transaction_id, mac_addr, server_ip), ('<broadcast>', c.SERVER_PORT))
    print('DHCP Request broadcasted in network')

    return transaction_id

def get_DHCP_ack(last_transaction_id: int, waiting_time: int, start_time:float):
    c_socket = m.create_socket('', c.CLIENT_PORT)
    c_socket.settimeout(waiting_time - m.get_passed_time(start_time))
    try:
        data, _ = c_socket.recvfrom(c.BUFFER_SIZE)
        offer_transaction_id, _, offered_ip, _, _, _ = m.extract_packet(data)
        if offer_transaction_id == last_transaction_id:
            print('Got IP ' + offered_ip)
            c_socket.close()
            exit(0)
        else:
            get_DHCP_ack(last_transaction_id, waiting_time, start_time)
    except socket.timeout:
        c_socket.close()
        return 'Time out'
    except Exception as e:
        print(e)

if __name__ == '__main__':
    client_mac = m.get_mac()

    waiting_time = get_waiting_interval(0)
    while True:
        
        start = time.time()
        transaction_id = send_DHCP_discover(client_mac)
        result, server_ip = get_DHCP_offer(transaction_id, waiting_time)
        if result and result != 'Time out':
            transaction_id = send_DHCP_request(client_mac, server_ip, start)
            result = get_DHCP_ack(transaction_id, waiting_time, start)
        
        waiting_time = get_waiting_interval(waiting_time)
