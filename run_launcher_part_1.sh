# See README.md for description of steps to set up a run

# This script adds stompy to the pythonpath environment variable and then runs sfb_dfm.py,
# which creates most of the input files

echo "Adding stompy to PYTHONPATH"
echo "(make sure stompy is in same directory as sfb_dfm)"
export PYTHONPATH=../stompy
echo "PYTHONPATH="$PYTHONPATH
echo "Running sfb_dfm.py"
python3 sfb_dfm.py
echo "If desired, add wind and meteo forcing before partitioning and executing"
echo "the run in run_launcher_part_2.sh"
