# TODO List for C3D and Video Viewer Application

- [x] Create requirements.txt with dependencies: PyQt5, vtk, ezc3d, numpy
- [x] Create c3d_viewer.py: Class to load C3D data using ezc3d and render markers/trajectories in VTK
- [x] Create video_player.py: Class to handle video playback with QVideoWidget
- [x] Create main.py: Main window with drag-and-drop support, containing 3D viewer and video player widgets side-by-side
- [x] Set up virtual environment and install dependencies
- [x] Test the application (run to ensure it starts without errors)
- [x] Install dependencies (completed via pip install)
- [x] Fix C3D data loading to handle inhomogeneous marker data
- [x] Add outliner panel to the left showing marker data list
- [x] Add timeline control at bottom for frame-by-frame animation
- [x] Update c3d_viewer.py for frame-based marker animation
- [x] Update marker_outliner.py for current frame positions
- [x] Add text labels for markers in 3D viewport
- [x] Add marker selection functionality in outliner to highlight selected markers in 3D view
- [x] Add marker type colors and display marker types in outliner
