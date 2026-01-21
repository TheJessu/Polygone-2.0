from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF

class TimelineWidget(QWidget):
    frame_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Play/Pause button
        self.play_button = QPushButton("Play")
        self.layout.addWidget(self.play_button)

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.layout.addWidget(self.stop_button)

        # Graphics view for timeline
        self.graphics_view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setFixedHeight(80)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.graphics_view)

        # Timeline properties
        self.total_frames = 100
        self.current_frame = 0
        self.frame_step = 25  # Frame numbers every 25 frames
        self.frame_rate = 100  # Default frame rate (Hz)
        self.events_data = []  # List of events with 'time', 'label', 'type'

        # Draw initial timeline
        self.draw_timeline()

        # Connect mouse events
        self.graphics_view.mousePressEvent = self.mouse_press_event
        self.graphics_view.mouseMoveEvent = self.mouse_move_event
        self.graphics_view.mouseReleaseEvent = self.mouse_release_event
        self.graphics_view.setMouseTracking(True)
        self.dragging = False

    def set_total_frames(self, total_frames):
        self.total_frames = total_frames
        self.draw_timeline()

    def set_current_frame(self, frame):
        self.current_frame = frame
        self.update_scrubber()

    def set_events_data(self, events_data):
        """Set the events data for displaying on the timeline."""
        self.events_data = events_data
        self.draw_timeline()

    def draw_timeline(self):
        self.scene.clear()
        if self.total_frames == 0:
            return

        width = self.graphics_view.width()
        height = self.graphics_view.height()

        # Set scene rect to match view size to prevent scrolling
        self.scene.setSceneRect(0, 0, width, height)

        # Draw timeline bar at bottom
        bar_rect = QRectF(0, height - 25, width, 15)
        self.scene.addRect(bar_rect, QPen(Qt.black), QBrush(QColor(200, 200, 200)))

        # Use fixed frame step of 25
        self.frame_step = 25

        # Draw frame ticks and labels
        font = QFont("Arial", 8)
        for frame in range(0, self.total_frames + 1, self.frame_step):
            x = (frame / self.total_frames) * width
            # Tick
            self.scene.addLine(x, height - 30, x, height - 25, QPen(Qt.black))
            # Label
            text_item = self.scene.addText(str(frame), font)
            text_item.setPos(x - text_item.boundingRect().width() / 2, height - 50)

        # Draw events on timeline
        self.draw_events(width, height)

        # Draw scrubber
        self.scrubber = self.scene.addRect(0, height - 35, 10, 30, QPen(Qt.red), QBrush(Qt.red))

        # Add current frame label on scrubber
        font = QFont("Arial", 8)
        font.setBold(True)
        self.frame_label = self.scene.addText(str(self.current_frame), font)
        self.frame_label.setDefaultTextColor(Qt.black)

        self.update_scrubber()

    def update_scrubber(self):
        if hasattr(self, 'scrubber') and self.total_frames > 0:
            width = self.graphics_view.width()
            x = (self.current_frame / self.total_frames) * width
            self.scrubber.setPos(x - 5, self.scrubber.pos().y())
            self.update_frame_label()

    def update_frame_label(self):
        """Update the frame label on the scrubber."""
        if hasattr(self, 'frame_label'):
            # Remove old label
            self.scene.removeItem(self.frame_label)
            # Create new label with updated text
            font = QFont("Arial", 8)
            font.setBold(True)
            self.frame_label = self.scene.addText(str(self.current_frame), font)
            self.frame_label.setDefaultTextColor(Qt.black)
            # Position the label on top of the scrubber
            scrubber_x = self.scrubber.pos().x() + 5  # Center on scrubber
            scrubber_y = self.scrubber.pos().y() - 5  # Above scrubber
            self.frame_label.setPos(scrubber_x - self.frame_label.boundingRect().width() / 2, scrubber_y)

    def mouse_press_event(self, event):
        if self.total_frames > 0:
            self.dragging = True
            self.update_frame_from_mouse(event.pos().x())

    def mouse_move_event(self, event):
        if self.dragging and self.total_frames > 0:
            self.update_frame_from_mouse(event.pos().x())

    def mouse_release_event(self, event):
        self.dragging = False

    def update_frame_from_mouse(self, x):
        width = self.graphics_view.width()
        frame = int((x / width) * self.total_frames)
        frame = max(0, min(frame, self.total_frames - 1))
        self.current_frame = frame
        self.update_scrubber()
        # Emit signal
        self.frame_changed.emit(frame)

    def draw_events(self, width, height):
        """Draw event blocks and symbols on the timeline."""
        if not self.events_data:
            return

        # --- 1. Draw Blocks for first gait cycle ---
        left_strikes = sorted([e['time'] for e in self.events_data if e.get('foot') == 'left' and e.get('type') == 'strike'])
        right_strikes = sorted([e['time'] for e in self.events_data if e.get('foot') == 'right' and e.get('type') == 'strike'])

        # Draw block for first left gait cycle (red)
        if len(left_strikes) >= 2:
            start_time, end_time = left_strikes[0], left_strikes[1]
            start_frame = int(start_time * self.frame_rate)
            end_frame = int(end_time * self.frame_rate)
            if 0 <= start_frame < self.total_frames and 0 <= end_frame < self.total_frames:
                x_start = (start_frame / self.total_frames) * width
                x_end = (end_frame / self.total_frames) * width
                rect = QRectF(x_start, height - 20, x_end - x_start, 10)
                self.scene.addRect(rect, QPen(QColor(255, 0, 0)), QBrush(QColor(255, 0, 0, 128)))

        # Draw block for first right gait cycle (green)
        if len(right_strikes) >= 2:
            start_time, end_time = right_strikes[0], right_strikes[1]
            start_frame = int(start_time * self.frame_rate)
            end_frame = int(end_time * self.frame_rate)
            if 0 <= start_frame < self.total_frames and 0 <= end_frame < self.total_frames:
                x_start = (start_frame / self.total_frames) * width
                x_end = (end_frame / self.total_frames) * width
                rect = QRectF(x_start, height - 30, x_end - x_start, 10)
                self.scene.addRect(rect, QPen(QColor(0, 255, 0)), QBrush(QColor(0, 255, 0, 128)))
        
        # --- 2. Draw Symbols for all events ---
        # Triangle settings
        tri_height = 8
        tri_width = 8

        for event in self.events_data:
            event_time = event.get('time')
            event_type = event.get('type')
            
            if event_time is None or event_type is None:
                continue

            event_frame = int(event_time * self.frame_rate)
            if not (0 <= event_frame <= self.total_frames):
                continue
            
            x_pos = (event_frame / self.total_frames) * width
            
            if event_type == 'strike':
                # Down-facing triangle (black)
                pen = QPen(Qt.black)
                brush = QBrush(Qt.black)
                y_base = height - 35
                p1 = QPointF(x_pos - tri_width / 2, y_base)
                p2 = QPointF(x_pos + tri_width / 2, y_base)
                p3 = QPointF(x_pos, y_base + tri_height)
                triangle = QPolygonF([p1, p2, p3])
                self.scene.addPolygon(triangle, pen, brush)

            elif event_type == 'off':
                # Up-facing triangle (white)
                pen = QPen(Qt.black) # Black border
                brush = QBrush(Qt.white) # White fill
                y_base = height - 5
                p1 = QPointF(x_pos - tri_width / 2, y_base)
                p2 = QPointF(x_pos + tri_width / 2, y_base)
                p3 = QPointF(x_pos, y_base - tri_height)
                triangle = QPolygonF([p1, p2, p3])
                self.scene.addPolygon(triangle, pen, brush)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.draw_timeline()
