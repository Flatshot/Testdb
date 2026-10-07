"""Python practice exercises: fifteen tiny functions, one tool each.

The tenth Python set, the third of one-tool functions in a row: every
question asks for a function of one or two lines that returns a value,
built around one named tool no earlier set used -- rstrip() with an
argument, swapcase(), removeprefix(), rfind(), casefold(), math.sqrt(),
math.floor(), the :, format spec, statistics.median(), set & and set -,
reversed(), sorted() over a set, dict.pop() with a default and
dict.fromkeys(). The title names the tool, so the tree on the left reads
like a list of tools.

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
        id=1, ledger="P146", concept="PY3 rstrip chars", tier="1 - Strings",
        title="rstrip(chars): trailing punctuation off", kind="function",
        func="no_trailing_punctuation",
        cases=[("Hello!",), ("Wait...",), ("plain",), ("Really?!?",)],
        prompt=(
            "Write a function `no_trailing_punctuation(s)` that returns s"
            " with any run of '.', ',', '!' or '?' removed from its END"
            " only, using rstrip() with those characters as its"
            " argument:\n\n"
            "  no_trailing_punctuation(\"Wait...\") -> \"Wait\"\n\n"
            "Return: the new string."
        ),
        solution="def no_trailing_punctuation(s):\n    return s.rstrip(\".,!?\")\n",
        trap="def no_trailing_punctuation(s):\n    return s.rstrip()\n",
        note="rstrip() with no argument removes whitespace only. Given a"
             " string of characters it removes any of THOSE from the right"
             " end, as a set, for as long as it keeps finding them -- so"
             " '?!?' goes in one call. The argument is not a suffix: it"
             " is the characters to strip.",
    ),
    dict(
        id=2, ledger="P147", concept="PY3 swapcase", tier="1 - Strings",
        title="swapcase(): upper for lower and back", kind="function",
        func="flip_case",
        cases=[("Hello World",), ("LS15",), ("",), ("aBc",)],
        prompt=(
            "Write a function `flip_case(s)` that returns s with every"
            " upper-case letter made lower and every lower-case letter"
            " made upper, using swapcase():\n\n"
            "  flip_case(\"Hello World\") -> \"hELLO wORLD\"\n\n"
            "Return: the new string."
        ),
        solution="def flip_case(s):\n    return s.swapcase()\n",
        trap="def flip_case(s):\n    return s.upper()\n",
        note="swapcase() flips each letter's case and leaves digits and"
             " spaces alone; upper() only goes one way. A string with no"
             " letters comes back unchanged from both, which is why"
             " 'LS15' alone would not tell them apart.",
    ),
    dict(
        id=3, ledger="P148", concept="PY3 removeprefix", tier="1 - Strings",
        title="removeprefix(): a title off the front", kind="function",
        func="without_title",
        cases=[("Dr Draper",), ("Dr Adams",), ("Rosa Khatri",), ("Drake Dr Ho",)],
        prompt=(
            "Write a function `without_title(name)` that returns name"
            " with a leading 'Dr ' removed -- and the name unchanged when"
            " it does not start with that -- using removeprefix():\n\n"
            "  without_title(\"Dr Draper\") -> \"Draper\"\n\n"
            "Return: the new string."
        ),
        solution="def without_title(name):\n    return name.removeprefix(\"Dr \")\n",
        trap="def without_title(name):\n    return name.lstrip(\"Dr \")\n",
        note="removeprefix() takes a PREFIX: the whole 'Dr ' at the start,"
             " once, or nothing. lstrip('Dr ') takes a SET of characters"
             " -- D, r and space -- and strips them from the left for as"
             " long as it finds any, so 'Dr Draper' loses its 'Dr' as"
             " well and 'Drake Dr Ho' loses its first letters.",
    ),
    dict(
        id=4, ledger="P149", concept="PY3 rfind", tier="1 - Strings",
        title="rfind(): the last space", kind="function",
        func="last_space",
        cases=[("Aisha Ekwueme",), ("Bartholomew van Hollingsworth",), ("Zara",), ("",)],
        prompt=(
            "Write a function `last_space(s)` that returns the position"
            " of the LAST space in s, or -1 when there is none, using"
            " rfind():\n\n"
            "  last_space(\"Bartholomew van Hollingsworth\") -> 15\n\n"
            "Return: an integer."
        ),
        solution="def last_space(s):\n    return s.rfind(\" \")\n",
        trap="def last_space(s):\n    return s.find(\" \")\n",
        note="find() searches from the left and reports the FIRST match;"
             " rfind() searches from the right and reports the last. Both"
             " give -1 for no match, where index() and rindex() would"
             " raise instead. Positions count from 0.",
    ),
    dict(
        id=5, ledger="P150", concept="PY3 casefold", tier="1 - Strings",
        title="casefold(): the same name, whatever the case", kind="function",
        func="same_name",
        cases=[("Leeds", "LEEDS"), ("Leeds", "Leeds"), ("Leeds", "Wakefield"), ("", "")],
        prompt=(
            "Write a function `same_name(a, b)` that returns True when"
            " the two strings are the same ignoring case, using"
            " casefold() on both before comparing:\n\n"
            "  same_name(\"Leeds\", \"LEEDS\") -> True\n\n"
            "Return: True or False."
        ),
        solution="def same_name(a, b):\n    return a.casefold() == b.casefold()\n",
        trap="def same_name(a, b):\n    return a == b\n",
        note="== compares the characters exactly, and 'L' is not 'l'."
             " casefold() is lower() made for comparison: it handles the"
             " letters that lower() gets wrong, like the German sharp s,"
             " and is the method the documentation recommends for"
             " case-insensitive matching.",
    ),
    # ============================================================== 2 Numbers
    dict(
        id=6, ledger="P151", concept="PY3 math sqrt", tier="2 - Numbers",
        title="math.sqrt(): the diagonal of a rectangle", kind="function",
        func="diagonal",
        cases=[(3, 4), (5, 12), (1, 1), (0, 7)],
        prompt=(
            "Write a function `diagonal(w, h)` that returns the length of"
            " the diagonal of a w by h rectangle -- the square root of"
            " w*w + h*h -- using math.sqrt(). Remember the import.\n\n"
            "  diagonal(3, 4) -> 5.0\n\n"
            "Return: a float."
        ),
        solution=("import math\n\n"
                  "def diagonal(w, h):\n"
                  "    return math.sqrt(w * w + h * h)\n"),
        trap=("import math\n\n"
              "def diagonal(w, h):\n"
              "    return math.sqrt(w * w) + math.sqrt(h * h)\n"),
        note="The root of a sum is not the sum of the roots: sqrt(9 + 16)"
             " is 5, sqrt(9) + sqrt(16) is 7 -- which is walking along"
             " two sides instead of cutting across. math.sqrt() always"
             " returns a float, so 5.0 rather than 5.",
    ),
    dict(
        id=7, ledger="P152", concept="PY3 math floor", tier="2 - Numbers",
        title="math.floor(): rounding down, below zero too", kind="function",
        func="round_down",
        cases=[(2.7,), (-2.5,), (4.0,), (-0.1,)],
        prompt=(
            "Write a function `round_down(x)` that returns the largest"
            " whole number that is not above x, as an int, using"
            " math.floor() -- so -2.5 goes DOWN to -3:\n\n"
            "  round_down(-2.5) -> -3\n\n"
            "Return: an integer."
        ),
        solution=("import math\n\n"
                  "def round_down(x):\n"
                  "    return math.floor(x)\n"),
        trap="def round_down(x):\n    return int(x)\n",
        note="int() truncates TOWARDS ZERO, so int(-2.5) is -2, which is"
             " above -2.5; math.floor() always goes down the number line,"
             " so -3. They agree for positive numbers, which is how the"
             " difference stays hidden until a negative one turns up.",
    ),
    dict(
        id=8, ledger="P153", concept="PY3 format comma", tier="2 - Numbers",
        title="f'{n:,}': thousands separators", kind="function",
        func="with_commas",
        cases=[(1234567,), (999,), (1000,), (0,)],
        prompt=(
            "Write a function `with_commas(n)` that returns the integer n"
            " as a string with a comma every three digits, using an"
            " f-string with the , format spec:\n\n"
            "  with_commas(1234567) -> \"1,234,567\"\n\n"
            "Return: the string."
        ),
        solution="def with_commas(n):\n    return f\"{n:,}\"\n",
        trap="def with_commas(n):\n    return str(n)\n",
        note="The part after the colon in {n:,} is a format spec, and a"
             " bare comma means 'group the thousands'. It combines with"
             " the others -- {x:,.2f} for money -- and does the right"
             " thing for numbers under a thousand, which get no comma.",
    ),
    dict(
        id=9, ledger="P154", concept="PY3 statistics median", tier="2 - Numbers",
        title="statistics.median(): the middle value", kind="function",
        func="middle",
        cases=[([1, 2, 10],), ([4, 1, 3, 2],), ([5],), ([7, 7, 100],)],
        prompt=(
            "Write a function `middle(values)` that returns the median of"
            " a non-empty list -- the middle value once sorted, or the"
            " mean of the two middle values when the count is even --"
            " using statistics.median(). Remember the import.\n\n"
            "  middle([1, 2, 10]) -> 2\n\n"
            "Return: the median."
        ),
        solution=("import statistics\n\n"
                  "def middle(values):\n"
                  "    return statistics.median(values)\n"),
        trap=("import statistics\n\n"
              "def middle(values):\n"
              "    return statistics.mean(values)\n"),
        note="The median is the value in the middle; the mean is the"
             " total divided by the count, and one large value drags it"
             " -- [7, 7, 100] has a median of 7 and a mean of 38. The"
             " statistics module has both, and median() sorts for you.",
    ),
    # ================================================================= 3 Sets
    dict(
        id=10, ledger="P155", concept="PY3 set intersection", tier="3 - Sets and sequences",
        title="&: what two lists have in common", kind="function",
        func="common",
        cases=[(["LS1", "LS9", "BD3"], ["BD3", "LS1", "WF1"]), ([1, 2], [3]),
               ([], [1]), ([1, 1, 2], [1])],
        prompt=(
            "Write a function `common(a, b)` that returns a SET of the"
            " values that appear in both lists, using set() on each and"
            " the & operator:\n\n"
            "  common([\"LS1\", \"LS9\", \"BD3\"], [\"BD3\", \"LS1\","
            " \"WF1\"]) -> {\"LS1\", \"BD3\"}\n\n"
            "Return: the set."
        ),
        solution="def common(a, b):\n    return set(a) & set(b)\n",
        trap="def common(a, b):\n    return set(a) | set(b)\n",
        note="& is intersection, the values in BOTH; | is union, the"
             " values in either. Sets have no order and no repeats, so"
             " [1, 1, 2] & [1] is {1}, and the empty set is a legitimate"
             " answer when nothing is shared.",
    ),
    dict(
        id=11, ledger="P156", concept="PY3 set difference", tier="3 - Sets and sequences",
        title="-: what is wanted but not held", kind="function",
        func="still_needed",
        cases=[(["pen", "ink", "paper"], ["ink"]), ([1, 2, 3], [1, 2, 3]),
               ([], [1]), (["a", "b"], ["c"])],
        prompt=(
            "Write a function `still_needed(wanted, have)` that returns a"
            " SET of the wanted values that are not in have, using set()"
            " on each and the - operator:\n\n"
            "  still_needed([\"pen\", \"ink\", \"paper\"], [\"ink\"])"
            " -> {\"pen\", \"paper\"}\n\n"
            "Return: the set."
        ),
        solution="def still_needed(wanted, have):\n    return set(wanted) - set(have)\n",
        trap="def still_needed(wanted, have):\n    return set(have) - set(wanted)\n",
        note="Set difference is not symmetric: a - b is what is in a and"
             " not in b. Written the other way round it is what you HAVE"
             " and did not want, which is a different question. This is"
             " SQL's EXCEPT, with the same rule about which side is which.",
    ),
    dict(
        id=12, ledger="P157", concept="PY3 reversed", tier="3 - Sets and sequences",
        title="reversed(): a reversed copy", kind="function",
        func="backwards_copy",
        cases=[([1, 2, 3],), ([],), (["a"],), ([3, 1, 2],)],
        prompt=(
            "Write a function `backwards_copy(values)` that returns a NEW"
            " list with the items in the opposite order, leaving the"
            " original alone, using list() over reversed():\n\n"
            "  backwards_copy([1, 2, 3]) -> [3, 2, 1]\n\n"
            "Return: the new list."
        ),
        solution="def backwards_copy(values):\n    return list(reversed(values))\n",
        trap="def backwards_copy(values):\n    return values.reverse()\n",
        note="reversed() hands back an iterator over the items from the"
             " end, and list() collects it into a new list. values."
             "reverse() turns the list round IN PLACE and returns None"
             " -- the caller's list is changed and the function returns"
             " nothing.",
    ),
    dict(
        id=13, ledger="P158", concept="PY3 sorted set", tier="3 - Sets and sequences",
        title="sorted(set()): the distinct values, in order", kind="function",
        func="distinct_sorted",
        cases=[(["LS9", "LS1", "LS9", "BD3"],), ([],), ([3, 3, 3],), ([2, 1],)],
        prompt=(
            "Write a function `distinct_sorted(values)` that returns a"
            " LIST of the different values in the list, each once, in"
            " ascending order, using sorted() over set():\n\n"
            "  distinct_sorted([\"LS9\", \"LS1\", \"LS9\", \"BD3\"]) ->"
            " [\"BD3\", \"LS1\", \"LS9\"]\n\n"
            "Return: the list."
        ),
        solution="def distinct_sorted(values):\n    return sorted(set(values))\n",
        trap="def distinct_sorted(values):\n    return sorted(values)\n",
        note="set() removes the repeats and sorted() puts what is left"
             " in order AND returns a list, which is why the answer is a"
             " list and not a set. sorted(values) alone keeps every"
             " repeat. SQL would say SELECT DISTINCT ... ORDER BY.",
    ),
    # ========================================================= 4 Dictionaries
    dict(
        id=14, ledger="P159", concept="PY3 dict pop default", tier="4 - Dictionaries",
        title="dict.pop(key, default): take a value out", kind="function",
        func="take",
        cases=[({"a": 1, "b": 2}, "a"), ({"a": 1}, "z"), ({}, "a"), ({"n": None}, "n")],
        prompt=(
            "Write a function `take(d, key)` that removes key from the"
            " dictionary and returns its value -- or returns None, with"
            " nothing removed, when the key is not there -- using pop()"
            " with a default:\n\n"
            "  take({\"a\": 1}, \"z\") -> None\n\n"
            "Return: the value, or None."
        ),
        solution="def take(d, key):\n    return d.pop(key, None)\n",
        trap="def take(d, key):\n    return d.pop(key)\n",
        note="pop(key) with no default raises KeyError for a missing"
             " key; pop(key, default) returns the default instead, and"
             " the dictionary is untouched. Unlike list.pop(), dict.pop()"
             " needs the key -- a dictionary has no 'last' item to take.",
    ),
    dict(
        id=15, ledger="P160", concept="PY3 dict fromkeys", tier="4 - Dictionaries",
        title="dict.fromkeys(): every key starting at zero", kind="function",
        func="zero_counts",
        cases=[(["good", "worn", "damaged"],), ([],), (["x"],), (["a", "a", "b"],)],
        prompt=(
            "Write a function `zero_counts(keys)` that returns a"
            " dictionary with every key in the list mapped to 0 -- a"
            " tally ready to be counted into -- using dict.fromkeys()"
            " with a value:\n\n"
            "  zero_counts([\"good\", \"worn\"]) -> {\"good\": 0,"
            " \"worn\": 0}\n\n"
            "Return: the dictionary."
        ),
        solution="def zero_counts(keys):\n    return dict.fromkeys(keys, 0)\n",
        trap="def zero_counts(keys):\n    return dict.fromkeys(keys)\n",
        note="dict.fromkeys(keys, value) builds a dictionary from a"
             " sequence of keys, all with the same value; with no second"
             " argument that value is None, which is not a count you can"
             " add 1 to. A repeated key appears once -- a dictionary"
             " cannot hold it twice.",
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
