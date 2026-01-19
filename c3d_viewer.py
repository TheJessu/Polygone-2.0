import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
import c3d
import numpy as np
from force_plate_visualizer import ForcePlateVisualizer

class C3DViewer(QWidget):
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

        # Initialize interactor
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.iren.Initialize()
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
        self.trajectory_actors = []
        self.label_actors = []  # Text labels for markers
        self.markers_data = None  # Store marker data for outliner
        self.marker_types = []  # Store marker type for each marker
        self.trajectory_visible = True  # Track trajectory visibility
        self.trajectory_update_counter = 0  # Counter for trajectory update frequency
        self.trajectory_update_interval = 10  # Update trajectories every 10 frames for better performance
        self.selected_markers = set()  # Track selected marker indices
        self.angle_units = 'degrees'  # Default angle units
        self.events_data = None  # Store event data for timeline
        self.force_plate_actors = []  # Store force plate actors

        # Initialize force plate visualizer
        self.force_plate_visualizer = ForcePlateVisualizer(self.ren)

        # Define marker type colors
        self.marker_type_colors = {
            'ANGLES': (0, 0, 1),        # Blue
            'FORCES': (0, 1, 0),        # Green
            'MOMENTS': (1, 1, 0),       # Yellow
            'POWERS': (1, 0, 1),        # Magenta
            'MODELED_MARKERS': (0, 1, 1),  # Cyan
            'OTHER': (1, 0.5, 0),       # Orange
            'DEFAULT': (1, 0, 0)        # Red
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

    def load_c3d(self, file_path):
        """Load C3D file and display markers and trajectories."""
        try:
            # Clear previous data
            self.clear_data()

            # Read C3D file
            reader = c3d.Reader(open(file_path, 'rb'))
            frames = reader.read_frames()

            # Get marker data - C3D frames contain [frame_num, marker_array, analog_array]
            all_markers = []
            max_markers = 0
            for frame in frames:
                # Extract marker data from the second element (index 1)
                marker_data = frame[1]  # Shape: (num_markers, 5) - x, y, z, residual, ?

                frame_markers = []
                for marker in marker_data:
                    # Each marker has at least 4 values: x, y, z, residual
                    if len(marker) >= 4:
                        frame_markers.append([float(marker[0]), float(marker[1]), float(marker[2]), float(marker[3])])

                all_markers.append(frame_markers)
                max_markers = max(max_markers, len(frame_markers))

            # Create a consistent 3D array
            num_frames = len(all_markers)
            markers = np.zeros((num_frames, max_markers, 4), dtype=float)

            for i, frame in enumerate(all_markers):
                for j, marker in enumerate(frame):
                    if j < max_markers:
                        markers[i, j] = marker

            # Store marker data and labels for outliner
            self.markers_data = markers
            self.marker_labels = reader.point_labels[:max_markers]  # Get marker labels

            # Extract angle units from C3D file
            self.angle_units = 'degrees'  # Default
            try:
                point_group = reader.get('POINT')
                if point_group:
                    angle_units_param = point_group.get('ANGLE_UNITS')
                    if angle_units_param:
                        self.angle_units = angle_units_param.string_value.strip().lower()
            except Exception as e:
                print(f"Error extracting angle units: {e}")
                self.angle_units = 'degrees'

            # Extract event data for timeline
            self.events_data = []
            try:
                event_group = reader.get('EVENT')
                used = event_group.get('USED').int16_value
                if used > 0:
                    labels = event_group.get('LABELS').string_array[:used]
                    times = event_group.get('TIMES').float_array[:used]
                    contexts = event_group.get('CONTEXTS').string_array[:used] if 'CONTEXTS' in event_group.param_keys() else [''] * used

                    for i in range(used):
                        label = labels[i].strip()
                        time = times[i][1]  # Second column is the time
                        context = contexts[i].strip() if i < len(contexts) else ''

                        # Determine event type and foot
                        if 'STRIKE' in label.upper():
                            event_type = 'strike'
                            foot = 'left' if 'LEFT' in context.upper() else 'right'
                        elif 'OFF' in label.upper():
                            event_type = 'off'
                            foot = 'left' if 'LEFT' in context.upper() else 'right'
                        else:
                            event_type = 'other'
                            foot = 'unknown'

                        self.events_data.append({
                            'label': label,
                            'time': time,
                            'context': context,
                            'type': event_type,
                            'foot': foot
                        })
            except Exception as e:
                print(f"Error extracting events: {e}")
                self.events_data = []

            # Extract force plate data
            self.force_plate_data = []
            try:
                force_platform_group = reader.get('FORCE_PLATFORM')
                if force_platform_group:
                    used = force_platform_group.get('USED').int16_value
                    if used > 0:
                        corners_param = force_platform_group.get('CORNERS')
                        if corners_param:
                            corners_data = corners_param.float_array
                            # corners_data is shape (used, 4, 3) - plates, corners, xyz
                            for plate_idx in range(used):
                                plate_corners = []
                                for corner_idx in range(4):
                                    x, y, z = corners_data[plate_idx][corner_idx]
                                    plate_corners.append([x, y, z])
                                self.force_plate_data.append(plate_corners)
            except Exception as e:
                print(f"Error extracting force plate data: {e}")
                self.force_plate_data = []

            # Determine marker types based on labels
            self.marker_types = []
            for label in self.marker_labels:
                if label:
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
                else:
                    marker_type = 'DEFAULT'
                self.marker_types.append(marker_type)

            num_frames = markers.shape[0]
            num_markers = markers.shape[1]

            # Add grid plane to the scene
            self.ren.AddActor(self.grid_actor)

            # Create force plate visualizations using the visualizer
            self.force_plate_visualizer.create_force_plates(self.force_plate_data)

            # Create spheres for markers at first frame
            for i in range(num_markers):
                x, y, z = markers[0, i, 0], markers[0, i, 1], markers[0, i, 2]

                # Skip if marker is invalid (all zeros or NaN)
                if np.allclose([x, y, z], 0) or np.isnan([x, y, z]).any():
                    continue

                # Create sphere
                sphere = vtk.vtkSphereSource()
                sphere.SetRadius(15)
                sphere.SetCenter(x, y, z)

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(sphere.GetOutputPort())

                # Get marker type and corresponding color
                marker_type = self.marker_types[i] if i < len(self.marker_types) else 'DEFAULT'
                color = self.marker_type_colors.get(marker_type, self.marker_type_colors['DEFAULT'])

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(color[0], color[1], color[2])

                self.marker_actors.append(actor)
                self.marker_sources.append(sphere)  # Store sphere source for updating
                self.ren.AddActor(actor)

                # Create text label for marker
                if self.marker_labels is not None and i < len(self.marker_labels):
                    label_text = self.marker_labels[i].strip()
                    if label_text:
                        # Create text source
                        text_source = vtk.vtkTextSource()
                        text_source.SetText(label_text)

                        # Create mapper and actor
                        mapper = vtk.vtkPolyDataMapper()
                        mapper.SetInputConnection(text_source.GetOutputPort())

                        follower = vtk.vtkFollower()
                        follower.SetMapper(mapper)
                        follower.GetProperty().SetColor(0.5, 0.5, 0.5)  # Grey text
                        follower.SetScale(1, 1, 1)  # Font size 1
                        follower.SetPosition(x, y, z + 50)  # Position above marker in 3D space
                        follower.SetCamera(self.ren.GetActiveCamera())

                        self.label_actors.append(follower)
                        self.ren.AddActor(follower)



            # Reset camera to fit all actors
            self.ren.ResetCamera()

            # Set default view: X as depth, Y as sides, Z as height
            camera = self.ren.GetActiveCamera()
            # Look along X-axis (depth), Y horizontal, Z vertical
            bounds = self.ren.ComputeVisiblePropBounds()
            center = [(bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, (bounds[4] + bounds[5]) / 2]
            distance = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]) * 2
            camera.SetPosition(center[0] + distance, center[1], center[2])
            camera.SetFocalPoint(center[0], center[1], center[2])
            camera.SetViewUp(0, 0, 1)  # Z up

            # Render
            self.vtk_widget.GetRenderWindow().Render()

        except Exception as e:
            print(f"Error loading C3D file: {e}")

    def clear_data(self):
        """Clear all marker and trajectory actors."""
        for actor in self.marker_actors + self.trajectory_actors + self.label_actors:
            self.ren.RemoveActor(actor)
        self.marker_actors.clear()
        self.marker_sources.clear()
        self.trajectory_actors.clear()
        self.label_actors.clear()
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

    def toggle_trajectories(self):
        """Toggle visibility of trajectory lines."""
        self.trajectory_visible = not self.trajectory_visible
        if self.trajectory_visible:
            for actor in self.trajectory_actors:
                self.ren.AddActor(actor)
            self.toggle_trajectory_button.setText("Hide Trajectories")
        else:
            for actor in self.trajectory_actors:
                self.ren.RemoveActor(actor)
            self.toggle_trajectory_button.setText("Show Trajectories")
        self.vtk_widget.GetRenderWindow().Render()

    def set_frame(self, frame_index):
        """Set the current frame for marker display."""
        if self.markers_data is not None and 0 <= frame_index < self.markers_data.shape[0]:
            num_markers = self.markers_data.shape[1]

            # MARKER POSITION UPDATING SECTION: Update marker positions for the current frame
            marker_idx = 0
            for i in range(num_markers):
                x, y, z = self.markers_data[frame_index, i, 0], self.markers_data[frame_index, i, 1], self.markers_data[frame_index, i, 2]

                # Skip if marker is invalid (all zeros or NaN)
                if np.allclose([x, y, z], 0) or np.isnan([x, y, z]).any():
                    continue

                # Update existing actor or create new one if needed
                if marker_idx < len(self.marker_actors):
                    # Update existing sphere center
                    self.marker_sources[marker_idx].SetCenter(x, y, z)
                else:
                    # Create new sphere if we don't have enough actors
                    sphere = vtk.vtkSphereSource()
                    sphere.SetRadius(15)
                    sphere.SetCenter(x, y, z)

                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputConnection(sphere.GetOutputPort())

                    # Get marker type and corresponding color
                    marker_type = self.marker_types[i] if i < len(self.marker_types) else 'DEFAULT'
                    color = self.marker_type_colors.get(marker_type, self.marker_type_colors['DEFAULT'])

                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)
                    actor.GetProperty().SetColor(color[0], color[1], color[2])

                    self.marker_actors.append(actor)
                    self.marker_sources.append(sphere)  # Store sphere source for updating
                    self.ren.AddActor(actor)

                # Update text label position
                if marker_idx < len(self.label_actors):
                    self.label_actors[marker_idx].SetPosition(x, y, z + 50)
                elif self.marker_labels is not None and i < len(self.marker_labels):
                    # Create new label if needed
                    label_text = self.marker_labels[i].strip()
                    if label_text:
                        text_source = vtk.vtkTextSource()
                        text_source.SetText(label_text)

                        mapper = vtk.vtkPolyDataMapper()
                        mapper.SetInputConnection(text_source.GetOutputPort())

                        follower = vtk.vtkFollower()
                        follower.SetMapper(mapper)
                        follower.GetProperty().SetColor(1, 1, 1)  # White text
                        follower.SetScale(1, 1, 1)  # Font size 1
                        follower.SetPosition(x, y, z + 50)  # Position above marker in 3D space
                        follower.SetCamera(self.ren.GetActiveCamera())

                        self.label_actors.append(follower)
                        self.ren.AddActor(follower)

                marker_idx += 1

            # Hide unused markers and labels
            for i in range(marker_idx, len(self.marker_actors)):
                self.marker_actors[i].VisibilityOff()
            for i in range(marker_idx, len(self.label_actors)):
                self.label_actors[i].VisibilityOff()

            # Show used markers and labels
            for i in range(marker_idx):
                self.marker_actors[i].VisibilityOn()
                self.label_actors[i].VisibilityOn()

            # Update marker colors based on selection
            self.update_marker_colors()

            # Update trajectories progressively (less frequently for performance)
            self.trajectory_update_counter += 1
            if self.trajectory_update_counter >= self.trajectory_update_interval:
                #self.update_trajectories(frame_index)
                self.trajectory_update_counter = 0

            # Render
            self.vtk_widget.GetRenderWindow().Render()

    def update_trajectories(self, frame_index):
        """Update trajectory lines progressively with optimized performance."""
        if not hasattr(self, 'trajectory_points'):
            self.trajectory_points = {}
            self.trajectory_lines = {}
            self.trajectory_polydatas = {}
            self.trajectory_mappers = {}
            self.last_trajectory_frame = {}  # Track last updated frame per marker

        num_markers = self.markers_data.shape[1]
        recent_frames = 15  # Reduced from 20 to 15 for better performance
        start_frame = max(0, frame_index - recent_frames + 1)

        for i in range(num_markers):
            # Initialize trajectory data structures if not exists
            if i not in self.trajectory_points:
                self.trajectory_points[i] = vtk.vtkPoints()
                self.trajectory_lines[i] = vtk.vtkCellArray()
                self.trajectory_polydatas[i] = vtk.vtkPolyData()
                self.trajectory_polydatas[i].SetPoints(self.trajectory_points[i])
                self.trajectory_polydatas[i].SetLines(self.trajectory_lines[i])
                self.trajectory_mappers[i] = vtk.vtkPolyDataMapper()
                self.trajectory_mappers[i].SetInputData(self.trajectory_polydatas[i])
                self.last_trajectory_frame[i] = -1

                if i >= len(self.trajectory_actors):
                    actor = vtk.vtkActor()
                    actor.SetMapper(self.trajectory_mappers[i])
                    actor.GetProperty().SetColor(0.5, 0.5, 0.5)  # Grey trajectories
                    actor.GetProperty().SetLineWidth(2)
                    self.trajectory_actors.append(actor)
                    if self.trajectory_visible:
                        self.ren.AddActor(actor)

            # Only update if frame has changed significantly
            if self.last_trajectory_frame[i] == frame_index:
                continue

            # Clear and rebuild trajectory for this marker (optimized: only rebuild when necessary)
            self.trajectory_points[i].Reset()
            self.trajectory_lines[i].Reset()

            valid_points = []
            for frame in range(start_frame, frame_index + 1):
                x, y, z = self.markers_data[frame, i, 0], self.markers_data[frame, i, 1], self.markers_data[frame, i, 2]
                if not (np.allclose([x, y, z], 0) or np.isnan([x, y, z]).any()):
                    valid_points.append((x, y, z))

            if len(valid_points) > 1:
                # Batch insert points for better performance
                points_array = np.array(valid_points, dtype=np.float64)
                for point in points_array:
                    self.trajectory_points[i].InsertNextPoint(point[0], point[1], point[2])

                # Create line cells more efficiently
                num_points = len(valid_points)
                for j in range(num_points - 1):
                    line = vtk.vtkLine()
                    line.GetPointIds().SetId(0, j)
                    line.GetPointIds().SetId(1, j + 1)
                    self.trajectory_lines[i].InsertNextCell(line)

                self.trajectory_polydatas[i].Modified()
                self.trajectory_actors[i].VisibilityOn()
            else:
                self.trajectory_actors[i].VisibilityOff()

            self.last_trajectory_frame[i] = frame_index

    def update_marker_colors(self):
        """Update marker colors based on selection state and marker type."""
        if self.markers_data is None:
            return

        num_markers = self.markers_data.shape[1]
        marker_idx = 0

        for i in range(num_markers):
            # Skip invalid markers
            x, y, z = self.markers_data[0, i, 0], self.markers_data[0, i, 1], self.markers_data[0, i, 2]
            if np.allclose([x, y, z], 0) or np.isnan([x, y, z]).any():
                continue

            if marker_idx < len(self.marker_actors):
                actor = self.marker_actors[marker_idx]
                if i in self.selected_markers:
                    actor.GetProperty().SetColor(0, 1, 0)  # Green for selected
                else:
                    # Use marker type color
                    marker_type = self.marker_types[i] if i < len(self.marker_types) else 'DEFAULT'
                    color = self.marker_type_colors.get(marker_type, self.marker_type_colors['DEFAULT'])
                    actor.GetProperty().SetColor(color[0], color[1], color[2])

            marker_idx += 1

    def set_selected_markers(self, selected_indices):
        """Set the selected marker indices and update visualization."""
        self.selected_markers = set(selected_indices)
        self.update_marker_colors()
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
