import dearpygui.dearpygui as dpg
from spiritbox import SpiritBox
import threading

sb = SpiritBox()

def start_spiritbox():
    start_freq = 88e6
    end_freq = 108e6
    step_freq = 0.2e6
    hold_time_sec = 0.1
    t = threading.Thread(target=sb.run, args=(start_freq, end_freq, step_freq, hold_time_sec))
    t.start()

def stop_spiritbox():
    sb.stop()

dpg.create_context()

dpg.create_viewport()
dpg.setup_dearpygui()

with dpg.window(label="Spirit Box", width=500, height=500, tag="main_window", on_close=stop_spiritbox):
    dpg.add_button(label="Start", callback=start_spiritbox)
    dpg.add_button(label="Stop", callback=stop_spiritbox)

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()