"""Python practice exercises: fifteen tiny functions, one tool each.

The seventeenth Python set, back to one-tool functions after the two-tool
set: every question asks for a function of one or two lines that returns
a value, built around one named tool no earlier set used -- startswith()
with a tuple, islower(), chr(), find() with a start position,
math.factorial(), math.lcm(), statistics.fmean(), math.trunc(), oct(),
itertools.pairwise(), heapq.nsmallest(), max() with a default,
itertools.chain(), dict.popitem() and >= on sets. Where a tool needs an
import, the prompt gives the exact line to write.

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
        id=1, ledger="P251", concept="PY3 startswith tuple", tier="1 - Strings",
        title="startswith(tuple): a Leeds or Bradford postcode?", kind="function",
        func="is_local",
        cases=[("LS15",), ("BD3",), ("WF1",), ("",)],
        prompt=(
            "Write a function `is_local(area)` that returns True when the"
            " postcode area begins with 'LS' or 'BD', using startswith()"
            " with a TUPLE of prefixes. No import is needed.\n\n"
            "  is_local(\"BD3\") -> True\n"
            "  is_local(\"WF1\") -> False\n\n"
            "Return: True or False."
        ),
        solution="def is_local(area):\n    return area.startswith((\"LS\", \"BD\"))\n",
        trap="def is_local(area):\n    return area.startswith(\"LS\" or \"BD\")\n",
        note="startswith() takes a tuple and is true if ANY prefix"
             " matches, like endswith() in an earlier set. 'LS' or 'BD'"
             " is evaluated first and is just 'LS', because a non-empty"
             " string is truthy, so Bradford is refused.",
    ),
    dict(
        id=2, ledger="P252", concept="PY3 islower", tier="1 - Strings",
        title="islower(): no capitals anywhere", kind="function",
        func="all_lower",
        cases=[("leeds",), ("Leeds",), ("ls15",), ("123",), ("",)],
        prompt=(
            "Write a function `all_lower(s)` that returns True when every"
            " letter in s is lower case and there is at least one letter,"
            " using islower(). No import is needed.\n\n"
            "  all_lower(\"ls15\") -> True\n"
            "  all_lower(\"123\") -> False\n\n"
            "Return: True or False."
        ),
        solution="def all_lower(s):\n    return s.islower()\n",
        trap="def all_lower(s):\n    return s == s.lower()\n",
        note="islower() needs at least one cased character and no"
             " upper-case ones; digits are ignored. Comparing with"
             " lower() says yes to '123' and to '', which have no letters"
             " at all -- the mirror of isupper() from an earlier set.",
    ),
    dict(
        id=3, ledger="P253", concept="PY3 chr", tier="1 - Strings",
        title="chr(): the character with a given code", kind="function",
        func="letter_from_code",
        cases=[(65,), (97,), (55,), (32,)],
        prompt=(
            "Write a function `letter_from_code(n)` that returns the"
            " single character whose Unicode code is n, using chr(). No"
            " import is needed.\n\n"
            "  letter_from_code(65) -> \"A\"\n\n"
            "Return: a one-character string."
        ),
        solution="def letter_from_code(n):\n    return chr(n)\n",
        trap="def letter_from_code(n):\n    return str(n)\n",
        note="chr() is the inverse of ord(): 65 becomes 'A', 97 'a', 55"
             " the digit '7' and 32 a space. str(65) is the two-character"
             " string '65' -- the number written out, not the character"
             " it codes for.",
    ),
    dict(
        id=4, ledger="P254", concept="PY3 find start", tier="1 - Strings",
        title="find(sub, start): the second space", kind="function",
        func="second_space",
        cases=[("Notes from the Salt Map",), ("Two words",), ("One",), ("a b c",)],
        prompt=(
            "Write a function `second_space(s)` that returns the position"
            " of the SECOND space in s, or -1 when there is no second"
            " space, using find() twice -- the second call with a start"
            " position just after the first space. No import is"
            " needed.\n\n"
            "  second_space(\"a b c\") -> 3\n\n"
            "Return: an integer."
        ),
        solution="def second_space(s):\n    return s.find(\" \", s.find(\" \") + 1)\n",
        trap="def second_space(s):\n    return s.find(\" \")\n",
        note="find() takes an optional start, and searching from one"
             " past the first match finds the next one. With no first"
             " space find() gives -1, the start becomes 0, and the second"
             " search also finds nothing -- so 'One' comes out -1 without"
             " a special case.",
    ),
    # ============================================================== 2 Numbers
    dict(
        id=5, ledger="P255", concept="PY3 math factorial", tier="2 - Numbers",
        title="math.factorial(): n times everything below it", kind="function",
        func="factorial",
        cases=[(5,), (0,), (1,), (10,)],
        prompt=(
            "Write a function `factorial(n)` that returns n! -- the"
            " product of the whole numbers from 1 to n, and 1 for n = 0"
            " -- using math.factorial(). Write `import math` as the"
            " first line.\n\n"
            "  factorial(5) -> 120\n\n"
            "Return: an integer."
        ),
        solution=("import math\n\n"
                  "def factorial(n):\n"
                  "    return math.factorial(n)\n"),
        trap="def factorial(n):\n    return n * (n - 1)\n",
        note="n * (n - 1) is only the first step of a factorial, and"
             " gives 0 for n = 1 and 0 for n = 0 where the answer is 1."
             " math.factorial() is exact for any size of n, because"
             " Python integers do not overflow.",
    ),
    dict(
        id=6, ledger="P256", concept="PY3 math lcm", tier="2 - Numbers",
        title="math.lcm(): the smallest shared multiple", kind="function",
        func="shared_multiple",
        cases=[(4, 6), (7, 3), (5, 10), (1, 1)],
        prompt=(
            "Write a function `shared_multiple(a, b)` that returns the"
            " smallest positive number both a and b divide into, using"
            " math.lcm(). Write `import math` as the first line.\n\n"
            "  shared_multiple(4, 6) -> 12\n\n"
            "Return: an integer."
        ),
        solution=("import math\n\n"
                  "def shared_multiple(a, b):\n"
                  "    return math.lcm(a, b)\n"),
        trap="def shared_multiple(a, b):\n    return a * b\n",
        note="The product is always a shared multiple but rarely the"
             " smallest: 4 and 6 share 12, not 24. math.lcm() is the"
             " partner of math.gcd() from an earlier set -- the two"
             " multiply to a * b.",
    ),
    dict(
        id=7, ledger="P257", concept="PY3 statistics fmean", tier="2 - Numbers",
        title="statistics.fmean(): the mean, always a float", kind="function",
        func="mean_of",
        cases=[([1, 2, 3, 4],), ([10],), ([2, 4],), ([1.5, 2.5],)],
        prompt=(
            "Write a function `mean_of(values)` that returns the"
            " arithmetic mean of a non-empty list as a float, using"
            " statistics.fmean(). Write `import statistics` as the first"
            " line.\n\n"
            "  mean_of([1, 2, 3, 4]) -> 2.5\n\n"
            "Return: a float."
        ),
        solution=("import statistics\n\n"
                  "def mean_of(values):\n"
                  "    return statistics.fmean(values)\n"),
        trap=("import statistics\n\n"
              "def mean_of(values):\n"
              "    return statistics.median(values)\n"),
        note="fmean() is mean() done in floating point: faster, and"
             " always a float even for whole-number data, where mean()"
             " can return a Fraction or an int. median() is the middle"
             " value, a different average -- for [1, 2, 3, 4] they agree,"
             " and for [1, 2, 10] they do not.",
    ),
    dict(
        id=8, ledger="P258", concept="PY3 math trunc", tier="2 - Numbers",
        title="math.trunc(): drop the fraction, towards zero", kind="function",
        func="whole_part",
        cases=[(2.7,), (-2.7,), (4.0,), (-0.5,)],
        prompt=(
            "Write a function `whole_part(x)` that returns the integer"
            " part of x with the fraction simply cut off, so -2.7 becomes"
            " -2, using math.trunc(). Write `import math` as the first"
            " line.\n\n"
            "  whole_part(-2.7) -> -2\n\n"
            "Return: an integer."
        ),
        solution=("import math\n\n"
                  "def whole_part(x):\n"
                  "    return math.trunc(x)\n"),
        trap=("import math\n\n"
              "def whole_part(x):\n"
              "    return math.floor(x)\n"),
        note="trunc() cuts towards zero, floor() rounds down the number"
             " line; they agree for positive numbers and differ for"
             " negative ones, where floor(-2.7) is -3. int(x) does the"
             " same as trunc() for a float; trunc() says which rule it"
             " follows.",
    ),
    dict(
        id=9, ledger="P259", concept="PY3 oct", tier="2 - Numbers",
        title="oct(): a number in base eight", kind="function",
        func="as_octal",
        cases=[(8,), (0,), (64,), (255,)],
        prompt=(
            "Write a function `as_octal(n)` that returns the octal form"
            " of a non-negative integer as a string WITH the 0o prefix,"
            " using oct(). No import is needed.\n\n"
            "  as_octal(8) -> \"0o10\"\n\n"
            "Return: the string."
        ),
        solution="def as_octal(n):\n    return oct(n)\n",
        trap="def as_octal(n):\n    return hex(n)\n",
        note="oct(), hex() and bin() are a family: each writes the number"
             " in its base with the prefix a Python literal would carry"
             " -- 0o, 0x, 0b. Eight is '0o10' in octal and '0x8' in hex."
             " format(n, 'o') gives the digits without the prefix.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=10, ledger="P260", concept="PY3 pairwise", tier="3 - Lists",
        title="itertools.pairwise(): each item with the next", kind="function",
        func="neighbours",
        cases=[([1, 2, 3, 4],), ([],), (["a"],), (["x", "y"],)],
        prompt=(
            "Write a function `neighbours(values)` that returns a list of"
            " tuples pairing each item with the one after it, using"
            " list() over itertools.pairwise(). Write `import itertools`"
            " as the first line.\n\n"
            "  neighbours([1, 2, 3, 4]) -> [(1, 2), (2, 3), (3, 4)]\n\n"
            "Return: the list of tuples."
        ),
        solution=("import itertools\n\n"
                  "def neighbours(values):\n"
                  "    return list(itertools.pairwise(values))\n"),
        trap="def neighbours(values):\n    return list(zip(values, values))\n",
        note="pairwise() yields overlapping pairs, one fewer than the"
             " items, and nothing at all for a list of one. zip(values,"
             " values) pairs each item with ITSELF. The same result"
             " without the import is zip(values, values[1:]).",
    ),
    dict(
        id=11, ledger="P261", concept="PY3 heapq nsmallest", tier="3 - Lists",
        title="heapq.nsmallest(): the three lowest", kind="function",
        func="bottom_three",
        cases=[([5, 1, 9, 3, 7],), ([2, 1],), ([],), ([4, 4, 4, 4],)],
        prompt=(
            "Write a function `bottom_three(values)` that returns the"
            " three smallest values, smallest first -- fewer when the"
            " list is shorter -- using heapq.nsmallest(). Write `import"
            " heapq` as the first line.\n\n"
            "  bottom_three([5, 1, 9, 3, 7]) -> [1, 3, 5]\n\n"
            "Return: the list."
        ),
        solution=("import heapq\n\n"
                  "def bottom_three(values):\n"
                  "    return heapq.nsmallest(3, values)\n"),
        trap="def bottom_three(values):\n    return sorted(values)[-3:]\n",
        note="sorted()[-3:] is the three LARGEST; the smallest are the"
             " first three of a sorted list, sorted(values)[:3]."
             " nsmallest(n, values) returns them in ascending order and"
             " handles a short list without complaint. nlargest() from"
             " an earlier set is its twin.",
    ),
    dict(
        id=12, ledger="P262", concept="PY3 max default", tier="3 - Lists",
        title="max(default=): the largest, or None", kind="function",
        func="highest",
        cases=[([4, 2, 9],), ([],), ([7],), ([-1, -5],)],
        prompt=(
            "Write a function `highest(values)` that returns the largest"
            " value in the list, or None when the list is empty, using"
            " max() with its default= argument. No import is needed.\n\n"
            "  highest([4, 2, 9]) -> 9\n"
            "  highest([]) -> None\n\n"
            "Return: the largest value, or None."
        ),
        solution="def highest(values):\n    return max(values, default=None)\n",
        trap="def highest(values):\n    return max(values)\n",
        note="max() of an empty list raises ValueError; default= names"
             " what to return instead, and only then. The same keyword"
             " works for min(), as an earlier set used.",
    ),
    dict(
        id=13, ledger="P263", concept="PY3 itertools chain", tier="3 - Lists",
        title="itertools.chain(): several lists as one", kind="function",
        func="flattened",
        cases=[([[1, 2], [3], [4, 5]],), ([],), ([[], ["a"]],), ([[1], [2], [3], [4]],)],
        prompt=(
            "Write a function `flattened(lists)` that returns one list"
            " holding the items of every inner list in order, using"
            " list() over itertools.chain(*lists) -- the star unpacks the"
            " outer list into chain's arguments. Write `import"
            " itertools` as the first line.\n\n"
            "  flattened([[1, 2], [3], [4, 5]]) -> [1, 2, 3, 4, 5]\n\n"
            "Return: the new list."
        ),
        solution=("import itertools\n\n"
                  "def flattened(lists):\n"
                  "    return list(itertools.chain(*lists))\n"),
        trap="def flattened(lists):\n    return lists[0] + lists[1]\n",
        note="chain() walks through each iterable in turn as if they were"
             " one, and *lists hands it every inner list however many"
             " there are. Adding lists[0] and lists[1] only works for"
             " exactly two, and fails on an empty outer list."
             " chain.from_iterable(lists) says the same without the star.",
    ),
    # ========================================================= 4 Sets and dicts
    dict(
        id=14, ledger="P264", concept="PY3 dict popitem", tier="4 - Sets and dictionaries",
        title="popitem(): the last pair, taken out", kind="function",
        func="last_added",
        cases=[({"a": 1, "b": 2, "c": 3},), ({"only": 0},), ({"x": None, "y": 5},)],
        prompt=(
            "Write a function `last_added(d)` that removes and returns"
            " the most recently inserted (key, value) pair of a non-empty"
            " dictionary as a tuple, using popitem(). No import is"
            " needed.\n\n"
            "  last_added({\"a\": 1, \"b\": 2, \"c\": 3}) -> (\"c\", 3)\n\n"
            "Return: the tuple."
        ),
        solution="def last_added(d):\n    return d.popitem()\n",
        trap="def last_added(d):\n    return list(d.items())[0]\n",
        note="popitem() takes the LAST pair in insertion order, returns"
             " it as a tuple and removes it -- a dict used as a stack."
             " items()[0] is the first pair, and leaves the dict as it"
             " was. On an empty dict popitem() raises KeyError.",
    ),
    dict(
        id=15, ledger="P265", concept="PY3 set superset", tier="4 - Sets and dictionaries",
        title=">= on sets: does the stock cover the order?", kind="function",
        func="covers",
        cases=[(["ink", "pen", "paper"], ["pen", "ink"]), (["ink", "pen"], ["pen", "glue"]),
               (["ink"], []), ([], ["ink"])],
        prompt=(
            "Write a function `covers(stock, wanted)` that returns True"
            " when every wanted item is in stock, using set() on each and"
            " the >= operator -- superset. No import is needed.\n\n"
            "  covers([\"ink\", \"pen\", \"paper\"], [\"pen\", \"ink\"]) ->"
            " True\n\n"
            "Return: True or False."
        ),
        solution="def covers(stock, wanted):\n    return set(stock) >= set(wanted)\n",
        trap="def covers(stock, wanted):\n    return set(stock) <= set(wanted)\n",
        note="a >= b on sets asks whether a contains everything in b --"
             " a is a superset. <= asks the opposite, whether the stock"
             " is contained in the order. The empty order is covered by"
             " any stock, and an empty stock covers only an empty order."
             " issuperset() is the same test spelled out.",
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
