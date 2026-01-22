from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel, QSpinBox

from angles_tab import AnglesTab, AnglesDataPlotter
from forces_tab import ForcesTab
from moments_tab import MomentsTab, MomentsDataPlotter
from powers_tab import PowersTab

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

        # Initialize angles data plotter
        self.angles_plotter = AnglesDataPlotter()

        # Initialize moments data plotter
        self.moments_plotter = MomentsDataPlotter()



        # Plot types to display as tabs
        self.plot_types = ['ANGLES', 'FORCES', 'MOMENTS', 'POWERS']

        # Initialize tabs
        self.tabs = {
            'ANGLES': AnglesTab(),
            'FORCES': ForcesTab(),
            'MOMENTS': MomentsTab(self.moments_plotter),
            'POWERS': PowersTab()
        }

        # Maximum number of plots to display
        self.max_plots = 4

        # Add spinbox for max plots
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
            # Add tab widget to the tab widget
            self.tab_widget.addTab(self.tabs[plot_type].widget, plot_type)

    def load_data(self, markers_data, marker_types, marker_labels, angle_units='degrees'):
        """Load marker data for plotting."""
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.angle_units = angle_units

        # Load data for each tab
        for plot_type in self.plot_types:
            self.tabs[plot_type].load_data(markers_data, marker_types, marker_labels)

        self.plot_data()

    def plot_data(self, plot_type_filter=None):
        """Plot the marker data for each type in separate tabs."""
        if self.markers_data is None or len(self.marker_types) == 0:
            return

        # Plot data for each tab
        for plot_type in self.plot_types:
            self.tabs[plot_type].plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots)

    def on_group_selected(self, plot_type, group_name):
        """Handle group selection change."""
        self.plot_data()

    def on_max_plots_changed(self, value):
        """Handle max plots change."""
        self.max_plots = value
        self.plot_data()

    def set_current_frame(self, frame_index):
        """Update the current frame indicator."""
        self.current_frame = frame_index
        # Update current frame for all tabs
        for plot_type in self.plot_types:
            self.tabs[plot_type].set_current_frame(frame_index)

    def on_line_pick(self, event, plot_type):
        """Handle line pick event to display value at current frame and highlight selected line."""
        if plot_type != 'ANGLES':
            return

        # Reset previous selection
        if self.selected_line is not None:
            self.selected_line.set_linewidth(1)

        # Find the picked line in angles plotter
        for marker_idx, (line, idx, label, magnitude_data) in self.angles_plotter.lines.items():
            if event.artist == line:
                # Highlight the selected line
                line.set_linewidth(3)
                self.selected_line = line
                # Store selected angle data
                self.selected_data = (marker_idx, label, magnitude_data)
                # Update value display for angles
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
        for marker_idx, (line, idx, label, magnitude_data) in self.tabs['FORCES'].lines.items():
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

        # Find the picked line in moments plotter
        for marker_idx, (line, idx, label, magnitude_data) in self.moments_plotter.lines.items():
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

        # Find the picked line in powers plotter
        for marker_idx, (line, idx, label, magnitude_data) in self.tabs['POWERS'].powers_plotter.lines.items():
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
        # Use angles plotter's get_value_at_frame method
        value_text = self.angles_plotter.get_value_at_frame(marker_idx, frame)
        if value_text:
            self.value_labels['ANGLES'].setText(value_text)
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
        # Use moments plotter's get_value_at_frame method
        value_text = self.moments_plotter.get_value_at_frame(marker_idx, frame)
        if value_text:
            self.value_labels['MOMENTS'].setText(value_text)
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
                self.tabs[plot_type].set_gait_info("")
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
            self.tabs[plot_type].set_gait_info(info_text)

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
        # Clear plotter lines
        self.angles_plotter.lines = {}
        self.moments_plotter.lines = {}
        self.tabs['FORCES'].lines = {}
        # Clear all tabs
        for plot_type in self.plot_types:
            self.tabs[plot_type].clear_data()
