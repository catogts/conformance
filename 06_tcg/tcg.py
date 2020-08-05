#
#  BSD LICENSE
#
#  Copyright (c) Crane Chu <cranechu@gmail.com>
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in
#      the documentation and/or other materials provided with the
#      distribution.
#    * Neither the name of Intel Corporation nor the names of its
#      contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# -*- coding: utf-8 -*-


import enum
import time
import pytest
import struct 
import logging

from nvme import *


class OPAL_TOKEN(enum.IntEnum):
    TRUE = 0x01
    FALSE = 0x00
    TABLE = 0x00
    STARTROW = 0x01
    ENDROW = 0x02
    STARTCOLUMN = 0x03
    ENDCOLUMN = 0x04
    VALUES = 0x01
    PIN = 0x03
    RANGESTART = 0x03
    RANGELENGTH = 0x04
    READLOCKENABLED = 0x05
    WRITELOCKENABLED = 0x06
    READLOCKED = 0x07
    WRITELOCKED = 0x08
    ACTIVEKEY = 0x0A
    MAXRANGES = 0x04
    MBRENABLE = 0x01
    MBRDONE = 0x02
    HOSTPROPERTIES = 0x00
    STARTLIST = 0xF0
    ENDLIST = 0xF1
    STARTNAME = 0xF2
    ENDNAME = 0xF3
    CALL = 0xF8
    ENDOFDATA = 0xF9
    ENDOFSESSION = 0xFA
    STARTTRANSACTON = 0xFB
    ENDTRANSACTON = 0xFC
    EMPTYATOM = 0xFF
    WHERE = 0x00
    LIFECYCLE = 0x06
    AUTH_ENABLE = 0x05
    BOOLEAN_EXPR = 0x03

        
class OPAL_UID(enum.IntEnum):
    # user
    SMUID = 0
    THISSP = 1 
    ADMINSP = 2
    LOCKINGSP = 3 
    ANYBODY = 4
    SID = 5
    ADMIN1 = 6
    USER1 = 7
    USER2 = 8

    # table
    LOCKINGRANGE_GLOBAL = 9
    LOCKINGRANGE_ACE_RDLOCKED = 10
    LOCKINGRANGE_ACE_WRLOCKED = 11
    MBRCONTROL = 12
    MBR = 13
    AUTHORITY_TABLE = 14
    C_PIN_TABLE = 15
    LOCKING_INFO_TABLE = 16
    PSID = 17

    # C_PIN
    C_PIN_MSID = 18
    C_PIN_SID = 19
    C_PIN_ADMIN1 = 20 
    C_PIN_USER1 = 21

    # half
    HALF_AUTHORITY_OBJ_REF = 22
    HALF_BOOLEAN_ACE = 23


class OPAL_METHOD(enum.IntEnum):
    PROPERTIES = 0
    STARTSESSION = 1
    REVERT = 2
    ACTIVATE = 3
    NEXT = 4
    GETACL = 5
    GENKEY = 6
    REVERTSP = 7
    GET = 8
    SET = 9
    AUTHENTICATE = 10
    RANDOM = 11


opal_uid_table = {
    OPAL_UID.SMUID: [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff],
    OPAL_UID.THISSP: [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01],
    OPAL_UID.ADMINSP: [0x00, 0x00, 0x02, 0x05, 0x00, 0x00, 0x00, 0x01],
    OPAL_UID.LOCKINGSP: [0x00, 0x00, 0x02, 0x05, 0x00, 0x00, 0x00, 0x02],
    OPAL_UID.ANYBODY: [0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x01],
    OPAL_UID.SID: [0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x06],
    OPAL_UID.ADMIN1: [0x00, 0x00, 0x00, 0x09, 0x00, 0x01, 0x00, 0x01],
    OPAL_UID.USER1: [0x00, 0x00, 0x00, 0x09, 0x00, 0x03, 0x00, 0x01],
    OPAL_UID.USER2: [0x00, 0x00, 0x00, 0x09, 0x00, 0x03, 0x00, 0x02],
    OPAL_UID.LOCKINGRANGE_GLOBAL: [0x00, 0x00, 0x08, 0x02, 0x00, 0x00, 0x00, 0x01],
    OPAL_UID.LOCKINGRANGE_ACE_RDLOCKED: [0x00, 0x00, 0x00, 0x08, 0x00, 0x03, 0xE0, 0x01],
    OPAL_UID.LOCKINGRANGE_ACE_WRLOCKED: [0x00, 0x00, 0x00, 0x08, 0x00, 0x03, 0xE8, 0x01],
    OPAL_UID.MBRCONTROL: [0x00, 0x00, 0x08, 0x03, 0x00, 0x00, 0x00, 0x01],
    OPAL_UID.MBR: [0x00, 0x00, 0x08, 0x04, 0x00, 0x00, 0x00, 0x00],
    OPAL_UID.AUTHORITY_TABLE: [0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x00],
    OPAL_UID.C_PIN_TABLE: [0x00, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x00, 0x00],
    OPAL_UID.LOCKING_INFO_TABLE: [0x00, 0x00, 0x08, 0x01, 0x00, 0x00, 0x00, 0x01],
    OPAL_UID.PSID: [0x00, 0x00, 0x00, 0x09, 0x00, 0x01, 0xff, 0x01],
    OPAL_UID.C_PIN_MSID: [0x00, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x84, 0x02],
    OPAL_UID.C_PIN_SID: [0x00, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x00, 0x01],
    OPAL_UID.C_PIN_ADMIN1: [0x00, 0x00, 0x00, 0x0B, 0x00, 0x01, 0x00, 0x01],
    OPAL_UID.C_PIN_USER1: [0x00, 0x00, 0x00, 0x0B, 0x00, 0x03, 0x00, 0x01],
    OPAL_UID.HALF_AUTHORITY_OBJ_REF: [0x00, 0x00, 0x0C, 0x05, 0xff, 0xff, 0xff, 0xff],
    OPAL_UID.HALF_BOOLEAN_ACE: [0x00, 0x00, 0x04, 0x0E, 0xff, 0xff, 0xff, 0xff]
}


