# Line Highlight Feature Implementation

## Completed Tasks
- [x] Added highlight_line method to GenericDataPlotter
- [x] Added get_line_info method to GenericDataPlotter for displaying value, frame, and gait cycle %
- [x] Added calculate_gait_cycle_percent method to GenericDataPlotter
- [x] Modified PlotWidget to emit line_clicked signal on line pick
- [x] Added on_line_clicked method to AnglesTab to handle highlighting and info display
- [x] Connected line_clicked signal in add_plot method
- [x] Updated set_current_frame to refresh info when frame changes
- [x] Updated clear_data to reset highlighted line
- [x] Updated plot_data to clear highlight and info on replot

## Pending Tasks
- [ ] Test the implementation to ensure it works correctly
- [ ] Verify that the feature integrates well with other tabs (future task)
