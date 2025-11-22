import dearpygui.dearpygui as dpg
import time
import string

from app import AppConfig, Plot, com, eeprom, sdcard, flight
from com import telemetry

app = AppConfig().load()

power   = Plot(samples=100, x_axis=[0.0], y_axis=[0.0])
voltage = Plot(samples=100, x_axis=[0.0], y_axis=[0.0])
current = Plot(samples=100, x_axis=[0.0], y_axis=[0.0])

def GRAPHICS_resolution_auto():
    if app.resolution_auto:
       app.resolution_width = dpg.get_viewport_width()
       app.resolution_height = dpg.get_viewport_height()
       dpg.configure_item('resolution_list', default_value=str(app.resolution_width) + 'x' + str(app.resolution_height))

def COM_update_list():
    dpg.configure_item('COM_available_ports', items=com.search_ports())

def GUI_UPDATE():
    dpg.configure_item('COM_status_button', label="Conectado com sucesso" if com.stm_connected else "Não conectado")
    dpg.configure_item('COM_status_bar', default_value=1 if com.stm_connected else 0)
    dpg.configure_item('COM_status_text_upper', text='Online' if com.stm_connected else 'Offline')
    dpg.configure_item('COM_status_text_upper2', text='Online' if com.stm_connected else 'Offline')
    dpg.configure_item('COM_status_bar_upper',
                       color=(0, 180, 0, 255) if com.stm_connected else (45, 45, 50, 255),
                       fill=(0, 180, 0, 255) if com.stm_connected else (45, 45, 50, 255))
    dpg.configure_item('COM_status_bar_upper2',
                       color=(0, 180, 0, 255) if com.stm_connected else (45, 45, 50, 255),
                       fill=(0, 180, 0, 255) if com.stm_connected else (45, 45, 50, 255))
    dpg.configure_item('flight_reg_list', items=sdcard.files)
    dpg.configure_item('sd_connect_bt', label='Conectado' if sdcard.sd_connected else 'Conectar ao SD')
    dpg.bind_item_theme("sd_connect_bt", theme_sd_connected if sdcard.sd_connected else theme_sd_disconnected)

def EEPROM_config_update():
    dpg.configure_item('sensors_average', default_value=bool(eeprom.average))
    dpg.configure_item('max_power', default_value=eeprom.max_power)
    dpg.configure_item('voltage_offset', default_value=eeprom.vlt_offset)
    dpg.configure_item('current_offset', default_value=eeprom.cur_offset)
    dpg.configure_item('pid_p', default_value=eeprom.pid_p)
    dpg.configure_item('pid_i', default_value=eeprom.pid_i)
    dpg.configure_item('pid_d', default_value=eeprom.pid_d)

def TELEMETRY_UPDATE():
    dpg.configure_item('volt_meter', label=telemetry.voltage)
    dpg.configure_item('amp_meter', label=telemetry.current)
    dpg.configure_item('power_meter', label=telemetry.power)
    dpg.configure_item('receiver_throttle', pmin=(
        0, (app.resolution_height/ 2.9 - (app.resolution_height / 2.9) * int(telemetry.receiver_throttle) / 100)))
    dpg.configure_item('effective_throttle', pmin=(
        0, (app.resolution_height / 2.9 - (app.resolution_height / 2.9) * int(telemetry.effective_throttle) / 100)))

def GRAPHICS_draw(time):
    #power
    power.x_axis.append(time)
    power.y_axis.append(int(telemetry.power))
    dpg.set_value('power_graph', [list(power.x_axis[-power.samples:]),
                                  list(power.y_axis[-power.samples:])])
    dpg.fit_axis_data('power_x_axis')
    dpg.fit_axis_data('power_y_axis')
    #voltage
    voltage.x_axis.append(time)
    voltage.y_axis.append(int(telemetry.voltage))
    dpg.set_value('voltage_graph', [list(voltage.x_axis[-voltage.samples:]),
                                  list(voltage.y_axis[-voltage.samples:])])
    dpg.fit_axis_data('voltage_x_axis')
    dpg.fit_axis_data('voltage_y_axis')
    #current
    current.x_axis.append(time)
    current.y_axis.append(int(telemetry.current))
    dpg.set_value('current_graph', [list(current.x_axis[-current.samples:]),
                                  list(current.y_axis[-current.samples:])])
    dpg.fit_axis_data('current_x_axis')
    dpg.fit_axis_data('current_y_axis')

