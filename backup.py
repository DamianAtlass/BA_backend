from pybackup.backup import Backup
import os

if not os.path.exists("userdata"):
    os.makedirs("userdata")

bkp = Backup(verbose=True)
bkp.run()
