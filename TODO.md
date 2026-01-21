# TODO: Implement Gait Data Display in Data Plots

## Tasks
- [x] Remove infobox code and click connections for gait blocks in `timeline_widget.py`
- [x] Add `gait_info_label` for each tab in `data_plotter.py`, placed below `value_labels`
- [x] Add `set_gait_info` method in `data_plotter.py` to update gait info labels with formatted gait data
- [x] In `main.py`, call `data_plotter.set_gait_info(events_data)` when events_data is set to display gait info persistently
