import os
import numpy as np
from astropy.io import fits
from scipy.ndimage import gaussian_filter

def high_pass_filter(flat_data, sigma=50):
    # Returns a high-pass filtered version of the flat field
    smoothed = gaussian_filter(flat_data, sigma=sigma)
    high_pass_flat = flat_data / smoothed
    return high_pass_flat

def apply_flat_correction(flat_path, input_dir, output_dir, sigma=50):
    with fits.open(flat_path) as hdu:
        flat_data = hdu[0].data
        flat_data /= np.median(flat_data)  # Normalize
        flat_processed = high_pass_filter(flat_data, sigma=sigma)
        print(f"Flat frame loaded and normalized from: {flat_path}")

    for filename in os.listdir(input_dir):
        if (filename.startswith("algol") or filename.startswith("capella") or filename.startswith("dark")) and filename.endswith('.fits'):
            file_path = os.path.join(input_dir, filename)
            with fits.open(file_path) as hdu:
                sci_data = hdu[0].data
                sci_header = hdu[0].header

            corrected_data = sci_data / flat_processed
            new_path = os.path.join(output_dir, filename)
            fits.writeto(new_path, corrected_data, sci_header, overwrite=True)
            print(f"Processed and saved: {filename}")

flat_file = "/home/manya/Documents/Reduction1/flat_0.05_2025-02-28T18:43:57.341.fits"
input_folder = "/home/manya/Documents/Reduction1/"
output_folder = "/home/manya/Documents/Reduction2/"

apply_flat_correction(flat_file, input_folder, output_folder)

