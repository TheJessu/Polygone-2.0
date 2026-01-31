from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QGridLayout, QLabel
from PyQt5.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from gait_cycle_plotter import GaitCyclePlotter

class PlotWidget(QWidget):
    plot_double_clicked = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(4, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.canvas.setFixedSize(200, 200)

        self.figure.patch.set_facecolor('white')
        self.ax.set_facecolor('white')

    def mouseDoubleClickEvent(self, event):
        self.plot_double_clicked.emit(self)

class GaitAnalysisTab(QWidget):
    def __init__(self):
        super().__init__()
        self.gait_cycle_plotter = GaitCyclePlotter()
        self.gait_cycles = None

        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Kinematics Tab
        self.kinematics_tab = QWidget()
        self.kinematics_layout = QGridLayout(self.kinematics_tab)
        self.tab_widget.addTab(self.kinematics_tab, "Gait 1 Kinematics")

        # Kinetics Tab
        self.kinetics_tab = QWidget()
        self.kinetics_layout = QGridLayout(self.kinetics_tab)
        self.tab_widget.addTab(self.kinetics_tab, "Gait 1 Kinetics")

        self.kinematics_plots = []
        self.kinetics_plots = []
        self.vlines = []

        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None
        self.current_frame = 0

        self.setup_kinematics_plots()
        self.setup_kinetics_plots()

    def setup_kinematics_plots(self):
        groups = ['Spine', 'Pelvis', 'Hip', 'Knee', 'Footprogress']
        components = ['x', 'y', 'z']
        row = 0
        for group in groups:
            col = 0
            for comp in components:
                plot_widget = PlotWidget(self.kinematics_tab)
                plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
                self.kinematics_layout.addWidget(plot_widget, row, col)
                self.kinematics_plots.append((plot_widget, group, comp))
                col += 1
            row += 1

    def setup_kinetics_plots(self):
        # 3x3 grid
        plots_config = [
            ('Hip', 'y', 'ANGLES', 'Angle'),
            ('Knee', 'y', 'ANGLES', 'Angle'),
            ('Footprogress', 'y', 'ANGLES', 'Angle'),
            ('Hi', 'y', 'MOMENTS', 'Moment (Nmm)', 1000),
            ('Kne', 'y', 'MOMENTS', 'Moment (Nmm)', 1000),
            ('Ankl', 'y', 'MOMENTS', 'Moment (Nmm)', 1000),
            ('Hi', 'z', 'POWERS', 'Power (W)'),
            ('Kne', 'z', 'POWERS', 'Power (W)'),
            ('Ankl', 'z', 'POWERS', 'Power (W)')
        ]
        for i, (group, comp, plot_type, y_label, *unit_factor) in enumerate(plots_config):
            row = i // 3
            col = i % 3
            plot_widget = PlotWidget(self.kinetics_tab)
            plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
            self.kinetics_layout.addWidget(plot_widget, row, col)
            self.kinetics_plots.append((plot_widget, group, comp, plot_type, y_label, unit_factor[0] if unit_factor else 1))

    def load_data(self, markers_data, marker_types, marker_labels):
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.plot_data()

    def set_gait_cycles(self, gait_cycles):
        self.gait_cycles = gait_cycles
        self.plot_data()

    def set_current_frame(self, frame_index):
        self.current_frame = frame_index
        # Update vlines
        for vline in self.vlines:
            if vline:
                # Remove old vline
                vline.remove()
        self.vlines = []
        for plot_widget, *_ in self.kinematics_plots + [(p[0], p[1], p[2], p[3], p[4], p[5]) for p in self.kinetics_plots]:
            if self.gait_cycles:
                for side in ['left', 'right']:
                    for start, end in self.gait_cycles.get(side, []):
                        if start <= self.current_frame < end:
                            cycle_len = end - start
                            if cycle_len > 0:
                                percentage = (self.current_frame - start) / cycle_len * 100
                                vline = plot_widget.ax.axvline(x=percentage, color='red', linestyle='--', linewidth=2)
                                self.vlines.append(vline)
                                break
                    if self.vlines:
                        break
            plot_widget.canvas.draw()

    def plot_data(self):
        if self.markers_data is None or not self.gait_cycles:
            return

        # Clear existing plots
        for plot_widget, *_ in self.kinematics_plots:
            plot_widget.ax.clear()
        for plot_widget, *_ in self.kinetics_plots:
            plot_widget.ax.clear()
        self.vlines = []

        # Plot kinematics
        for plot_widget, group, comp in self.kinematics_plots:
            title = f'{group} - {comp.upper()}'
            if group.lower() == 'spine':
                title = f'{group} - {"Trunk Sway" if comp == "x" else "Trunk Tilt" if comp == "y" else "Trunk Rotation"}'
            elif group.lower() == 'pelvis':
                title = f'{group} - {"Pelvic Obliquity" if comp == "x" else "Pelvic Tilt" if comp == "y" else "Pelvic Rotation"}'
            elif group.lower() == 'hip':
                title = f'{group} - {"Hip Ab-Adduction" if comp == "x" else "Hip Flexion-Extension" if comp == "y" else "Hip Rotation"}'
            elif group.lower() == 'knee':
                title = f'{group} - {"Knee Flexion-Extension" if comp == "y" else comp.upper()}'
            elif group.lower() == 'footprogress':
                title = f'{group} - {"Dorsi-Plantarflexion" if comp == "y" else "Foot Progression" if comp == "z" else comp.upper()}'
            plot_widget.ax.set_title(title)
            plot_widget.ax.set_xlabel('Gait Cycle (%)')
            plot_widget.ax.set_ylabel('Angle')
            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, 'ANGLES', 'Angle', self.current_frame, component=comp)
            plot_widget.canvas.draw()
            # Make plots with no name change invisible
            if title == f'{group} - {comp.upper()}':
                plot_widget.setVisible(False)
            else:
                plot_widget.setVisible(True)

        # Plot kinetics
        for plot_widget, group, comp, plot_type, y_label, unit_factor in self.kinetics_plots:
            if plot_type == 'ANGLES':
                if group.lower() == 'hip' and comp == 'y':
                    title = 'Hip Flexion-Extension'
                elif group.lower() == 'knee' and comp == 'y':
                    title = 'Knee Flexion-Extension'
                elif group.lower() == 'footprogress' and comp == 'y':
                    title = 'Dorsi-Plantarflexion'
                else:
                    title = f'{group} - {comp.upper()}'
            elif plot_type == 'MOMENTS':
                if group.lower() == 'hi' and comp == 'y':
                    title = 'Hip Flex-Ext Moment'
                elif group.lower() == 'kne' and comp == 'y':
                    title = 'Knee Flex-Ext Moment'
                elif group.lower() == 'ankl' and comp == 'y':
                    title = 'Dors-Plan Moment'
                else:
                    title = f'{group} - {comp.upper()}'
            elif plot_type == 'POWERS':
                if group.lower() == 'hi' and comp == 'z':
                    title = 'Hip Power'
                elif group.lower() == 'kne' and comp == 'z':
                    title = 'Knee Power'
                elif group.lower() == 'ankl' and comp == 'z':
                    title = 'Ankle Power'
                else:
                    title = f'{group} - {comp.upper()}'
            else:
                title = f'{group} - {comp.upper()}'
            plot_widget.ax.set_title(title)
            plot_widget.ax.set_xlabel('Gait Cycle (%)')
            plot_widget.ax.set_ylabel(y_label)
            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, plot_type, y_label, self.current_frame, component=comp, unit_conversion_factor=unit_factor)
            plot_widget.canvas.draw()
            # Make plots with no name change invisible
            if title == f'{group} - {comp.upper()}':
                plot_widget.setVisible(False)
            else:
                plot_widget.setVisible(True)

    def on_plot_double_clicked(self, plot_widget):
        # Simple zoom, but since fixed layout, maybe just ignore or implement basic zoom
        pass

    def clear_data(self):
        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None
        self.gait_cycles = None
        for plot_widget, *_ in self.kinematics_plots:
            plot_widget.ax.clear()
            plot_widget.canvas.draw()
        for plot_widget, *_ in self.kinetics_plots:
            plot_widget.ax.clear()
            plot_widget.canvas.draw()
        self.vlines = []
