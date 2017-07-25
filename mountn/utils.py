# -*- coding: utf-8 -*-
__author__ = 'alex'
import subprocess
import re
import time

class SubprocessException(Exception):
    def __init__(self, *args, **kwargs):
        super(SubprocessException, self).__init__(*args)
        self.command = kwargs.get("command", "")
        self.retcode = kwargs.get("retcode", 0)
        self.stdout = kwargs.get("stdout", "")
        self.errout = kwargs.get("errout", "")

def lsblk(max_cache_age=5.0):
    now = time.time()
    if now - lsblk._cache_time < max_cache_age:
        return lsblk._cache

    output = subprocess.check_output(["lsblk", "-anpP", "--output-all"])
    regex = re.compile("(\w+)=\"([^\"]*)\"")
    devices = [
        dict(m.group(1,2) for m in regex.finditer(line))
        for line in output.splitlines()
    ]
    devmap = {d.get("KNAME", ""): d for d in devices}

    for dev in devices:
        pname = dev["PKNAME"]
        if pname and pname in devmap:
            dev["PARENT"] = devmap[pname]

    lsblk._cache_time = now
    lsblk._cache = devices
    return lsblk._cache

lsblk._cache = []
lsblk._cache_time = 0.0

def mount():
    output = subprocess.check_output(["mount", "-v"])
    regex = re.compile("(\S+) on (\S+) type (\S+)")
    for line in output.splitlines():
        m = regex.search(line)
        if m:
            yield {"DEVICE": m.group(1), "MOUNT_POINT": m.group(2), "TYPE": m.group(3)}



