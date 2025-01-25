# Raspberry Pi High Speed Camera Software Suite

A collection of **Python scripts** intended for **Raspberry Pi**–based image capture, video recording (including high-speed modes), time-lapse automation, color and white balance analysis, ROI selection, and various batch-processing or data-analysis tasks. Most scripts rely on Python 3 and additional libraries (e.g., NumPy, OpenCV, Matplotlib) and may interface with Raspberry Pi camera command-line tools like `raspistill` or `raspivid`.

This suite includes everything from basic camera parameter logging to advanced color calibration, contact-angle measurements for droplets, thermal image batch processing, and generation of time-lapse videos.  

Below is a curated list of each Python script, with its main purpose and usage highlights:

---

## aspectrum.py

### Purpose  
Analyze a set of RGB data as if it were a spectrometer reading, computing “area under curve,” peak detection, etc.

### Description  
- Reads `rgb.csv` and tries to interpret data as spectral scans.  
- Extracts and merges them, identifies channels, normalizes “scan widths,” and calibrates approximate wavelength.  
- Outputs final C for the “analyzed spectrum” plus separate peak info.

### Key Features 
- Generates multiple .png plots of the spectrum (RGB, single channels, area bars).  
- Logs the steps and final adjustments to wavelength. 

---

## autocrop.py

### Purpose
Auto-crop images by detecting uniform borders and optionally leaving extra margins.

### Main Features
- Scans each image’s edges for changes in brightness to trim away uniform areas.
- Allows `-x <marginal>` and `-y <marginal>` to keep some border.
- Can store a `roi.ini` file with normalized crop coordinates.

### Usage Highlights
- Run `autocrop.py` in a folder with the target images.
- Optionally specify `-i <imagefile>` for single-file processing, or let it auto-process all supported images.
- Cropped images are saved to a `crop` folder (or a specified path).

---

## autoexp.py

### Purpose: Iteratively find an optimum exposure value for an image by scanning from low to high shutter speeds.  

### Description  
- Uses thresholds for under-/overexposure, modifies shutter speed, and stops near an optimum.  
- Logs results and saves the final recommended shutter speed.  

---

## awbgains-hypoc.py

### Purpose
`awbgains-hypoc.py` performs a **paired samples t-test** for sets of `(rgain, bgain)` data in two distinct CSV files, verifying the difference in mean coordinates.

### Main Features
1. **Reading Two AWB Series**: Looks for `awbgains-trials-*.csv` files, up to 2.  
2. **Paired t-test**: Compares the difference in **(rgain, bgain)** pairs from Series A and B.  
3. **Decision**: Prints out the test statistic, p-value, and whether it rejects or fails to reject the null hypothesis.

### Usage Highlights
- Null hypothesis: `µ1 - µ2 = 0` for each coordinate (r or b).  
- Expects at least 2 CSV files with columns `rgain_opt`, `bgain_opt`.

---

### awbgains-hypom.py

### Purpose
`awbgains-hypom.py` runs a **paired samples t-test** for two AWB (red/blue) gain CSV sets. Similar to `awbgains-hypoc.py`, but a different approach or naming.

### Main Features
1. **Hypothesis**: `µ1 - µ2 = 0` for each color channel.  
2. **Statistics**: Prints t-statistic, p-value.  
3. **File Pattern**: `awbgains-trials-*.csv`.

### Usage Highlights
- At most 2 files are read.  
- If exactly 2 valid CSVs found, the script performs the test.
---

## awbgains-ksanalysis.py

### Purpose: Perform Kolmogorov-Smirnov test on AWB gains distributions.  

### Description  
- Reads CSV files of AWB trials (where columns might have `rgain_opt` and `bgain_opt`).  
- Calculates distance distributions among gains, does KS test to see if two methods differ significantly.  
- Optionally plots the distributions and saves figures.   

---

## awbgains-mse.py

### Purpose  
Determine optimal red/blue AWB (auto white balance) gains by minimizing MSE of color histograms.

### Description  
- Repeatedly captures frames from a PiCamera while adjusting AWB gains.  
- Uses a “Nelder-Mead” minimization of the color channel distribution differences.  
- Optionally runs multiple trials to compute confidence intervals for final AWB gains.

### Key Features 
- Plots MSE, AWB gain evolution, and logs final recommended gains.  
- Allows normal or analysis mode, with extra CSV data for repeated calibrations.

---

## awbgains-normality.py

### Purpose
`awbgains-normality.py` tests normality for AWB gain samples (red and blue gains) using the Shapiro-Wilk test, then plots histograms and Q-Q plots.

### Main Features
1. **Data Validation**: Expects a CSV (like `awbgains-trials-XXX.csv`) with columns `rgain_opt`, `bgain_opt`.  
2. **Shapiro-Wilk Test**: Distinguishes if distribution might be normal or not.  
3. **Visualization**: Saves histograms, Q-Q plots, and tolerance-interval plots.

### Usage Highlights
- Default file pattern: `awbgains-trials-*.csv`.  
- Generates multiple `.png` figures (histograms, Q-Q, TI).

---

## awbgains-plotter.py

### Purpose
Visualize AWB gains from trials in scatter plots with confidence intervals.

### Description  
- Reads CSV files with AWB data and generates scatter plots.  
- Highlights confidence intervals on plots.  

---

## awbgains.py

### Purpose
`awbgains.py` performs automatic AWB optimization (under RPi camera) using the Nelder-Mead method, capturing multiple iterations to minimize color distance.

### Main Features
1. **Color Dist.**: Minimizes the average absolute distance among R, G, B.  
2. **Iterations**: The user can set a maximum iteration count with `--i`.  
3. **Plots**: Creates CSV logs and figures (like `awbgains-rgain-*.png`, `awbgains-bgain-*.png`).

### Usage Highlights
- Typical usage: `awbgains.py -ss 20000 -i 20`.  
- Requires PiCamera.  
- Writes final `awbgains-data-*.csv` plus summary logs and pictures. 

---
## awbgains-plotter.py

### Purpose
Plot auto white balance (AWB) gains or trials from a CSV file, showing how red and blue gains evolve over iterations.

### Main Features
- Reads CSVs of format `awbgains-trials-XXX.csv` (with columns like `rgain_opt` and `bgain_opt`).
- Plots confidence intervals or normal distribution-based intervals if enough data is present.
- Saves a `.png` with the AWB gain evolution.

### Usage Highlights
- Run `awbgains-plotter.py awbgains-trials-001.csv`.
- Outputs a figure named `awbgains-ci-<timestamp>.png`.
- Helps to see how AWB calibration converges.

---

## awbgains-rtrials.py

### Purpose
`awbgains-rtrials.py` is a simpler script that simply logs the PiCamera’s AWB gains at each trial without optimizing them. It helps see how camera auto AWB changes over multiple captures.

