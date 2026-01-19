from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Create video widget
        self.video_widget = QVideoWidget(self)
        self.layout.addWidget(self.video_widget)

        # Create media player
        self.media_player = QMediaPlayer(self)
        self.media_player.setVideoOutput(self.video_widget)

        # Create control buttons
        self.controls_layout = QHBoxLayout()

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_pause)
        self.controls_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop)
        self.controls_layout.addWidget(self.stop_button)

        self.layout.addLayout(self.controls_layout)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Connect media player signals
        self.media_player.stateChanged.connect(self.update_buttons)

    def load_video(self, file_path):
        """Load a video file."""
        try:
            url = QUrl.fromLocalFile(file_path)
            self.media_player.setMedia(QMediaContent(url))
            self.media_player.play()
        except Exception as e:
            print(f"Error loading video file: {e}")

    def play_pause(self):
        """Toggle play/pause."""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop(self):
        """Stop playback."""
        self.media_player.stop()

    def update_buttons(self, state):
        """Update button text based on media player state."""
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event for video files."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and any(url.toLocalFile().lower().endswith(('.avi', '.mp4')) for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop event for video files."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.avi', '.mp4')):
                self.load_video(file_path)
