# TODO: Adjust MOMENTS Data Plot

## Tasks
- [ ] Modify plot_data() for MOMENTS to plot magnitude instead of x,y,z, with color coding (red for L, green for R)
- [ ] Add unit conversion for MOMENTS to Nmm (multiply by 1000)
- [ ] Add self.selected_moment_data and self.selected_moment_line for tracking selected moment line
- [ ] Add on_moment_line_pick() method for handling pick events on MOMENTS tab
- [ ] Add update_selected_moment_value() method for displaying selected moment value
- [ ] Update __init__ to initialize self.lines['MOMENTS'] = []
- [ ] Update clear_data() to clear moment selections
- [ ] Connect pick event for MOMENTS tab in plot_data()
- [ ] Update set_current_frame() to update selected moment value if selected
