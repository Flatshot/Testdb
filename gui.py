"""Desktop GUI for practicing SQL against testdb.

    python gui.py

Left pane picks an exercise or browses the schema. Write SQL on the right,
F5 to run it, F6 to see its query plan, Ctrl+Enter to have your result graded
against the expected one.

The database is opened READ-ONLY, so nothing you type in here can damage the
practice data no matter how wrong it goes.

Progress (which exercises you've solved, and your SQL for each) is kept in
progress.json next to this file.
"""

import json
import re
import sqlite3
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

import db
import exercises as ex

PROGRESS_PATH = db.HERE / "progress.json"
FREE = 0  # pseudo-exercise id for the scratch pad
QUESTION_MAX_LINES = 16

# How many result rows to put in the table widget. Separate from db.MAX_ROWS,
# which bounds what is FETCHED: grading and the row count use the full result,
# this only bounds what is drawn. Tk inserts rows one at a time, so a 67,000-row
# table freezes the window for several seconds -- and nobody reads past the
# first screen anyway.
DISPLAY_ROWS = 2_000

# Tk resolves point sizes against the display DPI, and macOS reports 72 where
# Windows reports 96 -- the same number draws about a quarter smaller here.
# Every explicit size below derives from this one. It is a FLOOR, not an
# assignment: Tk's own named fonts are 13 on macOS and 9 on Windows, so raising
# a platform's larger default to match this would shrink the UI, not grow it.
BASE_FONT_SIZE = 14

# Font families in order of preference, Windows first then macOS then Linux.
# Tk does not error on a missing family -- it silently substitutes, which for
# the editor can mean a PROPORTIONAL face, and SQL is unreadable in one. So the
# family is resolved against what is actually installed, and the last resort is
# Tk's own named fonts, which every platform guarantees.
MONO_FAMILIES = ("Consolas", "Menlo", "SF Mono", "DejaVu Sans Mono",
                 "Liberation Mono", "Courier New")
UI_FAMILIES = ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Cantarell",
               "DejaVu Sans")


def _pick_family(candidates, named_fallback):
    """First installed family from candidates, else Tk's own named font.

    Must be called with a Tk root already created -- font.families() needs an
    interpreter to ask.
    """
    installed = {f.lower() for f in tkfont.families()}
    for name in candidates:
        if name.lower() in installed:
            return name
    return tkfont.nametofont(named_fallback).actual("family")

# Dark palette. Tk has no notion of a colour scheme, so every widget that is
# not a ttk widget has to be told individually -- and the ttk widgets only obey
# under a fully styleable theme (see _apply_theme).
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


# Reference solutions are stored as one long string so the source of
# exercises.py stays readable. Nobody wants to read one back that way, so the
# GUI breaks it into clauses before showing it.
CLAUSES = (
    "WITH RECURSIVE", "SELECT DISTINCT", "GROUP BY", "ORDER BY", "UNION ALL",
    "LEFT JOIN", "CROSS JOIN", "INNER JOIN", "INTERSECT", "WITH", "SELECT",
    "FROM", "JOIN", "ON", "WHERE", "HAVING", "LIMIT", "UNION", "EXCEPT",
)
_WORD = re.compile(r"\w")
_SUBQUERY = re.compile(r"\(\s*(SELECT|WITH|VALUES)\b", re.IGNORECASE)


