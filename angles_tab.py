from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import math
import numpy as np
from gait_cycle_plotter import GaitCyclePlotter
from generic_plotter import GenericDataPlotter

class PatchedFigureCanvas(FigureCanvas):
    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
        except ValueError as e:
            if "figure size must be positive finite" in str(e):
                # Skip the resize if it would cause negative size
                pass
            else:
                raise

class AnglesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.angles_plotter = GenericDataPlotter('ANGLES')
        self.gait_cycle_plotter = GaitCyclePlotter()
        self.gait_cycles = None
        self.frame_range = None

        # Create tab widget
        self.layout = QVBoxLayout(self)

        # Add dropdown for component selection
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Select Component:"))
        self.dropdown = QComboBox()
        self.dropdown.addItem("All")
        self.dropdown.currentTextChanged.connect(self.on_group_selected)
        dropdown_layout.addWidget(self.dropdown)
        dropdown_layout.addStretch()
        self.layout.addLayout(dropdown_layout)

        # Add buttons layout for group visibility
        self.buttons_layout = QVBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        # Create figure and canvas
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = PatchedFigureCanvas(self.figure)
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
        self.selected_line = None
        self.selected_data = None

        # Group visibility controls
        self.group_visibility = {}
        self.group_buttons = {}

        # New members for zoom
        self.zoomed_in_group = None
        self.ax_to_group = {}
        self.hovered_ax = None
        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None

        # Connect pick event
        self.canvas.mpl_connect('pick_event', self.on_line_pick)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)

    def resizeEvent(self, event):
        """Handle resize event to rearrange buttons."""
        super().resizeEvent(event)
        self.arrange_buttons()

    def arrange_buttons(self):
        """Arrange buttons in rows based on widget width."""
        if not self.group_buttons:
            return

        # Clear current layout
        for i in reversed(range(self.buttons_layout.count())):
            widget = self.buttons_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Calculate number of buttons per row
        button_width = 60  # Smaller button width
        spacing = 5
        available_width = self.width() - 20  # Account for margins
        buttons_per_row = max(1, available_width // (button_width + spacing))

        # Create rows
        button_list = list(self.group_buttons.values())
        for i in range(0, len(button_list), buttons_per_row):
            row_layout = QHBoxLayout()
            for j in range(buttons_per_row):
                if i + j < len(button_list):
                    button = button_list[i + j]
                    button.setFixedSize(button_width, 25)  # Smaller size
                    row_layout.addWidget(button)
            row_layout.addStretch()
            self.buttons_layout.addLayout(row_layout)

    def set_gait_cycles(self, gait_cycles):
        self.gait_cycles = gait_cycles

    def load_data(self, markers_data, marker_types, marker_labels):
        """Load marker data for this tab."""
        # Extract group names from labels
        type_indices = [i for i, t in enumerate(marker_types) if t == 'ANGLES']
        groups = set()
        for idx in type_indices:
            if idx < len(marker_labels) and marker_labels[idx]:
                label = marker_labels[idx]
                if label.startswith('L') or label.startswith('R'):
                    group = label[1:-len('ANGLES')].lower().capitalize()
                    groups.add(group)
                else:
                    group = label[:-len('ANGLES')].lower().capitalize() if label.endswith('ANGLES') else label.lower().capitalize()
                    groups.add(group)

        self.groups = sorted(list(groups))

        # Set dropdown to component options
        self.group_options = ["All", "X", "Y", "Z"]
        self.dropdown.clear()
        self.dropdown.addItems(self.group_options)

        # Remove group visibility buttons
        for button in self.group_buttons.values():
            button.setParent(None)
        self.group_buttons.clear()
        self.group_visibility.clear()

    def plot_data(self, markers_data, marker_types, marker_labels, current_frame, max_plots, frame_range=None):
        """Plot the angles data."""
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.current_frame = current_frame
        self.max_plots = max_plots
        self.frame_range = frame_range

        # Adjust current_frame for plotting if frame_range is provided
        plot_current_frame = current_frame
        if frame_range is not None:
            start_frame, end_frame = frame_range
            if not (start_frame <= current_frame <= end_frame):
                plot_current_frame = None  # Current frame is outside the range

        # Clear figure
        self.figure.clear()
        self.axes = []
        self.vlines = []
        self.ax_to_group = {}
        self.value_label.setText("")
        self.selected_line = None
        self.selected_data = None

        selected_component = self.dropdown.currentText()

        if self.gait_cycles and (self.gait_cycles['left'] or self.gait_cycles['right']):
            # Gait cycle plotting - need to handle differently, but for now, keep similar
            if self.zoomed_in_group:
                ax = self.figure.add_subplot(111)
                group = self.zoomed_in_group
                ax.set_title(f'ANGLES Data - {group} (Gait Cycle Normalized)')
                ax.set_ylabel('Angle (degrees)')
                self.axes.append(ax)
                self.gait_cycle_plotter.plot_gait_cycle_data(ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'ANGLES', 'Angle (degrees)', current_frame)
            elif selected_component != "All":
                ax = self.figure.add_subplot(111)
                ax.set_title(f'ANGLES Data - {selected_component} (Gait Cycle Normalized)')
                ax.set_ylabel('Angle (degrees)')
                self.axes.append(ax)
                self.gait_cycle_plotter.plot_gait_cycle_data(ax, markers_data, marker_labels, marker_types, selected_component, self.gait_cycles, 'ANGLES', 'Angle (degrees)', current_frame)
                self.ax_to_group[ax] = selected_component
            else:
                groups = self.groups
                num_plots = min(max_plots, len(groups))
                if num_plots > 0:
                    cols = int(math.ceil(math.sqrt(num_plots)))
                    rows = int(math.ceil(num_plots / float(cols)))
                    for i in range(num_plots):
                        group = groups[i]
                        ax = self.figure.add_subplot(rows, cols, i + 1)
                        ax.set_box_aspect(1)
                        ax.set_title(f'ANGLES Data - {group} (Gait Cycle Normalized)')
                        ax.set_ylabel('Angle (degrees)')
                        self.axes.append(ax)
                        self.ax_to_group[ax] = group
                        self.gait_cycle_plotter.plot_gait_cycle_data(ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'ANGLES', 'Angle (degrees)', current_frame)

        elif self.zoomed_in_group:
            ax = self.figure.add_subplot(111)
            group = self.zoomed_in_group
            ax.set_title(f'ANGLES Data - {group}')
            ax.set_xlabel('Frame')
            ax.set_ylabel('Angle (degrees)')
            ax.set_box_aspect(1)
            self.axes.append(ax)
            self.angles_plotter.plot_data(ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, 'degrees')
            if plot_current_frame is not None:
                vline = ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1)
                self.vlines.append(vline)

        elif selected_component == "All":
            # Plot all groups, each with 3 subplots (X, Y, Z)
            groups = self.groups
            num_groups = len(groups)
            if num_groups > 0:
                cols = 3  # X, Y, Z
                rows = num_groups
                for i, group in enumerate(groups):
                    for j, component in enumerate(['x', 'y', 'z']):
                        ax = self.figure.add_subplot(rows, cols, i * cols + j + 1)
                        ax.set_box_aspect(1)
                        title = f'{group} - {component.upper()}'
                        if group.lower() == 'spine':
                            if component == 'x':
                                title = f'{group} - Trunk Sway'
                            elif component == 'y':
                                title = f'{group} - Trunk Tilt'
                            elif component == 'z':
                                title = f'{group} - Trunk Rotation'
                        ax.set_title(title)
                        ax.set_xlabel('Frame')
                        ax.set_ylabel('Angle (degrees)')
                        self.axes.append(ax)
                        self.angles_plotter.plot_data(ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, 'degrees', component)
                        if plot_current_frame is not None:
                            vline = ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1, label='Current Frame')
                            self.vlines.append(vline)

        else:
            # Plot selected component (X, Y, Z) for all groups, one plot per group
            component = selected_component.lower()
            groups = self.groups
            num_plots = min(max_plots, len(groups))

            if num_plots > 0:
                cols = int(math.ceil(math.sqrt(num_plots)))
                rows = int(math.ceil(num_plots / float(cols)))

                for i in range(num_plots):
                    group = groups[i]
                    ax = self.figure.add_subplot(rows, cols, i + 1)
                    ax.set_box_aspect(1)
                    title = f'{group} - {selected_component}'
                    if group.lower() == 'spine':
                        if component == 'x':
                            title = f'{group} - Trunk Sway'
                        elif component == 'y':
                            title = f'{group} - Trunk Tilt'
                        elif component == 'z':
                            title = f'{group} - Trunk Rotation'
                    ax.set_title(title)
                    ax.set_xlabel('Frame')
                    ax.set_ylabel('Angle (degrees)')
                    self.axes.append(ax)
                    self.ax_to_group[ax] = group
                    self.angles_plotter.plot_data(ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, 'degrees', component)
                    if plot_current_frame is not None:
                        vline = ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1, label='Current Frame')
                        self.vlines.append(vline)

        import matplotlib.pyplot as plt
        self.figure.tight_layout()
        plt.subplots_adjust(hspace=0.4, wspace=0.4)
        self.canvas.draw()

    def on_group_selected(self, group_name):
        """Handle group selection change."""
        # Replot the data
        if self.markers_data is not None:
            self.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots, self.frame_range)

    def on_line_pick(self, event):
        """Handle line pick event."""
        # Reset previous selection
        if self.selected_line is not None:
            self.selected_line.set_linewidth(1)

        # Find the picked line
        for marker_idx, (line, idx, label, magnitude_data) in self.angles_plotter.lines.items():
            if event.artist == line:
                # Highlight the selected line
                line.set_linewidth(3)
                self.selected_line = line
                self.selected_data = (marker_idx, label, magnitude_data)
                self.update_selected_value(marker_idx)
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
            self.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots, self.frame_range)

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


    def update_selected_value(self):
        """Update the displayed value for the selected line at the current frame."""
        if self.selected_data is None:
            return

        marker_idx, label, magnitude_data = self.selected_data
        frame = int(self.current_frame)
        value_text = self.angles_plotter.get_value_at_frame(marker_idx, frame)
        if value_text:
            self.value_label.setText(value_text)
        else:
            self.value_label.setText(f"{label}: Frame {frame} out of range")

    def set_current_frame(self, frame_index):
        """Update the current frame indicator."""
        self.current_frame = frame_index

        # Adjust for frame_range if provided
        plot_frame = frame_index
        if self.frame_range is not None:
            start_frame, end_frame = self.frame_range
            if not (start_frame <= frame_index <= end_frame):
                plot_frame = None  # Outside range, hide vline

        for vline in self.vlines:
            if plot_frame is not None:
                vline.set_xdata([plot_frame, plot_frame])
                vline.set_visible(True)
            else:
                vline.set_visible(False)
        if self.canvas:
            self.canvas.draw_idle()

        # Update selected value display if a line is selected
        if self.selected_data is not None:
            self.update_selected_value(self.selected_data[0])

    def set_gait_info(self, info_text):
        """Set the gait info text."""
        self.gait_info_label.setText(info_text)

    def clear_highlight(self):
        """Clear all highlights."""
        for marker_idx, (line, idx, label, magnitude_data) in self.angles_plotter.lines.items():
            line.set_linewidth(1)
        self.selected_marker = None
        self.canvas.draw()

    def reset_highlight(self, marker_idx):
        """Reset highlight for a specific marker."""
        if marker_idx in self.angles_plotter.lines:
            line, idx, label, magnitude_data = self.angles_plotter.lines[marker_idx]
            line.set_linewidth(1)

    def set_highlight(self, marker_idx):
        """Set highlight for a specific marker."""
        if marker_idx in self.angles_plotter.lines:
            line, idx, label, magnitude_data = self.angles_plotter.lines[marker_idx]
            line.set_linewidth(3)
            self.selected_marker = marker_idx

    def update_selected_value(self, marker_idx):
        """Update the displayed value for the selected marker at the current frame."""
        if marker_idx in self.angles_plotter.lines:
            line, idx, label, magnitude_data = self.angles_plotter.lines[marker_idx]
            frame = int(self.current_frame)
            value_text = self.angles_plotter.get_value_at_frame(marker_idx, frame)
            if value_text:
                self.value_label.setText(value_text)
            else:
                self.value_label.setText(f"{label}: Frame {frame} out of range")

    def toggle_group_visibility(self, group):
        """Toggle visibility of a group."""
        self.group_visibility[group] = not self.group_visibility[group]
        button = self.group_buttons[group]
        button.setChecked(self.group_visibility[group])
        self.update_button_style(button, self.group_visibility[group])
        if self.markers_data is not None:
            self.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots, self.frame_range)

    def update_button_style(self, button, visible):
        """Update button style based on visibility."""
        if visible:
            button.setStyleSheet("QPushButton { background-color: white; color: black; }")
        else:
            button.setStyleSheet("QPushButton { background-color: grey; color: white; }")

    def clear_data(self):
        """Clear the plot data."""
        self.figure.clear()
        self.axes = []
        self.vlines = []
        self.value_label.setText("")
        self.gait_info_label.setText("")
        self.canvas.draw()
        self.angles_plotter.lines = {}
