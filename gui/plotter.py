# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 13:46:20 2025

@author: User
"""

import numpy as np
import matplotlib.pyplot as plt
from .te_ne_analyzer import TeNeAnalyzer

class Plotter():
    def __init__(self, tna):
        """ init """

        self.tna = tna

    def __call__(self):
        pass

class InteractivePlot:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.x = np.linspace(0, 10, 100)
        self.y = np.sin(self.x)
        self.line, = self.ax.plot(self.x, self.y)
        self.annotations = []
        self._connect_events()
        self.visible = True

    def _connect_events(self):
        """Connect matplotlib events"""
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)

    def on_click(self, event):
        """Handle mouse click events"""
        if event.inaxes != self.ax:
            return

        if event.button == 1:  # Left click
            self._add_vertical_line(event.xdata)
        elif event.button == 3:  # Right click
            self._remove_closest_line(event.xdata)

    def on_key(self, event):
        """Handle key press events"""
        if event.key == 't':
            self.visible = not self.visible
            self.line.set_visible(self.visible)
            self._redraw()
        elif event.key == 'c':
            self._clear_annotations()

    def on_hover(self, event):
        """Handle mouse motion events"""
        if event.inaxes == self.ax:
            self.ax.set_title(f'x: {event.xdata:.2f}, y: {event.ydata:.2f}')
            self.fig.canvas.draw_idle()

    def _add_vertical_line(self, xpos):
        """Add vertical line at clicked position"""
        line = self.ax.axvline(x=xpos, color='r', alpha=0.5)
        self.annotations.append(line)
        self._redraw()

    def _remove_closest_line(self, xpos):
        """Remove closest vertical line"""
        if not self.annotations:
            return

        distances = [abs(anno.get_xdata()[0] - xpos)
                    for anno in self.annotations]
        idx = np.argmin(distances)
        self.annotations.pop(idx).remove()
        self._redraw()

    def _clear_annotations(self):
        """Remove all added lines"""
        for anno in self.annotations:
            anno.remove()
        self.annotations.clear()
        self._redraw()

    def _redraw(self):
        """Update the plot"""
        self.fig.canvas.draw()

    def show(self):
        """Display the plot"""
        plt.show()

if __name__ == "__main__":
    plotter = InteractivePlot()
    plotter.show()
