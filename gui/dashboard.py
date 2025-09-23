# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 16:00:05 2025

@author: Ammosov
"""

import yaml
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
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
from .utils import (pop_up_window, verify_cfg, save_as_txt, align_signals)
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
            'u_range': [0,0],
            'lni_range': [0,0],
            'n_avg': 1,
            'te_threshold': 50,
            'sweep_direction': 'up',
            'probe_area': PROBE_AREA_DEFAULT,
            'smooth_u': [1,1],
            'smooth_i': [1,1],
            'dt_range_ne': [2,2],
            'dt_range_te': [0,0],
        }

        self.parameters = {}

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

        # Save data as TXT
        # Create the Save As submenu
        saveAsMenu = QMenu('Сохранить как txt', self)
        # Add options to the Save Te and ne for all probes As submenu
        saveTxtTeNeAction = QAction('Te, ne', self)
        saveTxtTeNeAction.triggered.connect(self.save_txt_te_ne)
        # Add options to the Save Te and ne for current probe As submenu
        saveTxtU_I = QAction('U, I', self)
        saveTxtU_I.triggered.connect(self.save_txt_u_i)
        # Add options to the Save FP submenu
        saveTxtFpAction = QAction('Плавающий потенциал для всех .FP зондов', self)
        saveTxtFpAction.triggered.connect(self.save_txt_fp)

        # add options to file menu
        saveAsMenu.addAction(saveTxtTeNeAction)
        saveAsMenu.addAction(saveTxtU_I)
        saveAsMenu.addAction(saveTxtFpAction)
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

    def update_probes_list(self):
        """ Update QComboBox list of probes on dashboard """
        # clear previous probes from qcombobox list
        self.probe.clear()
        # add new probes to qcombobox list
        probe_names = []
        for key, val in self.signals.items():
            if key != 'time' and key != 'LP.Power' and key != 'shot':
                probe_names.append(key)
        self.probe.addItems(probe_names)
        # self.probe.setCurrentIndex(0)
        # set probe name
        probe_name = self.parameters.get('probe', self.parameters_ini['probe'])
        self.probe.setCurrentText(probe_name)

    def set_parameters(self, parameters):
        """
        Set parameters to dashboard widgets.
        If parameter is missing, default (ini) parameter will be used.
        For list/tuple parameters (e.g. ranges), ensures:
          - Exactly 2 elements
          - Both elements are valid numbers (int or float)
        Otherwise, falls back to ini value.
        """
        par_ini = self.parameters_ini

        def validate_range(value):
            """Helper: validate 2-element numeric range."""
            if not isinstance(value, (list, tuple)):
                return False
            if len(value) != 2:
                return False
            return all(isinstance(x, (int, float)) and x is not None for x in value)

        def validate_number(value):
            """Helper: validate single numeric value."""
            return isinstance(value, (int, float)) and value is not None

        # Mapping: (param_key, fallback, validator, setter(s))
        settings = [
            # probe (simple text)
            ('probe', par_ini['probe'], lambda x: isinstance(x, str),
             lambda val: self.probe.setCurrentText(val)),

            # u_range: [min, max]
            ('u_range', par_ini['u_range'], validate_range,
             lambda val: (self.u_min.setValue(val[0]), self.u_max.setValue(val[1]))),

            # lni_range
            ('lni_range', par_ini['lni_range'], validate_range,
             lambda val: (self.lni_min.setValue(val[0]), self.lni_max.setValue(val[1]))),

            # n_avg: single number
            ('n_avg', par_ini['n_avg'], validate_number,
             lambda val: self.n_avg.setValue(val)),

            # te_threshold
            ('te_threshold', par_ini['te_threshold'], validate_number,
             lambda val: self.te_threshold.setValue(val)),

            # sweep_direction
            ('sweep_direction', par_ini['sweep_direction'],
             lambda x: x in ('up', 'down'),
             lambda val: (self.sweep_up.setChecked(val == 'up'),
                          self.sweep_down.setChecked(val == 'down'))),

            # probe_area
            ('probe_area', par_ini['probe_area'], validate_number,
             lambda val: self.probe_area.setValue(val)),

            # smooth_u
            ('smooth_u', par_ini['smooth_u'], validate_range,
             lambda val: (self.smooth_u_avg.setValue(val[0]), self.smooth_u_n.setValue(val[1]))),

            # smooth_i
            ('smooth_i', par_ini['smooth_i'], validate_range,
             lambda val: (self.smooth_i_avg.setValue(val[0]), self.smooth_i_n.setValue(val[1]))),

            # dt_range_ne
            ('dt_range_ne', par_ini['dt_range_ne'], validate_range,
             lambda val: (self.dt_ne_min.setValue(val[0]), self.dt_ne_max.setValue(val[1]))),

            # dt_range_te
            ('dt_range_te', par_ini['dt_range_te'], validate_range,
             lambda val: (self.dt_te_min.setValue(val[0]), self.dt_te_max.setValue(val[1]))),
        ]

        for key, default, validator, setter in settings:
            value = parameters.get(key, default)
            if not validator(value):
                print(f"Warning: Invalid value for '{key}', using default: {default}")
                value = default
            setter(value)

    # def set_parameters(self, parameters):
    #     """
    #     Set parameters to dashboard widgets.
    #     If parameter is missing, default (ini) parameter will be setted.
    #     """
    #     par_ini = self.parameters_ini
    #     # set probe name
    #     probe_name = parameters.get('probe', par_ini['probe'])
    #     self.probe.setCurrentText(probe_name)

    #     # set u_range
    #     u_range = parameters.get('u_range', par_ini['u_range'])
    #     self.u_min.setValue(u_range[0])
    #     self.u_max.setValue(u_range[1])

    #     # set lni_range
    #     lni_range = parameters.get('lni_range', par_ini['lni_range'])
    #     self.lni_min.setValue(lni_range[0])
    #     self.lni_max.setValue(lni_range[1])

    #     # set n_avg
    #     n_avg = parameters.get('n_avg', par_ini['n_avg'])
    #     self.n_avg.setValue(n_avg)

    #     # set te_threshold
    #     te_threshold = parameters.get('te_threshold', par_ini['te_threshold'])
    #     self.te_threshold.setValue(te_threshold)

    #     # set sweep_direction
    #     sweep_direction = parameters.get('sweep_direction',
    #                                      par_ini['sweep_direction'])
    #     self.sweep_up.setChecked(sweep_direction == 'up')
    #     self.sweep_down.setChecked(sweep_direction == 'down')

    #     # set probe_area
    #     probe_area = parameters.get('probe_area', par_ini['probe_area'])
    #     self.probe_area.setValue(probe_area)

    #     # set smooth_u
    #     smooth_u = parameters.get('smooth_u', par_ini['smooth_u'])
    #     self.smooth_u_avg.setValue(smooth_u[0])
    #     self.smooth_u_n.setValue(smooth_u[1])

    #     # set smooth_i
    #     smooth_i = parameters.get('smooth_i', par_ini['smooth_i'])
    #     self.smooth_i_avg.setValue(smooth_i[0])
    #     self.smooth_i_n.setValue(smooth_i[1])

    #     # set dt_range_ne
    #     dt_ne = parameters.get('dt_range_ne', par_ini['dt_range_ne'])
    #     self.dt_ne_min.setValue(dt_ne[0])
    #     self.dt_ne_max.setValue(dt_ne[1])

    #     # set dt_range_te
    #     dt_te = parameters.get('dt_range_te', par_ini['dt_range_te'])
    #     self.dt_te_min.setValue(dt_te[0])
    #     self.dt_te_max.setValue(dt_te[1])

    def open_configurator(self):
        """ Open config manager dialog and collect data """
        manager = Configurator(self)

        # open previously loaded cfg data
        if hasattr(self, 'cfg'):
            manager.tdms_path_entry.setText(self.cfg['tdms_path'])
            signals_text = yaml.dump(self.cfg['signals'], default_flow_style=False)
            manager.signals_text.setText(signals_text)
            parameters_text = yaml.dump(self.parameters, default_flow_style=False)
            manager.parameters_text.setText(parameters_text)

        # when configurator sends signal accepted
        if manager.exec_() == QDialog.Accepted:
            # get information from configurator
            self.cfg = manager.get_cfg() # full cfg
            self.signals = manager.signals # loaded signals dict
            # get parameters from configurator
            self.parameters = self.cfg.get("parameters", None)

            if self.parameters is None:
                self.set_parameters(self.parameters_ini)
            else:
                self.set_parameters(self.parameters)

            self.update_probes_list()

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
        """ Создаем панель управления параметрами
            Доступны следующие параметры:
                1) Кнопка обновления графика
                2) Кпока отдаления графика
                3) Список выбора номера зонда
                4) Диапазон напряжения на АЧХ
                5) Диапазон по логарифму тока зонда на АЧХ
                6) Число соседних сканов для обработки (скользящее окно)
                7) Ограничение максимального значения Te,
                   превышающие значения будут обнулены
                8) Построение АЧХ по подъёму или по спаду тока
                9) Площадь зонда [мм^2]
                10) Сглаживание входного сигнала напряжения
                    Первый параметр - размер окна, второй - количество проходов
                11) Сглаживание входного сигнала тока зонда
                    Первый параметр - размер окна, второй - количество проходов
                12) Временной диапазон для выбора полки на токе зонда, нужен
                    для определения плотности
                13) Временной диапазон для выбора зоны построения АЧХ
        """
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
        # set ToolTip
        refresh_button.setToolTip(TIPS['refresh_button'])

        # 2. zoom out button
        zoom_out_button_layout = QHBoxLayout()
        zoom_out_button = QPushButton()
        zoom_out_button.setText("Отдалить")
        zoom_out_button_layout.addWidget(zoom_out_button)
        form_1.addRow(zoom_out_button_layout)
        # Подключение кнопки отдалить для обновления графика
        zoom_out_button.pressed.connect(self.zoom_out_plot)
        # set ToolTip
        zoom_out_button.setToolTip(TIPS['zoom_out_button'])

        # 3. probe (выпадающий список) ВЗ - выбор зонда
        self.probe = QComboBox()
        form_2.addRow("Выбор зонда:", self.probe)
        # set ToolTip
        self.probe.setToolTip(TIPS['probe'])

        # 4. u_range (два double spinbox)
        u_range_layout = QHBoxLayout()
        self.u_min = QDoubleSpinBox()
        self.u_min.setRange(-500, 500)

        self.u_max = QDoubleSpinBox()
        self.u_max.setRange(-500, 500)

        u_range_layout.addWidget(self.u_min)
        u_range_layout.addWidget(self.u_max)
        form_2.addRow("Диапазон u [В]:", u_range_layout)
        # set ToolTips
        self.u_min.setToolTip(TIPS['u_range']['u_min'])
        self.u_max.setToolTip(TIPS['u_range']['u_max'])

        # 5. lni_range (два double spinbox)
        lni_range_layout = QHBoxLayout()
        self.lni_min = QDoubleSpinBox()
        self.lni_min.setRange(-500, 500)

        self.lni_max = QDoubleSpinBox()
        self.lni_max.setRange(-500, 500)

        lni_range_layout.addWidget(self.lni_min)
        lni_range_layout.addWidget(self.lni_max)
        form_2.addRow("Диапазон ln(I):", lni_range_layout)
        # set ToolTips
        self.lni_min.setToolTip(TIPS['lni_range']['lni_min'])
        self.lni_max.setToolTip(TIPS['lni_range']['lni_max'])

        # 6. n_avg (1-50)
        self.n_avg = QSpinBox()
        self.n_avg.setRange(1, 50)
        form_3.addRow("Число сканов:", self.n_avg)
        # set ToolTip
        self.n_avg.setToolTip(TIPS['n_avg'])

        # 7. te threshold (float)
        te_threshold_layout = QHBoxLayout()
        self.te_threshold = QDoubleSpinBox()
        self.te_threshold.setRange(0, 100000)
        self.te_threshold.setSingleStep(5)
        te_threshold_layout.addWidget(self.te_threshold)
        form_3.addRow("Ограничить Te [эВ]:", te_threshold_layout)
        # set ToolTip
        self.te_threshold.setToolTip(TIPS['te_threshold'])

        # 8. sweep_direction (радиокнопки)
        self.sweep_group = QButtonGroup(self)
        self.sweep_up = QRadioButton("up")
        self.sweep_down = QRadioButton("down")
        self.sweep_group.addButton(self.sweep_up)
        self.sweep_group.addButton(self.sweep_down)
        # set ToolTips
        self.sweep_up.setToolTip(TIPS['sweep_direction']['up'])
        self.sweep_down.setToolTip(TIPS['sweep_direction']['down'])

        # layout
        sweep_layout = QHBoxLayout()
        sweep_layout.addWidget(self.sweep_up)
        sweep_layout.addWidget(self.sweep_down)
        form_4.addRow("Определение Te:", sweep_layout)

        # 9. probe_area (float)
        probe_area_layout = QHBoxLayout()
        self.probe_area = QDoubleSpinBox()
        self.probe_area.setRange(0, 100)
        self.probe_area.setDecimals(3)
        probe_area_layout.addWidget(self.probe_area)
        form_4.addRow("Площадь зонда [мм^2]:", probe_area_layout)
        # set ToolTip
        self.probe_area.setToolTip(TIPS['probe_area'])

        # 10. smooth_u
        smooth_u_layout = QHBoxLayout()
        self.smooth_u_avg = QSpinBox()
        self.smooth_u_avg.setRange(1, 100)
        self.smooth_u_n = QSpinBox()
        self.smooth_u_n.setRange(1, 100)
        smooth_u_layout.addWidget(self.smooth_u_avg)
        smooth_u_layout.addWidget(self.smooth_u_n)
        form_5.addRow("Сглаживание U:", smooth_u_layout)
        # set ToolTips
        self.smooth_u_avg.setToolTip(TIPS['smooth_u']['avg'])
        self.smooth_u_n.setToolTip(TIPS['smooth_u']['n'])

        # 11. smooth_i
        smooth_i_layout = QHBoxLayout()
        self.smooth_i_avg = QSpinBox()
        self.smooth_i_avg.setRange(1, 100)
        self.smooth_i_n = QSpinBox()
        self.smooth_i_n.setRange(1, 100)
        smooth_i_layout.addWidget(self.smooth_i_avg)
        smooth_i_layout.addWidget(self.smooth_i_n)
        form_5.addRow("Сглаживание I:", smooth_i_layout)
        # set ToolTips
        self.smooth_i_avg.setToolTip(TIPS['smooth_i']['avg'])
        self.smooth_i_n.setToolTip(TIPS['smooth_i']['n'])

        # 12. dt_range_ne (два float)
        dt_range_ne_layout = QHBoxLayout()
        self.dt_ne_min = QDoubleSpinBox()
        self.dt_ne_min.setRange(-20, 20)
        self.dt_ne_min.setSingleStep(0.1)

        self.dt_ne_max = QDoubleSpinBox()
        self.dt_ne_max.setRange(-20, 20)
        self.dt_ne_max.setSingleStep(0.1)

        dt_range_ne_layout.addWidget(self.dt_ne_min)
        dt_range_ne_layout.addWidget(self.dt_ne_max)
        form_6.addRow("Диапазон dt_ne:", dt_range_ne_layout)
        # set ToolTips
        self.dt_ne_min.setToolTip(TIPS['dt_range_ne']['dt_ne_min'])
        self.dt_ne_max.setToolTip(TIPS['dt_range_ne']['dt_ne_max'])

        # 13. dt_range_te (два double spinbox)
        dt_range_te_layout = QHBoxLayout()
        self.dt_te_min = QDoubleSpinBox()
        self.dt_te_min.setRange(-15, 15)
        self.dt_te_min.setSingleStep(0.01)

        self.dt_te_max = QDoubleSpinBox()
        self.dt_te_max.setRange(-15, 15)
        self.dt_te_max.setSingleStep(0.01)

        dt_range_te_layout.addWidget(self.dt_te_min)
        dt_range_te_layout.addWidget(self.dt_te_max)
        form_6.addRow("Диапазон dt_te:", dt_range_te_layout)
        # set ToolTips
        self.dt_te_min.setToolTip(TIPS['dt_range_te']['dt_te_min'])
        self.dt_te_max.setToolTip(TIPS['dt_range_te']['dt_te_max'])

        # Добавляем формы в основной layout
        control_layout.addLayout(form_1)
        control_layout.addLayout(form_2)
        control_layout.addLayout(form_3)
        control_layout.addLayout(form_4)
        control_layout.addLayout(form_5)
        control_layout.addLayout(form_6)
        parent_layout.addWidget(control_panel)

        self.set_parameters(self.parameters_ini) # set default parameters


    def update_parameters(self):
        """ prepare parameters for calc_te_ne """
        self.parameters = {
            'probe': self.probe.currentText(),
            'u_range': [self.u_min.value(), self.u_max.value()],
            'lni_range': [self.lni_min.value(), self.lni_max.value()],
            'n_avg': self.n_avg.value(),
            'te_threshold': self.te_threshold.value(),
            'sweep_direction': self.sweep_group.checkedButton().text(),
            'probe_area': self.probe_area.value(),
            'smooth_u': [self.smooth_u_avg.value(), self.smooth_u_n.value()],
            'smooth_i': [self.smooth_i_avg.value(), self.smooth_i_n.value()],
            'dt_range_ne': [self.dt_ne_min.value(), self.dt_ne_max.value()],
            'dt_range_te': [self.dt_te_min.value(), self.dt_te_max.value()],
            }

    def create_matplotlib_widget(self, parent_layout):
        """Создаем виджет для Matplotlib графика с toolbar"""
        mplstyle.use('fast') # ускорение отрисовки данных
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()
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

            self.update_parameters()
            self.probe_name = self.parameters['probe']

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
        ax1.plot(t, u, label='Напряжение, В')
        ax1.plot(t, i, label=f'{self.probe_name}, мА')
        # ax1.plot(t, tna.spandet.u_smooth, label='Voltage smoothed, V')
        # ax1.plot(t, tna.spandet.di, label='Probe Current Gradient')
        ax1.set_ylabel('Напряжение, В; Ток зонда, мА')
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
        ax2.set_ylabel(r'$T_e$, эВ')
        ax2.grid()
        # Te errorbars
        # te_errs = [kerr/k**2 for k, _, kerr, _ in info]
        # ax2.errorbar(te_t, te, yerr=te_errs, fmt='o', ecolor='black',
        # capsize=5, color='green')

        # ax3 - ne
        ax3.plot(res_t, ne, 'o', color='red')
        ax3.set_xlabel('t, мс')
        ax3.set_ylabel(r'$n_e, 10^{18} м^{-3}$')
        ax3.grid()

        # add red line cursor for axes
        self.multi = MultiCursor(self.figure.canvas, self.axes, color='r', lw=1)
        # connect event to open Current-Voltage Plot
        self.figure.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.figure.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.figure.canvas.mpl_connect('button_press_event',
                                       self.current_voltage_plot_on_ctrl_click)

    def on_key_press(self, event):
        """ Checks if CTRL button pressed. Used for Current-Voltage Plot """
        if event.key in ['ctrl', 'control']:
            self.ctrl_is_held = True

    def on_key_release(self, event):
        """ Checks if CTRL button released. Used for Current-Voltage Plot """
        if event.key in ['ctrl', 'control']:
            self.ctrl_is_held = False

    def current_voltage_plot_on_ctrl_click(self, event):
        """ Plots Current-Volatage Plot on CTRL+Click on axes """
        # check if control is pressed
        if not self.ctrl_is_held:
            return
        self.ctrl_is_held = False # release control after success ctrl+click

        idx = self.tna.find_nearest_info(event.xdata)
        try:
            fig_detail, ax_detail = plt.subplots()
            # Set the window title

            u_range = (self.u_min.value(), self.u_max.value())
            lni_range = (self.lni_min.value(), self.lni_max.value())
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

            p_title = f't = {int(t)} мс   Te = {int(1/k)} эВ  u = {u_range} В  lnI = {lni_range}'
            ax_detail.set_title(p_title)
            shot = self.signals['shot']
            w_title = f'#{shot} ВАХ {int(t)} мс'
            fig_detail.canvas.manager.set_window_title(w_title)
            ax_detail.grid(True)
            plt.show()

            # fig_detail, ax_detail = plt.subplots()
            # # Set the window title

            # u_range = (self.u_min.value(), self.u_max.value())
            # lni_range = (self.lni_min.value(), self.lni_max.value())
            # # u_wide, i_wide, u, i, k, c, time_mean
            # u_wide, i_wide, u, i, k, c, t = self.tna.cv_plot_data[idx]
            # # Convert lists to NumPy arrays
            # u_wide = np.array(u_wide)
            # i_wide = np.array(i_wide)
            # u = np.array(u)
            # i = np.array(i)
            # # remove negative values from arrays to put I in log function
            # # u_wide, i_wide = remove_negatives(u_wide, i_wide)
            # # u, i = remove_negatives(u, i)

            # ax_detail.plot(u_wide, i_wide, 'o', alpha=0.2)
            # ax_detail.plot(u, i, 'o', ms=5)
            # ax_detail.plot(u, u*k + c)

            # ax_detail.set_xlabel('U, В')
            # ax_detail.set_ylabel('I, мА')

            # p_title = f't = {int(t)} мс   Te = {int(1/k)} эВ  u = {u_range} В  lnI = {lni_range}'
            # ax_detail.set_title(p_title)
            # shot = self.signals['shot']
            # w_title = f'#{shot} ВАХ {int(t)} мс'
            # fig_detail.canvas.manager.set_window_title(w_title)
            # ax_detail.grid(True)
            # plt.show()

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

    def save_txt_te_ne(self):
        """ Save Te and ne for current probe as txt """
        if not hasattr(self, 'signals'):
            self.open_configurator()
        else:
            # get time, u, shot, probe_name, currents, fp_signals (not used)
            t, u, shot, currents, fp_singals = self.parse_signals_dict()

            # create TeNeAnalyzer instance
            tna = TeNeAnalyzer(t, u, currents[self.probe_name])
            # calculate Te, Ne using given parameters
            res_t, te, ne, info = tna.calc_te_ne(self.parameters)

            data_columns = [res_t, te, ne]
            headers = [
                f'{self.probe_name}.time [ms]',
                f'{self.probe_name}.Te [eV]',
                f'{self.probe_name}.ne [10^18 m^-3]'
            ]

            # Combine all columns into a 2D array (rows = data points, columns = variables)
            data_to_save = np.column_stack(data_columns)
            default_file_name = f"{shot}_{self.probe_name}_Te_ne"
            save_as_txt(data_to_save, headers, default_file_name)

    def save_txt_u_i(self):
        """ Save I, Te and ne for current probe as txt """
        if not hasattr(self, 'signals'):
            self.open_configurator()
        else:
            # get time, u, shot, probe_name, currents, fp_signals (not used)
            t, u, shot, currents, fp_singals = self.parse_signals_dict()

            # construct data array to save
            data_columns = [t, u, currents[self.probe_name]]
            headers = [
                f'{self.probe_name}.time [ms]',
                f'{self.probe_name}.U [U]',
                f'{self.probe_name}.I [mA]',
            ]

            # Combine all columns into a 2D array (rows = data points, columns = variables)
            data_to_save = np.column_stack(data_columns)
            default_file_name = f"{shot}_{self.probe_name}_U_I"
            save_as_txt(data_to_save, headers, default_file_name)

    def save_txt_fp(self):
        """Saves floating potentials data as txt """
        if not hasattr(self, 'signals'):
            self.open_configurator()
        else:
            # get time, u, shot, probe_name, currents (not used), fp_signals
            t, u, shot, currents, fp_singals = self.parse_signals_dict()

            if len(fp_singals) == 0:
                pop_up_window('Ошибка сохранения',
                'Отсутствуют зонды с меткой плавающего потенциала .FP\n\
(см. Инструкцию в конфигураторе)')
                return

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
