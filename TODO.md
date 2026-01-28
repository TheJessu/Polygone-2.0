# TODO List for Angles Tab Modifications

## 1. Modify `generic_plotter.py`
- [x] Remove degree conversion for ANGLES (set conversion to lambda x: x).
- [x] Add a `component` parameter ('x', 'y', 'z', or 'magnitude') to `plot_data`.
- [x] Plot the specified component instead of magnitude.
- [x] For spine group, when component is 'x', label as "Trunk Sway", 'y' as "Trunk Tilt", 'z' as "Trunk Rotation".

## 2. Modify `angles_tab.py`
- [x] Change dropdown to "All", "X", "Y", "Z".
- [x] When "All": For each group, create 3 subplots (X, Y, Z).
- [x] When "X", "Y", "Z": Plot only that component for all groups (one plot per group).
- [x] Update titles and labels accordingly (e.g., "Trunk Sway" for spine X).
- [x] Keep y-axis labels as 'Angle (degrees)'.

## 3. Modify `gait_cycle_plotter.py`
- [x] Remove angle conversion to degrees.

## 4. Followup steps
- [x] Test the changes to ensure plots display correctly.
