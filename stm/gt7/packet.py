try:
    from salsa20 import Salsa20_xor
except:
    from .pure_salsa20 import Salsa20_xor

import struct
from enum import Enum

class Flags(Enum):
    IN_RACE   = 0b0000000000000001
    PAUSED    = 0b0000000000000010
    LOADING   = 0b0000000000000100
    IN_GEAR   = 0b0000000000001000
    HAS_TURBO = 0b0000000000010000
    REV_LIMIT = 0b0000000000100000
    HANDBRAKE = 0b0000000001000000
    LIGHTS    = 0b0000000010000000
    LOWBEAM   = 0b0000000100000000
    HIGHBEAM  = 0b0000001000000000
    ASM       = 0b0000010000000000
    TCS       = 0b0000100000000000

class GT7DataPacket:

    # https://www.gtplanet.net/forum/threads/gt7-is-compatible-with-motion-rig.410728/page-4#post-13799643

    fmt = struct.Struct(
        "<"
        "4x"  # MAGIC                  / i   / 4x  / 0x0000
        "3f"  # POSITION               / 3f  / 12x / 0x0004
        "12x" # VELOCITY               / 3f  / 12x / 0x0010
        "12x" # ROTATION               / 3f  / 12x / 0x001C
        "4x"  # ROTATION_NORTH         / f   / 4x  / 0x0028
        "12x" # VELOCITY_ANGULAR       / 3f  / 12x / 0x002C
        "4x"  # RIDE_HEIGHT            / f   / 4x  / 0x0038
        "f"   # RPM                    / f   / 4x  / 0x003C
        "4x"  # IV                     / 4B  / 4x  / 0x0040
        "4x"  # CURRENT_FUEL           / f   / 4x  / 0x0044
        "4x"  # FUEL_CAPACITY          / f   / 4x  / 0x0048
        "f"   # SPEED                  / f   / 4x  / 0x004C
        "4x"  # TURBO_BOOST            / f   / 4x  / 0x0050
        "4x"  # OIL_PRESSURE           / f   / 4x  / 0x0054
        "4x"  # WATER_TEMP             / f   / 4x  / 0x0058
        "4x"  # OIL_TEMP               / f   / 4x  / 0x005C
        "16x" # TYRES_TEMP             / 4f  / 16x / 0x0060
        "i"   # TICK                   / i   / 4x  / 0x0070
        "2h"  # LAPS                   / 2h  / 4x  / 0x0074
        "i"   # BEST_LAPTIME           / i   / 4x  / 0x0078
        "i"   # LAST_LAPTIME           / i   / 4x  / 0x007C
        "4x"  # DAYTIME_PROGRESSION    / i   / 4x  / 0x0080
        "2h"  # RACE_POSITION          / 2h  / 4x  / 0x0084
        "2x"  # REV_UPSHIFT            / h   / 2x  / 0x0088
        "2x"  # REV_LIMIT              / h   / 2x  / 0x008A
        "2x"  # MAX_SPEED              / h   / 2x  / 0x008C
        "H"   # FLAGS                  / H   / 2x  / 0x008E
        "B"   # GEAR                   / B   / x   / 0x0090 / Suggested:Current
        "B"   # THROTTLE               / B   / x   / 0x0091
        "B"   # BRAKE                  / B   / x   / 0x0092
        "x"   # UNKNOWN                / B   / x   / 0x0093
        "16x" # ROAD_PLANE             / 4f  / 16x / 0x0094
        "16x" # WHEELS_SPEED           / 4f  / 16x / 0x00A4
        "16x" # TYRES_RADIUS           / 4f  / 16x / 0x00B4
        "16x" # TYRE_SUSPENSION_TRAVEL / 4f  / 16x / 0x00C4
        "32x" # UNKNOWN_RESRVED        / 32B / 32x / 0x00D4
        "4x"  # CLUCH                  / f   / 4x  / 0x00F4
        "4x"  # CLUCH_ENGAGEMENT       / f   / 4x  / 0x00F8
        "4x"  # CLUCH_RPM              / f   / 4x  / 0x00FC
        "4x"  # TOP_SPEED              / f   / 4x  / 0x0100
        "32x" # GEAR_RATIOS            / 8f  / 32x / 0x0104
        "I"   # CAR_CODE               / i   / 4x  / 0x0124
    )

    size = fmt.size

    def __init__(self, buf, encrypted=True):

        if encrypted:
            buf = self.decrypt(buf)

        (
            self.positionX,
            self.positionY,
            self.positionZ,
            self.rpm,
            self.speed,
            self.tick,
            self.current_lap,
            self.laps,
            self.best_laptime,
            self.last_laptime,
            self.race_position,
            self.opponents,
            self.flags,
            gear,
            self.throttle,
            self.brake,
            self.car_code
        )  = self.fmt.unpack(buf)

        self.gear = gear & 0x0F
        self.suggested_gear = (gear & 0xF0) >> 4

        self.paused = bool(self.flags & Flags.PAUSED.value)
        self.in_race = bool(self.flags & Flags.IN_RACE.value)

    @staticmethod
    def decrypt(dat):
        KEY = b'Simulator Interface Packet GT7 ver 0.0'
        oiv = dat[0x40:0x44]
        iv1 = int.from_bytes(oiv, byteorder='little')
        iv2 = iv1 ^ 0xDEADBEAF 
        IV = bytearray()
        IV.extend(iv2.to_bytes(4, 'little'))
        IV.extend(iv1.to_bytes(4, 'little'))
        ddata = Salsa20_xor(dat, bytes(IV), KEY[0:32])

        #check magic number
        magic = int.from_bytes(ddata[0:4], byteorder='little')
        if magic != 0x47375330:
            return bytearray(b'')
        return ddata