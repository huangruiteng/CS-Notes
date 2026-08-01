import glob

file_pattern = file_prefix + '-part_*'
count = len(glob.glob(file_pattern))