import numpy as np
import c3d
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, QGridLayout, QFileDialog, QScrollArea, QLabel, QComboBox, QProgressDialog
from PyQt5.QtCore import Qt
from generic_plotter import EditablePlotWidget
from pxdExport import PXDExporter

class AverageSubTab(QWidget):
    def __init__(self, plot_type):
        super().__init__()
        self.plot_type = plot_type
        self.layout = QVBoxLayout(self)
        
        # Dropdown for component selection
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Select Component:"))
        self.dropdown = QComboBox()
        self.dropdown.addItems(["All", "X", "Y", "Z"])
        self.dropdown.currentTextChanged.connect(self.update_layout)
        dropdown_layout.addWidget(self.dropdown)
        dropdown_layout.addStretch()
        self.layout.addLayout(dropdown_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        self.plot_container = QWidget()
        self.plot_layout = QGridLayout(self.plot_container)
        self.scroll_area.setWidget(self.plot_container)
        
        self.plots = [] 
        self.data = {} # Stores aggregated data: data[group][component] = list of arrays
        
        # Default groups to show empty plots
        if plot_type == 'ANGLES':
            self.groups = ['Spine', 'Pelvis', 'Hip', 'Knee', 'Ankle', 'Footprogress']
        elif plot_type in ['MOMENTS', 'POWERS']:
            self.groups = ['Hip', 'Knee', 'Ankle']
        else:
            self.groups = []
            
        self.update_layout()

    def update_layout(self):
        # Clear existing plots
        for i in reversed(range(self.plot_layout.count())): 
            item = self.plot_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        self.plots = []
        
        selected_component = self.dropdown.currentText()
        components = ['x', 'y', 'z'] if selected_component == "All" else [selected_component.lower()]
        
        row = 0
        col = 0
        
        for group in self.groups:
            for comp in components:
                plot_widget = EditablePlotWidget()
                self.setup_plot_appearance(plot_widget, group, comp)
                
                # Plot data if available
                if group in self.data and comp in self.data[group]:
                    self.plot_average(plot_widget, self.data[group][comp])
                
                self.plot_layout.addWidget(plot_widget, row, col)
                self.plots.append(plot_widget)
                
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
        
        self.plot_container.adjustSize()

    def setup_plot_appearance(self, plot_widget, group, component):
        ax = plot_widget.ax
        title = f'{group} - {component.upper()}'
        
        # Copy title logic from original tabs
        if self.plot_type == 'ANGLES':
            if group.lower() == 'spine':
                title = f'{group} - {"Trunk Sway" if component == "x" else "Trunk Tilt" if component == "y" else "Trunk Rotation"}'
            elif group.lower() == 'pelvis':
                title = f'{group} - {"Pelvic Obliquity" if component == "x" else "Pelvic Tilt" if component == "y" else "Pelvic Rotation"}'
            elif group.lower() == 'hip':
                title = f'{group} - {"Hip Ab-Adduction" if component == "x" else "Hip Flexion-Extension" if component == "y" else "Hip Rotation"}'
            elif group.lower() == 'knee':
                title = f'{group} - {"Knee Flexion-Extension" if component == "y" else "Knee Rotation" if component == "z" else "Knee Valg/Varus"}'
            elif group.lower() == 'footprogress':
                title = f'{group} - {" Foot Dorsi-Plantarflexion" if component == "y" else "Foot Progression" if component == "z" else component.upper()}'
            elif group.lower() == 'ankle':
                title = f'{group} - {"Ankle Valg/Varus" if component == "x" else "Dorsi-Plantarflexion" if component == "y" else component.upper()}'
        elif self.plot_type == 'MOMENTS':
             if group.lower() == 'hip' and component == 'y':
                title = f'{group} - Hip Flex-Ext Moment'
             elif group.lower() == 'hip' and component == 'x':
                title = f'{group} - Hip Ab-Add Moment'
             elif group.lower() == 'hip' and component == 'z':
                title = f'{group} - Hip Rotation Moment'
             elif group.lower() == 'knee' and component == 'y':
                title = f'{group} - Knee Flex-Ext Moment'
             elif group.lower() == 'knee' and component == 'x':
                title = f'{group} - Knee Valg-Var Moment'
             elif group.lower() == 'knee' and component == 'z':
                title = f'{group} - Knee Rotation Moment'
             elif group.lower() == 'ankle' and component == 'y':
                title = f'{group} - Dors-Plan Moment'
             elif group.lower() == 'ankle' and component == 'x':
                title = f'{group} - Ankle Ab-Add Moment'
             elif group.lower() == 'ankle' and component == 'z':
                title = f'{group} - Ankle Rotation Moment'
        elif self.plot_type == 'POWERS':
            if group.lower() == 'hip' and component == 'z':
                title = 'Hip Power'
            elif group.lower() == 'knee' and component == 'z':
                title = 'Knee Power'
            elif group.lower() == 'ankle' and component == 'z':
                title = 'Ankle Power'

        ax.set_title(title, fontsize=10)
        ax.set_xlabel('Gait Cycle (%)', fontsize=8)
        
        # Set Y Label
        if self.plot_type == 'POWERS':
            ax.set_ylabel('Power (W/kg)')
        elif self.plot_type == 'MOMENTS':
            ax.set_ylabel('Moment (Nm/kg)')
        elif self.plot_type == 'ANGLES':
            ax.set_ylabel('Angle (degrees)')

        # Set limits and text labels
        ymin, ymax = -50, 50
        if self.plot_type == 'ANGLES':
             if group.lower() == 'spine': ymin, ymax = -20, 20
             elif group.lower() == 'pelvis':
                 if component == 'x': ymin, ymax = -20, 20
                 elif component == 'y': ymin, ymax = -5, 35
                 elif component == 'z': ymin, ymax = -30, 30
             elif group.lower() == 'hip':
                 if component == 'x': ymin, ymax = -15, 20
                 elif component == 'y': ymin, ymax = -15, 60
                 elif component == 'z': ymin, ymax = -30, 40
             elif group.lower() == 'knee': ymin, ymax = -15, 90
             elif group.lower() == 'footprogress': ymin, ymax = -40, 40
             
             # Text labels
             if component == 'x':
                if group.lower() in ['spine', 'pelvis']:
                    ax.text(-0.05, 0.25, 'Down', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Up', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                elif group.lower() in ['knee']:
                    ax.text(-0.05, 0.25, 'Val', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Var', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                else:
                    ax.text(-0.05, 0.25, 'Abd', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Add', transform=ax.transAxes, ha='right', va='center', fontsize=8)
             elif component == 'y':
                if group.lower() in ['spine', 'pelvis']:
                    ax.text(-0.05, 0.25, 'Post', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Ant', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                elif group.lower() in ['hip', 'knee']:
                    ax.text(-0.05, 0.25, 'Ext', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Flex', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                else:
                    ax.text(-0.05, 0.25, 'Plan', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Dors', transform=ax.transAxes, ha='right', va='center', fontsize=8)
             elif component == 'z':
                ax.text(-0.05, 0.25, 'Ext', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.50, 'deg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.75, 'Int', transform=ax.transAxes, ha='right', va='center', fontsize=8)

        elif self.plot_type == 'MOMENTS':
            ymin, ymax = -1.0, 1.0
            if group.lower() == 'hip':
                if component == 'y': ymin, ymax = -1.0, 2.0
                elif component == 'z': ymin, ymax = -0.5, 0.5
            elif group.lower() == 'knee':
                if component == 'y': ymin, ymax = -1.0, 2.0
                elif component == 'z': ymin, ymax = -0.5, 0.5
            elif group.lower() == 'ankle':
                if component == 'x': ymin, ymax = -0.5, 0.5
                elif component == 'y': ymin, ymax = -1.0, 2.0
                elif component == 'z': ymin, ymax = -0.5, 0.5
            
            # Text labels
            if component == 'x':
                if group.lower() in ['hip', 'ankle']:
                    ax.text(-0.05, 0.25, 'Add', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'Nm/kg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Abd', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                else:
                    ax.text(-0.05, 0.25, 'Var', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'Nm/kg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Valg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
            elif component == 'y':
                if group.lower() == 'ankle':
                    ax.text(-0.05, 0.25, 'Dors', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'Nm/kg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Plant', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                elif group.lower() in ['hip', 'knee']:
                    ax.text(-0.05, 0.25, 'Flex', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.50, 'Nm/kg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                    ax.text(-0.05, 0.75, 'Ext', transform=ax.transAxes, ha='right', va='center', fontsize=8)
            elif component == 'z':
                ax.text(-0.05, 0.25, 'Int', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.50, 'Nm/kg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.75, 'Ext', transform=ax.transAxes, ha='right', va='center', fontsize=8)

        elif self.plot_type == 'POWERS':
            ymin, ymax = -2.0, 3.0
            if component == 'z':
                ax.text(-0.05, 0.25, 'Abs', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.50, 'W/kg', transform=ax.transAxes, ha='right', va='center', fontsize=8)
                ax.text(-0.05, 0.75, 'Gen', transform=ax.transAxes, ha='right', va='center', fontsize=8)

        ax.set_ylim(ymin, ymax)
        ax.set_yticks([ymin, ymax])
        ax.set_xlim(0, 100)
        
        # Grid lines
        if ymin <= 0 <= ymax:
            ax.axhline(y=0, color='#555555', linestyle='-', linewidth=1.5, alpha=0.7)
        
        # Add horizontal grid lines
        max_abs = max(abs(ymin), abs(ymax))
        step = 10 if self.plot_type == 'ANGLES' else 0.5
        for s in np.arange(step, max_abs + step, step):
            if ymin <= s <= ymax:
                ax.axhline(y=s, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
            if ymin <= -s <= ymax:
                ax.axhline(y=-s, color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
        
        plot_widget.add_editable_texts(ymin, ymax, title)
        plot_widget.canvas.draw()

    def plot_average(self, plot_widget, data_list):
        if not data_list:
            return
        
        # data_list is a list of arrays (normalized gait cycles)
        data_matrix = np.array(data_list)
        mean = np.mean(data_matrix, axis=0)
        std = np.std(data_matrix, axis=0)
        x = np.linspace(0, 100, len(mean))
        
        ax = plot_widget.ax
        ax.plot(x, mean, color='#404040', linewidth=2) # Dark grey line
        ax.fill_between(x, mean - std, mean + std, color='grey', alpha=0.4) # Grey area
        plot_widget.canvas.draw()

    def set_data(self, data):
        self.data = data
        self.update_layout()

class AverageTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        btn_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import C3D Files")
        self.import_btn.clicked.connect(self.import_files)
        btn_layout.addWidget(self.import_btn)
        self.export_btn = QPushButton("Export Averages")
        self.export_btn.clicked.connect(self.export_averages)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addStretch()
        self.layout.addLayout(btn_layout)
        
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        self.angles_tab = AverageSubTab('ANGLES')
        self.moments_tab = AverageSubTab('MOMENTS')
        self.powers_tab = AverageSubTab('POWERS')
        
        self.tab_widget.addTab(self.angles_tab, "Angles")
        self.tab_widget.addTab(self.moments_tab, "Moments")
        self.tab_widget.addTab(self.powers_tab, "Powers")

    def import_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Import C3D Files", "", "C3D Files (*.c3d)")
        if not files:
            return
            
        # Initialize data structures
        angles_data = {}
        moments_data = {}
        powers_data = {}
        
        progress = QProgressDialog("Importing files...", "Cancel", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModal)
        
        for i, file_path in enumerate(files):
            progress.setValue(i)
            if progress.wasCanceled():
                break
                
            try:
                reader = c3d.Reader(open(file_path, 'rb'))
                frame_rate = getattr(reader, 'frame_rate', 100)
                first_frame = reader.first_frame
                
                # Extract body mass
                body_mass = 1.0
                try:
                    processing_group = reader.get('PROCESSING')
                    param = processing_group.get('Bodymass') or processing_group.get('BODYMASS') if processing_group else None
                    if param:
                        if hasattr(param, 'dimensions') and len(param.dimensions) > 0 and param.dimensions[0] > 1:
                            body_mass = param.float_array[1]
                        else:
                            body_mass = param.float_value
                except:
                    pass
                if body_mass <= 0: body_mass = 1.0

                # Read data
                markers = []
                for _, points, _ in reader.read_frames():
                    markers.append(points)
                markers = np.array(markers)
                
                marker_labels = [label.strip() for label in reader.point_labels]
                
                # Extract events
                events_data = []
                try:
                    event_group = reader.get('EVENT')
                    if event_group and event_group.get('USED').int16_value > 0:
                        labels = event_group.get('LABELS').string_array
                        times = event_group.get('TIMES').float_array
                        contexts = event_group.get('CONTEXTS').string_array
                        for j in range(len(labels)):
                            time_val = times[j]
                            time = time_val[1] if isinstance(time_val, (list, np.ndarray)) and len(time_val) > 1 else time_val
                            label = labels[j].strip().upper()
                            context = contexts[j].strip().upper()
                            foot = 'left' if context == 'LEFT' else 'right' if context == 'RIGHT' else None
                            event_type = 'strike' if 'STRIKE' in label or 'HS' in label else 'off' if 'OFF' in label or 'TO' in label else None
                            if foot and event_type:
                                events_data.append({'time': time, 'foot': foot, 'type': event_type})
                except:
                    pass
                
                # Calculate gait cycles
                left_strikes = sorted([int(e['time'] * frame_rate) - first_frame for e in events_data if e.get('foot') == 'left' and e.get('type') == 'strike'])
                right_strikes = sorted([int(e['time'] * frame_rate) - first_frame for e in events_data if e.get('foot') == 'right' and e.get('type') == 'strike'])
                gait_cycles = {'left': [], 'right': []}
                for j in range(len(left_strikes) - 1):
                    gait_cycles['left'].append((left_strikes[j], left_strikes[j+1]))
                for j in range(len(right_strikes) - 1):
                    gait_cycles['right'].append((right_strikes[j], right_strikes[j+1]))
                
                # Process markers
                name_map = {'Hi': 'Hip', 'Kne': 'Knee', 'Ankl': 'Ankle'}
                
                for idx, label in enumerate(marker_labels):
                    label_upper = label.upper()
                    plot_type = None
                    if 'ANGLE' in label_upper: plot_type = 'ANGLES'
                    elif 'MOMENT' in label_upper: plot_type = 'MOMENTS'
                    elif 'POWER' in label_upper: plot_type = 'POWERS'
                    
                    if not plot_type: continue
                    
                    # Determine group
                    group = ""
                    if label.startswith('L') or label.startswith('R'):
                        group = label[1:-len(plot_type)].lower().capitalize()
                    else:
                        group = label[:-len(plot_type)].lower().capitalize() if label.endswith(plot_type) else label.lower().capitalize()
                    group = name_map.get(group, group)
                    
                    # Determine side
                    side = 'left' if label.startswith('L') else 'right'
                    
                    # Get data
                    data = markers[:, idx, :3]
                    
                    # Normalize units
                    if plot_type == 'MOMENTS':
                        data = data / 1000 / body_mass
                    elif plot_type == 'POWERS':
                        data = data / body_mass
                        
                    # Extract cycles
                    cycles = gait_cycles.get(side, [])
                    for start, end in cycles:
                        if start >= len(data) or end > len(data): continue
                        cycle_data = data[start:end]
                        if len(cycle_data) < 2: continue
                        
                        # Normalize to 101 points
                        x_old = np.linspace(0, 100, len(cycle_data))
                        x_new = np.linspace(0, 100, 101)
                        
                        target_dict = angles_data if plot_type == 'ANGLES' else moments_data if plot_type == 'MOMENTS' else powers_data
                        if group not in target_dict: target_dict[group] = {}
                        
                        for k, comp in enumerate(['x', 'y', 'z']):
                            if comp not in target_dict[group]: target_dict[group][comp] = []
                            interp_val = np.interp(x_new, x_old, cycle_data[:, k])
                            target_dict[group][comp].append(interp_val)
                            
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                
        progress.setValue(len(files))
        
        self.angles_tab.set_data(angles_data)
        self.moments_tab.set_data(moments_data)
        self.powers_tab.set_data(powers_data)

    def export_averages(self):
        data = {
            'ANGLES': self.angles_tab.data,
            'MOMENTS': self.moments_tab.data,
            'POWERS': self.powers_tab.data
        }
        PXDExporter.export_averages(data, self)
