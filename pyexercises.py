"""Python practice exercises: fifteen tiny functions, one tool each.

The fourteenth Python set, one-tool functions again: every question asks
for a function of one or two lines that returns a value, built around one
named tool no earlier set used -- rpartition(), rjust(), rsplit() with a
count, isascii(), math.hypot(), math.comb(), statistics.mode(), hex(), the
del statement, list repetition with *, filter(None, ...), tuple(),
set.add(), isdisjoint() and dict() over pairs. The title names the tool,
so the tree on the left reads like a list of tools.

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
        id=1, ledger="P206", concept="PY3 rpartition", tier="1 - Strings",
        title="rpartition(): split at the LAST dot", kind="function",
        func="name_and_extension",
        cases=[("notes.txt",), ("archive.tar.gz",), ("README",), (".hidden",)],
        prompt=(
            "Write a function `name_and_extension(filename)` that returns"
            " a tuple (name, extension) split at the LAST '.', using"
            " rpartition(). With no dot, rpartition puts the whole string"
            " in the last part, so the name is '' and the extension is"
            " the string.\n\n"
            "  name_and_extension(\"archive.tar.gz\") -> (\"archive.tar\","
            " \"gz\")\n\n"
            "Return: the tuple."
        ),
        solution=("def name_and_extension(filename):\n"
                  "    name, _, ext = filename.rpartition(\".\")\n"
                  "    return (name, ext)\n"),
        trap=("def name_and_extension(filename):\n"
              "    name, _, ext = filename.partition(\".\")\n"
              "    return (name, ext)\n"),
        note="partition() splits at the FIRST separator, rpartition() at"
             " the last -- the difference between 'archive' with"
             " extension 'tar.gz' and 'archive.tar' with extension 'gz'."
             " Both return three parts; the middle one is the separator"
             " itself, or '' when it was not found.",
    ),
    dict(
        id=2, ledger="P207", concept="PY3 rjust", tier="1 - Strings",
        title="rjust(): numbers lined up on the right", kind="function",
        func="right_aligned",
        cases=[("42", 6), ("1234", 2), ("", 3), ("7", 1)],
        prompt=(
            "Write a function `right_aligned(s, width)` that returns s"
            " padded on the LEFT with spaces to the given width, so that"
            " a column of them lines up on the right, using rjust():\n\n"
            "  right_aligned(\"42\", 6) -> \"    42\"\n\n"
            "A string already wider than width is returned unchanged.\n\n"
            "Return: the string."
        ),
        solution="def right_aligned(s, width):\n    return s.rjust(width)\n",
        trap="def right_aligned(s, width):\n    return s.ljust(width)\n",
        note="rjust() puts the padding BEFORE the text, which is how"
             " numbers are aligned in a column; ljust() puts it after,"
             " which is for words. Neither cuts a string that is already"
             " too wide. The default fill is a space.",
    ),
    dict(
        id=3, ledger="P208", concept="PY3 rsplit", tier="1 - Strings",
        title="rsplit(maxsplit=1): everything but the last word", kind="function",
        func="without_last_word",
        cases=[("The Glass Path",), ("Hidden",), ("A B C D",), ("Notes from the Salt Map",)],
        prompt=(
            "Write a function `without_last_word(s)` that returns s with"
            " its last word removed -- and a one-word string unchanged --"
            " using rsplit() with a single split from the right and taking"
            " the first part:\n\n"
            "  without_last_word(\"The Glass Path\") -> \"The Glass\"\n\n"
            "Return: the string."
        ),
        solution="def without_last_word(s):\n    return s.rsplit(\" \", 1)[0]\n",
        trap="def without_last_word(s):\n    return s.split(\" \", 1)[0]\n",
        note="split(' ', 1) makes one cut from the LEFT, so [0] is the"
             " first word alone; rsplit(' ', 1) makes one cut from the"
             " right, and [0] is everything before the last word. With"
             " no space to cut at, both return the whole string.",
    ),
    dict(
        id=4, ledger="P209", concept="PY3 isascii", tier="1 - Strings",
        title="isascii(): plain characters only", kind="function",
        func="plain_ascii",
        cases=[("Leeds",), ("Zo\u00eb",), ("",), ("LS15!",)],
        prompt=(
            "Write a function `plain_ascii(s)` that returns True when"
            " every character in s is plain ASCII -- no accents, no"
            " symbols beyond the keyboard -- using isascii(). The empty"
            " string counts as True.\n\n"
            "  plain_ascii(\"LS15!\") -> True\n\n"
            "Return: True or False."
        ),
        solution="def plain_ascii(s):\n    return s.isascii()\n",
        trap="def plain_ascii(s):\n    return s.isalpha()\n",
        note="isascii() asks about the character SET -- codes under 128 --"
             " so digits and punctuation pass and an accented letter does"
             " not. isalpha() asks whether every character is a letter,"
             " which refuses 'LS15!' and accepts an accented name. It is"
             " also one of the few is...() methods that is True for ''.",
    ),
    # ============================================================== 2 Numbers
    dict(
        id=5, ledger="P210", concept="PY3 math hypot", tier="2 - Numbers",
        title="math.hypot(): straight-line distance", kind="function",
        func="distance",
        cases=[(3, 4), (0, 0), (5, 12), (1, 1)],
        prompt=(
            "Write a function `distance(dx, dy)` that returns the"
            " straight-line distance covered by moving dx across and dy"
            " up, using math.hypot(). Remember the import.\n\n"
            "  distance(3, 4) -> 5.0\n\n"
            "Return: a float."
        ),
        solution=("import math\n\n"
                  "def distance(dx, dy):\n"
                  "    return math.hypot(dx, dy)\n"),
        trap="def distance(dx, dy):\n    return abs(dx) + abs(dy)\n",
        note="math.hypot(a, b) is the square root of a squared plus b"
             " squared -- Pythagoras in one call, and it avoids the"
             " overflow that squaring large numbers can cause. Adding the"
             " two legs is the walking distance around the block, not"
             " across it.",
    ),
    dict(
        id=6, ledger="P211", concept="PY3 math comb", tier="2 - Numbers",
        title="math.comb(): ways to choose", kind="function",
        func="ways_to_choose",
        cases=[(5, 2), (6, 0), (4, 4), (10, 3)],
        prompt=(
            "Write a function `ways_to_choose(n, k)` that returns how"
            " many different groups of k can be picked from n items,"
            " order not mattering, using math.comb(). Remember the"
            " import.\n\n"
            "  ways_to_choose(5, 2) -> 10\n\n"
            "Return: an integer."
        ),
        solution=("import math\n\n"
                  "def ways_to_choose(n, k):\n"
                  "    return math.comb(n, k)\n"),
        trap=("import math\n\n"
              "def ways_to_choose(n, k):\n"
              "    return math.perm(n, k)\n"),
        note="comb() counts groups, perm() counts ORDERED arrangements,"
             " so perm(5, 2) is 20 because choosing A then B and B then A"
             " are different arrangements of the same pair. Both are exact"
             " integers; math.factorial is the long way round.",
    ),
    dict(
        id=7, ledger="P212", concept="PY3 statistics mode", tier="2 - Numbers",
        title="statistics.mode(): the commonest value", kind="function",
        func="most_common",
        cases=[(["LS1", "BD3", "LS1"],), ([1, 1, 2, 2, 3],), ([7],), (["b", "a", "a"],)],
        prompt=(
            "Write a function `most_common(values)` that returns the"
            " value that appears most often in a non-empty list -- the"
            " first one met, when several tie -- using statistics.mode()."
            " Remember the import.\n\n"
            "  most_common([\"b\", \"a\", \"a\"]) -> \"a\"\n\n"
            "Return: the value."
        ),
        solution=("import statistics\n\n"
                  "def most_common(values):\n"
                  "    return statistics.mode(values)\n"),
        trap="def most_common(values):\n    return max(values)\n",
        note="mode() is the most FREQUENT value; max() is the largest,"
             " which is a different question that happens to agree on"
             " some lists. Since Python 3.8 mode() breaks a tie by taking"
             " the first value encountered, and works on strings as well"
             " as numbers.",
    ),
    dict(
        id=8, ledger="P213", concept="PY3 hex", tier="2 - Numbers",
        title="hex(): a number in base sixteen", kind="function",
        func="as_hex",
        cases=[(255,), (0,), (16,), (4096,)],
        prompt=(
            "Write a function `as_hex(n)` that returns the hexadecimal"
            " form of a non-negative integer as a string WITH the 0x"
            " prefix, using hex():\n\n"
            "  as_hex(255) -> \"0xff\"\n\n"
            "Return: the string."
        ),
        solution="def as_hex(n):\n    return hex(n)\n",
        trap="def as_hex(n):\n    return format(n, \"x\")\n",
        note="hex() writes the prefix that marks a hexadecimal literal in"
             " source code, '0xff'; format(n, 'x') gives the bare digits"
             " 'ff'. Which one you want depends on who reads it -- the"
             " question asked for the prefix. int('0xff', 16) reads it"
             " back.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=9, ledger="P214", concept="PY3 del", tier="3 - Lists",
        title="del: remove the item at a position", kind="function",
        func="drop_at",
        cases=[([1, 2, 3], 1), (["a"], 0), ([1, 2, 3], -1), ([5, 6, 7, 8], 0)],
        prompt=(
            "Write a function `drop_at(values, i)` that returns a NEW"
            " list with the item at position i removed, leaving the"
            " original alone, using the del statement on a copy:\n\n"
            "  drop_at([1, 2, 3], 1) -> [1, 3]\n\n"
            "Return: the new list."
        ),
        solution="def drop_at(values, i):\n    out = list(values)\n    del out[i]\n    return out\n",
        trap="def drop_at(values, i):\n    out = list(values)\n    return out.pop(i)\n",
        note="del out[i] removes the item and returns nothing; pop(i)"
             " removes it and returns the ITEM, so 'return out.pop(i)'"
             " hands back 2 instead of [1, 3]. del is a statement, not a"
             " function -- no parentheses -- and works on slices too.",
    ),
    dict(
        id=10, ledger="P215", concept="PY3 list repeat", tier="3 - Lists",
        title="[x] * n: a list of n copies", kind="function",
        func="repeated",
        cases=[("ab", 3), (0, 4), ("x", 0), (None, 2)],
        prompt=(
            "Write a function `repeated(x, n)` that returns a list"
            " holding x n times, using list repetition with *:\n\n"
            "  repeated(\"ab\", 3) -> [\"ab\", \"ab\", \"ab\"]\n\n"
            "Return: the list."
        ),
        solution="def repeated(x, n):\n    return [x] * n\n",
        trap="def repeated(x, n):\n    return x * n\n",
        note="[x] * n repeats the one-item LIST; x * n repeats x itself,"
             " which for a string is 'ababab' and for a number is"
             " multiplication. The brackets are the whole difference."
             " Beware [[]] * n: the inner lists are the same object.",
    ),
    dict(
        id=11, ledger="P216", concept="PY3 filter None", tier="3 - Lists",
        title="filter(None, ...): drop everything falsy", kind="function",
        func="truthy_only",
        cases=[([0, 1, "", "a", None, [], [2]],), ([],), ([None, 0],)],
        prompt=(
            "Write a function `truthy_only(values)` that returns a list"
            " of the values that count as true -- dropping 0, '', None,"
            " empty lists and the like -- using list() over filter() with"
            " None as the function:\n\n"
            "  truthy_only([0, 1, \"\", \"a\", None]) -> [1, \"a\"]\n\n"
            "Return: the new list."
        ),
        solution="def truthy_only(values):\n    return list(filter(None, values))\n",
        trap="def truthy_only(values):\n    return [v for v in values if v is not None]\n",
        note="filter(None, values) keeps the items that are truthy -- None"
             " in place of a function means 'test the item itself'. A"
             " test for 'is not None' keeps 0, '' and [], which are"
             " not None but are falsy. [v for v in values if v] says the"
             " same as filter(None, ...).",
    ),
    dict(
        id=12, ledger="P217", concept="PY3 tuple", tier="3 - Lists",
        title="tuple(): a list made unchangeable", kind="function",
        func="freeze",
        cases=[([1, 2],), ([],), (["a"],), ([[1], [2]],)],
        prompt=(
            "Write a function `freeze(values)` that returns the items of"
            " the list as a tuple, using tuple():\n\n"
            "  freeze([1, 2]) -> (1, 2)\n\n"
            "Return: the tuple."
        ),
        solution="def freeze(values):\n    return tuple(values)\n",
        trap="def freeze(values):\n    return list(values)\n",
        note="tuple() builds an immutable sequence from any iterable; the"
             " same items in a list are a different type, and the grader"
             " keeps them apart as Python does -- a tuple can be a dict"
             " key or a set member, a list cannot. A one-item tuple"
             " prints as (1,), comma and all.",
    ),
    # ========================================================= 4 Sets and dicts
    dict(
        id=13, ledger="P218", concept="PY3 set add", tier="4 - Sets and dictionaries",
        title="add(): one more member of a set", kind="function",
        func="with_added",
        cases=[([1, 2], 3), ([1, 2], 2), ([], "a"), (["x", "x"], "y")],
        prompt=(
            "Write a function `with_added(items, x)` that returns a SET"
            " of the items with x included -- the set is unchanged when x"
            " was already in it -- using set() and add():\n\n"
            "  with_added([1, 2], 3) -> {1, 2, 3}\n\n"
            "Return: the set."
        ),
        solution="def with_added(items, x):\n    s = set(items)\n    s.add(x)\n    return s\n",
        trap="def with_added(items, x):\n    s = set(items)\n    return s.add(x)\n",
        note="add() changes the set in place and returns None, like"
             " append() on a list -- so 'return s.add(x)' returns nothing."
             " Add, then return the set. A set has no append(): there is"
             " no end to append to.",
    ),
    dict(
        id=14, ledger="P219", concept="PY3 isdisjoint", tier="4 - Sets and dictionaries",
        title="isdisjoint(): nothing in common?", kind="function",
        func="no_overlap",
        cases=[([1, 2], [3]), ([1, 2], [2, 3]), ([], []), (["a"], ["a"])],
        prompt=(
            "Write a function `no_overlap(a, b)` that returns True when"
            " the two lists share no value at all, using set() on a and"
            " isdisjoint():\n\n"
            "  no_overlap([1, 2], [3]) -> True\n\n"
            "Return: True or False."
        ),
        solution="def no_overlap(a, b):\n    return set(a).isdisjoint(b)\n",
        trap="def no_overlap(a, b):\n    return set(a) != set(b)\n",
        note="isdisjoint() is True when the intersection is empty, and"
             " takes any iterable as its argument. 'Not equal' is a"
             " different test: [1, 2] and [2, 3] are unequal and still"
             " share a value. Two empty lists are disjoint -- there is"
             " nothing to share.",
    ),
    dict(
        id=15, ledger="P220", concept="PY3 dict pairs", tier="4 - Sets and dictionaries",
        title="dict(pairs): a dictionary from (key, value) tuples", kind="function",
        func="to_dict",
        cases=[([("a", 1), ("b", 2)],), ([],), ([("a", 1), ("a", 2)],)],
        prompt=(
            "Write a function `to_dict(pairs)` that returns a dictionary"
            " built from a list of (key, value) tuples, using dict()."
            " When a key appears twice, the later value wins.\n\n"
            "  to_dict([(\"a\", 1), (\"b\", 2)]) -> {\"a\": 1, \"b\": 2}\n\n"
            "Return: the dictionary."
        ),
        solution="def to_dict(pairs):\n    return dict(pairs)\n",
        trap="def to_dict(pairs):\n    return dict.fromkeys(pairs)\n",
        note="dict() accepts a sequence of two-item pairs and makes each"
             " the key and value; a repeated key keeps the last value."
             " dict.fromkeys(pairs) makes each whole TUPLE a key with the"
             " value None -- a dictionary, but not the one asked for."
             " dict(zip(keys, values)) is the same tool with the pairs"
             " made on the way in.",
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