### Main Features
1. **PiCamera**: In each trial, starts preview, sleeps, and reads camera’s AWB gains.  
2. **Data Logging**: Saves a CSV with calibration number, rgain_opt, bgain_opt.  
3. **Confidence Interval**: Summarizes the final mean and 95% CI for both gains.

### Usage Highlights
- `-n`: number of trials.  
- Outputs `awbgains-trials-*.csv` and `.log` summarizing results and confidence intervals.

---

## awb_gains.py

### Purpose  
Obtain the camera’s current auto white balance gains from a Raspberry Pi camera.

### Description  
- Captures a short preview, sets AWB to `auto`, sleeps for stabilization, then prints out the AWB gains.  
- Useful for discovering the recommended red/blue gains in a certain lighting scenario.

### Key Features 
- Does not record images, just prints AWB gain.  

---

## bracket-exposure.py

### Purpose  
Automate exposure bracketing with the Raspberry Pi camera by capturing multiple images at different shutter speeds.

### Description  
- Reads maximum resolution from camera info.  
- Captures a series of images, each with a different shutter speed (`-ss`), from very short to longer exposures.  
- Allows user to specify image quality, ISO, analog/digital gain, and other camera parameters.

### Key Features 
- Stores output images under a named project path.  
- Logs all shot commands and camera settings to a `.log` file.

---

## bw-rgbcombine.py

### Purpose  
Combine three separate BW color channel images (BWR-, BWG-, and BWB- prefixed) into a single RGB image.

### Description  
- Scans the current directory for images named with prefixes “BWR-”, “BWG-”, and “BWB-”.  
- Merges these three channels into a single RGB image and writes it into an `img/` subdirectory.  
- Keeps track of skipped files and logs processing in a text file named `bw-rgbcombine-<folder>.txt`.

### Key Features 
- Creates the `img/` directory if it does not exist.  
- Outputs combined color images and logs results. 

---

## bw-rgbsplit.py
### Purpose: Split color images into BWR, BWG, and BWB channels.  
### Description  
- Instead of normal R/G/B, it extracts the red channel labeled as `BWR-`, green as `BWG-`, blue as `BWB-`.  
- Essentially a simpler variant of splitting channel data (resulting images look grayscale in each color).  

---

## cadrop.py

### Purpose
Performs contact angle analysis (CA) on sessile drop images, extracting droplet geometry (base, height, angles) and computing volume estimates.

### Main Features
- Converts images to grayscale or applies optional levels and ROI cropping.
- Finds drop boundaries using edge detection (`cv2.Canny`).
- Computes contact angles (left and right), drop base and height in mm, plus approximate droplet volume.
- Allows batch processing of images in a directory for time-series analysis.

### Usage Highlights
1. Run `cadrop.py` and specify an input file (`-f`) or a directory (`-d`).
2. Set the calibration resolution (`-res`), baseline (`-base`), optional ROI (`-roi`), and more.
3. Script outputs measurement results (angles, volume) and can save figures to a `figures/` subfolder.
4. Ideal for analyzing a time-lapse series of drop images.

---

## calen.py
### Purpose
`calen.py` calculates horizontal and vertical pixel distances (and optionally calibrates them to a known length in user-chosen units).

### Main Features
1. **Peak Detection**: Uses Savitzky-Golay derivative filtering to locate edges in x and y directions.  
2. **Auto/Manual**: The user can manually confirm or override proposed peak locations.  
3. **Calibration**: If “calibration mode” is chosen, it calculates a “pixels per unit” factor.

### Usage Highlights
- Argument `-d`: sets derivative order (1 or 2).  
- Interactive threshold for peaks.  
- Produces `.log` file with results.

---

## calibratecam.py
### Purpose: Calibrate a Raspberry Pi camera’s exposure and gains by capturing a series of images.  
### Description  
- Takes multiple pictures at various shutter speeds and AWB gains.  
- Measures color channel means, looks for minimal distance among R, G, B to find optimum gains.  
- Logs data, plots results, and suggests a recommended set of gains.  

---

## calscale.py

### Purpose
Determine the pixels-per-unit (e.g., mm, cm) scale from a calibration image by detecting peaks in brightness.

### Main Features
- Loads an image and horizontally or vertically scans for edges/peaks.
- Lets you enter an interval length (e.g., 1 mm or 0.5 in) to calculate a pixel scale.
- Writes log data with the computed scaling factor (e.g., “X pixels per mm”).

### Usage Highlights
- Run `calscale.py calibration_image.png`.
- Provide orientation (horizontal/vertical) and optional threshold and inversion settings.
- Check the resulting log (`cal-<stem>.log`) for the final scale factor.

---

## camapps.py
### Purpose
`camapps.py` is a menu-driven Python script for Raspberry Pi high-speed camera software, grouping multiple camera-related operations under a single text-based user interface.

### Main Features
1. **Menus and Submenus**: Offers categories like Composition, Exposure, White Balance, Image/Video capture, and Image Analysis.  
2. **Integration**: Launches specific Python scripts (e.g., `camera.py`, `rgbinfo.py`) to perform tasks from time-lapse to color analysis.

### Usage Highlights
- Run `camapps.py` to see a list of tasks.  
- Select a numeric option for each task.  
- Press `0` to exit.

---

## camera.py

### Purpose
A script to interactively set various parameters for Raspberry Pi’s camera module, generate a suitable `raspistill` command, and then capture images. Also creates a log file documenting the chosen parameters.

### Main Features
- Detects the Raspberry Pi camera module.
- Interactively prompts for parameters such as ISO, exposure, analog gains, and AWB modes.
- Automatically creates a log file with metadata (e.g., date/time, artist, camera revision, etc.).
- Generates and executes a `raspistill` command tailored to the chosen settings.

### Usage Highlights
1. Run `camera.py`.
2. Follow the interactive prompts for image quality, ISO, exposure time, AWB settings, gains, etc.
3. The script builds the `raspistill` command string and executes it.
4. A log file (`<name>.log`) is created, capturing all parameters and the final command.

---

## camera_model.py

### Purpose  
Query the Raspberry Pi camera info quickly and print sensor make, revision, max resolution, etc.

### Description  
- Uses internal Python calls or a helper (`rpi.camerainfo`) to detect the PiCamera and print out details.  
- If no camera is detected, notifies the user.

### Key Features 
- Simple script for checking connected camera’s parameters. 

---

## campreview.py

### Purpose
Provide a live preview from the Raspberry Pi camera module in full screen or a reduced window.

### Main Features
- Displays camera feed using `picamera` (or a similar library).
- Simple keyboard interface (`ESC` to exit, `ENTER` to confirm starting preview, etc.).
- Useful to quickly check camera framing or focus.

### Usage Highlights
- Run `campreview.py`; follow the console instructions.
- Press `ESC` to end the preview.
- Optionally specify or accept a full-screen preview.

---

## capture-sharpness.py

### Purpose
`capture-sharpness.py` is a server-mode script that captures frames from a camera, calculates a sharpness metric (variance of Laplacian), and optionally saves them for a client script (e.g., `sharpmon.py`) to read.

