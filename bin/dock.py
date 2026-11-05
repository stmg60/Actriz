#!/usr/bin/env python3
import gi, cairo, math, subprocess, sys, os, fcntl, shlex
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
try:
    lock_fd = os.open("/tmp/actriz_dock.lock", os.O_CREAT | os.O_RDWR, 0o666); fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError: sys.exit(0)

class ActrizDock(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_app_paintable(True); self.set_decorated(False); self.set_keep_above(True)
        self.set_wmclass("actriz-dock", "ActrizDock"); self.set_accept_focus(False)
        visual = self.get_screen().get_rgba_visual()
        if visual: self.set_visual(visual)
        self.screen_w = self.get_screen().get_width(); self.screen_h = self.get_screen().get_height()
        self.w, self.h = 400, 60; self.x = (self.screen_w - self.w) // 2; self.y = self.screen_h - self.h - 45 
        self.resize(self.w, self.h); self.move(self.x, self.y)
        self.connect("draw", self.on_draw); self.connect("realize", self.on_realize); self.connect("map-event", self.on_map); self.connect("button-press-event", self.on_click)
        self.win_id = None
        self.apps = [("Terminal", "utilities-terminal", "kitty"), ("Zen", "web-browser", "flatpak run app.zen_browser.zen"), ("Nemo", "system-file-manager", "nemo"), ("Ajustes", "preferences-system", "mate-control-center"), ("Editor", "accessories-text-editor", "gedit")]
        self.hover_index = -1; self.icon_size = 32
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("motion-notify-event", self.on_hover); self.connect("leave-notify-event", self.on_leave)

    def on_realize(self, widget): self.win_id = self.get_window().get_xid(); self.update_shape()
    def on_map(self, widget, event):
        if self.win_id:
            subprocess.Popen(["i3-msg", f'[id="{self.win_id}"] floating enable, border none, sticky enable'])
            subprocess.Popen(["xdotool", "windowraise", str(self.win_id)])
        return False
    def update_shape(self):
        mask = cairo.ImageSurface(cairo.FORMAT_A1, self.w, self.h); cr = cairo.Context(mask); r = self.h / 2
        cr.arc(self.w - r, r, r, -math.pi/2, 0); cr.arc(self.w - r, self.h - r, r, 0, math.pi/2)
        cr.arc(r, self.h - r, r, math.pi/2, math.pi); cr.arc(r, r, r, math.pi, 3*math.pi/2)
        cr.close_path(); cr.fill(); mask.flush()
        self.get_window().shape_combine_region(Gdk.cairo_region_create_from_surface(mask), 0, 0)
    def on_hover(self, widget, event):
        n_apps, spacing = len(self.apps), 60
        start_x = (self.w - (n_apps * spacing)) / 2 + (spacing - self.icon_size)/2
        new_hover = -1
        for i in range(n_apps):
            ix = start_x + i * spacing
            if ix <= event.x <= ix + self.icon_size and 14 <= event.y <= 14 + self.icon_size: new_hover = i; break
        if new_hover != self.hover_index: self.hover_index = new_hover; self.queue_draw()
    def on_leave(self, widget, event): self.hover_index = -1; self.queue_draw()
    def on_click(self, widget, event):
        if event.button == 1 and self.hover_index != -1:
            subprocess.Popen(shlex.split(self.apps[self.hover_index][2])); self.hide()
    def on_draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE); cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER); cr.set_antialias(cairo.ANTIALIAS_BEST)
        w, h = self.w, self.h; r = h / 2
        cr.arc(w - r, r, r, -math.pi/2, 0); cr.arc(w - r, h - r, r, 0, math.pi/2)
        cr.arc(r, h - r, r, math.pi/2, math.pi); cr.arc(r, r, r, math.pi, 3*math.pi/2)
        cr.close_path(); cr.set_source_rgba(0.1, 0.1, 0.1, 0.6); cr.fill_preserve()
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.2); cr.set_line_width(1.5); cr.stroke()
        theme = Gtk.IconTheme.get_default(); n_apps, spacing = len(self.apps), 60
        start_x = (self.w - (n_apps * spacing)) / 2 + (spacing - self.icon_size)/2
        for i, app in enumerate(self.apps):
            name, icon_name, _ = app; is_hover = (i == self.hover_index); size = 40 if is_hover else 32
            ix = start_x + i * spacing - (size - 32)/2; iy = 14 - (size - 32)/2
            try:
                pixbuf = theme.load_icon(icon_name, size, 0); Gdk.cairo_set_source_pixbuf(cr, pixbuf, ix, iy)
                cr.paint_with_alpha(1.0 if is_hover else 0.8)
            except: pass
        return False

if __name__ == '__main__':
    win = ActrizDock(); win.connect("destroy", Gtk.main_quit); win.show_all(); Gtk.main()
