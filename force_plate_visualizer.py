import vtk

class ForcePlateVisualizer:
    def __init__(self, renderer):
        self.renderer = renderer
        self.actors = []

    def create_force_plates(self, force_plate_data):
        """Create force plate visualizations from extracted data."""
        # Clear previous force plate actors
        for actor in self.actors:
            self.renderer.RemoveActor(actor)
        self.actors.clear()

        if not force_plate_data:
            return

        for plate_corners in force_plate_data:
            if len(plate_corners) != 4:
                continue

            # Create points for the plate corners
            points = vtk.vtkPoints()
            for corner in plate_corners:
                points.InsertNextPoint(corner[0], corner[1], corner[2])

            # Create polygon for the plate surface
            polygon = vtk.vtkPolygon()
            polygon.GetPointIds().SetNumberOfIds(4)
            for i in range(4):
                polygon.GetPointIds().SetId(i, i)

            # Create cell array and add the polygon
            cells = vtk.vtkCellArray()
            cells.InsertNextCell(polygon)

            # Create polydata
            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(cells)

            # Create mapper and actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.8, 0.8, 0.8)  # Light grey
            actor.GetProperty().SetOpacity(0.3)  # Semi-transparent
            actor.GetProperty().SetRepresentationToSurface()

            self.actors.append(actor)
            self.renderer.AddActor(actor)

    def clear(self):
        """Clear all force plate actors."""
        for actor in self.actors:
            self.renderer.RemoveActor(actor)
        self.actors.clear()
