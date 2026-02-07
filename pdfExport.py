import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
from PyQt5.QtWidgets import QFileDialog
import numpy as np

class PDFExporter:
    def __init__(self):
        pass

    def export_gait_analysis_to_pdf(self, gait_analysis_tab, filename=None):
        """
        Export the gait analysis tab content to PDF, 9 pages: 3 for each tab (All, Red, Green).
        """
        if filename is None:
            filename, _ = QFileDialog.getSaveFileName(
                None, "Save PDF", "", "PDF Files (*.pdf)"
            )
            if not filename:
                return

        # Save current tab index and side filters
        current_index = gait_analysis_tab.tab_widget.currentIndex()
        current_kinematics_side = gait_analysis_tab.kinematics_side_filter
        current_kinetics_side = gait_analysis_tab.kinetics_side_filter
        current_moments_side = gait_analysis_tab.moments_side_filter

        tabs = [
            ('kinematics', 0, gait_analysis_tab.kinematics_layout, 'kinematics_side_filter'),
            ('kinetics', 1, gait_analysis_tab.kinetics_layout, 'kinetics_side_filter'),
            ('moments', 2, gait_analysis_tab.moments_layout, 'moments_side_filter')
        ]
        sides = ['All', 'Red', 'Green']

        with PdfPages(filename) as pdf:
            for tab_name, tab_index, layout, side_attr in tabs:
                for side in sides:
                    # Set side filter
                    setattr(gait_analysis_tab, side_attr, side)
                    # Update plots
                    gait_analysis_tab.plot_data()
                    # Set tab active
                    gait_analysis_tab.tab_widget.setCurrentIndex(tab_index)
                    # Export page
                    title = f"Gait 1 {tab_name.capitalize()} - {side}"
                    fig = self._export_layout_to_figure(layout, title)
                    if fig:
                        pdf.savefig(fig)
                        plt.close(fig)

        # Restore original tab and side filters
        gait_analysis_tab.tab_widget.setCurrentIndex(current_index)
        gait_analysis_tab.kinematics_side_filter = current_kinematics_side
        gait_analysis_tab.kinetics_side_filter = current_kinetics_side
        gait_analysis_tab.moments_side_filter = current_moments_side
        gait_analysis_tab.plot_data()  # Restore plots

    def _export_layout_to_figure(self, layout, title):
        rows = layout.rowCount()
        cols = layout.columnCount()

        if rows == 0 or cols == 0:
            return None

        # Create a figure for the PDF page.
        # A4 paper size is 8.27 x 11.69 inches.
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.suptitle(title, fontsize=16, fontweight='bold')

        gs = gridspec.GridSpec(rows, cols, figure=fig, hspace=0.4, wspace=0.4)

        for r in range(rows):
            for c in range(cols):
                item = layout.itemAtPosition(r, c)
                if item and item.widget():
                    plot_widget = item.widget()
                    if hasattr(plot_widget, 'canvas') and plot_widget.isVisible():
                        # Get the content of the canvas as a numpy array
                        width, height = plot_widget.canvas.get_width_height()
                        ratio = plot_widget.devicePixelRatio()
                        phys_width = int(width * ratio)
                        phys_height = int(height * ratio)
                        img_data = np.frombuffer(plot_widget.canvas.tostring_rgb(), dtype=np.uint8).reshape((phys_height, phys_width, 3))
                        
                        # Create a new subplot in the figure and show the image
                        ax = fig.add_subplot(gs[r, c])
                        ax.imshow(img_data)
                        ax.axis('off') # Don't show axes for the image container
                    else:
                        # Create empty subplot to maintain grid position
                        ax = fig.add_subplot(gs[r, c])
                        ax.set_visible(False)
        
        return fig