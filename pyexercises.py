"""Python practice exercises: fifteen tiny functions, one tool each.

The ninth Python set, and the same shape as the eighth: every question
asks for a function of one or two lines that returns a value, built around
one named tool none of the earlier sets used -- capitalize(), zfill(),
isalpha(), partition(), splitlines(), the ** operator, min() with a
default, isinstance(), math.ceil(), any(), all(), len(set()), the [::2]
step slice, dict.update() and a dict comprehension. The title names the
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
        id=1, ledger="P131", concept="PY3 capitalize", tier="1 - Strings",
        title="capitalize(): one capital at the front", kind="function",
        func="sentence_case",
        cases=[("hello world",), ("hELLO wORLD",), ("",), ("ok",)],
        prompt=(
            "Write a function `sentence_case(s)` that returns s with its"
            " first character in upper case and EVERYTHING else in lower"
            " case, using capitalize():\n\n"
            "  sentence_case(\"hELLO wORLD\") -> \"Hello world\"\n\n"
            "Return: the new string."
        ),
        solution="def sentence_case(s):\n    return s.capitalize()\n",
        trap="def sentence_case(s):\n    return s.title()\n",
        note="capitalize() works on the whole string as one unit: first"
             " character up, the rest down. title() capitalizes every"
             " WORD, so 'hello world' becomes 'Hello World'. Both leave an"
             " empty string alone.",
    ),
    dict(
        id=2, ledger="P132", concept="PY3 zfill", tier="1 - Strings",
        title="zfill(): padding a number with zeros", kind="function",
        func="pad_id",
        cases=[(7, 4), (123, 4), (12345, 3), (0, 2)],
        prompt=(
            "Write a function `pad_id(n, width)` that returns the number n"
            " as a string of at least `width` characters, padded on the"
            " left with zeros, using str() and zfill():\n\n"
            "  pad_id(7, 4) -> \"0007\"\n\n"
            "A number already wider than width is returned as it is.\n\n"
            "Return: the string."
        ),
        solution="def pad_id(n, width):\n    return str(n).zfill(width)\n",
        trap="def pad_id(n, width):\n    return str(n).rjust(width)\n",
        note="zfill() is rjust() with zeros: it pads on the left to the"
             " width asked for and never cuts anything off, so 12345 at"
             " width 3 comes back whole. rjust(width) pads with spaces,"
             " which lines a column up but is not an id of '0007'.",
    ),
    dict(
        id=3, ledger="P133", concept="PY3 isalpha", tier="1 - Strings",
        title="isalpha(): letters and nothing else", kind="function",
        func="only_letters",
        cases=[("Leeds",), ("LS15",), ("",), ("Old Town",)],
        prompt=(
            "Write a function `only_letters(s)` that returns True when s"
            " is made of letters only -- no digits, spaces or punctuation"
            " -- and False otherwise, using isalpha():\n\n"
            "  only_letters(\"LS15\") -> False\n\n"
            "Return: True or False."
        ),
        solution="def only_letters(s):\n    return s.isalpha()\n",
        trap="def only_letters(s):\n    return s.isalnum()\n",
        note="isalpha() is true only when every character is a letter;"
             " isalnum() also accepts digits, so a postcode passes it."
             " Both are False for the empty string -- there is no"
             " character to be a letter -- and for 'Old Town', because a"
             " space is neither.",
    ),
    dict(
        id=4, ledger="P134", concept="PY3 partition", tier="1 - Strings",
        title="partition(): split at the first sign", kind="function",
        func="key_value",
        cases=[("town=Leeds",), ("eq=a=b",), ("novalue",), ("=x",)],
        prompt=(
            "Write a function `key_value(s)` that returns a tuple (key,"
            " value) from a setting written as 'key=value', splitting at"
            " the FIRST '=' only, using partition():\n\n"
            "  key_value(\"eq=a=b\") -> (\"eq\", \"a=b\")\n\n"
            "With no '=' at all the key is the whole string and the value"
            " is ''.\n\n"
            "Return: the tuple."
        ),
        solution=("def key_value(s):\n"
                  "    key, _, value = s.partition(\"=\")\n"
                  "    return (key, value)\n"),
        trap=("def key_value(s):\n"
              "    parts = s.split(\"=\")\n"
              "    return (parts[0], parts[1])\n"),
        note="partition() always returns three pieces -- before, the"
             " separator, after -- splitting at the first match, and"
             " gives two empty strings when the separator is absent, so"
             " it never fails. split('=') cuts at EVERY '=' and returns"
             " a one-element list when there is none, so parts[1] is an"
             " IndexError for 'novalue' and 'a' instead of 'a=b' for the"
             " second case.",
    ),
    dict(
        id=5, ledger="P135", concept="PY3 splitlines", tier="1 - Strings",
        title="splitlines(): how many lines", kind="function",
        func="line_count",
        cases=[("a\nb",), ("a\nb\n",), ("",), ("one",)],
        prompt=(
            "Write a function `line_count(text)` that returns how many"
            " lines text has, using splitlines(): a trailing newline does"
            " not start an extra line, and the empty string has no lines"
            " at all.\n\n"
            "  line_count(\"a\\nb\\n\") -> 2\n\n"
            "Return: an integer."
        ),
        solution="def line_count(text):\n    return len(text.splitlines())\n",
        trap="def line_count(text):\n    return text.count(\"\\n\") + 1\n",
        note="splitlines() breaks on every kind of line ending and does"
             " not make an empty last line out of a trailing newline, and"
             " gives [] for ''. Counting newlines and adding one says a"
             " file that ends properly has one line more than it does,"
             " and that the empty string has one line.",
    ),
    # ============================================================== 2 Numbers
    dict(
        id=6, ledger="P136", concept="PY3 power", tier="2 - Numbers",
        title="**: raising to a power", kind="function",
        func="cube",
        cases=[(2,), (3,), (1.5,), (-2,)],
        prompt=(
            "Write a function `cube(n)` that returns n to the power of 3,"
            " using the ** operator:\n\n"
            "  cube(3) -> 27\n\n"
            "Return: the number."
        ),
        solution="def cube(n):\n    return n ** 3\n",
        trap="def cube(n):\n    return n ^ 3\n",
        note="** is the power operator. ^ looks like one and is not: it"
             " is bitwise exclusive-or, so 3 ^ 3 is 0, 2 ^ 3 is 1, and a"
             " float raises a TypeError. Python has no caret power.",
    ),
    dict(
        id=7, ledger="P137", concept="PY3 min default", tier="2 - Numbers",
        title="min(default=): the smallest, or None", kind="function",
        func="lowest",
        cases=[([4, 2, 9],), ([],), ([7],), ([-1, -5],)],
        prompt=(
            "Write a function `lowest(values)` that returns the smallest"
            " value in the list, or None when the list is empty, using"
            " min() with its default= argument:\n\n"
            "  lowest([4, 2, 9]) -> 2\n"
            "  lowest([]) -> None\n\n"
            "Return: the smallest value, or None."
        ),
        solution="def lowest(values):\n    return min(values, default=None)\n",
        trap="def lowest(values):\n    return min(values)\n",
        note="min() of an empty list is a ValueError -- there is no"
             " smallest of nothing. The default= keyword names what to"
             " return instead, and only then; a one-element list still"
             " gives its element.",
    ),
    dict(
        id=8, ledger="P138", concept="PY3 isinstance", tier="2 - Numbers",
        title="isinstance(): is it a number?", kind="function",
        func="is_number",
        cases=[(3,), (2.5,), ("3",), ([1],)],
        prompt=(
            "Write a function `is_number(x)` that returns True when x is"
            " an int or a float and False for anything else, using"
            " isinstance() with a tuple of types:\n\n"
            "  is_number(2.5) -> True\n"
            "  is_number(\"3\") -> False\n\n"
            "Return: True or False."
        ),
        solution="def is_number(x):\n    return isinstance(x, (int, float))\n",
        trap="def is_number(x):\n    return type(x) == int\n",
        note="isinstance(x, (int, float)) is true for either type in the"
             " tuple. type(x) == int tests one exact type, so 2.5 is"
             " refused -- and the string '3' is refused by both, because"
             " looking like a number is not being one.",
    ),
    dict(
        id=9, ledger="P139", concept="PY3 math ceil", tier="2 - Numbers",
        title="math.ceil(): rounding up", kind="function",
        func="boxes_needed",
        cases=[(7, 3), (6, 3), (1, 10), (0, 4)],
        prompt=(
            "Write a function `boxes_needed(items, per_box)` that returns"
            " how many boxes hold all the items when each box takes"
            " per_box -- a part-filled box still counts -- using"
            " math.ceil() on the division. Remember the import.\n\n"
            "  boxes_needed(7, 3) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("import math\n\n"
                  "def boxes_needed(items, per_box):\n"
                  "    return math.ceil(items / per_box)\n"),
        trap=("def boxes_needed(items, per_box):\n"
              "    return round(items / per_box)\n"),
        note="math.ceil() always rounds UP to the next whole number and"
             " returns an int; round() goes to the nearest, so 7 / 3 ="
             " 2.33 becomes 2 and an item is left on the floor. The"
             " function lives in the math module, hence import math at"
             " the top.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=10, ledger="P140", concept="PY3 any", tier="3 - Lists",
        title="any(): is at least one true?", kind="function",
        func="has_negative",
        cases=[([1, -2, 3],), ([1, 2],), ([],), ([-1],)],
        prompt=(
            "Write a function `has_negative(values)` that returns True"
            " when at least one value in the list is below zero, using"
            " any() over a generator expression:\n\n"
            "  has_negative([1, -2, 3]) -> True\n\n"
            "Return: True or False."
        ),
        solution="def has_negative(values):\n    return any(v < 0 for v in values)\n",
        trap="def has_negative(values):\n    return all(v < 0 for v in values)\n",
        note="any() is True when at least one test passes, and False for"
             " an empty list -- nothing passed. all() is True only when"
             " every test passes, and True for an empty list -- nothing"
             " failed. The two are easy to swap and disagree on almost"
             " every input.",
    ),
    dict(
        id=11, ledger="P141", concept="PY3 all", tier="3 - Lists",
        title="all(): are they all true?", kind="function",
        func="all_passed",
        cases=[([50, 70, 65], 40), ([50, 30], 40), ([], 40), ([40], 40)],
        prompt=(
            "Write a function `all_passed(marks, pass_mark)` that returns"
            " True when every mark is at least pass_mark, using all() over"
            " a generator expression. An empty list passes -- nobody"
            " failed.\n\n"
            "  all_passed([50, 30], 40) -> False\n\n"
            "Return: True or False."
        ),
        solution="def all_passed(marks, pass_mark):\n    return all(m >= pass_mark for m in marks)\n",
        trap="def all_passed(marks, pass_mark):\n    return any(m >= pass_mark for m in marks)\n",
        note="all() asks whether every test passed; any() asks whether"
             " one did, so a class with a single pass would be reported"
             " as all passing. For the empty list all() is True by"
             " convention -- there is no mark that fails -- which is why"
             " the question says so.",
    ),
    dict(
        id=12, ledger="P142", concept="PY3 len set", tier="3 - Lists",
        title="len(set()): how many different values", kind="function",
        func="distinct_count",
        cases=[(["LS1", "LS1", "BD3"],), ([],), ([1, 1, 1],), (["a", "b"],)],
        prompt=(
            "Write a function `distinct_count(values)` that returns how"
            " many DIFFERENT values the list holds, using len() of a"
            " set():\n\n"
            "  distinct_count([\"LS1\", \"LS1\", \"BD3\"]) -> 2\n\n"
            "Return: an integer."
        ),
        solution="def distinct_count(values):\n    return len(set(values))\n",
        trap="def distinct_count(values):\n    return len(values)\n",
        note="A set keeps one of each value, so its length is the number"
             " of distinct values -- SQL's COUNT(DISTINCT ...). len() of"
             " the list counts the repeats as well.",
    ),
    dict(
        id=13, ledger="P143", concept="PY3 slice step", tier="3 - Lists",
        title="[::2]: every other item", kind="function",
        func="every_other",
        cases=[([1, 2, 3, 4, 5],), ([],), (["a", "b"],), ([9],)],
        prompt=(
            "Write a function `every_other(values)` that returns a new"
            " list of the items at positions 0, 2, 4, ... -- the first and"
            " then every second one -- using a slice with a step:\n\n"
            "  every_other([1, 2, 3, 4, 5]) -> [1, 3, 5]\n\n"
            "Return: the new list."
        ),
        solution="def every_other(values):\n    return values[::2]\n",
        trap="def every_other(values):\n    return values[1::2]\n",
        note="A slice has three parts, start:stop:step. [::2] starts at"
             " the beginning and takes every second item, so position 0"
             " is included; [1::2] starts at position 1 and gives the"
             " OTHER half. An empty list slices to an empty list.",
    ),
    # ========================================================= 4 Dictionaries
    dict(
        id=14, ledger="P144", concept="PY3 dict update", tier="4 - Dictionaries",
        title="dict.update(): one dictionary over another", kind="function",
        func="merged",
        cases=[({"a": 1}, {"b": 2}), ({"a": 1}, {"a": 5}), ({}, {}),
               ({"x": 1, "y": 2}, {"y": 3})],
        prompt=(
            "Write a function `merged(a, b)` that returns a NEW dictionary"
            " with everything from a and then everything from b, b"
            " winning where a key is in both, using update() on a copy of"
            " a. Neither argument is changed.\n\n"
            "  merged({\"x\": 1, \"y\": 2}, {\"y\": 3}) -> {\"x\": 1,"
            " \"y\": 3}\n\n"
            "Return: the new dictionary."
        ),
        solution=("def merged(a, b):\n"
                  "    out = dict(a)\n"
                  "    out.update(b)\n"
                  "    return out\n"),
        trap="def merged(a, b):\n    return a.update(b)\n",
        note="update() changes the dictionary it is called on and returns"
             " None, like list.sort() and append(): 'return a.update(b)'"
             " returns nothing and alters the caller's a. Copy first with"
             " dict(a), update the copy, return the copy.",
    ),
    dict(
        id=15, ledger="P145", concept="PY3 dict comprehension", tier="4 - Dictionaries",
        title="{k: v for ...}: a dictionary turned inside out", kind="function",
        func="invert",
        cases=[({"a": 1, "b": 2},), ({},), ({"x": "y"},), ({"only": 0},)],
        prompt=(
            "Write a function `invert(d)` that returns a new dictionary"
            " with d's values as keys and d's keys as values, using a"
            " dict comprehension over d.items():\n\n"
            "  invert({\"a\": 1, \"b\": 2}) -> {1: \"a\", 2: \"b\"}\n\n"
            "Return: the new dictionary."
        ),
        solution="def invert(d):\n    return {v: k for k, v in d.items()}\n",
        trap="def invert(d):\n    return {k: v for k, v in d.items()}\n",
        note="A dict comprehension is {key_expr: value_expr for ... in"
             " ...}; items() hands over (key, value) pairs, and writing"
             " them the other way round is the whole inversion. The trap"
             " copies the dictionary unchanged.",
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
