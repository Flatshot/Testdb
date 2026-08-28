#!/bin/sh
# Launch the practice GUI on macOS or Linux.
#
# The .command extension makes this double-clickable from Finder; on Linux it
# runs the same from a file manager or a shell. The Windows equivalent is
# "SQL Practice.bat".
#
# cd first so the GUI's relative paths and the database resolve the same way
# they do when you run "python3 gui.py" by hand.
cd "$(dirname "$0")" || exit 1

for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        exec "$py" gui.py
    fi
done

echo "No python3 on PATH. Install Python 3 from https://www.python.org/downloads/"
echo "(the python.org build bundles Tk 8.6; the macOS system Python may not)."
exit 1
