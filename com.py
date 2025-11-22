import threading
import serial
import serial.tools.list_ports
import time
import ast
import struct
import queue

from util import EEPROM, TELEMETRY
from serial.serialutil import SerialException

eeprom = EEPROM()
telemetry = TELEMETRY()

class Communication:
    def __init__(self):
        self.stm_connected = False
        self.available_ports = []
        self.selected_port = None
        self.serial = None
        self.data_frequency = 30
        self.timeout = 0.025
        self.lock_queue = False
        self.STX = 0x02
        self.ETX = 0x03
        self.CMD_COM_TEST = 0x04
        self.CMD_GET_DATA = 0x05
        self.CMD_DWL_EEPROM = 0x06
        self.CMD_UPL_EEPROM = 0x07
        self.lock = threading.Lock()
        self.requests = queue.Queue()
        self.thread = threading.Thread(target=self.requests_engine, daemon=True)
        self.thread.start()

        self.last_tick_time = time.time()
        self.tick_rate = 0.0  # tick/s instantâneo

    def requests_engine(self):
        """Motor de requisições, isso cria uma fila de requisições e garante que esteja organizado."""
        while True:
            try:
                func, args, kwargs, result_queue = self.requests.get(timeout=self.timeout)
                with self.lock:
                    result = func(*args, **kwargs)
                    if result_queue:
                        result_queue.put(result)
            except queue.Empty:
                continue

    def request(self, func, *args, wait_response=True, **kwargs):
        """Função que insere um request na fila de requisições"""
        result_queue = queue.Queue() if wait_response else None
        self.requests.put((func, args, kwargs, result_queue))
        if wait_response:
            result = result_queue.get()
            if result is None:
                resul = (False, None)
            if func.__name__ == "send_stm_data" and args and args[1] == self.CMD_UPL_EEPROM:
                self.lock_queue = False
            return result
        return None

    def search_ports(self):
        """Busca as portas COM disponíveis"""
        self.available_ports = [
            (port, desc) for port, desc, hwid in sorted(serial.tools.list_ports.comports())
        ]
        return self.available_ports

    def connect(self, data, baudrate=115200):
        """Conecta ao STM com Baudrate padrão de 115200 bits/s"""
        data = ast.literal_eval(data)

        self.selected_port = data[0]
        if not self.selected_port:
            return False
        try:
            self.serial = serial.Serial(port=self.selected_port, baudrate=baudrate, timeout=self.timeout, write_timeout=self.timeout)
            check, data = self.request(self.send_stm_data, "COM-TEST", self.CMD_COM_TEST)
            if check and data == b"CONNECTED":
               self.stm_connected = True
               print("[debug] -> Conectado com sucesso a porta " + self.selected_port)
            else:
               self.serial.close()
               raise Exception("[debug] -> Este dispositivo nao respondeu corretamente.")
            return True
        except Exception as failure:
            self.stm_connected = False
            print(failure)
            return False

    def check_stm_data(self):
        """Checa a resposta do STM se está no padrão STX/ETX"""
        if not self.serial:
            return False, None
        try:
            start = self.serial.read(1)
            if not start or start[0] != self.STX:
                return False, None

            command = self.serial.read(1)
            if not command:
                return False, None
            command = command[0]

            length = self.serial.read(1)
            if not length:
                return False, None
            length = length[0]

            data_bytes = self.serial.read(length)
            if len(data_bytes) != length:
                return False, None

            checksum = self.serial.read(1)
            if not checksum:
                return False, None
            checksum = checksum[0]

            end = self.serial.read(1)
            if not end or end[0] != self.ETX:
                return False, None

            calc = command ^ length
            for b in data_bytes:
                calc ^= b
            if calc != checksum:
                return False, None
            return True, data_bytes

        except SerialException as e:
            print(f"[debug] -> Erro de leitura serial: {e}")
            self.handle_serial_disconnect()
            return False, None

    def send_stm_data(self, data, command):
        """Envia dados ao stm via protocolo STX/ETX"""
        if not self.serial:
            return False
        try:
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, (tuple, list)):
                fmt = '<fffffHH'
                data_bytes = struct.pack(fmt, *data)
            else:
                raise TypeError("[debug] -> Tipo de dado não suportado.")

            length = len(data_bytes)

            checksum = command ^ length
            for b in data_bytes:
                checksum ^= b

            message = bytearray()
            message.append(self.STX)
            message.append(command)
            message.append(length)
            message.extend(data_bytes)
            message.append(checksum)
            message.append(self.ETX)

            self.serial.write(message)

            check, data = self.check_stm_data()
            if check:
                return check, data
            return False, None

        except (SerialException, serial.SerialTimeoutException) as e:
            print(f"[debug] -> Erro de comunicação serial: {e}")
            self.handle_serial_disconnect()
            return False, None

    def handle_serial_disconnect(self):
        """Trata desconexão do dispositivo sem travar o programa."""
        self.stm_connected = False
        if self.serial:
            try:
                self.serial.close()
            except Exception:
                pass
            self.serial = None
        print("[debug] -> Dispositivo desconectado da porta serial.")

    def upload_stm_eeprom(self, eeprom):
        """Envia dados à EEPROM do STM via protocolo STX/ETX"""
        if not self.serial:
            return False

        values = (eeprom.pid_p, eeprom.pid_i, eeprom.pid_d, eeprom.vlt_offset,
                  eeprom.cur_offset, eeprom.max_power, eeprom.average)


        self.lock_queue = True
        self.serial.reset_input_buffer()
        return self.request(self.send_stm_data, values, self.CMD_UPL_EEPROM)


    def download_stm_eeprom(self):
        """Recebe dados à EEPROM do STM via protocolo STX/ETX"""
        if not self.serial:
            return False

        self.lock_queue = True
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        check, data = self.request(self.send_stm_data, "DWL-EEPROM", self.CMD_DWL_EEPROM)

        #print(f"[debug] -> tick/s = {self.tick_rate:.2f}, port = [{self.selected_port}], valid = {check}, data = {data}")

        if check:
            updated = EEPROM.from_bytes(data)
            eeprom.pid_p = updated.pid_p
            eeprom.pid_i = updated.pid_i
            eeprom.pid_d = updated.pid_d
            eeprom.vlt_offset = updated.vlt_offset
            eeprom.cur_offset = updated.cur_offset
            eeprom.max_power = updated.max_power
            eeprom.average = updated.average
            return check
        return False

    def get_stm_telemetry(self):
        """Requisita telemetria ao STM via protocolo STX/ETX"""
        if not self.serial and not self.lock_queue:
            return False

        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        check, data = self.request(self.send_stm_data, "GET-DATA", self.CMD_GET_DATA)

        now = time.time()
        delta = now - self.last_tick_time  # tempo desde a última chamada
        self.last_tick_time = now

        if delta > 0:
            self.tick_rate = 1.0 / delta  # frequência instantânea (Hz)

        #print(f"[debug] -> tick/s = {self.tick_rate:.2f}, port = [{self.selected_port}], valid = {check}, data = {data}")

        if check and data:
            updated = TELEMETRY.from_bytes(data)
            if updated:
                telemetry.voltage = round(updated.voltage, 2)
                telemetry.current = round(updated.current, 2)
                telemetry.power = round(updated.power, 2)
                telemetry.receiver_throttle = round(updated.receiver_throttle, 2)
                telemetry.effective_throttle = round(updated.effective_throttle, 2)
            return check
        return False