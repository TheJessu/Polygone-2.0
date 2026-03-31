import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
from PyQt5.QtWidgets import QFileDialog
import numpy as np
import math
import os

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
            ('kinematics', 0, gait_analysis_tab.kinematics_plot_layout, 'kinematics_side_filter'),
            ('kinetics', 1, gait_analysis_tab.kinetics_plot_layout, 'kinetics_side_filter'),
            ('moments', 2, gait_analysis_tab.moments_plot_layout, 'moments_side_filter')
        ]
        sides = ['All', 'Left', 'Right']

        with PdfPages(filename) as pdf:
            for tab_name, tab_index, layout, side_attr in tabs:
                for side in sides:
                    # Set tab active before plotting so canvas has correct dimensions
                    gait_analysis_tab.tab_widget.setCurrentIndex(tab_index)
                    # Set side filter
                    setattr(gait_analysis_tab, side_attr, side)
                    # Update plots
                    gait_analysis_tab.plot_data()
                    # Export page
                    title = f"Gait 1 {tab_name.capitalize()} - {side}"
                    file_entries = self._collect_used_files(gait_analysis_tab, tab_name, side)
                    fig = self._export_layout_to_figure(layout, title, file_entries)
                    if fig:
                        pdf.savefig(fig, dpi=300)
                        plt.close(fig)

            # Export Parameters Tab (Page 10)
            fig_params = self._export_parameters_to_figure(gait_analysis_tab)
            if fig_params:
                pdf.savefig(fig_params, dpi=300)
                plt.close(fig_params)

        # Restore original tab and side filters
        gait_analysis_tab.tab_widget.setCurrentIndex(current_index)
        gait_analysis_tab.kinematics_side_filter = current_kinematics_side
        gait_analysis_tab.kinetics_side_filter = current_kinetics_side
        gait_analysis_tab.moments_side_filter = current_moments_side
        gait_analysis_tab.plot_data()  # Restore plots

    def _collect_used_files(self, gait_analysis_tab, tab_name, side):
        """
        Returns a list of file_entries, each a dict:
          {'filename': str, 'lines': [{'color': str, 'linestyle': str}, ...]}
        """
        line_styles = gait_analysis_tab.line_styles
        red_colors = gait_analysis_tab.red_colors
        green_colors = gait_analysis_tab.green_colors
        multiline = gait_analysis_tab.multiline_importer
        file_entries = []

        if tab_name == 'kinematics':
            visible_idx = gait_analysis_tab.kinematics_visible_file_index
            red_visible = list(gait_analysis_tab.kinematics_red_visible_files)
            green_visible = list(gait_analysis_tab.kinematics_green_visible_files)
        elif tab_name == 'kinetics':
            visible_idx = gait_analysis_tab.kinetics_visible_file_index
            red_visible = list(gait_analysis_tab.kinetics_red_visible_files)
            green_visible = list(gait_analysis_tab.kinetics_green_visible_files)
        elif tab_name == 'moments':
            visible_idx = gait_analysis_tab.moments_visible_file_index
            red_visible = list(gait_analysis_tab.moments_red_visible_files)
            green_visible = list(gait_analysis_tab.moments_green_visible_files)
        else:
            visible_idx = None
            red_visible = []
            green_visible = []

        if multiline.get_num_files() > 0:
            if side == 'All':
                if visible_idx is not None:
                    fd = multiline.imported_files[visible_idx]
                    ls = line_styles[visible_idx % len(line_styles)]
                    file_entries.append({
                        'filename': fd['filename'],
                        'lines': [
                            {'color': red_colors[0], 'linestyle': ls},
                            {'color': green_colors[0], 'linestyle': ls},
                        ]
                    })
            elif side == 'Left':
                for list_idx, idx in enumerate(red_visible):
                    if idx < multiline.get_num_files():
                        fd = multiline.imported_files[idx]
                        ls = line_styles[idx % len(line_styles)]
                        color = red_colors[list_idx % len(red_colors)]
                        file_entries.append({
                            'filename': fd['filename'],
                            'lines': [{'color': color, 'linestyle': ls}]
                        })
            elif side == 'Right':
                for list_idx, idx in enumerate(green_visible):
                    if idx < multiline.get_num_files():
                        fd = multiline.imported_files[idx]
                        ls = line_styles[idx % len(line_styles)]
                        color = green_colors[list_idx % len(green_colors)]
                        file_entries.append({
                            'filename': fd['filename'],
                            'lines': [{'color': color, 'linestyle': ls}]
                        })

        # PXD average shown as grey dashed
        if hasattr(gait_analysis_tab, 'imported_averages') and gait_analysis_tab.imported_averages:
            used_pxd = getattr(gait_analysis_tab, 'imported_pxd_filename', None)
            if used_pxd:
                file_entries.append({
                    'filename': used_pxd,
                    'lines': [{'color': 'grey', 'linestyle': '--'}]
                })

        return file_entries

    def _export_parameters_to_figure(self, gait_analysis_tab):
        """Creates a figure for the Parameters table."""
        table_widget = gait_analysis_tab.parameters_table
        rows = table_widget.rowCount()
        cols = table_widget.columnCount()

        if rows == 0:
            return None

        fig = plt.figure(figsize=(8.27, 11.69))
        ax = fig.add_subplot(111)
        ax.axis('off')
        fig.suptitle("Gait Parameters", fontsize=16, fontweight='bold')

        # Keep \n so units appear on a second line in the table header
        col_labels = [
            table_widget.horizontalHeaderItem(i).text()
            for i in range(cols)
        ]

        # Resolve main file display name
        main_name = gait_analysis_tab.main_filename if gait_analysis_tab.main_filename else "Main File"

        cell_text = []
        cell_colors = []
        # Map: table data-row index → (header_text, original_color) for section headers
        header_rows = {}

        for r in range(rows):
            row_data = []
            row_bg = []
            if table_widget.rowSpan(r, 0) > 1 or table_widget.columnSpan(r, 0) > 1:
                item = table_widget.item(r, 0)
                text = item.text() if item else ""
                # Store original bg color to use as text color in PDF
                orig_color = item.background().color().name() if item else "#000000"
                row_data = [text] + [""] * (cols - 1)
                row_bg = ["#EEEEEE"] * cols  # light gray background instead of full color
                header_rows[len(cell_text)] = orig_color  # data-row index → color
            else:
                for c in range(cols):
                    item = table_widget.item(r, c)
                    text = item.text() if item else ""
                    if c == 0 and text == "Main File":
                        text = f"{main_name} (Main File)"
                    row_data.append(text)
                    row_bg.append("#FFFFFF")

            cell_text.append(row_data)
            cell_colors.append(row_bg)

        the_table = ax.table(
            cellText=cell_text,
            colLabels=col_labels,
            cellColours=cell_colors,
            loc='center',
            cellLoc='center'
        )
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(9)
        # Scale: wider columns (1.1x), taller rows (2x) to fit 2-line headers
        the_table.scale(1.1, 2.0)
        the_table.auto_set_column_width(list(range(cols)))

        # Style column header row (row 0): smaller font, bold
        for c in range(cols):
            cell = the_table[0, c]
            cell.set_fontsize(8)
            cell.get_text().set_fontweight('bold')
            cell.get_text().set_multialignment('center')

        # Style section header rows: colored text, bold, light gray background
        for data_row_idx, orig_color in header_rows.items():
            table_row = data_row_idx + 1  # +1 because row 0 is column header
            for c in range(cols):
                cell = the_table[table_row, c]
                cell.set_facecolor("#EEEEEE")
                if c == 0:
                    cell.get_text().set_color(orig_color)
                    cell.get_text().set_fontweight('bold')

        return fig

    def _export_layout_to_figure(self, layout, title, file_entries=None):
        rows = layout.rowCount()
        cols = layout.columnCount()

        if rows == 0 or cols == 0:
            return None

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.99)

        # --- Draw all legend entries on a single horizontal line below the title ---
        line_len = 0.05      # width of each line sample in figure coords
        line_gap = 0.006     # gap between consecutive samples within one entry
        entry_gap = 0.025    # gap between separate file entries
        text_gap = 0.008     # gap between last line sample and filename text
        char_width = 0.007   # approximate figure-width per character at fontsize 7.5
        legend_y = 0.963     # vertical position of the legend line

        x = 0.05
        for entry in (file_entries or []):
            for line_info in entry['lines']:
                ln = mlines.Line2D(
                    [x, x + line_len],
                    [legend_y, legend_y],
                    color=line_info['color'],
                    linestyle=line_info['linestyle'],
                    linewidth=1.5,
                    transform=fig.transFigure,
                    figure=fig
                )
                fig.add_artist(ln)
                x += line_len + line_gap
            label = os.path.basename(entry['filename'])
            fig.text(x + text_gap, legend_y, label,
                     fontsize=7.5, va='center', ha='left',
                     transform=fig.transFigure)
            x += text_gap + len(label) * char_width + entry_gap

        # GridSpec: legend is one fixed-height line, give the rest to plots
        legend_height = 0.03  # one row of legend
        gs_top = legend_y + legend_height * 0.5 - legend_height - 0.005
        gs_top = 0.955  # fixed: just below the legend line

        gs_rows = rows
        gs = gridspec.GridSpec(
            gs_rows, cols, figure=fig,
            hspace=0.15, wspace=0.15,
            top=gs_top, bottom=0.02,
            left=0.04, right=0.99
        )

        for r in range(rows):
            for c in range(cols):
                item = layout.itemAtPosition(r, c)
                if item and item.widget():
                    plot_widget = item.widget()
                    if hasattr(plot_widget, 'canvas'):
                        try:
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

                            ax = fig.add_subplot(gs[r, c])
                            ax.imshow(img_data)
                            ax.axis('off')
                        except Exception as e:
                            print(f"Error exporting plot: {e}")
                            ax = fig.add_subplot(gs[r, c])
                            ax.set_visible(False)
                    else:
                        ax = fig.add_subplot(gs[r, c])
                        ax.set_visible(False)

        return fig
