from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QGridLayout, QLabel, QPushButton, QHBoxLayout, QInputDialog, QComboBox, QFileDialog, QCheckBox, QScrollArea
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStyle
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from gait_cycle_plotter import GaitCyclePlotter
from pdfExport import PDFExporter
from generic_plotter import EditablePlotWidget
from multiline import MultilineImporter
from pxdExport import PXDExporter

class GaitPlotWidget(EditablePlotWidget):
    line_clicked = pyqtSignal(str)

    def __init__(self, gait_cycle_plotter, parent=None):
        super().__init__(parent)
        self.gait_cycle_plotter = gait_cycle_plotter
        self.canvas.setFixedSize(200, 200)
        self.canvas.mpl_connect('pick_event', self.on_line_pick)

    def on_line_pick(self, event):
        for key, (line, _, _, _, _) in self.gait_cycle_plotter.lines.items():
            if line == event.artist:
                self.line_clicked.emit(key)
                return

class PlotWidget(EditablePlotWidget):
    line_clicked = pyqtSignal(str)

    def __init__(self, gait_cycle_plotter, parent=None):
        super().__init__(parent)
        self.gait_cycle_plotter = gait_cycle_plotter
        self.canvas.setFixedSize(200, 200)
        self.canvas.mpl_connect('pick_event', self.on_line_pick)

    def on_line_pick(self, event):
        for key, (line, _, _, _, _) in self.gait_cycle_plotter.lines.items():
            if line == event.artist:
                self.line_clicked.emit(key)
                return

