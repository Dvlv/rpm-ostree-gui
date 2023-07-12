import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, GLib

from rpm_ostree_bridge import rpm_ostree_install_rpm_fusion, rpm_ostree_status


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_default_size(900, 400)
        GLib.set_application_name("Rpm Ostree GUI")

        self.init_header()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.main_box.set_spacing(10)
        self.main_box.set_margin_top(10)
        self.main_box.set_margin_bottom(10)
        self.main_box.set_margin_start(10)
        self.main_box.set_margin_end(10)

        self.set_child(self.main_box)
        # self.main_box.append(self.left_box)
        # self.main_box.append(self.right_box)

        self.load_deployment_select()

    def load_deployment_select(self) -> None:
        status = rpm_ostree_status()

        tabs = Gtk.Notebook()
        tabs.set_tab_pos(Gtk.PositionType.LEFT)
        tabs.set_hexpand(True)
        tabs.set_vexpand(True)

        for dep in status.deployments:
            tab = self.make_deployment_page(dep)
            tab.set_hexpand(True)
            tab.set_vexpand(True)

            g = Gtk.Grid()
            g.set_column_spacing(8)
            l = Gtk.Label()
            l.set_text(dep.version_nice)

            if dep.is_current:
                i = Gtk.Image.new_from_icon_name("object-select-symbolic")
                g.attach(i, 1, 0, 1, 1)

            if dep.is_pinned:
                p = Gtk.Image.new_from_icon_name("view-pin-symbolic")
                g.attach(p, 2, 0, 1, 1)

            g.attach(l, 0, 0, 1, 1)
            tabs.append_page(tab, g)

        self.main_box.append(tabs)

    def make_deployment_page(self, dep) -> Gtk.Box:
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_spacing(20)

        # Checksum
        csLbl = Gtk.Label()
        csLbl.set_markup(f"<b>Commit {dep.base_commit}</b>")

        # grid of packages
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_start(10)
        grid.set_margin_end(10)

        gridIdx = 0

        # Layered
        lbl = Gtk.Label()
        lbl.set_markup("<b>Layered Packages</b>")
        lbl.set_font_options()
        lbl.set_xalign(0)
        grid.attach(lbl, gridIdx, 0, 1, 1)

        lpl = Gtk.Label()
        lpl.set_text("\n".join(dep.layered_packages) or "-")
        grid.attach(lpl, gridIdx, 1, 1, 1)
        gridIdx += 1

        # Local
        lbl = Gtk.Label()
        lbl.set_markup("<b>Local Packages</b>")
        lbl.set_font_options()
        lbl.set_xalign(0)
        grid.attach(lbl, gridIdx, 0, 1, 1)

        lpl = Gtk.Label()
        lpl.set_text("\n".join(dep.local_packages) or "-")
        grid.attach(lpl, gridIdx, 1, 1, 1)
        gridIdx += 1

        # Removed
        lbl = Gtk.Label()
        lbl.set_markup("<b>Removed Packages</b>")
        lbl.set_font_options()
        lbl.set_xalign(0)
        grid.attach(lbl, gridIdx, 0, 1, 1)

        lpl = Gtk.Label()
        lpl.set_text("\n".join(dep.removals) or "-")
        grid.attach(lpl, gridIdx, 1, 1, 1)
        gridIdx += 1

        # buttons at bottom
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.set_hexpand(True)
        hbox.set_spacing(20)
        hbox.set_margin_end(20)
        hbox.set_margin_bottom(20)

        pin_unpin_btn = Gtk.Button()
        pin_unpin_btn.set_icon_name("view-pin-symbolic")
        if dep.is_pinned:
            pin_unpin_btn.set_tooltip_text("Unpin")
        else:
            pin_unpin_btn.set_tooltip_text("Pin")

        deploy_btn = Gtk.Button()
        deploy_btn.set_icon_name("document-send-symbolic")
        deploy_btn.set_tooltip_text("Deploy")

        spacer = Gtk.Box()
        spacer.set_spacing(50)
        spacer.set_hexpand(True)

        hbox.append(spacer)
        hbox.append(pin_unpin_btn)
        hbox.append(deploy_btn)

        vbox.append(csLbl)
        vbox.append(grid)
        vbox.append(hbox)

        return vbox

    def init_header(self):
        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)
        self.set_title("Rpm Ostree GUI")

        # Menu
        self.init_menu()

        # Update
        # TODO better icon
        self.update_button = Gtk.Button.new_from_icon_name(
            "software-update-available-symbolic"
        )
        self.update_button.set_tooltip_text("Update")
        self.update_button.connect("clicked", self.on_update_button_clicked)
        self.header.pack_start(self.update_button)

        # Rollback
        self.rollback_button = Gtk.Button.new_from_icon_name(
            "media-seek-backward-symbolic"
        )
        self.rollback_button.set_tooltip_text("Rollback")
        self.rollback_button.connect("clicked", self.on_rollback_button_clicked)
        self.header.pack_start(self.rollback_button)

    def init_menu(self):
        menu = Gio.Menu.new()
        self.popover = Gtk.PopoverMenu()
        self.popover.set_menu_model(menu)

        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")
        self.header.pack_end(self.hamburger)

        # Set Automatic Update Preferences

        # Rebase
        rebase_action = Gio.SimpleAction.new("rebase", None)
        rebase_action.connect("activate", self.show_rebase_window)
        self.add_action(rebase_action)
        menu.append("Rebase", "win.rebase")

        # Add Rpm Fusion
        rf_action = Gio.SimpleAction.new("rpmfusion", None)
        rf_action.connect("activate", self.add_rpm_fusion)
        self.add_action(rf_action)
        menu.append("Add RPM Fusion Repo", "win.rpmfusion")

        # About
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.show_about)
        self.add_action(about_action)
        menu.append("About", "win.about")

    def show_rebase_window(self, action, param):
        self.rebase_dialogue = Gtk.MessageDialog()
        self.rebase_dialogue.set_transient_for(self)
        self.rebase_dialogue.set_modal(True)
        self.rebase_dialogue.add_buttons("Cancel", Gtk.ResponseType.CANCEL)
        self.rebase_dialogue.add_buttons("KK", Gtk.ResponseType.OK)
        self.rebase_dialogue.connect("response", self.on_rebase_response)

        l = Gtk.Label()
        l.set_text("balls")
        ca = self.rebase_dialogue.get_content_area()
        ca.append(l)

        self.rebase_dialogue.show()

    def on_rebase_response(self, _, res):
        if res == Gtk.ResponseType.CANCEL:
            print("cancel")
        else:
            print("ok")

        self.rebase_dialogue.destroy()

    def add_rpm_fusion(self, action, param):
        rpm_ostree_install_rpm_fusion()

    def show_about(self, action, param):
        self.about = Gtk.AboutDialog()
        self.about.set_transient_for(self)
        self.about.set_modal(True)

        self.about.set_authors(["Dvlv"])
        self.about.set_copyright("Copyright 2023 Dvlv")
        self.about.set_license_type(Gtk.License.MIT_X11)
        self.about.set_website("http://example.com")
        self.about.set_website_label("My Website")
        self.about.set_version("1.0")
        self.about.set_logo_icon_name("co.uk.dvlv.rpm-ostree-gui")

        self.about.show()

    def on_update_button_clicked(self, e):
        print("update")

    def on_rollback_button_clicked(self, e):
        print("rollback")
