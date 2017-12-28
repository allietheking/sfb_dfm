# sfb_dfm

Configuration for San Francisco Bay hydrodynamic model:
 * Uses Delft Flexible Mesh
 * Based on combined efforts of the [SF Bay/Delta Community Model](http://www.d3d-baydelta.org/), USGS CASCaDE, and the Nutrient Management Strategy
 * Focus on accurate representation of freshwater and wastewater inputs to the Bay.

## Running the Model

1. Clone this repository and submodules:

    ```$ git clone --recursive https://github.com/rustychris/sfb_dfm.git```

2. Clone `stompy` if you do not already have it

    ```$ git clone https://github.com/rustychris/stompy.git ; export PYTHONPATH=$PWD/stompy```
    
3. Edit sfb_dfm/sfb_dfm.py:
  a. In the second block ('SETTINGS') from the top, set `run_name`, `run_start`, and `run_stop`.
  b. Set `dfm_bin_dir` to point to the folder holding `dflowfm`.  If MPI is installed elsewhere, modify `mpi_bin_dir`, too.
  c. Set `nprocs` to the number of cores to use for MPI.  Currently this script assumes that MPI is used.
  
4. Run sfb_dfm.py from the sfb_dfm directory:

    ```
    $ python sfb_dfm.py
    ```
    
5. Manually run the simulation:

     ```
     $ cd runs/<run_name>
     $ mpiexec -np <nprocs> dflowfm --autostartstop <run_name>
     ```
  
5. If all goes well, you should end up with a complete run in runs/<run_name>.

### What does the script do?

* Adds freshwater flows to the model, making sure that the pour points are deep enough (-0.5m) to remain wet at all times.
* Adds POTW flows as point sources at the bed.
* Download tide and Delta outflow data, applying these as additional boundary conditions.
* Download a coarse wind field, add as boundary condition.
* Update settings in template.mdu to customize paths, time information, output selection.
* Partition the grid and scatter the MDUs.

## Files

**derived**
  Data/files derived from other inputs, but not part of a specific run.
  Currently only used for shapefiles generated from the grid.
  
**inputs-static**
  Files which do not change across runs, are not derived, but are instead
  referenced directly from the MDU or other parts of the model setup.
  
**nudged_features.pli**
  A Delft-style polyline file defining locations of sources.  This is created
  by exporting boundary condition features from Delta Shell.
  
**write_grid_shp.py**
  Short script which writes the shapefile for grid edges, used for loading
  grid representation into GIS.
  
**runs**
  Script-generated simulation setups are in subdirectories below here.
  
**sample_run_dfm**
  Not currently used.  Reference for how to start multiprocessor runs.
  
**sfbay_freshwater**
**sfbay_potw**
  Git submodules holding forcing data for rivers and wastewater discharges.
  
**sfb_dfm.py**
  Main script for generating new runs.
  
**sfei_v19_net.nc**
  Grid.  This grid is modified slightly during the setup of each run based
  on freshwater inputs, and the modified grid is written into the run directory.
  
**template.mdu**
  Template model definition.  Settings which needn't be set dynamically can
  be set here.  Can be tweaked in sfb_dfm.py
  
**update_alviso_bathy.py, plot_sources.py**
  Temporary dev-related scripts for troubleshooting some issues.  Probably
  will be removed down the road.

 
