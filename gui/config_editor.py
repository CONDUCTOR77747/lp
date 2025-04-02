# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 17:01:19 2025

@author: Student
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import yaml

class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Редактор конфигурации")

        # Поле для пути к TDMS файлу
        self.tdms_path_label = tk.Label(root, text="Путь к TDMS файлу:")
        self.tdms_path_label.grid(row=0, column=0, sticky="w")

        self.tdms_path_entry = tk.Entry(root, width=50)
        self.tdms_path_entry.grid(row=0, column=1, padx=5, pady=5)

        self.browse_button = tk.Button(root, text="Обзор", command=self.browse_tdms_path)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)

        # Текстовое поле для сигналов
        self.signals_label = tk.Label(root, text="Сигналы:")
        self.signals_label.grid(row=1, column=0, sticky="w")

        self.signals_text = tk.Text(root, width=60, height=10)
        self.signals_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        # Кнопки
        self.load_button = tk.Button(root, text="Загрузить конфиг", command=self.load_config)
        self.load_button.grid(row=3, column=0, padx=5, pady=5)

        self.save_button = tk.Button(root, text="Сохранить конфиг", command=self.save_config)
        self.save_button.grid(row=3, column=1, padx=5, pady=5)

        self.ok_button = tk.Button(root, text="OK", command=self.ok_action)
        self.ok_button.grid(row=3, column=2, padx=5, pady=5)

        # Данные конфигурации
        self.config_data = {}

    def browse_tdms_path(self):
        """Открывает диалоговое окно для выбора TDMS файла."""
        file_path = filedialog.askopenfilename(filetypes=[("TDMS files", "*.tdms")])
        if file_path:
            self.tdms_path_entry.delete(0, tk.END)
            self.tdms_path_entry.insert(0, file_path)

    def load_config(self):
        """Загружает конфигурацию из файла."""
        file_path = filedialog.askopenfilename(
            filetypes=[("YAML files", "*.yaml *.yml"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.config_data = yaml.safe_load(file)
                    self.tdms_path_entry.delete(0, tk.END)
                    self.tdms_path_entry.insert(0, self.config_data.get('tdms_path', ''))

                    self.signals_text.delete(1.0, tk.END)
                    signals = self.config_data.get('signals', {})
                    for signal, params in signals.items():
                        self.signals_text.insert(tk.END, f"{signal}:\n")
                        self.signals_text.insert(tk.END, f"  channel: {params['channel']}\n")
                        self.signals_text.insert(tk.END, f"  factor: {params['factor']}\n")
                        self.signals_text.insert(tk.END, "\n")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")

    def save_config(self):
        """Сохраняет конфигурацию в файл."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml *.yml"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.config_data['tdms_path'] = self.tdms_path_entry.get()

                signals_text = self.signals_text.get(1.0, tk.END).strip()
                signals = {}
                for signal_block in signals_text.split("\n\n"):
                    lines = signal_block.split("\n")
                    signal_name = lines[0].strip(":")
                    channel = lines[1].split(": ")[1]
                    factor = lines[2].split(": ")[1]
                    signals[signal_name] = {'channel': channel, 'factor': factor}

                self.config_data['signals'] = signals

                with open(file_path, 'w') as file:
                    yaml.dump(self.config_data, file, default_flow_style=False)

                messagebox.showinfo("Сохранение", "Конфигурация успешно сохранена!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    def ok_action(self):
        """Сохраняет конфигурацию и закрывает приложение."""
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigEditor(root)
    root.mainloop()
