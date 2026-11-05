#!/bin/bash
WIN_ID=$(xdotool getactivewindow 2>/dev/null); if [ -z "$WIN_ID" ]; then exit 0; fi
CLASS=$(xprop -id $WIN_ID WM_CLASS 2>/dev/null | awk -F'"' '{print $4}')
if [[ "$CLASS" == "ActrizIsla" || "$CLASS" == "ActrizIslaBajo" || "$CLASS" == "ActrizDock" || "$CLASS" == "ActrizBote" ]]; then exit 0; fi
PID=$(xdotool getwindowpid $WIN_ID 2>/dev/null); if [ -n "$PID" ]; then kill -9 "$PID" 2>/dev/null; else i3-msg kill; fi
