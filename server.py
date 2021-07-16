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
    transaction_id, seconds, _, client_mac_address, _, _ = m.extract_packet(data)
    str_client_mac = m.get_mac_str(client_mac_address)

    if str_client_mac in c.CONFIG['black_list']: #Check not to respond to blocked MACs
        return

    global lock, offered_client_macs, assigned_mac_ip
    lock.acquire()

    if str_client_mac in assigned_mac_ip.keys():
        offered_ip = assigned_mac_ip[str_client_mac]
    else:
        offered_ip = get_ip_from_pool()

    offered_client_macs[m.get_mac_str(client_mac_address)] = offered_ip
    lock.release()

    for ip in ALL_IPS:
        sl_socket = m.create_socket(ip, 0)
        server_ip = ip if ip != '127.0.0.1' else ALL_IPS[1]
        sl_socket.sendto(m.make_packet(False, seconds, transaction_id, client_mac_address, server_ip, m.ip_str_to_byte(offered_ip)), ('<broadcast>', c.CLIENT_PORT))

def send_DHCP_ack(data: bytes):
    transaction_id, seconds, _, client_mac_address, host_name, server_ip = m.extract_packet(data)
    ip_available = True

    global lock, assigned_mac_ip, offered_client_macs, ip_pool, infos, lease_ip
    str_client_mac_address = m.get_mac_str(client_mac_address)

    lock.acquire()
    if server_ip not in ALL_IPS:
        offered_client_macs.pop(str_client_mac_address)
        lock.release()
        return

    if str_client_mac_address not in assigned_mac_ip.keys():
        offered_ip = offered_client_macs[str_client_mac_address]
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
    else:
        offered_ip = assigned_mac_ip[str_client_mac_address]
    
    offered_client_macs.pop(str_client_mac_address)

    lock.release()

    if ip_available:
        for ip in ALL_IPS:
            sl_socket = m.create_socket(ip, 0)
            server_ip = ip if ip != '127.0.0.1' else ALL_IPS[1]
            sl_socket.sendto(m.make_packet(False, seconds, transaction_id, client_mac_address,'', m.ip_str_to_byte(offered_ip)), ('<broadcast>', c.CLIENT_PORT))

def dhcp_client_handler(data: bytes):
    _, _, _, client_mac_address, _, _ = m.extract_packet(data)
    if m.get_mac_str(client_mac_address) in offered_client_macs:
        send_DHCP_ack(data)
    else:
        send_DHCP_offer(data)


def initialize_ip_pool():
    global ip_pool, infos, assigned_mac_ip

    reserved_ips = []
    for mac, ip in c.CONFIG['reservation_list'].items():
        reserved_ips.append(ip)
        assigned_mac_ip[mac] = ip
        infos[ip] = {
            'mac': mac,
            'name': 'Unkown',
            'expire': -1
        }

    if c.CONFIG['pool_mode'] == 'range':
        start = ipaddress.ip_address(c.CONFIG['range']['from'])
        end = ipaddress.ip_address(c.CONFIG['range']['to'])
        while start <= end:
            if start not in reserved_ips:
                ip_pool.append(str(start))
            start += 1

    else:
        ip_pool = []
        for i in ipaddress.ip_network(c.CONFIG['subnet']['ip_block']+ '/' + c.CONFIG['subnet']['subnet_mask']):
            if i not in reserved_ips:
                ip_pool.append(str(i))
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

def show_clients():
    global infos, lock
    while True:
        instruction = input('>')
        if instruction == 'show_client':
            print('Name\t\tMAC\t\t\tIP\t\t\tExpiration')
            lock.acquire()
            for ip, info in infos.items():
                print(f"{info['name']}\t{info['mac']}\t{ip}\t{info['expire'] - time.time()} seconds ")
            lock.release()

if __name__ == '__main__':
    check_and_release()
    initialize_ip_pool()
    show_clients_thread = threading.Thread(target=show_clients)
    show_clients_thread.start()
    s_socket = m.create_socket('', c.SERVER_PORT)

    while True:
        data, info = s_socket.recvfrom(c.BUFFER_SIZE)
        dhcp_client_thread = threading.Thread(target=dhcp_client_handler, args=(data,))
        dhcp_client_thread.start()
