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
        Export the gait analysis tab content to PDF, one page per tab.
        """
        if filename is None:
            filename, _ = QFileDialog.getSaveFileName(
                None, "Save PDF", "", "PDF Files (*.pdf)"
            )
            if not filename:
                return

        # Save current tab index
        current_index = gait_analysis_tab.tab_widget.currentIndex()

        with PdfPages(filename) as pdf:
            # Export Kinematics tab
            gait_analysis_tab.tab_widget.setCurrentIndex(0)  # Make kinematics tab active
            fig = self._export_layout_to_figure(gait_analysis_tab.kinematics_layout, "Gait 1 Kinematics")
            if fig:
                pdf.savefig(fig)
                plt.close(fig)


            # Export Kinetics tab
            gait_analysis_tab.tab_widget.setCurrentIndex(1)  # Make kinetics tab active
            fig = self._export_layout_to_figure(gait_analysis_tab.kinetics_layout, "Gait 1 Kinetics")
            if fig:
                pdf.savefig(fig)
                plt.close(fig)

        # Restore original tab
        gait_analysis_tab.tab_widget.setCurrentIndex(current_index)

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