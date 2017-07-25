import re
import subprocess
import logging

from mountn.utils import lsblk, SubprocessException
from mountn.gui import gui

from locale import gettext as _

class LosetupFile(object):
    class Item(object):
        def __init__(self, **kwargs):
            self.active = kwargs.get("active", False)
            self.saved = kwargs.get("saved", False)
            self.device = kwargs.get("device", None)
            self.file = kwargs.get("file", None)

        def __str__(self):
            return self.device

        @property
        def actions(self):
            actions = []
            if self.active:
                actions.append((self.deactivate, _("Unmount")))
            else:
                actions.append((self.activate, _("Mount")))
            if self.saved:
                actions.append((self.unsave, _("Remove favourite")))
            else:
                actions.append((self.save, _("Add favourite")))
            return actions


        def activate(self):
            if not self.file:
                self.file = gui.get_file()
                if not self.file:
                    return False

            cmd = [LosetupFile.PKEXEC_BIN, LosetupFile.LOSETUP_BIN, self.device, self.file]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logging.error(stderr)
                raise SubprocessException("Process terminated with status %d" % proc.returncode, command=" ".join(cmd), retcode=proc.returncode, errout=stderr)
            self.active = True
            return True

        def deactivate(self):
            cmd = [LosetupFile.PKEXEC_BIN, LosetupFile.LOSETUP_BIN, "-d", self.device]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logging.error(stderr)
                raise SubprocessException("Process terminated with status %d" % proc.returncode, command=" ".join(cmd), retcode=proc.returncode, errout=stderr)
            self.active = False
            return True

        def save(self):
            saved = {"device": self.device, "file": self.file}
            conf = self.plugin.settings.setdefault("items",[])
            conf.append(saved)

        def unsave(self):
            saved = {"device": self.device, "file": self.file}
            conf = self.plugin.settings.setdefault("items",[])
            conf.remove(saved)


    PKEXEC_BIN = "pkexec"
    LOSETUP_BIN = "losetup"

    name = "Loop-Devices"

    settings = {
        "saved": [{"device": "/dev/loop0", "file": "/tmp/test"}]
    }



    def __init__(self, settings):
        self.settings = settings

    @property
    def items(self):
        items = []
        saved_items = self.settings.setdefault("items", [])
        cmd = [self.LOSETUP_BIN, "-a"]
        output = subprocess.check_output(cmd)

        for device in lsblk():
            if device["TYPE"] == "loop":
                regex = "^%s[^\(]+\(([^\)]*)\)" % device["NAME"]
                match = re.match(regex, output, re.MULTILINE)

                if match:
                    active = True
                    filename = match.group(1)
                    saved = bool(filter(lambda i: i["device"]==device["NAME"] and i["file"]==filename, saved_items))
                else:
                    active, saved = False, False
                items.append(LosetupFile.Item(device=device["NAME"], active=active, saved=saved))

        return items

