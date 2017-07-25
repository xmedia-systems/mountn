import os
import subprocess
import logging

from mountn import utils
from mountn.utils import SubprocessException
from mountn.gui import gui
from gi.repository import Gtk

from locale import gettext as _

class Encfs(object):
    ENCFS_BIN = "encfs"
    FUSERMOUNT_BIN = "fusermount"

    name = "Encfs"

    class Item(object):
        def __init__(self, plugin, **kwargs):
            self.plugin = plugin
            self.active = kwargs.get("active", False)
            self.saved = kwargs.get("saved", False)
            self.encfs_path = kwargs.get("encfs_path", "")
            self.mount_point = kwargs.get("mount_point", "")
            self.label = kwargs.get("label", os.path.basename(self.encfs_path))

        def __str__(self):
            return self.label

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
            dialog = EncfsDialog(self)
            if not dialog.validate():
                if dialog.run() != Gtk.ResponseType.OK:
                    dialog.destroy()
                    return
            dialog.destroy()
            password = gui.get_password(None, _("Enter password for %s:") % self.encfs_path, save_id="encfs:%s" % self.encfs_path)
            if not password:
                return

            cmd = [Encfs.ENCFS_BIN, self.encfs_path, self.mount_point]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(password+"\r")
            if proc.returncode != 0:
                logging.error(stderr)
                raise SubprocessException("Process terminated with status %d" % proc.returncode, command=" ".join(cmd), retcode=proc.returncode, errout=stderr)
            self.active = True
            return True

        def deactivate(self):
            cmd = [Encfs.FUSERMOUNT_BIN, "-u", self.mount_point]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logging.error(stderr)
                raise SubprocessException("Process terminated with status %d" % proc.returncode, command=" ".join(cmd), retcode=proc.returncode, errout=stderr)
            self.active = False

        def save(self):
            dialog = EncfsDialog(self)
            if not dialog.validate():
                if dialog.run() != Gtk.ResponseType.OK:
                    dialog.destroy()
                    return
            dialog.destroy()
            saved = {"encfs_path": self.encfs_path, "mount_point": self.mount_point}
            conf = self.plugin.settings.setdefault("items",[])
            conf.append(saved)

        def unsave(self):
            saved = {"encfs_path": self.encfs_path, "mount_point": self.mount_point}
            conf = self.plugin.settings.setdefault("items",[])
            conf.remove(saved)


    def __init__(self, settings):
        self.settings = settings

    @property
    def items(self):
        items = {}
        mounts = [m for m in utils.mount() if m["TYPE"] == "fuse.encfs"]

        saved_items = self.settings.setdefault("items", [])
        for saved in saved_items:
            items[saved["mount_point"]] = Encfs.Item(self, saved=True, **saved)

        for mount in mounts:
            saved = items.get(mount["MOUNT_POINT"], None)
            if saved:
                saved.active = True
            else:
                items[mount["MOUNT_POINT"]] = Encfs.Item(self, saved=False, active=True, mount_point=mount["MOUNT_POINT"], encfs_path=mount["DEVICE"])

        items["_"] = Encfs.Item(self, label=_("Select directories..."))

        return items.values()

class EncfsDialog(Gtk.Dialog):

    def __init__(self, item, parent=None):
        Gtk.Dialog.__init__(self, _("Mount Encfs Directory"), parent, Gtk.DialogFlags.MODAL,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(gui.UI_DATA_PATH, "encfs.glade"))
        content = self.builder.get_object("dlg_encfs")
        self.get_content_area().add(content)
        self.encfs_item = item

        self.btn_ok = self.get_widget_for_response(Gtk.ResponseType.OK)
        self.txt_encfs = self.builder.get_object("txt_encfs")
        self.lbl_error_encfs = self.builder.get_object("lbl_error_encfs")
        self.txt_mountpoint = self.builder.get_object("txt_mountpoint")
        self.lbl_error_mountpoint = self.builder.get_object("lbl_error_mountpoint")
        if self.encfs_item.encfs_path:
            self.txt_encfs.set_text(self.encfs_item.encfs_path)
        if self.encfs_item.mount_point:
            self.txt_mountpoint.set_text(self.encfs_item.mount_point)

        self.validate()

        self.builder.connect_signals(self)
        self.show_all()


    def on_btn_browse_encfs_clicked(self, *args, **kwargs):
        encfs = gui.get_file(parent=self, title=_("Select the encrypted directory"), action=Gtk.FileChooserAction.SELECT_FOLDER)
        if encfs:
            self.txt_encfs.set_text(encfs)

    def on_btn_browse_mountpoint_clicked(self, *args, **kwargs):
        mount_point = gui.get_file(parent=self, title=_("Select an empty directory as mount point"), action=Gtk.FileChooserAction.CREATE_FOLDER)
        if mount_point:
            self.txt_mountpoint.set_text(mount_point)

    def on_txt_encfs_changed(self, *args, **kwargs):
        self.validate()

    def on_txt_mountpoint_changed(self, *args, **kwargs):
        self.validate()


    def validate(self):
        error_mountpoint = self.validate_mountpoint()
        self.lbl_error_mountpoint.set_text(error_mountpoint)
        error_encfs = self.validate_encfs()
        self.lbl_error_encfs.set_text(error_encfs)
        valid = not (error_encfs or error_mountpoint)
        self.btn_ok.set_sensitive(valid)
        return valid

    def validate_encfs(self):
        encfs_path = self.txt_encfs.get_text()
        if not encfs_path:
            return _("Path is empty")
        if not os.path.isabs(encfs_path):
            return _("Path is not absolute")
        if not os.path.isdir(encfs_path):
            return _("Path is not a directory")
        return ""

    def validate_mountpoint(self):
        mountpoint_path = self.txt_mountpoint.get_text()
        if not mountpoint_path:
            return _("Path is empty")
        if not os.path.isabs(mountpoint_path):
            return _("Path is not absolute")
        if not os.path.isdir(mountpoint_path):
            return _("Path is not a directory")
        return ""

    def run(self):
        response = super(EncfsDialog, self).run()
        self.hide()
        if response == Gtk.ResponseType.OK:
            self.encfs_item.encfs_path = self.txt_encfs.get_text()
            self.encfs_item.mount_point = self.txt_mountpoint.get_text()
        return response

