#!/usr/bin/env python
"""
Script to configure and generate mdu ready for running dflow fm.

Uses sfei_v19 grid, a Southbay-enhancement of the SF Bay/Delta community
model grid, with some areas deepened (LSB bathy), trimmed (Coyote Creek)
and dredge (see dredge_grid.py in this directory)
"""
import os
import glob
import pdb
import io
import shutil
import subprocess
import numpy as np
import logging
import xarray as xr
import six

from stompy import utils
import stompy.model.delft.io as dio
from stompy.model.delft import dfm_grid
from stompy.spatial import wkb2shp
from stompy.io.local import usgs_nwis,noaa_coops

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)

log=logging.getLogger('sfb_dfm')

import sfb_dfm_utils 

DAY=np.timedelta64(86400,'s') # useful for adjusting times

## --------------------------------------------------

# Parameters to control more specific aspects of the run
if 0: # nice short setup for testing:
    run_name="test_20120801_p16" 
    run_start=np.datetime64('2012-08-01')
    run_stop=np.datetime64('2012-08-05')
if 0: # wy2013 with spinup
    # suffix:
    #   a=>lowpassed the tides
    run_name="wy2013a" 
    run_start=np.datetime64('2012-08-01')
    run_stop=np.datetime64('2013-10-01')
if 0: # hopefully fixing Delta inflows
    # suffix:
    run_name="wy2013b" 
    run_start=np.datetime64('2012-08-01')
    run_stop=np.datetime64('2013-10-01')
if 0: # try attenuating/lagging ocean boundary condition
    # initial run had bug in salt i.c., ocean b.c., and appeared
    # to have too much evaporation in the south.  re-doing that
    # run with fixes in place, and 50% of the evaporation.
    # This run is the basis for the Interim Model Validation Report
    run_name="wy2013c" 
    run_start=np.datetime64('2012-08-01')
    run_stop=np.datetime64('2013-10-01')

if 1: # tweaks, debug salt IC
    run_name="wy2013d" 
    run_start=np.datetime64('2012-08-01')
    run_stop=np.datetime64('2012-08-05')

nprocs=16
ALL_FLOWS_UNIT=False # for debug, set all volumetric flow rates to 1m3/s if True

dfm_bin_dir="/opt/software/delft/dfm/r52184-opt/bin"

## --------------------------------------------------

# Derived parameters used in multiple places

# base_dir=os.path.dirname(__file__) # for command line invocation
base_dir="." # during development

run_base_dir=os.path.join(base_dir,'runs',run_name)

# real location of static directory
abs_static_dir=os.path.join(base_dir,'inputs-static')
# and how to refer to it relative to the run directory
rel_static_dir=os.path.relpath(abs_static_dir,
                               run_base_dir)


# reference date - can only be specified to day precision, so 
# truncate to day precision (rounds down)
ref_date=run_start.astype('datetime64[D]')

net_file = os.path.join(base_dir,'sfei_v19_net.nc')

# No longer using any new-style boundary conditions
old_bc_fn = os.path.join(run_base_dir,'FlowFMold_bnd.ext')

obs_shp_fn = os.path.join(abs_static_dir, 'observation-points.shp')

dredge_depth=-0.5 # m NAVD88, depth to enforce at inflows and discharges

##

# Make sure run directory exists:
os.path.exists(run_base_dir) or os.makedirs(run_base_dir)

# clear any stale bc files:
for fn in [old_bc_fn]:
    os.path.exists(fn) and os.unlink(fn)

## --------------------------------------------------------------------------------
# Edits to the template mdu:
# 

mdu=dio.MDUFile('template.mdu')

if 1: # set dates
    # RefDate can only be specified to day precision
    mdu['time','RefDate'] = utils.to_datetime(ref_date).strftime('%Y%m%d')
    mdu['time','Tunit'] = 'M' # minutes.  kind of weird, but stick with what was used already
    mdu['time','TStart'] = 0
    mdu['time','TStop'] = int( (run_stop - run_start) / np.timedelta64(1,'m') )

mdu['geometry','LandBoundaryFile'] = os.path.join(rel_static_dir,"deltabay.ldb")

mdu['geometry','Kmx']=10 # 10 layers

# update location of the boundary conditions
# this has the source/sinks which cannot be written in the new style file
mdu['external forcing','ExtForceFile']=os.path.basename(old_bc_fn)

# Load the grid now -- it's used for clarifying some inputs, but
# is also modified to deepen areas near inflows, before being written
# out near the end of the script
grid=dfm_grid.DFMGrid(net_file)
    
##

# features which have manually set locations for this grid
adjusted_pli_fn = os.path.join(base_dir,'nudged_features.pli')

sfb_dfm_utils.add_sfbay_freshwater(run_base_dir,
                                   run_start,run_stop,ref_date,
                                   adjusted_pli_fn,
                                   freshwater_dir=os.path.join(base_dir, 'sfbay_freshwater'),
                                   grid=grid,
                                   dredge_depth=dredge_depth,
                                   old_bc_fn=old_bc_fn,
                                   all_flows_unit=ALL_FLOWS_UNIT)
                     