### Main Features
1. **OpenCV Live Preview**: Displays camera stream, showing sharpness in real time.  
2. **Server Option**: Writes small `var` files `_var;...` in the directory for the client to read.  
3. **Hotkeys**: Press `C` to capture, `ESC` to exit, `S` to enable/disable server mode.

### Usage Highlights
- Possible usage: `capture-sharpness.py -S` for server mode.  
- The client script `sharpmon.py` simultaneously reads `_var;` files to plot sharpness.

---

## capturepics-preview.py

### Purpose: Capture still images with a live preview at reduced resolution.  

### Description  
- Provides a minimal UI.  
- Press `SPACE` to capture an image, `ESC` to exit.  
- Configurable for PNG or JPG, quality, AWB/gains, etc.  
- Writes a log file with relevant settings.  

---

## capturepics.py

### Purpose
Capture multiple still images on Raspberry Pi with adjustable ISO, exposure, AWB, etc., storing them with consistent numbering.

### Main Features
- Interactively sets camera parameters (ISO, exposure in µs, AWB gains).
- Uses `raspistill` in a loop to capture pictures upon pressing the `SPACE` key.
- Names images with a project name + frame number, logging all actions.

### Usage Highlights
- Run `capturepics.py`, set desired parameters.
- Press `ENTER` to start capture mode, `SPACE` to capture each photo, `ESC` to exit.
- Outputs a log and saved images (e.g., `name_0001.png`, `name_0002.png`, etc.).

---

## cropmargins.py
### Purpose  
Crop images by fixed marginal sizes (or a common crop) from the left, right, top, and bottom.

### Description  
- Can process a single image (`-i`) or batch process all images in the current directory of supported formats.  
- Accepts `-c`, `-l`, `-r`, `-t`, `-b` arguments for crop margins.  
- Optionally preserves original extension (`-o`) or fixes odd dimensions (`-f`).

### Key Features 
- Writes cropped images to a `crop/` subdirectory.  
- Allows threshold-based dimension fixing if `-f` is used. 

---

## datamerge.py
### Purpose: Merge multiple CSV files (concatenate them by rows) into one.  
### Description  
- Takes multiple file arguments.  
- Reads them line by line; merges them row-by-row, filling missing lines with a user-specified placeholder.  
- Outputs a combined CSV `xydata.csv`.   

---

## dminexp.py
### Purpose  
Find minimal exposure time for a Raspberry Pi camera that still yields a detectable image.

### Description  
- Iterates over a set of possible microsecond exposures, capturing an image for each.  
- Tracks the average RGB or grayscale values.  
- Helps to determine the shortest feasible shutter speed for the lighting environment.

### Key Features 
- Plots and logs the final curve of brightness vs. shutter speed.  
- Allows optional AWB or manual red/blue gain settings.

---

## expss.py
### Purpose: Compute auto-exposure shutter speed and AWB gains from a Raspberry Pi camera (for reference or debug).  
### Description  
- Opens the camera, sets ISO, waits for auto-exposure to settle.  
- Prints the final shutter speed in microseconds and any AWB gains.  
- Optionally can adjust logic to gather “auto” exposure values. 

---

## fiberangle.py
### Purpose: Measure angles, lengths, and widths of a “fiber” curve from an image’s horizontal scan.  
### Description  
- Scans the top area of the image to detect a bright line or fiber.  
- Extracts the fiber’s (x,y) from a threshold.  
- Optionally rotates the curve to measure angles, calculates length, mean widths, etc.  
- Saves results to separate CSV files, can produce various diagnostic plots (standard, with limits, widths, beta angle, etc.).  

---

## filesampler.py
### Purpose
`filesampler.py` samples files from a directory at user-defined intervals or percentages, copying them into a subdirectory `files/`.

### Main Features
1. **Interval or Percentage Mode**: Takes every *n*-th file or based on a fraction (e.g., 10% of all).  
2. **Inverted Sampling**: Has an option to pick everything except the interval frames.  
3. **Renaming**: Can bare-number or maintain partial naming.

### Usage Highlights
- Prompts user for interval or sample percentage.  
- Optionally inverts the sampling to skip the chosen frames.  
- Copies sampled files to a subdir `files`. 

---

## fpsvideo.py
### Purpose: Capture high-FPS video from a Raspberry Pi camera.  
### Description  
- Asks user for the camera mode, frames per second, shutter speed, etc.  
- Builds a `raspivid` command, optionally runs it, and can also convert `.h264` to `.mkv`.  

---

## frame2images.py
### Purpose: Frame or embed images inside a colored frame of a defined width and color.  
### Description  
- Takes input images, creates a new blank frame background of user-specified size, color, and position.  
- Puts the original image onto that background, optionally with opacity.  
- Saves the results in a new subdirectory.

---

## gen-normgains.py
### Purpose
`gen-normgains.py` generates synthetic red and blue AWB gains following a normal distribution, saving them into a CSV file.

### Main Features
1. **Random Gains Generation**: Uses NumPy to generate `n` samples for `rgain` and `bgain`, each with user-specified mean and standard deviation (`--rs`, `--bs`).  
2. **Statistics**: Prints out mean, std, relative error.  
3. **Visualization**: Optionally plots a scatter distribution of the synthetic gains.

### Usage Highlights
- Main arguments: `-r`, `-b` for means, `-rs`, `-bs` for scale (standard deviation), `-n` for trials.  
- Produces a file named `awbgains-trials-n*.csv`. 

---

## gen_tlfiles.py

### Purpose
Create a sequentially numbered set of images (e.g., `img_0001.ext`) in a new `tl` directory, for use in time-lapse videos.

### Main Features
- Scans the current directory for all `.png` or `.jpg` files.
- Copies them into `tl/` with consistent numbering (`img_0001.png`, etc.).
- Generates a log file showing old and new names.

### Usage Highlights
- Place all your source images (JPG/PNG) in the current folder.
- Run `gen_tlfiles.py` (no arguments).  
- Processed time-lapse images appear in `tl/`.

---

## grayness.py
### Purpose  
Estimate how close an image’s histogram is to perfect gray (equal R/G/B distribution).

### Description  
- Loads a single RGB image using OpenCV, calculates color histograms, and measures MSE across color channels.  
- Prints an approximate “Perfectly Gray” vs. “Not Gray” classification if MSE is below a threshold.

### Key Features 
- Also plots the distribution lists and difference histograms, saving them as `.png`.

---

## gtlvideo.py

### Purpose
Generate a time-lapse or standard video (`.mkv`, `.mp4`, or `.h264`) from a series of images.

### Main Features
- Optionally converts raw CR2 to PNG via `darktable-cli`.
- Resizes/crops images, then calls `ffmpeg` to produce video.
- Allows customizing frame rate, CRF, resolution, and naming.

### Usage Highlights
- Run `gtlvideo.py`; follow prompts for quality, resolution, digits, etc.
- The script organizes multiple stages: CR2->PNG, PNG->cropped PNG, and then final video creation.
- Saves logs and the resulting video in subdirectories (`video/`, etc.).

