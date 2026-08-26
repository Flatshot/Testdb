"""Desktop GUI for practicing SQL against testdb.

    python gui.py

Left pane picks an exercise or browses the schema. Write SQL on the right,
F5 to run it, Ctrl+Enter to have your result graded against the expected one.

The database is opened READ-ONLY, so nothing you type in here can damage the
practice data no matter how wrong it goes.

Progress (which exercises you've solved, and your SQL for each) is kept in
progress.json next to this file.
"""

import json
import sqlite3
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

import db
import exercises as ex

PROGRESS_PATH = db.HERE / "progress.json"
FREE = 0  # pseudo-exercise id for the scratch pad

BG_OK = "#1a7f37"
BG_BAD = "#b3261e"
BG_INFO = "#444444"


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

        self.mono = tkfont.Font(family="Consolas", size=11)
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

    # ------------------------------------------------------------------- layout
    def _build_ui(self):
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Treeview", rowheight=22)

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
        right = ttk.PanedWindow(outer, orient="vertical")
        outer.add(right, weight=1)

        top = ttk.Frame(right)
        right.add(top, weight=0)

        self.title_var = tk.StringVar()
        ttk.Label(top, textvariable=self.title_var, font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=4, pady=(0, 2)
        )
        self.question = tk.Text(top, height=5, wrap="word", relief="flat",
                                font=("Segoe UI", 10), background="#f4f4f4", padx=8, pady=6)
        self.question.pack(fill="x", padx=4)
        self.question.configure(state="disabled")

        mid = ttk.Frame(right)
        right.add(mid, weight=1)

        ttk.Label(mid, text="SQL").pack(anchor="w", padx=4)
        editor_wrap = ttk.Frame(mid)
        editor_wrap.pack(fill="both", expand=True, padx=4)
        self.editor = tk.Text(editor_wrap, height=9, wrap="none", font=self.mono,
                              undo=True, tabs=("1c",))
        ed_y = ttk.Scrollbar(editor_wrap, orient="vertical", command=self.editor.yview)
        self.editor.configure(yscrollcommand=ed_y.set)
        self.editor.pack(side="left", fill="both", expand=True)
        ed_y.pack(side="right", fill="y")

        bar = ttk.Frame(mid)
        bar.pack(fill="x", padx=4, pady=4)
        ttk.Button(bar, text="Run  (F5)", command=self.run_query).pack(side="left")
        self.check_btn = ttk.Button(bar, text="Check answer  (Ctrl+Enter)",
                                    command=self.check_answer)
        self.check_btn.pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Clear", command=lambda: self.editor.delete("1.0", "end")).pack(
            side="left", padx=(6, 0)
        )
        self.solution_btn = ttk.Button(bar, text="Show solution", command=self.show_solution)
        self.solution_btn.pack(side="left", padx=(6, 0))
        self.progress_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.progress_var).pack(side="right")

        bottom = ttk.Frame(right)
        right.add(bottom, weight=1)

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
        self.results.tag_configure("odd", background="#f7f7f7")

        self.status = tk.Label(self, text="Ready", anchor="w", justify="left",
                               padx=8, pady=4, wraplength=1100,
                               background=BG_INFO, foreground="white")
        self.status.pack(fill="x", side="bottom")
        # keep the wrap width in step with the window
        self.bind("<Configure>",
                  lambda e: self.status.configure(wraplength=max(self.winfo_width() - 40, 400)))

        self.bind("<F5>", lambda e: (self.run_query(), "break")[1])
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
        self.editor.insert("1.0", self.progress["sql"].get(self._key(eid), ""))
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
        self.question.configure(state="normal")
        self.question.delete("1.0", "end")
        self.question.insert("1.0", body)
        self.question.configure(state="disabled")
        self._set_status("Ready", BG_INFO)
        self.editor.focus_set()

    def _sql(self):
        return self.editor.get("1.0", "end").strip().rstrip(";")

    def run_query(self):
        sql = self._sql()
        if not sql:
            self._set_status("Nothing to run.", BG_INFO)
            return None
        try:
            cur = self.conn.execute(sql)
            if cur.description is None:
                self._set_status("Statement returned no result set.", BG_INFO)
                return None
            rows = cur.fetchall()
            self._show_rows(rows, [d[0] for d in cur.description])
            self._set_status(f"{len(rows)} row(s).", BG_INFO)
            return rows
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

    def show_solution(self):
        if self.current == FREE:
            return
        if not messagebox.askyesno(
            "Show solution",
            "This replaces your editor contents with the reference answer.\n\nReveal it?",
        ):
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", ex.BY_ID[self.current]["solution"])
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
        for i, h in enumerate(headers):
            width = max([len(str(h))] + [len(self._fmt(r[i])) for r in sample] or [0])
            self.results.heading(h, text=h)
            self.results.column(h, width=min(max(width * 8 + 24, 70), 340), anchor="w")
        for n, row in enumerate(rows):
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
