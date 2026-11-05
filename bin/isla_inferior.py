#!/usr/bin/env python3
import gi, cairo, math, subprocess, sys, os, fcntl
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

try:
    lock_fd = os.open("/tmp/actriz_inf.lock", os.O_CREAT | os.O_RDWR, 0o666)
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError:
    sys.exit(0)

class IslaInferior(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_app_paintable(True); self.set_decorated(False); self.set_keep_above(True)
        self.set_wmclass("actriz-isla", "ActrizIslaBajo")
        visual = self.get_screen().get_rgba_visual()
        if visual: self.set_visual(visual)
        
        self.connect("draw", self.on_draw); self.connect("realize", self.on_realize); self.connect("map-event", self.on_map)
        
        self.base_w, self.base_h = 75.0, 18.0
        self.screen_w = self.get_screen().get_width()
        self.base_x = float((self.screen_w - int(self.base_w)) // 2)
        self.base_y = float(self.screen_h - int(self.base_h) - 6)
        self.cur_x, self.cur_y = self.base_x, self.base_y
        self.cur_w, self.cur_h = self.base_w, self.base_h
        self.vx = self.vy = self.vw = self.vh = 0.0
        self.target_x, self.target_y = self.base_x, self.base_y
        self.target_w, self.target_h = self.base_w, self.base_h
        self.smooth_timer = False
        self.resize(int(self.base_w), int(self.base_h)); self.move(int(self.base_x), int(self.base_y))
        
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect("button-press-event", self.on_press); self.connect("button-release-event", self.on_release); self.connect("motion-notify-event", self.on_motion)
        
        self.dragging = False; self.start_x = self.start_y = 0; self.final_dx = 0; self.animating = False; self.win_id = None
        GLib.timeout_add(1000, self.keep_on_top)

    def on_realize(self, widget):
        self.win_id = self.get_window().get_xid(); self.update_shape()

    def on_map(self, widget, event):
        if self.win_id: subprocess.Popen(["i3-msg", f'[id="{self.win_id}"] floating enable, border none, sticky enable'])
        self.force_window_size_and_pos(); self.update_shape()
        GLib.timeout_add(50, self.force_window_size_and_pos); return False

    def force_window_size_and_pos(self):
        if self.win_id and not self.dragging and not self.animating:
            subprocess.Popen(["xdotool", "windowmove", str(self.win_id), str(int(self.base_x)), str(int(self.base_y))])
            subprocess.Popen(["xdotool", "windowsize", str(self.win_id), str(int(self.base_w)), str(int(self.base_h))])
        return False

    def keep_on_top(self):
        if self.win_id: subprocess.Popen(["xdotool", "windowraise", str(self.win_id)])
        return True

    def update_shape(self):
        w, h = int(self.cur_w), int(self.cur_h)
        if w <= 1 or h <= 1: return
        mask = cairo.ImageSurface(cairo.FORMAT_A1, w, h)
        cr = cairo.Context(mask); r = h / 2
        cr.arc(w - r, r, r, -math.pi/2, 0); cr.arc(w - r, h - r, r, 0, math.pi/2)
        cr.arc(r, h - r, r, math.pi/2, math.pi); cr.arc(r, r, r, math.pi, 3*math.pi/2)
        cr.close_path(); cr.fill(); mask.flush()
        self.get_window().shape_combine_region(Gdk.cairo_region_create_from_surface(mask), 0, 0)

    def aplicar_resistencia(self, dx):
        signo = 1 if dx >= 0 else -1; dist = abs(dx)
        if dist <= 10: return dx
        return (10.0 + 160.0 * (1.0 - math.exp(-(dist - 10) / 150.0))) * signo

    def on_press(self, widget, event):
        if event.button == 1:
            self.dragging = True; self.start_x, self.start_y = event.x_root, event.y_root; self.final_dx = 0
            Gdk.Display.get_default().get_default_seat().grab(self.get_window(), Gdk.SeatCapabilities.ALL, False, None, None, None, None)
            self.target_w, self.target_h = self.base_w + 2.0, self.base_h + 2.0
            self.target_x, self.target_y = self.base_x - 1.0, self.base_y - 1.0
            self.animating = False
            if not self.smooth_timer: self.smooth_timer = True; GLib.timeout_add(16, self.smooth_move)
            return True
        return False

    def on_motion(self, widget, event):
        if self.dragging:
            raw_dx = max(-480.0, min(480.0, event.x_root - self.start_x))
            raw_dy = max(-100.0, min(0.0, event.y_root - self.start_y))
            abs_dx, abs_dy = abs(raw_dx), abs(raw_dy)
            if abs_dx > 0 and abs_dy > 0:
                pen = 1.0 - (0.8 * math.sin(math.radians(2 * math.degrees(math.atan2(abs_dy, abs_dx)))))
                raw_dx *= pen; raw_dy *= pen
            if abs_dx > abs_dy: raw_dx *= 0.6
            dy = 0.0
            if abs(raw_dy) > 0:
                tramos, resto = int(abs(raw_dy) // 10), abs(raw_dy) % 10
                dy = (sum(10.0 * max(0.1, 1.0 - (i * 0.15)) for i in range(tramos)) + resto * max(0.1, 1.0 - (tramos * 0.15))) * (1.0 if raw_dy >= 0 else -1.0)
            raw_dx *= max(0.1, 1.0 - (abs(dy) / 100.0))
            dx = self.aplicar_resistencia(raw_dx)
            dy *= max(0.1, 1.0 - (abs(dx) / 150.0))
            self.final_dx = dx
            extra_w = (abs(dy) - 5.0) * 0.5 if abs(dy) > 5 else 0.0
            extra_h = (abs(dy) - 5.0) * 0.05 if abs(dy) > 5 else 0.0
            self.target_w, self.target_h = self.base_w + 2.0 + extra_w, self.base_h + 2.0 + extra_h
            self.target_x, self.target_y = self.base_x - 1.0 + dx - (extra_w / 2.0), self.base_y - 1.0 + dy
            return True
        return False

    def smooth_move(self):
        if not self.dragging: self.smooth_timer = False; return False
        self.cur_x += (self.target_x - self.cur_x) * 0.3; self.cur_y += (self.target_y - self.cur_y) * 0.3
        self.cur_w += (self.target_w - self.cur_w) * 0.3; self.cur_h += (self.target_h - self.cur_h) * 0.3
        self.resize(int(self.cur_w), int(self.cur_h)); self.update_shape(); self.queue_draw()
        if self.win_id: subprocess.Popen(["xdotool", "windowmove", str(self.win_id), str(int(self.cur_x)), str(int(self.cur_y))])
        return True

    def on_release(self, widget, event):
        if event.button == 1 and self.dragging:
            self.dragging = False; Gdk.Display.get_default().get_default_seat().ungrab()
            if self.final_dx > 100: subprocess.Popen(["i3-msg", "workspace next_on_output"])
            elif self.final_dx < -100: subprocess.Popen(["i3-msg", "workspace prev_on_output"])
            self.smooth_timer = False; self.cur_x, self.cur_y = self.target_x, self.target_y
            self.cur_w, self.cur_h = self.target_w, self.target_h
            self.start_animation(); return True
        return False

    def start_animation(self):
        self.animating = True; self.vx = self.vy = self.vw = self.vh = 0.0; GLib.timeout_add(16, self.animate_back)

    def animate_back(self):
        if not self.animating: return False
        self.vx += (self.base_x - self.cur_x) * 0.15; self.vy += (self.base_y - self.cur_y) * 0.15
        self.vw += (self.base_w - self.cur_w) * 0.15; self.vh += (self.base_h - self.cur_h) * 0.15
        self.vx *= 0.7; self.vy *= 0.7; self.vw *= 0.7; self.vh *= 0.7
        self.cur_x += self.vx; self.cur_y += self.vy; self.cur_w += self.vw; self.cur_h += self.vh
        if (abs(self.vx) < 0.1 and abs(self.vy) < 0.1 and abs(self.vw) < 0.1 and abs(self.vh) < 0.1):
            self.cur_x, self.cur_y, self.cur_w, self.cur_h = self.base_x, self.base_y, self.base_w, self.base_h
            self.resize(int(self.cur_w), int(self.cur_h))
            if self.win_id: subprocess.Popen(["xdotool", "windowmove", str(self.win_id), str(int(self.cur_x)), str(int(self.cur_y))])
            self.update_shape(); self.animating = False; return False
        self.resize(int(self.cur_w), int(self.cur_h))
        if self.win_id: subprocess.Popen(["xdotool", "windowmove", str(self.win_id), str(int(self.cur_x)), str(int(self.cur_y))])
        self.update_shape(); return True

    def on_draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE); cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER); cr.set_antialias(cairo.ANTIALIAS_BEST)
        w, h = self.cur_w, self.cur_h; r = h / 2
        cr.arc(w - r, r, r, -math.pi/2, 0); cr.arc(w - r, h - r, r, 0, math.pi/2)
        cr.arc(r, h - r, r, math.pi/2, math.pi); cr.arc(r, r, r, math.pi, 3*math.pi/2)
        cr.close_path(); cr.clip()
        grad = cairo.LinearGradient(0, 0, 0, h)
        grad.add_color_stop_rgba(0.0, 1.0, 1.0, 1.0, 0.85); grad.add_color_stop_rgba(0.5, 1.0, 1.0, 1.0, 0.90)
        grad.add_color_stop_rgba(1.0, 1.0, 1.0, 1.0, 0.95)
        cr.set_source(grad); cr.paint(); return False

if __name__ == '__main__':
    win = IslaSuperior(); win.connect("destroy", Gtk.main_quit); win.show_all(); Gtk.main()