---

## labels2images.py

### Purpose
`labels2images.py` overlays textual labels onto images (interval-based or from TS/PTS files). 

### Main Features
1. **Modes**:  
   - Interval mode (inserting a numeric time or index).  
   - TS mode (custom text lines from `labels.ts`).  
   - PTS mode (timestamps from a `.pts` file).  
2. **Composite**: Adds text boxes with optional alpha onto images.  
3. **Output**: Saves PNG frames in a subfolder with overlaid labels.

### Usage Highlights
- Flexible alpha and color controls.  
- TSV-like input for lines that can appear or disappear (`++` or `--`). 

---

## levels-batch.py

### Purpose  
Perform a “levels” (black, white, gamma) adjustment on all images in a directory.

### Description  
- Reads a user-defined black point, white point, and gamma.  
- Applies these to each image, writing output to a `levels/` subdirectory.  
- Optionally converts everything to PNG (`-png`).

### Key Features 
- Interactive and command-line modes supported.  
- Logs processes in a `levels-<folder>.log` file. 

---

## mapgains.py

### Purpose: Map red and blue gains for a Raspberry Pi camera in a grid, then find the optimum combination.  

### Description  
- Either captures images in a loop for different (r_gain,b_gain) pairs or reads data from a `.pkl`.  
- Finds minimal color distance (R, G, B).  
- Saves maps, logs the best gains, can do iterative approach for quick calibration.

---

## memanalyze.py

### Purpose
`memanalyze.py` reads a `meminfo.log` file containing memory logs over time, then generates time-series plots of various parameters (e.g., memory usage).

### Main Features
1. **Memory Usage Plot**: Visualizes data columns (like total memory, free memory) over time in separate graphs.  
2. **Automatic Scaling**: Figures out an appropriate time unit (seconds, minutes, hours, or days) based on data range.  
3. **Multiple Graph Generation**: Saves PNG plots for each memory column.

### Usage Highlights
- Requires a log file named `meminfo.log`.  
- Outputs separate `.png` files for each memory metric. 

---

## mkvfix.py

### Purpose
Fix Raspberry Pi playback issues by converting `.mkv` files to `.h264` format, ensuring smoother local playback.

### Main Features
- Uses `ffmpeg` to convert MKV to H.264 with specific profiles (`libx264`, `profile:v high444`, etc.).
- Automatically detects and processes the input MKV file.

### Usage Highlights
- Run `mkvfix.py <video.mkv>` in the same directory.
- The script generates a `.h264` output which can subsequently be converted to `.mp4` if desired (`vid2mp4.py`).

---

## numlog.py

### Purpose
Recognize digits from seven-segment style displays in images, either in batch or real time, and log the results.

### Main Features
- Uses OpenCV to threshold and parse each digit area.
- Batch mode: processes a folder of images.
- Real-time logger: captures from camera, logging digit changes over time.

### Usage Highlights
- `numlog.py -b <images>` for batch OCR, or `numlog.py -r` for real-time logging.
- Adjust digits (`-n`) and decimals (`-p`) if you have decimal points.
- Outputs CSV data of recognized digits vs. time.

---

## ocean-analyze.py
### Purpose: Analyze a set of CSV spectra files from an Ocean spectrometer.  
### Description  
- Reads multiple CSV files containing spectrometer data (with 2 columns: wavelength, intensity).  
- Merges data over a number of scans, normalizes or thresholds if requested, calculates areas, and optionally plots the results.  
- Saves combined or averaged spectra and AUC values to CSV files.  
- Creates a log about the process.

---

## ocean2csv.py
### Purpose
`ocean2csv.py` converts Ocean Insight ASCII spectrometer files (`.txt`) to a simpler CSV format, optionally normalizing if they represent transmission spectra.

### Main Features
1. **Spectral Data Extraction**: Reads lines after the `>>>>>Begin Spectral Data<<<<<`.  
2. **Transmission Mode**: If flagged, can interpret data as % Transmission.  
3. **Batch Conversion**: Processes all matching “start pass filter” files in the directory, saving to a `data/` folder.

### Usage Highlights
- Option `-ts`: treat data as raw transmission, `-tn`: normalized transmission.  
- Writes out CSV with columns: “Wavelength, Intensity”.

---

## optimum_gains.py
### Purpose: Quickly compute the optimum red/blue gains from an existing `rgb-...txt` file.  
### Description  
- Reads a text file with lines of `[name,exposure,rgain,bgain,r_avg,g_avg,b_avg]`.  
- Skips under- or overexposed images.  
- Finds the minimal color distance (RG/GB/etc.) to pick the best red and blue gains.   

---

## `pics2png.py`

### Purpose
Converts all image files (JPG or other formats compatible with PIL) in the current directory into PNG format and saves them in a `png` subdirectory.

### Main Features
- Scans the current directory for valid image files.
- Converts each found image to PNG format using the Pillow library.
- Preserves original width and height in the log messages.
- Outputs converted files to a newly created `png` folder.

### Usage Highlights
1. Place `pics2png.py` in the directory containing images.
2. Run `python3 pics2png.py`.
3. The script creates a `png` folder if it does not exist.
4. Each image is processed and saved as a PNG file with the same base name but with `.png` extension.

---

## pipgen.py

### Purpose
Overlay (“picture-in-picture”) secondary images onto primary/base images at a chosen position.

### Main Features
- Loads a “base” image from one folder and a “PIP” image from another, matching their sequence or numbering.
- Places the PIP top-left, top-center, etc. (based on user choice).
- Outputs combined “master” images to a folder named `master/`.

### Usage Highlights
- Arrange “base” images in `img/` and “PIP” images in `pip/`, each with a consistent naming scheme.
- Run `pipgen.py`, select a position grid (1–9).
- Final overlaid images get written to `master/` directory.

---

## pips2frame.py  

### Purpose
`pips2frame.py` adds Picture-In-Picture (PIP) images over “main frames,” according to a mapping defined in `pip.csv`.

### Main Features
1. **Layering**: For each base frame, it overlays small “pip” images at specified coordinates and alpha level.  
2. **Coordinate & Alpha**: Reads `pip.csv` to place each PIP properly.  
3. **Output**: Saves composited frames (PNG) in a new output folder.

### Usage Highlights
- Directory naming convention: subdirectories named `pip1`, `pip2`, etc.  
- The script uses matching numeric suffixes to align which “pip” belongs on which main frame.

---

## ptbatch.py

### Purpose
Apply a perspective transformation to a batch of images using a stored transformation matrix.

### Main Features
- Reads transformation info (`ptmdata.csv`) generated by other scripts (e.g., `ptransform.py`).
- Transforms all images in a specified directory (JPG, PNG, or user-defined extension).
- Saves output images in a subdirectory (`pt`).

