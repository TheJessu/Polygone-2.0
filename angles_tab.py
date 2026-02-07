from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QScrollArea, QGridLayout, QInputDialog
from PyQt5.QtCore import pyqtSignal, QEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from gait_cycle_plotter import GaitCyclePlotter
from generic_plotter import GenericDataPlotter, EditablePlotWidget

class AnglesPlotWidget(EditablePlotWidget):
    line_clicked = pyqtSignal(object)  # Signal for line clicks, emits (plotter_type, key)

    def __init__(self, angles_plotter, gait_cycle_plotter, parent=None):
        super().__init__(parent)
        self.angles_plotter = angles_plotter
        self.gait_cycle_plotter = gait_cycle_plotter
        self.lines = {}  # Lines for this plot
        self.scrubber_lines = {}  # side to scrubber line

        # Override the pick event to handle line picking
        self.canvas.mpl_connect('pick_event', self.on_line_pick)

    def on_line_pick(self, event):
        # Handle line picking
        if hasattr(event.artist, 'get_label'):
            # Check this plot's lines first
            for key, (line, _, _, _) in self.lines.items():
                if line == event.artist:
                    self.line_clicked.emit(('angles', key))
                    return
            # Check angles_plotter lines
            for key, (line, _, _, _) in self.angles_plotter.lines.items():
                if line == event.artist:
                    self.line_clicked.emit(('angles', key))
                    return
            # Check gait_cycle_plotter lines
            for line_key, (line, _, _, _) in self.gait_cycle_plotter.lines.items():
                if line == event.artist:
                    self.line_clicked.emit(('gait', line_key))
                    return
        # Call parent on_pick for text editing
        super().on_pick(event)

    def enterEvent(self, event):
        self.ax.set_facecolor('#f0f0f0')
        self.canvas.draw()

    def leaveEvent(self, event):
        self.ax.set_facecolor('white')
        self.canvas.draw()

