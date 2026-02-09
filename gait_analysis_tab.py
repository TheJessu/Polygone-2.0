from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QGridLayout, QLabel, QPushButton, QHBoxLayout, QInputDialog, QComboBox, QFileDialog, QCheckBox
from PyQt5.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from gait_cycle_plotter import GaitCyclePlotter
from pdfExport import PDFExporter
from generic_plotter import EditablePlotWidget
from multiline import MultilineImporter
from pxdExport import PXDExporter

class GaitPlotWidget(EditablePlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class PlotWidget(EditablePlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas.setFixedSize(200, 200)

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

        self.main_visible = True

        self.layout = QVBoxLayout(self)

        # Add export button
        button_layout = QHBoxLayout()
        self.export_pdf_button = QPushButton("Export PDF")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.import_avg_button = QPushButton("Import Averages")
        self.import_avg_button.clicked.connect(self.import_averages)
        button_layout.addWidget(self.import_avg_button)
        button_layout.addWidget(self.export_pdf_button)
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
        self.kinematics_import_button = QPushButton("Import C3D")
        self.kinematics_import_button.clicked.connect(self.import_c3d_for_kinematics)
        dropdown_layout.addWidget(self.kinematics_import_button)
        self.main_toggle_button = QPushButton("Toggle Main C3D")
        self.main_toggle_button.setCheckable(True)
        self.main_toggle_button.setChecked(self.main_visible)
        self.main_toggle_button.clicked.connect(self.toggle_main_visibility)
        dropdown_layout.addWidget(self.main_toggle_button)
        dropdown_layout.addStretch()
        self.kinematics_tab_layout.addLayout(dropdown_layout)
        self.kinematics_file_buttons_layout = QHBoxLayout()
        self.kinematics_tab_layout.addLayout(self.kinematics_file_buttons_layout)
        self.kinematics_layout = QGridLayout()
        self.kinematics_tab_layout.addLayout(self.kinematics_layout)
        self.tab_widget.addTab(self.kinematics_tab, "Gait 1 Kinematics")
        self.kinematics_side_filter = "All"
        self.kinematics_file_buttons = []
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
        self.kinetics_import_button = QPushButton("Import C3D")
        self.kinetics_import_button.clicked.connect(self.import_c3d_for_kinetics)
        dropdown_layout.addWidget(self.kinetics_import_button)
        dropdown_layout.addStretch()
        self.kinetics_tab_layout.addLayout(dropdown_layout)
        self.kinetics_file_buttons_layout = QHBoxLayout()
        self.kinetics_tab_layout.addLayout(self.kinetics_file_buttons_layout)
        self.kinetics_layout = QGridLayout()
        self.kinetics_tab_layout.addLayout(self.kinetics_layout)
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
        self.moments_import_button = QPushButton("Import C3D")
        self.moments_import_button.clicked.connect(self.import_c3d_for_moments)
        dropdown_layout.addWidget(self.moments_import_button)
        dropdown_layout.addStretch()
        self.moments_tab_layout.addLayout(dropdown_layout)
        self.moments_file_buttons_layout = QHBoxLayout()
        self.moments_tab_layout.addLayout(self.moments_file_buttons_layout)
        self.moments_layout = QGridLayout()
        self.moments_tab_layout.addLayout(self.moments_layout)
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
                plot_widget = PlotWidget(self.kinematics_tab)
                plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
                plot_widget.ymin_double_clicked.connect(self.on_ymin_double_clicked)
                plot_widget.ymax_double_clicked.connect(self.on_ymax_double_clicked)
                plot_widget.title_double_clicked.connect(self.on_title_double_clicked)
                self.kinematics_layout.addWidget(plot_widget, row, col)
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
            ('Hip', 'y', 'ANGLES', 'Angle (degrees)'),
            ('Knee', 'y', 'ANGLES', 'Angle (degrees)'),
            ('Ankle', 'y', 'ANGLES', 'Angle (degrees)'),
            ('Hip', 'y', 'MOMENTS', 'Moment (Nm/kg)'),
            ('Knee', 'y', 'MOMENTS', 'Moment (Nm/kg)'),
            ('Ankle', 'y', 'MOMENTS', 'Moment (Nm/kg)'),
            ('Hip', 'z', 'POWERS', 'Power (W/kg)'),
            ('Knee', 'z', 'POWERS', 'Power (W/kg)'),
            ('Ankle', 'z', 'POWERS', 'Power (W/kg)')
        ]
        for i, (group, comp, plot_type, y_label, *unit_factor) in enumerate(plots_config):
            row = i // 3
            col = i % 3
            plot_widget = GaitPlotWidget(self.kinetics_tab)
            plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
            self.kinetics_layout.addWidget(plot_widget, row, col)
            self.kinetics_plots.append((plot_widget, group, comp, plot_type, y_label, unit_factor[0] if unit_factor else 1))

    def setup_moments_plots(self):
        # 3x3 grid for hip, knee, ankle x,y,z moments
        groups = ['Hip', 'Knee', 'Ankle']
        components = ['x', 'y', 'z']
        row = 0
        for group in groups:
            col = 0
            for comp in components:
                plot_widget = GaitPlotWidget(self.moments_tab)
                plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
                plot_widget.ymin_double_clicked.connect(self.on_ymin_double_clicked)
                plot_widget.ymax_double_clicked.connect(self.on_ymax_double_clicked)
                plot_widget.title_double_clicked.connect(self.on_title_double_clicked)
                self.moments_layout.addWidget(plot_widget, row, col)
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
        for plot_widget, *_ in self.kinematics_plots:
            if self.gait_cycles:
                for side in ['left', 'right']:
                    for start, end in self.gait_cycles.get(side, []):
                        if start <= self.current_frame < end:
                            cycle_len = end - start
                            if cycle_len > 0:
                                percentage = (self.current_frame - start) / cycle_len * 100
                                vline = plot_widget.ax.axvline(x=percentage, color='red', linestyle='--', linewidth=2)
                                self.vlines.append(vline)
                                break
                    if self.vlines:
                        break
            plot_widget.canvas.draw()

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
                title = f'{group} - {"Knee Flexion-Extension" if comp == "y" else comp.upper()}'
            elif group.lower() == 'ankle':
                title = f'{group} - {"Dorsi-Plantarflexion" if comp == "y" else comp.upper()}'
            elif group.lower() == 'footprogress':
                title = f'{group} - {"Dorsi-Plantarflexion" if comp == "y" else "Foot Progression" if comp == "z" else comp.upper()}'
            plot_widget.ax.set_title(title)
            plot_widget.ax.set_xlabel('Gait Cycle (%)')
            if self.main_visible:
                if self.imported_averages and 'ANGLES' in self.imported_averages:
                    if group in self.imported_averages['ANGLES'] and comp in self.imported_averages['ANGLES'][group]:
                        avg = self.imported_averages['ANGLES'][group][comp]
                        mean = np.array(avg['mean'])
                        std = np.array(avg['std'])
                        x = np.linspace(0, 100, len(mean))
                        plot_widget.ax.fill_between(x, mean - std, mean + std, color='grey', alpha=0.3)
                        plot_widget.ax.plot(x, mean, color='grey', linestyle='--', linewidth=1)
                self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, 'ANGLES', '', self.current_frame, component=comp, side_filter=self.kinematics_side_filter)

            # Plot multiline data
            if self.multiline_importer.get_num_files() > 0:
                for i, file_data in enumerate(self.multiline_importer.imported_files):
                    if self.kinematics_side_filter == "All":
                        if i == self.kinematics_visible_file_index:
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'ANGLES', '', self.current_frame, component=comp, side_filter="Red", color=self.red_colors[0])
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'ANGLES', '', self.current_frame, component=comp, side_filter="Green", color=self.green_colors[0])
                    elif self.kinematics_side_filter == "Red":
                        if i in self.kinematics_red_visible_files:
                            idx_in_red = list(self.kinematics_red_visible_files).index(i)
                            color = self.red_colors[idx_in_red % len(self.red_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'ANGLES', '', self.current_frame, component=comp, side_filter="Red", color=color)
                    elif self.kinematics_side_filter == "Green":
                        if i in self.kinematics_green_visible_files:
                            idx_in_green = list(self.kinematics_green_visible_files).index(i)
                            color = self.green_colors[idx_in_green % len(self.green_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'ANGLES', '', self.current_frame, component=comp, side_filter="Green", color=color)
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
            plot_widget.figure.subplots_adjust(left=0.25, right=0.9, top=0.85, bottom=0.15)
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
            plot_widget.ax.set_title(title)
            plot_widget.ax.set_xlabel('Gait Cycle (%)')
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
                self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, plot_type, y_label, self.current_frame, component=comp, body_mass=self.body_mass, side_filter=self.kinetics_side_filter)

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
                for i, file_data in enumerate(self.multiline_importer.imported_files):
                    if self.kinetics_side_filter == "All":
                        if i == self.kinetics_visible_file_index:
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], plot_type, '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Red", color=self.red_colors[0])
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], plot_type, '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Green", color=self.green_colors[0])
                    elif self.kinetics_side_filter == "Red":
                        if i in self.kinetics_red_visible_files:
                            idx_in_red = list(self.kinetics_red_visible_files).index(i)
                            color = self.red_colors[idx_in_red % len(self.red_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], plot_type, '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Red", color=color)
                    elif self.kinetics_side_filter == "Green":
                        if i in self.kinetics_green_visible_files:
                            idx_in_green = list(self.kinetics_green_visible_files).index(i)
                            color = self.green_colors[idx_in_green % len(self.green_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], plot_type, '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Green", color=color)
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
            plot_widget.ax.set_title(title)
            plot_widget.ax.set_xlabel('Gait Cycle (%)')
            if self.imported_averages and 'MOMENTS' in self.imported_averages:
                if group in self.imported_averages['MOMENTS'] and comp in self.imported_averages['MOMENTS'][group]:
                    avg = self.imported_averages['MOMENTS'][group][comp]
                    mean = np.array(avg['mean'])
                    std = np.array(avg['std'])
                    x = np.linspace(0, 100, len(mean))
                    plot_widget.ax.fill_between(x, mean - std, mean + std, color='grey', alpha=0.3)
                    plot_widget.ax.plot(x, mean, color='grey', linestyle='--', linewidth=1)
            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, self.markers_data, self.marker_labels, self.marker_types, group, self.gait_cycles, 'MOMENTS', 'Moment (Nm/kg)', self.current_frame, component=comp, body_mass=self.body_mass, side_filter=self.moments_side_filter)

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
                for i, file_data in enumerate(self.multiline_importer.imported_files):
                    if self.moments_side_filter == "All":
                        if i == self.moments_visible_file_index:
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'MOMENTS', '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Red", color=self.red_colors[0])
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'MOMENTS', '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Green", color=self.green_colors[0])
                    elif self.moments_side_filter == "Red":
                        if i in self.moments_red_visible_files:
                            idx_in_red = list(self.moments_red_visible_files).index(i)
                            color = self.red_colors[idx_in_red % len(self.red_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'MOMENTS', '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Red", color=color)
                    elif self.moments_side_filter == "Green":
                        if i in self.moments_green_visible_files:
                            idx_in_green = list(self.moments_green_visible_files).index(i)
                            color = self.green_colors[idx_in_green % len(self.green_colors)]
                            self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, file_data['markers_data'], file_data['marker_labels'], file_data['marker_types'], group, file_data['gait_cycles'], 'MOMENTS', '', self.current_frame, component=comp, body_mass=file_data['body_mass'], side_filter="Green", color=color)
            plot_widget.canvas.draw()

        # Adjust subplot margins to prevent cut-off labels for moments
        for plot_widget, *_ in self.moments_plots:
            plot_widget.figure.subplots_adjust(left=0.25, right=0.9, top=0.85, bottom=0.15)
            plot_widget.canvas.draw()

    def on_plot_double_clicked(self, plot_widget):
        # Simple zoom, but since fixed layout, maybe just ignore or implement basic zoom
        pass

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
        self.plot_data()

    def on_kinetics_side_changed(self, side):
        self.kinetics_side_filter = side
        self.plot_data()

    def on_moments_side_changed(self, side):
        self.moments_side_filter = side
        self.plot_data()

    def import_c3d_for_kinematics(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import C3D File", "", "C3D Files (*.c3d)")
        if file_path:
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

                self.update_kinematics_file_buttons()
                self.update_kinetics_file_buttons()
                self.update_moments_file_buttons()
                self.plot_data()
            else:
                # Show error message
                pass

    def import_c3d_for_kinetics(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import C3D File", "", "C3D Files (*.c3d)")
        if file_path:
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

                self.update_kinematics_file_buttons()
                self.update_kinetics_file_buttons()
                self.update_moments_file_buttons()
                self.plot_data()
            else:
                # Show error message
                pass

    def update_kinematics_file_buttons(self):
        # Clear existing buttons
        for button in self.kinematics_file_buttons:
            button.setParent(None)
        self.kinematics_file_buttons = []
        # Add new buttons
        for i, file_data in enumerate(self.multiline_importer.imported_files):
            button = QPushButton(file_data['filename'])
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=i: self.on_kinematics_file_button_clicked(idx))
            self.kinematics_file_buttons_layout.addWidget(button)
            self.kinematics_file_buttons.append(button)
        # Update visibility based on side filter
        self.update_kinematics_file_buttons_visibility()

    def update_kinetics_file_buttons(self):
        # Clear existing buttons
        for button in self.kinetics_file_buttons:
            button.setParent(None)
        self.kinetics_file_buttons = []
        # Add new buttons
        for i, file_data in enumerate(self.multiline_importer.imported_files):
            button = QPushButton(file_data['filename'])
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=i: self.on_kinetics_file_button_clicked(idx))
            self.kinetics_file_buttons_layout.addWidget(button)
            self.kinetics_file_buttons.append(button)
        # Update visibility based on side filter
        self.update_kinetics_file_buttons_visibility()

    def update_kinematics_file_buttons_visibility(self):
        if self.kinematics_side_filter == "All":
            for button in self.kinematics_file_buttons:
                button.setVisible(True)
            # Only one visible at a time
            for i, button in enumerate(self.kinematics_file_buttons):
                button.setChecked(i == self.kinematics_visible_file_index)
        elif self.kinematics_side_filter == "Red":
            for button in self.kinematics_file_buttons:
                button.setVisible(True)
                button.setChecked(button in self.kinematics_red_visible_files)
        elif self.kinematics_side_filter == "Green":
            for button in self.kinematics_file_buttons:
                button.setVisible(True)
                button.setChecked(button in self.kinematics_green_visible_files)
        # Set button colors based on checked state and side filter
        for button in self.kinematics_file_buttons:
            if button.isChecked():
                if self.kinematics_side_filter == "Red":
                    button.setStyleSheet(f"QPushButton {{ background-color: {self.red_colors[0]}; color: white; }}")
                elif self.kinematics_side_filter == "Green":
                    button.setStyleSheet(f"QPushButton {{ background-color: {self.green_colors[0]}; color: white; }}")
                else:
                    button.setStyleSheet("QPushButton { background-color: blue; color: white; }")
            else:
                button.setStyleSheet("QPushButton { background-color: white; color: black; }")

    def update_kinetics_file_buttons_visibility(self):
        if self.kinetics_side_filter == "All":
            for button in self.kinetics_file_buttons:
                button.setVisible(True)
            # Only one visible at a time
            for i, button in enumerate(self.kinetics_file_buttons):
                button.setChecked(i == self.kinetics_visible_file_index)
        elif self.kinetics_side_filter == "Red":
            for button in self.kinetics_file_buttons:
                button.setVisible(True)
                button.setChecked(button in self.kinetics_red_visible_files)
        elif self.kinetics_side_filter == "Green":
            for button in self.kinetics_file_buttons:
                button.setVisible(True)
                button.setChecked(button in self.kinetics_green_visible_files)
        # Set button colors based on checked state and side filter
        for button in self.kinetics_file_buttons:
            if button.isChecked():
                if self.kinetics_side_filter == "Red":
                    button.setStyleSheet(f"QPushButton {{ background-color: {self.red_colors[0]}; color: white; }}")
                elif self.kinetics_side_filter == "Green":
                    button.setStyleSheet(f"QPushButton {{ background-color: {self.green_colors[0]}; color: white; }}")
                else:
                    button.setStyleSheet("QPushButton { background-color: blue; color: white; }")
            else:
                button.setStyleSheet("QPushButton { background-color: white; color: black; }")

    def on_kinematics_file_button_clicked(self, idx):
        if self.kinematics_side_filter == "All":
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
        file_path, _ = QFileDialog.getOpenFileName(self, "Import C3D File", "", "C3D Files (*.c3d)")
        if file_path:
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

                self.update_kinematics_file_buttons()
                self.update_kinetics_file_buttons()
                self.update_moments_file_buttons()
                self.plot_data()
            else:
                # Show error message
                pass

    def update_moments_file_buttons(self):
        # Clear existing buttons
        for button in self.moments_file_buttons:
            button.setParent(None)
        self.moments_file_buttons = []
        # Add new buttons
        for i, file_data in enumerate(self.multiline_importer.imported_files):
            button = QPushButton(file_data['filename'])
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=i: self.on_moments_file_button_clicked(idx))
            self.moments_file_buttons_layout.addWidget(button)
            self.moments_file_buttons.append(button)
        # Update visibility based on side filter
        self.update_moments_file_buttons_visibility()

    def update_moments_file_buttons_visibility(self):
        if self.moments_side_filter == "All":
            for button in self.moments_file_buttons:
                button.setVisible(True)
            # Only one visible at a time
            for i, button in enumerate(self.moments_file_buttons):
                button.setChecked(i == self.moments_visible_file_index)
        elif self.moments_side_filter == "Red":
            for button in self.moments_file_buttons:
                button.setVisible(True)
                button.setChecked(button in self.moments_red_visible_files)
        elif self.moments_side_filter == "Green":
            for button in self.moments_file_buttons:
                button.setVisible(True)
                button.setChecked(button in self.moments_green_visible_files)
        # Set button colors based on checked state and side filter
        for button in self.moments_file_buttons:
            if button.isChecked():
                if self.moments_side_filter == "Red":
                    button.setStyleSheet(f"QPushButton {{ background-color: {self.red_colors[0]}; color: white; }}")
                elif self.moments_side_filter == "Green":
                    button.setStyleSheet(f"QPushButton {{ background-color: {self.green_colors[0]}; color: white; }}")
                else:
                    button.setStyleSheet("QPushButton { background-color: blue; color: white; }")
            else:
                button.setStyleSheet("QPushButton { background-color: white; color: black; }")

    def on_moments_file_button_clicked(self, idx):
        if self.moments_side_filter == "All":
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

    def import_averages(self):
        data = PXDExporter.import_averages(self)
        if data:
            self.imported_averages = data
            self.plot_data()
