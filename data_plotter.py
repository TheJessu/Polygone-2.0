from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel, QPushButton
from angles_tab import AnglesTab
from forces_tab import ForcesTab
from moments_tab import MomentsTab
from powers_tab import PowersTab
from gait_cycle_plotter import GaitCyclePlotter
import math
import numpy as np
from PyQt5.QtCore import pyqtSignal
from pxdExport import PXDExporter

class DataPlotter(QWidget):
    editable_values_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        btn_layout = QHBoxLayout()
        self.import_avg_btn = QPushButton("Import Averages")
        self.import_avg_btn.clicked.connect(self.import_averages)
        btn_layout.addWidget(self.import_avg_btn)
        btn_layout.addStretch()
        self.layout.addLayout(btn_layout)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.markers_data = None
        self.marker_types = []
        self.marker_labels = []
        self.current_frame = 0
        self.gait_cycles = None

        self.gait_cycle_plotter = GaitCyclePlotter()

        # Editable values storage: key is (group, component), value is {'ymin': val, 'ymax': val, 'title': str}
        self.editable_values = {}

        self.plot_types_config = {
            'ANGLES': {'tab': AnglesTab(), 'y_label': 'Angle (degrees)', 'unit_conversion': 1},
            'MOMENTS': {'tab': MomentsTab(), 'y_label': 'Moment (Nm/kg)', 'unit_conversion': 1},
            'POWERS': {'tab': PowersTab(), 'y_label': 'Power (W/kg)', 'unit_conversion': 1},
            'FORCES': {'tab': ForcesTab(), 'y_label': 'Force (N)', 'unit_conversion': 1}
        }

        self.max_plots = 4

        for plot_type, config in self.plot_types_config.items():
            self.tab_widget.addTab(config['tab'], plot_type)
            # Connect editable value changed signal
            config['tab'].editable_value_changed.connect(self.on_editable_value_changed)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

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



    def set_current_frame(self, frame_index):
        self.current_frame = frame_index
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            current_tab.set_current_frame(frame_index)

    def set_gait_info(self, events_data, frame_rate=100, first_frame=0):
        if not events_data:
            self.gait_cycles = None
            for _, config in self.plot_types_config.items():
                config['tab'].set_gait_info("")
            self.plot_data()
            return

        left_strikes = sorted([int(e['time'] * frame_rate) - first_frame for e in events_data if e.get('foot') == 'left' and e.get('type') == 'strike'])
        right_strikes = sorted([int(e['time'] * frame_rate) - first_frame for e in events_data if e.get('foot') == 'right' and e.get('type') == 'strike'])

        self.gait_cycles = {'left': [], 'right': []}
        for i in range(len(left_strikes) - 1):
            self.gait_cycles['left'].append((left_strikes[i], left_strikes[i+1]))
        for i in range(len(right_strikes) - 1):
            self.gait_cycles['right'].append((right_strikes[i], right_strikes[i+1]))

        # Compute foot-off percentages from first gait cycle of each side
        fo_frames = {
            'left': sorted([int(e['time'] * frame_rate) - first_frame for e in events_data if e.get('foot') == 'left' and e.get('type') == 'off']),
            'right': sorted([int(e['time'] * frame_rate) - first_frame for e in events_data if e.get('foot') == 'right' and e.get('type') == 'off'])
        }
        foot_off_pcts = {}
        for side in ['left', 'right']:
            cycles = self.gait_cycles.get(side, [])
            fos = fo_frames.get(side, [])
            if cycles and fos:
                start, end = cycles[0]
                cycle_len = end - start
                for fo in fos:
                    if start <= fo < end and cycle_len > 0:
                        foot_off_pcts[side] = (fo - start) / cycle_len * 100
                        break

        for _, config in self.plot_types_config.items():
            if hasattr(config['tab'], 'set_foot_off_pcts'):
                config['tab'].set_foot_off_pcts(foot_off_pcts)
            config['tab'].set_gait_cycles(self.gait_cycles)

        self.plot_data()
    
    def on_editable_value_changed(self, key, change_type, value_dict):
        # Update editable values
        if key not in self.editable_values:
            self.editable_values[key] = {}
        self.editable_values[key].update(value_dict)
        # Update editable values in tabs
        for _, config in self.plot_types_config.items():
            if hasattr(config['tab'], 'set_editable_values'):
                config['tab'].set_editable_values(self.editable_values)
        self.editable_values_updated.emit(self.editable_values)
        # Replot all tabs
        self.plot_data()

    def clear_data(self):
        self.markers_data = None
        self.marker_types = []
        self.marker_labels = []
        self.gait_cycles = None
        for _, config in self.plot_types_config.items():
            config['tab'].clear_data()

    def import_averages(self):
        data = PXDExporter.import_averages(self)
        if data:
            for plot_type, config in self.plot_types_config.items():
                if hasattr(config['tab'], 'set_imported_averages'):
                    config['tab'].set_imported_averages(data.get(plot_type, {}))
            self.plot_data()

    def on_tab_changed(self, index):
        current_tab = self.tab_widget.widget(index)
        if current_tab:
            current_tab.set_current_frame(self.current_frame)
