import numpy as np

class GenericDataPlotter:
    def __init__(self, marker_type):
        self.marker_type = marker_type
        self.lines = {}  # Store lines for picking

        # Define units and conversions based on marker type
        self.units_config = {
            'ANGLES': {'unit': '°', 'conversion': lambda x: x},  # No conversion, display raw XYZ values
            'FORCES': {'unit': 'N', 'conversion': lambda x: x},
            'MOMENTS': {'unit': 'Nmm', 'conversion': lambda x: x * 1000},
            'POWERS': {'unit': 'W', 'conversion': lambda x: x}
        }

    def plot_data(self, ax, markers_data, marker_labels, marker_types, current_frame, selected_group, frame_range=None, angle_units='degrees', component='magnitude'):
        """Generic plot method for any marker type."""
        self.lines = {}

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

            # Rename labels for spine group
            if self.marker_type == 'ANGLES' and 'Spine' in label:
                if component == 'x':
                    label = 'Trunk Sway'
                elif component == 'y':
                    label = 'Trunk Tilt'
                elif component == 'z':
                    label = 'Trunk Rotation'

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
                    line, = ax.plot(x_values[valid_mask], sliced_plot_data[valid_mask], label=f'{label}', linewidth=1, color=color, picker=5)
                    self.lines[marker_idx] = (line, marker_idx, label, plot_data)  # Store full plot_data
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
                    self.lines[marker_idx] = (line, marker_idx, label, plot_data)

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