class AnglesTab(QWidget):
    editable_value_changed = pyqtSignal(str, str, dict)  # key, type, value_dict

    def __init__(self):
        super().__init__()
        self.angles_plotter = GenericDataPlotter('ANGLES')
        self.gait_cycle_plotter = GaitCyclePlotter()
        self.gait_cycles = None
        self.frame_range = None

        self.layout = QVBoxLayout(self)

        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Select Component:"))
        self.dropdown = QComboBox()
        self.dropdown.addItem("All")
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
        self.editable_values = {}

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

    def set_editable_values(self, editable_values):
        self.editable_values = editable_values

    def load_data(self, markers_data, marker_types, marker_labels, body_mass=None):
        self.body_mass = body_mass
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
            default_visible = group not in grey_out_groups
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
        self.highlighted_line = None  # Clear highlight on replot
        self.value_label.setText("")  # Clear info on replot
        self.angles_plotter.lines.clear()
        self.gait_cycle_plotter.lines = {}
        for plot in self.plots:
            plot.scrubber_lines = {}

        selected_component = self.dropdown.currentText()
        desired_order = ['Spine', 'Pelvis', 'Hip', 'Knee', 'Footprogress', 'Absankl', 'Ankle', 'Elbow', 'Shoulder', 'Thorax', 'Wrist']
        visible_groups = [g for g in self.groups if self.group_visibility.get(g, True)]
        groups = sorted(visible_groups, key=lambda g: (0 if g in desired_order else 1, desired_order.index(g) if g in desired_order else 0))
        use_gait_cycle = self.gait_cycles and (self.gait_cycles['left'] or self.gait_cycles['right'])

        if self.zoomed_plot:
            self.zoomed_plot = None
            for p in self.plots:
                p.show()

        row, col = 0, 0
        components_to_plot = ['x', 'y', 'z'] if selected_component == "All" else [selected_component.lower()]
        for group in groups:
            for component in components_to_plot:
                plot_widget = self.add_plot(row, col)
                title = f'{group} - {component.upper()}'
                if group.lower() == 'spine':
                    title = f'{group} - {"Trunk Sway" if component == "x" else "Trunk Tilt" if component == "y" else "Trunk Rotation"}'
                elif group.lower() == 'pelvis':
                    title = f'{group} - {"Pelvic Obliquity" if component == "x" else "Pelvic Tilt" if component == "y" else "Pelvic Rotation"}'
                elif group.lower() == 'hip':
                    title = f'{group} - {"Hip Ab-Adduction" if component == "x" else "Hip Flexion-Extension" if component == "y" else "Hip Rotation"}'
                elif group.lower() == 'knee':
                    title = f'{group} - {"Knee Flexion-Extension" if component == "y" else "Knee Rotation" if component == "z" else "Knee Valg/Varus"}'
                elif group.lower() == 'footprogress':
                    title = f'{group} - {"Dorsi-Plantarflexion" if component == "y" else "Foot Progression" if component == "z" else component.upper()}'
                plot_widget.ax.set_xlabel('Frame' if not use_gait_cycle else 'Gait Cycle (%)', fontsize=8, labelpad=-1)
                if use_gait_cycle:
                    self.gait_cycle_plotter.plot_gait_cycle_data(plot_widget.ax, markers_data, marker_labels, marker_types, group, self.gait_cycles, 'ANGLES', '', current_frame, component=component, plot_widget=plot_widget)
                    plot_widget.ax.set_xlim(0, 100)
                else:
                    self.angles_plotter.plot_data(plot_widget.ax, markers_data, marker_labels, marker_types, current_frame, group, frame_range, 'degrees', component, plot_widget=plot_widget)
                if plot_current_frame is not None and not use_gait_cycle:
                    self.vlines.append(plot_widget.ax.axvline(x=plot_current_frame, color='red', linestyle='--', linewidth=1))

                # Clear any existing text labels to prevent overlap
                for text in list(plot_widget.ax.texts):
                    text.remove()

                if component == 'x':
                    if group.lower() in ['spine', 'pelvis']:
                        plot_widget.ax.text(-0.05, 0.25, 'Down', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.50, 'deg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.75, 'Up', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    elif group.lower() in ['knee']:
                        plot_widget.ax.text(-0.05, 0.25, 'Val', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.50, 'deg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.75, 'Var', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    else:  # hip, knee, footprogress
                        plot_widget.ax.text(-0.05, 0.25, 'Abd', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.50, 'deg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.75, 'Add', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                elif component == 'y':
                    if group.lower() in ['spine', 'pelvis']:
                        plot_widget.ax.text(-0.05, 0.25, 'Post', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.50, 'deg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.75, 'Ant', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    elif group.lower() in ['hip', 'knee']:
                        plot_widget.ax.text(-0.05, 0.25, 'Ext', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.50, 'deg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.75, 'Flex', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    else:  # footprogress
                        plot_widget.ax.text(-0.05, 0.25, 'Plan', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.50, 'deg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                        plot_widget.ax.text(-0.05, 0.75, 'Dors', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                elif component == 'z':
                    plot_widget.ax.text(-0.05, 0.25, 'Ext', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.50, 'deg', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                    plot_widget.ax.text(-0.05, 0.75, 'Int', transform=plot_widget.ax.transAxes, ha='right', va='center', fontsize=8)
                plot_widget.ax.set_box_aspect(1)
                # Determine default ymin, ymax based on group and component
                if group.lower() == 'spine':
                    ymin, ymax = -20, 20
                elif group.lower() == 'pelvis':
                    if component == 'x':
                        ymin, ymax = -20, 20
                    elif component == 'y':
                        ymin, ymax = -5, 35
                    elif component == 'z':
                        ymin, ymax = -30, 30
                elif group.lower() == 'hip':
                    if component == 'x':
                        ymin, ymax = -15, 20
                    elif component == 'y':
                        ymin, ymax = -15, 60
                    elif component == 'z':
                        ymin, ymax = -30, 40
                elif group.lower() == 'knee':
                    ymin, ymax = -15, 90
                elif group.lower() == 'footprogress':
                    ymin, ymax = -40, 40
                else:
                    ymin, ymax = -50, 50  # default

                # Check for edited values
                plot_key = f"ANGLES_{group}_{component}"
                plot_widget.plot_key = plot_key
                if plot_key in self.editable_values:
                    edited = self.editable_values[plot_key]
                    ymin = edited.get('ymin', ymin)
                    ymax = edited.get('ymax', ymax)
                    if 'title' in edited:
                        title = edited['title']

                plot_widget.ax.set_title(title, fontsize=10)
                plot_widget.ax.set_ylim(ymin, ymax)
                # Set y-ticks to only show min and max
                plot_widget.ax.set_yticks([ymin, ymax])
                # Always add a thick, darker grey line at y=0 if within range
                if ymin <= 0 <= ymax:
                    plot_widget.ax.axhline(y=0, color='#555555', linestyle='-', linewidth=1.5, alpha=0.7)
                # Add horizontal grid lines at every 10 units in both directions from 0
                max_abs = int(max(abs(ymin) if np.isfinite(ymin) else 50, abs(ymax) if np.isfinite(ymax) else 50))
                for step in range(10, max_abs + 10, 10):
                    if ymin <= step <= ymax:
                        plot_widget.ax.axhline(y=step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
                    if ymin <= -step <= ymax:
                        plot_widget.ax.axhline(y=-step, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
                plot_widget.canvas.draw()
                plot_widget.add_editable_texts(ymin, ymax, title)
        self.plot_layout.invalidate()
        self.plot_layout.activate()
        self.plot_container.adjustSize()
        self.plot_container.update()
        self.scroll_area.update()

        # Adjust subplot margins to prevent cut-off labels
        for plot in self.plots:
            plot.figure.subplots_adjust(left=0.25, right=0.9, top=0.85, bottom=0.15)
            plot.canvas.draw()


    def add_plot(self, row, col):
        plot_widget = AnglesPlotWidget(self.angles_plotter, self.gait_cycle_plotter, self.plot_container)
        plot_widget.plot_double_clicked.connect(self.on_plot_double_clicked)
        plot_widget.ymin_double_clicked.connect(self.on_ymin_double_clicked)
        plot_widget.ymax_double_clicked.connect(self.on_ymax_double_clicked)
        plot_widget.title_double_clicked.connect(self.on_title_double_clicked)
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
        self.plot_layout.invalidate()
        self.plot_layout.activate()
        self.plot_container.adjustSize()
        self.plot_container.update()
        self.scroll_area.update()

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
            if prev_plotter_type == 'angles':
                self.angles_plotter.highlight_line(prev_key, highlight=False)
            elif prev_plotter_type == 'gait':
                self.gait_cycle_plotter.highlight_line(prev_key, highlight=False)

        # Highlight new line
        if plotter_type == 'angles':
            self.angles_plotter.highlight_line(key, highlight=True)
        elif plotter_type == 'gait':
            self.gait_cycle_plotter.highlight_line(key, highlight=True)
        self.highlighted_line = line_info

        # Update display info
        if plotter_type == 'angles':
            info = self.angles_plotter.get_line_info(key, self.current_frame, self.gait_cycles)
        elif plotter_type == 'gait':
            info = self.gait_cycle_plotter.get_line_info(key, self.current_frame, self.gait_cycles, 'ANGLES')
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

        # Update scrubbers
        if self.gait_cycles and (self.gait_cycles.get('left') or self.gait_cycles.get('right')):
            for plot in self.plots:
                if hasattr(plot, 'scrubber_lines'):
                    for side, scrubber in plot.scrubber_lines.items():
                        cycles = self.gait_cycles.get(side, [])
                        percentage = 0
                        is_in_cycle = False
                        for start, end in cycles:
                            if start <= frame_index < end:
                                cycle_len = end - start
                                if cycle_len > 0:
                                    percentage = (frame_index - start) / cycle_len * 100
                                is_in_cycle = True
                                break
                        scrubber.set_xdata([percentage])
                        scrubber.set_visible(is_in_cycle)

        # Update highlighted line info if any
        if self.highlighted_line is not None:
            plotter_type, key = self.highlighted_line
            if plotter_type == 'angles':
                info = self.angles_plotter.get_line_info(key, self.current_frame, self.gait_cycles)
            elif plotter_type == 'gait':
                info = self.gait_cycle_plotter.get_line_info(key, self.current_frame, self.gait_cycles, 'ANGLES')
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

    def on_ymin_double_clicked(self, plot_widget):
        # Handle ymin editing
        # Find which plot this is
        for i, pw in enumerate(self.plots):
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
        for i, pw in enumerate(self.plots):
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
        for i, pw in enumerate(self.plots):
            if pw == plot_widget:
                # Get current title
                current_title = pw.ax.get_title()
                # Open input dialog
                text, ok = QInputDialog.getText(self, 'Edit Title', f'Enter new title (current: {current_title}):')
                if ok and text:
                    # Update the plot title directly
                    pw.ax.set_title(text)
                    pw.canvas.draw()
                    # Emit signal to update editable values
                    key = pw.plot_key
                    self.editable_value_changed.emit(key, 'title', {'title': text})
                break

    def clear_data(self):
        self.clear_plots()
        self.vlines = []
        self.value_label.setText("")
        self.gait_info_label.setText("")
        self.angles_plotter.lines = {}
        self.gait_cycle_plotter.lines = {}
        self.highlighted_line = None