### Usage Highlights
- Place `ptmdata.csv` (containing matrix data) in the working directory.
- Run `ptbatch.py`, selecting file format and confirming transformations.
- Resulting “deskewed” images appear in `pt/`.

---

## pitch.py  
### Purpose  
Measure repeated intervals (pitch) in an image row or column to find the average spacing (e.g., line patterns).

### Description  
- Searches for peaks in a grayscale line profile, calculates mean and median spacing, and converts to a user-chosen scale.  
- Logs the pitch results and optionally plots them.

### Key Features 
- Interactively asks for orientation, minimal distances, and threshold.  
- Outputs pitch in user-chosen units (e.g., mm).

---

## pts-sampler.py  
### Purpose: Sample a `.pts` file (presentation timestamps) at a given interval.  
### Description  
- Takes an input PTS file of timestamps.  
- Reduces / samples the file at a specified integer interval.  
- Writes out a reduced `timelabels.pts`.  

---

## ptsgen.py  
### Purpose: Generates a `.pts` file from file modified times or other logic.  
### Description  
- Scans the current directory for files (by extension), extracts their modification times, then writes them out as timestamps.  
- Allows zero-based or absolute times.

---

## ptsextract.py  

### Purpose
`ptsextract.py` extracts time-stamp data for frames either using each file’s modification time or a user-defined interval, creating a `.pts` file.

### Main Features
1. **File Sequence**: Lists certain files in the directory.  
2. **Generate Timecode**: For each file, it calculates a time offset and writes it to an output file with `.pts` extension.  

### Usage Highlights
- Arguments:  
  - If using `mtime` mode (`-mtime`?), it reads the file modification time.  
  - Otherwise sets a fixed interval.  
- Output format: “timecode format v2”. 

---

## resize-batch.py

### Purpose: Batch-resize images by width or height.

### Description  
- Recursively (or in the current directory) finds PNG/JPG files.  
- Lets you specify target width or height in pixels, plus optional rounding rules.  
- Resizes and saves results into subdirectories (`resize_x` or `resize_y`).  

---

## rgb-histograms.py  

### Purpose: Calculate and plot RGB and grayscale histograms for all images in the current directory.  

### Description  
- Scans images, computes color channel (R, G, B) histograms plus grayscale.  
- Saves numeric histogram data to CSV, as well as the histogram plots as PNG files.  
- Also logs pixel count above/below thresholds if specified.  

---

## rgb-iratios.py  

### Purpose  
Compute and plot internal color ratios from a standard `rgb.csv` data file.

### Description  
- Reads columns (bw, r, g, b) from CSV.  
- Calculates R/G, R/B, G/R, G/B, B/R, B/G, and also ratio to the mean of other channels (R/GB, etc.).  
- Plots these ratio trends and saves them in a subdirectory.

### Key Features 
- Handles times or frame counts on the x-axis.  
- Accepts optional start/interval/time unit arguments to label the x-axis. 

---

## rgb-scatter.py  

### Purpose: Generate scatter/line plots from an RGB CSV file.  

### Description  
- Reads `rgb.csv` format with columns `[Number, BW, R, G, B]` or `[X, #, BW, R, G, B]`.  
- Plots BW and RGB mean values (either lines, markers, or both).  
- Allows auto Y-scaling, grid toggling, etc.  
- Creates an updated CSV file with consistent headers and saves the plots. 

---

## rgb-sgraph.py  

### Purpose  
Smooth and plot grayscale or RGB data from a CSV file, using various smoothing algorithms (Moving average, Savitzky–Golay).

### Description  
- Reads a CSV with columns for “evaluation,” “bw,” “red,” “green,” “blue,” etc.  
- Provides a user interface to choose smoothing windows, brackets for labels, or merges.  
- Produces multiple plot outputs, including smoothed data with optional alpha overlay of raw data.

### Key Features 
- Saves the smoothed data as `sdma-...csv` or `sdsg-...csv`.  
- Creates various PNG plots with or without the original data overlaid. 

---

## rgbcombine.py  

### Purpose  
Combine three color channel images prefixed `R-`, `G-`, and `B-` into a single full-color image.

### Description  
- Loads each channel as color data, merges them into one.  
- Saves to a local `img/` folder, logs any missing or invalid images.

### Key Features 
- Overwrites if channels are missing by filling them with black.  
- Creates a final color image (`R/G/B -> B/G/R` rearrangement).

---

## rgbinfo.py

### Purpose: Summarize mean RGB for each image (simple version).  

### Description  
- Iterates over images, logs shape and mean R/G/B intensities.  
- Saves the results in a text file.  

---

## rgbmean.py

### Purpose
Reads all images in a directory (or processes an existing `rgb.csv` in file mode) and calculates the average Red, Green, Blue, and “grayscale” (BW) values for each image. Can also generate plots of these values over time or frame index.

### Main Features
- Automates computation of mean RGB channels using OpenCV or from existing CSV data.
- Optionally starts from a specific “time” and increments by a set interval (for time-based plots).
- Writes the results to a `rgb.csv` file (or updates one in “file mode”).
- Can produce plots (`RGB-mean.png` and `BW-mean.png`) if multiple images are processed.

### Usage Highlights
1. **Basic Mode**: Place `rgbmean.py` in a folder with images, then run:
   ```bash
   python3 rgbmean.py
   ```
   - Generates `rgb.csv` and plots in `rgb/` subfolder.
2. **File Mode** (`-f`): Reprocess an existing `rgb.csv` with new time intervals:
   ```bash
   python3 rgbmean.py -f -s <start> -i <interval> -u "time unit"
   ```
3. Set `-y` to auto-scale the y-axis in the generated plots, and `-d` to display them.

---

## rgbratio.py  

### Purpose
Compute the ratio of two RGB CSV files: `rgb.csv` and `rgbref.csv`.  

### Description  
- Reads two CSV files with matching lengths.  
- Divides the RGB values of the first by the second (e.g., R/Rref, G/Gref, B/Bref, Gray/Grayref).  
- Produces ratio CSV output and optionally plots the results.  

---

## rgbsplit.py  

### Purpose: Split an RGB image into separate R, G, B, and grayscale images.  

### Description  
- Reads all PNG/JPG images in the current folder.  
- For each image, creates four output images: R-channel, G-channel, B-channel, and grayscale.  
- Logs the processing and image dimensions. 

---

## rgbxy.py

### Purpose: For each image in the directory, calculates x/y profiles (RGB or BW) and saves them as CSV + plots.  

### Description  
- Reads each image, calculates line profiles either in the horizontal (x) or vertical (y) directions.  
- Plots them or saves them to CSV.  
- Multiple options to analyze only RGB, only BW, or both.  
- Creates a log with runtime information.  

---

## rgbxy-iratios.py

### Purpose
Compute internal color ratios (e.g., R/G, R/B, G/B, plus extended ratios) from a CSV of (x, R, G, B) data.

