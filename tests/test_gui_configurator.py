# -*- coding: utf-8 -*-
"""
Created on Wed Apr  9 22:05:18 2025

@author: Ammosov
"""

import yaml
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from gui import Configurator  # Replace with the actual module name

@pytest.fixture
def configurator(qtbot):
    """Fixture to create and return a Configurator instance."""
    widget = Configurator()
    qtbot.addWidget(widget)
    return widget

def test_initial_state(configurator):
    """Test that the initial state of the Configurator is correct."""
    assert configurator.tdms_path_entry.text() == ""
    assert configurator.signals_text.toPlainText() == ""

def test_browse_tdms_path(qtbot, configurator, mocker):
    """Test that browsing for a TDMS file updates the path entry."""
    mocker.patch("PyQt5.QtWidgets.QFileDialog.getOpenFileName", return_value=("test_file.tdms", ""))
    configurator.browse_tdms_path()
    assert configurator.tdms_path_entry.text() == "test_file.tdms"

def test_load_config(qtbot, configurator, mocker):
    """Test loading a configuration file."""
    mock_config = {
        "tdms_path": "test_file.tdms",
        "signals": {
            "signal1": {"channel": "ch1", "factor": 1.0},
            "signal2": {"channel": "ch2", "factor": 2.0},
        },
    }
    mocker.patch("PyQt5.QtWidgets.QFileDialog.getOpenFileName", return_value=("config.yaml", ""))
    mocker.patch("builtins.open", mocker.mock_open(read_data=yaml.dump(mock_config)))

    configurator.load_config()

    # Verify TDMS path
    assert configurator.tdms_path_entry.text() == "test_file.tdms"

    # Verify signals text
    expected_signals_text = (
        "signal1:\n"
        "  channel: ch1\n"
        "  factor: 1.0\n"
        "signal2:\n"
        "  channel: ch2\n"
        "  factor: 2.0"
    )
    assert configurator.signals_text.toPlainText().strip() == expected_signals_text

def test_save_config(qtbot, configurator, mocker):
    """Test saving a configuration file."""
    # Set up initial data in the UI
    configurator.tdms_path_entry.setText("test_file.tdms")
    signals_text = (
        "signal1:\n"
        "  channel: ch1\n"
        "  factor: 1.0\n"
        "signal2:\n"
        "  channel: ch2\n"
        "  factor: 2.0\n"
    )
    configurator.signals_text.setPlainText(signals_text)

    # Mock QFileDialog.getSaveFileName to return a valid file path
    mocker.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName", return_value=("config.yaml", ""))

    # Mock open() to prevent actual file operations
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    # Use QTimer to automatically close the QMessageBox after it appears
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(250, lambda: QApplication.activeWindow().accept())

    # Call save_config
    configurator.save_config()

    # Verify that fill_cfg_with_data was called and cfg was populated correctly
    expected_config = {
        "tdms_path": "test_file.tdms",
        "signals": {
            "signal1": {"channel": "ch1", "factor": 1.0},
            "signal2": {"channel": "ch2", "factor": 2.0},
        },
    }
    assert configurator.cfg == expected_config

    # Verify that open() was called with the correct arguments
    mock_open.assert_called_once_with("config.yaml", "w", encoding="utf-8")

    # Verify that yaml.dump was called with the correct data
    handle = mock_open.return_value
    written_data = "".join(
        call.args[0]
        for call in handle.write.mock_calls
    )
    expected_yaml = yaml.dump(
        expected_config,
        default_flow_style=False,
        allow_unicode=True
    )
    assert written_data == expected_yaml


def test_ok_button_pushed(qtbot, configurator, mocker):
    """Test the behavior of the OK button."""
    # Mock load function and signals processing
    mock_load = mocker.patch("gui.configurator.load", return_value="processed_signals")

    # Set up valid data in the UI
    configurator.tdms_path_entry.setText("test_data/T15MD_3008.tdms")

    signals_text = (
        "LP.Power:\n"
        "  channel: LP.15\n"
        "  factor: -34\n"
        "LP.09:\n"
        "  channel: LP.09\n"
        "  factor: 1000 / 50\n"
        "LP.13:\n"
        "  channel: LP.03\n"
        "  factor: 1000 / 100\n"
    )

    configurator.signals_text.setPlainText(signals_text)

    # Simulate clicking the OK button
    qtbot.mouseClick(configurator.ok_button, Qt.LeftButton)
    qtbot.waitUntil(lambda: mock_load.called, timeout=200)

    # Verify that load was called with correct arguments
    expected_cfg = {
        "tdms_path": "test_data/T15MD_3008.tdms",
        "signals": {
            "LP.Power": {"channel": "LP.15", "factor": -34},
            "LP.09": {"channel": "LP.09", "factor": "1000 / 50"},
            "LP.13": {"channel": "LP.03", "factor": "1000 / 100"},
        },
    }

    mock_load.assert_called_once_with(None, expected_cfg)

if __name__ == '__main__':
    pytest.main(['test_gui_configurator.py'])
