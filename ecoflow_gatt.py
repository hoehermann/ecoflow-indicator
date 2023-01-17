#!/usr/bin/python3

import sys
import gattlib
import pprint
from bluetooth.ble import GATTRequester
from ecoflow import receive, calcCrc8, calcCrc16
from collections import defaultdict
from collections.abc import Callable

class Requester(GATTRequester):
    def __init__(self, address: str, on_update: Callable[[dict], None]):
        super().__init__(address, False)
        self.info = defaultdict(int)
        self.receive_buffer = b''
        self.on_update = on_update
    def connect(self):
        super().connect(True)
        mtu = self.exchange_mtu(500)
        self.set_mtu(mtu)
    def _merge_packet(self, receive_bytes: bytes):
        # copied from hassio-ecoflow, but without reactivex
        self.receive_buffer += receive_bytes
        while len(self.receive_buffer) >= 18:
            if self.receive_buffer[:2] != b'\xaa\x02':
                self.receive_buffer = self.receive_buffer[1:]
                continue
            size = int.from_bytes(self.receive_buffer[2:4], 'little')
            if 18 + size > len(self.receive_buffer):
                return
            if calcCrc8(self.receive_buffer[:4]) != self.receive_buffer[4:5]:
                self.receive_buffer = self.receive_buffer[2:]
                continue
            if calcCrc16(self.receive_buffer[:16 + size]) != self.receive_buffer[16 + size:18 + size]:
                self.receive_buffer = self.receive_buffer[2:]
                continue
            yield self.receive_buffer[:18 + size]
            self.receive_buffer = self.receive_buffer[18 + size:]
    def on_notification(self, handle: int, data: str):
        if (len(data) < 5):
            return
        #data[0] is BT ATT Opcode: Handle Value Notification (0x1b)
        #data[1:3] is BT ATT Handle: 0x002c (SDP: RFCOMM)
        #data[3:] is BT ATT Value (actual Ecoflow data)
        for packet in self._merge_packet(data[3:]):
            decoded_packet = receive.decode_packet(packet)
            if (receive.is_pd(decoded_packet)):
                self.info.update(receive.parse_pd_delta(decoded_packet[3]))
            if (receive.is_bms(decoded_packet)):
                self.info.update(receive.parse_bms_delta(decoded_packet[3])[1])
            if (receive.is_ems(decoded_packet)):
                self.info.update(receive.parse_ems_delta(decoded_packet[3]))
            if (receive.is_mppt(decoded_packet)):
                self.info.update(receive.parse_mppt_delta(decoded_packet[3]))
            if (receive.is_inverter(decoded_packet)):
                self.info.update(receive.parse_inverter_delta(decoded_packet[3]))
            self.on_update(self.info)

def main(address: str):
    def on_update(info):
        sys.stdout.write(f"\rOut: {info['ac_out_power']: 3d}W In: {info['dc_in_power']*10: 3.0f}W Level: {info['battery_main_level']}%")
        if (info['ac_out_power'] > info['dc_in_power']*10):
            sys.stdout.write(f" ({info['battery_remain_discharge']} remaining)")
        pprint.pprint(info)
    requester = Requester(address, on_update)
    terminate = None
    while terminate is None:
        try:
            requester.connect()
            terminate = input("Press enter to exit.\n")
        except gattlib.BTIOException as e:
            print(e)
            print("Retrying...")

if __name__ == "__main__":
    ecoflow_address = sys.argv[1]
    main(ecoflow_address)
