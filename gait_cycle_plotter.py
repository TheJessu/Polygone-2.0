from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import math
import numpy as np

class GaitCyclePlotter:
    def __init__(self):
        self.lines = {}

    def plot_gait_cycle_data(self, ax, markers_data, marker_labels, marker_types, selected_group, gait_cycles, plot_type, y_label, current_frame=None, unit_conversion_factor=1, component='magnitude'):
        type_indices = [i for i, t in enumerate(marker_types) if t == plot_type]
        if selected_group != "All":
            type_indices = [
                idx for idx in type_indices
                if idx < len(marker_labels) and marker_labels[idx] and
                (label := marker_labels[idx]) and
                (
                    (label.startswith('L') or label.startswith('R')) and
                    label[1:-len(plot_type)].lower().capitalize() == selected_group
                ) or
                (
                    (label[:-len(plot_type)].lower().capitalize() if label.endswith(plot_type) else label.lower().capitalize()) == selected_group
                )
            ]

        all_left_cycles_norm, all_right_cycles_norm = [], []
        for marker_idx in type_indices:
            if marker_idx >= markers_data.shape[1]:
                continue
            
            label = marker_labels[marker_idx]
            data = markers_data[:, marker_idx, :] * unit_conversion_factor
            
            if component == 'x':
                plot_data = data[:, 0]
            elif component == 'y':
                plot_data = data[:, 1]
            elif component == 'z':
                plot_data = data[:, 2]
            else:
                plot_data = np.sqrt(np.sum(data**2, axis=1))

            side = 'left' if label.startswith('L') else 'right'
            for start, end in gait_cycles.get(side, []):
                cycle_data = plot_data[start:end]
                x_norm = np.linspace(0, 100, len(cycle_data))
                interp_data = np.interp(np.linspace(0, 100, 101), x_norm, cycle_data)
                if side == 'left':
                    all_left_cycles_norm.append(interp_data)
                else:
                    all_right_cycles_norm.append(interp_data)

        x_axis_norm = np.linspace(0, 100, 101)
        if all_left_cycles_norm:
            mean_left = np.mean(all_left_cycles_norm, axis=0)
            std_left = np.std(all_left_cycles_norm, axis=0)
            ax.plot(x_axis_norm, mean_left, color='red', linewidth=2, label='Mean Left')
            ax.fill_between(x_axis_norm, mean_left - std_left, mean_left + std_left, color='red', alpha=0.2)
        
        if all_right_cycles_norm:
            mean_right = np.mean(all_right_cycles_norm, axis=0)
            std_right = np.std(all_right_cycles_norm, axis=0)
            ax.plot(x_axis_norm, mean_right, color='green', linewidth=2, label='Mean Right')
            ax.fill_between(x_axis_norm, mean_right - std_right, mean_right + std_right, color='green', alpha=0.2)

        ax.set_xlabel('Gait Cycle (%)')
        ax.set_ylabel(y_label)

        if current_frame is not None:
            for side in ['left', 'right']:
                for start, end in gait_cycles.get(side, []):
                    if start <= current_frame < end:
                        cycle_len = end - start
                        if cycle_len > 0:
                            percentage = (current_frame - start) / cycle_len * 100
                            ax.axvline(x=percentage, color='red', linestyle='--', linewidth=2)
                        break
