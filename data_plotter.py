from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from force_data_plotter import ForceDataPlotter

class DataPlotter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Create tab widget for different plot types
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Initialize data
        self.markers_data = None
        self.marker_types = []
        self.marker_labels = []
        self.current_frame = 0
        self.angle_units = 'degrees'  # Default angle units
        self.selected_line = None  # Track the currently selected line
        self.selected_data = None  # Track the selected line's data (marker_idx, label, magnitude_data)
        self.selected_force_data = None  # Track the selected force line's data
        self.selected_force_line = None  # Track the currently selected force line
        self.selected_moment_data = None  # Track the selected moment line's data
        self.selected_moment_line = None  # Track the currently selected moment line
        self.selected_power_data = None  # Track the selected power line's data
        self.selected_power_line = None  # Track the currently selected power line

        # Initialize force data plotter
        self.force_plotter = ForceDataPlotter()

        # Plot types to display as tabs
        self.plot_types = ['ANGLES', 'FORCES', 'MOMENTS', 'POWERS']

        # Create tabs and canvases for each plot type
        self.canvases = {}
        self.figures = {}
        self.axes = {}
        self.vlines = {}
        self.dropdowns = {}
        self.group_options = {}
        self.value_labels = {}
        self.gait_info_labels = {}
        self.lines = {}

        for plot_type in self.plot_types:
            # Create figure and canvas for each tab
            figure = Figure(figsize=(8, 6), dpi=100)
            canvas = FigureCanvas(figure)

            # Create tab widget
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)

            # Add dropdown for group selection
            dropdown_layout = QHBoxLayout()
            dropdown_layout.addWidget(QLabel("Select Group:"))
            dropdown = QComboBox()
            dropdown.addItem("All")
            dropdown.currentTextChanged.connect(lambda text, pt=plot_type: self.on_group_selected(pt, text))
            dropdown_layout.addWidget(dropdown)
            dropdown_layout.addStretch()
            tab_layout.addLayout(dropdown_layout)

            tab_layout.addWidget(canvas)
            tab_widget.setLayout(tab_layout)

            self.tab_widget.addTab(tab_widget, plot_type)

            # Store references
            self.figures[plot_type] = figure
            self.canvases[plot_type] = canvas
            self.axes[plot_type] = []
            self.vlines[plot_type] = []
            self.dropdowns[plot_type] = dropdown
            self.group_options[plot_type] = ["All"]
            self.value_labels[plot_type] = QLabel("")
            self.lines[plot_type] = []

            # Add value label below the canvas
            tab_layout.addWidget(self.value_labels[plot_type])

            # Add gait info label below the value label
            self.gait_info_labels[plot_type] = QLabel("")
            self.gait_info_labels[plot_type].setWordWrap(True)
            tab_layout.addWidget(self.gait_info_labels[plot_type])

    def load_data(self, markers_data, marker_types, marker_labels, angle_units='degrees'):
        """Load marker data for plotting."""
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.angle_units = angle_units

        # Extract group names from labels for each plot type
        for plot_type in self.plot_types:
            type_indices = [i for i, t in enumerate(self.marker_types) if t == plot_type]
            groups = set()
            for idx in type_indices:
                if idx < len(self.marker_labels) and self.marker_labels[idx]:
                    label = self.marker_labels[idx]
                    # Extract group name (e.g., "Hip" from "LHipAngles" or "RHipAngles")
                    if label.startswith('L') or label.startswith('R'):
                        group = label[1:-len(plot_type)].lower()  # Remove L/R prefix and type suffix
                        groups.add(group.capitalize())
                    else:
                        # For labels without L/R prefix, use the full name minus type
                        group = label[:-len(plot_type)].lower() if label.endswith(plot_type) else label.lower()
                        groups.add(group.capitalize())

            self.group_options[plot_type] = ["All"] + sorted(list(groups))

            # Update dropdown
            dropdown = self.dropdowns[plot_type]
            dropdown.clear()
            dropdown.addItems(self.group_options[plot_type])

        self.plot_data()

    def plot_data(self, plot_type_filter=None):
        """Plot the marker data for each type in separate tabs."""
        if self.markers_data is None or len(self.marker_types) == 0:
            return

        # Clear all figures
        for plot_type in self.plot_types:
            self.figures[plot_type].clear()
            self.axes[plot_type] = []
            self.vlines[plot_type] = []
            self.lines[plot_type] = []
            self.value_labels[plot_type].setText("")
            if plot_type == 'ANGLES':
                self.selected_line = None
                self.selected_data = None
            elif plot_type == 'FORCES':
                self.selected_force_data = None
                self.selected_force_line = None
            elif plot_type == 'MOMENTS':
                self.selected_moment_data = None
                self.selected_moment_line = None
            elif plot_type == 'POWERS':
                self.selected_power_data = None
                self.selected_power_line = None

        for plot_type in self.plot_types:
            # Get markers of this type
            type_indices = [i for i, t in enumerate(self.marker_types) if t == plot_type]

            if not type_indices:
                continue

            # For ANGLES, sort markers with R before L
            if plot_type == 'ANGLES':
                type_indices.sort(key=lambda idx: (0 if self.marker_labels[idx].startswith('R') else 1, self.marker_labels[idx]))

            # Filter markers based on selected group
            selected_group = self.dropdowns[plot_type].currentText()
            if selected_group != "All":
                filtered_indices = []
                for idx in type_indices:
                    if idx < len(self.marker_labels) and self.marker_labels[idx]:
                        label = self.marker_labels[idx]
                        # Check if this marker belongs to the selected group
                        if label.startswith('L') or label.startswith('R'):
                            group = label[1:-len(plot_type)].lower().capitalize()
                            if group == selected_group:
                                filtered_indices.append(idx)
                        else:
                            group = label[:-len(plot_type)].lower().capitalize() if label.endswith(plot_type) else label.lower().capitalize()
                            if group == selected_group:
                                filtered_indices.append(idx)
                type_indices = filtered_indices

            if not type_indices:
                continue

            figure = self.figures[plot_type]
            canvas = self.canvases[plot_type]

            # Create subplot for this tab
            ax = figure.add_subplot(111)
            title = f'{plot_type} Data'
            if selected_group != "All":
                title += f' - {selected_group}'
            ax.set_title(title)
            ax.set_xlabel('Frame')
            if plot_type == 'ANGLES':
                ax.set_ylabel('Angle (degrees)')
            else:
                ax.set_ylabel('Value')
            self.axes[plot_type].append(ax)

            # Plot data for each marker in this type
            if plot_type == 'FORCES':
                # Use force plotter for FORCES tab
                self.force_plotter.plot_forces(ax, self.markers_data, self.marker_labels, self.marker_types, self.current_frame, selected_group, self.angle_units)
            else:
                for marker_idx in type_indices:
                    if marker_idx >= self.markers_data.shape[1]:
                        continue

                    # Get label
                    label = self.marker_labels[marker_idx] if marker_idx < len(self.marker_labels) and self.marker_labels[marker_idx] else f'Marker {marker_idx+1}'

                    # Plot x, y, z values over time
                    frames = np.arange(self.markers_data.shape[0])
                    x_data = self.markers_data[:, marker_idx, 0]
                    y_data = self.markers_data[:, marker_idx, 1]
                    z_data = self.markers_data[:, marker_idx, 2]

                    # Convert angles to degrees if necessary
                    if plot_type == 'ANGLES' and self.angle_units.lower() == 'radians':
                        x_data = np.degrees(x_data)
                        y_data = np.degrees(y_data)
                        z_data = np.degrees(z_data)

                    # For angles, moments, and powers, plot the magnitude (single line per marker) instead of x,y,z components
                    if plot_type == 'ANGLES':
                        # Compute magnitude of the angle vector
                        magnitude_data = np.sqrt(x_data**2 + y_data**2 + z_data**2)
                        # Only plot valid data (not NaN or all close to zero)
                        valid_mask = ~(np.isnan(magnitude_data) | np.isclose(magnitude_data, 0))
                        if np.any(valid_mask):
                            # Set color: red for left (L), green for right (R)
                            color = 'red' if label.startswith('L') else 'green'
                            line, = ax.plot(frames[valid_mask], magnitude_data[valid_mask], label=f'{label}', linewidth=1, color=color, picker=5)
                            self.lines[plot_type].append((line, marker_idx, label, magnitude_data))
                    elif plot_type == 'MOMENTS':
                        # Convert to Nmm (assuming data is in Nm, multiply by 1000)
                        x_data = x_data * 1000
                        y_data = y_data * 1000
                        z_data = z_data * 1000
                        # Compute magnitude of the moment vector
                        magnitude_data = np.sqrt(x_data**2 + y_data**2 + z_data**2)
                        # Only plot valid data (not NaN or all close to zero)
                        valid_mask = ~(np.isnan(magnitude_data) | np.isclose(magnitude_data, 0))
                        if np.any(valid_mask):
                            # Set color: red for left (L), green for right (R)
                            color = 'red' if label.startswith('L') else 'green'
                            line, = ax.plot(frames[valid_mask], magnitude_data[valid_mask], label=f'{label}', linewidth=1, color=color, picker=5)
                            self.lines[plot_type].append((line, marker_idx, label, magnitude_data))
                    elif plot_type == 'POWERS':
                        # Compute magnitude of the power vector (assuming data is in Watt)
                        magnitude_data = np.sqrt(x_data**2 + y_data**2 + z_data**2)
                        # Only plot valid data (not NaN or all close to zero)
                        valid_mask = ~(np.isnan(magnitude_data) | np.isclose(magnitude_data, 0))
                        if np.any(valid_mask):
                            # Set color: red for left (L), green for right (R)
                            color = 'red' if label.startswith('L') else 'green'
                            line, = ax.plot(frames[valid_mask], magnitude_data[valid_mask], label=f'{label}', linewidth=1, color=color, picker=5)
                            self.lines[plot_type].append((line, marker_idx, label, magnitude_data))
                    else:
                        # For other types, plot x, y, z separately
                        # Only plot valid data (not NaN or all close to zero)
                        valid_mask = ~(np.isnan(x_data) | np.isnan(y_data) | np.isnan(z_data) |
                                      (np.isclose(x_data, 0) & np.isclose(y_data, 0) & np.isclose(z_data, 0)))

                        if np.any(valid_mask):
                            ax.plot(frames[valid_mask], x_data[valid_mask], label=f'{label} X', linewidth=1)
                            ax.plot(frames[valid_mask], y_data[valid_mask], label=f'{label} Y', linewidth=1)
                            ax.plot(frames[valid_mask], z_data[valid_mask], label=f'{label} Z', linewidth=1)

            # Add legend if there are multiple markers
            if len(type_indices) <= 5:  # Only show legend if not too many markers
                ax.legend(fontsize='small', loc='upper right')

            # Add vertical line for current frame
            vline = ax.axvline(x=self.current_frame, color='red', linestyle='--', linewidth=1, label='Current Frame')
            self.vlines[plot_type].append(vline)

            figure.tight_layout()
            canvas.draw()

            # Connect pick event for ANGLES, FORCES, MOMENTS, and POWERS tabs
            if plot_type == 'ANGLES':
                canvas.mpl_connect('pick_event', lambda event, pt=plot_type: self.on_line_pick(event, pt))
            elif plot_type == 'FORCES':
                canvas.mpl_connect('pick_event', lambda event, pt=plot_type: self.on_force_line_pick(event, pt))
            elif plot_type == 'MOMENTS':
                canvas.mpl_connect('pick_event', lambda event, pt=plot_type: self.on_moment_line_pick(event, pt))
            elif plot_type == 'POWERS':
                canvas.mpl_connect('pick_event', lambda event, pt=plot_type: self.on_power_line_pick(event, pt))

    def on_group_selected(self, plot_type, group_name):
        """Handle group selection change."""
        self.plot_data()

    def set_current_frame(self, frame_index):
        """Update the current frame indicator."""
        self.current_frame = frame_index
        # Update vertical lines for current frame in all tabs
        for plot_type in self.plot_types:
            for vline in self.vlines[plot_type]:
                vline.set_xdata([frame_index, frame_index])
            if self.canvases[plot_type]:
                self.canvases[plot_type].draw_idle()

        # Update selected value display if a line is selected
        if self.selected_data is not None:
            self.update_selected_value()

        # Update force value display if a force line is selected
        if hasattr(self, 'selected_force_data') and self.selected_force_data is not None:
            self.update_selected_force_value()

        # Update moment value display if a moment line is selected
        if hasattr(self, 'selected_moment_data') and self.selected_moment_data is not None:
            self.update_selected_moment_value()

        # Update power value display if a power line is selected
        if hasattr(self, 'selected_power_data') and self.selected_power_data is not None:
            self.update_selected_power_value()

    def on_line_pick(self, event, plot_type):
        """Handle line pick event to display value at current frame and highlight selected line."""
        if plot_type != 'ANGLES':
            return

        # Reset previous selection
        if self.selected_line is not None:
            self.selected_line.set_linewidth(1)

        # Find the picked line
        for line, marker_idx, label, magnitude_data in self.lines[plot_type]:
            if event.artist == line:
                # Highlight the selected line
                line.set_linewidth(3)
                self.selected_line = line
                self.selected_data = (marker_idx, label, magnitude_data)

                # Update value display
                self.update_selected_value()
                break

        # Redraw the canvas to show the highlight
        self.canvases[plot_type].draw()

    def on_force_line_pick(self, event, plot_type):
        """Handle line pick event for FORCES tab to display value at current frame and highlight selected line."""
        if plot_type != 'FORCES':
            return

        # Reset previous selection
        if self.selected_force_line is not None:
            self.selected_force_line.set_linewidth(1)

        # Find the picked line in force plotter
        for marker_idx, (line, idx, label, magnitude_data) in self.force_plotter.lines.items():
            if event.artist == line:
                # Highlight the selected line
                line.set_linewidth(3)
                self.selected_force_line = line
                # Store selected force data
                self.selected_force_data = (marker_idx, label, magnitude_data)
                # Update value display for forces
                self.update_selected_force_value()
                break

        # Redraw the canvas to show the highlight
        self.canvases[plot_type].draw()

    def on_moment_line_pick(self, event, plot_type):
        """Handle line pick event for MOMENTS tab to display value at current frame and highlight selected line."""
        if plot_type != 'MOMENTS':
            return

        # Reset previous selection
        if self.selected_moment_line is not None:
            self.selected_moment_line.set_linewidth(1)

        # Find the picked line
        for line, marker_idx, label, magnitude_data in self.lines[plot_type]:
            if event.artist == line:
                # Highlight the selected line
                line.set_linewidth(3)
                self.selected_moment_line = line
                # Store selected moment data
                self.selected_moment_data = (marker_idx, label, magnitude_data)
                # Update value display for moments
                self.update_selected_moment_value()
                break

        # Redraw the canvas to show the highlight
        self.canvases[plot_type].draw()

    def on_power_line_pick(self, event, plot_type):
        """Handle line pick event for POWERS tab to display value at current frame and highlight selected line."""
        if plot_type != 'POWERS':
            return

        # Reset previous selection
        if self.selected_power_line is not None:
            self.selected_power_line.set_linewidth(1)

        # Find the picked line
        for line, marker_idx, label, magnitude_data in self.lines[plot_type]:
            if event.artist == line:
                # Highlight the selected line
                line.set_linewidth(3)
                self.selected_power_line = line
                # Store selected power data
                self.selected_power_data = (marker_idx, label, magnitude_data)
                # Update value display for powers
                self.update_selected_power_value()
                break

        # Redraw the canvas to show the highlight
        self.canvases[plot_type].draw()

    def update_selected_value(self):
        """Update the displayed value for the selected line at the current frame."""
        if self.selected_data is None:
            return

        marker_idx, label, magnitude_data = self.selected_data
        frame = int(self.current_frame)
        if frame < len(magnitude_data):
            value = magnitude_data[frame]
            if not np.isnan(value):
                self.value_labels['ANGLES'].setText(f"{label}: {value:.2f}° at frame {frame}")
            else:
                self.value_labels['ANGLES'].setText(f"{label}: No data at frame {frame}")
        else:
            self.value_labels['ANGLES'].setText(f"{label}: Frame {frame} out of range")

    def update_selected_force_value(self):
        """Update the displayed value for the selected force line at the current frame."""
        if self.selected_force_data is None:
            return

        marker_idx, label, magnitude_data = self.selected_force_data
        frame = int(self.current_frame)
        if frame < len(magnitude_data):
            value = magnitude_data[frame]
            if not np.isnan(value):
                self.value_labels['FORCES'].setText(f"{label}: {value:.2f} N at frame {frame}")
            else:
                self.value_labels['FORCES'].setText(f"{label}: No data at frame {frame}")
        else:
            self.value_labels['FORCES'].setText(f"{label}: Frame {frame} out of range")

    def update_selected_moment_value(self):
        """Update the displayed value for the selected moment line at the current frame."""
        if self.selected_moment_data is None:
            return

        marker_idx, label, magnitude_data = self.selected_moment_data
        frame = int(self.current_frame)
        if frame < len(magnitude_data):
            value = magnitude_data[frame]
            if not np.isnan(value):
                self.value_labels['MOMENTS'].setText(f"{label}: {value:.2f} Nmm at frame {frame}")
            else:
                self.value_labels['MOMENTS'].setText(f"{label}: No data at frame {frame}")
        else:
            self.value_labels['MOMENTS'].setText(f"{label}: Frame {frame} out of range")

    def update_selected_power_value(self):
        """Update the displayed value for the selected power line at the current frame."""
        if self.selected_power_data is None:
            return

        marker_idx, label, magnitude_data = self.selected_power_data
        frame = int(self.current_frame)
        if frame < len(magnitude_data):
            value = magnitude_data[frame]
            if not np.isnan(value):
                self.value_labels['POWERS'].setText(f"{label}: {value:.2f} W at frame {frame}")
            else:
                self.value_labels['POWERS'].setText(f"{label}: No data at frame {frame}")
        else:
            self.value_labels['POWERS'].setText(f"{label}: Frame {frame} out of range")

    def set_gait_info(self, events_data):
        """Set the gait info for display in all tabs."""
        if not events_data:
            for plot_type in self.plot_types:
                self.gait_info_labels[plot_type].setText("")
            return

        # Categorize events similar to the original infobox logic
        left_strikes = sorted([e['time'] for e in events_data if e.get('foot') == 'left' and e.get('type') == 'strike'])
        right_strikes = sorted([e['time'] for e in events_data if e.get('foot') == 'right' and e.get('type') == 'strike'])

        left_cycle_start = left_cycle_end = -1
        if len(left_strikes) >= 2:
            left_cycle_start, left_cycle_end = left_strikes[0], left_strikes[1]

        right_cycle_start = right_cycle_end = -1
        if len(right_strikes) >= 2:
            right_cycle_start, right_cycle_end = right_strikes[0], right_strikes[1]

        # Categorize all events
        left_cycle_events = []
        right_cycle_events = []
        other_events = []

        for event in events_data:
            t = event['time']
            frame = int(t * 100)  # Assuming frame_rate = 100 Hz
            event_str = f"  {event.get('foot', 'N/A').capitalize()} {event.get('type', 'N/A').capitalize()}: Frame {frame}"

            if left_cycle_start != -1 and left_cycle_start <= t <= left_cycle_end:
                left_cycle_events.append(event_str)
            elif right_cycle_start != -1 and right_cycle_start <= t <= right_cycle_end:
                right_cycle_events.append(event_str)
            else:
                other_events.append(event_str)

        # Format text
        info_text = "<b>Left Cycle Events:</b>\n" + ("\n".join(sorted(left_cycle_events)) or "  None")
        info_text += "\n\n<b>Right Cycle Events:</b>\n" + ("\n".join(sorted(right_cycle_events)) or "  None")
        info_text += "\n\n<b>Other Events:</b>\n" + ("\n".join(sorted(other_events)) or "  None")

        # Set the same text for all tabs
        for plot_type in self.plot_types:
            self.gait_info_labels[plot_type].setText(info_text)

    def clear_data(self):
        """Clear the plot data."""
        self.markers_data = None
        self.marker_types = []
        self.marker_labels = []
        self.selected_line = None
        self.selected_data = None
        self.selected_force_data = None
        self.selected_force_line = None
        self.selected_moment_data = None
        self.selected_moment_line = None
        self.selected_power_data = None
        self.selected_power_line = None
        # Clear all figures and reset data structures
        for plot_type in self.plot_types:
            self.figures[plot_type].clear()
            self.axes[plot_type] = []
            self.vlines[plot_type] = []
            self.lines[plot_type] = []
            self.value_labels[plot_type].setText("")
            self.gait_info_labels[plot_type].setText("")
            self.canvases[plot_type].draw()
