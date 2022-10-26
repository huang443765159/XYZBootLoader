import os
import math
import time
import socket
import struct
import threading

from PyQt5.QtCore import QObject, pyqtSignal

from XYZBootLoader.Utils.CMD import CMD
from XYZBootLoader.Utils.nettools import build_udp_socket


PKT_LENGTH = 992


class BootLoader(QObject):
    sign_cur_state = pyqtSignal(str)  # cur_state
    sign_cur_per = pyqtSignal(int, int, int)  # cur_per, cur_data_len, data_len

    def __init__(self):
        super(BootLoader, self).__init__()
        # SOCKET
        self._socket = build_udp_socket()
        self._socket.bind(('', 0))
        self._socket.settimeout(5)
        # ATTR
        self._cmd = list()
        self._cmd_iter = None  # type: iter
        self._cmd.append(CMD.SET_MODE)
        self._cmd.append(CMD.SET_REGISTER)
        self._mcu_addr = tuple()
        self._timeout = 0.1
        self._cur_cmd = bytes()
        # THREAD
        self._thread = threading.Thread(target=self._working, daemon=True)
        self._thread_switch = True
        self._thread.start()

    def _working(self):
        while self._thread_switch:
            if self._mcu_addr:
                try:
                    print('send', self._cur_cmd[0: 2], self._mcu_addr)
                    self._socket.sendto(self._cur_cmd, self._mcu_addr)
                except socket.error as err:
                    pass
                self._socket.settimeout(self._timeout)
                try:
                    data, address = self._socket.recvfrom(1024)
                    if data[: 2] == self._cur_cmd[: 2]:
                        try:
                            self._cur_cmd = self._cmd_iter.__next__()
                        except StopIteration:
                            self.sign_cur_state.emit('数据发送完毕')
                            self._mcu_addr = tuple()
                    if data.startswith(CMD.SET_MODE):
                        self.sign_cur_state.emit('设置进入烧录模式')
                        self._timeout = 0.1
                    elif data.startswith(CMD.SET_REGISTER):
                        self.sign_cur_state.emit('设置即将开始烧录')
                        self._timeout = 3
                    elif data.startswith(CMD.SET_END):
                        self.sign_cur_state.emit('烧录完成')
                    else:
                        cur_pkt_id = struct.unpack('!H', data[: 2])[0]
                        if cur_pkt_id < 1000:
                            self.sign_cur_per.emit(int((cur_pkt_id + 1) / (len(self._cmd) - 3) * 100),
                                                   cur_pkt_id, len(self._cmd) - 3)
                        self._timeout = 0.3
                except socket.timeout:
                    # print(f'接收超时, 超时数据={self._cur_cmd[0: 4]}')
                    continue
                except BlockingIOError:
                    print('TX_ERROR, 对方不在线')
                    pass
            else:
                time.sleep(0.5)

    # 在这里把指令都分完放进列表里，然后在发一条就等着收一条，一直到收到为止，流水账模式
    def load_file(self, path: str):
        self.sign_cur_state.emit('尝试连接中')
        self._cmd = list()
        self._cmd.append(CMD.SET_MODE)
        self._cmd.append(CMD.SET_REGISTER)
        if not os.path.exists(path):
            print(f'文件不存在，请检查路径, 路径={path}')
            return
        elif not path.endswith('.bin'):
            print('文件不正确，非bin文件')
            return
        elif self._mcu_addr:
            print('上一个文件还在烧录中，请稍后再试')
        else:
            # 开始进行拆包
            with open(path, 'rb') as fp:
                data = fp.read()
                all_data = bytes.fromhex(data.hex())
                ip = os.path.basename(path).split('.bin')[0]
                self._mcu_addr = (ip, 54188)
                # self._mcu_addr = ('192.168.50.151', 54188)
                pkt_length = math.ceil(len(all_data) / PKT_LENGTH)
                for i in range(pkt_length):
                    one_cmd = struct.pack('!H', i) + all_data[i * PKT_LENGTH: (i + 1) * PKT_LENGTH]
                    self._cmd.append(one_cmd)
                self._cmd.append(CMD.SET_END)
                self._cmd_iter = iter(self._cmd)
                self._cur_cmd = self._cmd_iter.__next__()

    def exit(self):
        self._thread_switch = False
        self._mcu_addr = tuple()