def GRAPHICS_sd_draw():
    x_values = flight.x_axis[-flight.samples:]
    y_values = flight.y_axis[-flight.samples:]

    dpg.set_value('flight_graph', [x_values, y_values])

    dpg.fit_axis_data('flight_x_axis')
    dpg.fit_axis_data('flight_y_axis')

    dpg.configure_item('limit_power_max', default_value=f'Potência Máxima (W): {max(y_values)}')
    dpg.configure_item('limit_power_med', default_value=f'Potência Média (W): {round(sum(y_values) / len(y_values), 2)}')
    dpg.configure_item('limit_cur_max', default_value=f'Corrente Máxima (A): {max(flight.current)}')
    dpg.configure_item('limit_cur_med', default_value=f'Corrente Média (A): {round(sum(flight.current) / len(flight.current), 2)}')
    dpg.configure_item('limit_vlt_max', default_value=f'Tensão Máxima (V): {max(flight.voltage)}')
    dpg.configure_item('limit_vlt_min', default_value=f'Tensão Mínima (V): {min(flight.voltage)}')
    dpg.configure_item('limit_acc_rcv', default_value=f'Acc Receptor (%): {max(flight.throttle_receiver)}')
    dpg.configure_item('limit_acc_eft', default_value=f'Acc Efetiva (%): {max(flight.throttle_effective)}')

global theme_sd_connected, theme_sd_disconnected

