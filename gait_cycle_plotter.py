from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import math
import numpy as np

class GaitCyclePlotter:
    def __init__(self):
        self.lines = {}

    def plot_gait_cycle_data(self, ax, markers_data, marker_labels, marker_types, selected_group, gait_cycles, plot_type, y_label, current_frame=None, unit_conversion_factor=1, component='magnitude', body_mass=None, plot_widget=None, side_filter="All"):
        if gait_cycles is None or not (gait_cycles.get('left') or gait_cycles.get('right')):
            # No gait cycles defined, set xlabel and ylabel but don't plot anything
            ax.set_xlabel('Gait Cycle (%)')
            ax.set_xlim(0, 100)
            return

        type_indices = [i for i, t in enumerate(marker_types) if t == plot_type]
        if selected_group != "All":
            filtered_indices = []
            name_map = {'Hi': 'Hip', 'Kne': 'Knee', 'Ankl': 'Ankle'}
            selected_group_mapped = name_map.get(selected_group, selected_group)
            for idx in type_indices:
                if idx < len(marker_labels) and marker_labels[idx]:
                    label = marker_labels[idx]
                    group = ""
                    if label.startswith('L') or label.startswith('R'):
                        group = label[1:-len(plot_type)].lower().capitalize()
                    else:
                        group = label[:-len(plot_type)].lower().capitalize() if label.endswith(plot_type) else label.lower().capitalize()

                    group = name_map.get(group, group)
                    if group == selected_group_mapped:
                        filtered_indices.append(idx)
            type_indices = filtered_indices

        all_left_cycles_norm, all_right_cycles_norm = [], []
        for marker_idx in type_indices:
            if marker_idx >= markers_data.shape[1]:
                continue
            
            label = marker_labels[marker_idx]
            data = markers_data[:, marker_idx, :]

            if plot_type == 'MOMENTS':
                data = data / 1000  # Convert Nmm to Nm
            data *= unit_conversion_factor
            
            if component == 'x':
                plot_data = data[:, 1]
            elif component == 'y':
                plot_data = data[:, 0]
            elif component == 'z':
                plot_data = data[:, 2]
            else:
                plot_data = np.sqrt(np.sum(data**2, axis=1))

            side = 'left' if label.startswith('L') else 'right'
            for start, end in gait_cycles.get(side, []):
                cycle_data = plot_data[start:end]
                if cycle_data.size == 0:
                    continue
                x_norm = np.linspace(0, 100, len(cycle_data))
                interp_data = np.interp(np.linspace(0, 100, 101), x_norm, cycle_data)
                if side == 'left':
                    all_left_cycles_norm.append(interp_data)
                else:
                    all_right_cycles_norm.append(interp_data)

        x_axis_norm = np.linspace(0, 100, 101)
        if (side_filter == "All" or side_filter == "Red") and all_left_cycles_norm:
            mean_left = np.mean(all_left_cycles_norm, axis=0)
            std_left = np.std(all_left_cycles_norm, axis=0)
            line, = ax.plot(x_axis_norm, mean_left, color='red', linewidth=2, label='Mean Left', picker=5)
            key = f'{selected_group}_{component}_mean_left'
            self.lines[key] = (line, key, 'Mean Left', mean_left)
            ax.fill_between(x_axis_norm, mean_left - std_left, mean_left + std_left, color='red', alpha=0.2)

        if (side_filter == "All" or side_filter == "Green") and all_right_cycles_norm:
            mean_right = np.mean(all_right_cycles_norm, axis=0)
            std_right = np.std(all_right_cycles_norm, axis=0)
            line, = ax.plot(x_axis_norm, mean_right, color='green', linewidth=2, label='Mean Right', picker=5)
            key = f'{selected_group}_{component}_mean_right'
            self.lines[key] = (line, key, 'Mean Right', mean_right)
            ax.fill_between(x_axis_norm, mean_right - std_right, mean_right + std_right, color='green', alpha=0.2)

        ax.set_xlabel('Gait Cycle (%)')
        ax.set_ylabel(y_label)
        ax.set_xlim(0, 100)
        ax.set_box_aspect(1)

        if plot_type == 'ANGLES':
            if component == 'x':
                if selected_group.lower() in ['spine', 'pelvis']:
                    ax.text(-0.05, 0.25, 'Down', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Up', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                elif selected_group.lower() in ['knee']:
                    ax.text(-0.05, 0.25, 'Val', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Var', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                else:  # hip, knee, footprogress
                    ax.text(-0.05, 0.25, 'Abd', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Add', transform=ax.transAxes, ha='right', va='center', fontsize=8)
            elif component == 'y':
                if selected_group.lower() in ['spine', 'pelvis']:
                    ax.text(-0.05, 0.25, 'Post', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Ant', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                elif selected_group.lower() in ['hip', 'knee']:
                    ax.text(-0.05, 0.25, 'Ext', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Flex', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                else:  # footprogress
                    ax.text(-0.05, 0.25, 'Plan', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Dors', transform=ax.transAxes, ha='right', va='center', fontsize=8)
            elif component == 'z':
                ax.text(-0.05, 0.25, 'Ext', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.75, 'Int', transform=ax.transAxes, ha='right', va='center', fontsize=8)

            # Set y-limits
            ymin, ymax = -1.0, 1.0  # Default
            if selected_group.lower() == 'spine':
                ymin, ymax = -20, 20
            elif selected_group.lower() == 'pelvis':
                if component == 'x':
                    ymin, ymax = -20, 20
                elif component == 'y':
                    ymin, ymax = -5, 35
                elif component == 'z':
                    ymin, ymax = -30, 30
            elif selected_group.lower() == 'hip':
                if component == 'x':
                    ymin, ymax = -15, 20
                elif component == 'y':
                    ymin, ymax = -15, 60
                elif component == 'z':
                    ymin, ymax = -30, 40
            elif selected_group.lower() == 'knee':
                ymin, ymax = -15, 90
            elif selected_group.lower() == 'footprogress':
                ymin, ymax = -40, 40
            elif selected_group.lower() == 'ankle':
                ymin, ymax = -50, 50
            ax.set_ylim(ymin, ymax)
            ax.set_yticks([ymin, ymax])
            # Always add a thick, darker grey line at y=0 if within range
            if ymin <= 0 <= ymax:
                ax.axhline(y=0, color='#555555', linestyle='-', linewidth=1.5, alpha=0.7)
            # Add horizontal grid lines at every 10 units in both directions from 0
            max_abs = max(abs(ymin), abs(ymax))
            for step in np.arange(10, max_abs + 10, 10):
                if ymin <= step <= ymax:
                    ax.axhline(y=step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
                if ymin <= -step <= ymax:
                    ax.axhline(y=-step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)

        elif plot_type == 'MOMENTS':
            # Labels and limits are handled in moments_tab.py to avoid duplication

            # Set y-limits
            ymin, ymax = -1.0, 1.0  # Default values
            if selected_group.lower() == 'hip':
                if component == 'x':
                    ymin, ymax = -1.0, 1.0
                elif component == 'y':
                    ymin, ymax = -1.0, 2.0
                elif component == 'z':
                    ymin, ymax = -0.5, 0.5
            elif selected_group.lower() == 'knee':
                if component == 'x':
                    ymin, ymax = -1.0, 1.0
                elif component == 'y':
                    ymin, ymax = -1.0, 2.0
                elif component == 'z':
                    ymin, ymax = -0.5, 0.5
            elif selected_group.lower() == 'ankle':
                if component == 'x':
                   ymin, ymax = -0.5, 0.5
                elif component == 'y':
                    ymin, ymax = -1.0, 2.0
                elif component == 'z':
                   ymin, ymax = -0.5, 0.5
            ax.set_ylim(ymin, ymax)
            ax.set_yticks([ymin, ymax])
            # Always add a thick, darker grey line at y=0 if within range
            if ymin <= 0 <= ymax:
                ax.axhline(y=0, color='#555555', linestyle='-', linewidth=1.5, alpha=0.7)
            # Add horizontal grid lines at every 0.5 units in both directions from 0
            max_abs = max(abs(ymin), abs(ymax))
            for step in np.arange(0.5, max_abs + 0.5, 0.5):
                if ymin <= step <= ymax:
                    ax.axhline(y=step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
                if ymin <= -step <= ymax:
                    ax.axhline(y=-step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)

        elif plot_type == 'POWERS':
            ax.set_ylabel('')  # Remove ylabel to avoid overlap with text labels
            if component == 'z':
                ax.text(-0.05, 0.25, 'Abs', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.50, 'W/kg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.75, 'Gen', transform=ax.transAxes, ha='right', va='center', fontsize=8)

            if component == 'z' and selected_group_mapped.lower() in ['hip', 'knee', 'ankle']:
                ymin, ymax = -2.0, 3.0
                ax.set_ylim(ymin, ymax)
                ax.set_yticks([ymin, ymax])

                if ymin <= 0 <= ymax:
                    ax.axhline(y=0, color='#555555', linestyle='-', linewidth=1.5, alpha=0.7, zorder=-1)

                max_abs = max(abs(ymin), abs(ymax))
                for step in np.arange(0.5, max_abs + 0.5, 0.5):
                    if ymin <= step <= ymax:
                        ax.axhline(y=step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5, zorder=-1)
                    if ymin <= -step <= ymax:
                        ax.axhline(y=-step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5, zorder=-1)

        if current_frame is not None:
            for side in ['left', 'right']:
                color = 'red' if side == 'left' else 'green'
                cycles = gait_cycles.get(side, [])
                percentage = 0
                for start, end in cycles:
                    if start <= current_frame < end:
                        cycle_len = end - start
                        if cycle_len > 0:
                            percentage = (current_frame - start) / cycle_len * 100
                        break
                
                scrubber = ax.axvline(x=percentage, color=color, linestyle='-', linewidth=1)
                if plot_widget and hasattr(plot_widget, 'scrubber_lines'):
                    plot_widget.scrubber_lines[side] = scrubber

    def highlight_line(self, line_key, highlight=True):
        """Highlight or unhighlight a line."""
        if line_key in self.lines:
            line, _, _, _ = self.lines[line_key]
            if highlight:
                line.set_linewidth(4)
                line.set_color('blue')
            else:
                # Reset to original color
                if 'mean_left' in line_key:
                    line.set_linewidth(2)
                    line.set_color('red')
                elif 'mean_right' in line_key:
                    line.set_linewidth(2)
                    line.set_color('green')

    def get_line_info(self, line_key, current_frame, gait_cycles, plot_type):
        """Get detailed info for the line at the current frame."""
        if line_key not in self.lines:
            return ""
        line, _, label, plot_data = self.lines[line_key]
        # Determine side from line_key
        if 'mean_left' in line_key:
            side = 'left'
        elif 'mean_right' in line_key:
            side = 'right'
        else:
            return f"{label}: Invalid line key"
        # Calculate current percentage only for the matching side
        percentage = None
        for start, end in gait_cycles.get(side, []):
            if start <= current_frame < end:
                cycle_len = end - start
                if cycle_len > 0:
                    percentage = (current_frame - start) / cycle_len * 100
                break
        if percentage is None:
            return f"{label}: No gait cycle data at frame {current_frame}"
        # Interpolate value at percentage
        x_axis_norm = np.linspace(0, 100, len(plot_data))
        value = np.interp(percentage, x_axis_norm, plot_data)
        unit = self.get_unit(plot_type)
        return f"{label}: {value:.2f} {unit} at frame {current_frame} and {percentage:.1f}%"

    def get_unit(self, plot_type):
        """Get unit for the plot type."""
        units = {
            'ANGLES': '',
            'FORCES': 'N',
            'MOMENTS': 'Nm/kg',
            'POWERS': 'W/kg'
        }
        return units.get(plot_type, '')
