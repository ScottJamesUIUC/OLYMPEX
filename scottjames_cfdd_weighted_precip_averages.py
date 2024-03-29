#do all relevant importing
# %pylab inline
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

import wrf
from wrf import (getvar, latlon_coords, ALL_TIMES)

import netCDF4
from netCDF4 import Dataset

# %config InlineBackend.figure_format='retina'

import warnings #Use this to prevent runtime and future warnings from popping up
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

from glob import glob

import cartopy.crs as ccrs
from cartopy.feature import NaturalEarthFeature
import cartopy.feature as cfeature

import xarray as xr

import geopandas
import scipy
import regionmask
from cmcrameri import cm

#################################################################################################
#read in all of the wrf out files for domain 4
files_domain4 = glob('/data/dhence/a/scottj2/WRF/WRF_d4_thomp/wrfout_d04_2015-12-*')
files_domain4.sort()

#create the list of all files to get variables from
ds4 = []
for i in files_domain4:
    ds4.append(Dataset(i))

#pull each model component of precipitation
rainc = getvar(ds4, 'RAINC', timeidx=ALL_TIMES)
rainnc = getvar(ds4, "RAINNC", timeidx=ALL_TIMES)
rainsh = getvar(ds4, "RAINSH", timeidx=ALL_TIMES)

# add all components together for total rain
tot_precip = rainc + rainnc + rainsh

#get the lat/lon coordinates from the model output
lats, lons = latlon_coords(rainc)
#################################################################################################

#create numpy array of indices for each mask region. (mask regions created in ARC GIS)
large_cfdd =  np.array([[-125.230193164361,46.350249762460],[-123.152180945193, 47.504266855703],
                       [-123.828143316776,48.062773793159],[-125.906155535046,46.920977111815]])

NPOL_cfad = np.array([[-124.444289441873,47.293052336476], [-124.176019380743,47.428737061524],
                    [-123.975710557543,47.246937619174], [-124.243980618673,47.110785424121]])

MID_cfad = np.array([[-124.872289441338,47.082144098268], [-124.604019381107,47.218369626643],
                   [-124.403710557907,47.035845851313], [-124.671980619036,46.899152592239]])

UPSTREAM_cfad = np.array([[-125.298289442434,46.869236412529], [-125.030019381305,47.006006006105],
                         [-124.829710558105,46.822753531928], [-125.097980619235,46.685515970220]])

FAR_cfad  = np.array([[-125.509289441919,46.763282233548], [-125.241019380790,46.900321882263],
                         [-125.040710557590,46.716707709077], [-125.308980618719,46.579199983710]])

# create region masks using arrays above
regions = regionmask.Regions([large_cfdd, NPOL_cfad, MID_cfad, UPSTREAM_cfad, FAR_cfad],
                                  names=['large cfdd', 'NPOL cfad', 'MID cfad', 'UPSTREAM cfad', 'FAR_cfad'],
                                  abbrevs=['Large', 'NPOL', 'MID', 'UP', 'FAR'], overlap=True)

#apply region mask to total precip arrays using lat and longitude
all_times_mask = regions.mask_3D(tot_precip.XLONG, tot_precip.XLAT)
#################################################################################################

#diff does the difference between each file which is 5-minutes, then resample to 15-min for other possible analysis
precip_5min_all_times = tot_precip.diff('Time')

precip_15min_all_times = precip_5min_all_times.resample(Time='15Min').sum()

# only grab non-zero values
drop_zeroes_precip_5min = precip_5min_all_times.where(precip_5min_all_times > 0.00)

#select values only within each mask region for plotting and stats
large_precip_5min = drop_zeroes_precip_5min.where(all_times_mask.sel(region=0))
NPOL_precip_5min = drop_zeroes_precip_5min.where(all_times_mask.sel(region=1))
MID_precip_5min = drop_zeroes_precip_5min.where(all_times_mask.sel(region=2))
UPSTREAM_precip_5min = drop_zeroes_precip_5min.where(all_times_mask.sel(region=3))
FAR_precip_5min = drop_zeroes_precip_5min.where(all_times_mask.sel(region=4))
#################################################################################################

