# TODO: Add Line Styles to Imported Plot Lines in Gait Analysis Tabs

## Tasks
- [x] Add line_styles list in GaitAnalysisTab.__init__
- [x] Modify plot_data method in GaitAnalysisTab to compute linestyle for each file and pass it to plot_gait_cycle_data
- [x] Update plot_gait_cycle_data in GaitCyclePlotter to accept linestyle parameter and apply it to ax.plot
- [ ] Test the changes to ensure lines are plotted with varying styles and colors
