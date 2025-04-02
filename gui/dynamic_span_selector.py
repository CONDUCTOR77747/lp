# -*- coding: utf-8 -*-
"""
Created on Tue Mar 25 17:12:56 2025

@author: Student
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

class DynamicSpanSelector:
    def __init__(self, fig, ax):
        self.ax = ax
        self.fig = fig
        self.span = None
        self.text = None
        self.press_x = None

        # Connect event handlers
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)

    def on_press(self, event):
        if event.button != 1 or event.inaxes != self.ax:
            return

        self.press_x = event.xdata
        self.span = Rectangle((self.press_x, 0), 0, 1,
                            transform=self.ax.get_xaxis_transform(),
                            alpha=0.3, color='blue')
        self.ax.add_patch(self.span)

        # Create text annotation
        self.text = self.ax.text(self.press_x, 0.95, '',
                               transform=self.ax.get_xaxis_transform(),
                               ha='center', va='top',
                               bbox=dict(facecolor='white', alpha=0.8))
        self.fig.canvas.draw()

    def on_motion(self, event):
        if self.span is None or event.inaxes != self.ax:
            return

        current_x = event.xdata
        width = current_x - self.press_x

        # Update span
        self.span.set_width(width)

        # Update text
        dx = abs(width)
        self.text.set_text(f'Δx = {dx:.2f}')
        self.text.set_position(((self.press_x + current_x)/2, 0.95))

        self.fig.canvas.draw()

    def on_release(self, event):
        if self.span is None or event.button != 1:
            return

        # Remove span and text
        self.span.remove()
        self.text.remove()
        self.span = None
        self.text = None
        self.press_x = None

        self.fig.canvas.draw()

if __name__ == '__main__':
    # Example usage
    fig, ax = plt.subplots()
    ax.plot(np.random.rand(100))  # Sample plot

    selector = DynamicSpanSelector(ax)
    plt.show()
