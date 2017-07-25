#!/usr/bin/env python
import os
import sys
import locale


# Add project root directory (enable symlink and trunk execution)
PROJECT_ROOT_DIRECTORY = os.path.abspath(
    os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))

python_path = []

if (os.path.exists(os.path.join(PROJECT_ROOT_DIRECTORY, 'mountn'))
    and PROJECT_ROOT_DIRECTORY not in sys.path):
    python_path.insert(0, PROJECT_ROOT_DIRECTORY)
    sys.path.insert(0, PROJECT_ROOT_DIRECTORY)
if python_path:
    os.putenv('PYTHONPATH', "%s:%s" % (os.getenv('PYTHONPATH', ''), ':'.join(python_path))) # for subprocesses

locale.textdomain('mountn')
locale.bindtextdomain('mountn', os.path.join(PROJECT_ROOT_DIRECTORY, "locale"))

from mountn import mountn
mountn.main()
