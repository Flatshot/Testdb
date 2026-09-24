"""Run a learner's Python in a separate process and report what it did.

Two ways to run, matching the two kinds of Python question:

  run_program(code, stdin)          the code is a whole program; what it
                                    PRINTS is the answer
  run_function(code, func, cases)   the code defines a function; what it
                                    RETURNS for each case is the answer

Both start a fresh interpreter (the same one the GUI runs under) with
`-I`, so the learner's code sees no site-packages, no environment variables
and no current directory -- only the standard library. A wall-clock limit
kills an infinite loop, and output is capped so a runaway print cannot fill
memory. Nothing here can touch the practice database or the app's own state,
because the child process never imports either.

The function runner sends the code and the test cases to a small harness
(HARNESS below, passed on the command line) as JSON on stdin and reads JSON
back. Every result is reduced to a canonical form -- dicts and sets sorted,
floats rounded -- so that two answers that are the same VALUE compare equal
even where their repr() would not. The learner's own prints are captured and
returned separately, so a debugging print never corrupts the comparison.
"""

import json
import os
import re
import subprocess
import sys
import tempfile

TIME_LIMIT_SECONDS = 5
OUTPUT_CAP = 20_000      # characters of stdout or stderr kept per run
PROGRAM_NAME = "answer.py"

# Traceback lines from the harness itself are noise to a learner; only the
# frames inside their own file are shown. The harness compiles their code
# under PROGRAM_NAME so those frames can be told apart.
HARNESS = r'''
import io, json, math, sys, traceback

PROG = %r

def canon(v):
    """A form in which equal values are equal: order-free for dicts and
    sets, floats rounded, and the container TYPE kept, so a tuple returned
    where a list was asked for still shows up as different."""
    if isinstance(v, bool) or v is None or isinstance(v, (int, str)):
        return ["v", repr(v)]
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return ["v", repr(v)]
        return ["v", repr(round(v, 6))]
    if isinstance(v, list):
        return ["list", [canon(x) for x in v]]
    if isinstance(v, tuple):
        return ["tuple", [canon(x) for x in v]]
    if isinstance(v, (set, frozenset)):
        return ["set", sorted((canon(x) for x in v), key=repr)]
    if isinstance(v, dict):
        return ["dict", sorted(([canon(k), canon(x)] for k, x in v.items()),
                               key=repr)]
    return ["v", repr(v)]

def user_frames(exc):
    """The traceback with the harness's own frames removed."""
    tb = exc.__traceback__
    frames = traceback.extract_tb(tb)
    mine = [f for f in frames if f.filename == PROG]
    out = traceback.format_list(mine) if mine else []
    out += traceback.format_exception_only(type(exc), exc)
    return "".join(out).rstrip()

req = json.load(sys.stdin)
real_stdout = sys.stdout
buf = io.StringIO()
sys.stdout = buf
ns = {"__name__": "__main__"}
reply = {"define_error": None, "results": []}
try:
    exec(compile(req["code"], PROG, "exec"), ns)
except BaseException as exc:
    reply["define_error"] = user_frames(exc)
else:
    fn = ns.get(req["func"])
    if not callable(fn):
        reply["define_error"] = "no function named %%s() is defined" %% req["func"]
    else:
        for args in req["cases"]:
            call = "%%s(%%s)" %% (req["func"], ", ".join(repr(a) for a in args))
            try:
                # A fresh copy of each argument, so a function that mutates
                # its input cannot leak that into the next case.
                r = fn(*json.loads(json.dumps(args)))
            except BaseException as exc:
                reply["results"].append({"call": call, "error": user_frames(exc)})
            else:
                reply["results"].append({"call": call, "repr": repr(r),
                                         "canon": canon(r)})
sys.stdout = real_stdout
reply["stdout"] = buf.getvalue()
json.dump(reply, real_stdout)
''' % PROGRAM_NAME


def _env():
    """A minimal, deterministic environment for the child.

    PYTHONHASHSEED pins set and dict-of-str iteration order, so the learner's
    run and the reference run cannot differ by hash randomisation alone.
    """
    return {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        # Windows needs these to start a process at all.
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "TEMP": os.environ.get("TEMP", ""),
    }


def _cap(text):
    if len(text) > OUTPUT_CAP:
        return text[:OUTPUT_CAP] + f"\n... output cut at {OUTPUT_CAP:,} characters"
    return text


def _run(argv, stdin_text, cwd):
    """(stdout, stderr, timed_out) for one child process."""
    try:
        proc = subprocess.run(
            argv, input=stdin_text, capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=cwd, env=_env(),
            timeout=TIME_LIMIT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", "replace")
        return _cap(out), _cap(err), True
    return _cap(proc.stdout), _cap(proc.stderr), False


def run_program(code, stdin_text=""):
    """Run `code` as a program. Returns a dict:

      stdout      what it printed
      stderr      any traceback, with the temp-file path replaced by
                  PROGRAM_NAME so the learner sees "answer.py, line 3"
      timed_out   True if it was killed at the time limit
      ok          True if it finished with no traceback
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, PROGRAM_NAME)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(code)
        out, err, timed_out = _run([sys.executable, "-I", PROGRAM_NAME],
                                   stdin_text, tmp)
    # The traceback names the temp file by its full path -- and on macOS by
    # its /private/... realpath, which is not the string we wrote -- so the
    # whole path is matched, not just the directory we know about.
    err = re.sub(r'"[^"\n]*' + re.escape(PROGRAM_NAME) + '"',
                 '"' + PROGRAM_NAME + '"', err)
    if timed_out:
        err = (err + "\n" if err else "") + (
            f"stopped after {TIME_LIMIT_SECONDS}s -- is there a loop that"
            f" never ends, or an input() with nothing to read?")
    return {"stdout": out, "stderr": err.strip(), "timed_out": timed_out,
            "ok": not timed_out and not err.strip()}


def run_function(code, func, cases):
    """Define `func` from `code`, call it once per case. Returns a dict:

      define_error  a traceback if the code itself failed to run, or a
                    message if it ran but defined no such function
      results       one per case: {"call": "f(1, 2)", "repr": "3",
                    "canon": [...]} or {"call": ..., "error": traceback}
      stdout        anything the code printed while defining or running
      timed_out     True if killed at the time limit
    """
    req = json.dumps({"code": code, "func": func, "cases": [list(c) for c in cases]})
    with tempfile.TemporaryDirectory() as tmp:
        out, err, timed_out = _run([sys.executable, "-I", "-c", HARNESS], req, tmp)
    if timed_out:
        return {"define_error": (f"stopped after {TIME_LIMIT_SECONDS}s -- is"
                                 f" there a loop that never ends?"),
                "results": [], "stdout": out, "timed_out": True}
    try:
        reply = json.loads(out[out.rindex("{\"define_error\""):])
    except (ValueError, json.JSONDecodeError):
        # The harness itself died -- a MemoryError or a sys.exit() in the
        # learner's code. Whatever it managed to say is the best diagnosis.
        return {"define_error": (err.strip() or out.strip()
                                 or "the program stopped before it could report"),
                "results": [], "stdout": "", "timed_out": False}
    reply["timed_out"] = False
    if err.strip():
        reply["stdout"] = reply.get("stdout", "") + "\n" + err.strip()
    return reply
