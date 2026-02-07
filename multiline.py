import c3d
import numpy as np
import json

class MultilineImporter:
    def __init__(self):
        self.imported_files = []  # List of dicts: {'filename': str, 'markers_data': array, 'marker_labels': list, 'marker_types': list, 'gait_cycles': dict, 'body_mass': float}

    def import_c3d(self, file_path):
        """Import a C3D file and store its data."""
        if len(self.imported_files) >= 5:
            return False  # Max 5 files

        try:
            reader = c3d.Reader(open(file_path, 'rb'))
            num_frames = reader.frame_count
            first_frame = reader.first_frame
            frame_rate = getattr(reader, 'frame_rate', 100)

            # Extract body mass
            body_mass = None
            try:
                processing_group = reader.get('PROCESSING')
                param = processing_group.get('Bodymass') or processing_group.get('BODYMASS') if processing_group else None
                if param:
                    if hasattr(param, 'dimensions') and len(param.dimensions) > 0 and param.dimensions[0] > 1:
                        body_mass = param.float_array[1]
                    else:
                        body_mass = param.float_value
            except:
                pass

            # Read data
            read_data = {}
            max_markers = 0
            for i, points, analog in reader.read_frames():
                read_data[i] = (points, analog)
                max_markers = max(max_markers, len(points))

            markers = np.zeros((num_frames, max_markers, 4), dtype=float)
            for i in range(first_frame, first_frame + num_frames):
                frame_idx = i - first_frame
                if i in read_data:
                    points, _ = read_data[i]
                    for j, marker in enumerate(points):
                        if j < max_markers:
                            markers[frame_idx, j] = [float(m) for m in marker[:4]]

            marker_labels = [label.strip() for label in reader.point_labels[:max_markers]]
            marker_types = []
            for label in marker_labels:
                label_upper = label.upper()
                if 'ANGLE' in label_upper:
                    marker_type = 'ANGLES'
                elif 'FORCE' in label_upper:
                    marker_type = 'FORCES'
                elif 'MOMENT' in label_upper:
                    marker_type = 'MOMENTS'
                elif 'POWER' in label_upper:
                    marker_type = 'POWERS'
                else:
                    marker_type = 'DEFAULT'
                marker_types.append(marker_type)

            # Extract events for gait cycles
            events_data = []
            try:
                event_group = reader.get('EVENT')
                if event_group:
                    used_param = event_group.get('USED')
                    if used_param:
                        used = used_param.int16_value
                        if used > 0:
                            labels_param = event_group.get('LABELS')
                            times_param = event_group.get('TIMES')
                            contexts_param = event_group.get('CONTEXTS')
                            if labels_param and times_param and contexts_param:
                                labels = labels_param.string_array[:used]
                                times = times_param.float_array[:used]
                                contexts = contexts_param.string_array[:used]
                                for i in range(used):
                                    time_val = times[i]
                                    time = time_val[1] if isinstance(time_val, (list, np.ndarray)) and len(time_val) > 1 else time_val
                                    label = labels[i].strip().upper()
                                    context = contexts[i].strip().upper()
                                    foot = 'left' if context == 'LEFT' else 'right' if context == 'RIGHT' else None
                                    event_type = 'strike' if 'FOOT STRIKE' in label or 'STRIKE' in label or 'HS' in label or 'ON' in label else 'off' if 'FOOT OFF' in label or 'OFF' in label or 'TO' in label else None
                                    if foot and event_type:
                                        events_data.append({'time': time, 'foot': foot, 'type': event_type})
            except:
                pass

            # Calculate gait cycles
            left_strikes = sorted([int(e['time'] * frame_rate) - first_frame for e in events_data if e.get('foot') == 'left' and e.get('type') == 'strike'])
            right_strikes = sorted([int(e['time'] * frame_rate) - first_frame for e in events_data if e.get('foot') == 'right' and e.get('type') == 'strike'])
            gait_cycles = {'left': [], 'right': []}
            for i in range(len(left_strikes) - 1):
                gait_cycles['left'].append((left_strikes[i], left_strikes[i+1]))
            for i in range(len(right_strikes) - 1):
                gait_cycles['right'].append((right_strikes[i], right_strikes[i+1]))

            filename = file_path.split('/')[-1].split('\\')[-1]  # Get filename
            self.imported_files.append({
                'filename': filename,
                'markers_data': markers,
                'marker_labels': marker_labels,
                'marker_types': marker_types,
                'gait_cycles': gait_cycles,
                'body_mass': body_mass
            })
            return True
        except Exception as e:
            print(f"Error importing C3D: {e}")
            return False

    def get_file_data(self, index):
        """Get data for a specific imported file."""
        if 0 <= index < len(self.imported_files):
            return self.imported_files[index]
        return None

    def get_num_files(self):
        return len(self.imported_files)
