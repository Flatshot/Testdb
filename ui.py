"""What the SQL pane and the Python pane share: fonts, colours, and the
handful of widget helpers both need.

Kept out of gui.py so that pygui.py can import it without importing the
window that imports pygui.py.
"""

import tkinter as tk
from tkinter import font as tkfont

# Tk resolves point sizes against the display DPI, and macOS reports 72 where
# Windows reports 96 -- the same number draws about a quarter smaller here.
# Every explicit size in the GUI derives from this one. It is a FLOOR, not an
# assignment: Tk's own named fonts are 13 on macOS and 9 on Windows, so raising
# a platform's larger default to match this would shrink the UI, not grow it.
BASE_FONT_SIZE = 14

# Font families in order of preference, Windows first then macOS then Linux.
# Tk does not error on a missing family -- it silently substitutes, which for
# the editor can mean a PROPORTIONAL face, and code is unreadable in one. So
# the family is resolved against what is actually installed, and the last
# resort is Tk's own named fonts, which every platform guarantees.
MONO_FAMILIES = ("Consolas", "Menlo", "SF Mono", "DejaVu Sans Mono",
                 "Liberation Mono", "Courier New")
UI_FAMILIES = ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Cantarell",
               "DejaVu Sans")

# Dark palette. Tk has no notion of a colour scheme, so every widget that is
# not a ttk widget has to be told individually -- and the ttk widgets only obey
# under a fully styleable theme (see App._apply_theme in gui.py).
BG_APP = "#1e1e1e"      # window and panel backgrounds
BG_SURFACE = "#252526"  # raised surfaces: notebook pages, buttons, headings
BG_FIELD = "#1b1b1b"    # text entry areas
BG_QUESTION = "#26292b"  # the question panel, slightly lifted off the app bg
BG_SELECT = "#0a4a7a"    # selected row / selected text
BG_STRIPE = "#232323"    # alternating result rows
FG_TEXT = "#d6d6d6"
FG_MUTED = "#9d9d9d"
FG_HEADING = "#e8e8e8"
BORDER = "#3a3a3a"
CURSOR = "#d6d6d6"

BG_OK = "#1a7f37"
BG_BAD = "#b3261e"
BG_INFO = "#333333"

# The question panel grows to fit its text, up to this many lines. Past that
# it would push the editor off the window.
QUESTION_MAX_LINES = 16

# The status bar wraps rather than scrolls, so an unbounded message grows
# upward until it covers the editor. Six lines is enough for the longest
# message any caller sends and small enough to stay out of the way.
STATUS_MAX_LINES = 6


def pick_family(candidates, named_fallback):
    """First installed family from candidates, else Tk's own named font.

    Must be called with a Tk root already created -- font.families() needs an
    interpreter to ask.
    """
    installed = {f.lower() for f in tkfont.families()}
    for name in candidates:
        if name.lower() in installed:
            return name
    return tkfont.nametofont(named_fallback).actual("family")


def fit_question(widget):
    """Grow a question panel to fit its text.

    A fixed height silently truncated longer prompts, and the line that gets
    cut is the last one -- which is the "Return: ..." line naming the columns
    the answer needs.
    """
    widget.update_idletasks()
    try:
        wanted = widget.count("1.0", "end", "displaylines")[0]
    except (tk.TclError, TypeError):
        wanted = int(widget.index("end-1c").split(".")[0])
    wanted = max(3, min(wanted, QUESTION_MAX_LINES))
    if wanted != int(widget.cget("height")):
        widget.configure(height=wanted)


def set_text(widget, text):
    """Replace the contents of a read-only Text widget."""
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", text)
    widget.configure(state="disabled")


def make_question(parent, ui_family):
    """The read-only panel the prompt is shown in, styled like the SQL one."""
    q = tk.Text(parent, height=5, wrap="word", relief="flat",
                font=(ui_family, BASE_FONT_SIZE), background=BG_QUESTION,
                foreground=FG_TEXT, insertbackground=CURSOR,
                selectbackground=BG_SELECT, selectforeground="#ffffff",
                highlightthickness=0, padx=8, pady=6)
    q.configure(state="disabled")
    q.bind("<Configure>", lambda _e: fit_question(q))
    return q


def make_editor(parent, mono, wrap="none"):
    """A code editor: monospaced, undoable, dark."""
    return tk.Text(parent, height=14, wrap=wrap, font=mono, undo=True,
                   tabs=("1c",), background=BG_FIELD, foreground=FG_TEXT,
                   insertbackground=CURSOR, selectbackground=BG_SELECT,
                   selectforeground="#ffffff", relief="flat",
                   highlightthickness=1, highlightbackground=BORDER,
                   highlightcolor=BG_SELECT)


def clip_status(text, width):
    """Trim a status message to a few lines' worth of characters.

    The status label wraps and grows DOWNWARD, and pack gives it what it
    asks for -- so a long message does not scroll, it pushes the editor and
    the results off the top of the window. Everything that reaches the bar
    is clipped here rather than in each caller, because the long ones
    arrive from several places: SQLite error text, grading feedback holding
    a sample row, a Python traceback, and result values that can themselves
    be enormous.
    """
    per_line = max(width // 7, 40)   # ~7px a character in the default font
    lines = text.split("\n")
    if len(lines) > STATUS_MAX_LINES:
        hidden = len(lines) - STATUS_MAX_LINES + 1
        lines = lines[:STATUS_MAX_LINES - 1] + [f"... ({hidden} more lines)"]
    out = "\n".join(lines)
    budget = per_line * STATUS_MAX_LINES
    if len(out) > budget:
        out = out[:budget - 3] + "..."
    return out
