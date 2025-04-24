import os
import numpy as np
from astropy.io import fits

def extract_exposure(filename):
    start = filename.find('_')
    end = filename.find('_', start + 1)
    if start != -1 and end != -1:
        return float(filename[start + 1:end])
    return None

def make_dark_library(dark_files, input_dir):
    dark_library = {}
    for dark_filename in dark_files:
        exposure = extract_exposure(dark_filename)
        if exposure:
            with fits.open(os.path.join(input_dir, dark_filename)) as hdu:
                dark_data = hdu[0].data
            dark_library[exposure] = dark_data
    return dark_library

def dark_subtraction(dark_library, sci_files, input_dir, output_dir):
    for sci_filename in sci_files:
        exposure = extract_exposure(sci_filename)
        if exposure and exposure in dark_library:
            sci_path = os.path.join(input_dir, sci_filename)
            with fits.open(sci_path) as hdu:
                sci_data = hdu[0].data
                sci_header = hdu[0].header

            dark_data = dark_library[exposure]
            corrected_data = sci_data - dark_data

            output_path = os.path.join(output_dir, sci_filename)
            fits.writeto(output_path, corrected_data, sci_header, overwrite=True)
            print(f"Dark-subtracted and saved: {sci_filename}")
        else:
            print(f"No matching dark frame for: {sci_filename}")
            
def get_files_from_directory(directory, type=None):
    files = []
    for filename in os.listdir(directory):
        if filename.startswith(type) and filename.endswith('.fits'):
            files.append(filename)
    return files

input_folder = "/home/manya/Documents/Reduction2/"
output_folder = "/home/manya/Documents/Reduction3/"

dark_files = get_files_from_directory(input_folder, type="dark")
algol_files = get_files_from_directory(input_folder, type="algol")
capella_files = get_files_from_directory(input_folder, type="capella")

dark_library = make_dark_library(dark_files, input_folder)
dark_subtraction(dark_library, algol_files, input_folder, output_folder)
dark_subtraction(dark_library, capella_files, input_folder, output_folder)