# bins for the histogram and for plotting
dist_bins = np.arange(0,587,1)
precip_bins = np.arange(0.01,.75, 0.001)

large_box_cfdd = pd.DataFrame()

#go through each dist bin and create a histogram of precip at each time/y-lat points using the precip bins
for k in dist_bins:
    hist = np.histogram(rotated_5min_large_only_da_nozero[:,:,k],precip_bins)[0]
    hist=pd.DataFrame(hist)
    hist=hist.T
    large_box_cfdd = pd.concat([large_box_cfdd, hist])

##############################################################################
#Pre-warm frontal
large_box_PWF_cfdd = pd.DataFrame()

#go through each dist bin and create a histogram of precip at each time/y-lat points using the precip bins
for k in dist_bins:
    hist_PWF = np.histogram(large_precip_5min_no_zero_PWF[:,:,k],precip_bins)[0]
    hist_PWF=pd.DataFrame(hist_PWF)
    hist_PWF=hist_PWF.T
    large_box_PWF_cfdd = pd.concat([large_box_PWF_cfdd, hist_PWF])
###############################################################################
#warm frontal
large_box_WF_cfdd = pd.DataFrame()

#go through each dist bin and create a histogram of precip at each time/y-lat points using the precip bins
for k in dist_bins:
    hist_WF = np.histogram(large_precip_5min_no_zero_WF[:,:,k],precip_bins)[0]
    hist_WF=pd.DataFrame(hist_WF)
    hist_WF=hist_WF.T
    large_box_WF_cfdd = pd.concat([large_box_WF_cfdd, hist_WF])
###############################################################################
#postfrontal
large_box_WS_cfdd = pd.DataFrame()

#go through each dist bin and create a histogram of precip at each time/y-lat points using the precip bins
for k in dist_bins:
    hist_WS = np.histogram(large_precip_5min_no_zero_WS[:,:,k],precip_bins)[0]
    hist_WS=pd.DataFrame(hist_WS)
    hist_WS=hist_WS.T
    large_box_WS_cfdd = pd.concat([large_box_WS_cfdd, hist_WS])

#go through data and divide CFDD by by total number of counts in each row.
large_box_cfdd = large_box_cfdd.loc[:,large_box_cfdd.select_dtypes(exclude='object').columns]=large_box_cfdd.select_dtypes(exclude='object').div(large_box_cfdd.select_dtypes(exclude='object').sum(1),0)*100

#take only frequencies above 1%
large_box_cfdd = large_box_cfdd[large_box_cfdd>0.01]

###################################################################################
large_box_PWF_cfdd = large_box_PWF_cfdd.loc[:,large_box_PWF_cfdd.select_dtypes(exclude='object').columns]=large_box_PWF_cfdd.select_dtypes(exclude='object').div(large_box_PWF_cfdd.select_dtypes(exclude='object').sum(1),0)*100

#take only frequencies above 1%
large_box_PWF_cfdd = large_box_PWF_cfdd[large_box_PWF_cfdd>0.01]

###################################################################################
large_box_WF_cfdd = large_box_WF_cfdd.loc[:,large_box_WF_cfdd.select_dtypes(exclude='object').columns]=large_box_WF_cfdd.select_dtypes(exclude='object').div(large_box_WF_cfdd.select_dtypes(exclude='object').sum(1),0)*100

#take only frequencies above 1%
large_box_WF_cfdd = large_box_WF_cfdd[large_box_WF_cfdd>0.01]

###################################################################################
large_box_WS_cfdd = large_box_WS_cfdd.loc[:,large_box_WS_cfdd.select_dtypes(exclude='object').columns]=large_box_WS_cfdd.select_dtypes(exclude='object').div(large_box_WS_cfdd.select_dtypes(exclude='object').sum(1),0)*100

