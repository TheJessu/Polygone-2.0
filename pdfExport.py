import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
from PyQt5.QtWidgets import QFileDialog

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
            self._export_kinematics_to_pdf(gait_analysis_tab, pdf)

            # Export Kinetics tab
            gait_analysis_tab.tab_widget.setCurrentIndex(1)  # Make kinetics tab active
            self._export_kinetics_to_pdf(gait_analysis_tab, pdf)

        # Restore original tab
        gait_analysis_tab.tab_widget.setCurrentIndex(current_index)

    def _export_tab_to_pdf(self, tab_widget, layout, title, pdf):
        """
        Export a single tab's content to a PDF page.
        """
        # Determine grid size based on layout
        rows = 0
        cols = 0
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                pos = layout.getItemPosition(item)
                row, col, rowspan, colspan = pos
                rows = max(rows, row + rowspan)
                cols = max(cols, col + colspan)

        if rows == 0 or cols == 0:
            return

        # Create a figure for the PDF page with square subplots
        subplot_size = 2.0  # inches, matching UI plot size (200px at 100dpi = 2in)
        width = cols * subplot_size
        height = rows * subplot_size
        fig = plt.figure(figsize=(width, height))
        fig.suptitle(title, fontsize=16, fontweight='bold')

        # Create subplot grid
        gs = gridspec.GridSpec(rows, cols, figure=fig, hspace=0.3, wspace=0.3)

        # Get plot widgets by position
        for row in range(rows):
            for col in range(cols):
                item = layout.itemAtPosition(row, col)
                if item and item.widget():
                    plot_widget = item.widget()
                    if hasattr(plot_widget, 'figure') and plot_widget.isVisible():
                        # Create subplot and copy plot data
                        ax = fig.add_subplot(gs[row, col])

                        # Copy the plot data
                        for line in plot_widget.ax.get_lines():
                            ax.plot(line.get_xdata(), line.get_ydata(),
                                   color=line.get_color(),
                                   linestyle=line.get_linestyle(),
                                   linewidth=line.get_linewidth(),
                                   label=line.get_label())

                        # Copy axis labels and title
                        ax.set_xlabel(plot_widget.ax.get_xlabel())
                        ax.set_ylabel(plot_widget.ax.get_ylabel())
                        ax.set_title(plot_widget.ax.get_title(), fontsize=10)

                        # Copy vlines if any (red dashed lines)
                        for child in plot_widget.ax.get_children():
                            if hasattr(child, 'get_linestyle') and hasattr(child, 'get_color'):
                                if child.get_linestyle() == '--' and child.get_color() == 'red':
                                    ax.axvline(x=child.get_xdata()[0], color='red', linestyle='--', linewidth=2)

                        # Set axis limits
                        ax.set_xlim(plot_widget.ax.get_xlim())
                        ax.set_ylim(plot_widget.ax.get_ylim())
                    else:
                        # Create empty subplot to maintain grid position
                        ax = fig.add_subplot(gs[row, col])
                        ax.set_visible(False)

        # Save the page
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def _export_kinematics_to_pdf(self, gait_analysis_tab, pdf):
        """
        Export kinematics tab to PDF page.
        """
        layout = gait_analysis_tab.kinematics_layout
        rows, cols = 5, 3
        # Calculate subplot size to make them square
        subplot_size = min(8.27 / cols, 11.69 / rows)  # 2.338 inches
        fig_width = cols * subplot_size
        fig_height = rows * subplot_size
        fig = plt.figure(figsize=(fig_width, fig_height))
        fig.suptitle("Gait 1 Kinematics", fontsize=16, fontweight='bold')

        gs = gridspec.GridSpec(rows, cols, figure=fig, hspace=0.1, wspace=0.1)

        for row in range(rows):
            for col in range(cols):
                item = layout.itemAtPosition(row, col)
                if item and item.widget():
                    plot_widget = item.widget()
                    if hasattr(plot_widget, 'figure') and plot_widget.isVisible():
                        ax = fig.add_subplot(gs[row, col])
                        self._copy_plot_to_ax(plot_widget, ax)
                    else:
                        ax = fig.add_subplot(gs[row, col])
                        ax.set_visible(False)

        pdf.savefig(fig)
        plt.close(fig)

    def _export_kinetics_to_pdf(self, gait_analysis_tab, pdf):
        """
        Export kinetics tab to PDF page.
        """
        layout = gait_analysis_tab.kinetics_layout
        rows, cols = 3, 3
        # Calculate subplot size to make them square
        subplot_size = min(8.27 / cols, 11.69 / rows)  # 2.756 inches
        fig_width = cols * subplot_size
        fig_height = rows * subplot_size
        fig = plt.figure(figsize=(fig_width, fig_height))
        fig.suptitle("Gait 1 Kinetics", fontsize=16, fontweight='bold')

        gs = gridspec.GridSpec(rows, cols, figure=fig, hspace=0.1, wspace=0.1)

        for row in range(rows):
            for col in range(cols):
                item = layout.itemAtPosition(row, col)
                if item and item.widget():
                    plot_widget = item.widget()
                    if hasattr(plot_widget, 'figure') and plot_widget.isVisible():
                        ax = fig.add_subplot(gs[row, col])
                        self._copy_plot_to_ax(plot_widget, ax)
                    else:
                        ax = fig.add_subplot(gs[row, col])
                        ax.set_visible(False)

        pdf.savefig(fig)
        plt.close(fig)

    def _copy_plot_to_ax(self, plot_widget, ax):
        """
        Copy plot data from plot_widget to ax.
        """
        # Copy the plot data
        for line in plot_widget.ax.get_lines():
            ax.plot(line.get_xdata(), line.get_ydata(),
                   color=line.get_color(),
                   linestyle=line.get_linestyle(),
                   linewidth=line.get_linewidth(),
                   label=line.get_label())

        # Copy axis labels and title
        ax.set_xlabel(plot_widget.ax.get_xlabel())
        ax.set_ylabel(plot_widget.ax.get_ylabel())
        ax.set_title(plot_widget.ax.get_title(), fontsize=10)

        # Copy vlines if any (red dashed lines)
        for child in plot_widget.ax.get_children():
            if hasattr(child, 'get_linestyle') and hasattr(child, 'get_color'):
                if child.get_linestyle() == '--' and child.get_color() == 'red':
                    ax.axvline(x=child.get_xdata()[0], color='red', linestyle='--', linewidth=2)

        # Set axis limits
        ax.set_xlim(plot_widget.ax.get_xlim())
        ax.set_ylim(plot_widget.ax.get_ylim())

        # Make plot square
        ax.set_aspect('equal', adjustable='box')
