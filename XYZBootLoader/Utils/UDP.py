import time
import socket
import threading
from typing import Tuple, Callable

from .nettools import build_udp_socket


class _CONST:
    RECV_LENGTH = 1024
    RESEND_TIMEOUT = 2
    HEARTBEAT_PERIOD = 1


class UDP:
    def __init__(self, callback: Callable, udp_ip: str = '', udp_port: int = None):
        self._callback = callback
        self._udp_ip = udp_ip
        self._udp_port = udp_port
        # SOCKET
        self._udp = build_udp_socket()
        self._lock = threading.Lock()
        self._peer_address = tuple()  # type: Tuple[str, int]  # 指单片机，也是唯一的ADDRESS
        self._is_bound = False
        # EVENT 重发事件
        self._event = threading.Event()
        self._resend_command = bytes()
        self._is_resend_command = False
        # THREAD
        self._thread = threading.Thread(target=self._working, daemon=True)
        self._thread_switch = True
        self._thread.start()

    def _working(self):
        while self._thread_switch:
            self._bind()
            try:
                data, address = self._udp.recvfrom(_CONST.RECV_LENGTH)
                if data:
                    print('recv', data, data == self._resend_command, self._resend_command)
                    if self._is_resend_command and data == self._resend_command:  # 关键指令包检测
                        self._event.set()
                    self._callback(data=data, ip=address[0], port=address[1])
            except socket.error as err:
                print('RECV ERROR', err)
        self._udp.close()

    def _bind(self):
        if not self._is_bound:
            host_address = (self._udp_ip, self._udp_port or 0)
            try:
                self._udp.bind(host_address)
                self._is_bound = True
            except socket.error as err:
                if err.errno in [49, 99, 101]:  # 地址不存在
                    print('UDP_地址不存在')
                elif err.errno == 48:  # 地址已占用
                    print('UDP_地址被占用')
                elif err.errno == 22:  # 地址已绑定
                    print('UDP_地址已绑定')
                else:
                    raise err
            time.sleep(1)

    # SEND
    def _send(self, data: bytes, address: tuple) -> int:
        try:
            # print('UDP_SEND', data, address)
            sent_length = self._udp.sendto(data, address)
            # print(f'SEND SUCCESS, data={data}, addr={address}')
        except socket.error as err:
            if err.errno in [64, 65]:
                print('发送错误')
            else:
                print('发送错误2')
            sent_length = 0
        return sent_length

    def send_to(self, data: bytes, ip: str, port: int, is_resent_command: bool = False) -> int:
        if self._udp_port and not self._is_bound:
            print(f'UDP[] UDP还没有绑定成功, 请稍后再发')
            return 0
        if len(data) > _CONST.RECV_LENGTH:
            print('消息过长')
            return 0
        with self._lock:
            resend_count = 5
            self._peer_address = (ip, port)
            self._is_resend_command = is_resent_command
            self._resend_command = data[0: 2]
            if is_resent_command:
                for i in range(resend_count):
                    print(f'重发次数{i}, Data={self._resend_command[0: 2]}')
                    res = self._send(data=data, address=self._peer_address)
                    if self._event.wait(_CONST.RESEND_TIMEOUT):  # 是否有被设置为True，如果被设置为True了则证明收到了
                        # self._resend_command = bytes()
                        self._event.clear()
                        break
                    else:
                        str_data = data if len(data) < 20 else f'len({len(data)})'
                else:
                    print(F'指令重发失败, CMD={self._is_resend_command}')
                    res = 0
            else:
                res = self._send(data=data, address=self._peer_address)
            return res

    def send_broadcast(self, data: bytes, port: int) -> int:
        return self._send(data=data, address=('<broadcast>', port))

    def set_peer_address(self, address: tuple):
        self._peer_address = address

    def get_bind_address(self) -> Tuple[str, int]:
        return self._udp.getsockname()

    # EXIT
    def exit(self):
        self._udp.close()
        self._event.set()
        self._event.clear()
        self._thread_switch = False
