import threading
import common.constants as c
import common.methods as m 
import ipaddress
import time
from random import random

ALL_IPS = m.get_all_interfaces()
offered_client_macs = {}
assigned_mac_ip = {}
lease_ip = []
ip_pool = []
infos = {}

lock = threading.Lock()


def send_DHCP_offer(data: bytes):
    transaction_id, seconds, _, client_mac_address, _ = m.extract_packet(data)

    str_client_mac = m.get_mac_str(client_mac_address)
    global lock, offered_client_macs, assigned_mac_ip
    lock.acquire()

    if str_client_mac in assigned_mac_ip.keys():
        send_DHCP_ack(data, assigned_mac_ip[str_client_mac])
        lock.release()
        return

    offered_ip = get_ip_from_pool()
    offered_client_macs[m.get_mac_str(client_mac_address)] = offered_ip
    lock.release()

    for ip in ALL_IPS:
        sl_socket = m.create_socket(ip, 0)
        sl_socket.sendto(m.make_packet(False, seconds, transaction_id, client_mac_address, '', m.ip_str_to_byte(offered_ip)), ('<broadcast>', c.CLIENT_PORT))

def send_DHCP_ack(data: bytes, given_ip=None):
    transaction_id, seconds, _, client_mac_address, host_name = m.extract_packet(data)
    ip_available = True

    if not given_ip:
        str_client_mac_address = m.get_mac_str(client_mac_address)
        global lock, assigned_mac_ip, offered_client_macs, ip_pool, infos, lease_ip
        offered_ip = offered_client_macs[str_client_mac_address]
        lock.acquire()
        offered_client_macs.pop(str_client_mac_address)
        if offered_ip in ip_pool:
            ip_pool.remove(offered_ip)
            infos[offered_ip] = {
                'mac': str_client_mac_address,
                'name': host_name,
                'expire': m.get_expiration()
            }
            lease_ip.append({
                'IP': offered_ip,
                'expire': infos[offered_ip]['expire']
            })
            assigned_mac_ip[str_client_mac_address] = offered_ip
        else:
            ip_available = False
        lock.release()
    else:
        offered_ip = given_ip

    if ip_available:
        for ip in ALL_IPS:
            sl_socket = m.create_socket(ip, 0)
            sl_socket.sendto(m.make_packet(False, seconds, transaction_id, client_mac_address,'', m.ip_str_to_byte(offered_ip)), ('<broadcast>', c.CLIENT_PORT))

def dhcp_client_handler(data: bytes):
    _, _, _, client_mac_address, _ = m.extract_packet(data)
    if m.get_mac_str(client_mac_address) in offered_client_macs:
        send_DHCP_ack(data)
    else:
        send_DHCP_offer(data)


def initialize_ip_pool():
    global ip_pool
    if c.CONFIG['pool_mode'] == 'range':
        start = ipaddress.ip_address(c.CONFIG['range']['from'])
        end = ipaddress.ip_address(c.CONFIG['range']['to'])
        while start <= end:
            ip_pool.append(str(start))
            start += 1

    else:
        ip_pool = [str(i) for i in ipaddress.ip_network(c.CONFIG['subnet']['ip_block']+ '/' + c.CONFIG['subnet']['subnet_mask'])]
        ip_pool.pop(0)


def check_and_release():
    global lease_ip, lock, ip_pool, infos, assigned_mac_ip
    new_time = 1
    lock.acquire()
    if len(lease_ip) != 0:
        if time.time() >= lease_ip[0]['expire']:
            old_ip = lease_ip.pop(0)['IP']
            old_mac = infos[old_ip]['mac']
            infos.pop(old_ip)
            assigned_mac_ip.pop(old_mac)
            ip_pool.append(old_ip)
            if len(lease_ip) != 0:
                new_time = time.time() - lease_ip[0]['expire']
    lock.release()
    t = threading.Timer(new_time, check_and_release)
    t.start()


def get_ip_from_pool():
    global ip_pool

    index = int(random() * len(ip_pool))
    selected_ip = ip_pool[index]

    return selected_ip

if __name__ == '__main__':
    check_and_release()
    initialize_ip_pool()
    s_socket = m.create_socket('', c.SERVER_PORT)

    while True:
        data, info = s_socket.recvfrom(c.BUFFER_SIZE)
        dhcp_client_thread = threading.Thread(target=dhcp_client_handler, args=(data,))
        dhcp_client_thread.start()
