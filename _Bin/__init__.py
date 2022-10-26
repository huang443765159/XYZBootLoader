import os
import math
import struct


# cmd = list()
# cmd.append(1)
# cmd_iter = iter(cmd)
# print(cmd_iter.__next__())
# print(cmd_iter.__next__())
# PKT_LENGTH = 992
# path = '192.168.50.211.bin'
#
#
# with open(path, 'rb') as fp:
#     data = fp.read()
#     all_data = bytes.fromhex(data.hex())
#     ip = os.path.basename(path).split('.bin')[0]
#     mcu_addr = (ip, 54188)
#     pkt_length = math.ceil(len(all_data) / PKT_LENGTH)
#     print(f'PKT_LEN = {pkt_length}')
#     for i in range(pkt_length):
#         one_cmd = struct.pack('!H', i) + all_data[i * PKT_LENGTH: (i + 1) * PKT_LENGTH]
#         print(i, len(one_cmd))
#         cmd.append(one_cmd)
