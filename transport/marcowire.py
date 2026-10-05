# PROTOCOLLO MARCO-WIRE
#   SYNC --> 0xCD
#   LEN  --> 3 byte (24 byte) (pkt len di ccsds ha 16 bit)
#   DATA --> N byte
#   CRC  --> 1 byte


from enum import Enum
SYNC = 0xCD
LEN_BYTES_N = 3

class RxState(Enum):
    STANDBY = 0
    WAIT_SYNC = 1
    READ_LEN = 2
    READ_DATA = 3
    READ_CRC = 4

class MarcoWireStatus(Enum):
    OK = 0
    BAD_CRC = 1

class PacketReceiver:
    def __init__(self):
        self.state = RxState.STANDBY
        self.buffer = bytearray()
        self.packets = list()
        self.len_byte_n = 0
        self.data_len = 0
        self.data_received = 0
        self.len_shift = (LEN_BYTES_N - 1) * 8
        self.crc = 0

    def __reset_variables(self):
        self.buffer.clear()
        self.len_byte_n = 0
        self.data_len = 0
        self.data_received = 0
        self.len_shift = (LEN_BYTES_N - 1) * 8
        self.crc = 0

    def __verify_marcowire_packet(self, crc: int) -> MarcoWireStatus:
        crc_test = self.crc & 0xFF
        if crc == crc_test:
            return MarcoWireStatus.OK
        else:
            return MarcoWireStatus.BAD_CRC

    def has_packets(self) -> bool:
        if len(self.packets) == 0:
            return False
        else:
            return True

    def reset(self):
        self.packets.clear()
        self.__reset_variables()
        self.state = RxState.STANDBY

    def listen(self):
        self.state = RxState.WAIT_SYNC

    def stop(self):
        self.state = RxState.STANDBY

    def get_packet(self):
        if len(self.packets) == 0:
            return None
        packet = self.packets[0]
        self.packets = self.packets[1:]
        return packet

    def get_state(self) -> RxState:
        status = self.state
        return status

    def process_byte(self, byte: int):
        if self.state == RxState.WAIT_SYNC:
            if byte == SYNC:
                self.state = RxState.READ_LEN
                self.crc += byte

        elif self.state == RxState.READ_LEN:
            self.data_len += byte << self.len_shift
            self.len_shift -= 8
            self.len_byte_n += 1
            self.crc += byte
            if self.len_byte_n == LEN_BYTES_N:
                if self.data_len == 0:
                    self.state = RxState.READ_CRC
                else:
                    self.state = RxState.READ_DATA

        elif self.state == RxState.READ_DATA:
            self.buffer.append(byte)
            self.crc += byte
            self.data_received = self.data_received +1
            if self.data_received == self.data_len:
                self.state = RxState.READ_CRC

        elif self.state == RxState.READ_CRC:
            
            marcowire_status = self.__verify_marcowire_packet(byte)
            if marcowire_status == MarcoWireStatus.OK:
                self.packets.append(self.buffer.copy())
            self.__reset_variables()
            self.state = RxState.WAIT_SYNC

    

class PacketSender:

    def __init__(self):
        self.tx_queue = []
        self.apid_queue = []

    def clear_tx_queue(self):
        self.tx_queue.clear()

    def have_bytes(self) -> bool:
        if len(self.tx_queue) == 0:
            return False
        else: 
            return True

    def get_next_byte(self) -> tuple[int, int] | None:
        if len(self.tx_queue) == 0 or len(self.apid_queue) == 0:
            return None
        else:
            byte = self.tx_queue[0]
            target = self.apid_queue[0]
            self.tx_queue = self.tx_queue[1:]
            self.apid_queue = self.apid_queue[1:]
            return (byte, target)

    def send(self, payload, target):
        data_len = len(payload)
        data_len_l = data_len & 0xFF
        data_len = data_len >> 8
        data_len_m = data_len & 0xFF
        data_len = data_len >> 8
        data_len_h = data_len & 0xFF

        crc = sum([SYNC, 
                   data_len_h, 
                   data_len_m, 
                   data_len_l,
                   *payload]) & 0xFF
     
        marcowire_packet = [
            SYNC,
            data_len_h,
            data_len_m,
            data_len_l,
            *payload,
            crc
        ]
        for i in range(len(marcowire_packet)):
            self.tx_queue.append(marcowire_packet[i])
            self.apid_queue.append(target)


        

    