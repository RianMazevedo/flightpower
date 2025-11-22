from util import EEPROM
from com import Communication, eeprom
from sdcard import SDCardConnection
from typing import Dict

import pickle
import time
import csv
import io

com = Communication()
sdcard = SDCardConnection()

class Plot:
    def __init__(self, samples=100, x_axis=None, y_axis=None):
        self.samples = samples
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.voltage = []
        self.current = []
        self.throttle_receiver = []
        self.throttle_effective = []

flight = Plot(samples=3000, x_axis=[0.0], y_axis=[0.0])

class AppConfig:
    def __init__(self, fillscreen=True, resolution_auto=False, font_size=20,
                 resolution_width=1280, resolution_height=720, sampling_frequency=25, time_now=0):
        self.fillscreen = fillscreen
        self.resolution_auto = resolution_auto
        self.font_size = font_size
        self.resolution_width = resolution_width
        self.resolution_height = resolution_height
        self.sampling_frequency = sampling_frequency
        self.resolution_list = ["800x600", "1024x768", "1280x720", "1920x1080"]
        self.draw_sampling_list = ["5", "10", "25", "40"]
        self.time_now = time_now

    def save(self, filename="config.config"):
        with open(filename, "wb") as f:
            pickle.dump([
                self.fillscreen, self.resolution_auto, self.font_size,
                self.resolution_width, self.resolution_height, self.sampling_frequency
            ], f)

    @staticmethod
    def load(filename="config.config"):
        try:
            with open(filename, "rb") as f:
                values = pickle.load(f)
                return AppConfig(*values)
        except FileNotFoundError:
            return AppConfig()

    @staticmethod
    def process_from_sdcard(filename):
        data = sdcard.load_file(filename)

        if not data:
            print("[debug] -> No data to process.")
            return False

        f = io.StringIO("".join(data))
        reader = csv.DictReader(f, delimiter=';')

        temp_time, temp_voltage, temp_current, temp_power = [], [], [], []
        temp_thr_recv, temp_thr_eff = [], []

        for row in reader: # type: Dict[str, str]
            try:
                temp_time.append(float(row['Tempo(S)']))
                temp_voltage.append(float(row['Tensao(V)']))
                temp_current.append(float(row['Corrente(A)']))
                temp_power.append(float(row['Potencia(W)']))
                temp_thr_recv.append(int(row['Acel_receptor(%)']))
                temp_thr_eff.append(int(row['Acel_efetiva(%)']))
            except ValueError:
                continue

        step = max(1, len(temp_time) // flight.samples)
        flight.x_axis = temp_time[::step]
        flight.y_axis = temp_power[::step]
        flight.voltage = temp_voltage[::step]
        flight.current = temp_current[::step]
        flight.throttle_receiver = temp_thr_recv[::step]
        flight.throttle_effective = temp_thr_eff[::step]

        print(f"[debug] -> Flight data loaded: {len(flight.x_axis)} points.")
        return True


    def edit_app(self, sender, data=None, gui_callback=None):
        def set_resolution(data):
            self.resolution_width, self.resolution_height = map(int, data.split('x'))

        APPactions = {
            'save_config': lambda: self.save(),
            'font_size': lambda data: setattr(self, 'font_size', data),
            'resolution_auto': lambda data: setattr(self, 'resolution_auto', data),
            'sampling_frequency': lambda data: setattr(self, 'sampling_frequency', data),
            'resolution_list': lambda data: set_resolution(data),
            'COM_available_ports': lambda data: com.connect(data),
            'COM_search_button': lambda: gui_callback(),
            'download_eeprom': lambda: gui_callback() if com.download_stm_eeprom() else None,
            'upload_eeprom': lambda: com.upload_stm_eeprom(eeprom),
            'sensors_average': lambda data: setattr(eeprom,'average', round(data, 3)),
            'max_power': lambda data: setattr(eeprom,'max_power', round(data, 3)),
            'voltage_offset': lambda data: setattr(eeprom,'vlt_offset', round(data, 3)),
            'current_offset': lambda data: setattr(eeprom,'cur_offset', round(data, 3)),
            'pid_p': lambda data: setattr(eeprom,'pid_p', round(data, 3)),
            'pid_i': lambda data: setattr(eeprom,'pid_i', round(data, 3)),
            'pid_d': lambda data: setattr(eeprom,'pid_d', round(data, 3)),
            'sd_connect_bt': lambda: sdcard.automatic_connection(),
            'sd_clear_bt': lambda: print("CLEAR BT"),
            'sd_file_load': lambda data: gui_callback() if self.process_from_sdcard(data) else None
        }

        if sender in APPactions:
            if data is not None:
                APPactions[sender](data)
            else:
                APPactions[sender]()