import threading
import gui
import time

timer_0 = time.time()
timer_1 = time.time()
timer_2 = time.time()
WAIT = lambda: time.sleep(0.001)

def primary_engine():
    global timer_0, timer_1, timer_2
    while True:
        if time.time() - timer_0 >= (1 / gui.com.data_frequency):
            timer_0 = time.time()
            gui.GUI_UPDATE()
            if gui.com.stm_connected:
                gui.com.get_stm_telemetry()
                gui.TELEMETRY_UPDATE()
        else:
            WAIT()

def secondary_engine():
    global timer_1, timer_2
    while True:
        if time.time() - timer_1 >= (1 / gui.app.sampling_frequency) and gui.com.stm_connected:
            timer_1 = time.time()
            gui.GRAPHICS_draw(time.time() - timer_2)
        else:
            WAIT()

if __name__ == "__main__":
    thread1 = threading.Thread(target=primary_engine, daemon=True)
    thread1.start()
    thread2 = threading.Thread(target=secondary_engine, daemon=True)
    thread2.start()
    gui.start()


