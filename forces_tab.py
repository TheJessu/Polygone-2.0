from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QScrollArea, QGridLayout
from PyQt5.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from gait_cycle_plotter import GaitCyclePlotter
from generic_plotter import GenericDataPlotter

class PlotWidget(QWidget):
    plot_double_clicked = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(4, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def mouseDoubleClickEvent(self, event):
        self.plot_double_clicked.emit(self)

class ForcesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.forces_plotter = GenericDataPlotter('FORCES')
        self.gait_cycle_plotter = GaitCyclePlotter()
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

        self.clear_plots()
        self.vlines = []

        selected_group = self.group_dropdown.currentText()
        selected_component = self.component_dropdown.currentText()
        
        groups = [g for g in self.groups if g != "All" and self.group_visibility.get(g, True)]
        if selected_group != "All":
            groups = [selected_group]

        use_gait_cycle = self.gait_cycles and (self.gait_cycles['left'] or self.gait_cycles['right'])
        
        if self.zoomed_plot:
            self.zoomed_plot = None
            for p in self.plots:
                p.show()

        row, col = 0, 0
        if selected_component == "All":
            for group in groups:
                for component in ['x', 'y', 'z']:
                    plot_widget = self.add_plot(row, col)
                    plot_widget.ax.set_title(f'{group} - {component.upper()}')
                    plot_widget.ax.set_xlabel('Frame' if not use_gait_cycle else 'Gait Cycle (%)')
                    plot_widget.ax.set_ylabel('Force (N)')
                    if use_gait_cycle:
                        self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'FORCES', 'Force (N)', current_frame, component=component)
                    else:
                        self.forces_plotter.plot_data(plot_widget.ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, component=component)
                        if plot_current_frame is not None:
                            self.vlines.append(plot_widget.ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1))
                    
                    col += 1
                    if col >= 3:
                        col = 0
                        row += 1
                    plot_widget.canvas.draw()
        else:
            component = selected_component.lower()
            for group in groups:
                plot_widget = self.add_plot(row, col)
                plot_widget.ax.set_title(f'{group} - {selected_component}')
                plot_widget.ax.set_xlabel('Frame' if not use_gait_cycle else 'Gait Cycle (%)')
                plot_widget.ax.set_ylabel('Force (N)')
                if use_gait_cycle:
                    self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'FORCES', 'Force (N)', current_frame, component=component)
                else:
                    self.forces_plotter.plot_data(plot_widget.ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, component=component)
                    if plot_current_frame is not None:
                        self.vlines.append(plot_widget.ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1))
                
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
                plot_widget.canvas.draw()

    def add_plot(self, row, col):
        plot_widget = PlotWidget(self.plot_container)
        plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
        self.plot_layout.addWidget(plot_widget, row, col)
        self.plots.append(plot_widget)
        return plot_widget

    def clear_plots(self):
        for plot_widget in self.plots:
            self.plot_layout.removeWidget(plot_widget)
            plot_widget.deleteLater()
        self.plots = []

    def on_selection_changed(self, value):
        if self.markers_data is not None:
            self.plot_data(self.markers_data, self.marker_types, self.marker_labels, self.current_frame, self.max_plots, self.frame_range)
    
    def on_plot_double_clicked(self, plot_widget):
        if self.zoomed_plot:
            self.zoomed_plot = None
            for p in self.plots:
                p.show()
        else:
            self.zoomed_plot = plot_widget
            for p in self.plots:
                if p is not plot_widget:
                    p.hide()

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
        
        for plot in self.plots:
            plot.canvas.draw_idle()

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
        self.forces_plotter.lines = {}