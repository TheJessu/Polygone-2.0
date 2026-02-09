import json
import numpy as np
from PyQt5.QtWidgets import QFileDialog

class PXDExporter:
    @staticmethod
    def export_averages(data, parent=None):
        filename, _ = QFileDialog.getSaveFileName(parent, "Save PXD", "", "PXD Files (*.pxd)")
        
        if not filename:
            return

        # Convert numpy arrays to lists for JSON serialization
        serializable_data = {}
        for plot_type, groups in data.items():
            serializable_data[plot_type] = {}
            for group, components in groups.items():
                serializable_data[plot_type][group] = {}
                for comp, values in components.items():
                    # values is a list of arrays. Calculate mean and std.
                    if not values:
                        continue
                    arr = np.array(values)
                    if arr.size == 0:
                        continue
                    mean = np.mean(arr, axis=0)
                    std = np.std(arr, axis=0)
                    serializable_data[plot_type][group][comp] = {
                        'mean': mean.tolist(),
                        'std': std.tolist()
                    }
        
        try:
            with open(filename, 'w') as f:
                json.dump(serializable_data, f)
        except Exception as e:
            print(f"Error saving PXD file: {e}")

    @staticmethod
    def import_averages(parent=None):
        filename, _ = QFileDialog.getOpenFileName(parent, "Open PXD", "", "PXD Files (*.pxd)")
        
        if not filename:
            return None

        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading PXD file: {e}")
            return None
