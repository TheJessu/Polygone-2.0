import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal
import c3d
import numpy as np
import json
from force_plate_visualizer import ForcePlateVisualizer

class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, picker, ren, marker_actors, label_actors, callback):
        super().__init__()
        self.picker = picker
        self.ren = ren
        self.marker_actors = marker_actors
        self.label_actors = label_actors
        self.callback = callback

    def OnLeftButtonDown(self):
        click_pos = self.GetInteractor().GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.ren)
        actor = self.picker.GetActor()
        if actor in self.marker_actors:
            marker_index = self.marker_actors.index(actor)
        elif actor in self.label_actors:
            marker_index = self.label_actors.index(actor)
        else:
            super().OnLeftButtonDown()
            return
        self.callback(marker_index)

class C3DViewer(QWidget):
    markers_selected = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Create top button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()  # Push buttons to the right

        # Side view button
        self.side_view_button = QPushButton("Side View")
        self.side_view_button.clicked.connect(self.set_side_view)
        self.button_layout.addWidget(self.side_view_button)

        # Front view button
        self.front_view_button = QPushButton("Front View")
        self.front_view_button.clicked.connect(self.set_front_view)
        self.button_layout.addWidget(self.front_view_button)

        self.layout.addLayout(self.button_layout)

        # Create VTK render window interactor
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.layout.addWidget(self.vtk_widget)

        # Set up VTK renderer and render window
        self.ren = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtk_widget.GetRenderWindow().GetInteractor()

        # Set camera view up to Z axis
        camera = self.ren.GetActiveCamera()
        camera.SetViewUp(0, 0, 1)
        camera.SetPosition(0, 1000, 500)
        camera.SetFocalPoint(0, 0, 0)

        self.ren.SetBackground(0.1, 0.1, 0.1)  # Dark background

        # Add axes as orientation marker in bottom left corner
        self.axes = vtk.vtkAxesActor()
        self.axes.SetTotalLength(100, 100, 100)

        self.orientation_widget = vtk.vtkOrientationMarkerWidget()
        self.orientation_widget.SetOrientationMarker(self.axes)
        self.orientation_widget.SetInteractor(self.iren)
        self.orientation_widget.SetViewport(0.0, 0.0, 0.2, 0.2)  # Bottom left corner
        self.orientation_widget.SetEnabled(1)
        self.orientation_widget.InteractiveOff()

        # Initialize data structures
        self.marker_actors = []
        self.marker_sources = []  # Store sphere sources for updating positions
        self.trajectory_actors = {}
        self.label_actors = []  # Text labels for markers
        self.line_actors = []  # Actors for lines between markers
        self.line_sources = []  # Sources for lines
        self.markers_data = None  # Store marker data for outliner
        self.marker_types = []  # Store marker type for each marker
        self.trajectory_visible = True  # Track trajectory visibility
        self.trajectory_update_counter = 0  # Counter for trajectory update frequency
        self.trajectory_update_interval = 10  # Update trajectories every 10 frames for better performance
        self.selected_markers = set()  # Track selected marker indices
        self.angle_units = 'degrees'  # Default angle units
        self.events_data = None  # Store event data for timeline
        self.force_plate_actors = []  # Store force plate actors
        self.segments = [] # Store segment data for drawing lines

        # Initialize interactor and picker
        self.iren.Initialize()
        self.picker = vtk.vtkPicker()
        self.custom_style = CustomInteractorStyle(self.picker, self.ren, self.marker_actors, self.label_actors, self.handle_marker_click)
        self.iren.SetInteractorStyle(self.custom_style)

        # Initialize force plate visualizer
        self.force_plate_visualizer = ForcePlateVisualizer(self.ren)

        # Load marker group info from JSON
        self.marker_group_colors = {}
        try:
            with open('marker_group_info.JSON', 'r') as f:
                data = json.load(f)
                for group in data.get('groups', {}).values():
                    color = group.get('color')
                    for marker in group.get('markers', []):
                        self.marker_group_colors[marker] = color
                for segment in data.get('segments', {}).values():
                    self.segments.append(segment)
        except FileNotFoundError:
            print("marker_group_info.JSON not found.")
        except json.JSONDecodeError:
            print("Error decoding marker_group_info.JSON.")

        # Define VTK colors
        self.vtk_colors = {
            'red': (1, 0, 0),
            'green': (0, 1, 0),
            'purple': (0.5, 0, 0.5),
            'yellow': (1, 1, 0) # Added yellow color
        }


        # Create toggle button for trajectories
        self.toggle_trajectory_button = QPushButton("Hide Trajectories")
        self.toggle_trajectory_button.clicked.connect(self.toggle_trajectories)
        self.layout.addWidget(self.toggle_trajectory_button)

        # Initialize grid plane
        self.grid_plane = vtk.vtkPlaneSource()
        self.grid_plane.SetResolution(20, 20)  # Number of divisions
        self.grid_plane.SetOrigin(-2000, -2000, 0)  # Bottom-left corner
        self.grid_plane.SetPoint1(2000, -2000, 0)   # Bottom-right corner
        self.grid_plane.SetPoint2(-2000, 2000, 0)   # Top-left corner

        self.grid_mapper = vtk.vtkPolyDataMapper()
        self.grid_mapper.SetInputConnection(self.grid_plane.GetOutputPort())

        self.grid_actor = vtk.vtkActor()
        self.grid_actor.SetMapper(self.grid_mapper)
        self.grid_actor.GetProperty().SetColor(0.3, 0.3, 0.3)  # Dark grey grid
        self.grid_actor.GetProperty().SetOpacity(0.5)  # Semi-transparent
        self.grid_actor.GetProperty().SetRepresentationToWireframe()  # Wireframe mode

    def handle_marker_click(self, marker_index):
        if marker_index in self.selected_markers:
            self.selected_markers.remove(marker_index)
        else:
            self.selected_markers.add(marker_index)

        self.update_marker_colors()
        self.markers_selected.emit(list(self.selected_markers))
        self.vtk_widget.GetRenderWindow().Render()

    def pick_marker(self, obj, event):
        click_pos = self.iren.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.ren)
        actor = self.picker.GetActor()

        if actor in self.marker_actors:
            marker_index = self.marker_actors.index(actor)
            if marker_index in self.selected_markers:
                self.selected_markers.remove(marker_index)
            else:
                self.selected_markers.add(marker_index)

            self.update_marker_colors()
            self.markers_selected.emit(list(self.selected_markers))
            self.vtk_widget.GetRenderWindow().Render()

    def load_c3d(self, file_path):
        """Load C3D file and display markers and trajectories."""
        try:
            # Clear previous data
            self.clear_data()

            # Read C3D file
            reader = c3d.Reader(open(file_path, 'rb'))
            print(dir(reader))

            # Extract body mass
            self.body_mass = None
            try:
                processing_group = reader.get('PROCESSING')
                param = None
                if processing_group:
                    param = processing_group.get('Bodymass') or processing_group.get('BODYMASS')

                if param:
                    # Check if the parameter is an array with at least 2 elements based on user hint
                    if hasattr(param, 'dimensions') and len(param.dimensions) > 0 and param.dimensions[0] > 1:
                        self.body_mass = param.float_array[1]
                    else:
                        self.body_mass = param.float_value
                    print(f"Body mass extracted: {self.body_mass} kg")
                else:
                    print("Body mass not found in C3D file")

            except Exception as e:
                print(f"Could not extract body mass: {e}")
            
            all_markers = []
            all_analog = []
            max_markers = 0

            for i, points, analog in reader.read_frames():
                frame_markers = [[float(m[0]), float(m[1]), float(m[2]), float(m[3])] for m in points if len(m) >= 4]
                all_markers.append(frame_markers)
                all_analog.append(analog)
                max_markers = max(max_markers, len(frame_markers))

            # Create a consistent 3D array for markers
            num_frames = len(all_markers)
            markers = np.zeros((num_frames, max_markers, 4), dtype=float)
            for i, frame in enumerate(all_markers):
                for j, marker in enumerate(frame):
                    if j < max_markers:
                        markers[i, j] = marker

            # Store marker data and labels
            self.markers_data = markers
            self.marker_labels = [label.strip() for label in reader.point_labels[:max_markers]]

            # Determine marker types based on labels for outliner and plotter grouping
            self.marker_types = []
            for label in self.marker_labels:
                label_upper = label.upper()
                if 'ANGLE' in label_upper:
                    marker_type = 'ANGLES'
                elif 'FORCE' in label_upper:
                    marker_type = 'FORCES'
                elif 'MOMENT' in label_upper:
                    marker_type = 'MOMENTS'
                elif 'POWER' in label_upper:
                    marker_type = 'POWERS'
                elif 'MODEL' in label_upper or 'MARKER' in label_upper:
                    marker_type = 'MODELED_MARKERS'
                else:
                    marker_type = 'DEFAULT'
                self.marker_types.append(marker_type)

            # Extract event data for timeline
            self.events_data = []
            try:
                event_group = reader.get('EVENT')
                used = event_group.get('USED').int16_value
                if used > 0:
                    labels = event_group.get('LABELS').string_array[:used]
                    times = event_group.get('TIMES').float_array[:used]
                    contexts = event_group.get('CONTEXTS').string_array[:used]

                    for i in range(used):
                        time = times[i][1]
                        label = labels[i].strip().upper()
                        context = contexts[i].strip().upper()

                        foot = None
                        if context == 'LEFT':
                            foot = 'left'
                        elif context == 'RIGHT':
                            foot = 'right'

                        event_type = None
                        if 'STRIKE' in label or 'HS' in label or 'ON' in label:
                            event_type = 'strike'
                        elif 'OFF' in label or 'TO' in label:
                            event_type = 'off'
                        
                        if foot and event_type:
                            self.events_data.append({
                                'time': time,
                                'foot': foot,
                                'type': event_type
                            })
            except Exception as e:
                print(f"Error extracting events: {e}")

            # Extract force plate data
            self.force_plate_data = []
            self.force_data = []
            try:
                force_platform_group = reader.get('FORCE_PLATFORM')
                used = force_platform_group.get('USED').int16_value
                if used > 0:
                    corners_data = force_platform_group.get('CORNERS').float_array
                    for plate_idx in range(used):
                        plate_corners = [[corners_data[plate_idx][c][i] for i in range(3)] for c in range(4)]
                        self.force_plate_data.append(plate_corners)

                    analog_labels = [l.strip() for l in reader.analog_labels]
                    
                    all_frames_force_data = []
                    for frame_index in range(num_frames):
                        frame_force_data = []
                        analog_data_frame = all_analog[frame_index]

                        for plate_idx in range(used):
                            force_channels = []
                            for i in range(3):  # Fx, Fy, Fz
                                # Assuming channels are named like 'Force.Fx1', 'Force.Fy1', etc.
                                # This part might need adjustment based on actual channel names in the C3D file.
                                try:
                                    channel_name = f'Force.F{["x", "y", "z"][i]}{plate_idx+1}'
                                    channel_index = analog_labels.index(channel_name)
                                    force_channels.append(np.mean(analog_data_frame[:, channel_index]))
                                except (ValueError, IndexError):
                                    # Fallback if labels are not as expected
                                    channel_index = plate_idx * 6 + i
                                    if channel_index < analog_data_frame.shape[1]:
                                        force_channels.append(np.mean(analog_data_frame[:, channel_index]))
                                    else:
                                        force_channels.append(0)

                            cop_channels = []
                            for i in range(3): # CoPx, CoPy, CoPz
                                try:
                                    channel_name = f'Force.C{["x", "y", "z"][i]}{plate_idx+1}'
                                    channel_index = analog_labels.index(channel_name)
                                    cop_channels.append(np.mean(analog_data_frame[:, channel_index]))
                                except (ValueError, IndexError):
                                     channel_index = plate_idx * 6 + 3 + i
                                     if channel_index < analog_data_frame.shape[1]:
                                        cop_channels.append(np.mean(analog_data_frame[:, channel_index]))
                                     else:
                                        cop_channels.append(0)
                            
                            moment_value = 0
                            label = ''
                            if plate_idx * 6 < len(analog_labels):
                                label = 'LGroundReactionMoment' if 'L' in analog_labels[plate_idx*6] else 'RGroundReactionMoment'
                            
                            if label:
                                try:
                                    channel_index = analog_labels.index(label)
                                    moment_value = np.mean(analog_data_frame[:, channel_index])
                                except (ValueError, IndexError):
                                    pass

                            frame_force_data.append({'F': force_channels, 'CoP': cop_channels, 'M': moment_value})
                        all_frames_force_data.append(frame_force_data)
                    self.force_data = all_frames_force_data

            except (KeyError, AttributeError) as e:
                print(f"Warning: Could not extract force plate data: {e}")
            except Exception as e:
                print(f"Error extracting force plate data: {e}")

            # Add grid plane and force plates to the scene
            self.ren.AddActor(self.grid_actor)
            self.force_plate_visualizer.create_force_plates(self.force_plate_data, self.force_data)

            # Create spheres and labels for markers
            for i in range(max_markers):
                label_text = self.marker_labels[i]
                x, y, z = markers[0, i, 0], markers[0, i, 1], markers[0, i, 2]

                # Create sphere
                sphere = vtk.vtkSphereSource()
                sphere.SetRadius(15)
                sphere.SetCenter(x, y, z)
                self.marker_sources.append(sphere)

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(sphere.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                self.marker_actors.append(actor)

                # Create text label
                text_source = vtk.vtkTextSource()
                text_source.SetText(label_text)
                
                text_mapper = vtk.vtkPolyDataMapper()
                text_mapper.SetInputConnection(text_source.GetOutputPort())

                follower = vtk.vtkFollower()
                follower.SetMapper(text_mapper)
                follower.GetProperty().SetColor(0.8, 0.8, 0.8)
                follower.SetScale(2, 2, 2)
                follower.SetPosition(x, y, z + 20)
                follower.SetCamera(self.ren.GetActiveCamera())
                self.label_actors.append(follower)

                # Set color and visibility based on JSON group
                color_name = self.marker_group_colors.get(label_text)
                if color_name and color_name in self.vtk_colors:
                    actor.GetProperty().SetColor(self.vtk_colors[color_name])
                    actor.VisibilityOn()
                    follower.VisibilityOn()
                else:
                    actor.VisibilityOff()
                    follower.VisibilityOff()

                self.ren.AddActor(actor)
                self.ren.AddActor(follower)

            # Create lines between markers based on segments
            marker_label_to_index = {label: i for i, label in enumerate(self.marker_labels)}
            for segment in self.segments:
                color_name = segment.get('color')
                if not color_name or color_name not in self.vtk_colors:
                    continue
                
                color = self.vtk_colors[color_name]
                for link in segment.get('links', []):
                    marker1_label, marker2_label = link
                    marker1_index = marker_label_to_index.get(marker1_label)
                    marker2_index = marker_label_to_index.get(marker2_label)

                    if marker1_index is not None and marker2_index is not None:
                        p1 = markers[0, marker1_index, :3]
                        p2 = markers[0, marker2_index, :3]

                        line_source = vtk.vtkLineSource()
                        line_source.SetPoint1(p1)
                        line_source.SetPoint2(p2)
                        self.line_sources.append(line_source)

                        mapper = vtk.vtkPolyDataMapper()
                        mapper.SetInputConnection(line_source.GetOutputPort())

                        actor = vtk.vtkActor()
                        actor.SetMapper(mapper)
                        actor.GetProperty().SetColor(color)
                        actor.GetProperty().SetLineWidth(3)
                        
                        self.line_actors.append(actor)
                        self.ren.AddActor(actor)

            self.ren.ResetCamera()
            # Ensure camera view up remains Z axis after reset
            camera = self.ren.GetActiveCamera()
            camera.SetViewUp(0, 0, 1)
            self.vtk_widget.GetRenderWindow().Render()

        except Exception as e:
            print(f"Error loading C3D file: {e}")

    def clear_data(self):
        """Clear all marker and trajectory actors."""
        for actor in self.marker_actors + list(self.trajectory_actors.values()) + self.label_actors + self.line_actors:
            self.ren.RemoveActor(actor)
        self.marker_actors.clear()
        self.marker_sources.clear()
        self.trajectory_actors.clear()
        self.label_actors.clear()
        self.line_actors.clear()
        self.line_sources.clear()
        self.force_plate_visualizer.clear()  # Clear force plate actors
        self.ren.RemoveActor(self.grid_actor)
        self.markers_data = None
        self.trajectory_update_counter = 0  # Reset counter
        self.selected_markers.clear()  # Clear selected markers
        self.vtk_widget.GetRenderWindow().Render()

    def get_markers_data(self):
        """Get the current marker data for the outliner."""
        return self.markers_data

    def get_marker_labels(self):
        """Get the current marker labels for the outliner."""
        return getattr(self, 'marker_labels', None)

    def get_events_data(self):
        """Get the current event data for the timeline."""
        return self.events_data

    def get_body_mass(self):
        """Get the body mass extracted from the C3D file."""
        return self.body_mass

    def toggle_trajectories(self):
        """Toggle visibility of trajectory lines for selected markers."""
        self.trajectory_visible = not self.trajectory_visible
        
        for marker_index in self.selected_markers:
            if marker_index in self.trajectory_actors:
                actor = self.trajectory_actors[marker_index]
                if self.trajectory_visible:
                    self.ren.AddActor(actor)
                else:
                    self.ren.RemoveActor(actor)

        if self.trajectory_visible:
            self.toggle_trajectory_button.setText("Hide Trajectories")
        else:
            self.toggle_trajectory_button.setText("Show Trajectories")
            
        self.vtk_widget.GetRenderWindow().Render()

    def set_frame(self, frame_index):
        """Set the current frame for marker display."""
        if self.markers_data is not None and 0 <= frame_index < self.markers_data.shape[0]:
            num_markers = self.markers_data.shape[1]

            for i in range(num_markers):
                if i < len(self.marker_sources):
                    x, y, z = self.markers_data[frame_index, i, 0], self.markers_data[frame_index, i, 1], self.markers_data[frame_index, i, 2]
                    
                    # Update sphere and label positions
                    self.marker_sources[i].SetCenter(x, y, z)
                    if i < len(self.label_actors):
                        self.label_actors[i].SetPosition(x, y, z + 20)

            # Update trajectories for selected markers
            self.update_trajectories(frame_index, self.selected_markers)

            # Update line positions
            marker_label_to_index = {label: i for i, label in enumerate(self.marker_labels)}
            line_idx = 0
            for segment in self.segments:
                for link in segment.get('links', []):
                    marker1_label, marker2_label = link
                    marker1_index = marker_label_to_index.get(marker1_label)
                    marker2_index = marker_label_to_index.get(marker2_label)

                    if marker1_index is not None and marker2_index is not None:
                        p1 = self.markers_data[frame_index, marker1_index, :3]
                        p2 = self.markers_data[frame_index, marker2_index, :3]
                        
                        if line_idx < len(self.line_sources):
                            self.line_sources[line_idx].SetPoint1(p1)
                            self.line_sources[line_idx].SetPoint2(p2)
                            line_idx += 1

            # Update force plate visualization
            self.force_plate_visualizer.update_force_visualization(frame_index)

            self.vtk_widget.GetRenderWindow().Render()

    def create_trajectory_actor(self, marker_index):
        """Create a trajectory actor for a specific marker if it doesn't exist."""
        if marker_index not in self.trajectory_actors:
            if not hasattr(self, 'trajectory_points'):
                self.trajectory_points = {}
                self.trajectory_lines = {}
                self.trajectory_polydatas = {}
                self.trajectory_mappers = {}
                self.last_trajectory_frame = {}

            # Initialize data structures if not exists
            if marker_index not in self.trajectory_points:
                self.trajectory_points[marker_index] = vtk.vtkPoints()
                self.trajectory_lines[marker_index] = vtk.vtkCellArray()
                self.trajectory_polydatas[marker_index] = vtk.vtkPolyData()
                self.trajectory_polydatas[marker_index].SetPoints(self.trajectory_points[marker_index])
                self.trajectory_polydatas[marker_index].SetLines(self.trajectory_lines[marker_index])
                self.trajectory_mappers[marker_index] = vtk.vtkPolyDataMapper()
                self.trajectory_mappers[marker_index].SetInputData(self.trajectory_polydatas[marker_index])
                self.last_trajectory_frame[marker_index] = -1

            actor = vtk.vtkActor()
            actor.SetMapper(self.trajectory_mappers[marker_index])
            actor.GetProperty().SetColor(0.5, 0.5, 0.5)
            actor.GetProperty().SetLineWidth(2)
            self.trajectory_actors[marker_index] = actor

    def update_trajectories(self, frame_index, marker_indices):
        """Update trajectory lines for specified markers."""
        if not hasattr(self, 'trajectory_points'):
            return

        recent_frames = 100
        ahead_frames = 100
        start_frame = max(0, frame_index - recent_frames)
        end_frame = min(self.markers_data.shape[0] - 1, frame_index + ahead_frames)

        for i in marker_indices:
            if i not in self.trajectory_points:
                continue

            if self.last_trajectory_frame.get(i) == frame_index:
                continue

            self.trajectory_points[i].Reset()
            self.trajectory_lines[i].Reset()

            valid_points = [
                (self.markers_data[f, i, 0], self.markers_data[f, i, 1], self.markers_data[f, i, 2])
                for f in range(start_frame, end_frame + 1)
                if not (np.allclose(self.markers_data[f, i, :3], 0) or np.isnan(self.markers_data[f, i, :3]).any())
            ]

            if len(valid_points) > 1:
                for p in valid_points:
                    self.trajectory_points[i].InsertNextPoint(p)

                for j in range(len(valid_points) - 1):
                    line = vtk.vtkLine()
                    line.GetPointIds().SetId(0, j)
                    line.GetPointIds().SetId(1, j + 1)
                    self.trajectory_lines[i].InsertNextCell(line)

                self.trajectory_polydatas[i].Modified()
                if i in self.trajectory_actors:
                    self.trajectory_actors[i].VisibilityOn()
            else:
                if i in self.trajectory_actors:
                    self.trajectory_actors[i].VisibilityOff()

            self.last_trajectory_frame[i] = frame_index
            
    def update_marker_colors(self):
        """Update marker colors and size based on selection state."""
        if self.markers_data is None or not hasattr(self, 'marker_labels'):
            return

        for i in range(len(self.marker_actors)):
            actor = self.marker_actors[i]
            source = self.marker_sources[i]
            label_text = self.marker_labels[i]

            # If selected, highlight by changing color and size
            if i in self.selected_markers:
                actor.GetProperty().SetColor(self.vtk_colors['yellow']) # Changed to yellow
                source.SetRadius(25)
                actor.VisibilityOn()
                if i < len(self.label_actors):
                    self.label_actors[i].VisibilityOn()
                # Set trajectory color to yellow for selected markers
                if i in self.trajectory_actors:
                    self.trajectory_actors[i].GetProperty().SetColor(self.vtk_colors['yellow'])
            else:
                # Otherwise, use default color and size from JSON group
                source.SetRadius(15)
                color_name = self.marker_group_colors.get(label_text)
                if color_name and color_name in self.vtk_colors:
                    actor.GetProperty().SetColor(self.vtk_colors[color_name])
                    actor.VisibilityOn()
                    if i < len(self.label_actors):
                        self.label_actors[i].VisibilityOn()
                else:
                    # Hide if not in any group
                    actor.VisibilityOff()
                    if i < len(self.label_actors):
                        self.label_actors[i].VisibilityOff()
        
        self.vtk_widget.GetRenderWindow().Render()

    def set_selected_markers(self, selected_indices):
        """Set the selected marker indices and update visualization."""
        self.selected_markers = set(selected_indices)
        self.update_marker_colors()

        # Update trajectory visibility based on selection
        for i in range(len(self.marker_actors)):
            if i in self.selected_markers:
                self.create_trajectory_actor(i)
                if self.trajectory_visible:
                    self.ren.AddActor(self.trajectory_actors[i])
            else:
                if i in self.trajectory_actors:
                    self.ren.RemoveActor(self.trajectory_actors[i])

        self.vtk_widget.GetRenderWindow().Render()

    def set_side_view(self):
        """Set the camera to side view (looking along Y-axis)."""
        if self.markers_data is not None:
            bounds = self.ren.ComputeVisiblePropBounds()
            center = [(bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, (bounds[4] + bounds[5]) / 2]
            distance = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]) * 2

            camera = self.ren.GetActiveCamera()
            camera.SetPosition(center[0], center[1] + distance, center[2])  # Look from positive Y
            camera.SetFocalPoint(center[0], center[1], center[2])
            camera.SetViewUp(0, 0, 1)  # Z up

            self.ren.ResetCameraClippingRange()
            self.vtk_widget.GetRenderWindow().Render()



    def set_front_view(self):
        """Set the camera to front view (looking along X-axis)."""
        if self.markers_data is not None:
            bounds = self.ren.ComputeVisiblePropBounds()
            center = [(bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, (bounds[4] + bounds[5]) / 2]
            distance = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]) * 2

            camera = self.ren.GetActiveCamera()
            camera.SetPosition(center[0] + distance, center[1], center[2])  # Look from positive X
            camera.SetFocalPoint(center[0], center[1], center[2])
            camera.SetViewUp(0, 0, 1)  # Z up

            self.ren.ResetCameraClippingRange()
            self.vtk_widget.GetRenderWindow().Render()
