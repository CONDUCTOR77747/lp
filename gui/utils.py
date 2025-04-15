# -*- coding: utf-8 -*-
"""
Created on Fri Apr  4 14:37:47 2025

@author: Student

Utils functions to create windows and similar elements
"""

import numpy as np
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from .defaults import ICON_PATH

def pop_up_window(window_title, text, selectable_text=False):
    """
    Creates general pop up window template
    For proviing instructions and information
    """
    msg = QMessageBox()
    msg.setWindowIcon(QIcon(ICON_PATH)) # default icon
    msg.setWindowTitle(window_title)
    msg.resize(640, 480)
    msg.setText(text)
    if selectable_text:
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
    msg.exec_()

def verify_cfg(cfg):
    """ Checks if cfg is not empty """
    if cfg and 'signals' in cfg and 'tdms_path' in cfg:
        if Path(cfg['tdms_path']).exists():
            return True

def save_as_txt(data, headers, default_file_name=""):
    """ Saves data into columns with headers as txt """
    # Open a file dialog to select where to save the file
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getSaveFileName(
        None,
        "Cохранить файл",
        default_file_name,
        "Текстовый документ (*.txt);;Все файлы (*)",
        options=options
    )
    if not file_path:  # If no file is selected, return
        return

    try:
        # Save the data to the selected file with tab as the separator
        np.savetxt(
            file_path,
            data,
            header='\t'.join(headers),  # Join headers with tab separator
            fmt='%s',                   # Format for saving data (adjust as needed)
            delimiter='\t',             # Use tab as the separator for data
            comments=''                 # Prevent '#' before the header
        )
    except Exception as e:
        print(f"Error saving file: {e}")
