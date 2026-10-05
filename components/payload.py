from transport.ccsds_packets import parse_ccsds_packet, build_ccsds_packet
from constants import *
from components.base_components import BaseInternalComponent


class Payload(BaseInternalComponent):
    def __init__(self, apid):
        super().__init__(apid)
        self.temperature = 25
        self.voltage = 12

    def simulate(self):
        temp_increment = 0
        if self.uptime < 2500:
            if self.uptime > 110:
                temp_increment = 0.01
        else:
            temp_increment = -0.01
        volt_increment = -0.0001

        self.temperature += temp_increment 
        self.voltage += volt_increment
        if self.voltage < 0:
            self.voltage = 0

        if self.uptime % 200 == 0:
            self.tm_send_status(OBDH_APID)
        

    def process(self):
        packet = self.rx.get_packet()
        if packet is None:
            return
        unpacked = parse_ccsds_packet(packet)
        if unpacked is None:
            return
        apid = unpacked["apid"]
        if apid == self.apid:   
            data = unpacked["data"]
            if not(isinstance(data, list)):
                return
            tc_type = data[0]

            if tc_type == TC_GET_STATUS:
                self.tm_send_status(OBDH_APID)

    
    # Type = TM
    # DATA = 4 byte: mode, uptime, temp, voltage
    def tm_send_status(self, target):
        temp = int(self.temperature * 100)
        volt = int(self.voltage * 100)

        temp_l = temp &0xFF
        temp_h = (temp >> 8) & 0xFF

        volt_l = volt & 0xFF
        volt_h = (volt >> 8) & 0xFF

        uptime_l = self.uptime & 0xFF
        uptime_m = (self.uptime >> 8) & 0xFF
        uptime_h = (self.uptime >> 16) &0xFF
        data = bytes([
            TM_SEND_STATUS,
            self.mode,
            uptime_h,
            uptime_m,
            uptime_l,
            temp_h,
            temp_l,
            volt_h,
            volt_l,
        ])
        packet = build_ccsds_packet(TM, target, 0, self.seq_cnt, data)
        self.tx.send(packet, target)


