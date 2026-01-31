- [ ] Modify PlotWidget class to include hover feature (enterEvent/leaveEvent), line picking (mpl_connect, on_line_pick), and pass plotters to constructor
- [ ] Add line_clicked signal to PlotWidget and on_line_clicked method to ForcesTab
- [ ] Add highlighted_line tracking variable
- [ ] Change dropdown layout: remove "Select Group" dropdown, keep "Select Component" dropdown
- [ ] Update load_data method to match angles_tab.py (group_options, grey_out_groups logic)
- [ ] Update plot_data method to use desired_order, specific titles, proper group filtering, and clear highlighted_line/value_label on replot
- [ ] Improve clear_plots method to match angles_tab.py (invalidate/activate layout, update geometry)
- [ ] Update on_plot_double_clicked to match angles_tab.py (proper zoom in/out with canvas resizing)
- [ ] Update set_current_frame to include highlighted line info update
- [ ] Update clear_data to clear highlighted_line and gait_cycle_plotter.lines
- [ ] Ensure plots are always square with canvas.setFixedSize(200,200)
- [ ] Test all features: hover, double-click zoom, scrollbar, square plots, component dropdown only, line highlighting
=======
# TODO: Adjust forces_tab.py to match angles_tab.py features

- [x] Modify PlotWidget class to include hover feature (enterEvent/leaveEvent), line picking (mpl_connect, on_line_pick), and pass plotters to constructor
- [x] Add line_clicked signal to PlotWidget and on_line_clicked method to ForcesTab
- [x] Add highlighted_line tracking variable
- [x] Change dropdown layout: remove "Select Group" dropdown, keep "Select Component" dropdown
- [x] Update load_data method to match angles_tab.py (group_options, grey_out_groups logic)
- [x] Update plot_data method to use desired_order, specific titles, proper group filtering, and clear highlighted_line/value_label on replot
- [x] Improve clear_plots method to match angles_tab.py (invalidate/activate layout, update geometry)
- [x] Update on_plot_double_clicked to match angles_tab.py (proper zoom in/out with canvas resizing)
- [x] Update set_current_frame to include highlighted line info update
- [x] Update clear_data to clear highlighted_line and gait_cycle_plotter.lines
- [x] Ensure plots are always square with canvas.setFixedSize(200,200)
- [x] Update the else part of plot_data for specific component selection (add titles and logic)
- [x] Test all features: hover, double-click zoom, scrollbar, square plots, component dropdown only, line highlighting
