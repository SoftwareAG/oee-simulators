import os,sys

print(f"Source path before insert: ")
print(f" ")
for path in sys.path:
    print(path)

# Get the path of the parent directory of the current file (i.e., the root folder oee-simulators)
ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '../..'))
# Make a path to simulators/main
SIMULATOR_DIR = os.path.join(ROOT_DIR, 'simulators', 'main')
# Make a path to simulators/test
TEST_DIR = os.path.join(ROOT_DIR, 'test')

for directory in [ROOT_DIR, SIMULATOR_DIR, TEST_DIR]: # check if test, main and root (oee-simulators) directory path are all in root path config
    if directory not in sys.path:
        sys.path.insert(0, directory)   # Add the missing directory to the root path config for module search

print(f"Source path after insert: ")
print(f" ")
for path in sys.path:
    print(path)