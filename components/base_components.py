from abc import ABC, abstractmethod
from transport.marcowire import PacketReceiver, PacketSender, RxState

class BaseComponent(ABC):
    def __init__(self):
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


    @abstractmethod
    def process(self):
        pass


class BaseInternalComponent(BaseComponent):
    def __init__(self, apid: int):
        super().__init__()
        self.apid = apid
        self.uptime = 0
        self.mode = 0
        self.seq_cnt = 0

    def tick(self):
        self.uptime += 1

    @abstractmethod
    def simulate(self):
        pass

