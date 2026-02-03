import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QLabel, QSplitter, QVBoxLayout, QSlider, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from c3d_viewer import C3DViewer
from video_player import VideoPlayer
from marker_outliner import MarkerOutliner
from data_plotter import DataPlotter
from gait_analysis_tab import GaitAnalysisTab
from timeline_widget import TimelineWidget
from PyQt5.QtWidgets import QTabWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("C3D and Video Viewer")
        self.setGeometry(100, 100, 1920, 1080)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create top content layout
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, 1)

        # Create marker outliner
        self.marker_outliner = MarkerOutliner()
        self.marker_outliner.setMaximumWidth(350)
        content_layout.addWidget(self.marker_outliner)

        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        content_layout.addWidget(splitter)

        # Create C3D viewer
        self.c3d_viewer = C3DViewer()
        splitter.addWidget(self.c3d_viewer)

        # Connect marker selection signal to C3D viewer
        self.marker_outliner.marker_selection_changed.connect(self.c3d_viewer.set_selected_markers)
        self.c3d_viewer.markers_selected.connect(self.marker_outliner.set_selected_markers)

        # Create tab widget for video player and data plots
        self.right_tabs = QTabWidget()
        splitter.addWidget(self.right_tabs)

        # Create video player tab
        self.video_player = VideoPlayer()
        self.right_tabs.addTab(self.video_player, "Video")

        # Create data plotter tab
        self.data_plotter = DataPlotter()
        self.right_tabs.addTab(self.data_plotter, "Data Plots")

        # Create gait analysis tab
        self.gait_analysis_tab = GaitAnalysisTab()
        self.right_tabs.addTab(self.gait_analysis_tab, "Gait Analysis")

        # Set splitter proportions
        splitter.setSizes([1100, 500])

        # Create timeline controls at bottom
        self.timeline_widget = TimelineWidget()
        self.timeline_widget.play_button.clicked.connect(self.toggle_playback)
        self.timeline_widget.stop_button.clicked.connect(self.stop_playback)
        self.timeline_widget.frame_changed.connect(self.on_timeline_changed)
        main_layout.addWidget(self.timeline_widget)

        # FRAMES PER SECOND ANIMATION SECTION: Animation timer for frame-by-frame playback
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.next_frame)
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0

        # Enable drag and drop for the main window
        self.setAcceptDrops(True)

        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Drag and drop C3D or video files to load them")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile().lower()
                if file_path.endswith('.c3d') or file_path.endswith(('.avi', '.mp4')):
                    event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.c3d'):
                self.c3d_viewer.load_c3d(file_path)
                # Update marker outliner with data, labels, and marker types
                markers_data = self.c3d_viewer.get_markers_data()
                marker_labels = self.c3d_viewer.get_marker_labels()
                marker_types = getattr(self.c3d_viewer, 'marker_types', [])
                self.marker_outliner.load_markers(markers_data, marker_labels, marker_types)
                # Update data plotter with data
                angle_units = getattr(self.c3d_viewer, 'angle_units', 'degrees')
                body_mass = self.c3d_viewer.get_body_mass()
                self.data_plotter.load_data(markers_data, marker_types, marker_labels, angle_units, body_mass)
                self.gait_analysis_tab.load_data(markers_data, marker_types, marker_labels)
                # Update timeline controls
                if markers_data is not None:
                    self.total_frames = markers_data.shape[0]
                    self.timeline_widget.set_total_frames(self.total_frames)
                    self.current_frame = 0
                    self.timeline_widget.set_current_frame(0)
                    self.c3d_viewer.set_frame(0)  # Set to first frame
                    self.marker_outliner.set_frame(0)
                    self.data_plotter.set_current_frame(0)
                    self.gait_analysis_tab.set_current_frame(0)

                    # Set events data for timeline
                    events_data = self.c3d_viewer.get_events_data()
                    first_frame = self.c3d_viewer.get_first_frame()
                    frame_rate = self.c3d_viewer.frame_rate
                    if events_data:
                        self.timeline_widget.set_events_data(events_data)
                        self.timeline_widget.set_first_frame(first_frame)
                        self.timeline_widget.set_frame_rate(frame_rate)
                        # Set gait info for data plotter
                        self.data_plotter.set_gait_info(events_data, frame_rate)
                        # Set gait cycles for gait analysis tab
                        left_strikes = sorted([int(e['time'] * frame_rate) for e in events_data if e.get('foot') == 'left' and e.get('type') == 'strike'])
                        right_strikes = sorted([int(e['time'] * frame_rate) for e in events_data if e.get('foot') == 'right' and e.get('type') == 'strike'])
                        gait_cycles = {'left': [], 'right': []}
                        for i in range(len(left_strikes) - 1):
                            gait_cycles['left'].append((left_strikes[i], left_strikes[i+1]))
                        for i in range(len(right_strikes) - 1):
                            gait_cycles['right'].append((right_strikes[i], right_strikes[i+1]))
                        self.gait_analysis_tab.set_gait_cycles(gait_cycles)
                self.status_bar.showMessage(f"Loaded C3D file: {file_path}")
            elif file_path.lower().endswith(('.avi', '.mp4')):
                self.video_player.load_video(file_path)
                self.status_bar.showMessage(f"Loaded video file: {file_path}")

    def toggle_playback(self):
        """Toggle play/pause animation."""
        if self.is_playing:
            self.animation_timer.stop()
            self.timeline_widget.play_button.setText("Play")
            self.is_playing = False
        else:
            if self.total_frames > 0:
                self.animation_timer.start(10)  # ~100 FPS - FRAMES PER SECOND ANIMATION: Timer set to 10ms for ~100 FPS playback
                self.timeline_widget.play_button.setText("Pause")
                self.is_playing = True

    def on_timeline_changed(self, value):
        """Handle timeline slider change."""
        if self.total_frames > 0:
            self.current_frame = value
            self.c3d_viewer.set_frame(self.current_frame)
            self.marker_outliner.set_frame(self.current_frame)
            self.data_plotter.set_current_frame(self.current_frame)
            self.gait_analysis_tab.set_current_frame(self.current_frame)

    def stop_playback(self):
        """Stop playback."""
        self.animation_timer.stop()
        self.is_playing = False
        self.current_frame = 0
        self.timeline_widget.set_current_frame(0)
        self.c3d_viewer.set_frame(0)
        self.marker_outliner.set_frame(0)
        self.data_plotter.set_current_frame(0)
        self.gait_analysis_tab.set_current_frame(0)

    def next_frame(self):
        """Advance to next frame in animation."""
        if self.total_frames > 0:
            self.current_frame = (self.current_frame + 1) % self.total_frames
            self.timeline_widget.set_current_frame(self.current_frame)
            self.c3d_viewer.set_frame(self.current_frame)
            self.marker_outliner.set_frame(self.current_frame)
            self.data_plotter.set_current_frame(self.current_frame)
            self.gait_analysis_tab.set_current_frame(self.current_frame)

    def update_frame_label(self):
        """Update the frame display label."""
        self.frame_label.setText(f"Frame: {self.current_frame + 1}/{self.total_frames}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
