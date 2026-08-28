# FriendlyVRI: Webcam-to-Interferometer Pipeline & Dual Camera Walkthrough

This document summarizes the engineering review, bug fixes, multi-camera enhancements, and computer vision upgrades implemented in `friendlyVRI`.

---

## Executive Summary of Enhancements

### 1. Dual-Webcam & Multi-Camera Support
- **Automatic Camera Discovery**: Added `get_available_cameras()` utility in [`Imports/util_scan.py`](file:///Users/smishra/Documents/VRI/friendlyVRI/Imports/util_scan.py) to probe active system video devices (`Camera 0`, `Camera 1`, etc.).
- **Camera Device Selectors**: Added interactive camera selection comboboxes across [`vriTk.py`](file:///Users/smishra/Documents/VRI/friendlyVRI/vriTk.py) and [`vriTkDemo.py`](file:///Users/smishra/Documents/VRI/friendlyVRI/vriTkDemo.py):
  - **Array Scanner Window**: Select between connected webcams (defaults to `Camera 1` for an external overhead camera).
  - **Model Image Selector**: Select between connected webcams (defaults to `Camera 0` for built-in laptop camera).
- **Independent Targeting**: Built-in laptop webcam and external USB webcam are recognized and operated independently at the same time.

### 2. Illuminated Lightbox & Reflective Aluminum Foil Dish Detection
- **Specular White Top-Hat Filtering**: Updated `scan_to_pixcoords()` in [`Imports/util_scan.py`](file:///Users/smishra/Documents/VRI/friendlyVRI/Imports/util_scan.py) to use a White Top-Hat filter (`imgArr - morphological_opening(imgArr)`). This removes uniform background light from illuminated surface lightboxes while cleanly isolating **bright specular glints and reflections off aluminum foil dish elements**.
- **Configurable Target Modes**: Added a **Target Mode** dropdown to `ArrayScanner`:
  - `Reflective Foil (Light Table)` *(Default)*: Optimized for illuminated lightboxes with aluminum foil dish reflections.
  - `Dark Dots (Paper Sheet)`: Traditional dark ink dots on white paper.
  - `Auto Detect`: Automatic local contrast selection.

### 3. Natural Grayscale & Black-Spot Visualization
- **Natural Photo Rendering**: Replaced default `cubehelix` pseudo-color palette with natural grayscale (`plt.cm.gray`), so webcam photos of targets render in realistic colors.
- **Black-Spot Preview**: Scanned lightbox previews for `Reflective Foil (Light Table)` map high-intensity bright specular foil reflections to **black spots on a white background** (using `gray_r`), fulfilling visual display expectations.

### 4. Automated Observation Pipeline & Coordinate Correctness
- **Preserved Custom Configuration Files**: Removed premature `os.remove("arrays/custom.config")` calls so `vriCalc` can read baseline coordinates from disk without `FileNotFoundError`.
- **Automatic Pipeline Execution**: Saving a scanned array automatically populates it into `configOutTab` and triggers real-time calculation of baselines, UV coverage, dirty beam, and visualizer plots.
- **Geographical Orientation**: Corrected North ($N_m$) coordinate mapping in `write_arrayfile` so $Y=0$ maps to North pointing upwards.

---

## Verification & Testing

- **Compilation**: Verified all modified Python files (`Imports/util_scan.py`, `Imports/vriCalc.py`, `vriTk.py`, `vriTkDemo.py`) using `py_compile`. Compilation completed cleanly with exit code `0`.
- **Reflective Foil Lightbox Test**: Executed automated test script in the `vri` conda environment (`/Users/smishra/miniconda3/envs/vri/bin/python`):
  ```text
  [Reflective Foil Mode] Detected 4 aluminum foil dishes on illuminated lightbox.
  X_pix: [130. 230. 460. 360.]
  Y_pix: [100. 180. 200. 290.]
  SUCCESS: Aluminum foil dish reflections on illuminated lightbox detected correctly!
  ```

---

## Quick Start

To launch the application with multi-camera support and lightbox foil scanning:
```bash
python vriTk.py
```
