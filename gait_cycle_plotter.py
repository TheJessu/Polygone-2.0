from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import math
import numpy as np

class GaitCyclePlotter:
    def __init__(self):
        self.lines = {}

    def plot_gait_cycle_data(self, ax, markers_data, marker_labels, marker_types, selected_group, gait_cycles, plot_type, y_label, current_frame=None, unit_conversion_factor=1, angle_units='degrees'):
        """Plot data normalized over gait cycles."""

        type_indices = [i for i, t in enumerate(marker_types) if t == plot_type]
        if selected_group != "All":
            filtered_indices = []
            for idx in type_indices:
                if idx < len(marker_labels) and marker_labels[idx]:
                    label = marker_labels[idx]
                    suffix = plot_type
                    if label.startswith('L') or label.startswith('R'):
                        group = label[1:-len(suffix)].lower().capitalize()
                        if group == selected_group:
                            filtered_indices.append(idx)
                    else:
                        group = label[:-len(suffix)].lower().capitalize() if label.endswith(suffix) else label.lower().capitalize()
                        if group == selected_group:
                            filtered_indices.append(idx)
            type_indices = filtered_indices

        all_left_cycles_norm = []
        all_right_cycles_norm = []

        for marker_idx in type_indices:
            if marker_idx >= markers_data.shape[1]:
                continue

            label = marker_labels[marker_idx] if marker_idx < len(marker_labels) and marker_labels[marker_idx] else f'Marker {marker_idx+1}'
            x_data = markers_data[:, marker_idx, 0] * unit_conversion_factor
            y_data = markers_data[:, marker_idx, 1] * unit_conversion_factor
            z_data = markers_data[:, marker_idx, 2] * unit_conversion_factor

            # Convert angles to degrees if necessary
            if plot_type == 'ANGLES' and angle_units.lower() == 'radians':
                x_data = np.degrees(x_data)
                y_data = np.degrees(y_data)
                z_data = np.degrees(z_data)

            magnitude_data = np.sqrt(x_data**2 + y_data**2 + z_data**2)

            side = 'left' if label.startswith('L') else 'right'
            cycles = gait_cycles.get(side, [])

            for start_frame, end_frame in cycles:
                cycle_data = magnitude_data[start_frame:end_frame]

                # Normalize time to 0-100
                x_norm = np.linspace(0, 100, len(cycle_data))

                # Store normalized data for mean/std calculation
                if side == 'left':
                    all_left_cycles_norm.append(np.interp(np.linspace(0, 100, 101), x_norm, cycle_data))
                else:
                    all_right_cycles_norm.append(np.interp(np.linspace(0, 100, 101), x_norm, cycle_data))

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

        # Add marker for current frame position in gait cycle
        if current_frame is not None:
            # Find which gait cycle the current frame belongs to
            for side in ['left', 'right']:
                cycles = gait_cycles.get(side, [])
                for start_frame, end_frame in cycles:
                    if start_frame <= current_frame <= end_frame:
                        # Calculate percentage within the cycle
                        cycle_length = end_frame - start_frame
                        if cycle_length > 0:
                            percentage = ((current_frame - start_frame) / cycle_length) * 100
                            ax.axvline(x=percentage, color='red', linestyle='--', linewidth=2, label='Current Position')
                        break
