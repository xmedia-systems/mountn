from gui import GUI

__author__ = 'alex'


import json
import os
import logging
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as appindicator
from collections import defaultdict
from locale import gettext as _

from utils import SubprocessException
from plugins import *


class MountNIndicator:
    APPINDICATOR_ID = "mountn"
    CONFFILE_NAME = "mountn.json"


    plugins = []
    settings = {}
    ui = None

    def __init__(self):
        self.load_conf()
        for plugin_class in (LosetupFile, TcplayDevice, Encfs):
            if plugin_class.__name__ not in self.settings:
                self.settings[plugin_class.__name__] = {}
            self.plugins.append(plugin_class(self.settings[plugin_class.__name__]))

        self.indicator = appindicator.Indicator.new(self.APPINDICATOR_ID, os.path.join(GUI.UI_DATA_PATH, "mountn_icon.svg"), appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

        self.static_menu_items = []
        self.menu = Gtk.Menu()

        separator = Gtk.SeparatorMenuItem()
        separator.show()

        quit = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_QUIT)
        quit.connect("activate", self.quit)
        quit.show()
        self.static_menu_items.append(separator)
        self.static_menu_items.append(quit)
        self.menu.append(separator)
        self.menu.append(quit)

        self.indicator.set_menu(self.menu)
        menuserver = self.indicator.get_property("dbus-menu-server")
        rootmenu = menuserver.get_property("root-node")
        rootmenu.connect("about-to-show", self.on_menu_about_to_show)

    def load_conf(self):
        for path in [os.path.expanduser("~"), os.path.dirname(__file__)]:
            confpath = os.path.join(path, self.CONFFILE_NAME)
            if os.path.exists(confpath):
                break
        else:
            return

        try:
            with open(confpath, "r") as conff:
                self.settings = json.loads(conff.read())
        except:
            self.settings = {}

    def save_conf(self):
        confpath = os.path.expanduser(os.path.join("~", self.CONFFILE_NAME))
        with open(confpath, "w") as conff:
            conff.write(json.dumps(self.settings))

    def on_menu_about_to_show(self, widget):

        activeitems = defaultdict(list)
        saveditems = defaultdict(list)
        subitems = defaultdict(list)

        for plugin in self.plugins:
            for item in plugin.items:
                if item.active:
                    activeitems[plugin].append(item)
                elif item.saved:
                    saveditems[plugin].append(item)
                else:
                    subitems[plugin].append(item)

        for item in self.menu.get_children():
            if item not in self.static_menu_items:
                self.menu.remove(item)

        add_menuitem = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_ADD)
        add_menu = Gtk.Menu()

        for plugin, items in subitems.items():
            plugin_sub = Gtk.MenuItem(plugin.name)
            plugin_menu = Gtk.Menu()
            for item in items:
                menuitem = Gtk.MenuItem(str(item))
                menuitem.connect("activate", self.plugin_item_action, plugin, item, item.actions[0])
                menuitem.show()
                plugin_menu.append(menuitem)
            plugin_sub.set_submenu(plugin_menu)
            plugin_sub.show()
            add_menu.append(plugin_sub)
        add_menuitem.set_submenu(add_menu)
        add_menuitem.show()
        self.menu.prepend(add_menuitem)
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        self.menu.prepend(separator)

        activeitems = [(plugin, item) for plugin, items in activeitems.items() for item in items]
        saveditems = [(plugin, item) for plugin, items in saveditems.items() for item in items]


        for plugin, item in activeitems:
            self.menu.prepend(self._create_item_top_menuitem(item, plugin))
        if activeitems:
            label_menuitem = Gtk.MenuItem(_("Active:"))
            label_menuitem.show()
            label_menuitem.set_sensitive(False)
            self.menu.prepend(label_menuitem)

        for plugin, item in saveditems:
            self.menu.prepend(self._create_item_top_menuitem(item, plugin))
        if saveditems:
            label_menuitem = Gtk.MenuItem(_("Favourites:"))
            label_menuitem.show()
            label_menuitem.set_sensitive(False)
            self.menu.prepend(label_menuitem)



    def _create_item_top_menuitem(self, item, plugin):
        menuitem = Gtk.MenuItem(str(item))
        menuitem.show()
        subsubmenu = Gtk.Menu()
        for action in item.actions:
            aitem = Gtk.MenuItem(action[1])
            aitem.connect("activate", self.plugin_item_action, plugin, item, action)
            aitem.show()
            subsubmenu.append(aitem)
        menuitem.set_submenu(subsubmenu)
        return menuitem

    def plugin_item_action(self, widget, plugin, item, action):
        try:
            action[0]()
        except SubprocessException as e:
            md = Gtk.MessageDialog(None,
                Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                _("Command failed:\n%(command)s\n\nOutput was:\n%(output)s\n\nReturn code was: %(code)d") % {
                                       "command": e.command, "output": e.errout, "code": e.retcode})
            md.set_keep_above(True)
            md.run()
            md.destroy()
        except Exception as e:
            logging.exception(e)

    def save_plugin_item(self, widget, plugin, item):
        item.saved = True

    def quit(self, widget, data=None):
        self.save_conf()
        Gtk.main_quit()


def main():
    global indicator
    indicator = MountNIndicator()
    Gtk.main()
    return 0


if __name__ == "__main__":
    main()
