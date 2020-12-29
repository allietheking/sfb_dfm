# See README.md for description of steps to set up a run

# This script partitions and executes the DFM run

# USER INPUT:
export MDUNAME="test.mdu"                          # name of *.mdu file
export RUNPATH="../runs/test/"                     # path to *.mdu file (this is where run will be executed)
export NPROC=16                                    # number of processors (16 is a good number)
export DFMV=/opt/software/delft/dfm/r52184-opt/bin # path to DFM binaries

# ECHO USER INPUT 
echo "Echo user input"
echo "  Name of *.mdu file:"
echo "     MDUNAME="$MDUNAME
echo "  Path to *.mdu file:"
echo "     RUNPATH="$RUNPATH
echo "  Number of processors"
echo "     NPROC="$NPROC
echo "  Path to DFM binaries:"
echo "     DFMV="$DFMV
echo ""

# Add DFM to PATH environment variable and check it only points to one version
export PATH=$DFMV:$PATH
echo "Make sure PATH points to only one version of DFM:"
echo "     PATH="$PATH
echo ""

# Now navigate to the directory with the *.mdu file
echo "Changing directories to RUNPATH"
echo ""
cd $RUNPATH

# Create partitions for parallel run
echo "Partitioning into "$NPROC" subdomains, check partition.txt for ouptut"
echo ""
dflowfm --partition:ndomains=$NPROC:icgsolver=6 $MDUNAME >partition.txt

# Execute parallel run
echo "Executing DFM run, check out.txt and err.txt for output"
echo ""
mpiexec -n $NPROC dflowfm --autostartstop $MDUNAME > out.txt 2> err.txt