opal_method_table = {
    OPAL_METHOD.PROPERTIES: [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x01],
    OPAL_METHOD.STARTSESSION: [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x02],
    OPAL_METHOD.REVERT: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x02, 0x02],
    OPAL_METHOD.ACTIVATE: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x02, 0x03],
    OPAL_METHOD.NEXT: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x08],
    OPAL_METHOD.GETACL: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x0d],
    OPAL_METHOD.GENKEY: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x10],
    OPAL_METHOD.REVERTSP: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x11],
    OPAL_METHOD.GET: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x16],
    OPAL_METHOD.SET: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x17],
    OPAL_METHOD.AUTHENTICATE: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x1c],
    OPAL_METHOD.RANDOM: [0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x06, 0x01]
}


class Command(Buffer):
    def __init__(self, comid):
        self[:8] = struct.pack('>IHH', 0, comid, 0)
        self.pos = 0x38

    def append_u8(self, val):
        logging.debug(val)
        self[self.pos:] = struct.pack('>B', val)
        self.pos += 1

    def append_8_u8(self, val):
        self[self.pos:] = struct.pack('>BBBBBBBB', *val)
        self.pos += 8
        
    def append_token_call(self):
        self.append_u8(0xf8)

    def append_token_uid(self, u):
        self.append_u8(0xa8)
        self.append_8_u8(opal_uid_table[u])
        
    def append_token_method(self, m):
        logging.debug(m)
        self.append_u8(0xa8)
        self.append_8_u8(opal_method_table[m])

    def append_token_list(self, *val_list):
        for val in val_list:
            self.append_u8(int(val))
        
    def start_anybody_adminsp_session(self):
        self.append_token_call()
        self.append_token_uid(OPAL_UID.SMUID)
        self.append_token_method(OPAL_METHOD.STARTSESSION)
        self.append_token_list(0xf0, 0x81, 0x69)
        self.append_token_uid(OPAL_UID.ADMINSP)
        self.append_token_list(1, 0xf1)
        self.append_token_list(0xf9, 0xf0, 0, 0, 0, 0xf1)
        self[16:] = struct.pack('>I', 0x4c)
        self[40:] = struct.pack('>I', 0x34)
        self[52:] = struct.pack('>I', 0x27)

    def get_msid_cpin_pin(self):
        self.append_token_call()
        self.append_token_uid(OPAL_UID.C_PIN_MSID)
        self.append_token_method(OPAL_METHOD.GET)
        self.append_token_list(OPAL_TOKEN.STARTLIST,
                               OPAL_TOKEN.STARTLIST,
                               OPAL_TOKEN.STARTNAME,
                               OPAL_TOKEN.STARTCOLUMN,
                               OPAL_TOKEN.PIN,
                               OPAL_TOKEN.ENDNAME,
                               OPAL_TOKEN.STARTNAME,
                               OPAL_TOKEN.ENDCOLUMN,
                               OPAL_TOKEN.PIN,
                               OPAL_TOKEN.ENDNAME,
                               OPAL_TOKEN.ENDLIST,
                               OPAL_TOKEN.ENDLIST)
        self.append_token_list(0xf9, 0xf0, 0, 0, 0, 0xf1)
        self[16:] = struct.pack('>I', 0x4c)
        self[20:] = struct.pack('>I', 0x101d)
        self[24:] = struct.pack('>I', 0x69)
        self[40:] = struct.pack('>I', 0x34)
        self[52:] = struct.pack('>I', 0x25)
        

class Responce(Buffer):
    def level0_discovery(self):
        total_length, ver, _ = struct.unpack('>IIQ', self[:16])
        total_length += 4
        offset = 48
        while offset < total_length:
            feature, version, length = struct.unpack('>HBB', self[offset:offset+4])
            version >>= 4
            length += 4

            # parse discovery responce buffer
            logging.info((offset, feature, version, length))
            if feature == 0x303:
                # pyrite 2.0
                comid, = struct.unpack('>H', self[offset+4:offset+6])
                
            offset += length
        assert offset == total_length
        
        return comid
        

def test_pyrite_discovery0(nvme0):
    r = Responce()
    nvme0.security_receive(r, 1).waitdone()
    logging.info(r.dump(256))
    r.level0_discovery()

    
def test_take_ownership(nvme0):
    r = Responce()
    nvme0.security_receive(r, 1, size=2048).waitdone()
    comid = r.level0_discovery()
    logging.info(r.dump(256))
    
    c = Command(comid)
    c.start_anybody_adminsp_session()
    logging.info(c.dump(256))
    
    nvme0.security_send(c, comid, size=2048).waitdone()
    nvme0.security_receive(r, comid, size=2048).waitdone()
    logging.info(r.dump(256))

    c = Command(comid)
    c.get_msid_cpin_pin()
    logging.info(c.dump(256))
    
    nvme0.security_send(c, comid, size=2048).waitdone()
    nvme0.security_receive(r, comid, size=2048).waitdone()
    logging.info(r.dump(256))
    
    