class GaitAnalysisTab(QWidget):
    editable_value_changed = pyqtSignal(str, str, dict)  # key, type, value_dict

    def __init__(self):
        super().__init__()
        self.gait_cycle_plotter = GaitCyclePlotter()
        self.gait_cycles = None
        self.pdf_exporter = PDFExporter()
        self.body_mass = None
        self.multiline_importer = MultilineImporter()
        self.imported_averages = None

        self.red_colors = ['#A30000', '#FF0000', '#FF5C5C', '#E34234', '#F88379']
        self.green_colors = ['#008000', '#00D100', '#00FF00', '#004700', '#AFE1AF']
        self.line_styles = ['-', '--', ':', '-.', (0, (3, 1, 1, 1))]  # solid, dashed, dotted, dash-dot, dash-dot-dot

        self.main_visible = True

        self.layout = QVBoxLayout(self)

        # Add export button
        button_layout = QHBoxLayout()
        self.export_pdf_button = QPushButton("Export PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.import_avg_button = QPushButton("Import Averages")
        self.import_avg_button.clicked.connect(self.import_averages)
        self.import_c3d_button = QPushButton("Import C3D")
        self.import_c3d_button.clicked.connect(self.import_c3d_for_gait_analysis)
        self.main_toggle_button = QPushButton("Toggle Main C3D")
        self.main_toggle_button.setCheckable(True)
        self.main_toggle_button.setChecked(self.main_visible)
        self.main_toggle_button.clicked.connect(self.toggle_main_visibility)
        button_layout.addWidget(self.import_avg_button)
        button_layout.addWidget(self.export_pdf_button)
        button_layout.addWidget(self.main_toggle_button)
        button_layout.addWidget(self.import_c3d_button)
        button_layout.addStretch()
        self.layout.addLayout(button_layout)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Kinematics Tab
        self.kinematics_tab = QWidget()
        self.kinematics_tab_layout = QVBoxLayout(self.kinematics_tab)
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Side:"))
        self.kinematics_dropdown = QComboBox()
        self.kinematics_dropdown.addItems(["All", "Red", "Green"])
        self.kinematics_dropdown.currentTextChanged.connect(self.on_kinematics_side_changed)
        dropdown_layout.addWidget(self.kinematics_dropdown)
        dropdown_layout.addStretch()
        self.kinematics_tab_layout.addLayout(dropdown_layout)
        self.kinematics_file_buttons_layout = QHBoxLayout()
        self.kinematics_tab_layout.addLayout(self.kinematics_file_buttons_layout)
        self.kinematics_scroll_area = QScrollArea()
        self.kinematics_scroll_area.setWidgetResizable(True)
        self.kinematics_plot_container = QWidget()
        self.kinematics_plot_layout = QGridLayout(self.kinematics_plot_container)
        self.kinematics_scroll_area.setWidget(self.kinematics_plot_container)
        self.kinematics_tab_layout.addWidget(self.kinematics_scroll_area)
        self.tab_widget.addTab(self.kinematics_tab, "Gait 1 Kinematics")
        self.kinematics_side_filter = "All"
        self.kinematics_file_buttons = []
        self.kinematics_delete_buttons = []
        self.kinematics_visible_file_index = None
        self.kinematics_red_visible_files = set()
        self.kinematics_green_visible_files = set()

        # Kinetics Tab
        self.kinetics_tab = QWidget()
        self.kinetics_tab_layout = QVBoxLayout(self.kinetics_tab)
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Side:"))
        self.kinetics_dropdown = QComboBox()
        self.kinetics_dropdown.addItems(["All", "Red", "Green"])
        self.kinetics_dropdown.currentTextChanged.connect(self.on_kinetics_side_changed)
        dropdown_layout.addWidget(self.kinetics_dropdown)
        dropdown_layout.addStretch()
        self.kinetics_tab_layout.addLayout(dropdown_layout)
        self.kinetics_file_buttons_layout = QHBoxLayout()
        self.kinetics_tab_layout.addLayout(self.kinetics_file_buttons_layout)
        self.kinetics_scroll_area = QScrollArea()
        self.kinetics_scroll_area.setWidgetResizable(True)
        self.kinetics_plot_container = QWidget()
        self.kinetics_plot_layout = QGridLayout(self.kinetics_plot_container)
        self.kinetics_scroll_area.setWidget(self.kinetics_plot_container)
        self.kinetics_tab_layout.addWidget(self.kinetics_scroll_area)
        self.tab_widget.addTab(self.kinetics_tab, "Gait 1 Kinetics")
        self.kinetics_side_filter = "All"
        self.kinetics_file_buttons = []
        self.kinetics_visible_file_index = None
        self.kinetics_red_visible_files = set()
        self.kinetics_green_visible_files = set()

        # Moments Tab
        self.moments_tab = QWidget()
        self.moments_tab_layout = QVBoxLayout(self.moments_tab)
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Side:"))
        self.moments_dropdown = QComboBox()
        self.moments_dropdown.addItems(["All", "Red", "Green"])
        self.moments_dropdown.currentTextChanged.connect(self.on_moments_side_changed)
        dropdown_layout.addWidget(self.moments_dropdown)
        dropdown_layout.addStretch()
        self.moments_tab_layout.addLayout(dropdown_layout)
        self.moments_file_buttons_layout = QHBoxLayout()
        self.moments_tab_layout.addLayout(self.moments_file_buttons_layout)
        self.moments_scroll_area = QScrollArea()
        self.moments_scroll_area.setWidgetResizable(True)
        self.moments_plot_container = QWidget()
        self.moments_plot_layout = QGridLayout(self.moments_plot_container)
        self.moments_scroll_area.setWidget(self.moments_plot_container)
        self.moments_tab_layout.addWidget(self.moments_scroll_area)
        self.tab_widget.addTab(self.moments_tab, "Gait 1 Moments")
        self.moments_side_filter = "All"
        self.moments_file_buttons = []
        self.moments_visible_file_index = None
        self.moments_red_visible_files = set()
        self.moments_green_visible_files = set()

        self.kinematics_plots = []
        self.kinetics_plots = []
        self.moments_plots = []
        self.vlines = []
        self.plot_keys = {}  # key to (plot_widget, group, comp, plot_type)

        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None
        self.current_frame = 0
        self.editable_values = {}
        self.highlighted_line_key = None
        self.highlighted_section = None

        self.setup_kinematics_plots()
        self.setup_kinetics_plots()
        self.setup_moments_plots()

    def setup_kinematics_plots(self):
        groups = ['Spine', 'Pelvis', 'Hip', 'Knee', 'Footprogress']
        components = ['x', 'y', 'z']
        row = 0
        for group in groups:
            col = 0
            for comp in components:
                plot_widget = PlotWidget(self.gait_cycle_plotter, self.kinematics_tab)
                plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
                plot_widget.ymin_double_clicked.connect(self.on_ymin_double_clicked)
                plot_widget.ymax_double_clicked.connect(self.on_ymax_double_clicked)
                plot_widget.title_double_clicked.connect(self.on_title_double_clicked)
                plot_widget.line_clicked.connect(lambda key: self.on_line_clicked(key, 'kinematics'))
                self.kinematics_plot_layout.addWidget(plot_widget, row, col)
                self.kinematics_plots.append((plot_widget, group, comp))
                col += 1
            row += 1
        # Modify the Footprogress y plot to Ankle y
        for i, (plot_widget, group, comp) in enumerate(self.kinematics_plots):
            if group == 'Footprogress' and comp == 'y':
                self.kinematics_plots[i] = (plot_widget, 'Ankle', 'y')
                break

    def setup_kinetics_plots(self):
        # 3x3 grid
        plots_config = [
            ('Hip', 'y', 'ANGLES', ''),
            ('Knee', 'y', 'ANGLES', ''),
            ('Ankle', 'y', 'ANGLES', ''),
            ('Hip', 'y', 'MOMENTS', ''),
            ('Knee', 'y', 'MOMENTS', ''),
            ('Ankle', 'y', 'MOMENTS', ''),
            ('Hip', 'z', 'POWERS', ''),
            ('Knee', 'z', 'POWERS', ''),
            ('Ankle', 'z', 'POWERS', '')
        ]
        for i, (group, comp, plot_type, *rest) in enumerate(plots_config):
            y_label = rest[0] if rest else ''
            unit_factor = rest[1:] if len(rest) > 1 else []
            row = i // 3
            col = i % 3
            plot_widget = GaitPlotWidget(self.gait_cycle_plotter, self.kinetics_tab)
            plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
            plot_widget.line_clicked.connect(lambda key: self.on_line_clicked(key, 'kinetics'))
            self.kinetics_plot_layout.addWidget(plot_widget, row, col)
            self.kinetics_plots.append((plot_widget, group, comp, plot_type, y_label, unit_factor[0] if unit_factor else 1))

    def setup_moments_plots(self):
        # 3x3 grid for hip, knee, ankle x,y,z moments
        groups = ['Hip', 'Knee', 'Ankle']
        components = ['x', 'y', 'z']
        row = 0
        for group in groups:
            col = 0
            for comp in components:
                plot_widget = GaitPlotWidget(self.gait_cycle_plotter, self.moments_tab)
                plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
                plot_widget.ymin_double_clicked.connect(self.on_ymin_double_clicked)
                plot_widget.ymax_double_clicked.connect(self.on_ymax_double_clicked)
                plot_widget.title_double_clicked.connect(self.on_title_double_clicked)
                plot_widget.line_clicked.connect(lambda key: self.on_line_clicked(key, 'moments'))
                self.moments_plot_layout.addWidget(plot_widget, row, col)
                self.moments_plots.append((plot_widget, group, comp))
                col += 1
            row += 1

    def load_data(self, markers_data, marker_types, marker_labels, body_mass=None):
        self.markers_data = markers_data
        self.marker_types = marker_types
        self.marker_labels = marker_labels
        self.body_mass = body_mass
        self.plot_data()

    def set_gait_cycles(self, gait_cycles):
        self.gait_cycles = gait_cycles
        self.plot_data()

    def set_editable_values(self, editable_values):
        self.editable_values = editable_values
        self.plot_data()

    def set_current_frame(self, frame_index):
        self.current_frame = frame_index
        # Update vlines only for kinematics plots
        for vline in self.vlines:
            if vline:
                # Remove old vline
                vline.remove()
        self.vlines = []

    def plot_data(self):
        if self.markers_data is None or not self.gait_cycles:
            return

        # Clear existing plots
        for plot_widget, *_ in self.kinematics_plots:
            plot_widget.ax.clear()
        for plot_widget, *_ in self.kinetics_plots:
            plot_widget.ax.clear()
        for plot_widget, *_ in self.moments_plots:
            plot_widget.ax.clear()
        self.vlines = []
        self.gait_cycle_plotter.lines = {}

        # Plot kinematics
        for plot_widget, group, comp in self.kinematics_plots:
            title = f'{group} - {comp.upper()}'

            if group.lower() == 'spine':
                title = f'{group} - {"Trunk Sway" if comp == "x" else "Trunk Tilt" if comp == "y" else "Trunk Rotation"}'
            elif group.lower() == 'pelvis':
                title = f'{group} - {"Pelvic Obliquity" if comp == "x" else "Pelvic Tilt" if comp == "y" else "Pelvic Rotation"}'
            elif group.lower() == 'hip':
                title = f'{group} - {"Hip Ab-Adduction" if comp == "x" else "Hip Flexion-Extension" if comp == "y" else "Hip Rotation"}'
            elif group.lower() == 'knee':
                title = f'{group} - {"Knee Flexion-Extension" if comp == "y" else "Knee Rotation" if comp == "z" else "Knee Valg/Varus"}'
            elif group.lower() == 'ankle':
                title = f'{group} - {"Dorsi-Plantarflexion" if comp == "y" else comp.upper()}'

            elif group.lower() == 'footprogress':
                title = f'{group} - {"Dorsi-Plantarflexion" if comp == "y" else "Foot Progression" if comp == "z" else comp.upper()}'
            plot_widget.ax.set_title(title, fontsize=10)
            plot_widget.ax.set_xlabel('Gait Cycle (%)', fontsize=8, labelpad=-1)
            if self.main_visible:
                if self.imported_averages and 'ANGLES' in self.imported_averages:
                    if group in self.imported_averages['ANGLES'] and comp in self.imported_averages['ANGLES'][group]:
                        avg = self.imported_averages['ANGLES'][group][comp]
                        mean = np.array(avg['mean'])
                        std = np.array(avg['std'])
                        x = np.linspace(0, 100, len(mean))
                        plot_widget.ax.fill_between(x, mean - std, mean + std, color='grey', alpha=0.3)
                        plot_widget.ax.plot(x, mean, color='grey', linestyle='--', linewidth=1)                

                self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, 'ANGLES', '', self.current_frame, component=comp, side_filter=self.kinematics_side_filter, key_suffix="_main")

            # Plot multiline data
            if self.multiline_importer.get_num_files() > 0:
                for i, file_data in reversed(list(enumerate(self.multiline_importer.imported_files))):
                    linestyle = self.line_styles[i % len(self.line_styles)]
                    if self.kinematics_side_filter == "All":
                        if i == self.kinematics_visible_file_index:
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'ANGLES', '', self.current_frame, component=comp, side_filter="Red", color=self.red_colors[0], linestyle=linestyle, key_suffix=f"_file_{i}")
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'ANGLES', '', self.current_frame, component=comp, side_filter="Green", color=self.green_colors[0], linestyle=linestyle, key_suffix=f"_file_{i}")
                    elif self.kinematics_side_filter == "Red":
                        if i in self.kinematics_red_visible_files:
                            idx_in_red = list(self.kinematics_red_visible_files).index(i)
                            color = self.red_colors[idx_in_red % len(self.red_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'ANGLES', '', self.current_frame, component=comp, side_filter="Red", color=color, linestyle=linestyle, key_suffix=f"_file_{i}")
                    elif self.kinematics_side_filter == "Green":
                        if i in self.kinematics_green_visible_files:
                            idx_in_green = list(self.kinematics_green_visible_files).index(i)
                            color = self.green_colors[idx_in_green % len(self.green_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'ANGLES', '', self.current_frame, component=comp, side_filter="Green", color=color, linestyle=linestyle, key_suffix=f"_file_{i}")
            # Set default y-limits for kinematics (angles)
            if group.lower() == 'spine':
                ymin, ymax = -20, 20
            elif group.lower() == 'pelvis':
                if comp == 'x':
                    ymin, ymax = -20, 20
                elif comp == 'y':
                    ymin, ymax = -5, 35
                else:
                    ymin, ymax = -30, 30
            elif group.lower() == 'hip':
                if comp == 'x':
                    ymin, ymax = -15, 20
                elif comp == 'y':
                    ymin, ymax = -15, 60
                else:
                    ymin, ymax = -30, 40
            elif group.lower() == 'knee':
                ymin, ymax = -15, 90
            elif group.lower() == 'ankle':
                ymin, ymax = -50, 50
            elif group.lower() == 'footprogress':
                ymin, ymax = -40, 40
            else:
                ymin, ymax = -50, 50  # default
            
            # Check for edited values
            plot_key = f"ANGLES_{group}_{comp}"
            plot_widget.plot_key = plot_key
            if plot_key in self.editable_values:
                edited = self.editable_values[plot_key]
                ymin = edited.get('ymin', ymin)
                ymax = edited.get('ymax', ymax)
                if 'title' in edited:
                    title = edited['title']
                    plot_widget.ax.set_title(title)

            plot_widget.ax.set_ylim(ymin, ymax)
            if group.lower() == 'ankle' and comp == 'y':
                plot_widget.ax.set_yticks([-50, 50])
            else:
                plot_widget.ax.set_yticks([ymin, ymax])
            # Add editable texts
            plot_widget.add_editable_texts(ymin, ymax, title)
            plot_widget.canvas.draw()
            plot_widget.setVisible(True)

        # Adjust subplot margins to prevent cut-off labels for kinematics
        for plot_widget, *_ in self.kinematics_plots:
            plot_widget.figure.subplots_adjust(left=0.25, right=0.98, top=0.9, bottom=0.2)
            plot_widget.canvas.draw()

        # Plot kinetics
        for plot_widget, group, comp, plot_type, y_label, unit_factor in self.kinetics_plots:
            if plot_type == 'ANGLES':
                if group.lower() == 'hip' and comp == 'y':
                    title = 'Hip Flexion-Extension'
                elif group.lower() == 'knee' and comp == 'y':
                    title = 'Knee Flexion-Extension'
                elif group.lower() == 'ankle' and comp == 'y':
                    title = 'Dorsi-Plantarflexion'
                else:
                    title = f'{group} - {comp.upper()}'
            elif plot_type == 'MOMENTS':
                if group.lower() == 'hip' and comp == 'y':
                    title = 'Hip Flex-Ext Moment'
                elif group.lower() == 'knee' and comp == 'y':
                    title = 'Knee Flex-Ext Moment'
                elif group.lower() == 'ankle' and comp == 'y':
                    title = 'Dors-Plan Moment'
                else:
                    title = f'{group} - {comp.upper()}'
            elif plot_type == 'POWERS':
                if group.lower() == 'hip' and comp == 'z':
                    title = 'Hip Power'
                elif group.lower() == 'knee' and comp == 'z':
                    title = 'Knee Power'
                elif group.lower() == 'ankle' and comp == 'z':
                    title = 'Ankle Power'
                else:
                    title = f'{group} - {comp.upper()}'
            else:
                title = f'{group} - {comp.upper()}'
            plot_widget.ax.set_title(title, fontsize=10)
            plot_widget.ax.set_xlabel('Gait Cycle (%)', fontsize=8, labelpad=-1)
            if plot_type in ['ANGLES', 'MOMENTS']:
                plot_widget.ax.set_ylabel('')
            else:
                plot_widget.ax.set_ylabel(y_label)
            if self.main_visible:
                if self.imported_averages and plot_type in self.imported_averages:
                    if group in self.imported_averages[plot_type] and comp in self.imported_averages[plot_type][group]:
                        avg = self.imported_averages[plot_type][group][comp]
                        mean = np.array(avg['mean'])
                        std = np.array(avg['std'])
                        x = np.linspace(0, 100, len(mean))
                        plot_widget.ax.fill_between(x, mean - std, mean + std, color='grey', alpha=0.3)
                        plot_widget.ax.plot(x, mean, color='grey', linestyle='--', linewidth=1)
                self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, plot_type, y_label, self.current_frame, component=comp, body_mass=self.body_mass, side_filter=self.kinetics_side_filter, key_suffix="_main")

            # Check for edited values
            plot_key = f"{plot_type}_{group}_{comp}"
            plot_widget.plot_key = plot_key
            ymin, ymax = plot_widget.ax.get_ylim()
            if plot_key in self.editable_values:
                edited = self.editable_values[plot_key]
                ymin = edited.get('ymin', ymin)
                ymax = edited.get('ymax', ymax)
                if 'title' in edited:
                    title = edited['title']
                    plot_widget.ax.set_title(title)
            else:
                # Set default y-limits for kinetics
                if plot_type == 'MOMENTS':
                    ymin, ymax = -1.0, 2.0
                elif group.lower() == 'ankle' and comp == 'y':
                    ymin, ymax = -50, 50

            plot_widget.ax.set_ylim(ymin, ymax)
            if plot_type == 'MOMENTS':
                # plot_widget.ax.set_yticks([-1, 2])
                # Clear any existing text labels to prevent overlap
                for text in list(plot_widget.ax.texts):
                    text.remove()
                # Add y-axis text labels at 75%, 50%, 25% based on moments_tab.py
                if group.lower() == 'ankle':
                    plot_widget.ax.text(-0.05, 0.25, 'Dors', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.50, 'Nm/kg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.75, 'Plant', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                elif group.lower() in ['hip', 'knee']:
                    plot_widget.ax.text(-0.05, 0.25, 'Flex', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.50, 'Nm/kg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.75, 'Ext', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
            if group.lower() == 'ankle' and comp == 'y' and plot_type == 'ANGLES':
                for y in range(-50, 51, 10):
                    plot_widget.ax.axhline(y=y, color='grey', linestyle='-', linewidth=0.5)
            plot_widget.add_editable_texts(ymin, ymax, title)
            plot_widget.canvas.draw()
            plot_widget.setVisible(True)
            
            # Plot multiline data for Kinetics
            if self.multiline_importer.get_num_files() > 0:
                for i, file_data in reversed(list(enumerate(self.multiline_importer.imported_files))):
                    linestyle = self.line_styles[i % len(self.line_styles)]
                    if self.kinetics_side_filter == "All":
                        if i == self.kinetics_visible_file_index:
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], plot_type, '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Red", color=self.red_colors[0], linestyle=linestyle, key_suffix=f"_file_{i}")
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], plot_type, '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Green", color=self.green_colors[0], linestyle=linestyle, key_suffix=f"_file_{i}")
                    elif self.kinetics_side_filter == "Red":
                        if i in self.kinetics_red_visible_files:
                            idx_in_red = list(self.kinetics_red_visible_files).index(i)
                            color = self.red_colors[idx_in_red % len(self.red_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], plot_type, '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Red", color=color, linestyle=linestyle, key_suffix=f"_file_{i}")
                    elif self.kinetics_side_filter == "Green":
                        if i in self.kinetics_green_visible_files:
                            idx_in_green = list(self.kinetics_green_visible_files).index(i)
                            color = self.green_colors[idx_in_green % len(self.green_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], plot_type, '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Green", color=color, linestyle=linestyle, key_suffix=f"_file_{i}")
            plot_widget.canvas.draw()

        # Adjust subplot margins to prevent cut-off labels for kinetics
        for plot_widget, *_ in self.kinetics_plots:
            plot_widget.figure.subplots_adjust(left=0.25, right=0.98, top=0.9, bottom=0.2)
            plot_widget.canvas.draw()

        # Plot moments
        for plot_widget, group, comp in self.moments_plots:
            title = f'{group} - {comp.upper()}'
            if group.lower() == 'hip' and comp == 'y':
                title = f'{group} - Hip Flex-Ext Moment'
            elif group.lower() == 'hip' and comp == 'x':
                title = f'{group} - Hip Ab-Add Moment'
            elif group.lower() == 'hip' and comp == 'z':
                title = f'{group} - Hip Rotation Moment'
            elif group.lower() == 'knee' and comp == 'y':
                title = f'{group} - Knee Flex-Ext Moment'
            elif group.lower() == 'knee' and comp == 'x':
                title = f'{group} - Knee Valg-Var Moment'
            elif group.lower() == 'knee' and comp == 'z':
                title = f'{group} - Knee Rotation Moment'
            elif group.lower() == 'ankle' and comp == 'y':
                title = f'{group} - Dors-Plan Moment'
            elif group.lower() == 'ankle' and comp == 'x':
                title = f'{group} - Ankle Ab-Add Moment'
            elif group.lower() == 'ankle' and comp == 'z':
                title = f'{group} - Ankle Rotation Moment'
            plot_widget.ax.set_title(title, fontsize=10)
            plot_widget.ax.set_xlabel('Gait Cycle (%)', fontsize=8, labelpad=-1)
            if self.imported_averages and 'MOMENTS' in self.imported_averages:
                if group in self.imported_averages['MOMENTS'] and comp in self.imported_averages['MOMENTS'][group]:
                    avg = self.imported_averages['MOMENTS'][group][comp]
                    mean = np.array(avg['mean'])
                    std = np.array(avg['std'])
                    x = np.linspace(0, 100, len(mean))
                    plot_widget.ax.fill_between(x, mean - std, mean + std, color='grey', alpha=0.3)
                    plot_widget.ax.plot(x, mean, color='grey', linestyle='--', linewidth=1)                
            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, 'MOMENTS', '', self.current_frame, component=comp, body_mass=self.body_mass, side_filter=self.moments_side_filter, key_suffix="_main")

            # Set default y-limits for moments
            if group.lower() == 'hip':
                if comp == 'x':
                    ymin, ymax = -1.0, 1.0
                elif comp == 'y':
                    ymin, ymax = -1.0, 2.0
                elif comp == 'z':
                    ymin, ymax = -0.5, 0.5
            elif group.lower() == 'knee':
                if comp == 'x':
                    ymin, ymax = -1.0, 1.0
                elif comp == 'y':
                    ymin, ymax = -1.0, 2.0
                elif comp == 'z':
                    ymin, ymax = -0.5, 0.5
            elif group.lower() == 'ankle':
                if comp == 'x':
                    ymin, ymax = -0.5, 0.5
                elif comp == 'y':
                    ymin, ymax = -1.0, 2.0
                elif comp == 'z':
                    ymin, ymax = -0.5, 0.5

            # Check for edited values
            plot_key = f"MOMENTS_{group}_{comp}"
            plot_widget.plot_key = plot_key
            if plot_key in self.editable_values:
                edited = self.editable_values[plot_key]
                ymin = edited.get('ymin', ymin)
                ymax = edited.get('ymax', ymax)
                if 'title' in edited:
                    title = edited['title']
                    plot_widget.ax.set_title(title)

            plot_widget.ax.set_ylim(ymin, ymax)
            plot_widget.ax.set_yticks([ymin, ymax])
            # Clear any existing text labels to prevent overlap
            for text in list(plot_widget.ax.texts):
                text.remove()
            # Add y-axis text labels at 75%, 50%, 25% based on moments_tab.py
            if comp == 'x':
                if group.lower() in ['hip', 'ankle']:
                    plot_widget.ax.text(-0.05, 0.25, 'Add', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.50, 'Nm/kg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.75, 'Abd', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                else:  # knee
                    plot_widget.ax.text(-0.05, 0.25, 'Var', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.50, 'Nm/kg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.75, 'Valg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
            elif comp == 'y' and group.lower() == 'ankle':
                plot_widget.ax.text(-0.05, 0.25, 'Dors', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                plot_widget.ax.text(-0.05, 0.50, 'Nm/kg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                plot_widget.ax.text(-0.05, 0.75, 'Plant', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
            elif comp == 'y' and group.lower() in ['hip', 'knee']:
                plot_widget.ax.text(-0.05, 0.25, 'Flex', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                plot_widget.ax.text(-0.05, 0.50, 'Nm/kg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                plot_widget.ax.text(-0.05, 0.75, 'Ext', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
            elif comp == 'z':
                plot_widget.ax.text(-0.05, 0.25, 'Int', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                plot_widget.ax.text(-0.05, 0.50, 'Nm/kg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                plot_widget.ax.text(-0.05, 0.75, 'Ext', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)

            # Always add a thick, darker grey line at y=0 if within range
            if ymin <= 0 <= ymax:
                plot_widget.ax.axhline(y=0, color='#555555', linestyle='-', linewidth=1.5, alpha=0.7)
            # Add horizontal grid lines at every 0.5 units in both directions from 0
            max_abs = max(abs(ymin), abs(ymax))
            for step in np.arange(0.5, max_abs + 0.5, 0.5):
                if ymin <= step <= ymax:
                    plot_widget.ax.axhline(y=step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
                if ymin <= -step <= ymax:
                    plot_widget.ax.axhline(y=-step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)

            plot_widget.add_editable_texts(ymin, ymax, title)
            plot_widget.canvas.draw()
            plot_widget.setVisible(True)
            
            # Plot multiline data for Moments
            if self.multiline_importer.get_num_files() > 0:
                for i, file_data in reversed(list(enumerate(self.multiline_importer.imported_files))):
                    linestyle = self.line_styles[i % len(self.line_styles)]
                    if self.moments_side_filter == "All":
                        if i == self.moments_visible_file_index:
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'MOMENTS', '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Red", color=self.red_colors[0], linestyle=linestyle, key_suffix=f"_file_{i}")
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'MOMENTS', '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Green", color=self.green_colors[0], linestyle=linestyle, key_suffix=f"_file_{i}")
                    elif self.moments_side_filter == "Red":
                        if i in self.moments_red_visible_files:
                            idx_in_red = list(self.moments_red_visible_files).index(i)
                            color = self.red_colors[idx_in_red % len(self.red_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'MOMENTS', '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Red", color=color, linestyle=linestyle, key_suffix=f"_file_{i}")
                    elif self.moments_side_filter == "Green":
                        if i in self.moments_green_visible_files:
                            idx_in_green = list(self.moments_green_visible_files).index(i)
                            color = self.green_colors[idx_in_green % len(self.green_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'MOMENTS', '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Green", color=color, linestyle=linestyle, key_suffix=f"_file_{i}")
            plot_widget.canvas.draw()

        # Adjust subplot margins to prevent cut-off labels for moments
        for plot_widget, *_ in self.moments_plots:
            plot_widget.figure.subplots_adjust(left=0.25, right=0.98, top=0.9, bottom=0.2)
            plot_widget.canvas.draw()

    def on_plot_double_clicked(self, plot_widget):
        # Simple zoom, but since fixed layout, maybe just ignore or implement basic zoom
        pass

    def on_line_clicked(self, key, section):
        if key == self.highlighted_line_key:
            self.gait_cycle_plotter.highlight_line(key, highlight=False)
            self.highlighted_line_key = None
            self.highlighted_section = None
        else:
            if self.highlighted_line_key:
                self.gait_cycle_plotter.highlight_line(self.highlighted_line_key, highlight=False)
            
            self.gait_cycle_plotter.highlight_line(key, highlight=True, color='blue')
            self.highlighted_line_key = key
            self.highlighted_section = section
        
        # Update buttons
        self.update_kinematics_file_buttons_visibility()
        self.update_kinetics_file_buttons_visibility()
        self.update_moments_file_buttons_visibility()
        
        # Redraw plots to show highlight
        for plot_widget, *_ in self.kinematics_plots + self.kinetics_plots + self.moments_plots:
            plot_widget.canvas.draw()

    def on_ymin_double_clicked(self, plot_widget):
        # Handle ymin editing
        # Find which plot this is
        for i, (pw, *_) in enumerate(self.kinematics_plots + self.kinetics_plots + self.moments_plots):
            if pw == plot_widget:
                # Get current ymin
                ylim = pw.ax.get_ylim()
                current_ymin = ylim[0]
                # Open input dialog
                text, ok = QInputDialog.getText(self, 'Edit Y Min', f'Enter new Y min (current: {current_ymin:.1f}):')
                if ok and text:
                    try:
                        new_ymin = float(text)
                        # Emit signal
                        key = pw.plot_key
                        self.editable_value_changed.emit(key, 'ymin', {'ymin': new_ymin})
                    except ValueError:
                        pass  # Invalid input, ignore
                break

    def on_ymax_double_clicked(self, plot_widget):
        # Handle ymax editing
        # Find which plot this is
        for i, (pw, *_) in enumerate(self.kinematics_plots + self.kinetics_plots + self.moments_plots):
            if pw == plot_widget:
                # Get current ymax
                ylim = pw.ax.get_ylim()
                current_ymax = ylim[1]
                # Open input dialog
                text, ok = QInputDialog.getText(self, 'Edit Y Max', f'Enter new Y max (current: {current_ymax:.1f}):')
                if ok and text:
                    try:
                        new_ymax = float(text)
                        # Emit signal
                        key = pw.plot_key
                        self.editable_value_changed.emit(key, 'ymax', {'ymax': new_ymax})
                    except ValueError:
                        pass  # Invalid input, ignore
                break

    def on_title_double_clicked(self, plot_widget):
        # Handle title editing
        # Find which plot this is
        for i, (pw, *_) in enumerate(self.kinematics_plots + self.kinetics_plots):
            if pw == plot_widget:
                # Get current title
                current_title = pw.ax.get_title()
                # Open input dialog
                text, ok = QInputDialog.getText(self, 'Edit Title', f'Enter new title (current: {current_title}):')
                if ok and text:
                    # Emit signal
                    key = pw.plot_key
                    self.editable_value_changed.emit(key, 'title', {'title': text})
                break

    def export_to_pdf(self):
        """Export the gait analysis tab content to PDF."""
        if self.markers_data is None or not self.gait_cycles:
            # Show a message or disable button if no data
            return
        # Ensure plots are up to date
        self.plot_data()
        self.pdf_exporter.export_gait_analysis_to_pdf(self)

    def clear_data(self):
        self.markers_data = None
        self.marker_types = None
        self.marker_labels = None
        self.gait_cycles = None
        for plot_widget, *_ in self.kinematics_plots:
            plot_widget.ax.clear()
            plot_widget.canvas.draw()
        for plot_widget, *_ in self.kinetics_plots:
            plot_widget.ax.clear()
            plot_widget.canvas.draw()
        for plot_widget, *_ in self.moments_plots:
            plot_widget.ax.clear()
            plot_widget.canvas.draw()
        self.vlines = []

    def on_kinematics_side_changed(self, side):
        self.kinematics_side_filter = side
        self.update_kinematics_file_buttons_visibility()
        self.plot_data()

    def on_kinetics_side_changed(self, side):
        self.kinetics_side_filter = side
        self.update_kinetics_file_buttons_visibility()
        self.plot_data()

    def on_moments_side_changed(self, side):
        self.moments_side_filter = side
        self.update_moments_file_buttons_visibility()
        self.plot_data()

    def import_c3d_for_kinematics(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Import C3D Files", "", "C3D Files (*.c3d)")
        if file_paths:
            for file_path in file_paths:
                if self.multiline_importer.get_num_files() >= 5:
                    break  # Stop if limit reached
                if self.multiline_importer.import_c3d(file_path):
                    new_idx = self.multiline_importer.get_num_files() - 1
                    
                    # Set default visibility
                    if self.multiline_importer.get_num_files() == 1:
                        self.kinematics_visible_file_index = 0
                        self.kinetics_visible_file_index = 0
                        self.moments_visible_file_index = 0
                    
                    self.kinematics_red_visible_files.add(new_idx)
                    self.kinematics_green_visible_files.add(new_idx)
                    self.kinetics_red_visible_files.add(new_idx)
                    self.kinetics_green_visible_files.add(new_idx)
                    self.moments_red_visible_files.add(new_idx)
                    self.moments_green_visible_files.add(new_idx)
                else:
                    # Show error message for failed import
                    pass
            self.update_kinematics_file_buttons()
            self.update_kinetics_file_buttons()
            self.update_moments_file_buttons()
            self.plot_data()

    def import_c3d_for_kinetics(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Import C3D Files", "", "C3D Files (*.c3d)")
        if file_paths:
            for file_path in file_paths:
                if self.multiline_importer.get_num_files() >= 5:
                    break  # Stop if limit reached
                if self.multiline_importer.import_c3d(file_path):
                    new_idx = self.multiline_importer.get_num_files() - 1

                    # Set default visibility
                    if self.multiline_importer.get_num_files() == 1:
                        self.kinematics_visible_file_index = 0
                        self.kinetics_visible_file_index = 0
                        self.moments_visible_file_index = 0

                    self.kinematics_red_visible_files.add(new_idx)
                    self.kinematics_green_visible_files.add(new_idx)
                    self.kinetics_red_visible_files.add(new_idx)
                    self.kinetics_green_visible_files.add(new_idx)
                    self.moments_red_visible_files.add(new_idx)
                    self.moments_green_visible_files.add(new_idx)
                else:
                    # Show error message for failed import
                    pass
            self.update_kinematics_file_buttons()
            self.update_kinetics_file_buttons()
            self.update_moments_file_buttons()
            self.plot_data()

    def update_kinematics_file_buttons(self):
        # Clear existing buttons
        for button in self.kinematics_file_buttons:
            button.setParent(None)
        self.kinematics_file_buttons = []
        # Clear layout properly, including sub-layouts
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    clear_layout(item.layout())
        clear_layout(self.kinematics_file_buttons_layout)
        # Add new buttons
        for i, file_data in enumerate(self.multiline_importer.imported_files):
            # Create horizontal layout for file button and delete button
            file_layout = QHBoxLayout()
            button = QPushButton(file_data['filename'])
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=i: self.on_kinematics_file_button_clicked(idx))
            file_layout.addWidget(button)
            self.kinematics_file_buttons.append(button)

            # Add delete button
            delete_button = QPushButton()
            delete_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            delete_button.setFixedSize(20, 20)
            delete_button.clicked.connect(lambda checked, idx=i: self.delete_c3d_file(idx))
            file_layout.addWidget(delete_button)

            self.kinematics_file_buttons_layout.addLayout(file_layout)
        # Update visibility based on side filter
        self.update_kinematics_file_buttons_visibility()

    def update_kinetics_file_buttons(self):
        # Clear existing buttons
        for button in self.kinetics_file_buttons:
            button.setParent(None)
        self.kinetics_file_buttons = []
        # Clear layout properly, including sub-layouts
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    clear_layout(item.layout())
        clear_layout(self.kinetics_file_buttons_layout)
        # Add new buttons
        for i, file_data in enumerate(self.multiline_importer.imported_files):
            # Create horizontal layout for file button and delete button
            file_layout = QHBoxLayout()
            button = QPushButton(file_data['filename'])
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=i: self.on_kinetics_file_button_clicked(idx))
            file_layout.addWidget(button)
            self.kinetics_file_buttons.append(button)

            # Add delete button
            delete_button = QPushButton()
            delete_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            delete_button.setFixedSize(20, 20)
            delete_button.clicked.connect(lambda checked, idx=i: self.delete_c3d_file(idx))
            file_layout.addWidget(delete_button)

            self.kinetics_file_buttons_layout.addLayout(file_layout)
        # Update visibility based on side filter
        self.update_kinetics_file_buttons_visibility()

    def update_kinematics_file_buttons_visibility(self):
        for i, button in enumerate(self.kinematics_file_buttons):
            is_visible = False
            if self.kinematics_side_filter == "All":
                is_visible = (self.kinematics_visible_file_index is not None and i == self.kinematics_visible_file_index)
            elif self.kinematics_side_filter == "Red":
                is_visible = (i in self.kinematics_red_visible_files)
            elif self.kinematics_side_filter == "Green":
                is_visible = (i in self.kinematics_green_visible_files)

            button.setChecked(is_visible)

            if self.highlighted_section == 'kinematics' and self.highlighted_line_key and f"_file_{i}" in self.highlighted_line_key:
                if is_visible:
                    button.setStyleSheet("QPushButton { background-color: blue; color: white; }")
                else:
                    # Dehighlight since the line is no longer visible
                    self.gait_cycle_plotter.highlight_line(self.highlighted_line_key, highlight=False)
                    self.highlighted_line_key = None
                    self.highlighted_section = None
                    button.setStyleSheet("QPushButton { background-color: white; color: black; }")
            elif is_visible:
                button.setStyleSheet("QPushButton { background-color: #ADD8E6; color: black; }")
            else:
                button.setStyleSheet("QPushButton { background-color: white; color: black; }")

    def update_kinetics_file_buttons_visibility(self):
        for i, button in enumerate(self.kinetics_file_buttons):
            is_visible = False
            if self.kinetics_side_filter == "All":
                is_visible = (self.kinetics_visible_file_index is not None and i == self.kinetics_visible_file_index)
            elif self.kinetics_side_filter == "Red":
                is_visible = (i in self.kinetics_red_visible_files)
            elif self.kinetics_side_filter == "Green":
                is_visible = (i in self.kinetics_green_visible_files)

            button.setChecked(is_visible)

            if self.highlighted_section == 'kinetics' and self.highlighted_line_key and f"_file_{i}" in self.highlighted_line_key:
                if is_visible:
                    button.setStyleSheet("QPushButton { background-color: blue; color: white; }")
                else:
                    # Dehighlight since the line is no longer visible
                    self.gait_cycle_plotter.highlight_line(self.highlighted_line_key, highlight=False)
                    self.highlighted_line_key = None
                    self.highlighted_section = None
                    button.setStyleSheet("QPushButton { background-color: white; color: black; }")
            elif is_visible:
                button.setStyleSheet("QPushButton { background-color: #ADD8E6; color: black; }")
            else:
                button.setStyleSheet("QPushButton { background-color: white; color: black; }")

    def on_kinematics_file_button_clicked(self, idx):
        if self.kinematics_side_filter == "All":
            if self.kinematics_visible_file_index == idx:
                self.kinematics_visible_file_index = None
            else:
                self.kinematics_visible_file_index = idx
        elif self.kinematics_side_filter == "Red":
            if idx in self.kinematics_red_visible_files:
                self.kinematics_red_visible_files.remove(idx)
            else:
                self.kinematics_red_visible_files.add(idx)
        elif self.kinematics_side_filter == "Green":
            if idx in self.kinematics_green_visible_files:
                self.kinematics_green_visible_files.remove(idx)
            else:
                self.kinematics_green_visible_files.add(idx)
        self.update_kinematics_file_buttons_visibility()
        self.plot_data()

    def on_kinetics_file_button_clicked(self, idx):
        if self.kinetics_side_filter == "All":
            if self.kinetics_visible_file_index == idx:
                self.kinetics_visible_file_index = None
            else:
                self.kinetics_visible_file_index = idx
        elif self.kinetics_side_filter == "Red":
            if idx in self.kinetics_red_visible_files:
                self.kinetics_red_visible_files.remove(idx)
            else:
                self.kinetics_red_visible_files.add(idx)
        elif self.kinetics_side_filter == "Green":
            if idx in self.kinetics_green_visible_files:
                self.kinetics_green_visible_files.remove(idx)
            else:
                self.kinetics_green_visible_files.add(idx)
        self.update_kinetics_file_buttons_visibility()
        self.plot_data()

    def import_c3d_for_moments(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Import C3D Files", "", "C3D Files (*.c3d)")
        if file_paths:
            for file_path in file_paths:
                if self.multiline_importer.get_num_files() >= 5:
                    break  # Stop if limit reached
                if self.multiline_importer.import_c3d(file_path):
                    new_idx = self.multiline_importer.get_num_files() - 1
                    
                    # Set default visibility
                    if self.multiline_importer.get_num_files() == 1:
                        self.kinematics_visible_file_index = 0
                        self.kinetics_visible_file_index = 0
                        self.moments_visible_file_index = 0
                    
                    self.kinematics_red_visible_files.add(new_idx)
                    self.kinematics_green_visible_files.add(new_idx)
                    self.kinetics_red_visible_files.add(new_idx)
                    self.kinetics_green_visible_files.add(new_idx)
                    self.moments_red_visible_files.add(new_idx)
                    self.moments_green_visible_files.add(new_idx)
                else:
                    # Show error message for failed import
                    pass
            self.update_kinematics_file_buttons()
            self.update_kinetics_file_buttons()
            self.update_moments_file_buttons()
            self.plot_data()

    def update_moments_file_buttons(self):
        # Clear existing buttons
        for button in self.moments_file_buttons:
            button.setParent(None)
        self.moments_file_buttons = []
        # Clear layout properly, including sub-layouts
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    clear_layout(item.layout())
        clear_layout(self.moments_file_buttons_layout)
        # Add new buttons
        for i, file_data in enumerate(self.multiline_importer.imported_files):
            # Create horizontal layout for file button and delete button
            file_layout = QHBoxLayout()
            button = QPushButton(file_data['filename'])
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=i: self.on_moments_file_button_clicked(idx))
            file_layout.addWidget(button)
            self.moments_file_buttons.append(button)

            # Add delete button
            delete_button = QPushButton()
            delete_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            delete_button.setFixedSize(20, 20)
            delete_button.clicked.connect(lambda checked, idx=i: self.delete_c3d_file(idx))
            file_layout.addWidget(delete_button)

            self.moments_file_buttons_layout.addLayout(file_layout)
        # Update visibility based on side filter
        self.update_moments_file_buttons_visibility()

    def update_moments_file_buttons_visibility(self):
        for i, button in enumerate(self.moments_file_buttons):
            is_visible = False
            if self.moments_side_filter == "All":
                is_visible = (self.moments_visible_file_index is not None and i == self.moments_visible_file_index)
            elif self.moments_side_filter == "Red":
                is_visible = (i in self.moments_red_visible_files)
            elif self.moments_side_filter == "Green":
                is_visible = (i in self.moments_green_visible_files)

            button.setChecked(is_visible)

            if self.highlighted_section == 'moments' and self.highlighted_line_key and f"_file_{i}" in self.highlighted_line_key:
                if is_visible:
                    button.setStyleSheet("QPushButton { background-color: blue; color: white; }")
                else:
                    # Dehighlight since the line is no longer visible
                    self.gait_cycle_plotter.highlight_line(self.highlighted_line_key, highlight=False)
                    self.highlighted_line_key = None
                    self.highlighted_section = None
                    button.setStyleSheet("QPushButton { background-color: white; color: black; }")
            elif is_visible:
                button.setStyleSheet("QPushButton { background-color: #005A9C; color: black; }")
            else:
                button.setStyleSheet("QPushButton { background-color: white; color: black; }")

    def on_moments_file_button_clicked(self, idx):
        if self.moments_side_filter == "All":
            if self.moments_visible_file_index == idx:
                self.moments_visible_file_index = None
            else:
                self.moments_visible_file_index = idx
        elif self.moments_side_filter == "Red":
            if idx in self.moments_red_visible_files:
                self.moments_red_visible_files.remove(idx)
            else:
                self.moments_red_visible_files.add(idx)
        elif self.moments_side_filter == "Green":
            if idx in self.moments_green_visible_files:
                self.moments_green_visible_files.remove(idx)
            else:
                self.moments_green_visible_files.add(idx)
        self.update_moments_file_buttons_visibility()
        self.plot_data()

    def toggle_main_visibility(self):
        self.main_visible = not self.main_visible
        self.main_toggle_button.setChecked(self.main_visible)
        self.plot_data()

    def import_c3d_for_gait_analysis(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Import C3D Files", "", "C3D Files (*.c3d)")
        if file_paths:
            for file_path in file_paths:
                if self.multiline_importer.get_num_files() >= 5:
                    break  # Stop if limit reached
                if self.multiline_importer.import_c3d(file_path):
                    new_idx = self.multiline_importer.get_num_files() - 1

                    # Set default visibility
                    if self.multiline_importer.get_num_files() == 1:
                        self.kinematics_visible_file_index = 0
                        self.kinetics_visible_file_index = 0
                        self.moments_visible_file_index = 0

                    self.kinematics_red_visible_files.add(new_idx)
                    self.kinematics_green_visible_files.add(new_idx)
                    self.kinetics_red_visible_files.add(new_idx)
                    self.kinetics_green_visible_files.add(new_idx)
                    self.moments_red_visible_files.add(new_idx)
                    self.moments_green_visible_files.add(new_idx)
                else:
                    # Show error message for failed import
                    pass
            self.update_kinematics_file_buttons()
            self.update_kinetics_file_buttons()
            self.update_moments_file_buttons()
            self.plot_data()

    def import_averages(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open PXD", "", "PXD Files (*.pxd)")
        if filename:
            data = PXDExporter.import_averages_static(filename)
            if data:
                self.imported_averages = data
                self.imported_pxd_filename = filename.split('/')[-1].split('\\')[-1]
                self.plot_data()

    def delete_c3d_file(self, idx):
        """Delete a C3D file and adjust indices."""
        if 0 <= idx < len(self.multiline_importer.imported_files):
            # Remove from importer
            del self.multiline_importer.imported_files[idx]

            # Adjust visible indices
            def adjust_set(s):
                new_s = set()
                for i in s:
                    if i > idx:
                        new_s.add(i - 1)
                    elif i < idx:
                        new_s.add(i)
                return new_s

            self.kinematics_red_visible_files = adjust_set(self.kinematics_red_visible_files)
            self.kinematics_green_visible_files = adjust_set(self.kinematics_green_visible_files)
            self.kinetics_red_visible_files = adjust_set(self.kinetics_red_visible_files)
            self.kinetics_green_visible_files = adjust_set(self.kinetics_green_visible_files)
            self.moments_red_visible_files = adjust_set(self.moments_red_visible_files)
            self.moments_green_visible_files = adjust_set(self.moments_green_visible_files)

            # Adjust visible_file_index
            if self.kinematics_visible_file_index is not None:
                if self.kinematics_visible_file_index == idx:
                    self.kinematics_visible_file_index = None
                elif self.kinematics_visible_file_index > idx:
                    self.kinematics_visible_file_index -= 1
            if self.kinetics_visible_file_index is not None:
                if self.kinetics_visible_file_index == idx:
                    self.kinetics_visible_file_index = None
                elif self.kinetics_visible_file_index > idx:
                    self.kinetics_visible_file_index -= 1
            if self.moments_visible_file_index is not None:
                if self.moments_visible_file_index == idx:
                    self.moments_visible_file_index = None
                elif self.moments_visible_file_index > idx:
                    self.moments_visible_file_index -= 1

            # Update buttons
            self.update_kinematics_file_buttons()
            self.update_kinetics_file_buttons()
            self.update_moments_file_buttons()
            self.plot_data()
