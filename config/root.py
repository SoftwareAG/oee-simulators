import os,sys

# Get the path of the parent directory of the current file (i.e., the root folder)
ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
# Make a path to simulators/main (source directory)
SOURCE_DIR = os.path.join(ROOT_DIR, 'simulators', 'main')
# Add the source directory to the module search path
sys.path.insert(0, SOURCE_DIR)