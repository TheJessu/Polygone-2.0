import numpy as np
import math

class GenericDataPlotter:
    def __init__(self, marker_type):
        self.marker_type = marker_type
        self.lines = {}  # Store lines for picking, dict of key to (line, marker_idx, label, plot_data)

        # Define units and conversions based on marker type
        self.units_config = {
            'ANGLES': {'unit': '', 'conversion': lambda x: x},  # No conversion, display raw XYZ values
            'FORCES': {'unit': 'N', 'conversion': lambda x: x},
            'MOMENTS': {'unit': 'Nmm', 'conversion': lambda x: x * 1000},
            'POWERS': {'unit': 'W', 'conversion': lambda x: x}
        }

    @staticmethod
    def create_plot_grid(figure, num_plots, num_cols):
        """
        Clears the figure, calculates rows/cols, resizes the figure to fit
        square plots, and returns a list of axes.
        """
        figure.clear()
        if num_plots == 0:
            return []

        rows = int(math.ceil(num_plots / float(num_cols)))
        
        plot_size_inch = 4 
        fig_width = num_cols * plot_size_inch
        fig_height = rows * plot_size_inch
        figure.set_size_inches(fig_width, fig_height)

        axes = []
        for i in range(num_plots):
            ax = figure.add_subplot(rows, num_cols, i + 1)
            ax.set_box_aspect(1)
            axes.append(ax)

        return axes

    def plot_data(self, ax, markers_data, marker_labels, marker_types, current_frame, selected_group, frame_range=None, angle_units='degrees', component='magnitude', plot_widget=None):
        """Generic plot method for any marker type."""
        lines_dict = plot_widget.lines if plot_widget else self.lines

        # Get markers of the specified type
        type_indices = [i for i, t in enumerate(marker_types) if t == self.marker_type]

        # For ANGLES, sort markers with R before L
        if self.marker_type == 'ANGLES':
            type_indices.sort(key=lambda idx: (0 if marker_labels[idx].startswith('R') else 1, marker_labels[idx]))

        # Filter by selected group
        if selected_group != "All":
            filtered_indices = []
            for idx in type_indices:
                if idx < len(marker_labels) and marker_labels[idx]:
                    label = marker_labels[idx]
                    # Check if this marker belongs to the selected group
                    if label.startswith('L') or label.startswith('R'):
                        group = label[1:-len(self.marker_type)].lower().capitalize()
                        if group == selected_group:
                            filtered_indices.append(idx)
                    else:
                        group = label[:-len(self.marker_type)].lower().capitalize() if label.endswith(self.marker_type) else label.lower().capitalize()
                        if group == selected_group:
                            filtered_indices.append(idx)
            type_indices = filtered_indices

        # Plot data for each marker
        for marker_idx in type_indices:
            if marker_idx >= markers_data.shape[1]:
                continue

            # Get label
            label = marker_labels[marker_idx] if marker_idx < len(marker_labels) and marker_labels[marker_idx] else f'Marker {marker_idx+1}'

            # Plot x, y, z values over time
            frames = np.arange(markers_data.shape[0])
            x_data = markers_data[:, marker_idx, 0]
            y_data = markers_data[:, marker_idx, 1]
            z_data = markers_data[:, marker_idx, 2]

            # Apply unit conversion
            config = self.units_config[self.marker_type]
            x_data = config['conversion'](x_data)
            y_data = config['conversion'](y_data)
            z_data = config['conversion'](z_data)

            # Select component to plot
            if component == 'x':
                plot_data = x_data
            elif component == 'y':
                plot_data = y_data
            elif component == 'z':
                plot_data = z_data
            else:  # magnitude
                plot_data = np.sqrt(x_data**2 + y_data**2 + z_data**2)

            key = f"{marker_idx}_{component}"

            # Slice data to gait cycle range if provided
            if frame_range is not None:
                start_frame, end_frame = frame_range
                frame_mask = (frames >= start_frame) & (frames <= end_frame)
                sliced_frames = frames[frame_mask]
                sliced_plot_data = plot_data[frame_mask]

                # Use relative x-axis starting from 0, with tick labels as frame numbers
                x_values = np.arange(len(sliced_frames))
                valid_mask = ~(np.isnan(sliced_plot_data) | np.isclose(sliced_plot_data, 0))
                if np.any(valid_mask):
                    # Set color: red for left (L), green for right (R)
                    color = 'red' if label.startswith('L') else 'green'
                    line, = ax.plot(x_values[valid_mask], sliced_plot_data[valid_mask], label=f'{label}', linewidth=2, color=color, picker=20)
                    # Store in lines_dict
                    lines_dict[key] = (line, marker_idx, label, plot_data)
                    # Also store in self.lines for global access
                    self.lines[key] = (line, marker_idx, label, plot_data)
                    # Set tick labels to frame numbers
                    ax.set_xticks(x_values)
                    ax.set_xticklabels(sliced_frames.astype(int))
            else:
                # No slicing, plot all data
                valid_mask = ~(np.isnan(plot_data) | np.isclose(plot_data, 0))
                if np.any(valid_mask):
                    # Set color: red for left (L), green for right (R)
                    color = 'red' if label.startswith('L') else 'green'
                    line, = ax.plot(frames[valid_mask], plot_data[valid_mask], label=f'{label}', linewidth=1, color=color, picker=5)
                    # Store in lines_dict
                    lines_dict[key] = (line, marker_idx, label, plot_data)
                    # Also store in self.lines for global access
                    self.lines[key] = (line, marker_idx, label, plot_data)

        return self.lines

    def get_value_at_frame(self, marker_idx, frame):
        """Get the value at a specific frame for display."""
        if marker_idx in self.lines:
            line, idx, label, plot_data = self.lines[marker_idx]
            if frame < len(plot_data):
                value = plot_data[frame]
                if not np.isnan(value):
                    unit = self.units_config[self.marker_type]['unit']
                    return f"{label}: {value:.2f} {unit} at frame {frame}"
                else:
                    return f"{label}: No data at frame {frame}"
        return ""

    def highlight_line(self, key, highlight=True):
        """Highlight or unhighlight a line."""
        if key in self.lines:
            line, _, label, _ = self.lines[key]
            if highlight:
                line.set_linewidth(4)
                line.set_color('blue')
            else:
                # Reset to original color
                color = 'red' if label.startswith('L') else 'green'
                line.set_linewidth(2)
                line.set_color(color)

    def get_line_info(self, key, frame, gait_cycles=None):
        """Get detailed info for the line at the current frame, including gait cycle %."""
        if key not in self.lines:
            return ""
        line, idx, label, plot_data = self.lines[key]
        if frame >= len(plot_data):
            return f"{label}: No data at frame {frame}"
        value = plot_data[frame]
        if np.isnan(value):
            return f"{label}: No data at frame {frame}"
        unit = self.units_config[self.marker_type]['unit']
        info = f"{value:.2f} {unit} at frame {frame}"
        if gait_cycles:
            # Calculate gait cycle %
            gait_percent = self.calculate_gait_cycle_percent(frame, gait_cycles)
            if gait_percent is not None:
                info += f" and {gait_percent:.1f}%"
        return f"{label}: {info}"

    def calculate_gait_cycle_percent(self, frame, gait_cycles):
        """Calculate the gait cycle percentage for the given frame."""
        for side in ['left', 'right']:
            for start, end in gait_cycles.get(side, []):
                if start <= frame < end:
                    percent = ((frame - start) / (end - start)) * 100
                    return percent
        return None