def build():
    global theme_sd_connected, theme_sd_disconnected

    with dpg.font_registry():
        font = dpg.add_font("Roboto-Regular.ttf", app.font_size, tag="roboto-font")

    with dpg.theme() as COM_status_theme:
        with dpg.theme_component(dpg.mvProgressBar):
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, (0, 180, 0, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (50, 50, 50, 255))

    with dpg.theme() as theme_sd_disconnected:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 45, 50), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255), category=dpg.mvThemeCat_Core)

    with dpg.theme() as theme_sd_connected:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 180, 0), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255), category=dpg.mvThemeCat_Core)

    with dpg.window(label="main-window") as main_window:
        dpg.set_primary_window(main_window, app.fillscreen)
        dpg.bind_item_font(dpg.last_item(), "roboto-font")

        with dpg.tab_bar(label='tab_bar'):
            with dpg.tab(label='CONFIGURAÇÕES'):
                dpg.add_text('CONFIGURAÇÕES GRÁFICAS')

                dpg.add_slider_int(
                    label='Tamanho da fonte',
                    tag='font_size',
                    max_value=28,
                    min_value=15,
                    default_value=app.font_size,
                    width=app.resolution_width / 6,
                    height=app.resolution_height / 6,
                    callback=lambda sender, data: app.edit_app('font_size', data)
                )

                dpg.add_combo(
                    app.resolution_list,
                    label="Resolução",
                    tag='resolution_list',
                    default_value=f"{app.resolution_width}x{app.resolution_height}",
                    width=app.resolution_width / 6,
                    callback=lambda sender, data: app.edit_app('resolution_list', data)
                )

                dpg.add_checkbox(
                    label="Resolução automática",
                    tag='resolution_auto',
                    default_value=app.resolution_auto,
                    callback=lambda sender, data: app.edit_app('resolution_auto', data)
                )

                dpg.add_combo(
                    app.draw_sampling_list,
                    label="Amostragem gráfica (samples/s)",
                    tag='sampling_frequency',
                    default_value=app.sampling_frequency,
                    width=app.resolution_width / 6,
                    callback=lambda sender, data: app.edit_app('sampling_frequency', int(data))
                )

                dpg.add_button(
                    label='Salvar',
                    tag="save_config",
                    width=app.resolution_width / 10,
                    height=app.resolution_height / 20,
                    callback=lambda: app.edit_app('save_config')
                )

                dpg.add_text('NOTA: Configurações de resolução e tamanho da fonte necessitam reinicialização do software.')
                dpg.add_spacer(height=5)

                dpg.add_text('COMUNICAÇÃO COM A PLACA')

                dpg.add_listbox(
                    label='Portas COM Disponíveis',
                    tag='COM_available_ports',
                    width=app.resolution_width / 3,
                    items=com.available_ports,
                    callback=lambda sender, data: app.edit_app('COM_available_ports', data)
                )

                dpg.add_progress_bar(
                    label="Progress Bar",
                    tag='COM_status_bar',
                    default_value=0,
                    width=app.resolution_width / 3,
                    height=app.resolution_height / 17
                )
                dpg.bind_item_theme("COM_status_bar", COM_status_theme)

                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Não conectado",
                        tag='COM_status_button',
                        width=app.resolution_width / 4,
                        height=app.resolution_height / 17
                    )

                    dpg.add_button(
                        label="Buscar",
                        tag='COM_search_button',
                        width=app.resolution_width / 13,
                        height=app.resolution_height / 17,
                        callback=lambda: app.edit_app('COM_search_button', gui_callback=COM_update_list)
                    )

            with dpg.tab(label='TELEMETRIA'):
                with dpg.drawlist(width=app.resolution_width, height=20):
                    dpg.draw_rectangle(
                        pmin=(0, 0),
                        pmax=(app.resolution_width, app.resolution_height),
                        tag='COM_status_bar_upper',
                        color=(45, 45, 50, 255),
                        fill=(45, 45, 50, 255)
                    )
                    dpg.draw_text(
                        pos=(app.resolution_width / 2, 0),
                        text='Offline',
                        color=(255, 255, 255, 255),
                        size=app.font_size,
                        tag='COM_status_text_upper'
                    )
                    dpg.bind_item_theme("COM_status_bar_upper", COM_status_theme)

                with dpg.group(horizontal=True):
                    with dpg.plot(width=app.resolution_width / 3, height=app.resolution_height / 4):
                        current_x_axis = dpg.add_plot_axis(dpg.mvXAxis, tag='current_x_axis')
                        current_y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Corrente (A)', tag='current_y_axis')
                        dpg.add_line_series(
                            x=list(current.x_axis),
                            y=list(current.y_axis),
                            label='corrente',
                            parent='current_y_axis',
                            tag='current_graph'
                        )
                        dpg.set_axis_limits("current_y_axis", 0, 60)

                    with dpg.plot(width=app.resolution_width / 3, height=app.resolution_height / 4):
                        voltage_x_axis = dpg.add_plot_axis(dpg.mvXAxis, tag='voltage_x_axis')
                        voltage_y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Tensão (V)', tag='voltage_y_axis')
                        dpg.add_line_series(
                            x=list(voltage.x_axis),
                            y=list(voltage.y_axis),
                            label='Tensão',
                            parent='voltage_y_axis',
                            tag='voltage_graph'
                        )
                        dpg.set_axis_limits("voltage_y_axis", 0, 30)

                    with dpg.group(horizontal=True):
                        with dpg.group():
                            dpg.add_button(
                                label='0.0',
                                tag="volt_meter",
                                width=app.resolution_width / 10,
                                height=app.resolution_height / 15,
                                callback=AppConfig.edit_app
                            )
                            dpg.add_text("\tTensão (V)")

                        with dpg.group():
                            dpg.add_button(
                                label='0.0',
                                tag="amp_meter",
                                width=app.resolution_width / 10,
                                height=app.resolution_height / 15,
                                callback=AppConfig.edit_app
                            )
                            dpg.add_text("\tCorrente (A)")

                        with dpg.group():
                            dpg.add_button(
                                label='0.0',
                                tag="power_meter",
                                width=app.resolution_width / 10,
                                height=app.resolution_height / 15,
                                callback=AppConfig.edit_app
                            )
                            dpg.add_text("\tPotência (W)")

                with dpg.group(horizontal=True):
                    with dpg.plot(label='Gráfico de potência', width=app.resolution_width / 1.49,
                                  height=app.resolution_height / 2.5):
                        power_x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='Tempo (s)', tag='power_x_axis')
                        power_y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Potência (W)', tag='power_y_axis')
                        dpg.add_line_series(
                            x=list(power.x_axis),
                            y=list(power.y_axis),
                            label='potência',
                            parent='power_y_axis',
                            tag='power_graph'
                        )
                        dpg.set_axis_limits("power_y_axis", 0, 1000)

                    dpg.add_spacer(width=20)

                    with dpg.drawlist(width=app.resolution_width / 10, height=app.resolution_height / 2.5):
                        dpg.draw_rectangle(
                            pmin=(0, 0),
                            pmax=(app.resolution_width / 13, app.resolution_height / 2.9),
                            color=(50, 50, 50, 255)
                        )
                        dpg.draw_rectangle(
                            pmin=(0, app.resolution_height / 2.9),
                            pmax=(app.resolution_width / 13, app.resolution_height / 2.9),
                            color=(10, 125, 195, 255),
                            fill=(10, 125, 195, 255),
                            tag="receiver_throttle"
                        )
                        dpg.draw_text(
                            text='Acc recebida(%)',
                            pos=(0, app.resolution_height / 2.8),
                            size=app.font_size
                        )

                    dpg.add_spacer(width=30)

                    with dpg.drawlist(width=app.resolution_width / 10, height=app.resolution_height / 2.5):
                        dpg.draw_rectangle(
                            pmin=(0, 0),
                            pmax=(app.resolution_width / 13, app.resolution_height / 2.9),
                            color=(50, 50, 50, 255)
                        )
                        dpg.draw_rectangle(
                            pmin=(0, app.resolution_height / 2.9),
                            pmax=(app.resolution_width / 13, app.resolution_height / 2.9),
                            color=(10, 125, 195, 255),
                            fill=(10, 125, 195, 255),
                            tag="effective_throttle"
                        )
                        dpg.draw_text(
                            text='Acc efetiva(%)',
                            pos=(0, app.resolution_height / 2.8),
                            size=app.font_size
                        )

                dpg.add_spacer()

                with dpg.child_window(width=app.resolution_width, height=app.resolution_height / 5):
                    with dpg.group(horizontal=True):
                        with dpg.group():
                            dpg.add_checkbox(
                                label="Tirar média dos sensores",
                                tag='sensors_average',
                                callback=lambda sender, data: app.edit_app('sensors_average', data),
                                default_value=False
                            )
                            dpg.add_spacer(width=10)

                        with dpg.group():
                            dpg.add_input_int(
                                label='Potência máxima (W)',
                                default_value=100,
                                step=1,
                                width=app.resolution_width / 5,
                                callback=lambda sender, data: (
                                    dpg.set_value(sender, min(max(data, 1), 1000)),
                                    app.edit_app('max_power', min(max(data, 1), 1000))
                                ),
                                tag='max_power'
                            )
                            dpg.add_input_float(
                                label='Offset tensão',
                                default_value=1.000,
                                step=0.001,
                                width=app.resolution_width / 5,
                                callback=lambda sender, data: (
                                    dpg.set_value(sender, min(max(data, 0.001), 10)),
                                    app.edit_app('voltage_offset', min(max(data, 0.001), 10))
                                ),
                                tag='voltage_offset'
                            )
                            dpg.add_input_float(
                                label='Offset corrente',
                                default_value=1.000,
                                step=0.001,
                                width=app.resolution_width / 5,
                                callback=lambda sender, data: (
                                    dpg.set_value(sender, min(max(data, 0.001), 10)),
                                    app.edit_app('current_offset', min(max(data, 0.001), 10))
                                ),
                                tag='current_offset'
                            )
                            dpg.add_text('Configuração dos Sensores')
                            dpg.add_spacer(width=10)

                        with dpg.group():
                            dpg.add_input_float(
                                label='P',
                                default_value=1.000,
                                step=0.001,
                                width=app.resolution_width / 5,
                                callback=lambda sender, data: (
                                    dpg.set_value(sender, min(max(data, 0.001), 100)),
                                    app.edit_app('pid_p', min(max(data, 0.001), 100))
                                ),
                                tag='pid_p'
                            )
                            dpg.add_input_float(
                                label='I',
                                default_value=1.000,
                                step=0.001,
                                width=app.resolution_width / 5,
                                callback=lambda sender, data: (
                                    dpg.set_value(sender, min(max(data, 0.001), 100)),
                                    app.edit_app('pid_i', min(max(data, 0.001), 100))
                                ),
                                tag='pid_i'
                            )
                            dpg.add_input_float(
                                label='D',
                                default_value=1.000,
                                step=0.001,
                                width=app.resolution_width / 5,
                                callback=lambda sender, data: (
                                    dpg.set_value(sender, min(max(data, 0.001), 100)),
                                    app.edit_app('pid_d', min(max(data, 0.001), 100))
                                ),
                                tag='pid_d'
                            )
                            dpg.add_text('Configuração PID')
                            dpg.add_spacer(width=30)

                        with dpg.group():
                            dpg.add_text('Carregar da EEPROM')
                            dpg.add_button(
                                width=app.resolution_width / 9,
                                label='Carregar',
                                height=app.resolution_height / 23,
                                tag='download_eeprom',
                                callback=lambda: app.edit_app('download_eeprom', gui_callback=EEPROM_config_update)
                            )
                            dpg.add_text('Enviar para EEPROM')
                            dpg.add_button(
                                width=app.resolution_width / 9,
                                label='Enviar',
                                height=app.resolution_height / 23,
                                tag='upload_eeprom',
                                callback=lambda: app.edit_app('upload_eeprom')
                            )

            with dpg.tab(label='ANÁLISE'):
                with dpg.drawlist(width=app.resolution_width, height=20):
                    dpg.draw_rectangle(
                        pmin=(0, 0),
                        pmax=(app.resolution_width, app.resolution_height),
                        tag='COM_status_bar_upper2',
                        color=(45, 45, 50, 255),
                        fill=(45, 45, 50, 255)
                    )
                    dpg.draw_text(
                        pos=(app.resolution_width / 2, 0),
                        text='Offline',
                        color=(255, 255, 255, 255),
                        size=app.font_size,
                        tag='COM_status_text_upper2'
                    )
                    dpg.bind_item_theme("COM_status_bar_upper2", COM_status_theme)

                with dpg.group(horizontal=True):
                    with dpg.plot(label='Gráfico de potência', width=app.resolution_width * 0.75,
                                  height=app.resolution_height * 0.75):
                        flight_x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='Tempo (s)', tag='flight_x_axis')
                        flight_y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Potência (W)', tag='flight_y_axis')
                        dpg.add_line_series(
                            x=list(flight.x_axis),
                            y=list(flight.y_axis),
                            label='potência',
                            parent='flight_y_axis',
                            tag='flight_graph'
                        )
                        dpg.set_axis_limits("flight_y_axis", 0, 150)


                    with dpg.child_window(width=app.resolution_width * 0.5, height=app.resolution_height * 0.5):
                        dpg.add_text('REGISTRO DE VÔOS:')
                        dpg.add_combo(items=sdcard.files, label="Vôo nº", tag='flight_reg_list',
                                      width=app.resolution_width / 6, callback=lambda sender, data: app.edit_app('sd_file_load', data, gui_callback=GRAPHICS_sd_draw))

                        dpg.add_spacer(height=30)
                        dpg.add_text('========= LIMITES ATINGIDOS =========')

                        dpg.add_text('Potência Máxima (W): ', tag='limit_power_max')
                        dpg.add_text('Potência Média (W): ', tag='limit_power_med')
                        dpg.add_text('Corrente Máxima (A): ', tag='limit_cur_max')
                        dpg.add_text('Corrente Média (A): ', tag='limit_cur_med')
                        dpg.add_text('Tensão Máxima (V): ', tag='limit_vlt_max')
                        dpg.add_text('Tensão Mínima (V): ', tag='limit_vlt_min')
                        dpg.add_text('Acc Receptor (%): ', tag='limit_acc_rcv')
                        dpg.add_text('Acc Efetiva (%): ', tag='limit_acc_eft')

                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_button(width=app.resolution_width * 0.23, label='limpar SD',
                                       height=app.resolution_height * 0.1, tag='sd_clear_bt',
                                       callback=lambda: app.edit_app('sd_clear_bt'))

                    with dpg.group():
                        dpg.add_button(width=app.resolution_width * 0.23, label='Conectar ao SD',
                                       height=app.resolution_height * 0.1, tag='sd_connect_bt',
                                       callback=lambda: app.edit_app('sd_connect_bt'))
                        dpg.bind_item_theme("sd_connect_bt", theme_sd_disconnected)

            with dpg.tab(label='INFO'):
                dpg.add_text("Adaptative Power Controller (APC) data analysis software"
                             "\n\nSoftware Version 1.0 - BETA RELEASE\n\n")

def start():
    dpg.create_context()
    build()

    dpg.create_viewport(
        title='CEFAST - FlightPower',
        width=app.resolution_width,
        height=app.resolution_height,
        small_icon='cefast-icon.ico'
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


