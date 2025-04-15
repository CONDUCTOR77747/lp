# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 17:01:19 2025

@author: Student
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (QApplication , QDialog, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,
                             QFileDialog, QMessageBox, QMenuBar, QAction,
                             QErrorMessage)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import yaml
from .defaults import ICON_PATH, INFO
from .utils import pop_up_window, verify_cfg
from lpy import load

class Configurator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор конфигурации")
        self.setMinimumSize(600, 400)
        self.setWindowIcon(QIcon(ICON_PATH))

        self.layout = QVBoxLayout()

        # Create menu bar
        self.create_menu()
        # Данные конфигурации
        self.cfg = {}
        # Создаем интерфейс
        self.create_ui()

    def create_menu(self):
        # Create a menubar
        menubar = QMenuBar(self)
        self.layout.addWidget(menubar)

        # Add menus to the menubar
        helpMenu = menubar.addMenu("Помощь")

        # Add actions to the menus
        helpAction = QAction("Инструкция", self)
        helpAction.triggered.connect(self.showHelpMessage)
        helpMenu.addAction(helpAction)

    def showHelpMessage(self):
        # Display your custom help message here
        info = INFO['configurator_instruction']
        pop_up_window(info['window_title'], info['text'], selectable_text=True)


    def create_ui(self):
        """Создаем пользовательский интерфейс"""

        # Поле для пути к TDMS файлу
        tdms_layout = QHBoxLayout()
        self.tdms_path_label = QLabel("Путь к TDMS файлу:")
        self.tdms_path_entry = QLineEdit()
        self.tdms_path_entry.setMinimumWidth(400)
        self.browse_button = QPushButton("Обзор")
        self.browse_button.clicked.connect(self.browse_tdms_path)

        tdms_layout.addWidget(self.tdms_path_label)
        tdms_layout.addWidget(self.tdms_path_entry)
        tdms_layout.addWidget(self.browse_button)
        self.layout.addLayout(tdms_layout)

        # Текстовое поле для сигналов
        self.signals_label = QLabel("Сигналы:")
        self.signals_text = QTextEdit()
        self.signals_text.setAcceptRichText(False)

        self.layout.addWidget(self.signals_label)
        self.layout.addWidget(self.signals_text)

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.load_button = QPushButton("Загрузить конфиг")
        self.load_button.clicked.connect(self.load_config)

        self.save_button = QPushButton("Сохранить конфиг")
        self.save_button.clicked.connect(self.save_config)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.ok_button_pushed)

        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.ok_button)
        self.layout.addLayout(buttons_layout)

        self.setLayout(self.layout)

    def browse_tdms_path(self):
        """Открывает диалоговое окно для выбора TDMS файла."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите TDMS файл",
            "",
            "TDMS files (*.tdms);;All files (*)"
        )
        if file_path:
            self.tdms_path_entry.setText(file_path)

    def ok_button_pushed(self):
        try:
            # clear previous cfg
            self.cfg = {}
            # fill cfg with new data
            self.fill_cfg_with_data()
        except Exception as e:
            pop_up_window("Ошибка", f"Не удалось загрузить файл:\n{str(e)}",
                          selectable_text=True)

        if verify_cfg(self.cfg):
            self.signals = load(None, self.cfg)
            self.accept() # send signal to main window that ok button pushed
        else:
            pop_up_window("Ошибка загрузки данных",
                        "Проверьте наличие TDMS файла и корректность сигналов")

    def load_config(self):
        """Загружает конфигурацию из файла."""

        # clear previous cfg
        self.cfg = {}

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить конфигурацию",
            "",
            "YAML files (*.yaml *.yml);;Text files (*.txt);;All files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    cfg = yaml.safe_load(file)
                    self.tdms_path_entry.setText(cfg.get('tdms_path', ''))

                    signals_text = yaml.dump(cfg.get('signals', {}))
                    self.signals_text.setPlainText(signals_text.strip())

            except Exception as e:
                pop_up_window("Ошибка", f"Не удалось загрузить файл:\n{str(e)}",
                              selectable_text=True)

    def save_config(self):
        """Сохраняет конфигурацию в файл."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить конфигурацию",
            "",
            "YAML files (*.yaml *.yml);;Text files (*.txt);;All files (*)",
            options=QFileDialog.Options()
        )

        if file_path:
            try:
                self.fill_cfg_with_data()

                with open(file_path, 'w', encoding='utf-8') as file:
                    yaml.dump(self.cfg, file, default_flow_style=False, allow_unicode=True)

                # Success saving notification
                pop_up_window("Сохранение", "Конфигурация успешно сохранена!")

            except Exception as e:
                pop_up_window("Ошибка", f"Не удалось загрузить файл:\n{str(e)}",
                              selectable_text=True)

    def fill_cfg_with_data(self):
        """ Fills cfg dict with data from text forms """
        # put tdms file path in cfg
        tdms_path = self.tdms_path_entry.text()
        if tdms_path is not None and len(tdms_path) > 0:
            self.cfg['tdms_path'] = tdms_path

        # put signals in cfg
        signals_text = self.signals_text.toPlainText().strip()
        if signals_text is not None and len(signals_text) > 0:
            self.cfg['signals'] = yaml.safe_load(signals_text)

    def get_cfg(self):
        """Возвращает данные конфигурации"""
        if verify_cfg(self.cfg):
            return self.cfg
        else:
            pop_up_window("Ошибка загрузки данных",
                          "Проверьте наличие TDMS файла и корректность сигналов")
