import os
import pickle
import platform
import re
import socket
import time
from typing import Tuple


def build_udp_socket() -> socket.socket:
    udp = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # FOR BROADCAST
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, _socket_buffer_size())
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, _socket_buffer_size())
    return udp


def build_tcp_socket() -> socket.socket:
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # BUFFER
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, _socket_buffer_size())
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, _socket_buffer_size())
    return tcp


_MY_IP = [0.0, '']


# 切分ifconfig返回列表，拿到active的ip地址
def get_my_ip() -> str:
    global _MY_IP
    if time.time() - _MY_IP[0] < 5:
        return _MY_IP[1]
    ip = str()
    status_check = str()
    fil_list = ['10.10.10.100']
    if platform.system() == 'Darwin':
        for line in os.popen('ifconfig'):
            if line[:1] != '\t':
                if ip and status_check:
                    break
                ip = str()
                status_check = False
            elif line[1:6] == 'inet ':
                ip_cache = line.split(' ', 2)[1]
                if ip_cache.split('.')[0] in ['192', '172', '10'] and ip_cache not in fil_list:
                    ip = ip_cache
            elif line[1:7] == 'status':
                status_check = line[9:] == 'active\n'
    else:
        search_flag = False
        for line in os.popen('ip address'):
            if re.match(r'\d+:', line):
                if re.search(r'state UP', line, re.I):
                    search_flag = True
                else:
                    search_flag = False
            elif not search_flag:
                continue
            else:
                res = re.match(r' {4}inet (192|172|10).\d{1,3}.\d{1,3}.\d{1,3}/24', line)
                if res:
                    ip = line[9:res.span()[1] - 3]
                    if ip not in fil_list:
                        break
    _MY_IP[0] = time.time()
    _MY_IP[1] = ip
    return ip


def broadcast_ip():
    my_ip = get_my_ip()
    b_ip = ''
    if my_ip:
        ip_iter = my_ip.split('.')
        ip_iter[-1] = '255'
        b_ip = '.'.join(ip_iter)
    return b_ip


def _socket_buffer_size() -> int:
    buffer_size = 104857600
    if platform.system() == 'Darwin':
        release = platform.release().split('.')
        mac_ver = 0
        for idx, num in enumerate(release):
            mac_ver += int(num) / 10 ** idx
        if mac_ver < 18:
            buffer_size = 2097152
        else:
            buffer_size = 6553600
    return buffer_size


def encode(code, **kwargs):
    return pickle.dumps((code, kwargs))


def decode(bytes_array) -> Tuple[int, dict]:
    code, kwargs = pickle.loads(bytes_array)
    return code, kwargs
