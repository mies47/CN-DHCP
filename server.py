import socket
import threading

SERVER_PORT = 3030
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

def dhcp_client_handler(data: bytearray, info):
    print(data.decode(ENCODING))
    print(info)

if __name__ == '__main__':
    #Create UDP socket
    server_socket = socket.socket(type= socket.SOCK_DGRAM)
    #Set option for address reusability
    server_socket.setsockopt(socket.SOL_IP, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_socket.bind(('', SERVER_PORT))

    while True:
        data, info = server_socket.recvfrom(BUFFER_SIZE)
        print('hi')
        dhcp_client_thread = threading.Thread(target=dhcp_client_handler, args=(data, info))
        dhcp_client_thread.start()
