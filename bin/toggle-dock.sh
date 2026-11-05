#!/bin/bash
if pgrep -f "python3 $HOME/actriz/bin/dock.py" > /dev/null; then pkill -f "python3 $HOME/actriz/bin/dock.py"
else setsid python3 $HOME/actriz/bin/dock.py > /dev/null 2>&1 & fi
