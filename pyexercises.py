"""Python practice exercises: fifteen tiny functions, one tool each.

The fifteenth Python set, one-tool functions again: every question asks
for a function of one or two lines that returns a value, built around one
named tool no earlier set used -- the + format spec, lstrip() with an
argument, textwrap.shorten(), !r in an f-string, math.isqrt(),
int.bit_length(), math.dist(), pow() with a modulus, itertools.accumulate(),
heapq.nlargest(), operator.itemgetter(), collections.Counter(), sorted()
with key=d.get, next(iter()) and sum() over values(). The title names the
tool, so the tree on the left reads like a list of tools.

Two kinds of question, told apart by `kind`:

  "program"   the editor holds a whole program, graded on what it prints.
              Not used in this set.
  "function"  the editor defines a function named `func`. Run calls it once
              per case in `cases` and shows each call and its result; Check
              compares each result with the reference function's. Values
              are compared, not their printed form -- a dict in another
              order is the same dict -- but the container type counts, so a
              tuple is not a list, and 0 is not False.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py).
"""

import pyrun

EXERCISES = [
    # ============================================================== 1 Strings
    dict(
        id=1, ledger="P221", concept="PY3 sign spec", tier="1 - Strings",
        title="f'{n:+}': always show the sign", kind="function",
        func="signed",
        cases=[(5,), (-3,), (0,), (2.5,)],
        prompt=(
            "Write a function `signed(n)` that returns the number as a"
            " string with its sign always shown -- '+5' as well as '-3'"
            " -- using the + format spec in an f-string:\n\n"
            "  signed(5) -> \"+5\"\n\n"
            "Return: the string."
        ),
        solution="def signed(n):\n    return f\"{n:+}\"\n",
        trap="def signed(n):\n    return str(n)\n",
        note="The + in a format spec asks for a sign on positive numbers"
             " too; str() and the default spec show only the minus. Zero"
             " gets a plus. It combines with the rest -- {n:+.2f} for a"
             " signed amount to two decimals.",
    ),
    dict(
        id=2, ledger="P222", concept="PY3 lstrip chars", tier="1 - Strings",
        title="lstrip(chars): leading zeros off", kind="function",
        func="without_leading_zeros",
        cases=[("0042",), ("100",), ("000",), ("7",)],
        prompt=(
            "Write a function `without_leading_zeros(s)` that returns s"
            " with any zeros removed from its LEFT end only -- the zeros"
            " inside or at the end stay -- using lstrip() with '0':\n\n"
            "  without_leading_zeros(\"0042\") -> \"42\"\n"
            "  without_leading_zeros(\"100\") -> \"100\"\n\n"
            "Return: the new string."
        ),
        solution="def without_leading_zeros(s):\n    return s.lstrip(\"0\")\n",
        trap="def without_leading_zeros(s):\n    return s.strip(\"0\")\n",
        note="lstrip() works on the left end only; strip() does both"
             " ends, so '100' loses its trailing zeros and becomes '1'."
             " A string that is all zeros strips to '' -- there is no"
             " zero left to keep -- which is what the question asked for.",
    ),
    dict(
        id=3, ledger="P223", concept="PY3 textwrap shorten", tier="1 - Strings",
        title="textwrap.shorten(): cut at a word, with a marker", kind="function",
        func="shortened",
        cases=[("The quick brown fox jumps over the lazy dog", 20), ("short", 10),
               ("one two three four", 13)],
        prompt=(
            "Write a function `shortened(text, width)` that returns the"
            " text cut to at most width characters at a WORD boundary,"
            " ending in ' [...]' when something was cut, using"
            " textwrap.shorten(). Text that already fits is returned as it"
            " is. Remember the import.\n\n"
            "  shortened(\"one two three four\", 13) -> \"one two [...]\"\n\n"
            "Return: the string."
        ),
        solution=("import textwrap\n\n"
                  "def shortened(text, width):\n"
                  "    return textwrap.shorten(text, width)\n"),
        trap="def shortened(text, width):\n    return text[:width]\n",
        note="Slicing cuts in the middle of a word and gives no sign that"
             " anything is missing. shorten() breaks at a space and"
             " appends its placeholder, keeping the whole result within"
             " width. It also collapses runs of whitespace, as the rest"
             " of textwrap does.",
    ),
    dict(
        id=4, ledger="P224", concept="PY3 repr spec", tier="1 - Strings",
        title="f'{s!r}': the value as Python would write it", kind="function",
        func="quoted",
        cases=[("Leeds",), ("",), ("it's",), ("a b",)],
        prompt=(
            "Write a function `quoted(s)` that returns s wrapped in the"
            " quotes Python itself would print it with -- repr form --"
            " using !r inside an f-string:\n\n"
            "  quoted(\"Leeds\") -> \"'Leeds'\"\n\n"
            "Return: the string."
        ),
        solution="def quoted(s):\n    return f\"{s!r}\"\n",
        trap="def quoted(s):\n    return f\"{s}\"\n",
        note="!r asks for repr() of the value instead of str(): for a"
             " string that means quotes around it, with the quote style"
             " chosen so a string containing an apostrophe comes out in"
             " double quotes. Without !r an f-string shows the bare text."
             " !r is what makes a debugging message say which value was"
             " a string.",
    ),
    # ============================================================== 2 Numbers
    dict(
        id=5, ledger="P225", concept="PY3 math isqrt", tier="2 - Numbers",
        title="math.isqrt(): the whole-number square root", kind="function",
        func="whole_root",
        cases=[(16,), (17,), (0,), (1000000,)],
        prompt=(
            "Write a function `whole_root(n)` that returns the largest"
            " whole number whose square is at most n, as an int, using"
            " math.isqrt(). Remember the import.\n\n"
            "  whole_root(17) -> 4\n\n"
            "Return: an integer."
        ),
        solution=("import math\n\n"
                  "def whole_root(n):\n"
                  "    return math.isqrt(n)\n"),
        trap="def whole_root(n):\n    return n ** 0.5\n",
        note="n ** 0.5 is a FLOAT -- 4.123 for 17, and 4.0 rather than 4"
             " for 16 -- and for very large n it is not even exact."
             " math.isqrt() works in integers throughout and returns an"
             " int, rounded down.",
    ),
    dict(
        id=6, ledger="P226", concept="PY3 bit_length", tier="2 - Numbers",
        title="bit_length(): how many binary digits", kind="function",
        func="bits_needed",
        cases=[(0,), (1,), (255,), (256,)],
        prompt=(
            "Write a function `bits_needed(n)` that returns how many"
            " binary digits a non-negative integer needs -- 0 for zero,"
            " 8 for 255, 9 for 256 -- using the int method"
            " bit_length():\n\n"
            "  bits_needed(255) -> 8\n\n"
            "Return: an integer."
        ),
        solution="def bits_needed(n):\n    return n.bit_length()\n",
        trap="def bits_needed(n):\n    return len(bin(n))\n",
        note="bit_length() is a method every int has, and it answers"
             " without building a string. len(bin(n)) counts the '0b'"
             " prefix as two extra digits, and says zero needs three.",
    ),
    dict(
        id=7, ledger="P227", concept="PY3 math dist", tier="2 - Numbers",
        title="math.dist(): distance between two points", kind="function",
        func="distance_between",
        cases=[((0, 0), (3, 4)), ((1, 1), (1, 1)), ((2, 3), (5, 7)), ((-1, 0), (1, 0))],
        prompt=(
            "Write a function `distance_between(p, q)` that returns the"
            " straight-line distance between two points given as (x, y)"
            " tuples, using math.dist(). Remember the import.\n\n"
            "  distance_between((0, 0), (3, 4)) -> 5.0\n\n"
            "Return: a float."
        ),
        solution=("import math\n\n"
                  "def distance_between(p, q):\n"
                  "    return math.dist(p, q)\n"),
        trap=("def distance_between(p, q):\n"
              "    return abs(p[0] - q[0]) + abs(p[1] - q[1])\n"),
        note="math.dist() takes two points of any dimension and returns"
             " the Euclidean distance -- hypot of the differences, done"
             " for you. Adding the two differences is the taxi-cab"
             " distance, which is longer whenever the points are not in"
             " line.",
    ),
    dict(
        id=8, ledger="P228", concept="PY3 pow mod", tier="2 - Numbers",
        title="pow(b, e, m): a power, reduced as it goes", kind="function",
        func="last_two_digits",
        cases=[(7, 2), (2, 10), (3, 0), (12, 3)],
        prompt=(
            "Write a function `last_two_digits(b, e)` that returns the"
            " last two digits of b to the power e -- the remainder on"
            " division by 100 -- using the three-argument form of"
            " pow():\n\n"
            "  last_two_digits(2, 10) -> 24\n\n"
            "Return: an integer."
        ),
        solution="def last_two_digits(b, e):\n    return pow(b, e, 100)\n",
        trap="def last_two_digits(b, e):\n    return pow(b, e) % 10\n",
        note="pow(b, e, m) computes b ** e modulo m without ever forming"
             " the full power, which matters when e is in the thousands."
             " The trap takes the remainder by 10, which is the last ONE"
             " digit. Anything to the power 0 is 1, so the last two digits"
             " are 01 -- the integer 1.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=9, ledger="P229", concept="PY3 accumulate", tier="3 - Lists",
        title="itertools.accumulate(): running totals", kind="function",
        func="running_total",
        cases=[([1, 2, 3],), ([],), ([5],), ([2, -2, 2],)],
        prompt=(
            "Write a function `running_total(values)` that returns a list"
            " where each item is the sum of the values up to and including"
            " that position, using list() over itertools.accumulate()."
            " Remember the import.\n\n"
            "  running_total([1, 2, 3]) -> [1, 3, 6]\n\n"
            "Return: the new list."
        ),
        solution=("import itertools\n\n"
                  "def running_total(values):\n"
                  "    return list(itertools.accumulate(values))\n"),
        trap="def running_total(values):\n    return list(values)\n",
        note="accumulate() yields the running sum, one value per input,"
             " and it is SQL's SUM() OVER (ORDER BY ...) in Python. A"
             " function can be passed to accumulate differently -- max"
             " for a running maximum, for instance. The empty list"
             " accumulates to an empty list.",
    ),
    dict(
        id=10, ledger="P230", concept="PY3 heapq nlargest", tier="3 - Lists",
        title="heapq.nlargest(): the top three", kind="function",
        func="top_three",
        cases=[([5, 1, 9, 3, 7],), ([1, 2],), ([],), ([4, 4, 4, 4],)],
        prompt=(
            "Write a function `top_three(values)` that returns the three"
            " largest values, largest first -- fewer when the list is"
            " shorter -- using heapq.nlargest(). Remember the import.\n\n"
            "  top_three([5, 1, 9, 3, 7]) -> [9, 7, 5]\n\n"
            "Return: the list."
        ),
        solution=("import heapq\n\n"
                  "def top_three(values):\n"
                  "    return heapq.nlargest(3, values)\n"),
        trap="def top_three(values):\n    return sorted(values)[:3]\n",
        note="sorted() ascending then [:3] is the three SMALLEST; the top"
             " three need reverse=True, or [-3:] reversed. nlargest(n,"
             " values) says what it means, returns largest first, and"
             " does not sort the whole list to find them. nsmallest is"
             " its twin.",
    ),
    dict(
        id=11, ledger="P231", concept="PY3 itemgetter", tier="3 - Lists",
        title="itemgetter(): sort pairs by their second item", kind="function",
        func="by_second",
        cases=[([("a", 3), ("b", 1), ("c", 2)],), ([],), ([("x", 0)],),
               ([("p", 2), ("q", 2), ("r", 1)],)],
        prompt=(
            "Write a function `by_second(pairs)` that returns the list of"
            " (name, number) pairs sorted by the NUMBER, using sorted()"
            " with key=itemgetter(1) from the operator module. Remember"
            " the import.\n\n"
            "  by_second([(\"a\", 3), (\"b\", 1), (\"c\", 2)]) ->"
            " [(\"b\", 1), (\"c\", 2), (\"a\", 3)]\n\n"
            "Return: the new list."
        ),
        solution=("from operator import itemgetter\n\n"
                  "def by_second(pairs):\n"
                  "    return sorted(pairs, key=itemgetter(1))\n"),
        trap="def by_second(pairs):\n    return sorted(pairs)\n",
        note="Plain sorted() compares tuples item by item, so it sorts by"
             " the name first. itemgetter(1) is a ready-made key function"
             " that picks item 1 -- the same as key=lambda p: p[1], a"
             " little faster and with a name that says what it does."
             " Equal numbers keep their original order.",
    ),
    dict(
        id=12, ledger="P232", concept="PY3 Counter", tier="3 - Lists",
        title="Counter(): how many of each", kind="function",
        func="tally",
        cases=[(["a", "b", "a"],), ([],), ([1, 1, 1],), (["LS1", "BD3", "LS1", "WF1"],)],
        prompt=(
            "Write a function `tally(values)` that returns a dictionary"
            " mapping each value to how many times it appears, using"
            " collections.Counter(). Remember the import.\n\n"
            "  tally([\"a\", \"b\", \"a\"]) -> {\"a\": 2, \"b\": 1}\n\n"
            "Return: the dictionary."
        ),
        solution=("from collections import Counter\n\n"
                  "def tally(values):\n"
                  "    return Counter(values)\n"),
        trap="def tally(values):\n    return dict.fromkeys(values, 1)\n",
        note="Counter is a dict subclass that counts for you -- the"
             " counting loop with get(key, 0) + 1 from the earlier sets,"
             " in one call -- and it compares equal to a plain dict with"
             " the same counts. fromkeys(values, 1) gives every value a"
             " count of 1 however often it appears.",
    ),
    # ========================================================= 4 Dictionaries
    dict(
        id=13, ledger="P233", concept="PY3 sorted key get", tier="4 - Dictionaries",
        title="sorted(d, key=d.get): keys in order of their values", kind="function",
        func="keys_by_value",
        cases=[({"a": 3, "b": 1, "c": 2},), ({},), ({"x": 1},), ({"p": 2, "q": 2, "r": 1},)],
        prompt=(
            "Write a function `keys_by_value(d)` that returns the"
            " dictionary's keys as a list ordered by their VALUES,"
            " smallest value first, using sorted() over the dict with"
            " key=d.get:\n\n"
            "  keys_by_value({\"a\": 3, \"b\": 1, \"c\": 2}) -> [\"b\","
            " \"c\", \"a\"]\n\n"
            "Return: the list of keys."
        ),
        solution="def keys_by_value(d):\n    return sorted(d, key=d.get)\n",
        trap="def keys_by_value(d):\n    return sorted(d)\n",
        note="Iterating a dict gives its keys, and d.get is a function"
             " from key to value -- so key=d.get sorts the keys by what"
             " they map to. sorted(d) alone sorts the keys by themselves,"
             " alphabetically. This is the idiom behind max(d, key=d.get)"
             " from an earlier set.",
    ),
    dict(
        id=14, ledger="P234", concept="PY3 next iter", tier="4 - Dictionaries",
        title="next(iter(d)): the first key", kind="function",
        func="first_key",
        cases=[({"a": 1, "b": 2},), ({"z": 0},), ({3: "x", 1: "y"},)],
        prompt=(
            "Write a function `first_key(d)` that returns the first key"
            " of a non-empty dictionary -- the one inserted first --"
            " using next() over iter():\n\n"
            "  first_key({\"a\": 1, \"b\": 2}) -> \"a\"\n\n"
            "Return: the key."
        ),
        solution="def first_key(d):\n    return next(iter(d))\n",
        trap="def first_key(d):\n    return d[0]\n",
        note="d[0] looks up the KEY 0, which is a KeyError unless the"
             " dict happens to have one -- dictionaries are not"
             " positional. iter(d) walks the keys in insertion order and"
             " next() takes the first, without building a list of all of"
             " them. next(iter(d), None) is the safe form for an empty"
             " dict.",
    ),
    dict(
        id=15, ledger="P235", concept="PY3 sum values", tier="4 - Dictionaries",
        title="sum(d.values()): the total of a tally", kind="function",
        func="total_of",
        cases=[({"a": 1, "b": 2},), ({},), ({"x": 2.5, "y": 0.5},), ({"only": 7},)],
        prompt=(
            "Write a function `total_of(d)` that returns the sum of all"
            " the dictionary's values, using sum() over values():\n\n"
            "  total_of({\"a\": 1, \"b\": 2}) -> 3\n\n"
            "Return: the total."
        ),
        solution="def total_of(d):\n    return sum(d.values())\n",
        trap="def total_of(d):\n    return sum(d)\n",
        note="sum(d) iterates the KEYS, which for string keys is a"
             " TypeError -- strings do not add to 0 -- and for numeric"
             " keys is the wrong number quietly. values() is the view of"
             " what the keys map to, and sum() of an empty view is 0.",
    ),
]

