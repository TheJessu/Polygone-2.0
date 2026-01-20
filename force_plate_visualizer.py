import vtk
import numpy as np

class ForcePlateVisualizer:
    def __init__(self, renderer):
        self.renderer = renderer
        self.actors = []
        self.text_actors = []
        self.arrow_actors = []
        self.force_data = None

    def create_force_plates(self, force_plate_data, force_data):
        """Create force plate visualizations from extracted data."""
        self.clear()
        self.force_data = force_data

        if not force_plate_data:
            return

        for i, plate_corners in enumerate(force_plate_data):
            if len(plate_corners) != 4:
                continue

            points = vtk.vtkPoints()
            for corner in plate_corners:
                points.InsertNextPoint(corner[0], corner[1], corner[2])

            polygon = vtk.vtkPolygon()
            polygon.GetPointIds().SetNumberOfIds(4)
            for j in range(4):
                polygon.GetPointIds().SetId(j, j)

            cells = vtk.vtkCellArray()
            cells.InsertNextCell(polygon)

            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(cells)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.8, 0.8, 0.8)
            actor.GetProperty().SetOpacity(0.3)
            actor.GetProperty().SetRepresentationToSurface()

            self.actors.append(actor)
            self.renderer.AddActor(actor)

            # Add number to the plate
            center = np.mean(plate_corners, axis=0)
            text_source = vtk.vtkVectorText()
            text_source.SetText(str(i + 1))
            
            text_mapper = vtk.vtkPolyDataMapper()
            text_mapper.SetInputConnection(text_source.GetOutputPort())
            
            text_actor = vtk.vtkActor()
            text_actor.SetMapper(text_mapper)
            text_actor.GetProperty().SetColor(1.0, 1.0, 1.0)  # White
            text_actor.SetPosition(center[0], center[1], center[2] + 5)
            text_actor.SetScale(50, 50, 50)
            
            self.text_actors.append(text_actor)
            self.renderer.AddActor(text_actor)

            # Create arrow for force vector
            arrow_source = vtk.vtkArrowSource()
            arrow_mapper = vtk.vtkPolyDataMapper()
            arrow_mapper.SetInputConnection(arrow_source.GetOutputPort())
            arrow_actor = vtk.vtkActor()
            arrow_actor.SetMapper(arrow_mapper)
            arrow_actor.GetProperty().SetColor(1, 0, 0)  # Red
            arrow_actor.VisibilityOff()
            self.arrow_actors.append(arrow_actor)
            self.renderer.AddActor(arrow_actor)

    def update_force_visualization(self, frame_index):
        if self.force_data is None or frame_index >= len(self.force_data):
            return

        for i, arrow_actor in enumerate(self.arrow_actors):
            if i < len(self.force_data[frame_index]):
                force_vector = self.force_data[frame_index][i]['F']
                cop = self.force_data[frame_index][i]['CoP']
                moment_value = self.force_data[frame_index][i]['M']
                
                force_magnitude = np.linalg.norm(force_vector)

                # Use a threshold for visibility
                if force_magnitude > 20:  # Threshold for visibility
                    arrow_actor.VisibilityOn()

                    # The arrow source points along the X axis. We want it to point up (Z axis).
                    # So we need to rotate it.
                    transform = vtk.vtkTransform()
                    transform.Translate(cop)
                    transform.RotateWXYZ(90, 0, 1, 0)  # Rotate around Y-axis to point up (Z)
                    
                    # Scale the arrow. The default arrow is 1 unit long.
                    # We scale in the direction of the arrow (now Z, but X for the source)
                    # and by the moment value.
                    scale_factor = abs(moment_value) * 0.01 # Adjust this factor as needed
                    transform.Scale(scale_factor, scale_factor, scale_factor)

                    arrow_actor.SetUserTransform(transform)

                else:
                    arrow_actor.VisibilityOff()

    def clear(self):
        """Clear all force plate actors."""
        for actor in self.actors + self.text_actors + self.arrow_actors:
            self.renderer.RemoveActor(actor)
        self.actors.clear()
        self.text_actors.clear()
        self.arrow_actors.clear()
        self.force_data = None