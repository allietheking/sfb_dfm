 Steps for setting up an open bay hydro simulation:

 1) create a folder for the run, e.g. runfolder
 2) clone sfb_dfm from https://github.com/allietheking/sfb_dfm
    using a recursive clone to include the submodules, e.g. from the 
    command line:
        cd runfolder
        git clone --recursive https://github.com/allietheking/sfb_dfm  
 3) clone stompy into the same folder:
        git clone https://github.com/rustychris/stompy
 4) edit sfb_dfm.py inside the sfb_dfm package to specify run name, start time, and end time
 5) using run_launcher_part_1.sh in the sfb_dfm package, call sfb_dfm.py to set up the 
    vast majority of the model input files. The main input file is the *.mdu file, and
    this points to everything else. To execute from command line:
        ./run_launcher_part_1.sh
    may need to change permissions to execute:
        chmod 777 run_launcher_part_1.sh
 6) use the SFEI_Wind and SFEI_Meteo packages on SFEI's Google Drive (both are in the 
    1_Nutrient_Share/2_Data_NUTRIENTS folder) to generate wind and meteorological forcing 
    files. Make sure they are in the UTC time zone). Upload these files to the run folder 
    (where the *.mdu file is located) and manually edit the FlowFMold_bnd.ext file, adding 
    the following lines pointing to the wind and met forcing files:
         QUANTITY=windx
         FILENAME=wind_x_velocity_filename.amu
         FILETYPE=4
         METHOD=1
         OPERAND=O
         
         QUANTITY=windy
         FILENAME=wind_y_velocity_filename.amv
         FILETYPE=4
         METHOD=1
         OPERAND=O
         
         QUANTITY=humidity_airtemperature_cloudiness
         FILENAME=humidity_airtemp_cloud_filename.tem
         FILETYPE=6
         METHOD=3
         OPERAND=O
 7) using run_launcher_part_2.sh, call dflowfm to launch the run
    To execute from command line:
        ./run_launcher_part_2.sh
    may need to change permissions to execute:
        chmod 777 run_launcher_part_2.sh


## What does sfb_dfm.py script do?

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

 
