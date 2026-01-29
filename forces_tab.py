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

class ForcesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.forces_plotter = GenericDataPlotter('FORCES')
        self.gait_cycle_plotter = GaitCyclePlotter()
        self.lines = {}
        self.gait_cycles = None
        self.frame_range = None

        self.layout = QVBoxLayout(self)

        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Select Group:"))
        self.group_dropdown = QComboBox()
        self.group_dropdown.addItem("All")
        self.group_dropdown.currentTextChanged.connect(self.on_selection_changed)
        dropdown_layout.addWidget(self.group_dropdown)

        dropdown_layout.addWidget(QLabel("Select Component:"))
        self.component_dropdown = QComboBox()
        self.component_dropdown.addItems(["All", "X", "Y", "Z"])
        self.component_dropdown.currentTextChanged.connect(self.on_selection_changed)
        dropdown_layout.addWidget(self.component_dropdown)
        dropdown_layout.addStretch()
        self.layout.addLayout(dropdown_layout)

        self.buttons_layout = QVBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = PatchedFigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, 1)

        self.value_label = QLabel("")
        self.layout.addWidget(self.value_label)

        self.gait_info_label = QLabel("")
        self.gait_info_label.setWordWrap(True)
        self.layout.addWidget(self.gait_info_label)

        self.axes = []
        self.vlines = []
        self.groups = []
        self.current_frame = 0
        self.max_plots = 4
        self.selected_line = None
        self.selected_data = None

        self.group_visibility = {}
        self.group_buttons = {}

        self.zoomed_in_group = None
        self.ax_to_group = {}
        self.hovered_ax = None
        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None

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
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels

        type_indices = [i for i, t in enumerate(marker_types) if t == 'FORCES']
        groups = set()
        for idx in type_indices:
            if idx < len(marker_labels) and marker_labels[idx]:
                label = marker_labels[idx]
                if label.startswith('L') or label.startswith('R'):
                    group = label[1:-len('FORCES')].lower().capitalize()
                    groups.add(group)
                else:
                    group = label[:-len('FORCES')].lower().capitalize() if label.endswith('FORCES') else label.lower().capitalize()
                    groups.add(group)

        self.groups = ["All"] + sorted(list(groups))
        self.group_dropdown.clear()
        self.group_dropdown.addItems(self.groups)

        for button in self.group_buttons.values():
            button.setParent(None)
        self.group_buttons.clear()
        self.group_visibility.clear()

        for group in sorted(list(groups)):
            button = QPushButton(group)
            button.setCheckable(True)
            button.setChecked(True)
            button.clicked.connect(lambda checked, g=group: self.toggle_group_visibility(g))
            self.group_buttons[group] = button
            self.group_visibility[group] = True
            self.update_button_style(button, True)

        self.arrange_buttons()

    def plot_data(self, markers_data, marker_types, marker_labels, current_frame, max_plots, frame_range=None):
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.current_frame = current_frame
        self.max_plots = max_plots
        self.frame_range = frame_range

        plot_current_frame = current_frame
        if frame_range and not (frame_range[0] <= current_frame <= frame_range[1]):
            plot_current_frame = None

        self.figure.clear()
        self.axes, self.vlines, self.ax_to_group = [], [], {}
        self.value_label.setText("")
        self.selected_line, self.selected_data = None, None

        selected_group = self.group_dropdown.currentText()
        selected_component = self.component_dropdown.currentText()
        
        groups = [g for g in self.groups if g != "All" and self.group_visibility.get(g, True)]
        if selected_group != "All":
            groups = [selected_group]

        use_gait_cycle = self.gait_cycles and (self.gait_cycles['left'] or self.gait_cycles['right'])

        if self.zoomed_in_group:
            ax = self.figure.add_subplot(111)
            group = self.zoomed_in_group
            ax.set_title(f'FORCES Data - {group}')
            ax.set_xlabel('Frame' if not use_gait_cycle else 'Gait Cycle (%)')
            ax.set_ylabel('Force (N)')
            ax.set_box_aspect(1)
            self.axes.append(ax)
            if use_gait_cycle:
                self.gait_cycle_plotter.plot_gait_cycle_data(ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'FORCES', 'Force (N)', current_frame)
            else:
                self.forces_plotter.plot_data(ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range)
                if plot_current_frame is not None:
                    self.vlines.append(ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1))

        elif selected_component == "All":
            if groups:
                rows, cols = len(groups), 3
                for i, group in enumerate(groups):
                    for j, component in enumerate(['x', 'y', 'z']):
                        ax = self.figure.add_subplot(rows, cols, i * cols + j + 1)
                        ax.set_title(f'{group} - {component.upper()}')
                        ax.set_xlabel('Frame' if not use_gait_cycle else 'Gait Cycle (%)')
                        ax.set_ylabel('Force (N)')
                        self.axes.append(ax)
                        self.ax_to_group[ax] = group
                        if use_gait_cycle:
                            self.gait_cycle_plotter.plot_gait_cycle_data(ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'FORCES', 'Force (N)', current_frame, component=component)
                        else:
                            self.forces_plotter.plot_data(ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, component=component)
                            if plot_current_frame is not None:
                                self.vlines.append(ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1))
        
        else:
            if groups:
                component = selected_component.lower()
                rows, cols = int(math.ceil(len(groups) / 3)), 3
                for i, group in enumerate(groups):
                    ax = self.figure.add_subplot(rows, cols, i + 1)
                    ax.set_title(f'{group} - {selected_component}')
                    ax.set_xlabel('Frame' if not use_gait_cycle else 'Gait Cycle (%)')
                    ax.set_ylabel('Force (N)')
                    self.axes.append(ax)
                    self.ax_to_group[ax] = group
                    if use_gait_cycle:
                        self.gait_cycle_plotter.plot_gait_cycle_data(ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'FORCES', 'Force (N)', current_frame, component=component)
                    else:
                        self.forces_plotter.plot_data(ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, component=component)
                        if plot_current_frame is not None:
                            self.vlines.append(ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1))

        self.figure.tight_layout()
        self.canvas.draw()



    def on_selection_changed(self, value):
        if self.markers_data is not None:
            self.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots, self.frame_range)

    def on_line_pick(self, event):
        if self.selected_line:
            self.selected_line.set_linewidth(1)

        lines = self.forces_plotter.lines if not (self.gait_cycles and (self.gait_cycles['left'] or self.gait_cycles['right'])) else self.gait_cycle_plotter.lines
        
        for marker_idx, (line, idx, label, magnitude_data) in lines.items():
            if event.artist == line:
                line.set_linewidth(3)
                self.selected_line = line
                self.selected_data = (marker_idx, label, magnitude_data)
                self.update_selected_value()
                break
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
            if self.hovered_ax:
                self.hovered_ax.patch.set_edgecolor('none')
                self.hovered_ax.patch.set_linewidth(0)

            self.hovered_ax = ax

            if self.hovered_ax and self.hovered_ax in self.axes:
                self.hovered_ax.patch.set_edgecolor('grey')
                self.hovered_ax.patch.set_linewidth(2)

            self.canvas.draw_idle()

    def update_selected_value(self):
        if not self.selected_data:
            return

        marker_idx, label, magnitude_data = self.selected_data
        frame = int(self.current_frame)
        
        plotter = self.forces_plotter if not (self.gait_cycles and (self.gait_cycles['left'] or self.gait_cycles['right'])) else self.gait_cycle_plotter
        value_text = plotter.get_value_at_frame(marker_idx, frame)
        
        if value_text:
            self.value_label.setText(value_text)
        else:
            self.value_label.setText(f"{label}: Frame {frame} out of range")

    def set_current_frame(self, frame_index):
        self.current_frame = frame_index

        plot_current_frame = frame_index
        if self.frame_range:
            start_frame, end_frame = self.frame_range
            if not (start_frame <= frame_index <= end_frame):
                plot_current_frame = None

        for vline in self.vlines:
            if plot_current_frame is not None:
                vline.set_xdata([plot_current_frame])
                vline.set_visible(True)
            else:
                vline.set_visible(False)
        
        if self.canvas:
            self.canvas.draw_idle()

        if self.selected_data:
            self.update_selected_value()

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
        self.lines = {}
