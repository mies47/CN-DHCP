import socket
import threading
import common.constants as c
import common.methods as m 


def dhcp_client_handler(data: bytearray, info):
    print(data)
    print(info)

if __name__ == '__main__':
    s_socket = m.create_socket('', c.SERVER_PORT)

    while True:
        data, info = s_socket.recvfrom(c.BUFFER_SIZE)
        dhcp_client_thread = threading.Thread(target=dhcp_client_handler, args=(data, info))
        dhcp_client_thread.start()