#take only frequencies above 1%
large_box_WS_cfdd = large_box_WS_cfdd[large_box_WS_cfdd>0.01]

#plotting routine for 12 box plot.
cmap=cm.hawaii
fig, axs = plt.subplots(3, 4, figsize=(15,9), sharex=True, sharey=True)
fig.suptitle('All Small Mask d04 CFDD', x=.43, fontsize=16, fontweight='bold')

################# First row Pre-WF ####################
im= axs[0, 0].pcolormesh(dist_bins,precip_bins, FAR_box_PWF_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[0, 0].set_title('FAR Pre-WF (0230-0900 UTC)', fontsize=10)

axs[0, 1].pcolormesh(dist_bins,precip_bins, UPSTREAM_box_PWF_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[0, 1].set_title('UPSTREAM Pre-WF (0400-0900 UTC)',fontsize=10)

axs[0, 2].pcolormesh(dist_bins,precip_bins, MID_box_PWF_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[0, 2].set_title('MID Pre-WF (0500-1000 UTC)',fontsize=10)

axs[0, 3].pcolormesh(dist_bins,precip_bins, NPOL_box_PWF_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[0, 3].set_title('NPOL Pre-WF (0600-1100 UTC)',fontsize=10)

################# Second row WF ####################
axs[1, 0].pcolormesh(dist_bins,precip_bins, FAR_box_WF_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[1, 0].set_title('FAR WF (1200-1400 UTC)',fontsize=10)

axs[1, 1].pcolormesh(dist_bins,precip_bins, UPSTREAM_box_WF_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[1, 1].set_title('UPSTREAM WF (1200-1530 UTC)',fontsize=10)

axs[1, 2].pcolormesh(dist_bins,precip_bins, MID_box_WF_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[1, 2].set_title('MID WF (1200-1400 UTC)',fontsize=10)

axs[1, 3].pcolormesh(dist_bins,precip_bins, NPOL_box_WF_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[1, 3].set_title('NPOL WF (1100-1400 UTC)',fontsize=10)

################# Third row Post-WF (WS)####################
axs[2, 3].pcolormesh(dist_bins,precip_bins, NPOL_box_WS_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[2, 3].set_title('NPOL Post-WF (1400-1800 UTC)',fontsize=10)

axs[2, 2].pcolormesh(dist_bins,precip_bins, MID_box_WS_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[2, 2].set_title('MID Post-WF (1400-1800 UTC)',fontsize=10)

axs[2, 1].pcolormesh(dist_bins,precip_bins, UPSTREAM_box_WS_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[2, 1].set_title('UPSTREAM Post-WF (1530-1700 UTC)',fontsize=10)

axs[2, 0].pcolormesh(dist_bins,precip_bins, FAR_box_WS_cfdd.T,vmin=0, vmax=1, cmap=cmap)
axs[2, 0].set_title('FAR Post-WF (1400-1700 UTC)',fontsize=10)

#set ticks so that labels are centered on point in the box
ticks = [-12,-6,0,6,12]

#grid each of the subplot boxes
for ax in axs.flat:
    ax.grid(alpha=0.6)

#set the xticks
for ax in axs.flat:
    ax.set(xlabel='Distance From Central Point', ylabel='5-min Precip (mm)',
           xticks=[0,18,36,54,72], xticklabels=ticks)

# Hide x labels and tick labels for top plots and y ticks for right plots.
for ax in axs.flat:
    ax.label_outer()
    
plt.tight_layout()
fig.colorbar(im, ax=axs, pad=0.01)
#################################################################################################

# compute weighted average of precipitation across each of the masked regions
weights = np.cos(np.deg2rad(large_precip_5min.XLAT))

large_precip_weighted = large_precip_5min.weighted(all_times_mask * weights).mean(dim=('south_north','west_east'))
large_precip_weighted.plot(col="region")
