import dearpygui.dearpygui as dpg
from spiritbox import SpiritBox
import threading
import numpy as np
import color_theme as ct

sb = SpiritBox()

def start_spiritbox():
    start_freq = 88e6
    end_freq = 108e6
    step_freq = 0.2e6
    hold_time_sec = dpg.get_value("hold_time")
    t = threading.Thread(target=sb.run, args=(start_freq, end_freq, step_freq, hold_time_sec))
    t.start()

def stop_spiritbox():
    sb.close()

dpg.create_context()

dpg.create_viewport()
dpg.setup_dearpygui()

with dpg.window(label="Spirit Box", width=500, height=500, tag="main_window", on_close=stop_spiritbox) as main_window:
    # Inputs
    dpg.add_button(label="Start", callback=start_spiritbox)
    dpg.add_button(label="Stop", callback=stop_spiritbox)
    dpg.add_input_float(label="Hold Time", default_value=0.1, tag="hold_time")

    dpg.add_spacer(height=10)

    # Outputs
    dpg.add_text("Current Frequency: ", tag="current_freq")
    dpg.add_text("The spirits say:", label="Speech Buffer", tag="text_buffer")
    with dpg.plot(label="Audio (Time Domain)", tag="audio_plot", width=-1, height=-1):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Sample", tag="x_axis")
        dpg.add_plot_axis(dpg.mvYAxis, label="int16", tag="y_axis")
        dpg.add_line_series(np.arange(len(sb.sample_buffer)), sb.sample_buffer, parent="y_axis", tag="audio_line")

with dpg.theme() as theme:
    # spooky halloween colors
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, ct.VAMPIRE_BLACK, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, ct.PUMPKIN, category=dpg.mvThemeCat_Core)


dpg.bind_item_theme(main_window, theme)

dpg.show_viewport()
while dpg.is_dearpygui_running():
    dpg.set_value("current_freq", f"Current Frequency: {sb.current_freq/1e6:.2f} MHz")
    if tbuf := sb.text_buffer:
        dpg.set_value("text_buffer", f"The spirits say: {tbuf}")
    if sbuf := sb.sample_buffer:
        dpg.set_axis_limits("y_axis", np.iinfo(np.int16).min, np.iinfo(np.int16).max)
        dpg.set_axis_limits("x_axis", 0, len(sbuf))

        dpg.set_value("audio_line", [np.arange(len(sbuf)), sbuf])
    dpg.render_dearpygui_frame()

dpg.destroy_context()