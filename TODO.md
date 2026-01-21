# TODO

- [x] Fix `IndexError` in `c3d_viewer.py` during force plate data extraction.
  - [x] Use `analog_data_frame.shape[1]` for bounds check in `force_channels` fallback.
  - [x] Use `analog_data_frame.shape[1]` for bounds check in `cop_channels` fallback.
  - [x] Add bounds check for `analog_labels` access in `moment_value` calculation.
- [x] Fix `QVTKRenderWindowInteractor` import path in `c3d_viewer.py`.
- [x] Restore foot strike event visualization on the timeline.
  - [x] Update event data parsing in `c3d_viewer.py` to identify foot and event type.
  - [x] Correct event data parsing to use `CONTEXTS` for foot and `LABELS` for type.
- [x] Update timeline event block logic to show the first gait cycle.
- [x] Update timeline to show event markers as symbols.
  - [x] Draw down-facing triangle for foot strike.
  - [x] Draw up-facing triangle for foot off.
- [x] Combine timeline visualizations:
    - [x] Render both gait cycle blocks and event symbols.
    - [x] Change foot off symbol color to white.