from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel, QSpinBox
from angles_tab import AnglesTab
from forces_tab import ForcesTab
from moments_tab import MomentsTab
from powers_tab import PowersTab
from gait_cycle_plotter import GaitCyclePlotter
import math
import numpy as np

class DataPlotter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.markers_data = None
        self.marker_types = []
        self.marker_labels = []
        self.current_frame = 0
        self.gait_cycles = None

        self.gait_cycle_plotter = GaitCyclePlotter()

        self.plot_types_config = {
            'ANGLES': {'tab': AnglesTab(), 'y_label': 'Angle (degrees)', 'unit_conversion': 1},
            'MOMENTS': {'tab': MomentsTab(), 'y_label': 'Moment (Nmm)', 'unit_conversion': 1000},
            'POWERS': {'tab': PowersTab(), 'y_label': 'Power (W)', 'unit_conversion': 1},
            'FORCES': {'tab': ForcesTab(), 'y_label': 'Force (N)', 'unit_conversion': 1}
        }

        self.max_plots = 4
        plots_layout = QHBoxLayout()
        plots_layout.addWidget(QLabel("Max Plots:"))
        self.plots_spinbox = QSpinBox()
        self.plots_spinbox.setMinimum(1)
        self.plots_spinbox.setMaximum(12)
        self.plots_spinbox.setValue(self.max_plots)
        self.plots_spinbox.valueChanged.connect(self.on_max_plots_changed)
        plots_layout.addWidget(self.plots_spinbox)
        plots_layout.addStretch()
        self.layout.addLayout(plots_layout)

        for plot_type, config in self.plot_types_config.items():
            self.tab_widget.addTab(config['tab'], plot_type)

    def load_data(self, markers_data, marker_types, marker_labels, angle_units='degrees', body_mass=None):
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.body_mass = body_mass
        for plot_type, config in self.plot_types_config.items():
            config['tab'].load_data(markers_data, marker_types, marker_labels, body_mass)
        self.plot_data()

    def plot_data(self):
        if self.markers_data is None or len(self.marker_types) == 0:
            return

        for plot_type, config in self.plot_types_config.items():
            tab = config['tab']
            tab.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots)

    def on_max_plots_changed(self, value):
        self.max_plots = value
        self.plot_data()

    def set_current_frame(self, frame_index):
        self.current_frame = frame_index
        for plot_type, config in self.plot_types_config.items():
            config['tab'].set_current_frame(frame_index)

    def set_gait_info(self, events_data):
        if not events_data:
            self.gait_cycles = None
            for _, config in self.plot_types_config.items():
                config['tab'].set_gait_info("")
            self.plot_data()
            return

        left_strikes = sorted([int(e['time'] * 100) for e in events_data if e.get('foot') == 'left' and e.get('type') == 'strike'])
        right_strikes = sorted([int(e['time'] * 100) for e in events_data if e.get('foot') == 'right' and e.get('type') == 'strike'])

        self.gait_cycles = {'left': [], 'right': []}
        for i in range(len(left_strikes) - 1):
            self.gait_cycles['left'].append((left_strikes[i], left_strikes[i+1]))
        for i in range(len(right_strikes) - 1):
            self.gait_cycles['right'].append((right_strikes[i], right_strikes[i+1]))

        for _, config in self.plot_types_config.items():
            config['tab'].set_gait_cycles(self.gait_cycles)

        self.plot_data()
    
    def clear_data(self):
        self.markers_data = None
        self.marker_types = []
        self.marker_labels = []
        self.gait_cycles = None
        for _, config in self.plot_types_config.items():
            config['tab'].clear_data()
        self.gait_analysis_tab.clear_data()
