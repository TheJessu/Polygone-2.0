from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import math
import numpy as np

class PowersDataPlotter:
    def __init__(self):
        self.lines = {}  # Store lines for picking

    def plot_powers(self, ax, markers_data, marker_labels, marker_types, current_frame, selected_group):
        """Plot power data - showing magnitude with L/R colors."""
        self.lines = {}

        # Get POWERS markers
        type_indices = [i for i, t in enumerate(marker_types) if t == 'POWERS']

        # Filter by selected group
        if selected_group != "All":
            filtered_indices = []
            for idx in type_indices:
                if idx < len(marker_labels) and marker_labels[idx]:
                    label = marker_labels[idx]
                    # Check if this marker belongs to the selected group
                    if label.startswith('L') or label.startswith('R'):
                        group = label[1:-len('POWERS')].lower().capitalize()
                        if group == selected_group:
                            filtered_indices.append(idx)
                    else:
                        group = label[:-len('POWERS')].lower().capitalize() if label.endswith('POWERS') else label.lower().capitalize()
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

            # Compute magnitude of the power vector (assuming data is in Watt)
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
        """Get the power magnitude value at a specific frame for display."""
        if marker_idx in self.lines:
            line, idx, label, magnitude_data = self.lines[marker_idx]
            if frame < len(magnitude_data):
                value = magnitude_data[frame]
                if not np.isnan(value):
                    return f"{label}: {value:.2f} W at frame {frame}"
                else:
                    return f"{label}: No data at frame {frame}"
        return ""

