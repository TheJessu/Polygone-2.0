# Refactor Tab Files to Reduce Duplication

## Overview
Centralize common plotting functionality in `data_plotter.py` and simplify tab files to use generic functions.

## Tasks
- [ ] Create GenericDataPlotter class in data_plotter.py
- [ ] Implement plot_data method for generic plotting
- [ ] Implement get_value_at_frame method for value display
- [ ] Update moments_tab.py to use GenericDataPlotter
- [ ] Update forces_tab.py to use GenericDataPlotter
- [ ] Update angles_tab.py to use GenericDataPlotter
- [ ] Update powers_tab.py to use GenericDataPlotter
- [ ] Ensure correct units and formatting for each marker type
- [ ] Test functionality
