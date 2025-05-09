import os
from datetime import datetime
import pandas as pd
import numpy as np
from astropy.io import fits
from matplotlib.backends.backend_pdf import PdfPages
from photutils.aperture import CircularAperture, CircularAnnulus, aperture_photometry
import matplotlib.pyplot as plt


input_folder = '/home/manya/Documents/Reduction3/'
fits_files = [f for f in os.listdir(input_folder) if f.endswith(".fits") and f.startswith("algol")]
fits_files.sort(key=lambda x: datetime.strptime(x.split("_")[2].replace(".fits", ""), "%Y-%m-%dT%H:%M:%S.%f"))

positions = pd.read_csv('/home/manya/Documents/tracked_positions.csv')
algol_pos = positions[['algol_x', 'algol_y']].apply(tuple, axis=1).tolist()
ref_pos = positions[['ref3_x', 'ref3_y']].apply(tuple, axis=1).tolist()
timestamps = positions['timestamp']

adu = 48

algol_flux = {}  
ref_flux = {} 
algol_rel_flux = {}

for i, file in enumerate(fits_files):
    file_path = os.path.join(input_folder, file)
    with fits.open(file_path) as hdul:
        image_data = hdul[0].data
        header = hdul[0].header
        exposure_time = header["EXPOSURE"]

    timestamp = timestamps[i]

    # Defining circular apertures and annulus apertures for background
    algol_aperture = CircularAperture(algol_pos[i], r=5)
    algol_annulus = CircularAnnulus(algol_pos[i], r_in=10, r_out=15)
    ref_aperture = CircularAperture(ref_pos[i], r=5)
    ref_annulus = CircularAnnulus(ref_pos[i], r_in=10, r_out=15)

    # Aperture photometry
    phot_algol = aperture_photometry(image_data, algol_aperture)
    annulus_algol = aperture_photometry(image_data, algol_annulus)
    phot_ref = aperture_photometry(image_data, ref_aperture)
    annulus_ref = aperture_photometry(image_data, ref_annulus)

    # Background and net flux
    bkg_mean_algol = annulus_algol["aperture_sum"][0] / algol_annulus.area
    bkg_total_algol = bkg_mean_algol * algol_aperture.area
    bkg_mean_ref = annulus_ref["aperture_sum"][0] / ref_annulus.area
    bkg_total_ref = bkg_mean_ref * ref_aperture.area

    # Net flux and variance 
    flux_algol = (phot_algol["aperture_sum"][0] - bkg_total_algol) * adu / exposure_time
    var_algol = (phot_algol["aperture_sum"][0] + bkg_total_algol) * adu / (exposure_time**2)
    flux_ref = (phot_ref["aperture_sum"][0] - bkg_total_ref) * adu / exposure_time
    var_ref = (phot_ref["aperture_sum"][0] + bkg_total_ref) * adu / (exposure_time**2)

    algol_flux[timestamp] = (flux_algol, var_algol)
    ref_flux[timestamp] = (flux_ref, var_ref)

# Relative flux and error
for timestamp in algol_flux.keys():
    flux_algol, var_algol = algol_flux[timestamp]
    if timestamp in ref_flux:
        flux_ref, var_ref = ref_flux[timestamp]
        rel_flux = flux_algol / flux_ref
        rel_var = rel_flux**2 * (var_algol / flux_algol**2 + var_ref / flux_ref**2)
        algol_rel_flux[timestamp] = (rel_flux, np.sqrt(rel_var))

with PdfPages('photometry.pdf') as pdf:
    time_labels = [ts.split("T")[1][:-7] for ts in timestamps]  

    rel_flux = np.array([algol_rel_flux[t][0] for t in timestamps])
    rel_error = np.array([algol_rel_flux[t][1] for t in timestamps])
    
    plt.figure(figsize=(8, 6))
    plt.errorbar(time_labels, rel_flux, yerr=rel_error, color="k",
                 linestyle="-", ecolor="red", fmt='o', capsize=3)
    plt.xlabel("Time (HH:MM:SS)")
    plt.ylabel(f"Relative Flux ")
    plt.title("Algol Light Curve")
    plt.grid(True)

    step = max(1, len(time_labels) // 10)
    plt.xticks(time_labels[::step], rotation=45)
    plt.tight_layout()
    pdf.savefig()
    plt.close()

print(f"Saved light curves to photometery.pdf. ")

