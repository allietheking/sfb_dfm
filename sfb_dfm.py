#!/usr/bin/env python
"""
Script to configure and generate mdu ready for running dflow fm.

Uses sfei_v19 grid, a Southbay-enhancement of the SF Bay/Delta community
model grid, with some areas deepened (LSB bathy), trimmed (Coyote Creek)
and dredge (see dredge_grid.py in this directory)
"""
import os
import pdb
import io
import shutil
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
if 1: # wy2013 with spinup
    # suffix:
    #   a=>lowpassed the tides
    run_name="wy2013a" 
    run_start=np.datetime64('2012-08-01')
    run_stop=np.datetime64('2013-10-01')


# debugging - set all volumetric flow rates to 1m3/s.
ALL_FLOWS_UNIT=False

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

##

# Load the grid now -- it's used for clarifying some inputs, but
# is also modified to deepen areas near inflows, before being written
# out near the end of the script
grid=dfm_grid.DFMGrid(net_file)
    
## 

# WIND
sfb_dfm_utils.add_erddap_ludwig_wind(run_base_dir,
                                     run_start,run_stop,
                                     old_bc_fn)
                                         
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
sfb_dfm_utils.add_ocean(run_base_dir,
                        run_start,run_stop,ref_date,
                        static_dir=abs_static_dir,
                        grid=grid,
                        old_bc_fn=old_bc_fn,
                        all_flows_unit=ALL_FLOWS_UNIT)

##

sfb_dfm_utils.add_initial_salinity(run_base_dir,
                                   static_dir=abs_static_dir,
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

## --------------------------------------------------------------------------------
# Edits to the template mdu:
# 

mdu=dio.MDUFile('template.mdu')

mdu['geometry','LandBoundaryFile'] = os.path.join(rel_static_dir,"deltabay.ldb")

if 1:  # Copy grid file into run directory and update mdu
    mdu['geometry','NetFile'] = os.path.basename(net_file)
    dest=os.path.join(run_base_dir, net_file)
    if 0: # back when this script made no changes to the grid:
        shutil.copyfile(net_file, dest)
    else: # write out the modified grid
        dfm_grid.write_dfm(grid,dest,overwrite=True)

if 1: # fixed weir file is just referenced as static input
    mdu['geometry','FixedWeirFile'] = os.path.join(rel_static_dir,'SBlevees_tdk.pli')

if 1: # set dates
    # RefDate can only be specified to day precision
    mdu['time','RefDate'] = utils.to_datetime(ref_date).strftime('%Y%m%d')
    mdu['time','Tunit'] = 'M' # minutes.  kind of weird, but stick with what was used already
    mdu['time','TStart'] = 0
    mdu['time','TStop'] = int( (run_stop - run_start) / np.timedelta64(1,'m') )

if 1: # update location of the boundary conditions
    # this has the source/sinks which cannot be written in the new style file
    mdu['external forcing','ExtForceFile']=os.path.basename(old_bc_fn)

if 0: # Would be adding evaporation as negative rain here.
    pass

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
mdu.write(os.path.join(run_base_dir,run_name+".mdu"))

