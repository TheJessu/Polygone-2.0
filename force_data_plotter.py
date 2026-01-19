from PyQt5.QtWidgets import QLabel
import numpy as np

class ForceDataPlotter:
    def __init__(self):
        self.lines = {}  # Store lines for picking

    def plot_forces(self, ax, markers_data, marker_labels, marker_types, current_frame, selected_group, angle_units):
        """Plot force data similar to angles - showing magnitude with L/R colors."""
        self.lines = {}

        # Get FORCES markers
        type_indices = [i for i, t in enumerate(marker_types) if t == 'FORCES']

        # Filter by selected group
        if selected_group != "All":
            filtered_indices = []
            for idx in type_indices:
                if idx < len(marker_labels) and marker_labels[idx]:
                    label = marker_labels[idx]
                    # Check if this marker belongs to the selected group
                    if label.startswith('L') or label.startswith('R'):
                        group = label[1:-len('FORCES')].lower().capitalize()
                        if group == selected_group:
                            filtered_indices.append(idx)
                    else:
                        group = label[:-len('FORCES')].lower().capitalize() if label.endswith('FORCES') else label.lower().capitalize()
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

            # Compute magnitude of the force vector
            magnitude_data = np.sqrt(x_data**2 + y_data**2 + z_data**2)

            # Only plot valid data (not NaN or all close to zero)
            valid_mask = ~(np.isnan(magnitude_data) | np.isclose(magnitude_data, 0))
            if np.any(valid_mask):
                # Set color: red for left (L), green for right (R)
                color = 'red' if label.startswith('L') else 'green'
                line, = ax.plot(frames[valid_mask], magnitude_data[valid_mask], label=f'{label}', linewidth=1, color=color, picker=5)
                self.lines[marker_idx] = (line, marker_idx, label, magnitude_data)

        # Add legend if there are multiple markers
        if len(type_indices) <= 5:  # Only show legend if not too many markers
            ax.legend(fontsize='small', loc='upper right')

        return self.lines

    def get_value_at_frame(self, marker_idx, frame):
        """Get the force magnitude value at a specific frame for display."""
        if marker_idx in self.lines:
            line, idx, label, magnitude_data = self.lines[marker_idx]
            if frame < len(magnitude_data):
                value = magnitude_data[frame]
                if not np.isnan(value):
                    return f"{label}: {value:.2f} N at frame {frame}"
                else:
                    return f"{label}: No data at frame {frame}"
        return ""
