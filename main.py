from components.obdh import OBDH
from components.egse import EGSE
from components.payload import Payload
from constants import *
from components.base_components import *


TICK_TARGET = 5000
TC_LIST = [
    (100, TC_GET_STATUS, OBDH_APID), 
    (2000, TC_GET_STATUS, OBDH_APID), 
    ]

def transmit(egse: BaseComponent, components: list[BaseInternalComponent], components_match_apids: dict[int, BaseComponent]):
    if egse.have_bytes():
        transmit_byte(egse,  components_match_apids)

    for component in components:
        if component.have_bytes():
            transmit_byte(component, components_match_apids)

def transmit_byte(sender: BaseComponent, components_match_apids: dict[int, BaseComponent]):
    outputs = sender.get_next_byte()
    sender_apid = sender.get_apid()
    if len(outputs) == 0:
        return
    for output in outputs:
        byte = output[0]
        target = output[1]
        receiver = components_match_apids[target]
        receiver.receive_byte(byte, sender_apid)

def process(egse: EGSE, components: list[BaseInternalComponent]):
    if egse.has_packets():
        egse.process()
    for component in components:
        if component.has_packets():
            component.process()

def simulate(components: list[BaseInternalComponent]):
    for component in components:
        component.simulate()

def tick(components: list[BaseInternalComponent]):
    for component in components:
        component.tick()

def main():
    egse = EGSE(EGSE_APID)
    obdh = OBDH(OBDH_APID)
    payload = Payload(PAYLOAD_APID)

    egse.add_link(OBDH_APID) 
    payload.add_link(OBDH_APID)   
    obdh.add_link(EGSE_APID)
    obdh.add_link(PAYLOAD_APID)



    components: list[BaseInternalComponent] = [
        obdh,
        payload]
    components_match_apids: dict[int, BaseComponent] = {
        EGSE_APID: egse,
        OBDH_APID: obdh,
        PAYLOAD_APID: payload,
        
    } 
    tc_list = TC_LIST.copy()
    obdh.listen()
    egse.listen()
    main_tick = 0
    next_tc = tc_list[0]
    tc_list = tc_list[1:]
    tc_num = 0
    #main simulation loop 1 loop = 1ms
    while True:
        tick(components)

        if next_tc[0] == main_tick:
            tc_num += 1
            print(f"sending {tc_num}")
            egse.prepare_tc(next_tc[1], next_tc[2])
            if len(tc_list)> 0:
                next_tc = tc_list[0]
                tc_list = tc_list[1:]
        
        simulate(components)
        transmit(egse, components, components_match_apids)
        process(egse, components)

        main_tick += 1
        if main_tick == TICK_TARGET:
            break

if __name__ == "__main__":
    main()



    

