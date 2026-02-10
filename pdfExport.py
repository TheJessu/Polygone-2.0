import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
from PyQt5.QtWidgets import QFileDialog
import numpy as np
import math

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
                    used_c3d_files, used_pxd = self._collect_used_files(gait_analysis_tab, tab_name, side)
                    fig = self._export_layout_to_figure(layout, title, used_c3d_files, used_pxd)
                    if fig:
                        pdf.savefig(fig, dpi=300)
                        plt.close(fig)

        # Restore original tab and side filters
        gait_analysis_tab.tab_widget.setCurrentIndex(current_index)
        gait_analysis_tab.kinematics_side_filter = current_kinematics_side
        gait_analysis_tab.kinetics_side_filter = current_kinetics_side
        gait_analysis_tab.moments_side_filter = current_moments_side
        gait_analysis_tab.plot_data()  # Restore plots

    def _collect_used_files(self, gait_analysis_tab, tab_name, side):
        used_c3d_files = set()
        used_pxd = None

        # Check if averages are imported
        if hasattr(gait_analysis_tab, 'imported_averages') and gait_analysis_tab.imported_averages:
            used_pxd = getattr(gait_analysis_tab, 'imported_pxd_filename', None)

        # Check multiline files based on tab and side
        if tab_name == 'kinematics':
            if side == 'All':
                if gait_analysis_tab.kinematics_visible_file_index is not None:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[gait_analysis_tab.kinematics_visible_file_index]
                    used_c3d_files.add(file_data['filename'])
            elif side == 'Red':
                for idx in gait_analysis_tab.kinematics_red_visible_files:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[idx]
                    used_c3d_files.add(file_data['filename'])
            elif side == 'Green':
                for idx in gait_analysis_tab.kinematics_green_visible_files:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[idx]
                    used_c3d_files.add(file_data['filename'])
        elif tab_name == 'kinetics':
            if side == 'All':
                if gait_analysis_tab.kinetics_visible_file_index is not None:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[gait_analysis_tab.kinetics_visible_file_index]
                    used_c3d_files.add(file_data['filename'])
            elif side == 'Red':
                for idx in gait_analysis_tab.kinetics_red_visible_files:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[idx]
                    used_c3d_files.add(file_data['filename'])
            elif side == 'Green':
                for idx in gait_analysis_tab.kinetics_green_visible_files:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[idx]
                    used_c3d_files.add(file_data['filename'])
        elif tab_name == 'moments':
            if side == 'All':
                if gait_analysis_tab.moments_visible_file_index is not None:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[gait_analysis_tab.moments_visible_file_index]
                    used_c3d_files.add(file_data['filename'])
            elif side == 'Red':
                for idx in gait_analysis_tab.moments_red_visible_files:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[idx]
                    used_c3d_files.add(file_data['filename'])
            elif side == 'Green':
                for idx in gait_analysis_tab.moments_green_visible_files:
                    file_data = gait_analysis_tab.multiline_importer.imported_files[idx]
                    used_c3d_files.add(file_data['filename'])

        return sorted(list(used_c3d_files)), used_pxd

    def _export_layout_to_figure(self, layout, title, used_c3d_files=None, used_pxd=None):
        rows = layout.rowCount()
        cols = layout.columnCount()

        if rows == 0 or cols == 0:
            return None

        # Create a figure for the PDF page.
        # Increased size for better visibility: 10 x 14 inches.
        fig = plt.figure(figsize=(10, 14))
        fig.suptitle(title, fontsize=16, fontweight='bold')

        # Add text below the title if files were used
        subtitle_lines = []
        if used_c3d_files:
            subtitle_lines.append(f"C3D Files: {', '.join(used_c3d_files)}")
        if used_pxd:
            subtitle_lines.append(f"Average PXD: {used_pxd}")
        if subtitle_lines:
            subtitle = '\n'.join(subtitle_lines)
            fig.text(0.5, 0.95, subtitle, ha='center', va='top', fontsize=10, wrap=True)

        gs = gridspec.GridSpec(rows, cols, figure=fig, hspace=0.4, wspace=0.4)

        for r in range(rows):
            for c in range(cols):
                item = layout.itemAtPosition(r, c)
                if item and item.widget():
                    plot_widget = item.widget()
                    if hasattr(plot_widget, 'canvas'):
                        try:
                            # Get the content of the canvas as a numpy array
                            canvas_width, canvas_height = plot_widget.canvas.get_width_height()
                            buffer = plot_widget.canvas.tostring_rgb()
                            buffer_size = len(buffer)
                            if buffer_size % 3 != 0:
                                raise ValueError(f"Buffer size {buffer_size} not divisible by 3")
                            num_pixels = buffer_size // 3
                            ratio = math.sqrt(num_pixels / (canvas_width * canvas_height))
                            width = int(canvas_width * ratio)
                            height = int(canvas_height * ratio)
                            if width * height != num_pixels:
                                raise ValueError(f"Calculated size {width}x{height} = {width*height}, but num_pixels {num_pixels}")
                            img_data = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 3))

                            # Create a new subplot in the figure and show the image
                            ax = fig.add_subplot(gs[r, c])
                            ax.imshow(img_data)
                            ax.axis('off') # Don't show axes for the image container
                        except Exception as e:
                            print(f"Error exporting plot: {e}")
                            ax = fig.add_subplot(gs[r, c])
                            ax.set_visible(False)
                    else:
                        # Create empty subplot to maintain grid position
                        ax = fig.add_subplot(gs[r, c])
                        ax.set_visible(False)

        return fig
