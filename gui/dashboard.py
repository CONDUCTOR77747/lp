# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 16:00:05 2025

@author: Ammosov
"""

import numpy as np
import yaml
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.widgets import MultiCursor
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg
                                                as FigureCanvas)
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT
                                                as NavigationToolbar)
from PyQt5.QtWidgets import (QWidget, QAction, QDialog, QSpinBox, QComboBox,
                             QMainWindow,QSizePolicy,QPushButton, QFormLayout,
                             QVBoxLayout, QRadioButton, QButtonGroup,
                             QHBoxLayout, QDoubleSpinBox, QMenu, QFileDialog)

from .configurator import Configurator
from .defaults import ICON_PATH, INFO, TIPS
from .utils import (pop_up_window, verify_cfg, save_as_txt)
from lpy import PROBE_AREA_DEFAULT, TeNeAnalyzer, remove_negatives

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(INFO['main_window_title'])
        self.setMinimumSize(683, 384)
        self.setWindowIcon(QIcon(ICON_PATH))

        # emaple of shot 3008
        self.example = {
            'tdms_path': 'tests/test_data/T15MD_3008.tdms',
            'signals': {'LP.Power': {'channel': 'LP.15', 'factor': -34},
                        'LP.09': {'channel': 'LP.09', 'factor': '1000 / 50'},
                        'LP.13': {'channel': 'LP.03', 'factor': '1000 / 100'}
                        }
            }

        # Initialize default config
        self.parameters_ini = {
            'probe': '',
            'u_range': (0,0),
            'n_avg': 1,
            'te_threshold': 50,
            'sweep_direction': 'up',
            'probe_area': PROBE_AREA_DEFAULT,
            'smooth_u': (1,1),
            'smooth_i': (1,1),
            'dt_range_ne': (2,2),
            'dt_range_te': (0,0),
        }

        # Create menu bar
        self.create_menu()
        # Главный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        # Верхняя панель параметров
        self.create_control_panel(main_layout)
        # График Matplotlib с toolbar
        self.create_matplotlib_widget(main_layout)

        self.ctrl_is_held = False

        # axes for preserving limits
        self.axes = None
        self.xy_lims = None

    def create_menu(self):
        """Create menu bar with File menu"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('Файл')
        # Open configurator action
        manager_action = QAction('Открыть конфигуратор', self)
        manager_action.triggered.connect(self.open_configurator)
        file_menu.addAction(manager_action)

        # Save data
        # Create the Save As submenu
        saveAsMenu = QMenu('Сохранить', self)
        # Add options to the Save Te and ne As submenu
        saveTeneAsTxtAction = QAction('Te и ne для всех зондов как .txt', self)
        saveTeneAsTxtAction.triggered.connect(self.save_te_ne_as_txt)

        # Add options to the Save Te and ne As submenu
        saveFPAsTxtAction = QAction('Плавающий потенциал для .FP зондов как .txt', self)
        saveFPAsTxtAction.triggered.connect(self.save_fp_as_txt)

        # add options to file menu
        saveAsMenu.addAction(saveTeneAsTxtAction)
        saveAsMenu.addAction(saveFPAsTxtAction)
        file_menu.addMenu(saveAsMenu)

        # Help menu (manual)
        help_menu = menubar.addMenu('Помощь')
        # instruction action
        instruction_action = QAction('Инструкция', self)
        instruction_action.triggered.connect(self.open_instruction_pop_up)
        help_menu.addAction(instruction_action)
        # 3008 example action
        example_action = QAction('Пример импульс #3008', self)
        example_action.triggered.connect(self.load_example)
        help_menu.addAction(example_action)
        # about action
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.open_about_pop_up)
        help_menu.addAction(about_action)

    def open_configurator(self):
        """ Open config manager dialog and collect data """
        manager = Configurator(self)

        # open previously loaded cfg data
        if hasattr(self, 'cfg'):
            manager.tdms_path_entry.setText(self.cfg['tdms_path'])
            text = yaml.dump(self.cfg['signals'], default_flow_style=False)
            manager.signals_text.setText(text)

        # when configurator sends signal accepted
        if manager.exec_() == QDialog.Accepted:
            # get information from configurator
            self.cfg = manager.get_cfg() # full cfg
            self.signals = manager.signals # loaded signals dict

            # clear previous probes from qcombobox list
            self.probe.clear()
            # add new probes to qcombobox list
            probe_names = []
            for key, val in self.signals.items():
                if key != 'time' and key != 'LP.Power' and key != 'shot':
                    probe_names.append(key)
            self.probe.addItems(probe_names)
            self.probe.setCurrentIndex(0)
            self.probe.setCurrentText(probe_names[0])

            self.update_plot()

    def load_example(self):
        """ Opens configurator with preloaded config for shot 3008 """
        manager = Configurator(self)

        # set example for shot #3008
        manager.tdms_path_entry.setText(self.example['tdms_path'])
        text = yaml.dump(self.example['signals'], default_flow_style=False)
        manager.signals_text.setText(text)

        # when configurator sends signal accepted
        if manager.exec_() == QDialog.Accepted:
            # get information from configurator
            self.cfg = manager.get_cfg() # full cfg
            self.signals = manager.signals # loaded signals dict

            # clear previous probes from qcombobox list
            self.probe.clear()
            # add new probes to qcombobox list
            probe_names = []
            for key, val in self.signals.items():
                if key != 'time' and key != 'LP.Power' and key != 'shot':
                    probe_names.append(key)
            self.probe.addItems(probe_names)
            self.probe.setCurrentIndex(0)
            self.probe.setCurrentText(probe_names[0])

            self.update_plot()


    def open_instruction_pop_up(self):
        """ Open instruction main window """
        info = INFO['main_window_instruction']
        window_title = info['window_title']
        text = info['text']
        pop_up_window(window_title, text, selectable_text=True)

    def open_about_pop_up(self):
        """ Open about window """
        info = INFO['main_window_about']
        window_title = info['window_title']
        text = info['text']
        pop_up_window(window_title, text, selectable_text=False)

    def create_control_panel(self, parent_layout):
        """Создаем панель управления параметрами"""
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        # Группируем параметры в формы (слева направо 1...n)
        form_1 = QFormLayout()
        form_2 = QFormLayout()
        form_3 = QFormLayout()
        form_4 = QFormLayout()
        form_5 = QFormLayout()
        form_6 = QFormLayout()

        # 1. refresh button
        refresh_button_layout = QHBoxLayout()
        refresh_button = QPushButton()
        refresh_button.setText("Обновить")
        refresh_button_layout.addWidget(refresh_button)
        form_1.addRow(refresh_button_layout)
        # Подключение кнопки обновить для обновления графика
        refresh_button.pressed.connect(self.update_plot)

        # 1.2 zoom out button
        zoom_out_button_layout = QHBoxLayout()
        zoom_out_button = QPushButton()
        zoom_out_button.setText("Отдалить")
        zoom_out_button_layout.addWidget(zoom_out_button)
        form_1.addRow(zoom_out_button_layout)
        # Подключение кнопки отдалить для обновления графика
        zoom_out_button.pressed.connect(self.zoom_out_plot)

        # 2. probe (выпадающий список) ВЗ - выбор зонда
        self.probe = QComboBox()
        self.probe.addItem(self.parameters_ini['probe'])
        form_2.addRow("Выбор зонда:", self.probe)

        # 3. u_range (два double spinbox) #!!! add tooltips
        u_range_layout = QHBoxLayout()
        self.u_min = QDoubleSpinBox()
        self.u_min.setRange(-500, 500)
        self.u_min.setValue(self.parameters_ini['u_range'][0])
        self.u_max = QDoubleSpinBox()
        self.u_max.setRange(-500, 500)
        self.u_max.setValue(self.parameters_ini['u_range'][1])
        u_range_layout.addWidget(self.u_min)
        u_range_layout.addWidget(self.u_max)
        form_2.addRow("Диапазон u [В]:", u_range_layout)

        # 4. n_avg (1-50)
        self.n_avg = QSpinBox()
        self.n_avg.setRange(1, 50)
        self.n_avg.setValue(self.parameters_ini['n_avg'])
        form_3.addRow("Число сканов:", self.n_avg)
        self.n_avg.setToolTip(
            "Число соседних сканов для обработки (скользящее окно)")

        # 5. te threshold (float)
        te_threshold_layout = QHBoxLayout()
        self.te_threshold = QDoubleSpinBox()
        self.te_threshold.setRange(0, 100000)
        self.te_threshold.setValue(self.parameters_ini['te_threshold'])
        self.te_threshold.setSingleStep(5)
        te_threshold_layout.addWidget(self.te_threshold)
        form_3.addRow("Ограничить Te [эВ]:", te_threshold_layout)

        # 6. sweep_direction (радиокнопки)
        self.sweep_group = QButtonGroup(self)

        self.sweep_up = QRadioButton("up")
        self.sweep_up.setChecked(
            self.parameters_ini['sweep_direction'] == 'up')

        self.sweep_down = QRadioButton("down")
        self.sweep_down.setChecked(
            self.parameters_ini['sweep_direction'] == 'down')

        self.sweep_group.addButton(self.sweep_up)
        self.sweep_group.addButton(self.sweep_down)

        # sweep_direction tooltip #!!! add to TIPS
        self.sweep_up.setToolTip("Определение Te по подъему тока зонда")
        self.sweep_down.setToolTip("Определение Te по падению тока зонда")

        # layout
        sweep_layout = QHBoxLayout()
        sweep_layout.addWidget(self.sweep_up)
        sweep_layout.addWidget(self.sweep_down)
        form_4.addRow("Определение Te:", sweep_layout)

        # 7. probe_area (float)
        probe_area_layout = QHBoxLayout()
        self.probe_area = QDoubleSpinBox()
        self.probe_area.setRange(0, 100)
        self.probe_area.setDecimals(3)
        self.probe_area.setValue(self.parameters_ini['probe_area'])
        probe_area_layout.addWidget(self.probe_area)
        form_4.addRow("Площадь зонда [мм^2]:", probe_area_layout)

        # 8. smooth U #!!! refactor, add to TIPS
        smooth_u_layout = QHBoxLayout()

        self.smooth_u_avg = QSpinBox()
        self.smooth_u_avg.setRange(1, 100)
        self.smooth_u_avg.setValue(self.parameters_ini['smooth_u'][0])

        self.smooth_u_n = QSpinBox()
        self.smooth_u_n.setRange(1, 100)
        self.smooth_u_n.setValue(self.parameters_ini['smooth_u'][1])

        smooth_u_layout.addWidget(self.smooth_u_avg)
        smooth_u_layout.addWidget(self.smooth_u_n)
        form_5.addRow("Сглаживание U:", smooth_u_layout)

        # 9. smooth I #!!! refactor, add to TIPS
        smooth_i_layout = QHBoxLayout()

        self.smooth_i_avg = QSpinBox()
        self.smooth_i_avg.setRange(1, 100)
        self.smooth_i_avg.setValue(self.parameters_ini['smooth_i'][0])

        self.smooth_i_n = QSpinBox()
        self.smooth_i_n.setRange(1, 100)
        self.smooth_i_n.setValue(self.parameters_ini['smooth_i'][1])

        smooth_i_layout.addWidget(self.smooth_i_avg)
        smooth_i_layout.addWidget(self.smooth_i_n)
        form_5.addRow("Сглаживание I:", smooth_i_layout)

        # 10. dt_range_ne (два float)
        dt_range_ne_layout = QHBoxLayout()
        self.dt_ne_min = QDoubleSpinBox()
        self.dt_ne_min.setRange(-20, 20)
        self.dt_ne_min.setSingleStep(0.1)
        self.dt_ne_min.setValue(self.parameters_ini['dt_range_ne'][0])
        self.dt_ne_max = QDoubleSpinBox()
        self.dt_ne_max.setRange(-20, 20)
        self.dt_ne_max.setSingleStep(0.1)
        self.dt_ne_max.setValue(self.parameters_ini['dt_range_ne'][1])
        dt_range_ne_layout.addWidget(self.dt_ne_min)
        dt_range_ne_layout.addWidget(self.dt_ne_max)
        form_6.addRow("Диапазон dt_ne:", dt_range_ne_layout)

        # 11. dt_range (два double spinbox)
        dt_range_te_layout = QHBoxLayout()
        self.dt_te_min = QDoubleSpinBox()
        self.dt_te_min.setRange(-15, 15)
        self.dt_te_min.setSingleStep(0.01)
        self.dt_te_min.setValue(self.parameters_ini['dt_range_te'][0])
        self.dt_te_max = QDoubleSpinBox()
        self.dt_te_max.setRange(-15, 15)
        self.dt_te_max.setSingleStep(0.01)
        self.dt_te_max.setValue(self.parameters_ini['dt_range_te'][1])
        dt_range_te_layout.addWidget(self.dt_te_min)
        dt_range_te_layout.addWidget(self.dt_te_max)
        form_6.addRow("Диапазон dt_te:", dt_range_te_layout)

        # Добавляем формы в основной layout
        control_layout.addLayout(form_1)
        control_layout.addLayout(form_2)
        control_layout.addLayout(form_3)
        control_layout.addLayout(form_4)
        control_layout.addLayout(form_5)
        control_layout.addLayout(form_6)
        parent_layout.addWidget(control_panel)

    def create_matplotlib_widget(self, parent_layout):
        """Создаем виджет для Matplotlib графика с toolbar"""
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Добавляем стандартный toolbar Matplotlib
        self.toolbar = NavigationToolbar(self.canvas, self)
        # Layout для графика и toolbar
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        # Создание и добавления виджета в предка
        plot_widget = QWidget()
        plot_widget.setLayout(plot_layout)
        parent_layout.addWidget(plot_widget, stretch=1)

    def update_plot(self):
        """ Updates plot but saves axes limits """
        if not hasattr(self, 'signals'):
            self.open_configurator()
        else:

            if self.axes is not None:
                # Save the original limits for the "Home" button
                self.xy_lims = (self.axes[0].get_xlim(),
                                self.axes[0].get_ylim())

            # clear figure for replotting
            self.figure.clear()
            # create 3 rows axes for signals, te and ne
            self.axes = self.figure.subplots(nrows=3, sharex=True)

            # get time, u, shot, probe_name, currents, fp_signals
            (self.t, self.u, self.shot, self.currents,
             self.fp_singals) = self.parse_signals_dict()

            self.probe_name = self.probe.currentText()

            # prepare parameters for calc_te_ne
            self.parameters = {
                'u_range': (self.u_min.value(), self.u_max.value()),
                'n_avg': self.n_avg.value(),
                'te_threshold': self.te_threshold.value(),
                'sweep_direction': self.sweep_group.checkedButton().text(),
                'probe_area': self.probe_area.value(),
                'smooth_u': (self.smooth_u_avg.value(), self.smooth_u_n.value()),
                'smooth_i': (self.smooth_i_avg.value(), self.smooth_i_n.value()),
                'dt_range_ne': (self.dt_ne_min.value(), self.dt_ne_max.value()),
                'dt_range_te': (self.dt_te_min.value(), self.dt_te_max.value()),
                }

            # Plotting
            if self.probe_name.endswith('.FP'):
                # plot Floating Potential signal
                self.plot_fp(self.t, self.u, self.fp_singals, self.shot,
                          self.probe_name)
            else:
                # plot data Te ne
                self.plot(self.t, self.u, self.currents, self.shot,
                          self.probe_name, self.parameters)

            # adjust margins
            self.figure.subplots_adjust(
                left=0.05, right=0.995, top=0.9, bottom=0.1)

            # Restore zoom level
            if self.xy_lims is not None:
                self.axes[0].set_xlim(self.xy_lims[0])
                self.axes[0].set_ylim(self.xy_lims[1])

            # update viewport
            self.canvas.draw()

    def plot_fp(self, t, u, fp_signals, shot, probe_name):
        """ Plot Floating Potential signals """
        ax1, ax2, ax3 = self.axes
        # ax1 - signals
        ax1.plot(t, u, label='Voltage, V')
        ax1.plot(t, fp_signals[probe_name], label=f'{self.probe_name}, V')
        ax1.set_ylabel('Voltage, V; Floating Potential, V')
        ax1.set_title(f'#{self.shot}')
        ax1.legend(loc='upper right')
        ax1.grid()

    def plot(self, t, u, currents, shot, probe_name, parameters):
        """ Create interactive plot """
        self.t, self.u, self.i = t, u, currents[probe_name]
        # create TeNeAnalyzer instance
        self.tna = TeNeAnalyzer(self.t, self.u, self.i)

        # calculate Te, Ne using given parameters
        res_t, te, ne, info = self.tna.calc_te_ne(parameters)

        self.info = info

        ax1, ax2, ax3 = self.axes
        # ax1 - signals
        t, u, i = self.tna.t, self.tna.u, self.tna.i
        ax1.plot(t, u, label='Voltage, V')
        ax1.plot(t, i, label=f'{self.probe_name}, mA')
        # ax1.plot(t, tna.spandet.u_smooth, label='Voltage smoothed, V')
        # ax1.plot(t, tna.spandet.di, label='Probe Current Gradient')
        ax1.set_ylabel('Voltage, V; Probe Current, mA')
        ax1.set_title(f'#{self.shot}')
        ax1.legend(loc='upper right')
        ax1.grid()

        for span in self.tna.spans_te:
            ax1.axvspan(t[span[0]], t[span[1]],
                        color='green', alpha=0.2)

        for span in self.tna.spans_ne:
            ax1.axvspan(t[span[0]], t[span[1]],
                        color='red', alpha=0.2)

        # ax2 - Te
        ax2.plot(res_t, te, 'o', color='green')
        ax2.set_ylabel('Te, eV')
        ax2.grid()
        # Te errorbars
        # te_errs = [kerr/k**2 for k, _, kerr, _ in info]
        # ax2.errorbar(te_t, te, yerr=te_errs, fmt='o', ecolor='black',
        # capsize=5, color='green')

        # ax3 - ne
        ax3.plot(res_t, ne, 'o', color='red')
        ax3.set_xlabel('t, ms')
        ax3.set_ylabel('ne, 10^18 m^-3')
        ax3.grid()

        # add red line cursor for axes
        self.multi = MultiCursor(self.figure.canvas, self.axes, color='r', lw=1)
        # connect event to open Current-Voltage Plot
        self.figure.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.figure.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.figure.canvas.mpl_connect('button_press_event',
                                       self.current_voltage_plot_on_ctrl_click)

    def on_key_press(self, event):
        if event.key == 'control':
            self.ctrl_is_held = True

    def on_key_release(self, event):
        if event.key == 'control':
            self.ctrl_is_held = False

    def current_voltage_plot_on_ctrl_click(self, event):
        if not ('ctrl' in event.modifiers):
            return

        idx = self.tna.find_nearest_info(event.xdata)
        try:
            fig_detail, ax_detail = plt.subplots()
            # Set the window title

            u_range = (self.u_min.value(), self.u_max.value())
            # u_wide, i_wide, u, i, k, c, time_mean
            u_wide, i_wide, u, i, k, c, t = self.tna.cv_plot_data[idx]
            # Convert lists to NumPy arrays
            u_wide = np.array(u_wide)
            i_wide = np.array(i_wide)
            u = np.array(u)
            i = np.array(i)
            # remove negative values from arrays to put I in log function
            u_wide, i_wide = remove_negatives(u_wide, i_wide)
            u, i = remove_negatives(u, i)

            ax_detail.plot(u_wide, np.log(i_wide), 'o', alpha=0.2)
            ax_detail.plot(u, np.log(i), 'o', ms=5)
            ax_detail.plot(u, u*k + c)

            ax_detail.set_xlabel('U, В')
            ax_detail.set_ylabel('ln(I), мА')

            p_title = f't = {int(t)} мс   Te = {int(1/k)} эВ  u = {u_range} В'
            ax_detail.set_title(p_title)
            shot = self.signals['shot']
            w_title = f'#{shot} ВАХ {int(t)} мс'
            fig_detail.canvas.manager.set_window_title(w_title)
            ax_detail.grid(True)
            plt.show()
        except Exception as e:
            print(f'Error: {e}')

    def zoom_out_plot(self):
        """
        Updates plot with dashboard buttons
        and redraws it with auto axes limits
        """
        self.axes, self.xy_lims = None, None
        self.update_plot()

    def key_press_event_enter(self, event):
        """ If enter is pressed updates plot with saving axes limits """
        if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
            self.update_plot()

    def parse_signals_dict(self):
        """ Extracts data from signals dict """
        if not hasattr(self, 'signals'):
            self.open_configurator()
        else:
            # Extract specific signals
            t = self.signals.get('time', None)
            u = self.signals.get('LP.Power', None)
            shot = self.signals.get('shot', 0)

            # Define exclude keys
            exclude_keys = ['time', 'LP.Power', 'shot']

            # Extract floating potential signals (keys ending with ".FP")
            fp_signals = {k: v for k, v in self.signals.items() if k.endswith('.FP')}

            # Extract currents (all except exclude keys and keys ending with ".FP")
            currents = {k: v for k, v in self.signals.items()
                        if k not in exclude_keys and not k.endswith('.FP')}

            return t, u, shot, currents, fp_signals

    def save_te_ne_as_txt(self):
        """Saves te and ne data as txt """
        if not hasattr(self, 'signals'):
            self.open_configurator()
        else:
            # get time, u, shot, probe_name, currents, fp_signals (not used)
            t, u, shot, currents, fp_singals = self.parse_signals_dict()

            data_columns = []  # List to collect all columns (res_t, te, ne for each probe)
            headers = []       # List to collect headers
            for probe_name, current in currents.items():

                # create TeNeAnalyzer instance
                tna = TeNeAnalyzer(t, u, current)
                # calculate Te, Ne using given parameters
                res_t, te, ne, info = tna.calc_te_ne(self.parameters)
                # Append data as columns
                data_columns.extend([res_t, te, ne])

                # Append headers for these columns
                headers.extend([
                    f'{probe_name}.time',
                    f'{probe_name}.Te',
                    f'{probe_name}.ne'
                ])

            # Combine all columns into a 2D array (rows = data points, columns = variables)
            data_to_save = np.column_stack(data_columns)
            default_file_name = f"{shot}_LP_Te_ne"
            save_as_txt(data_to_save, headers, default_file_name)

    def save_fp_as_txt(self):
        """Saves te and ne data as txt """
        if not hasattr(self, 'signals'):
            self.open_configurator()
        else:
            # get time, u, shot, probe_name, currents (not used), fp_signals
            t, u, shot, currents, fp_singals = self.parse_signals_dict()

            # data arrays time included already
            data_columns = [t]  # List to collect all columns (res_t, te, ne for each probe)
            headers = ['time']       # List to collect headers
            for signame, signal in fp_singals.items():
                data_columns.append(signal)
                # Append headers for these columns
                headers.append(f'{signame}')

            # Combine all columns into a 2D array (rows = data points, columns = variables)
            data_to_save = np.column_stack(data_columns)
            default_file_name = f"{shot}_LP_FP"
            save_as_txt(data_to_save, headers, default_file_name)
