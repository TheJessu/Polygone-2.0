from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QScrollArea, QGridLayout
from PyQt5.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from gait_cycle_plotter import GaitCyclePlotter
from generic_plotter import GenericDataPlotter

class PlotWidget(QWidget):
    plot_double_clicked = pyqtSignal(QWidget)
    line_clicked = pyqtSignal(object)  # Signal for line clicks, emits (plotter_type, key)

    def __init__(self, powers_plotter, gait_cycle_plotter, parent=None):
        super().__init__(parent)
        self.powers_plotter = powers_plotter
        self.gait_cycle_plotter = gait_cycle_plotter
        self.lines = {}  # Lines for this plot
        self.figure = Figure(figsize=(4, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.canvas.setFixedSize(200, 200)

        self.figure.patch.set_facecolor('white')
        self.ax.set_facecolor('white')

        self.canvas.mpl_connect('button_press_event', self.on_mpl_click)
        self.canvas.mpl_connect('pick_event', self.on_line_pick)

    def on_mpl_click(self, event):
        if event.dblclick:
            self.plot_double_clicked.emit(self)

    def on_line_pick(self, event):
        # Handle line picking
        if hasattr(event.artist, 'get_label'):
            # Check this plot's lines first
            for key, (line, _, _, _) in self.lines.items():
                if line == event.artist:
                    self.line_clicked.emit(('powers', key))
                    return
            # Check powers_plotter lines
            for key, (line, _, _, _, _, _) in self.powers_plotter.lines.items():
                if line == event.artist:
                    self.line_clicked.emit(('powers', key))
                    return
            # Check gait_cycle_plotter lines
            for line_key, (line, _, _, _) in self.gait_cycle_plotter.lines.items():
                if line == event.artist:
                    self.line_clicked.emit(('gait', line_key))
                    return

    def enterEvent(self, event):
        self.ax.set_facecolor('#f0f0f0')
        self.canvas.draw()

    def leaveEvent(self, event):
        self.ax.set_facecolor('white')
        self.canvas.draw()

class PowersTab(QWidget):
    def __init__(self):
        super().__init__()
        self.powers_plotter = GenericDataPlotter('POWERS')
        self.gait_cycle_plotter = GaitCyclePlotter()
        self.gait_cycles = None
        self.frame_range = None

        self.layout = QVBoxLayout(self)

        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Select Component:"))
        self.dropdown = QComboBox()
        self.dropdown.addItem("All")
        self.dropdown.addItem("X")
        self.dropdown.addItem("Y")
        self.dropdown.addItem("Z")
        self.dropdown.currentTextChanged.connect(self.on_group_selected)
        dropdown_layout.addWidget(self.dropdown)
        dropdown_layout.addStretch()
        self.layout.addLayout(dropdown_layout)

        self.buttons_layout = QVBoxLayout()
        self.layout.addLayout(self.buttons_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area, 1)
        
        self.plot_container = QWidget()
        self.plot_layout = QGridLayout(self.plot_container)
        self.scroll_area.setWidget(self.plot_container)

        self.value_label = QLabel("")
        self.layout.addWidget(self.value_label)

        self.gait_info_label = QLabel("")
        self.gait_info_label.setWordWrap(True)
        self.layout.addWidget(self.gait_info_label)

        self.plots = []
        self.vlines = []
        self.groups = []
        self.current_frame = 0
        self.max_plots = 4

        self.group_visibility = {}
        self.group_buttons = {}

        self.zoomed_plot = None
        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None
        self.highlighted_line = None  # Track the currently highlighted line

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.arrange_buttons()

    def arrange_buttons(self):
        if not self.group_buttons:
            return

        for i in reversed(range(self.buttons_layout.count())):
            layout_item = self.buttons_layout.itemAt(i)
            if layout_item and layout_item.layout():
                while layout_item.layout().count():
                    item = layout_item.layout().takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                self.buttons_layout.removeItem(layout_item.layout())

        button_width = 60
        spacing = 5
        available_width = self.width() - 20
        buttons_per_row = max(1, available_width // (button_width + spacing))

        button_list = list(self.group_buttons.values())
        for i in range(0, len(button_list), buttons_per_row):
            row_layout = QHBoxLayout()
            for j in range(buttons_per_row):
                if i + j < len(button_list):
                    button = button_list[i + j]
                    button.setFixedSize(button_width, 25)
                    row_layout.addWidget(button)
            row_layout.addStretch()
            self.buttons_layout.addLayout(row_layout)
            
    def set_gait_cycles(self, gait_cycles):
        self.gait_cycles = gait_cycles

    def load_data(self, markers_data, marker_types, marker_labels, body_mass=None):
        type_indices = [i for i, t in enumerate(marker_types) if t == 'POWERS']
        groups = set()
        name_map = {'Hi': 'Hip', 'Kne': 'Knee', 'Ankl': 'Ankle'}
        for idx in type_indices:
            if idx < len(marker_labels) and marker_labels[idx]:
                label = marker_labels[idx]
                group = ""
                if label.startswith('L') or label.startswith('R'):
                    group = label[1:-len('POWERS')].lower().capitalize()
                else:
                    group = label[:-len('POWERS')].lower().capitalize() if label.endswith('POWERS') else label.lower().capitalize()

                group = name_map.get(group, group)
                if group:
                    groups.add(group)

        self.groups = sorted(list(groups))

        self.group_options = ["All", "X", "Y", "Z"]
        self.dropdown.clear()
        self.dropdown.addItems(self.group_options)

        for button in self.group_buttons.values():
            button.setParent(None)
        self.group_buttons.clear()
        self.group_visibility.clear()

        grey_out_groups = ['Absankl', 'Ankle', 'Elbow', 'Shoulder', 'Thorax', 'Wrist']
        for group in self.groups:
            button = QPushButton(group)
            button.setCheckable(True)
            default_visible = group in ['Hip', 'Knee', 'Ankle']
            button.setChecked(default_visible)
            button.clicked.connect(lambda checked, g=group: self.toggle_group_visibility(g))
            self.group_buttons[group] = button
            self.group_visibility[group] = default_visible
            self.update_button_style(button, default_visible)
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

        self.clear_plots()
        self.vlines = []
        self.highlighted_line = None
        self.value_label.setText("")
        self.powers_plotter.lines.clear()
        self.gait_cycle_plotter.lines = {}

        selected_component = self.dropdown.currentText()
        desired_order = ['Hip', 'Knee', 'Ankle']
        groups = [g for g in desired_order if g in self.groups and self.group_visibility.get(g, True)]
        use_gait_cycle = self.gait_cycles and (self.gait_cycles['left'] or self.gait_cycles['right'])

        if self.zoomed_plot:
            self.zoomed_plot = None
            for p in self.plots:
                p.show()

        row, col = 0, 0
        components_to_plot = ['x', 'y', 'z'] if selected_component == "All" else [selected_component.lower()]
        
        for group in groups:
            for component in components_to_plot:
                if selected_component != "All" and component != selected_component.lower():
                    continue

                plot_widget = self.add_plot(row, col)
                
                # Set title
                title = f'{group} - {component.upper()}'
                if group.lower() == 'hip' and component == 'z':
                    title = 'Hip Power'
                elif group.lower() == 'knee' and component == 'z':
                    title = 'Knee Power'
                elif group.lower() == 'ankle' and component == 'z':
                    title = 'Ankle Power'
                plot_widget.ax.set_title(title)

                # Set labels
                plot_widget.ax.set_xlabel('Frame' if not use_gait_cycle else 'Gait Cycle (%)')
                plot_widget.ax.set_ylabel('Power (W/kg)')

                # Plot data
                if use_gait_cycle:
                    self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'POWERS', 'Power (W/kg)', current_frame, component=component)
                else:
                    self.powers_plotter.plot_data(plot_widget.ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, component=component, plot_widget=plot_widget)
                    if plot_current_frame is not None:
                        self.vlines.append(plot_widget.ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1))

                # Apply specific styles for Z-component plots
                if component == 'z':
                    plot_widget.ax.text(-0.05, 0.25, 'Abs', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.50, 'W/kg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.75, 'Gen', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)

                    if group.lower() in ['hip', 'knee', 'ankle']:
                        ymin, ymax = -2.0, 3.0
                        plot_widget.ax.set_ylim(ymin, ymax)
                        plot_widget.ax.set_yticks([ymin, ymax])

                        if ymin <= 0 <= ymax:
                            plot_widget.ax.axhline(y=0, color='#555555', linestyle='-', linewidth=1.5, alpha=0.7, zorder=-1)

                        max_abs = max(abs(ymin), abs(ymax))
                        for step in np.arange(0.5, max_abs + 0.5, 0.5):
                            if ymin <= step <= ymax:
                                plot_widget.ax.axhline(y=step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5, zorder=-1)
                            if ymin <= -step <= ymax:
                                plot_widget.ax.axhline(y=-step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5, zorder=-1)

                plot_widget.ax.set_box_aspect(1)
                plot_widget.canvas.draw()
                
                col += 1
                if col >= 3:
                    col = 0
                    row += 1


    def add_plot(self, row, col):
        plot_widget = PlotWidget(self.powers_plotter, self.gait_cycle_plotter, self.plot_container)
        plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
        plot_widget.line_clicked.connect(self.on_line_clicked)
        plot_widget.setProperty("grid_pos", (row, col))
        self.plot_layout.addWidget(plot_widget, row, col)
        self.plots.append(plot_widget)
        return plot_widget

    def clear_plots(self):
        for plot_widget in self.plots:
            self.plot_layout.removeWidget(plot_widget)
            plot_widget.deleteLater()
        self.plots = []

    def on_group_selected(self, group_name):
        if self.markers_data is not None:
            self.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots, self.frame_range)

    def on_plot_double_clicked(self, plot_widget):
        if self.zoomed_plot:
            # Zoom out
            self.plot_layout.removeWidget(self.zoomed_plot)
            self.zoomed_plot.canvas.setFixedSize(200, 200)
            self.zoomed_plot.canvas.draw()
            for p in self.plots:
                pos = p.property("grid_pos")
                if pos:
                    self.plot_layout.addWidget(p, pos[0], pos[1])
                p.canvas.setFixedSize(200, 200)
                p.canvas.draw()
                p.show()
            self.zoomed_plot = None
        else:
            # Zoom in
            self.zoomed_plot = plot_widget
            for p in self.plots:
                if p is not self.zoomed_plot:
                    self.plot_layout.removeWidget(p)
                    p.hide()
            # Remove and re-add zoomed plot at (0,0) with larger size
            self.plot_layout.removeWidget(self.zoomed_plot)
            self.plot_layout.addWidget(self.zoomed_plot, 0, 0)
            self.zoomed_plot.canvas.setFixedSize(400, 400)
            self.zoomed_plot.canvas.draw()
            self.zoomed_plot.show()
        self.plot_layout.update()
        self.plot_container.adjustSize()
        self.plot_container.updateGeometry()
        self.plot_container.show()
        self.scroll_area.update()
        self.scroll_area.show()

    def on_line_clicked(self, line_info):
        plotter_type, key = line_info

        # Unhighlight previous line
        if self.highlighted_line is not None:
            prev_plotter_type, prev_key = self.highlighted_line
            if prev_plotter_type == 'powers':
                self.powers_plotter.highlight_line(prev_key, highlight=False)
            elif prev_plotter_type == 'gait':
                self.gait_cycle_plotter.highlight_line(prev_key, highlight=False)

        # Highlight new line
        if plotter_type == 'powers':
            self.powers_plotter.highlight_line(key, highlight=True)
        elif plotter_type == 'gait':
            self.gait_cycle_plotter.highlight_line(key, highlight=True)
        self.highlighted_line = line_info

        # Update display info
        if plotter_type == 'powers':
            info = self.powers_plotter.get_line_info(key, self.current_frame, self.gait_cycles)
        elif plotter_type == 'gait':
            info = self.gait_cycle_plotter.get_line_info(key, self.current_frame, self.gait_cycles, 'POWERS')
        self.value_label.setText(info)

        # Redraw all plots
        for plot in self.plots:
            plot.canvas.draw()

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

        # Update highlighted line info if any
        if self.highlighted_line is not None:
            plotter_type, key = self.highlighted_line
            if plotter_type == 'powers':
                info = self.powers_plotter.get_line_info(key, self.current_frame, self.gait_cycles)
            elif plotter_type == 'gait':
                info = self.gait_cycle_plotter.get_line_info(key, self.current_frame, self.gait_cycles, 'POWERS')
            self.value_label.setText(info)

        for plot in self.plots:
            plot.canvas.draw()

    def set_gait_info(self, info_text):
        self.gait_info_label.setText(info_text)

    def toggle_group_visibility(self, group):
        self.group_visibility[group] = not self.group_visibility[group]
        button = self.group_buttons[group]
        button.setChecked(self.group_visibility[group])
        self.update_button_style(button, self.group_visibility[group])
        if self.markers_data is not None:
            self.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots, self.frame_range)

    def update_button_style(self, button, visible):
        if visible:
            button.setStyleSheet("QPushButton { background-color: white; color: black; }")
        else:
            button.setStyleSheet("QPushButton { background-color: grey; color: white; }")

    def clear_data(self):
        self.clear_plots()
        self.vlines = []
        self.value_label.setText("")
        self.gait_info_label.setText("")
        self.powers_plotter.lines = {}
        self.gait_cycle_plotter.lines = {}
        self.highlighted_line = None
