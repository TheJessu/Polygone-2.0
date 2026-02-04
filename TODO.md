# Gait Analysis Tab Update

## Task: Mirror plots from data plots tabs (angles, moments, powers) in gait analysis tab

### Changes Made:
- Updated `gait_analysis_tab.py`:
  - Changed ylabel for kinematics to 'Angle (degrees)'
  - Updated plots_config to use 'Angle (degrees)' for ANGLES, 'Power (W/kg)' for POWERS
  - Updated plot_gait_cycle_data call for kinematics to use 'Angle (degrees)'

- Updated `gait_cycle_plotter.py`:
  - Added ax.set_box_aspect(1) for consistent plot proportions
  - Added text labels, y-limits, yticks, grid lines, and zero lines for ANGLES, MOMENTS, and POWERS to match data tabs styling

### Verification:
- Kinematics plots now have proper y-limits, grid lines, and text labels matching angles_tab.py
- Kinetics plots have y-limits, grid lines, and text labels matching moments_tab.py and powers_tab.py
- Titles and visibility rules remain the same
- Ylabels updated to match data tabs

### Next Steps:
- Test the application to ensure plots display correctly
- Verify that the styling matches the data plots tabs
