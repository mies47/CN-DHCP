import socket
import time

CLIENT_PORT = 68
BUFFER_SIZE = 4096
ENCODING = 'utf-8'

if __name__ == '__main__':
    interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
    allips = [ip[-1][0] for ip in interfaces]
    allips = set(allips)
    allips = list(allips)
    print(allips)

    while True:
        for ip in allips:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            client_socket.bind(('127.0.0.1', 0))
            client_socket.sendto(b"your very important message", ('255.255.255.255', 3030))
            print('Sent')
            time.sleep(1)