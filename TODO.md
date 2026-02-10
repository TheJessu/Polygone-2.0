# TODO for Gait Analysis Tab Button Colors and Multi-Import

- [x] Modify update_kinematics_file_buttons_visibility to set checked buttons to light blue (#ADD8E6) regardless of side filter
- [x] Modify update_kinetics_file_buttons_visibility to set checked buttons to light blue (#ADD8E6) regardless of side filter
- [x] Modify update_moments_file_buttons_visibility to set checked buttons to light blue (#ADD8E6) regardless of side filter
- [x] Modify import_c3d_for_kinematics to allow multiple file selection and import up to 5 files
- [x] Modify import_c3d_for_kinetics to allow multiple file selection and import up to 5 files
- [x] Modify import_c3d_for_moments to allow multiple file selection and import up to 5 files
- [ ] Verify changes work as expected (buttons light blue when plot lines visible, white when invisible, blue when highlighted; multi-import works up to 5 files)

# TODO for Window Resizing Fix

- [x] Add resizeEvent to MainWindow in main.py to trigger VTK render on window resize
- [x] Add resizeEvent to C3DViewer in c3d_viewer.py to trigger VTK render on widget resize
- [x] Set size policy for central_widget to expanding in main.py
- [x] Add minimum size to MainWindow in main.py
- [x] Test vertical resizing by running the application
