from transport.ccsds_packets import parse_ccsds_packet, build_ccsds_packet
from constants import *
from components.base_components import BaseInternalComponent


class OBDH(BaseInternalComponent):
    def __init__(self, apid):
        super().__init__(apid)

        self.voltage = 0
        self.cpu_usage = 0
        
        self.payload_mode = 0
        self.payload_img_acquired = 0
        self.payload_mem_used = 0

        self.thermal_temperature = 0
        self.thermal_heater_enabled = 0


    def simulate(self):
        pass
        
    def process(self):
        for link in self.links.values():
            if link.has_packets():
                packet = link.get_packet()
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
                        self.tm_send_status(EGSE_APID)

                    if tc_type == TM_SEND_STATUS:
                        self.update_status(data[1:])

    def update_status(self, data):
        self.payload_mode = data[0]

        temperature_h = data[4]
        temperature_l = data[5]
        voltage_h = data[6]
        voltage_l = data[7]

        temperature = temperature_l | (temperature_h << 8)
        voltage = voltage_l | (voltage_h << 8)

        temperature = temperature * 0.01
        voltage = voltage * 0.01
        self.temperature = temperature
        self.voltage = voltage

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
        self.send(packet, target)


