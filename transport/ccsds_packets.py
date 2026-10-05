# ---------------------- CCSDS PACKET ---------------------------  
# 1° WORD - 16 bit - 0xAAAA
# 15                0
# +---+---+---+-----------+
# |VER|TYP|SHF|   APID    |
# +---+---+---+-----------+

# VER   3 bit   --> const = 0                   Version
# TYP   1 bit   --> 0 = TM, 1 = TC              Type
# SHF   1 bit   --> 0 = absent, 1 = present     Second header flag)
# APID 11 bit   --> [0:2047]
# ---------------------------------------------------------------
# 2° WORD - 16 bit
# 15               0
# +--+-------------+
# |SF| SEQ COUNT   |
# +--+-------------+
#
# SF  = 2 bit   --> [0:3]       Sequence flags
# SEQ = 14 bit  --> [0:16383]   Sequence count
# ---------------------------------------------------------------
# 3° WORD - 16 bit
# 15               0
# +----------------+
# |    pkt_len     |
# +----------------+
#
# PACKET_LENGTH --> [0:2^16-1]
# ---------------------------------------------------------------
# N - WORDS
# DATA
# ---------------------------------------------------------------
# CRC - 8 bit
# ---------------------------------------------------------------
from enum import Enum

class VerifyCCSDSStatus(Enum):
    OK = 0
    TOO_SHORT = 1
    TOO_LONG = 2
    BAD_LEN = 3
    BAD_CRC = 4

TWO_TO_THE_16 = 2**16
TWO_TO_THE_14 = 2**14
TWO_TO_THE_11 = 2**11
TWO_TO_THE_2 = 4

SECOND_HEADER_LENGTH = 2

MIN_FRAME_LENGTH = 7
MAX_FRAME_LENGTH = MIN_FRAME_LENGTH + (TWO_TO_THE_16 - 1) + SECOND_HEADER_LENGTH

APID_MASK = 0b0000011111111111
SEQ_MASK  = 0b0011111111111111

def build_ccsds_packet(
        pkt_type: int,
        apid: int,
        seq_flags: int,
        seq_count: int,
        data: list[int] | bytes | None = None,
        sec_hdr: list[int] | None = None
    ) -> bytes | None:

    # check inputs
    if pkt_type < 0 or pkt_type > 1:
        return None
    if apid < 0 or apid > TWO_TO_THE_11 - 1:
        return None
    if seq_flags < 0 or seq_flags > TWO_TO_THE_2 - 1:
        return None
    if seq_count < 0 or seq_count > TWO_TO_THE_14 - 1:
        return None

    if data is None:
        pkt_len = 0
        data = []
    else:
        pkt_len = len(data)
    
    if sec_hdr is None:
        sec_hdr_flg = 0
        sec_hdr = []
    else:
        sec_hdr_flg = 1

    # build word 1,2,3

    ver = 0

    word1 = apid | sec_hdr_flg << 11
    word1 |= pkt_type << 12
    word1 |= ver << 13

    word2 = seq_count | seq_flags << 14

    word3 = pkt_len

    # unpack words in bytes

    word1_l = word1 & 0xFF
    word1_h = word1 >> 8

    word2_l = word2 & 0xFF
    word2_h = word2 >> 8

    word3_l = word3 & 0xFF
    word3_h = word3 >> 8
    
    # calculate CRC and pack msg

    crc = sum([word1_h, word1_l, 
              word2_h, word2_l,
              word3_h, word3_l,
              *data, *sec_hdr]) & 0xFF

    frame = bytes([
        word1_h,
        word1_l,
        word2_h,
        word2_l,
        word3_h,
        word3_l,
        *sec_hdr,
        *data,
        crc,
    ])

    return frame  

def parse_ccsds_packet(frame: bytes) -> dict[str, int | list[int]] | None:
    status = verify_ccsds_packet(frame)
    if status != VerifyCCSDSStatus.OK:
        print(status)
        return None

    #get header
    # WORD 1

    word1 = get_word_from_frame(0, 1, frame)

    apid = word1 & APID_MASK
    shf = (word1 >> 11) & 0b1 
    typ = (word1 >> 12) & 0b1
    ver = word1 >> 13

    # WORD 2
    word2 = get_word_from_frame(2, 3, frame)

    seq_cnt = word2 & SEQ_MASK
    seq_flg = (word2 >> 14)

    # WORD 3
    word3 = get_word_from_frame(4, 5, frame)

    pkt_len = word3

    content: dict[str, int | list[int]] = {
            "ver": ver,
            "type": typ,
            "shf": shf,
            "apid": apid,
            "seq_flg": seq_flg,
            "seq_cnt": seq_cnt,
            "pkt_len": pkt_len,
        }

    # extract 2nd header and data
    data_idx = 6

    if shf == 1:
        sh_h = frame[6]
        sh_l = frame[7]
        sh = sh_l | (sh_h << 8)
        data_idx = 8
        content["sh"] = sh

    data = []

    for i in range(pkt_len):
        data.append(frame[i + data_idx])

    content["data"] = data

    return content

def get_word_from_frame(idx_h: int, idx_l: int, frame: bytes) -> int:
    word_h = frame[idx_h]
    word_l = frame[idx_l]
    word = word_l | word_h << 8
    return word
    

def verify_ccsds_packet(frame: bytes) -> VerifyCCSDSStatus:

    frame_len = len(frame)
    if frame_len < MIN_FRAME_LENGTH:
        return VerifyCCSDSStatus.TOO_SHORT
    
    if frame_len > MAX_FRAME_LENGTH:
        return VerifyCCSDSStatus.TOO_LONG

    # WORD 3
    word3 = get_word_from_frame(4, 5, frame)
    pkt_len = word3

    shf = frame[0] >> 3 & 1
    
    check_len = MIN_FRAME_LENGTH
    
    if shf:
        check_len += SECOND_HEADER_LENGTH
        
    if frame_len != pkt_len + check_len:
        return VerifyCCSDSStatus.BAD_LEN

    crc = sum(frame[:-1]) & 0xFF
    crc_to_test = frame[-1]

    if crc != crc_to_test:
        return VerifyCCSDSStatus.BAD_CRC

    return VerifyCCSDSStatus.OK
    