BY_ID = {e["id"]: e for e in EXERCISES}
TIERS = list(dict.fromkeys(e["tier"] for e in EXERCISES))


def is_program(exercise):
    return exercise["kind"] == "program"


def run(exercise, code):
    """Run the learner's code the way the question needs, and return the
    raw pyrun result."""
    if is_program(exercise):
        return pyrun.run_program(code, exercise.get("stdin", ""))
    return pyrun.run_function(code, exercise["func"], exercise["cases"])


def render(exercise, result):
    """The text for the output pane after a Run."""
    if is_program(exercise):
        text = result["stdout"]
        if result["stderr"]:
            text += ("\n" if text and not text.endswith("\n") else "") + result["stderr"]
        return text or "(nothing printed)"
    parts = []
    if result.get("stdout", "").strip():
        parts.append(result["stdout"].rstrip() + "\n")
    if result["define_error"]:
        parts.append(result["define_error"])
        return "\n".join(parts)
    parts.append("Test calls:")
    for r in result["results"]:
        if "error" in r:
            parts.append(f"  {r['call']}\n    raised: {r['error'].splitlines()[-1]}")
        else:
            parts.append(f"  {r['call']} -> {r['repr']}")
    return "\n".join(parts)


def _lines(text):
    """Output as a list of lines, trailing spaces and blank lines dropped."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def _short(s, n=60):
    return s if len(s) <= n else s[:n - 3] + "..."


def grade(exercise, code):
    """(passed, message, output_text): run the learner's code and the
    reference the same way, and compare."""
    got = run(exercise, code)
    text = render(exercise, got)
    if got.get("timed_out"):
        return False, (got.get("stderr") or got.get("define_error")), text

    if is_program(exercise):
        if got["stderr"]:
            return False, "Your program raised an error -- see the output pane.", text
        want = pyrun.run_program(exercise["solution"], exercise.get("stdin", ""))
        g, w = _lines(got["stdout"]), _lines(want["stdout"])
        if g == w:
            return True, f"Correct - {len(w)} line(s) matched.", text
        if not g:
            return False, f"Your program printed nothing; expected {len(w)} line(s).", text
        if len(g) != len(w):
            return False, (f"Wrong number of lines: you printed {len(g)},"
                           f" expected {len(w)}."), text
        for i, (a, b) in enumerate(zip(g, w), 1):
            if a != b:
                return False, (f"Line {i} differs.\n  Expected: {_short(b)!r}"
                               f"\n  Printed:  {_short(a)!r}"), text
        return False, "Output differs.", text

    if got["define_error"]:
        return False, got["define_error"].splitlines()[-1], text
    want = pyrun.run_function(exercise["solution"], exercise["func"], exercise["cases"])
    if want["define_error"]:
        return False, f"reference solution failed: {want['define_error']}", text
    failed = 0
    first = None
    for g, w in zip(got["results"], want["results"]):
        if "error" in g:
            failed += 1
            first = first or (f"{g['call']} raised {g['error'].splitlines()[-1]};"
                              f" expected {w['repr']}")
        elif g["canon"] != w["canon"]:
            failed += 1
            first = first or (f"{g['call']} returned {_short(g['repr'])},"
                              f" expected {_short(w['repr'])}")
    if not failed:
        return True, f"Correct - all {len(want['results'])} test call(s) matched.", text
    return False, (f"{failed} of {len(want['results'])} test call(s) wrong."
                   f"\n  {first}"), text
