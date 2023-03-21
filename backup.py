from time import localtime, strftime
import shutil

# Source path
src = 'userdata'

now = strftime("%Y-%m-%d_%H-%M-%S", localtime())
# Destination path
dest = f'Backup/userdata_{now}'

# Copy the content of
# source to destination
destination = shutil.copytree(src, dest)

