import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

try:
    import keyring
except:
    keyring = None

class GUI(object):
    UI_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "ui")

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(self.UI_DATA_PATH, "mountn.glade"))

    def get_file(self, parent=None, title="Open...", action = Gtk.FileChooserAction.OPEN):
        if action == Gtk.FileChooserAction.SAVE:
            buttons=(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_SAVE,Gtk.ResponseType.OK)
        elif action == Gtk.FileChooserAction.CREATE_FOLDER:
            buttons=(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN,Gtk.ResponseType.OK)
        else:
            buttons=(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN,Gtk.ResponseType.OK)
        dialog = Gtk.FileChooserDialog(title,
                                       parent,
                                       action,
                                       buttons)
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)
        response = dialog.run()
        filename = None
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        dialog.destroy()
        return filename

    def get_password(self, parent=None, message="", save_id=None):
        """
        Display a dialog with a text entry.
        Returns the text, or None if canceled.
        """

        if keyring and save_id:
            password = keyring.get_password("mountn:"+save_id, "")
            if password:
                return password


        dialog = self.builder.get_object("dlg_password")
        chk_save = self.builder.get_object("chk_save")
        txt_pass = self.builder.get_object("txt_password")
        if not (keyring and save_id):
            chk_save.hide()
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_keep_above(True)
        response = dialog.run()
        dialog.hide()
        if response == Gtk.ResponseType.OK:
            password = txt_pass.get_text().decode("utf8")
            if password:
                if keyring and save_id:
                    keyring.set_password("mountn:"+save_id,"", password)
                return password

        return None


gui = GUI()