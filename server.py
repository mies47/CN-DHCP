import socket
import threading
import common.constants as c
import common.methods as m 

def send_DHCP_offer(seconds:int, transaction_id:int, client_mac_address:bytearray):
    all_ips = m.get_all_interfaces()
    for ip in all_ips:
        sl_socket = m.create_socket(ip, 0)
        sl_socket.sendto(m.make_packet(False, seconds, transaction_id, client_mac_address, m.ip_str_to_byte('192.168.1.10')), ('<broadcast>', c.CLIENT_PORT))

def send_DHCP_ack(data: bytearray, offered_ip:str):
    pass

def dhcp_client_handler(s_socket:socket.socket, data: bytearray, info):
    print(f'Client {info[0]} with port {info[1]} DHCP discover recieved')
    transaction_id, seconds, _, client_mac_address = m.extract_packet(data)
    print(f'Transaction_id:{transaction_id}\nmac_address {m.get_mac_str(client_mac_address)}')
    send_DHCP_offer(seconds, transaction_id, client_mac_address)
    s_socket.settimeout(c.INITIAL_INTERVAL)
    # while True:
    #     try:
    #         data, info = s_socket.recvfrom(c.BUFFER_SIZE)
    #         if transaction_id ==
    #     except socket.timeout:
    #         s_socket.close()
    #         break



if __name__ == '__main__':
    s_socket = m.create_socket('', c.SERVER_PORT)

    while True:
        data, info = s_socket.recvfrom(c.BUFFER_SIZE)
        dhcp_client_thread = threading.Thread(target=dhcp_client_handler, args=(s_socket, data, info))
        dhcp_client_thread.start()
