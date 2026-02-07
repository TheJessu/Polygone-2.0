# TODO: Add "Gait 1 Moments" Tab to GaitAnalysisTab

- [ ] Add self.moments_tab = QWidget() and self.moments_layout = QGridLayout(self.moments_tab) in __init__
- [ ] Add self.tab_widget.addTab(self.moments_tab, "Gait 1 Moments")
- [ ] Add self.moments_plots = [] in __init__
- [ ] Implement setup_moments_plots() method to create 3x3 grid for hip, knee, ankle x,y,z
- [ ] Call self.setup_moments_plots() in __init__
- [ ] Add plotting logic for moments_plots in plot_data() method
- [ ] Add clearing logic for moments_plots in clear_data() method
- [ ] Ensure PDF export includes the new tab in export_to_pdf method
