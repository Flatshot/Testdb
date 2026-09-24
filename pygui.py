"""The Python tab of the practice GUI.

Same shape as the SQL tab: a tree of exercises on the left; the question,
an editor and an output pane on the right. The differences are what the
editor needs -- Tab inserts four spaces and Return keeps the indentation,
because Python is whitespace-sensitive and a Tk Text widget knows nothing
about that -- and that the output is text, not a table.

The pane owns nothing global. The window (gui.py) hands it the fonts, the
progress dict and a way to set the status bar, and calls run(), check() and
stash() on it when the keyboard shortcuts fire while this tab is in front.
"""

import tkinter as tk
from tkinter import messagebox, ttk

import pyexercises as px
from ui import (BASE_FONT_SIZE, BG_BAD, BG_FIELD, BG_INFO, BG_OK, BORDER,
                CURSOR, FG_HEADING, FG_MUTED, FG_TEXT, BG_SELECT,
                fit_question, make_editor, make_question, set_text)

FREE = 0        # pseudo-exercise id for the scratch pad
INDENT = "    "


class PythonPane(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current = FREE
        self._build()
        self._populate()
        self._select(FREE)
        self.refresh_progress()

    # ------------------------------------------------------------------ layout
    def _build(self):
        outer = ttk.PanedWindow(self, orient="horizontal")
        outer.pack(fill="both", expand=True)

        left = ttk.Frame(outer, width=290)
        outer.add(left, weight=0)
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.Frame(outer)
        outer.add(right, weight=1)

        top = ttk.Frame(right)
        top.pack(fill="x", side="top")
        self.title_var = tk.StringVar()
        ttk.Label(top, textvariable=self.title_var,
                  font=(self.app.ui_family, BASE_FONT_SIZE + 1, "bold"),
                  foreground=FG_HEADING).pack(anchor="w", padx=4, pady=(0, 2))
        self.question = make_question(top, self.app.ui_family)
        self.question.pack(fill="x", padx=4)

        split = ttk.PanedWindow(right, orient="vertical")
        split.pack(fill="both", expand=True, pady=(6, 0))

        mid = ttk.Frame(split)
        split.add(mid, weight=3)
        ttk.Label(mid, text="Python", foreground=FG_MUTED).pack(anchor="w", padx=4)

        bar = ttk.Frame(mid)
        bar.pack(side="bottom", fill="x", padx=4, pady=4)
        ttk.Button(bar, text="Run  (F5)", command=self.run).pack(side="left")
        self.check_btn = ttk.Button(bar, text="Check answer  (Ctrl+Enter)",
                                    command=self.check)
        self.check_btn.pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Clear",
                   command=lambda: self.editor.delete("1.0", "end")).pack(
            side="left", padx=(6, 0))
        self.solution_btn = ttk.Button(bar, text="Show solution",
                                       command=self.show_solution)
        self.solution_btn.pack(side="left", padx=(6, 0))
        self.progress_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.progress_var,
                  foreground=FG_MUTED).pack(side="right")

        wrap = ttk.Frame(mid)
        wrap.pack(fill="both", expand=True, padx=4)
        self.editor = make_editor(wrap, self.app.mono)
        ed_y = ttk.Scrollbar(wrap, orient="vertical", command=self.editor.yview)
        self.editor.configure(yscrollcommand=ed_y.set)
        self.editor.pack(side="left", fill="both", expand=True)
        ed_y.pack(side="right", fill="y")
        self.editor.bind("<Tab>", self._tab)
        self.editor.bind("<Return>", self._return)
        self.editor.bind("<BackSpace>", self._backspace)
        self.editor.bind("<Control-Return>", lambda e: (self.check(), "break")[1])

        bottom = ttk.Frame(split)
        split.add(bottom, weight=2)
        ttk.Label(bottom, text="Output", foreground=FG_MUTED).pack(anchor="w", padx=4)
        out_wrap = ttk.Frame(bottom)
        out_wrap.pack(fill="both", expand=True, padx=4)
        self.output = tk.Text(out_wrap, height=8, wrap="word", font=self.app.mono,
                              background=BG_FIELD, foreground=FG_TEXT,
                              insertbackground=CURSOR, selectbackground=BG_SELECT,
                              selectforeground="#ffffff", relief="flat",
                              highlightthickness=1, highlightbackground=BORDER,
                              state="disabled", padx=6, pady=4)
        out_y = ttk.Scrollbar(out_wrap, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=out_y.set)
        self.output.pack(side="left", fill="both", expand=True)
        out_y.pack(side="right", fill="y")

    def _populate(self):
        self.tree.insert("", "end", iid="py0", text="  Scratch (run anything)")
        for tier in px.TIERS:
            node = self.tree.insert("", "end", iid=f"t{tier}", text=tier, open=True)
            for e in (x for x in px.EXERCISES if x["tier"] == tier):
                self.tree.insert(node, "end", iid=f"py{e['id']}", text=self._label(e))

    def _label(self, e):
        done = "  [solved]" if e["ledger"] in self.app.progress["solved"] else ""
        return f"  {e['id']}. {e['title']}{done}"

    # ------------------------------------------------------- editor behaviour
    # Tk's Text widget inserts a literal tab and knows nothing about
    # indentation. These three bindings give it the minimum an editor for
    # Python needs: Tab is four spaces, Return copies the indentation of the
    # line above (plus one level after a colon), and Backspace at the start
    # of the indentation removes a whole level rather than one space.
    def _tab(self, _event):
        self.editor.insert("insert", INDENT)
        return "break"

    def _return(self, _event):
        line = self.editor.get("insert linestart", "insert")
        indent = line[:len(line) - len(line.lstrip())]
        if line.rstrip().endswith(":"):
            indent += INDENT
        self.editor.insert("insert", "\n" + indent)
        self.editor.see("insert")
        return "break"

    def _backspace(self, _event):
        before = self.editor.get("insert linestart", "insert")
        if before and not before.strip() and len(before) % len(INDENT) == 0:
            self.editor.delete(f"insert-{len(INDENT)}c", "insert")
            return "break"
        return None

    def _code(self):
        return self.editor.get("1.0", "end").rstrip() + "\n"

    # ---------------------------------------------------------- selection
    def _on_select(self, _event):
        sel = self.tree.selection()
        if not sel or not sel[0].startswith("py"):
            return
        self.stash()
        self._select(int(sel[0][2:]))

    def _key(self, eid):
        return "py-scratch" if eid == FREE else px.BY_ID[eid]["ledger"]

    def stash(self):
        """Keep the editor text for the current question in progress."""
        text = self.editor.get("1.0", "end").strip()
        store = self.app.progress["python"]
        if text:
            store[self._key(self.current)] = text
        else:
            store.pop(self._key(self.current), None)

    def _select(self, eid):
        self.current = eid
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", self.app.progress["python"].get(self._key(eid), ""))
        self.editor.edit_reset()
        if eid == FREE:
            self.title_var.set("Scratch")
            body = ("Run any Python you like here. Nothing is graded."
                    " Pick an exercise on the left to be graded.")
            state = "disabled"
        else:
            e = px.BY_ID[eid]
            done = "  [solved]" if e["ledger"] in self.app.progress["solved"] else ""
            self.title_var.set(f"{e['id']}. {e['title']}   ({e['tier']}){done}")
            body = e["prompt"]
            state = "normal"
        self.check_btn.configure(state=state)
        self.solution_btn.configure(state=state)
        set_text(self.question, body)
        fit_question(self.question)
        set_text(self.output, "")
        self.app.set_status("Ready", BG_INFO)
        self.editor.focus_set()

    # ------------------------------------------------------------- actions
    def run(self):
        code = self._code()
        if not code.strip():
            self.app.set_status("Nothing to run.", BG_INFO)
            return
        if self.current == FREE:
            result = px.pyrun.run_program(code)
            text = result["stdout"]
            if result["stderr"]:
                text += ("\n" if text and not text.endswith("\n") else "") + result["stderr"]
            set_text(self.output, text or "(nothing printed)")
            self.app.set_status("Ran." if result["ok"] else
                                "Your program raised an error -- see the output pane.",
                                BG_INFO if result["ok"] else BG_BAD)
            return
        e = px.BY_ID[self.current]
        result = px.run(e, code)
        set_text(self.output, px.render(e, result))
        if result.get("timed_out"):
            self.app.set_status(result.get("stderr") or result.get("define_error"), BG_BAD)
        elif px.is_program(e):
            self.app.set_status("Ran." if result["ok"] else
                                "Your program raised an error -- see the output pane.",
                                BG_INFO if result["ok"] else BG_BAD)
        elif result["define_error"]:
            self.app.set_status(result["define_error"].splitlines()[-1], BG_BAD)
        else:
            raised = sum("error" in r for r in result["results"])
            self.app.set_status(
                f"Ran {len(result['results'])} test call(s)"
                + (f", {raised} raised an error" if raised else "")
                + ". Check answer compares them with the reference.", BG_INFO)

    def check(self):
        if self.current == FREE:
            return
        code = self._code()
        if not code.strip():
            self.app.set_status("Nothing to check.", BG_INFO)
            return
        e = px.BY_ID[self.current]
        passed, msg, text = px.grade(e, code)
        set_text(self.output, text)
        if passed:
            self.app.progress["solved"].add(e["ledger"])
            self.tree.item(f"py{e['id']}", text=self._label(e))
            self.title_var.set(f"{e['id']}. {e['title']}   ({e['tier']})  [solved]")
            self.refresh_progress()
            self.stash()
            self.app.save_progress()
            if e.get("note"):
                msg = f"{msg}   {e['note']}"
        self.app.set_status(msg, BG_OK if passed else BG_BAD)

    def show_solution(self):
        if self.current == FREE:
            return
        if not messagebox.askyesno(
            "Show solution",
            "This replaces your editor contents with the reference answer.\n\nReveal it?",
        ):
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", px.BY_ID[self.current]["solution"])
        self.app.set_status("Reference solution shown -- it is one valid answer,"
                            " not the only one.", BG_INFO)

    def refresh_progress(self):
        live = {e["ledger"] for e in px.EXERCISES}
        done = len(live & set(self.app.progress["solved"]))
        self.progress_var.set(f"Solved {done} / {len(px.EXERCISES)}")
