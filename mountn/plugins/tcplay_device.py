__author__ = 'alex'
import os
import subprocess
import logging

from mountn.utils import lsblk, SubprocessException
from mountn.gui import gui

from locale import gettext as _

class TcplayDevice(object):
    class Item(object):
        def __init__(self, plugin, **kwargs):
            self.plugin = plugin
            self.active = kwargs.get("active", False)
            self.device = kwargs.get("device", None)
            self.name = kwargs.get("name", None)
            self.uuid = kwargs.get("uuid", "")

        def __str__(self):
            return os.path.basename(self.device)

        @property
        def saved(self):
            conf = self.plugin.settings.setdefault("items",[])
            return self.uuid in conf

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
            cmd = [TcplayDevice.PKEXEC_BIN, TcplayDevice.TCPLAY_BIN, "--map="+self.name, "--device="+self.device]
            password = gui.get_password(None, _("Enter password for %s:") % self.name, save_id="tcplay:%s" % self.uuid)
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(password+"\r")
    
            if proc.returncode != 0:
                logging.error(stderr)
                raise SubprocessException("Process terminated with status %d" % proc.returncode, command=" ".join(cmd), retcode=proc.returncode, errout=stderr, stdout=stdout)
            self.active = True
            return True

        def deactivate(self):
            cmd = [TcplayDevice.PKEXEC_BIN, TcplayDevice.DMSETUP_BIN, "remove", self.name]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logging.error(stderr)
                raise SubprocessException("Process terminated with status %d" % proc.returncode, command=" ".join(cmd), retcode=proc.returncode, errout=stderr, stdout=stdout)
            self.active = False
            return True

        def save(self):
            conf = self.plugin.settings.setdefault("items",[])
            if self.uuid not in conf:
                conf.append(self.uuid)

        def unsave(self):
            conf = self.plugin.settings.setdefault("items",[])
            conf.remove(self.uuid)

    PKEXEC_BIN = "pkexec"
    TCPLAY_BIN = "tcplay"
    DMSETUP_BIN = "dmsetup"

    name = "TCPlay-Devices"

    def __init__(self, settings):
        self.settings = settings

    @property
    def items(self):
        items = {}
        for device in lsblk():
            fname = os.path.basename(device["NAME"])
            uuid = self._get_uuid(device)

            if device["TYPE"] == "crypt" and fname.startswith("tc_"):
                items[uuid] = TcplayDevice.Item(self, device=device["NAME"], name=os.path.basename(fname), uuid=uuid, active=True)
            elif device["TYPE"] == "part" and device["MOUNTPOINT"] == "":
                items[uuid] = TcplayDevice.Item(self, device=device["NAME"], name="tc_%s"%fname, uuid=uuid, active=False)

        return items.values()

    def _get_uuid(self, device):
        ATTRS = ("PARTUUID", "WSN")
        uuid = ""

        for attr in ATTRS:
            uuid = device.get(attr)
            if uuid:
                return uuid

        if "PARENT" in device:    
            return self._get_uuid(device["PARENT"])
        else:
            return None




