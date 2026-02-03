# TODO: Fix Angles Tab "All" Selection Issue

## Completed Tasks
- [x] Analyzed the angles_tab.py code to understand the plotting logic for "All" selection.
- [x] Identified that canvas.draw() was called during the loop for each plot, but layout updates happened after, potentially causing only the last plot (Z) to be visible due to stacking or positioning issues.
- [x] Removed plot_widget.canvas.draw() from the "All" branch loop.
- [x] Added for plot in self.plots: plot.canvas.draw() after layout updates to ensure all plots are drawn in their correct positions.

## Followup Steps
- [ ] Test the application to verify that "All" selection now shows X, Y, and Z plots for each group.
- [ ] Ensure individual X, Y, Z selections still work correctly.
- [ ] Check for any performance issues or rendering delays with the new drawing sequence.