### Main Features
- Reads an input CSV (like `rgb.csv`) with columns `[x,R,G,B,(BW)]`.
- Calculates various color ratios: `R/G`, `R/B`, `G/R`, `G/B`, `B/R`, `B/G`, and extended combinations like `R/GBmean`.
- Outputs a new CSV (`rgbratios.csv`) and a series of plots (in a created directory).

### Usage Highlights
- Run `rgbxy-iratios.py rgb.csv` (or your input file).
- Choose clipping/scaling options when prompted.
- Script saves numerical results and visual plots under a folder named after the input file (e.g., `rgb-rgbratios/`).

---

## rgbxy-peaks.py  

### Purpose: Find peaks and valleys in RGB data from an input CSV (presumably generated by a script like `rgbxy.py`).  

### Description  
- Reads `rgbxy`-formatted data from a CSV.  
- Uses SciPy’s `find_peaks` and related functions to locate peaks and valleys.  
- Saves the results (positions, heights, areas, etc.) to `peaks.csv` and generates diagnostic plots (peak/valley figures for each channel).  
- Creates a log file containing the parameters and results.

---

## roixy.py

### Purpose
`roixy.py` is an interactive ROI selection tool specifically for XY matrix data in CSV format (or a generated “thermogram”).

### Main Features
1. **Heatmap Generation** (optional): Can generate a dummy thermogram and display it as an image.  
2. **Matrix Visualization**: Visualizes data using an OpenCV colormap and allows user to drag-select an ROI.  
3. **INI Output**: Saves the ROI definition (crop coordinates) into a file named `roixy.ini`.

### Usage Highlights
- Command-line flags:  
  - `-n`: XY data file,  
  - `-g`: generate a sample thermogram,  
  - `-cmap`: choose a colormap,  
  - `-l`: list available colormaps.  
- After ROI selection, it saves sub-images (`roixy-fov.png`, `roixy-crop.png`) and `roixy.ini`.

---

## roi-aselect.py  

### Purpose
`roi-aselect.py` is an interactive Python script for selecting a Region of Interest (ROI) in an image. After loading an image file, you can click on it with your mouse to define the ROI boundaries automatically based on brightness thresholds.

### Main Features
1. **Threshold-based ROI edge detection**: The script uses mean value comparisons and threshold adjustments to find upper, lower, left, and right boundaries once you click an initial point in the image.  
2. **Interactivity**: You can left-click on the image to propose a new ROI or right-click to remove it.  
3. **Data Output**: Once ROI selection is confirmed, the script writes the ROI definition to `roi.ini` and saves images of the marked ROI patch, the ROI selection, and the cropped ROI itself.

### Usage Highlights
- Required argument `-f/--file`: Image filename.  
- Optional arguments:
  - `-t`: Threshold value (float).  
  - `-s`: Selection cross size.  
  - `-u`: Enable “under threshold” selection.  
  - `-o`: Enable “over threshold” selection.

---

## roi-batch.py

### Purpose  
Apply an ROI-based crop operation to multiple images according to an `roi.ini` file.

### Description  
- Reads `roi.ini` for crop coordinates or normalized ROI values.  
- Crops all images in the current directory that match the dimension constraints.  
- Outputs cropped images into an `roi/` directory.

### Key Features 
- Can optionally convert images to PNG if `-p` is used.  
- Skips images that do not match the original dimension references in the ROI file.

---

## roi-manual.py

### Purpose
`roi-manual.py` allows manually defining ROI coordinates in a text-based interface rather than a GUI.

### Main Features
1. **Manual Cropping**: Prompts user for image or manual dimension input.  
2. **Generates `roi.ini`**: Stores original width/height plus the cropping coordinates and normalized ROI.  

### Usage Highlights
- If no image argument provided, prompts for manual “width, height.”  
- Interactively requests `x0, y0, width, height` (or `x1, y1`) for the ROI. 

---

## roi-picture.py  
### Purpose
`roi-picture.py` provides a small PySimpleGUI-based interface to select an ROI on a single image, saving the selection to `roi.ini`.

### Main Features
1. **GUI**: Uses PySimpleGUI to prompt for an initial frame path, then OpenCV’s `selectROI` for interactive region selection.  
2. **Result**: Writes `roi.ini` plus a cropped ROI image (`roi-image.jpg`).

### Usage Highlights
- Requires PySimpleGUI installed.  
- The user chooses an image path, then drags the ROI area in an OpenCV preview window. 

---

## roi-preview.py  
### Purpose: Preview a selected camera ROI (region of interest) on a Raspberry Pi camera.  
### Description  
- Reads ROI values from a configuration or predefined code.  
- Uses the Raspberry Pi camera to start a preview window.  
- Allows toggling between full FOV and the defined ROI by pressing the spacebar.  
- Exits on `ESC`.

---

## roi-sharpness.py  
### Purpose: Live video preview with ROI sharpness level monitoring.  
### Description  
- Streams from the Pi camera, calculates variance-of-laplacian for the region of interest.  
- Displays the numeric sharpness on the preview.  
- Press keys for toggling overlay, console prints, or to exit.    

---

## roi-select.py

### Purpose
Interactively define an image’s region of interest (ROI) by selecting four corners or a rectangular bounding box.

### Main Features
- Opens an image via OpenCV (e.g., `cv2.imshow`) and allows user mouse clicks to define corners.
- Saves the resulting coordinates to a file (often `roi.ini`).
- Typically used with other scripts to crop or transform the image.

### Usage Highlights
- Run `roi-select.py <image>`.
- Click corners to define your region, then press a key to finalize.
- `roi.ini` (or similar) is created for subsequent usage.

---

## roiapps.py

### Purpose
A small menu-based launcher for a set of ROI (Region Of Interest) utilities.

### Main Features
- Presents a textual menu to run scripts like `roi-select.py`, `roi-picture.py`, `roi-preview.py`, `roi-batch.py`, etc.
- Groups tasks into categories like composition, focusing, etc.
- Simplifies usage for frequent ROI-related tasks.

### Usage Highlights
- Run `roiapps.py`.  
- Choose from displayed numeric menu options.
- The selected utility script will launch in a separate shell environment.

---

## roixy-crop.py

### Purpose
Select a portion of a 2D numeric matrix (often a thermal map) and save that region of interest.

### Main Features
- Reads a CSV or TXT array of numeric data (like temperature values).
- Displays it as an image with a color map, allowing the user to draw a bounding rectangle (OpenCV).
- Writes the chosen crop coordinates to a file (`roixy.ini`), plus optional images of the full FOV and the cropped region.

### Usage Highlights
- `roixy-crop.py -n <thermogram.csv>` or use `-g` to generate a test thermogram.
- Select ROI in the displayed window, press Enter.
- Cropped matrix and `roixy.ini` get saved.

---

## rpm2rt.py

### Purpose
Converts revolutions per minute (RPM) values into the corresponding revolution time in seconds, milliseconds, or microseconds.

