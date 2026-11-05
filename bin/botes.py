#!/usr/bin/env python3
import gi, cairo, math, subprocess, sys, os, fcntl, datetime
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
try:
    lock_fd = os.open("/tmp/actriz_botes.lock", os.O_CREAT | os.O_RDWR, 0o666); fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError: sys.exit(0)

class Bote(Gtk.Window):
    def __init__(self, bote_id, x, y, w=210, h=24):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.set_app_paintable(True); self.set_decorated(False); self.set_keep_above(True)
        self.set_wmclass("actriz-bote", "ActrizBote"); visual = self.get_screen().get_rgba_visual()
        if visual: self.set_visual(visual)
        self.w, self.h, self.x, self.y, self.bote_id = w, h, x, y, bote_id
        self.resize(self.w, self.h); self.move(self.x, self.y)
        self.connect("draw", self.on_draw); self.connect("realize", self.on_realize); self.connect("map-event", self.on_map)
        self.win_id = None; self.texto_actual = ""; self.nivel_bat = 0; self.estado_bat = "Unknown"; self.wifi_strength = 0
        GLib.timeout_add(1000, self.keep_on_top); GLib.timeout_add(1000, self.update_data)

    def update_data(self):
        if self.bote_id == 'A': self.texto_actual = datetime.datetime.now().strftime("%I:%M").lstrip("0")
        elif self.bote_id == 'B':
            try:
                with open('/sys/class/power_supply/BAT0/capacity', 'r') as f: self.nivel_bat = int(f.read().strip())
                with open('/sys/class/power_supply/BAT0/status', 'r') as f: self.estado_bat = f.read().strip()
            except: pass
            try:
                out = subprocess.check_output(["nmcli", "-t", "-f", "IN-USE,SIGNAL", "device", "wifi"]).decode()
                for line in out.splitlines():
                    if line.startswith("*") or line.startswith("yes"): self.wifi_strength = int(line.split(":")[1])
            except: pass
        self.queue_draw(); return True

    def on_realize(self, widget):
        self.win_id = self.get_window().get_xid(); region = cairo.Region(); self.get_window().input_shape_combine_region(region, 0, 0)
    def on_map(self, widget, event):
        if self.win_id:
            subprocess.run(["i3-msg", f'[id="{self.win_id}"] floating enable, border none, sticky enable'])
            subprocess.run(["xdotool", "windowmove", str(self.win_id), str(self.x), str(self.y)])
            subprocess.run(["xdotool", "windowsize", str(self.win_id), str(self.w), str(self.h)])
            subprocess.run(["xdotool", "windowraise", str(self.win_id)])
        return False
    def keep_on_top(self):
        if self.win_id:
            subprocess.Popen(["xdotool", "windowmove", str(self.win_id), str(self.x), str(self.y)])
            subprocess.Popen(["xdotool", "windowraise", str(self.win_id)])
        return True
    def on_draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE); cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER); cr.set_antialias(cairo.ANTIALIAS_BEST)
        cr.select_font_face("Roboto", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        if self.bote_id == 'A':
            cr.set_font_size(15.2); ext = cr.text_extents(self.texto_actual)
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
            cr.move_to(self.w - 30 - ext.width + 7, (self.h + ext.height) / 2 - 1); cr.show_text(self.texto_actual)
        elif self.bote_id == 'B':
            cr.set_line_width(1.5); cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.9); cr.arc(25, self.h/2, 1.5, 0, 2*math.pi); cr.fill()
        return False

if __name__ == '__main__':
    screen = Gdk.Screen.get_default(); sw, sh = screen.get_width(), screen.get_height()
    center_x = (sw - 75) // 2; w_bote, gap = 210, 10
    bA = Bote('A', center_x - w_bote - gap + 5, 4); bB = Bote('B', center_x + 75 + gap - 11, 4)
    for b in (bA, bB): b.connect("destroy", Gtk.main_quit); b.show_all()
    Gtk.main()
