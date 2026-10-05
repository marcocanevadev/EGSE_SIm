from abc import ABC, abstractmethod
from transport.marcowire import PacketReceiver, PacketSender, RxState

class BaseComponent(ABC):
    def __init__(self, apid: int):
        self.apid = apid
        self.links: dict[int, Link] = {}

    def add_link(self, apid: int):
        new_link = Link(self.apid, apid)
        self.links[apid] = new_link

    def listen(self):
        for link in self.links.values():
            link.listen()

    def get_apid(self):
        return self.apid

    def send(self, packet, target):
        for apid in self.links.keys():
            if apid == target:
                link = self.links[apid]
                link.send(packet, target)

    def receive_byte(self, byte: int, sender: int):
        for apid in self.links.keys():
            if apid == sender:
                link = self.links[apid]
                link.receive_byte(byte)

    def have_bytes(self) -> bool:
        res = False
        for link in self.links.values():
            if link.have_bytes():
                res = True
                break
        return res

    def get_next_byte(self) -> list[tuple[int, int]]:
        res = []
        for link in self.links.values():
            if link.have_bytes():
                next_byte = link.get_next_byte()
                if not(next_byte is None):
                    res.append(next_byte)
        return res

    def has_packets(self) -> bool:
        res = False
        for link in self.links.values():
            if link.has_packets():
                res = True
                break
        return res

    def get_receiver_state(self) -> list[tuple[RxState,int]]:
        states = []
        for apid in self.links.keys():
            link = self.links[apid]
            state = link.get_receiver_state()
            tupla = (state, apid)
            states.append(tupla)
        return states


    @abstractmethod
    def process(self):
        pass


class BaseInternalComponent(BaseComponent):
    def __init__(self, apid: int):
        super().__init__(apid)
        self.uptime = 0
        self.mode = 0
        self.seq_cnt = 0

    def tick(self):
        self.uptime += 1

    @abstractmethod
    def simulate(self):
        pass

class Link():
    def __init__(self, in_apid: int, out_apid: int):
        self.in_apid = in_apid
        self.out_apid = out_apid
        self.tx = PacketSender()
        self.rx = PacketReceiver()

    def listen(self):
        self.rx.listen()

    def receive_byte(self, byte: int):
        self.rx.process_byte(byte)

    def have_bytes(self) -> bool:
        return self.tx.have_bytes()

    def get_next_byte(self) -> tuple[int, int] | None:
        return self.tx.get_next_byte()

    def has_packets(self) -> bool:
        return self.rx.has_packets()

    def get_receiver_state(self) -> RxState:
        return self.rx.get_state()

    def get_packet(self):
        return self.rx.get_packet()

    def send(self, packet, target):
        self.tx.send(packet, target)