### Main Features
- Accepts a single **RPM** integer (or float) as the primary positional argument.
- Use the `-a` option to print revolution time in all units (seconds, ms, and µs).
- Use the `-b` option to print only the bare time value (in seconds).
- Rounds or truncates times to a specified number of decimal places.

### Usage Highlights
1. **Default usage** (prints revolution time in milliseconds):
   ```bash
   python3 rpm2rt.py 300
   ```
   - Calculates and displays the revolution time for 300 RPM in milliseconds.
2. **Print all units**:
   ```bash
   python3 rpm2rt.py 600 -a
   ```
   - Shows revolution time in seconds, milliseconds, and microseconds.
3. **Print only a bare time in seconds**:
   ```bash
   python3 rpm2rt.py 1200 -b
   ```
4. **Display help**:
   ```bash
   python3 rpm2rt.py -h
   ```
---

## sharpmon.py  

### Purpose
`sharpmon.py` is a client-side script for real-time monitoring of image sharpness values generated by a server-side script (`capture-sharpness.py`).

### Main Features
1. **Live Graphing**: It continuously plots the “Variance of Laplacian” values in a matplotlib window.  
2. **Server-based**: Expects the server script to produce `_var;*` files; it reads these files to update the graph.

### Usage Highlights
- **Dependence**: Must run simultaneously with `capture-sharpness.py` in the same directory.  
- No specific command-line arguments. It looks for matching files with `_var;` pattern in the directory.

---

## testlines.py  
### Purpose
`testlines.py` modifies an image by adding multiple colored vertical lines (e.g., test patterns) that can progressively increase or decrease R, G, B channel intensities along the x-axis.

### Main Features
1. **Line Patterns**: For each line, it changes pixel values in R, G, B by some factor.  
2. **Gradients**: Optionally left, right, or both sides for smooth color transitions.  
3. **Comparison**: Saves difference plots (RGB difference from the original) and the new “patched” image.

### Usage Highlights
- Command-line flags for line width (`-w`), spacing (`-d`), step (`-s`), color factors (`-rf`, `-gf`, `-bf`).  
- Creates an output folder named after the original image’s stem.

---

## thasc2txt.py

### Purpose
Parse and convert “Thermal ASC” (ASCII-based thermal images) files into CSV or TXT for further analysis.

### Main Features
- Extracts the `[Settings]` and `[Data]` blocks, ignoring or storing each properly.
- Writes numerical temperature data into `.txt` or `.csv`.
- Creates a summary log listing all successful conversions.

### Usage Highlights
- Place `.asc` thermal files in the same directory.
- Run `thasc2txt.py`, which finds all `.asc` and generates `.txt` in a subfolder.
- Check `files.log` for a record of conversions.

---

## thermfilter.py

### Purpose
Filter and interpolate missing frames in thermal camera logs.

### Description  
- Reads a log with thermal data (min, max, var).  
- Identifies and discards outlier frames.  
- Copies valid heatmap `.txt` files to a new folder, interpolates missing frames if needed.

---

## thermoga.py

### Purpose
Analyze and visualize thermal data (from `.txt` or `.csv` “thermogram” files) over multiple frames or time-lapse.

### Main Features
- Computes min, max, mean, median, percentile thresholds, etc.
- Can generate binary masks (hot/cold areas) and store them as images or scatter plots.
- Produces time-series results (e.g., how hot area changes across frames) with multiple subdirectories for data, figures, results.

### Usage Highlights
- Run `thermoga.py`, specifying thresholds, or decile-based mask modes (`-masks`, `-dec`).
- It scans numeric data files in the current directory, applying user-specified threshold logic.
- Outputs results in time-stamped folders (`YYYYMMDD-HHMMSS-...`) for easy organization.

---

## timelapse.py

### Purpose
A simpler time-lapse script that prompts for parameters (like ISO, exposure, interval, and duration) then builds and optionally executes a `raspistill` time-lapse command.

### Main Features
- Interactively acquires settings (ISO, quality, exposure, analog gain, AWB, etc.).
- Calculates the `-tl` (time-lapse interval) and `-t` (duration) arguments.
- Creates a log file documenting all parameters and the generated command.
- Provides an option to either execute the `raspistill` command immediately or show it for manual usage.

### Usage Highlights
1. Run `timelapse.py`.
2. Enter the requested parameters (e.g., path to save images, project name, interval, etc.).
3. Choose whether to start the time-lapse immediately (`raspistill` runs) or simply display the command.
4. Log file is created in `<path>/<projectname>.log`.

---

## tlcron.py

### Purpose
Automates time-lapse photography using the Raspberry Pi’s `cron` for scheduling. Simplifies starting, stopping, and capturing frames at specified intervals.

### Main Features
- Creates or removes cron jobs to call itself for capturing images.
- Maintains a lock file to track time-lapse status.
- Allows specifying intervals in minutes/hours for the cron-based triggers.
- Generates an optional log file and ID for frames (`TLID`), ensuring continuity even after reboots.

### Usage Highlights
1. **Initial Setup** (no arguments):  
   ```bash
   python3 tlcron.py
   ```
   - Prompts for time-lapse settings (ISO, quality, intervals, etc.).
   - Creates a `.tlcron.lock` file and modifies the user’s crontab.
2. **Start**:  
   ```bash
   python3 tlcron.py -s
   ```
   - Begins the time-lapse.
3. **Capture**: cron automatically executes `tlcron.py -c` at intervals.
4. **Stop**:  
   ```bash
   python3 tlcron.py -e
   ```
   - Clears the crontab entries and removes the lock file.

---

## tlcronmin.py

### Purpose
Manage time-lapse on a Raspberry Pi using `cron` scheduling: start, stop, and capture frames at set intervals.

### Main Features
- Automates `raspistill` commands, editing crontab for once-per-minute captures (or desired frequency).
- Commands:  
  - `tlcronmin.py` (setup),  
  - `tlcronmin.py -s` (start),  
  - `tlcronmin.py -e` (end),  
  - `tlcronmin.py -c` (capture one frame).
- Keeps a log file and a lock file to avoid collisions.

### Usage Highlights
- Run `tlcronmin.py` to configure; then `tlcronmin.py -s` to start the job in crontab.
- `-e` ends/stops the time-lapse job, clearing crontab entries.
- Inspect logs in the current directory for time-lapse info.

---

## tlgraph-csv.py  
### Purpose: Generate a time-lapse style line or scatter plot from columns in a CSV file.  
### Description  
- Takes a CSV, picks one column as X, and multiple columns as Y for primary or secondary axes.  
- Creates sequential or final plots.  
- Has many optional parameters for styling, legend, log-scale, etc.

---

## tlgraphs-xy.py

### Purpose
`tlgraphs-xy.py` transforms XY data (2D or more columns) into a time-lapse series of images, each an incremental line or scatter. 

### Main Features
1. **Interval-based Plotting**: Plots partial data up to each row, saving sequential PNG images.  
2. **Logarithmic Axes**: Option to set x- or y-axis to log scale.  
3. **Labels**: Asks user for auto or custom labels for x- and y-axes.

