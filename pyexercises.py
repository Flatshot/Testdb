"""Python practice exercises: fifteen tiny functions, one tool each.

The thirteenth Python set, one-tool functions again: every question asks
for a function of one or two lines that returns a value, built around one
named tool no earlier set used -- center() with a fill, isupper(), the
format() method, ord(), the is None test, math.isclose(), float's
is_integer(), math.prod(), min() with key=abs, list.sort() in place,
extend(), map(), set.discard(), ^ on sets and | on dicts. The title names
the tool, so the tree on the left reads like a list of tools.

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
        id=1, ledger="P191", concept="PY3 center fill", tier="1 - Strings",
        title="center(width, '*'): a label in the middle", kind="function",
        func="banner",
        cases=[("Hi", 8), ("Odd", 8), ("Far too long", 5), ("", 4)],
        prompt=(
            "Write a function `banner(label, width)` that returns the"
            " label centred in a field of the given width, padded on"
            " both sides with '*', using center() with a fill"
            " character:\n\n"
            "  banner(\"Hi\", 8) -> \"***Hi***\"\n\n"
            "A label wider than width is returned unchanged.\n\n"
            "Return: the string."
        ),
        solution="def banner(label, width):\n    return label.center(width, \"*\")\n",
        trap="def banner(label, width):\n    return label.ljust(width, \"*\")\n",
        note="center() splits the padding between the two sides, giving"
             " the odd character to the right; ljust() puts it all on"
             " the right. Like its siblings it never truncates, and the"
             " fill character defaults to a space.",
    ),
    dict(
        id=2, ledger="P192", concept="PY3 isupper", tier="1 - Strings",
        title="isupper(): is it all capitals?", kind="function",
        func="is_shouting",
        cases=[("HELLO",), ("Hello",), ("123",), ("",), ("LS15",)],
        prompt=(
            "Write a function `is_shouting(s)` that returns True when"
            " every letter in s is upper case and there is at least one"
            " letter, using isupper():\n\n"
            "  is_shouting(\"LS15\") -> True\n"
            "  is_shouting(\"123\") -> False\n\n"
            "Return: True or False."
        ),
        solution="def is_shouting(s):\n    return s.isupper()\n",
        trap="def is_shouting(s):\n    return s == s.upper()\n",
        note="isupper() needs at least one cased character and no"
             " lower-case ones; digits and punctuation are ignored."
             " Comparing with upper() says yes to '123' and to the empty"
             " string, which have no letters to be upper case.",
    ),
    dict(
        id=3, ledger="P193", concept="PY3 str format", tier="1 - Strings",
        title="format(): slots filled in order", kind="function",
        func="loan_line",
        cases=[("Aisha", 3), ("Kwame", 0), ("Rosa", 150)],
        prompt=(
            "Write a function `loan_line(name, n)` that returns the"
            " sentence '<name> has <n> loans' using the string format()"
            " method with {} slots:\n\n"
            "  loan_line(\"Aisha\", 3) -> \"Aisha has 3 loans\"\n\n"
            "Return: the string."
        ),
        solution="def loan_line(name, n):\n    return \"{} has {} loans\".format(name, n)\n",
        trap="def loan_line(name, n):\n    return name + \" has \" + n + \" loans\"\n",
        note="format() fills each {} from its arguments in order and"
             " converts them to text on the way, so an int slots in"
             " without str(). Concatenation with + refuses to join a str"
             " to an int and raises TypeError. f-strings do the same job"
             " inline; format() is the older form you will meet in"
             " existing code.",
    ),
    dict(
        id=4, ledger="P194", concept="PY3 ord", tier="1 - Strings",
        title="ord(): a character's code", kind="function",
        func="code_point",
        cases=[("A",), ("a",), ("7",), (" ",)],
        prompt=(
            "Write a function `code_point(ch)` that returns the Unicode"
            " code of a single character as an integer, using ord():\n\n"
            "  code_point(\"A\") -> 65\n\n"
            "Return: an integer."
        ),
        solution="def code_point(ch):\n    return ord(ch)\n",
        trap="def code_point(ch):\n    return int(ch)\n",
        note="ord() gives the number a character is stored as -- 65 for"
             " 'A', 97 for 'a', 55 for the digit '7'. int('7') is the"
             " VALUE seven, and int('A') is a ValueError. chr() goes the"
             " other way.",
    ),
    # ====================================================== 2 Numbers and None
    dict(
        id=5, ledger="P195", concept="PY3 is None", tier="2 - Numbers and None",
        title="is None: missing, not merely empty", kind="function",
        func="is_missing",
        cases=[(None,), (0,), ("",), ("x",), ([],)],
        prompt=(
            "Write a function `is_missing(x)` that returns True only when"
            " x is None -- not when it is 0, an empty string or an empty"
            " list -- using the is None test:\n\n"
            "  is_missing(None) -> True\n"
            "  is_missing(0) -> False\n\n"
            "Return: True or False."
        ),
        solution="def is_missing(x):\n    return x is None\n",
        trap="def is_missing(x):\n    return not x\n",
        note="'not x' is True for every falsy value: None, 0, '', [] and"
             " False alike. 'is None' is True for None only, which is the"
             " difference between 'no value was given' and 'the value"
             " is zero'. It is SQL's IS NULL, and the reason the row-"
             "shaped questions tested returned is None.",
    ),
    dict(
        id=6, ledger="P196", concept="PY3 math isclose", tier="2 - Numbers and None",
        title="math.isclose(): equal enough", kind="function",
        func="about_equal",
        cases=[(0.30000000000000004, 0.3), (1.0, 1.0), (1.0, 1.1), (100.0, 100.0000000001)],
        prompt=(
            "Write a function `about_equal(a, b)` that returns True when"
            " two floats are equal within floating-point noise -- 0.1 +"
            " 0.2 against 0.3 -- using math.isclose() with its default"
            " tolerance. Remember the import.\n\n"
            "  about_equal(0.1 + 0.2, 0.3) -> True\n\n"
            "Return: True or False."
        ),
        solution=("import math\n\n"
                  "def about_equal(a, b):\n"
                  "    return math.isclose(a, b)\n"),
        trap="def about_equal(a, b):\n    return a == b\n",
        note="0.1 + 0.2 is 0.30000000000000004 in binary floating point,"
             " and == is exact, so it is not 0.3. math.isclose() allows a"
             " relative tolerance of one part in a billion by default,"
             " which absorbs that noise and still calls 1.0 and 1.1"
             " different. Never compare computed floats with ==.",
    ),
    dict(
        id=7, ledger="P197", concept="PY3 is_integer", tier="2 - Numbers and None",
        title="is_integer(): a float with nothing after the point", kind="function",
        func="is_whole",
        cases=[(4.0,), (4.5,), (0.0,), (-3.0,)],
        prompt=(
            "Write a function `is_whole(x)` that returns True when the"
            " float x has no fractional part, using the float method"
            " is_integer():\n\n"
            "  is_whole(4.0) -> True\n"
            "  is_whole(4.5) -> False\n\n"
            "Return: True or False."
        ),
        solution="def is_whole(x):\n    return x.is_integer()\n",
        trap="def is_whole(x):\n    return isinstance(x, int)\n",
        note="4.0 is a float, so isinstance(4.0, int) is False however"
             " whole its value. is_integer() asks about the VALUE: is"
             " there anything after the point? It is a method of float,"
             " and the question that matters after a division.",
    ),
    dict(
        id=8, ledger="P198", concept="PY3 math prod", tier="2 - Numbers and None",
        title="math.prod(): multiply them all", kind="function",
        func="product",
        cases=[([2, 3, 4],), ([],), ([5],), ([1.5, 2],)],
        prompt=(
            "Write a function `product(values)` that returns all the"
            " numbers multiplied together, 1 for an empty list, using"
            " math.prod(). Remember the import.\n\n"
            "  product([2, 3, 4]) -> 24\n\n"
            "Return: the product."
        ),
        solution=("import math\n\n"
                  "def product(values):\n"
                  "    return math.prod(values)\n"),
        trap="def product(values):\n    return sum(values)\n",
        note="math.prod() is to multiplication what sum() is to addition,"
             " and its empty result is 1 -- the number that multiplies"
             " nothing -- as sum()'s is 0. Before Python 3.8 this needed"
             " a loop or functools.reduce.",
    ),
    dict(
        id=9, ledger="P199", concept="PY3 min key abs", tier="2 - Numbers and None",
        title="min(key=abs): nearest to zero", kind="function",
        func="closest_to_zero",
        cases=[([3, -1, 2],), ([-5, 4],), ([0, 7],), ([-2, 2],)],
        prompt=(
            "Write a function `closest_to_zero(values)` that returns the"
            " value in a non-empty list nearest to zero -- the FIRST such"
            " value when two are equally near -- using min() with"
            " key=abs:\n\n"
            "  closest_to_zero([3, -1, 2]) -> -1\n\n"
            "Return: the value."
        ),
        solution="def closest_to_zero(values):\n    return min(values, key=abs)\n",
        trap="def closest_to_zero(values):\n    return min(values)\n",
        note="key=abs compares the values by their distance from zero"
             " but returns the value itself, sign and all. Plain min()"
             " returns the most negative number, which is usually the"
             " FURTHEST from zero. For a tie, min() keeps the first.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=10, ledger="P200", concept="PY3 list sort", tier="3 - Lists",
        title="sort(): in place, returning None", kind="function",
        func="sort_in_place",
        cases=[([3, 1, 2],), ([],), (["b", "a"],)],
        prompt=(
            "Write a function `sort_in_place(values)` that sorts the list"
            " itself with its sort() method and then returns that same"
            " list:\n\n"
            "  sort_in_place([3, 1, 2]) -> [1, 2, 3]\n\n"
            "Return: the list."
        ),
        solution="def sort_in_place(values):\n    values.sort()\n    return values\n",
        trap="def sort_in_place(values):\n    return values.sort()\n",
        note="list.sort() rearranges the list it is called on and returns"
             " None; sorted() leaves the list alone and returns a new"
             " one. 'return values.sort()' returns the None. Two lines:"
             " sort, then return the list.",
    ),
    dict(
        id=11, ledger="P201", concept="PY3 extend", tier="3 - Lists",
        title="extend(): one list onto the end of another", kind="function",
        func="joined",
        cases=[([1, 2], [3, 4]), ([], [1]), (["a"], []), ([1], [[2]])],
        prompt=(
            "Write a function `joined(a, b)` that returns a NEW list"
            " holding a's items followed by b's, using extend() on a"
            " copy of a:\n\n"
            "  joined([1, 2], [3, 4]) -> [1, 2, 3, 4]\n\n"
            "Return: the new list."
        ),
        solution="def joined(a, b):\n    out = list(a)\n    out.extend(b)\n    return out\n",
        trap="def joined(a, b):\n    out = list(a)\n    out.append(b)\n    return out\n",
        note="extend() adds each ITEM of b; append() adds b itself as one"
             " item, so [1, 2] becomes [1, 2, [3, 4]], a list with a list"
             " inside it. a + b builds the same result as extend on a"
             " copy. The copy is what keeps the caller's a unchanged.",
    ),
    dict(
        id=12, ledger="P202", concept="PY3 map", tier="3 - Lists",
        title="map(): the same function over every item", kind="function",
        func="as_strings",
        cases=[([1, 2, 3],), ([],), ([2.5, None],)],
        prompt=(
            "Write a function `as_strings(values)` that returns a list of"
            " the items each converted to a string, using list() over"
            " map() with str:\n\n"
            "  as_strings([1, 2, 3]) -> [\"1\", \"2\", \"3\"]\n\n"
            "Return: the new list."
        ),
        solution="def as_strings(values):\n    return list(map(str, values))\n",
        trap="def as_strings(values):\n    return str(values)\n",
        note="map(f, items) applies f to each item and yields the results"
             " lazily; list() collects them. str(values) converts the"
             " whole list to ONE string, '[1, 2, 3]'. A comprehension,"
             " [str(v) for v in values], is the other spelling of the"
             " same thing.",
    ),
    # ========================================================= 4 Sets and dicts
    dict(
        id=13, ledger="P203", concept="PY3 set discard", tier="4 - Sets and dictionaries",
        title="discard(): remove if present", kind="function",
        func="without",
        cases=[([1, 2, 3], 2), ([1, 2], 9), ([], 1), (["a", "a"], "a")],
        prompt=(
            "Write a function `without(items, x)` that returns a SET of"
            " the items with x removed -- and simply the set of items"
            " when x was never there -- using set() and discard():\n\n"
            "  without([1, 2, 3], 2) -> {1, 3}\n"
            "  without([1, 2], 9) -> {1, 2}\n\n"
            "Return: the set."
        ),
        solution="def without(items, x):\n    s = set(items)\n    s.discard(x)\n    return s\n",
        trap="def without(items, x):\n    s = set(items)\n    s.remove(x)\n    return s\n",
        note="remove() raises KeyError when the value is absent;"
             " discard() does nothing. Both change the set in place and"
             " return None, which is why the set is built first and"
             " returned afterwards.",
    ),
    dict(
        id=14, ledger="P204", concept="PY3 set symmetric", tier="4 - Sets and dictionaries",
        title="^ on sets: in one but not both", kind="function",
        func="either_not_both",
        cases=[(["LS1", "BD3"], ["BD3", "WF1"]), ([1, 2], [1, 2]), ([], [1]), ([1], [2])],
        prompt=(
            "Write a function `either_not_both(a, b)` that returns a SET"
            " of the values in exactly one of the two lists -- in a or"
            " in b but not in both -- using set() on each and the ^"
            " operator:\n\n"
            "  either_not_both([\"LS1\", \"BD3\"], [\"BD3\", \"WF1\"]) ->"
            " {\"LS1\", \"WF1\"}\n\n"
            "Return: the set."
        ),
        solution="def either_not_both(a, b):\n    return set(a) ^ set(b)\n",
        trap="def either_not_both(a, b):\n    return set(a) | set(b)\n",
        note="^ is the symmetric difference: the union minus the"
             " intersection. | is the union, which keeps the shared"
             " values too. Two equal sets have an empty symmetric"
             " difference. symmetric_difference() is the same operator"
             " spelled out.",
    ),
    dict(
        id=15, ledger="P205", concept="PY3 dict union", tier="4 - Sets and dictionaries",
        title="| on dicts: merged, the right one winning", kind="function",
        func="combined",
        cases=[({"a": 1}, {"b": 2}), ({"a": 1}, {"a": 5}), ({}, {}), ({"x": 1, "y": 2}, {"y": 3})],
        prompt=(
            "Write a function `combined(a, b)` that returns a NEW dict"
            " with everything from a and everything from b, b winning"
            " where a key is in both, using the | operator on dicts:\n\n"
            "  combined({\"x\": 1, \"y\": 2}, {\"y\": 3}) -> {\"x\": 1,"
            " \"y\": 3}\n\n"
            "Return: the new dictionary."
        ),
        solution="def combined(a, b):\n    return a | b\n",
        trap="def combined(a, b):\n    return a + b\n",
        note="Dicts have no +, and the TypeError says so. | merges them"
             " into a new dict, keys from the right operand overriding,"
             " and leaves both arguments alone -- what dict.update() on a"
             " copy did in an earlier set, in one expression. Available"
             " since Python 3.9.",
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