class PowersTab:
    def __init__(self):
        self.powers_plotter = PowersDataPlotter()

        # Create tab widget
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)

        # Add dropdown for group selection
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Select Group:"))
        self.dropdown = QComboBox()
        self.dropdown.addItem("All")
        self.dropdown.currentTextChanged.connect(self.on_group_selected)
        dropdown_layout.addWidget(self.dropdown)
        dropdown_layout.addStretch()
        self.layout.addLayout(dropdown_layout)

        # Create figure and canvas
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, 1)

        # Add value label below the canvas
        self.value_label = QLabel("")
        self.layout.addWidget(self.value_label)

        # Add gait info label below the value label
        self.gait_info_label = QLabel("")
        self.gait_info_label.setWordWrap(True)
        self.layout.addWidget(self.gait_info_label)

        # Initialize data structures
        self.axes = []
        self.vlines = []
        self.group_options = ["All"]
        self.current_frame = 0
        self.max_plots = 4
        self.selected_power_line = None
        self.selected_power_data = None

        # New members for zoom
        self.zoomed_in_group = None
        self.ax_to_group = {}
        self.hovered_ax = None
        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None

        # Connect pick event
        self.canvas.mpl_connect('pick_event', self.on_power_line_pick)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)

    def load_data(self, markers_data, marker_types, marker_labels):
        """Load marker data for this tab."""
        # Extract group names from labels
        type_indices = [i for i, t in enumerate(marker_types) if t == 'POWERS']
        groups = set()
        for idx in type_indices:
            if idx < len(marker_labels) and marker_labels[idx]:
                label = marker_labels[idx]
                if label.startswith('L') or label.startswith('R'):
                    group = label[1:-len('POWERS')].lower().capitalize()
                    groups.add(group)
                else:
                    group = label[:-len('POWERS')].lower().capitalize() if label.endswith('POWERS') else label.lower().capitalize()
                    groups.add(group)

        self.group_options = ["All"] + sorted(list(groups))
        self.dropdown.clear()
        self.dropdown.addItems(self.group_options)

    def plot_data(self, markers_data, marker_types, marker_labels, current_frame, max_plots):
        """Plot the powers data."""
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.current_frame = current_frame
        self.max_plots = max_plots

        # Clear figure
        self.figure.clear()
        self.axes = []
        self.vlines = []
        self.ax_to_group = {}
        self.value_label.setText("")
        self.selected_power_line = None
        self.selected_power_data = None

        selected_group = self.dropdown.currentText()

        if self.zoomed_in_group:
            ax = self.figure.add_subplot(111)
            group = self.zoomed_in_group
            ax.set_title(f'POWERS Data - {group}')
            ax.set_xlabel('Frame')
            ax.set_ylabel('Value')
            ax.set_box_aspect(1)
            self.axes.append(ax)
            self.powers_plotter.plot_powers(ax, markers_data, marker_labels, marker_types, current_frame, group)
            vline = ax.axvline(x=current_frame, color='red', linestyle='--', linewidth=1)
            self.vlines.append(vline)

        elif selected_group != "All":
            # Plot only the selected group
            ax = self.figure.add_subplot(111)
            ax.set_title(f'POWERS Data - {selected_group}')
            ax.set_xlabel('Frame')
            ax.set_ylabel('Value')
            ax.set_box_aspect(1)
            self.axes.append(ax)
            self.powers_plotter.plot_powers(ax, markers_data, marker_labels, marker_types, current_frame, selected_group)
            vline = ax.axvline(x=current_frame, color='red', linestyle='--', linewidth=1, label='Current Frame')
            self.vlines.append(vline)
            self.ax_to_group[ax] = selected_group

        else:
            # Plot multiple groups based on max_plots
            groups = [g for g in self.group_options if g != "All"]
            num_plots = min(max_plots, len(groups))

            if num_plots > 0:
                cols = int(math.ceil(math.sqrt(num_plots)))
                rows = int(math.ceil(num_plots / float(cols)))

                for i in range(num_plots):
                    group = groups[i]
                    ax = self.figure.add_subplot(rows, cols, i + 1)
                    ax.set_box_aspect(1)
                    ax.set_title(f'POWERS Data - {group}')
                    ax.set_xlabel('Frame')
                    ax.set_ylabel('Value')
                    self.axes.append(ax)
                    self.ax_to_group[ax] = group
                    self.powers_plotter.plot_powers(ax, markers_data, marker_labels, marker_types, current_frame, group)
                    vline = ax.axvline(x=current_frame, color='red', linestyle='--', linewidth=1, label='Current Frame')
                    self.vlines.append(vline)

        self.figure.tight_layout()
        self.canvas.draw()

    def on_group_selected(self, group_name):
        """Handle group selection change."""
        # This will be called by parent to replot
        pass

    def on_power_line_pick(self, event):
        """Handle line pick event for powers."""
        # Reset previous selection
        if self.selected_power_line is not None:
            self.selected_power_line.set_linewidth(1)

        # Find the picked line
        for marker_idx, (line, idx, label, magnitude_data) in self.powers_plotter.lines.items():
            if event.artist == line:
                # Highlight the selected line
                line.set_linewidth(3)
                self.selected_power_line = line
                self.selected_power_data = (marker_idx, label, magnitude_data)
                self.update_selected_power_value()
                break

        # Redraw the canvas
        self.canvas.draw()

    def on_button_press(self, event):
        if not event.dblclick:
            return

        if self.zoomed_in_group is None:
            if event.inaxes in self.ax_to_group:
                self.zoomed_in_group = self.ax_to_group[event.inaxes]
        else:
            self.zoomed_in_group = None

        if self.markers_data is not None:
            self.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots)

    def on_hover(self, event):
        ax = event.inaxes
        if ax != self.hovered_ax:
            if self.hovered_ax is not None:
                self.hovered_ax.patch.set_edgecolor('none')
                self.hovered_ax.patch.set_linewidth(0)

            self.hovered_ax = ax

            if self.hovered_ax is not None and self.hovered_ax in self.axes:
                self.hovered_ax.patch.set_edgecolor('grey')
                self.hovered_ax.patch.set_linewidth(2)

            self.canvas.draw_idle()


    def update_selected_power_value(self):
        """Update the displayed value for the selected power line at the current frame."""
        if self.selected_power_data is None:
            return

        marker_idx, label, magnitude_data = self.selected_power_data
        frame = int(self.current_frame)
        if frame < len(magnitude_data):
            value = magnitude_data[frame]
            if not np.isnan(value):
                self.value_label.setText(f"{label}: {value:.2f} W at frame {frame}")
            else:
                self.value_label.setText(f"{label}: No data at frame {frame}")
        else:
            self.value_label.setText(f"{label}: Frame {frame} out of range")

    def set_current_frame(self, frame_index):
        """Update the current frame indicator."""
        self.current_frame = frame_index
        for vline in self.vlines:
            vline.set_xdata([frame_index, frame_index])
        if self.canvas:
            self.canvas.draw_idle()

        # Update selected value display if a line is selected
        if self.selected_power_data is not None:
            self.update_selected_power_value()

    def set_gait_info(self, info_text):
        """Set the gait info text."""
        self.gait_info_label.setText(info_text)

    def clear_data(self):
        """Clear the plot data."""
        self.figure.clear()
        self.axes = []
        self.vlines = []
        self.value_label.setText("")
        self.gait_info_label.setText("")
        self.canvas.draw()
        self.powers_plotter.lines = {}
