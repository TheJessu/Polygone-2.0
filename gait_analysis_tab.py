from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QGridLayout, QScrollArea
from PyQt5.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from gait_cycle_plotter import GaitCyclePlotter
from generic_plotter import GenericDataPlotter

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

    def mouseDoubleClickEvent(self, event):
        self.plot_double_clicked.emit(self)

class GaitAnalysisTab(QWidget):
    def __init__(self):
        super().__init__()
        self.angles_plotter = GenericDataPlotter('ANGLES')
        self.moments_plotter = GenericDataPlotter('MOMENTS')
        self.powers_plotter = GenericDataPlotter('POWERS')
        self.gait_cycle_plotter = GaitCyclePlotter()
        self.gait_cycles = None

        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Kinematics tab
        self.kinematics_tab = QWidget()
        self.tab_widget.addTab(self.kinematics_tab, "Gait 1 Kinematics")
        kinematics_layout = QVBoxLayout(self.kinematics_tab)
        self.kinematics_scroll = QScrollArea()
        self.kinematics_scroll.setWidgetResizable(True)
        kinematics_layout.addWidget(self.kinematics_scroll)
        self.kinematics_container = QWidget()
        self.kinematics_layout = QGridLayout(self.kinematics_container)
        self.kinematics_scroll.setWidget(self.kinematics_container)

        # Kinetics tab
        self.kinetics_tab = QWidget()
        self.tab_widget.addTab(self.kinetics_tab, "Gait 1 Kinetics")
        kinetics_layout = QVBoxLayout(self.kinetics_tab)
        self.kinetics_scroll = QScrollArea()
        self.kinetics_scroll.setWidgetResizable(True)
        kinetics_layout.addWidget(self.kinetics_scroll)
        self.kinetics_container = QWidget()
        self.kinetics_layout = QGridLayout(self.kinetics_container)
        self.kinetics_scroll.setWidget(self.kinetics_container)

        self.value_label = QLabel("")
        self.layout.addWidget(self.value_label)

        self.gait_info_label = QLabel("")
        self.gait_info_label.setWordWrap(True)
        self.layout.addWidget(self.gait_info_label)

        self.plots = []
        self.vlines = []
        self.current_frame = 0
        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None

    def load_data(self, markers_data, marker_types, marker_labels):
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.plot_data()

    def plot_data(self):
        if self.markers_data is None or len(self.marker_types) == 0:
            return

        self.clear_plots()
        self.vlines = []
        self.angles_plotter.lines.clear()
        self.moments_plotter.lines.clear()
        self.powers_plotter.lines.clear()
        self.gait_cycle_plotter.lines = {}

        use_gait_cycle = self.gait_cycles and (self.gait_cycles['left'] or self.gait_cycles['right'])

        # Kinematics: 3 columns, groups: spine, pelvis, hip, knee, footprogress, each x,y,z
        groups = ['Spine', 'Pelvis', 'Hip', 'Knee', 'Footprogress']
        row = 0
        col = 0
        for group in groups:
            for component in ['x', 'y', 'z']:
                plot_widget = self.add_plot(self.kinematics_layout, row, col)
                title = self.get_kinematics_title(group, component)
                plot_widget.ax.set_title(title)
                plot_widget.ax.set_ylabel('Angle (degrees)')
                plot_widget.ax.set_xlabel('Gait Cycle (%)')
                self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, 'ANGLES', 'Angle (degrees)', self.current_frame, component=component)
                plot_widget.canvas.draw()
                col += 1
                if col >= 3:
                    col = 0
                    row += 1

        # Kinetics: 3x3 grid
        kinetics_plots = [
            ('Hip', 'y', 'ANGLES'),
            ('Knee', 'y', 'ANGLES'),
            ('Footprogress', 'y', 'ANGLES'),
            ('Hip', 'y', 'MOMENTS'),
            ('Knee', 'y', 'MOMENTS'),
            ('Ankle', 'y', 'MOMENTS'),
            ('Hip', 'z', 'POWERS'),
            ('Knee', 'z', 'POWERS'),
            ('Ankle', 'z', 'POWERS')
        ]
        for i, (group, component, plot_type) in enumerate(kinetics_plots):
            row = i // 3
            col = i % 3
            plot_widget = self.add_plot(self.kinetics_layout, row, col)
            title = self.get_kinetics_title(group, component, plot_type)
            plot_widget.ax.set_title(title)
            y_label = self.get_y_label(plot_type)
            plot_widget.ax.set_ylabel(y_label)
            plot_widget.ax.set_xlabel('Gait Cycle (%)')
            unit_conversion = 1000 if plot_type == 'MOMENTS' else 1
            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, plot_type, y_label, self.current_frame, component=component, unit_conversion_factor=unit_conversion)
            plot_widget.canvas.draw()

        self.kinematics_container.adjustSize()
        self.kinetics_container.adjustSize()

    def add_plot(self, layout, row, col):
        plot_widget = PlotWidget()
        layout.addWidget(plot_widget, row, col)
        self.plots.append(plot_widget)
        return plot_widget

    def clear_plots(self):
        for plot_widget in self.plots:
            plot_widget.figure.clear()
            plot_widget.canvas.draw()
        self.plots = []

    def get_kinematics_title(self, group, component):
        titles = {
            'Spine': {'x': 'Spine - Trunk Sway', 'y': 'Spine - Trunk Tilt', 'z': 'Spine - Trunk Rotation'},
            'Pelvis': {'x': 'Pelvis - Pelvic Obliquity', 'y': 'Pelvis - Pelvic Tilt', 'z': 'Pelvis - Pelvic Rotation'},
            'Hip': {'x': 'Hip - Hip Ab-Adduction', 'y': 'Hip - Hip Flexion-Extension', 'z': 'Hip - Hip Rotation'},
            'Knee': {'x': 'Knee - X', 'y': 'Knee - Knee Flexion-Extension', 'z': 'Knee - Z'},
            'Footprogress': {'x': 'Footprogress - X', 'y': 'Footprogress - Dorsi-Plantarflexion', 'z': 'Footprogress - Foot Progression'}
        }
        return titles.get(group, {}).get(component, f'{group} - {component.upper()}')

    def get_kinetics_title(self, group, component, plot_type):
        if plot_type == 'ANGLES':
            return f'{group} - {component.upper()}'
        elif plot_type == 'MOMENTS':
            return f'{group} - {component.upper()} Moment'
        elif plot_type == 'POWERS':
            return f'{group} - {component.upper()} Power'

    def get_y_label(self, plot_type):
        labels = {'ANGLES': 'Angle (degrees)', 'MOMENTS': 'Moment (Nmm)', 'POWERS': 'Power (W)'}
        return labels.get(plot_type, '')

    def get_plotter(self, plot_type):
        plotters = {'ANGLES': self.angles_plotter, 'MOMENTS': self.moments_plotter, 'POWERS': self.powers_plotter}
        return plotters.get(plot_type)

    def set_current_frame(self, frame_index):
        self.current_frame = frame_index
        for vline in self.vlines:
            if self.current_frame is not None:
                vline.set_xdata([self.current_frame])
                vline.set_visible(True)
            else:
                vline.set_visible(False)
        for plot in self.plots:
            plot.canvas.draw_idle()

    def set_gait_info(self, info_text):
        self.gait_info_label.setText(info_text)

    def set_gait_cycles(self, gait_cycles):
        self.gait_cycles = gait_cycles

    def clear_data(self):
        self.clear_plots()
        self.vlines = []
        self.value_label.setText("")
        self.gait_info_label.setText("")
        self.angles_plotter.lines = {}
        self.moments_plotter.lines = {}
        self.powers_plotter.lines = {}
        self.gait_cycle_plotter.lines = {}
