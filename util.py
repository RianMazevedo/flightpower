import struct
from dataclasses import dataclass

@dataclass
class EEPROM:
    pid_p: float = 1.0
    pid_i: float = 1.0
    pid_d: float = 1.0
    vlt_offset: float = 1.0
    cur_offset: float = 1.0
    max_power: int = 100
    average: int = 0

    @classmethod
    def from_bytes(cls, data_bytes: bytes):
        fmt = "<fffffHH"
        try:
            return cls(*struct.unpack(fmt, data_bytes))
        except struct.error:
            return None


@dataclass
class TELEMETRY:
    voltage: float = 0.0
    current: float = 0.0
    power: float = 0.0
    receiver_throttle: int = 0
    effective_throttle: int = 0

    @classmethod
    def from_bytes(cls, data_bytes: bytes):
        fmt = "<fffBB"
        try:
            return cls(*struct.unpack(fmt, data_bytes))
        except struct.error:
            return None