##

# POTW inputs:
# The new-style boundary inputs file (FlowFM_bnd_new.ext) cannot represent
# sources and sinks, so these come in via the old-style file.
potw_dir=os.path.join(base_dir,'sfbay_potw')

sfb_dfm_utils.add_sfbay_potw(run_base_dir,
                             run_start,run_stop,ref_date,
                             potw_dir,
                             adjusted_pli_fn,
                             grid,dredge_depth,
                             old_bc_fn,
                             all_flows_unit=ALL_FLOWS_UNIT)

##

# Delta boundary conditions
sfb_dfm_utils.add_delta_inflow(run_base_dir,
                               run_start,run_stop,ref_date,
                               static_dir=abs_static_dir,
                               grid=grid,dredge_depth=dredge_depth,
                               old_bc_fn=old_bc_fn,
                               all_flows_unit=ALL_FLOWS_UNIT)
##


# This factor seems to be about right for Point Reyes tides
# to show up at SF with the right amplitude.  Without
# attenuation, in runs/w2013b tides at SF are 1.10x observed.
# The lag is a bit less clear, with SF tides at -2.5 minutes (leading),
# but SF currents at about -15 minutes (leading).  All of these
# are likely wrapped up in some friction calibration, for another
# day.
sfb_dfm_utils.add_ocean(run_base_dir,
                        run_start,run_stop,ref_date,
                        static_dir=abs_static_dir,
                        grid=grid,
                        factor=0.901,lag_seconds=120,
                        old_bc_fn=old_bc_fn,
                        all_flows_unit=ALL_FLOWS_UNIT)

## 
if 1:            
    lines=["QUANTITY=frictioncoefficient",
           "FILENAME=%s/friction12e.xyz"%rel_static_dir,
           "FILETYPE=7",
           "METHOD=5",
           "OPERAND=O",
           ""]
    with open(old_bc_fn,'at') as fp:
        fp.write("\n".join(lines))

if 1:  # Copy grid file into run directory and update mdu
    mdu['geometry','NetFile'] = os.path.basename(net_file)
    dest=os.path.join(run_base_dir, mdu['geometry','NetFile'])
    # write out the modified grid
    dfm_grid.write_dfm(grid,dest,overwrite=True)


sfb_dfm_utils.add_initial_salinity_dyn(run_base_dir,
                                       abs_static_dir,
                                       mdu,
                                       run_start)


# WIND
ludwig_ok=sfb_dfm_utils.add_erddap_ludwig_wind(run_base_dir,
                                               run_start,run_stop,
                                               old_bc_fn)
assert ludwig_ok # or see lsb_dfm.py for constant field.

##

if 1: # fixed weir file is just referenced as static input
    mdu['geometry','FixedWeirFile'] = os.path.join(rel_static_dir,'SBlevees_tdk.pli')

if 1: 
    # evaporation was a bit out of control in south bay - try scaling back just
    # the evaporation some.  This is a punt!
    sfb_dfm_utils.add_cimis_evap_precip(run_base_dir,mdu,scale_evap=0.5)

if 1: # output locations
    mdu['output','CrsFile'] = os.path.join(rel_static_dir,"SB-observationcrosssection.pli")

##
if 1:
    # Observation points taken from shapefile for easier editing/comparisons in GIS
    obs_pnts=wkb2shp.shp2geom(obs_shp_fn)
    obs_fn='observation_pnts.xyn'
    
    with open(os.path.join(run_base_dir,obs_fn),'wt') as fp:
        for idx,row in enumerate(obs_pnts):
            xy=np.array(row['geom'])
            fp.write("%12g %12g '%s'\n"%(xy[0], xy[1], row['name']))
    mdu['output','ObsFile'] = obs_fn

    if run_name.startswith('short'):
        mdu['output','MapInterval'] = 3600
    
##
mdu_fn=os.path.join(run_base_dir,run_name+".mdu")
mdu.write(mdu_fn)

##

# As of r52184, explicitly built with metis support, partitioning can be done automatically
# from here.

cmd="%s/mpiexec -n %d %s/dflowfm --partition:ndomains=%d %s"%(dfm_bin_dir,nprocs,dfm_bin_dir,nprocs,
                                                              mdu['geometry','NetFile'])
pwd=os.getcwd()
try:
    os.chdir(run_base_dir)
    res=subprocess.call(cmd,shell=True)
finally:
    os.chdir(pwd)


# similar, but for the mdu:
cmd="%s/generate_parallel_mdu.sh %s %d 6"%(dfm_bin_dir,os.path.basename(mdu_fn),nprocs)
try:
    os.chdir(run_base_dir)
    res=subprocess.call(cmd,shell=True)
finally:
    os.chdir(pwd)
