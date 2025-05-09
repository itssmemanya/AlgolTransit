import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.visualization import ZScaleInterval
from photutils.detection import DAOStarFinder
from matplotlib.backends.backend_pdf import PdfPages
from scipy.spatial import KDTree
from datetime import datetime
import pandas as pd

folder_path = '/home/manya/Documents/Reduction3/'
fits_files = [f for f in os.listdir(folder_path) if f.endswith(".fits") and f.startswith("algol")]
fits_files.sort(key=lambda x: datetime.strptime(x.split("_")[2].replace(".fits", ""), "%Y-%m-%dT%H:%M:%S.%f"))

zscale = ZScaleInterval()

def detect_stars(image_data):
    daofind = DAOStarFinder(fwhm=5.0, threshold=1.5 * np.std(image_data))
    sources = daofind(image_data)
    if sources is None or len(sources) == 0:
        return np.array([])
    return np.array([sources["xcentroid"], sources["ycentroid"]]).T

def find_star(image, x_guess, y_guess, search_box=20):
    ny, nx = image.shape
    x_min, x_max = max(0, int(x_guess - search_box)), min(nx, int(x_guess + search_box))
    y_min, y_max = max(0, int(y_guess - search_box)), min(ny, int(y_guess + search_box))
    cropped_image = image[y_min:y_max, x_min:x_max]
    if cropped_image.size == 0:
        return None
    cropped_image = np.nan_to_num(cropped_image)
    stars = detect_stars(cropped_image)
    if len(stars) == 0:
        return None
    stars[:, 0] += x_min
    stars[:, 1] += y_min
    kdtree = KDTree(stars)
    _, idx = kdtree.query([x_guess, y_guess])
    return tuple(stars[idx])

algol_positions = [] 
ref1_pos = []
ref2_pos = []
ref3_pos = []
timestamps = []
filenames = []
exposures = []

# Initial guesses from DS9
ref1_guess = (1355, 340)
ref2_guess = (1704, 591)
ref3_guess = (441, 642)

# Processing Each Frame
for file in fits_files:
    file_path = os.path.join(folder_path, file)
    with fits.open(file_path) as hdul:
        image_data = hdul[0].data
        header = hdul[0].header
        x_guess_algol, y_guess_algol = header["PHDLOCKX"], header["PHDLOCKY"]
        timestamp = header["DATE-OBS"]

    algol_pos = find_star(image_data, x_guess_algol, y_guess_algol)
    ref1_found = find_star(image_data, *ref1_guess)
    ref2_found = find_star(image_data, *ref2_guess)
    ref3_found = find_star(image_data, *ref3_guess)

    algol_positions.append(algol_pos)
    ref1_pos.append(ref1_found)
    ref2_pos.append(ref2_found)
    ref3_pos.append(ref3_found)
    
    timestamps.append(timestamp)
    filenames.append(file)
    exposures.append(header["EXPOSURE"])  

    ref1_guess = ref1_found
    ref2_guess = ref2_found
    ref3_guess = ref3_found


# Saving to CSV
data = {
    "filename": filenames,
    "exposure": exposures,
    "timestamp": timestamps,
    "algol_x": [pos[0] for pos in algol_positions],
    "algol_y": [pos[1] for pos in algol_positions],
    "ref1_x": [pos[0] for pos in ref1_pos],
    "ref1_y": [pos[1] for pos in ref1_pos],
    "ref2_x": [pos[0] for pos in ref2_pos],
    "ref2_y": [pos[1] for pos in ref2_pos],
    "ref3_x": [pos[0] for pos in ref3_pos],
    "ref3_y": [pos[1] for pos in ref3_pos],
}
df = pd.DataFrame(data)
df.to_csv("tracked_positions.csv", index=False)
print("Saved tracked positions to 'tracked_positions.csv'")

with PdfPages("tracked_frames.pdf") as pdf:
    for i, file in enumerate(fits_files):
        file_path = os.path.join(folder_path, file)
        with fits.open(file_path) as hdul:
            image_data = hdul[0].data

        vmin, vmax = zscale.get_limits(image_data)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(image_data, origin='lower', cmap='gray', vmin=vmin, vmax=vmax)

        ax.plot(*algol_positions[i], 'rX', markersize=12, label='Algol')
        ax.plot(*ref1_pos[i], 'go', label='Ref Star 1')
        ax.plot(*ref2_pos[i], 'bo', label='Ref Star 2')
        ax.plot(*ref3_pos[i], 'yo', label='Ref Star 3')

        ax.set_title(f"Frame: {file}\n{timestamps[i]}")
        ax.set_xlabel("X (pixels)")
        ax.set_ylabel("Y (pixels)")
        ax.legend()
        pdf.savefig(fig)
        plt.close(fig)

print("Saved all annotated frames to 'tracked_frames.pdf'")

