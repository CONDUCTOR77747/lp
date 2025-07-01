# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 09:15:23 2025

@author: Ammosov

Main file to launch program with GUI
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