def format_sql(sql, indent="    "):
    """Break a one-line reference solution onto readable lines.

    One clause per line, one select-list item per line, indented by subquery
    depth. Only parentheses that open a subquery are structural; a function
    call -- ROUND(...), OVER (...) -- is left strictly alone, so an expression
    is never split in half. Purely cosmetic: the SQL is unchanged.
    """
    s = " ".join(sql.split())
    out, line, i = [], "", 0
    depth = 0          # nesting of subquery parens only
    stack = []         # True for each open paren that was structural
    in_select = False  # inside a select list, so commas end a line

    def flush():
        nonlocal line
        if line.strip():
            out.append(indent * depth + line.strip())
        line = ""

    while i < len(s):
        ch = s[i]

        if ch == "'":                                    # string literal
            j = s.index("'", i + 1) + 1
            line, i = line + s[i:j], j
            continue

        if ch == "(":
            stack.append(bool(_SUBQUERY.match(s, i)))
            line += "("
            if stack[-1]:
                flush()
                depth += 1
            i += 1
            continue

        if ch == ")":
            if stack and stack.pop():
                flush()
                depth -= 1
                line = ")"
            else:
                line += ")"
            i += 1
            continue

        # Only break at statement level -- never inside a function call.
        at_top = len(stack) == depth

        if ch == "," and in_select and at_top:
            line += ","
            flush()
            i += 1
            continue

        if at_top and (not line or not _WORD.match(line[-1])) \
                and (i == 0 or not _WORD.match(s[i - 1])):
            upper = s[i:].upper()
            hit = next((k for k in CLAUSES if upper.startswith(k) and (
                len(s) == i + len(k) or not _WORD.match(s[i + len(k)]))), None)
            if hit:
                flush()
                line = s[i:i + len(hit)]
                if hit.startswith("SELECT"):
                    in_select = True
                elif hit == "FROM":
                    in_select = False
                i += len(hit)
                continue

        line += ch
        i += 1

    flush()
    return "\n".join(out)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("testdb - SQL practice")
        self.minsize(940, 620)
        self._centre(1220, 800)

        if not db.DB_PATH.exists():
            messagebox.showerror(
                "Database missing",
                f"{db.DB_PATH} does not exist.\n\nRun:  python seed.py",
            )
            self.destroy()
            return

        self.conn = sqlite3.connect(f"file:{db.DB_PATH}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

        self.mono_family = _pick_family(MONO_FAMILIES, "TkFixedFont")
        self.ui_family = _pick_family(UI_FAMILIES, "TkDefaultFont")
        self.mono = tkfont.Font(family=self.mono_family, size=BASE_FONT_SIZE)
        self._scale_named_fonts()
        self.current = FREE
        self.progress = self._load_progress()

        self._build_ui()
        self._populate_exercises()
        self._populate_schema()
        self._select_exercise(FREE)
        self._refresh_progress_label()

    def _centre(self, want_w, want_h):
        """Fit the window to the screen and centre it.

        Without this the window can be placed low enough that the status bar --
        which is where grading feedback appears -- falls off the bottom edge.
        """
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(want_w, sw - 80), min(want_h, sh - 80)
        self.geometry(f"{w}x{h}+{max((sw - w) // 2, 0)}+{max((sh - h) // 2, 0)}")

    # ------------------------------------------------------------- persistence
    def _load_progress(self):
        try:
            raw = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
            return {"solved": set(raw.get("solved", [])), "sql": raw.get("sql", {})}
        except (OSError, ValueError):
            return {"solved": set(), "sql": {}}

    def _save_progress(self):
        try:
            PROGRESS_PATH.write_text(
                json.dumps(
                    {"solved": sorted(self.progress["solved"]), "sql": self.progress["sql"]},
                    indent=2,
                ),
                encoding="utf-8",
            )
        except OSError:
            pass  # practice progress is not worth crashing over

    # -------------------------------------------------------------------- theme
    def _scale_named_fonts(self):
        """Lift Tk's named fonts to BASE_FONT_SIZE, which is what ttk inherits.

        The ttk widgets here take no font= argument: the trees, buttons, tabs
        and status bar all draw in TkDefaultFont/TkTextFont/TkHeadingFont.
        Setting those once is what makes a size change reach the whole window
        instead of just the two Text widgets. max() keeps it a floor so a
        platform whose default is already larger is left alone.
        """
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont",
                     "TkHeadingFont", "TkTooltipFont", "TkIconFont"):
            try:
                f = tkfont.nametofont(name)
            except tk.TclError:
                continue          # not every named font exists on every platform
            f.configure(size=max(f.actual("size"), BASE_FONT_SIZE))
        tkfont.nametofont("TkFixedFont").configure(
            family=self.mono_family, size=BASE_FONT_SIZE)

    def _apply_theme(self):
        """Paint every ttk widget class dark.

        'vista' is the good-looking default on Windows but it draws natively and
        silently ignores background/foreground, so a dark scheme is impossible
        under it. 'clam' is fully styleable, which is the whole reason for the
        switch -- everything below is what vista was doing for us for free.
        """
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG_APP, foreground=FG_TEXT,
                        fieldbackground=BG_FIELD, bordercolor=BORDER,
                        lightcolor=BG_SURFACE, darkcolor=BG_APP,
                        troughcolor=BG_APP, focuscolor=BG_SELECT)
        style.configure("TFrame", background=BG_APP)
        style.configure("TLabel", background=BG_APP, foreground=FG_TEXT)
        style.configure("TPanedwindow", background=BG_APP)
        style.configure("Sash", sashthickness=6, gripcount=0,
                        background=BORDER)

        style.configure("TButton", background=BG_SURFACE, foreground=FG_TEXT,
                        bordercolor=BORDER, lightcolor=BG_SURFACE,
                        darkcolor=BG_SURFACE, focusthickness=0,
                        padding=(10, 4))
        style.map("TButton",
                  background=[("pressed", BG_SELECT), ("active", "#333335"),
                              ("disabled", BG_APP)],
                  foreground=[("disabled", "#5f5f5f")])

        # clam hard-codes a near-white lightcolor per style, which draws as a
        # bright bevel around the notebook and its tabs. The root "." setting
        # does not win against that, so each one has to be named explicitly.
        style.configure("TNotebook", background=BG_APP, bordercolor=BORDER,
                        lightcolor=BG_APP, darkcolor=BG_APP, borderwidth=0,
                        tabmargins=(2, 4, 2, 0))
        style.configure("TNotebook.Tab", background=BG_APP,
                        foreground=FG_MUTED, padding=(12, 5), borderwidth=1,
                        bordercolor=BORDER, lightcolor=BG_APP,
                        darkcolor=BG_APP)
        style.map("TNotebook.Tab",
                  background=[("selected", BG_SURFACE)],
                  foreground=[("selected", FG_HEADING)],
                  lightcolor=[("selected", BG_SURFACE)],
                  expand=[("selected", (0, 0, 0, 0))])

        # Derived, not fixed: at a larger font a hard-coded row height
        # crops the text instead of growing with it.
        row_h = tkfont.nametofont("TkDefaultFont").metrics("linespace") + 6
        style.configure("Treeview", rowheight=row_h, background=BG_FIELD,
                        fieldbackground=BG_FIELD, foreground=FG_TEXT,
                        bordercolor=BORDER, borderwidth=0,
                        lightcolor=BG_FIELD, darkcolor=BG_FIELD)
        style.map("Treeview",
                  background=[("selected", BG_SELECT)],
                  foreground=[("selected", "#ffffff")])
        style.configure("Treeview.Heading", background=BG_SURFACE,
                        foreground=FG_HEADING, relief="flat", borderwidth=1,
                        bordercolor=BORDER, lightcolor=BG_SURFACE,
                        darkcolor=BG_SURFACE)
        style.map("Treeview.Heading",
                  background=[("active", "#33373a")])
        # clam draws a dotted focus ring on the tree; kill it, it reads as noise
        style.layout("Treeview.Item", [
            ("Treeitem.padding", {"sticky": "nswe", "children": [
                ("Treeitem.indicator", {"side": "left", "sticky": ""}),
                ("Treeitem.image", {"side": "left", "sticky": ""}),
                ("Treeitem.text", {"side": "left", "sticky": ""}),
            ]}),
        ])

        style.configure("TScrollbar", background=BG_SURFACE, troughcolor=BG_APP,
                        bordercolor=BG_APP, arrowcolor=FG_MUTED,
                        borderwidth=0)
        style.map("TScrollbar",
                  background=[("pressed", BG_SELECT), ("active", "#3d3d3f")])

    # ------------------------------------------------------------------- layout
    def _build_ui(self):
        self.configure(background=BG_APP)
        self._apply_theme()

        # The status bar is where grading feedback appears, so it is packed
        # FIRST and anchored to the bottom. pack allocates in order: if the
        # expanding pane went first it would claim everything and Tk would
        # unmap the status bar entirely at small window sizes.
        self.status = tk.Label(self, text="Ready", anchor="w", justify="left",
                               padx=8, pady=4, wraplength=1100,
                               background=BG_INFO, foreground="white")
        self.status.pack(fill="x", side="bottom")

        outer = ttk.PanedWindow(self, orient="horizontal")
        outer.pack(fill="both", expand=True, padx=6, pady=6)

        # ---- left: exercises + schema -------------------------------------
        left = ttk.Notebook(outer, width=290)
        outer.add(left, weight=0)

        ex_frame = ttk.Frame(left)
        left.add(ex_frame, text="Exercises")
        self.ex_tree = ttk.Treeview(ex_frame, show="tree", selectmode="browse")
        ex_scroll = ttk.Scrollbar(ex_frame, orient="vertical", command=self.ex_tree.yview)
        self.ex_tree.configure(yscrollcommand=ex_scroll.set)
        self.ex_tree.pack(side="left", fill="both", expand=True)
        ex_scroll.pack(side="right", fill="y")
        self.ex_tree.bind("<<TreeviewSelect>>", self._on_exercise_select)

        sc_frame = ttk.Frame(left)
        left.add(sc_frame, text="Schema")
        self.schema_tree = ttk.Treeview(sc_frame, show="tree", selectmode="browse")
        sc_scroll = ttk.Scrollbar(sc_frame, orient="vertical", command=self.schema_tree.yview)
        self.schema_tree.configure(yscrollcommand=sc_scroll.set)
        self.schema_tree.pack(side="left", fill="both", expand=True)
        sc_scroll.pack(side="right", fill="y")
        self.schema_tree.bind("<Double-1>", self._insert_schema_name)

        # ---- right: question / editor / results ---------------------------
        # The question is fixed-height content, so it sits ABOVE the split
        # rather than competing with the editor for space. Only the editor and
        # the results share what is left.
        right = ttk.Frame(outer)
        outer.add(right, weight=1)

        top = ttk.Frame(right)
        top.pack(fill="x", side="top")

        self.title_var = tk.StringVar()
        ttk.Label(top, textvariable=self.title_var,
                  font=(self.ui_family, BASE_FONT_SIZE + 1, "bold"),
                  foreground=FG_HEADING).pack(anchor="w", padx=4, pady=(0, 2))
        self.question = tk.Text(top, height=5, wrap="word", relief="flat",
                                font=(self.ui_family, BASE_FONT_SIZE),
                                background=BG_QUESTION,
                                foreground=FG_TEXT, insertbackground=CURSOR,
                                selectbackground=BG_SELECT,
                                selectforeground="#ffffff",
                                highlightthickness=0, padx=8, pady=6)
        self.question.pack(fill="x", padx=4)
        self.question.configure(state="disabled")
        self.question.bind("<Configure>", lambda _e: self._fit_question())

        split = ttk.PanedWindow(right, orient="vertical")
        split.pack(fill="both", expand=True, pady=(6, 0))

        mid = ttk.Frame(split)
        split.add(mid, weight=3)

        ttk.Label(mid, text="SQL", foreground=FG_MUTED).pack(anchor="w", padx=4)

        # Packed before the editor so the buttons always get their height --
        # under a squeeze it is the editor that shrinks, never the controls.
        bar = ttk.Frame(mid)
        bar.pack(side="bottom", fill="x", padx=4, pady=4)
        ttk.Button(bar, text="Run  (F5)", command=self.run_query).pack(side="left")
        self.check_btn = ttk.Button(bar, text="Check answer  (Ctrl+Enter)",
                                    command=self.check_answer)
        self.check_btn.pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Clear", command=lambda: self.editor.delete("1.0", "end")).pack(
            side="left", padx=(6, 0)
        )
        self.explain_btn = ttk.Button(bar, text="Explain plan (F6)",
                                      command=self.explain_plan)
        self.explain_btn.pack(side="left", padx=(6, 0))
        self.solution_btn = ttk.Button(bar, text="Show solution", command=self.show_solution)
        self.solution_btn.pack(side="left", padx=(6, 0))
        # Only the efficiency questions open with a query already in the editor,
        # so this is the only place restoring one means anything. Packed and
        # unpacked in _select_exercise rather than greyed out, so it is absent
        # rather than merely disabled on the other 24 questions.
        self.starter_btn = ttk.Button(bar, text="Reset",
                                      command=self.reset_starter)
        self.progress_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.progress_var,
                  foreground=FG_MUTED).pack(side="right")

        editor_wrap = ttk.Frame(mid)
        editor_wrap.pack(fill="both", expand=True, padx=4)
        self.editor = tk.Text(editor_wrap, height=14, wrap="none", font=self.mono,
                              undo=True, tabs=("1c",), background=BG_FIELD,
                              foreground=FG_TEXT, insertbackground=CURSOR,
                              selectbackground=BG_SELECT,
                              selectforeground="#ffffff",
                              relief="flat", highlightthickness=1,
                              highlightbackground=BORDER,
                              highlightcolor=BG_SELECT)
        ed_y = ttk.Scrollbar(editor_wrap, orient="vertical", command=self.editor.yview)
        self.editor.configure(yscrollcommand=ed_y.set)
        self.editor.pack(side="left", fill="both", expand=True)
        ed_y.pack(side="right", fill="y")

        bottom = ttk.Frame(split)
        split.add(bottom, weight=2)

        res_wrap = ttk.Frame(bottom)
        res_wrap.pack(fill="both", expand=True, padx=4)
        self.results = ttk.Treeview(res_wrap, show="headings", selectmode="browse")
        res_y = ttk.Scrollbar(res_wrap, orient="vertical", command=self.results.yview)
        res_x = ttk.Scrollbar(res_wrap, orient="horizontal", command=self.results.xview)
        self.results.configure(yscrollcommand=res_y.set, xscrollcommand=res_x.set)
        self.results.grid(row=0, column=0, sticky="nsew")
        res_y.grid(row=0, column=1, sticky="ns")
        res_x.grid(row=1, column=0, sticky="ew")
        res_wrap.rowconfigure(0, weight=1)
        res_wrap.columnconfigure(0, weight=1)
        self.results.tag_configure("odd", background=BG_STRIPE)

        # keep the wrap width in step with the window
        self.bind("<Configure>",
                  lambda e: self.status.configure(wraplength=max(self.winfo_width() - 40, 400)))

        self.bind("<F5>", lambda e: (self.run_query(), "break")[1])
        self.bind("<F6>", lambda e: (self.explain_plan(), "break")[1])
        self.bind("<Control-Return>", lambda e: (self.check_answer(), "break")[1])
        self.editor.bind("<Control-Return>", lambda e: (self.check_answer(), "break")[1])
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------- tree filling
    def _populate_exercises(self):
        self.ex_tree.insert("", "end", iid="ex0", text="  Free query (scratch)")
        for tier in ex.TIERS:
            node = self.ex_tree.insert("", "end", iid=f"t{tier}", text=tier, open=True)
            for e in (x for x in ex.EXERCISES if x["tier"] == tier):
                self.ex_tree.insert(node, "end", iid=f"ex{e['id']}",
                                    text=self._exercise_label(e))

    def _exercise_label(self, e):
        mark = "[x]" if e["ledger"] in self.progress["solved"] else "[ ]"
        return f"{mark} {e['id']}. {e['title']}"

    def _populate_schema(self):
        tables = [r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        for t in tables:
            n = self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            node = self.schema_tree.insert("", "end", text=f"{t}  ({n})", open=False)
            for col in self.conn.execute(f"PRAGMA table_info({t})"):
                flags = []
                if col["pk"]:
                    flags.append("PK")
                if col["notnull"]:
                    flags.append("NOT NULL")
                suffix = f"  {', '.join(flags)}" if flags else ""
                self.schema_tree.insert(node, "end",
                                        text=f"{col['name']} : {col['type']}{suffix}")

    def _insert_schema_name(self, _event):
        sel = self.schema_tree.selection()
        if not sel:
            return
        text = self.schema_tree.item(sel[0], "text")
        name = text.split(" ")[0].split(":")[0].strip()
        self.editor.insert("insert", name)
        self.editor.focus_set()

    # ------------------------------------------------------------- interactions
    def _on_exercise_select(self, _event):
        sel = self.ex_tree.selection()
        if not sel or not sel[0].startswith("ex"):
            return
        self._stash_sql()
        self._select_exercise(int(sel[0][2:]))

    def _key(self, eid):
        """Progress key for an exercise: its ledger id, which is unique forever.

        Numeric ids restart at 1 with each new question set, so keying on them
        made old progress attach itself to whatever question later took that
        slot.
        """
        if eid == FREE:
            return "scratch"
        return ex.BY_ID[eid]["ledger"]

    def _stash_sql(self):
        text = self.editor.get("1.0", "end").strip()
        if text:
            self.progress["sql"][self._key(self.current)] = text
        else:
            self.progress["sql"].pop(self._key(self.current), None)

    def _select_exercise(self, eid):
        self.current = eid
        self.editor.delete("1.0", "end")
        saved = self.progress["sql"].get(self._key(eid), "")
        if not saved and eid != FREE:
            # Efficiency questions open with a query that already returns the
            # right answer by a slow route -- the task is to improve the plan,
            # not to work out what to select. Only used when nothing of yours
            # is saved for this exercise, so it can never overwrite your work.
            saved = format_sql(ex.BY_ID[eid].get("starter_sql", "")) \
                if ex.BY_ID[eid].get("starter_sql") else ""
        self.editor.insert("1.0", saved)
        self.editor.edit_reset()

        if eid == FREE:
            self.title_var.set("Free query")
            body = ("Scratch pad -- run anything you like against the database.\n"
                    "Nothing is graded here. Pick an exercise on the left to be graded.")
            state = "disabled"
        else:
            e = ex.BY_ID[eid]
            done = "  [solved]" if e["ledger"] in self.progress["solved"] else ""
            self.title_var.set(f"{e['id']}. {e['title']}   ({e['tier']}){done}")
            body = e["prompt"]
            state = "normal"

        self.check_btn.configure(state=state)
        self.solution_btn.configure(state=state)
        if eid != FREE and ex.BY_ID[eid].get("starter_sql"):
            self.starter_btn.pack(side="left", padx=(6, 0))
        else:
            self.starter_btn.pack_forget()
        self.question.configure(state="normal")
        self.question.delete("1.0", "end")
        self.question.insert("1.0", body)
        self.question.configure(state="disabled")
        self._fit_question()
        self._set_status("Ready", BG_INFO)
        self.editor.focus_set()

    def _fit_question(self):
        """Grow the question panel to fit its text.

        A fixed height silently truncated longer prompts, and the line that gets
        cut is the last one -- which is the "Return: ..." line naming the columns
        the answer needs.
        """
        self.question.update_idletasks()
        try:
            wanted = self.question.count("1.0", "end", "displaylines")[0]
        except (tk.TclError, TypeError):
            wanted = int(self.question.index("end-1c").split(".")[0])
        wanted = max(3, min(wanted, QUESTION_MAX_LINES))
        if wanted != int(self.question.cget("height")):
            self.question.configure(height=wanted)

    def _sql(self):
        return self.editor.get("1.0", "end").strip().rstrip(";")

    def run_query(self):
        sql = self._sql()
        if not sql:
            self._set_status("Nothing to run.", BG_INFO)
            return None
        try:
            # fetchall() is inside the limit too: a runaway recursive CTE does
            # not hang on execute(), it hangs while the rows pile up.
            with db.time_limit(self.conn):
                cur = self.conn.execute(sql)
                if cur.description is None:
                    self._set_status("Statement returned no result set.", BG_INFO)
                    return None
                rows = db.fetch_capped(cur)
            self._show_rows(rows, [d[0] for d in cur.description])
            shown = (f" Showing the first {DISPLAY_ROWS:,}."
                     if len(rows) > DISPLAY_ROWS else "")
            self._set_status(f"{len(rows):,} row(s).{shown}", BG_INFO)
            return rows
        except (db.QueryTimeout, db.TooManyRows) as exc:
            self._clear_results()
            self._set_status(str(exc), BG_BAD)
            return None
        except sqlite3.Error as exc:
            self._clear_results()
            self._set_status(f"SQL error: {exc}", BG_BAD)
            return None

    def check_answer(self):
        if self.current == FREE:
            return
        rows = self.run_query()
        if rows is None:
            return
        e = ex.BY_ID[self.current]
        expected = self.conn.execute(e["solution"]).fetchall()
        passed, msg = ex.compare([tuple(r) for r in rows], [tuple(r) for r in expected])
        if passed and (e.get("plan_requires") or e.get("plan_forbids")):
            # An efficiency question cannot be graded on its result -- the slow
            # way and the fast way return the same rows. So the plan is part of
            # the answer, and a correct result taken by the wrong route is not
            # a pass.
            passed, plan_msg = ex.plan_ok(
                e, ex.query_plan(self.conn, self._sql()))
            if not passed:
                msg = plan_msg
        if passed:
            self.progress["solved"].add(self._key(self.current))
            self.ex_tree.item(f"ex{self.current}", text=self._exercise_label(e))
            self.title_var.set(f"{e['id']}. {e['title']}   ({e['tier']})  [solved]")
            self._refresh_progress_label()
            self._stash_sql()
            self._save_progress()
            if e.get("note"):
                msg = f"{msg}   {e['note']}"
        self._set_status(msg, BG_OK if passed else BG_BAD)

    def explain_plan(self):
        """Show how SQLite intends to run the query in the editor.

        The three words worth knowing are in nearly every plan:
          SCAN    every row of the table is read
          SEARCH  an index is used to jump straight to the rows that match
          TEMP B-TREE  the rows had to be sorted or grouped on the fly
        Timed as well, because a plan tells you the shape and the clock tells
        you whether the shape matters.
        """
        sql = self._sql()
        if not sql:
            return
        try:
            with db.time_limit(self.conn):
                plan = self.conn.execute(
                    "EXPLAIN QUERY PLAN " + sql).fetchall()
                start = time.perf_counter()
                n = len(db.fetch_capped(self.conn.execute(sql)))
                elapsed = (time.perf_counter() - start) * 1000
        except Exception as exc:
            self._set_status(f"error: {exc}", BG_BAD)
            return
        self._show_rows([(r[0], r[3]) for r in plan], ["step", "detail"])
        self._set_status(
            f"{n} row(s) in {elapsed:.1f} ms.  SCAN reads every row;"
            f" SEARCH uses an index; TEMP B-TREE means a sort or group was"
            f" built on the fly.", BG_INFO)

    def reset_starter(self):
        """Put the question's original slow query back in the editor.

        No confirmation: edit_reset is deliberately NOT called, so Ctrl+Z undoes
        the restore and nothing you had typed is unrecoverable.
        """
        if self.current == FREE:
            return
        starter = ex.BY_ID[self.current].get("starter_sql")
        if not starter:
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", format_sql(starter))
        self._set_status(
            "Starter query restored -- it returns the right answer by the wrong"
            " route. Ctrl+Z undoes this.", BG_INFO)

    def show_solution(self):
        if self.current == FREE:
            return
        if not messagebox.askyesno(
            "Show solution",
            "This replaces your editor contents with the reference answer.\n\nReveal it?",
        ):
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", format_sql(ex.BY_ID[self.current]["solution"]))
        self._set_status("Reference solution shown -- it is one valid answer, not the only one.",
                         BG_INFO)

    # --------------------------------------------------------------- rendering
    def _clear_results(self):
        self.results.delete(*self.results.get_children())
        self.results["columns"] = ()

    def _show_rows(self, rows, headers):
        self._clear_results()
        self.results["columns"] = headers
        sample = rows[:120]
        # Measured rather than assumed -- the old 8px/char was tied to the
        # previous font size and clips once the cells draw wider.
        char_w = tkfont.nametofont("TkDefaultFont").measure("0")
        for i, h in enumerate(headers):
            width = max([len(str(h))] + [len(self._fmt(r[i])) for r in sample] or [0])
            self.results.heading(h, text=h)
            self.results.column(h, width=min(max(width * char_w + 24, 70), 340),
                                anchor="w")
        for n, row in enumerate(rows[:DISPLAY_ROWS]):
            self.results.insert("", "end",
                                values=[self._fmt(v) for v in row],
                                tags=("odd",) if n % 2 else ())

    @staticmethod
    def _fmt(v):
        if v is None:
            return "NULL"
        if isinstance(v, float):
            return f"{v:,.2f}"
        return str(v)

    def _set_status(self, text, colour):
        self.status.configure(text=text, background=colour)

    def _refresh_progress_label(self):
        # Count only the CURRENT set. progress.json also holds solved ledger ids
        # from retired sets, which must not inflate the score.
        live = {e["ledger"] for e in ex.EXERCISES}
        done = len(live & set(self.progress["solved"]))
        self.progress_var.set(f"Solved {done} / {len(ex.EXERCISES)}")

    def _on_close(self):
        self._stash_sql()
        self._save_progress()
        self.conn.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
