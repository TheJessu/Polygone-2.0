# Refactor Plot Configuration for Gait Cycle Normalization

## Objective
Standardize plot configuration across powers_tab, angles_tab, moments_tab, and forces_tab to use gait_cycle_plotter.py for 0-100% gait cycle timeframe with left/right line overlap.

## Tasks
- [x] Modify powers_tab.py to import and use GaitCyclePlotter instead of its own plot_gait_cycle_data method
- [x] Add gait cycle plotting to angles_tab.py using GaitCyclePlotter
- [x] Add gait cycle plotting to moments_tab.py using GaitCyclePlotter
- [x] Ensure consistent y-labels: Power (W), Angle (degrees), Moment (Nmm), Force (N).
- [x] Handle unit conversions appropriately (e.g., moments to Nmm)
- [x] Test the changes to ensure plots display correctly with overlap and 0-100% normalization
