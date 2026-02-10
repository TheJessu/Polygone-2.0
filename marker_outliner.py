from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel, QHBoxLayout, QAbstractItemView, QTreeWidgetItemIterator
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np

class MarkerOutliner(QWidget):
    # Signal emitted when marker selection changes
    marker_selection_changed = pyqtSignal(list)  # Emits list of selected marker indices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Title
        title = QLabel("Marker Data")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(title)

        # Marker tree
        self.marker_list = QTreeWidget()
        self.marker_list.setMaximumWidth(250)
        self.marker_list.setHeaderHidden(True)  # Hide header
        self.marker_list.setSelectionMode(QAbstractItemView.MultiSelection)  # Allow multiple selection
        self.marker_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.layout.addWidget(self.marker_list)

        # Initialize data
        self.markers = None
        self.num_markers = 0
        self.marker_types = []  # Store marker types

    def load_markers(self, markers, labels=None, marker_types=None):
        """Load marker data and populate the tree grouped by type."""
        self.markers = markers
        self.marker_list.clear()

        if markers is None or markers.size == 0:
            return

        num_frames, num_markers, _ = markers.shape
        self.num_markers = num_markers
        self.marker_types = marker_types if marker_types else []

        # Group markers by type
        type_groups = {}
        for i in range(num_markers):
            marker_type = self.marker_types[i] if i < len(self.marker_types) else 'OTHER'
            if marker_type not in type_groups:
                type_groups[marker_type] = []
            type_groups[marker_type].append(i)

        # Create tree structure
        for marker_type, indices in type_groups.items():
            # Create parent item for marker type
            type_item = QTreeWidgetItem([f"{marker_type} ({len(indices)})"])
            type_item.setData(0, Qt.UserRole, -1)  # -1 indicates it's a group item
            self.marker_list.addTopLevelItem(type_item)

            # Add child items for each marker in this type
            for marker_index in indices:
                # Get marker label
                if labels is not None and len(labels) > 0 and marker_index < len(labels):
                    label = labels[marker_index].strip()
                else:
                    label = f"Marker {marker_index+1}"

                item_text = f"{marker_index+1}: {label}"
                marker_item = QTreeWidgetItem([item_text])
                marker_item.setData(0, Qt.UserRole, marker_index)  # Store marker index
                type_item.addChild(marker_item)

        # Type groups are now collapsed by default

    def clear_markers(self):
        """Clear the marker list."""
        self.marker_list.clear()
        self.markers = None
        self.num_markers = 0

    def set_frame(self, frame_index):
        """Update marker positions for the current frame."""
        # No need to update text since we removed coordinate display
        pass

    def on_selection_changed(self):
        """Handle marker selection changes."""
        selected_indices = []
        for item in self.marker_list.selectedItems():
            marker_index = item.data(0, Qt.UserRole)  # Column 0 for QTreeWidget
            if marker_index != -1:  # Only add actual markers, not group headers
                selected_indices.append(marker_index)
        self.marker_selection_changed.emit(selected_indices)

    def set_selected_markers(self, selected_indices):
        """Set the selected markers in the tree."""
        self.marker_list.blockSignals(True)
        self.marker_list.clearSelection()
        
        iterator = QTreeWidgetItemIterator(self.marker_list)
        while iterator.value():
            item = iterator.value()
            marker_index = item.data(0, Qt.UserRole)
            if marker_index in selected_indices:
                item.setSelected(True)
            iterator += 1
            
        self.marker_list.blockSignals(False)
