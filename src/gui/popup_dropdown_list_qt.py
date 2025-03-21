# -*- coding: utf-8 -*-
"""
Created on Tue Mar 18 18:05:04 2025

@author: Student
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button
from PyQt5.QtWidgets import QMenu, QAction, QApplication
from PyQt5.QtCore import QPoint
import sys

class QtDropdownMenu:
    """A dropdown menu for matplotlib using PyQt popups."""

    def __init__(self, fig, options, title="Select an option", callback=None, active=0, position=(0.8, 0.025)):
        """
        Initialize the dropdown menu.

        Parameters:
        -----------
        fig : matplotlib.figure.Figure
            The parent figure to attach the dropdown button to.
        options : list
            List of options for the dropdown menu.
        title : str, optional
            Title for the dropdown menu.
        callback : function, optional
            Function to call when an option is selected.
        active : int, optional
            Index of initially selected option.
        position : tuple, optional
            Position of the dropdown button in figure coordinates (x, y).
        """
        self.fig = fig
        self.options = options
        self.title = title
        self.callback = callback
        self.active = active

        # Create button on figure
        self.btn_ax = fig.add_axes([position[0], position[1], 0.15, 0.05])
        self.btn = Button(self.btn_ax, f"{title}: {options[active]}")
        self.btn.on_clicked(self.show_popup)

    def show_popup(self, event):
        """Show the Qt popup menu with options."""
        canvas = self.fig.canvas

        # Create menu
        menu = QMenu()

        # Add options to the menu
        for i, option in enumerate(self.options):
            action = QAction(option, menu)
            action.triggered.connect(lambda checked, idx=i: self.select_option(idx))
            menu.addAction(action)

        # Convert figure coordinates to pixel coordinates for Qt
        button_pos = self.btn_ax.get_position()
        # Get the button position in pixel coordinates
        x = button_pos.x0 * self.fig.get_figwidth() * self.fig.dpi
        y = button_pos.y0 * self.fig.get_figheight() * self.fig.dpi

        # Convert to QPoint and map to global coordinates
        qpoint = QPoint(int(x), int(y))
        global_pos = canvas.mapToGlobal(qpoint)

        # Show menu at button position
        menu.exec_(global_pos)

    def select_option(self, index):
        """Handle selection of an option."""
        self.active = index
        self.btn.label.set_text(f"{self.title}: {self.options[index]}")

        # Call the callback if provided
        if self.callback:
            self.callback(self.options[index])

        self.fig.canvas.draw_idle()

    def get_selected(self):
        """Return the currently selected option."""
        return self.options[self.active]


# Backend-agnostic implementation
class BackendAgnosticDropdown:
    """A dropdown menu that works with any matplotlib backend."""

    def __init__(self, fig, options, title="Select an option", callback=None, active=0, position=(0.8, 0.025)):
        """
        Initialize the dropdown menu.

        Parameters:
        -----------
        fig : matplotlib.figure.Figure
            The parent figure to attach the dropdown button to.
        options : list
            List of options for the dropdown menu.
        title : str, optional
            Title for the dropdown menu.
        callback : function, optional
            Function to call when an option is selected.
        active : int, optional
            Index of initially selected option.
        position : tuple, optional
            Position of the dropdown button in figure coordinates (x, y).
        """
        self.fig = fig
        self.options = options
        self.title = title
        self.callback = callback
        self.active = active
        self.buttons = []
        self.button_axes = []

        # Calculate button dimensions
        btn_height = 0.05
        btn_width = 0.15

        # Create main button
        self.main_ax = fig.add_axes([position[0], position[1], btn_width, btn_height])
        self.main_btn = Button(self.main_ax, f"{title}: {options[active]}")
        self.main_btn.on_clicked(self.toggle_dropdown)

        # Create hidden option buttons
        self.visible = False
        for i, option in enumerate(options):
            # Each option goes below the main button
            y_pos = position[1] - btn_height * (i + 1)
            ax = fig.add_axes([position[0], y_pos, btn_width, btn_height])
            btn = Button(ax, option)
            btn.on_clicked(lambda event, idx=i: self.select_option(idx))

            # Initially hide
            ax.set_visible(False)

            self.button_axes.append(ax)
            self.buttons.append(btn)

    def toggle_dropdown(self, event):
        """Toggle the visibility of dropdown options."""
        self.visible = not self.visible
        for ax in self.button_axes:
            ax.set_visible(self.visible)
        self.fig.canvas.draw_idle()

    def select_option(self, index):
        """Handle selection of an option."""
        self.active = index
        self.main_btn.label.set_text(f"{self.title}: {self.options[index]}")

        # Hide options
        self.visible = False
        for ax in self.button_axes:
            ax.set_visible(False)

        # Call the callback if provided
        if self.callback:
            self.callback(self.options[index])

        self.fig.canvas.draw_idle()

    def get_selected(self):
        """Return the currently selected option."""
        return self.options[self.active]


# Example usage
if __name__ == "__main__":
    # Create a simple plot
    fig, ax = plt.subplots(figsize=(8, 6))

    x = np.linspace(0, 10, 100)
    y_sin = np.sin(x)
    y_cos = np.cos(x)
    y_tan = np.tan(x)
    y_exp = np.exp(x/5)/100
    y_log = np.log(x+0.1)
    y_sqrt = np.sqrt(x)

    line, = ax.plot(x, y_sin)
    ax.set_title("Function Plotter")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)

    # Define callback function
    def on_selection(option):
        """Update the plot when a new function is selected."""
        if option == "sin(x)":
            line.set_ydata(y_sin)
            ax.set_ylim(-1.5, 1.5)
        elif option == "cos(x)":
            line.set_ydata(y_cos)
            ax.set_ylim(-1.5, 1.5)
        elif option == "tan(x)":
            line.set_ydata(y_tan)
            ax.set_ylim(-3, 3)
        elif option == "exp(x/5)":
            line.set_ydata(y_exp)
            ax.set_ylim(-0.5, 1)
        elif option == "log(x)":
            line.set_ydata(y_log)
            ax.set_ylim(-3, 3)
        elif option == "sqrt(x)":
            line.set_ydata(y_sqrt)
            ax.set_ylim(-0.5, 4)

        ax.set_title(f"Function: {option}")
        fig.canvas.draw_idle()

    try:
        # Try to use the Qt dropdown
        dropdown = QtDropdownMenu(
            fig,
            options=["sin(x)", "cos(x)", "tan(x)", "exp(x/5)", "log(x)", "sqrt(x)"],
            title="Function",
            callback=on_selection,
            active=0,
            position=(0.8, 0.025)
        )
        print("Using Qt dropdown")
    except Exception as e:
        print(f"Could not create Qt dropdown: {e}")
        # Fallback to backend-agnostic implementation
        dropdown = BackendAgnosticDropdown(
            fig,
            options=["sin(x)", "cos(x)", "tan(x)", "exp(x/5)", "log(x)", "sqrt(x)"],
            title="Function",
            callback=on_selection,
            active=0,
            position=(0.8, 0.025)
        )
        print("Using backend-agnostic dropdown")

    plt.tight_layout()
    plt.show()
