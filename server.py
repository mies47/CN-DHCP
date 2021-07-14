import socket
import threading
import common.constants as c
import common.methods as m 

ALL_IPS = m.get_all_interfaces()
offered_client_macs = {}
ip_pool = []
infos = {}

lock = threading.Lock()


def send_DHCP_offer(data: bytes):
    transaction_id, seconds, _, client_mac_address = m.extract_packet(data)

    global lock, offered_client_macs
    lock.acquire()
    offered_ip = get_ip_from_pool()
    offered_client_macs[m.get_mac_str(client_mac_address)] = offered_ip
    lock.release()

    for ip in ALL_IPS:
        sl_socket = m.create_socket(ip, 0)
        sl_socket.sendto(m.make_packet(False, seconds, transaction_id, client_mac_address, '', m.ip_str_to_byte(offered_ip)), ('<broadcast>', c.CLIENT_PORT))

def send_DHCP_ack(data: bytes):
    transaction_id, seconds, _, client_mac_address = m.extract_packet(data)

    str_client_mac_address = m.get_mac_str(client_mac_address)
    global lock, offered_client_macs, ip_pool, infos
    offered_ip = offered_client_macs[str_client_mac_address]
    lock.acquire()
    offered_client_macs.pop(str_client_mac_address)
    if offered_ip in ip_pool:
        ip_pool.remove(offered_ip)
    infos[str_client_mac_address] = {
        'IP': offered_ip,
        'name': 'mies',
        'expire': m.get_expiration()
    }
    lock.release()

    for ip in ALL_IPS:
        sl_socket = m.create_socket(ip, 0)
        sl_socket.sendto(m.make_packet(False, seconds, transaction_id, client_mac_address,'', m.ip_str_to_byte(offered_ip)), ('<broadcast>', c.CLIENT_PORT))

def dhcp_client_handler(data: bytes):
    _, _, _, client_mac_address = m.extract_packet(data)
    if m.get_mac_str(client_mac_address) in offered_client_macs:
        send_DHCP_ack(data)
    else:
        send_DHCP_offer(data)

def get_ip_from_pool():
    return '192.168.1.3'

if __name__ == '__main__':
    s_socket = m.create_socket('', c.SERVER_PORT)

    while True:
        data, info = s_socket.recvfrom(c.BUFFER_SIZE)
        dhcp_client_thread = threading.Thread(target=dhcp_client_handler, args=(data,))
        dhcp_client_thread.start()