### Usage Highlights
- Default reads `xydata.csv`.  
- Interval for data lines and the final images are stored in `xy_tl/` subdirectory.

---

## tlgraphs-rgb.py

### Purpose
`tlgraphs-rgb.py` reads `rgb.csv` (with columns for time/frames and RGB channels) and generates a series of partial plots that can be used as frames in a time-lapse (in `rgb_tl/`).

### Main Features
1. **Data Interval**: Takes every `n`th row.  
2. **Multi-Channel**: The script can handle R, G, B, and BW columns, plotting them over time or numeric X.  
3. **PNG Output**: Saves incremental frames for each row, which can later be turned into a video.

### Usage Highlights
- Asks user about axis labeling, scales, and bracket styles for time.  
- Creates subfolder `rgb_tl/`.  

---

## tlpicam.py

### Purpose
A Python script for time-lapse photography using a Raspberry Pi and PiCamera. It enables configurable intervals, exposure/white balance settings, ISO, optional relay control for powering external components, and improved timing accuracy.

### Main Features
- **Interval Capture:** Choose second- or minute-based intervals with up to 8-digit zero-padded filenames.  
- **Exposure & AWB Control:** Auto/manual exposure, ISO (100–800), and manual gains if AWB is off.  
- **Relay Support (Optional):** Toggle GPIO pins to power external devices only when needed.  
- **Accurate Timing:** Uses `perf_counter()` for stable intervals, unaffected by system clock changes.  
- **Logging:** Creates `tlpicam.log`, recording settings, start/end times, and any delayed frames.

### Usage Highlights
1. **Configuration:** Run interactively to set quality, ISO, exposure, AWB, and intervals.  
2. **Precision:** Aligns capture to the next whole second, leading to more consistent timestamps.  
3. **Why `perf_counter()`:** Ensures interval accuracy, ignoring clock shifts (e.g., NTP, daylight savings).  
4. **Relay Automation:** Automatically turns a relay on/off based on your interval settings, saving energy.  
5. **Enhanced from Original:** Better timing precision and independence from system clock adjustments.

---

## vid2mp4.py  
### Purpose  
Convert an existing MKV (or other format) video into MP4 using `MP4Box` or `ffmpeg`.

### Description  
- Optionally parses a `.pts` file to adjust frame rate (`-rec` or `-fps`).  
- Performs minimal parse of interval data, can do distribution analysis.  
- Finally calls `MP4Box` to produce `.mp4`.

### Key Features 
- Logs the entire process, calculates new playback speeds or normalizes frame intervals.

---

## vid2pic.py  
### Purpose  
Extract frames from a video file (using `imageio` + `ffmpeg`) into `.jpg` or `.png` images.

### Description  
- Takes a video file, enumerates each frame, and saves them in an `img/` directory.  
- User can specify output image format (`-png` for PNG or default `.jpg`).

### Key Features 
- Logs final extraction count and time.  
- Useful for converting a short video clip into a frame sequence.

---

## vidpreview.py  
### Purpose: Preview video modes on a Raspberry Pi camera.  
### Description  
- Lists various predefined video modes for Pi Camera.  
- Lets the user select a mode (resolution and crop).  
- Starts a preview of that particular ROI for video capturing.  
- Exits on `ESC`. 

---

## vrecorder.py

### Purpose
A comprehensive video recording tool for Raspberry Pi, allowing customized video parameters (e.g., resolution, frame rates, gains, etc.). Can also produce a `.mkv` container file after recording.

### Main Features
- Uses `raspivid` internally but allows more flexible, interactive parameter settings.
- Supports automatic or manual naming of recorded files (`.h264` plus optional conversion to `.mkv`).
- Accepts command-line arguments to override default or saved (`.ini`) parameters.
- Logs key camera parameters, frames, and timestamps.

### Usage Highlights
1. Run `vrecorder.py` without arguments for an interactive setup:
   ```bash
   python3 vrecorder.py
   ```
2. Or provide command-line arguments (e.g., `-name <video_name>` or `-fps <value>`).
3. Depending on user input, the script:
   - Creates an `.ini` file with selected parameters.
   - Records an H.264 video and optionally converts to MKV using `mkvmerge`.
   - Writes a `.log` file with all execution details and optional frame statistics.

---

## xy-sgraph.py

### Purpose
Smooth and plot XY data (with either a moving average or Savitzky-Golay filter) from an input CSV.

### Main Features
- Loads a 2-column or multi-column CSV, focusing on the first two columns as X and Y data.
- Applies user-chosen smoothing (`1` = moving average, `2` = Savitzky-Golay).
- Saves the smoothed data and generates line plots.

### Usage Highlights
- Command: `xy-sgraph.py data.csv`.
- Chooses method (moving average or Savitzky-Golay) and smoothing window size in an interactive prompt.
- Outputs “smooth data” files and `.png` plots.

---

## xyarray.py

### Purpose
Combines two data files (one for x-axis data, another for y-axis data) into a single CSV-formatted array (`xydata.csv`) for further analysis or plotting.

### Main Features
- Reads two separate files containing x-values and y-values, respectively.
- Allows optional bracket/label adjustments for column headers.
- Merges data into a single CSV file (`xydata.csv`) with consistent labeling.
- Handles different extension conventions (e.g., `.pts` files vs. generic data files).

### Usage Highlights
1. Run `xyarray.py` with two arguments: the x-data file and y-data file:
   ```bash
   python3 xyarray.py xdata.txt ydata.txt
   ```
2. Follow interactive prompts for bracket style, labeling, etc.
3. The combined data is written to `xydata.csv`.

---

### License

All scripts authored by **(c) Kim Miikki** and, in some cases, additional contributors.  
See individual script headers for licensing details or usage constraints if any.

---

**Note:**  
These scripts assume a functioning **Raspberry Pi camera** environment, often requiring certain Python modules (e.g., `numpy`, `matplotlib`, `opencv-python`, `PIL`, `python-crontab`, `ffmpeg`, etc.) and/or system utilities (`raspistill`, `raspivid`, `darktable-cli`). Make sure to install all dependencies (via `apt`, `pip`, or your preferred package manager) before using these tools.

---

## Usage Notes

1. **Python 3** is recommended for all scripts.  
2. Some scripts rely on specific hardware (HQ camera, PiCamera) or external command-line tools (`ffmpeg`, `darktable-cli`).  
3. Many scripts are **interactive**—they prompt for parameters (file extension, intervals, AWB gains, etc.). For advanced usage, check each script’s built-in `--help` or docstring (where available).  
4. **Batch processing**: Many scripts detect all images in a directory if no single file is specified.

---

**Author**  
[**Kim Miikki**](https://github.com/kmiikki/rpi-camera) (and collaborators), 2019–2024

Use, adapt, or improve these scripts as needed for Raspberry Pi camera tasks, image transformations, color analysis, time-lapse automation, or thermal data workflows.

