from transport.ccsds_packets import parse_ccsds_packet, build_ccsds_packet
from constants import *
from components.base_components import BaseComponent

class EGSE(BaseComponent):
    def __init__(self, apid: int):
        super().__init__(apid)
        self.seq_cnt = 0

    def process(self):
        for link in self.links.values():
            if link.has_packets():
                packet = link.get_packet()
                if packet is None:
                    return
                unpacked = parse_ccsds_packet(packet)
                if unpacked is None:
                    return
                data = unpacked["data"]
                if not(isinstance(data, list)):
                    return
                tm_type = data[0]

                if tm_type == TM_SEND_STATUS:
                    self.print_obdh_status(data[1:])

    def prepare_tc(self, tc, target):
        match tc:
            case TC_GET_STATUS:
                self.send_get_status(target)

    # Type = TC
    # DATA = 0x01 -> GET_STATUS
    def send_get_status(self, target):
        packet = build_ccsds_packet(TC, target, 0, self.seq_cnt, [TC_GET_STATUS])
        self.send(packet, target)
        print(f"SENDING TC_GET_STATUS")

    def print_obdh_status(self, data):
        mode = data[0]
        uptime_h = data[1]
        uptime_m = data[2]
        uptime_l = data[3]
        temperature_h = data[4]
        temperature_l = data[5]
        voltage_h = data[6]
        voltage_l = data[7]

        temperature = temperature_l | (temperature_h << 8)
        voltage = voltage_l | (voltage_h << 8)

        uptime = uptime_l | (uptime_m << 8) | (uptime_h << 16)
        temperature = temperature * 0.01
        voltage = voltage * 0.01

        print(f"""TM_SEND_STATUS from OBDH:
Mode:\t\t{mode}
Uptime:\t\t{uptime}
Temperature:\t{temperature}
Voltage:\t{voltage}\n""")