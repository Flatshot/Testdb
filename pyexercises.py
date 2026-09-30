"""Python practice exercises: fifteen tiny functions, one tool each.

The fifth Python set, and a small step up from the three before it: every
question asks for a FUNCTION of one to three lines that RETURNS a value,
and is graded on what it returns for several inputs rather than on what it
prints. Each is still built around one named tool -- sum(), max(key=),
upper(), strip(), split(), join(), %, /, [-1], [start:stop], get(),
count(), a list comprehension, set() -- and the title names it, so the
tree on the left reads like a list of tools.

Two kinds of question, told apart by `kind`:

  "program"   the editor holds a whole program. Run executes it and shows
              what it printed; Check compares that, line for line, with what
              the reference program prints. Not used in this set.
  "function"  the editor defines a function named `func`. Run calls it once
              per case in `cases` and shows each call and its result; Check
              compares each result with the reference function's. Values
              are compared, not their printed form -- a dict in another
              order is the same dict -- but the container type counts, so a
              tuple is not a list, and 0 is not False.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py),
so an infinite loop or a print in a loop is stopped, not fatal.
"""

import pyrun

EXERCISES = [
    # ============================================================== 1 Numbers
    dict(
        id=1, ledger="P071", concept="PY3 return", tier="1 - Numbers",
        title="return: sum() handed back", kind="function",
        func="total",
        cases=[([16, 30, 18],), ([],), ([5],)],
        prompt=(
            "Write a function `total(nums)` that RETURNS the sum of the"
            " numbers in the list, using sum():\n\n"
            "  total([16, 30, 18]) -> 64\n\n"
            "Return the value; do not print it. An empty list totals 0.\n\n"
            "Return: the total."
        ),
        solution="def total(nums):\n    return sum(nums)\n",
        trap="def total(nums):\n    print(sum(nums))\n",
        note="A function that prints its answer shows it on the screen and"
             " returns None, so the caller gets nothing to use. return"
             " hands the value back; printing is the caller's decision."
             " sum() of an empty list is 0, so no special case is needed.",
    ),
    dict(
        id=2, ledger="P072", concept="PY3 modulo", tier="1 - Numbers",
        title="%: is it even", kind="function",
        func="is_even",
        cases=[(4,), (7,), (0,), (-3,)],
        prompt=(
            "Write a function `is_even(n)` that returns True when n is"
            " even and False otherwise, using the remainder operator %:\n\n"
            "  is_even(4) -> True\n"
            "  is_even(7) -> False\n\n"
            "Return: True or False, not a number."
        ),
        solution="def is_even(n):\n    return n % 2 == 0\n",
        trap="def is_even(n):\n    return n % 2\n",
        note="n % 2 is 0 or 1, and returning it gives a NUMBER, not a"
             " boolean -- and the wrong way round, since 0 means even. The"
             " comparison n % 2 == 0 is already True or False, so it can"
             " be returned directly; no if/else needed. The grader tells"
             " 0 from False, as a caller writing `if is_even(n)` would"
             " not.",
    ),
    dict(
        id=3, ledger="P073", concept="PY3 division", tier="1 - Numbers",
        title="/: an average to two decimals", kind="function",
        func="average",
        cases=[([1, 2, 3, 4],), ([36.8, 37.2, 38.1],), ([7],)],
        prompt=(
            "Write a function `average(nums)` that returns the mean of a"
            " non-empty list, rounded to two decimal places, using / for"
            " the division:\n\n"
            "  average([1, 2, 3, 4]) -> 2.5\n\n"
            "Return: the mean, rounded."
        ),
        solution="def average(nums):\n    return round(sum(nums) / len(nums), 2)\n",
        trap="def average(nums):\n    return round(sum(nums) // len(nums), 2)\n",
        note="/ divides and keeps the fraction; // throws it away first,"
             " so 10 // 4 is 2 and no rounding can bring the .5 back. Use"
             " // only when you want whole-number division. round(x, 2)"
             " keeps two decimals; on a value like 2.5 it prints as 2.5,"
             " because a float does not carry trailing zeros.",
    ),
    # ============================================================== 2 Strings
    dict(
        id=4, ledger="P074", concept="PY3 upper", tier="2 - Strings",
        title="upper(): shouting", kind="function",
        func="shout",
        cases=[("code blue",), ("Ward 5",), ("",)],
        prompt=(
            "Write a function `shout(text)` that returns the text in"
            " capitals with an exclamation mark on the end, using"
            " upper():\n\n"
            "  shout(\"code blue\") -> \"CODE BLUE!\"\n\n"
            "Return: the new string."
        ),
        solution='def shout(text):\n    return text.upper() + "!"\n',
        trap='def shout(text):\n    return text.upper + "!"\n',
        note="text.upper without parentheses is the method itself, not"
             " its result, and adding a string to a method is a"
             " TypeError. Call it: text.upper(). The + then joins two"
             " strings. An empty string shouts as just '!'.",
    ),
    dict(
        id=5, ledger="P075", concept="PY3 strip", tier="2 - Strings",
        title="strip(): tidy input", kind="function",
        func="clean",
        cases=[("  Bay 3  ",), ("O+",), ("\tA B \n",)],
        prompt=(
            "Write a function `clean(text)` that returns the text with"
            " whitespace removed from both ends, using strip(). Spaces"
            " inside the text stay:\n\n"
            "  clean(\"  Bay 3  \") -> \"Bay 3\"\n\n"
            "Return: the stripped string."
        ),
        solution="def clean(text):\n    return text.strip()\n",
        trap='def clean(text):\n    return text.replace(" ", "")\n',
        note="strip() trims the ends and nothing else, and it trims tabs"
             " and newlines as well as spaces. replace(' ', '') deletes"
             " every space, including the one in 'Bay 3', and leaves a"
             " tab alone. lstrip() and rstrip() trim one end only.",
    ),
    dict(
        id=6, ledger="P076", concept="PY3 split", tier="2 - Strings",
        title="split(): text into words", kind="function",
        func="words",
        cases=[("Morphine Codeine Diazepam",), ("one",), ("",)],
        prompt=(
            "Write a function `words(text)` that returns the words of the"
            " text as a list, using split():\n\n"
            "  words(\"Morphine Codeine Diazepam\") -> [\"Morphine\","
            " \"Codeine\", \"Diazepam\"]\n\n"
            "Return: a list of strings; empty text gives an empty list."
        ),
        solution="def words(text):\n    return text.split()\n",
        trap="def words(text):\n    return list(text)\n",
        note="list(text) breaks a string into its CHARACTERS, one per"
             " item. split() breaks it at whitespace into words, and with"
             " no argument it also drops extra spaces and returns [] for"
             " empty text. split(',') splits at commas instead.",
    ),
    dict(
        id=7, ledger="P077", concept="PY3 join", tier="2 - Strings",
        title="join(): words into text", kind="function",
        func="joined",
        cases=[(["Barry", "Bevan", "Cavell"],), (["Fleming"],), ([],)],
        prompt=(
            "Write a function `joined(names)` that returns the names as one"
            " string separated by ', ', using join():\n\n"
            "  joined([\"Barry\", \"Bevan\"]) -> \"Barry, Bevan\"\n\n"
            "Return: one string; an empty list gives an empty string."
        ),
        solution='def joined(names):\n    return ", ".join(names)\n',
        trap='def joined(names):\n    return names.join(", ")\n',
        note="join() is a STRING method: the separator calls it and the"
             " list is the argument, ', '.join(names). Lists have no join,"
             " so names.join(...) is an AttributeError. It joins any"
             " number of items, including none, without a stray separator"
             " at either end.",
    ),
    dict(
        id=8, ledger="P078", concept="PY3 slice", tier="2 - Strings",
        title="[start:stop]: the first three", kind="function",
        func="first_three",
        cases=[("Nightingale",), ("SRG-04",), ("ab",)],
        prompt=(
            "Write a function `first_three(text)` that returns the first"
            " three characters of the text, using a slice. Shorter text"
            " returns what there is:\n\n"
            "  first_three(\"Nightingale\") -> \"Nig\"\n\n"
            "Return: the slice."
        ),
        solution="def first_three(text):\n    return text[:3]\n",
        trap="def first_three(text):\n    return text[0:2]\n",
        note="[0:3] or [:3] is three characters, because the stop is not"
             " included; [0:2] is two. A slice past the end of a short"
             " string returns what exists rather than raising, which is"
             " why 'ab' needs no special case -- unlike text[2], which"
             " would be an IndexError.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=9, ledger="P079", concept="PY3 max key", tier="3 - Lists",
        title="max(key=len): the longest", kind="function",
        func="longest",
        cases=[(["Barry", "Nightingale", "Bevan"],), (["a", "bb", "cc"],), (["x"],)],
        prompt=(
            "Write a function `longest(words)` that returns the longest"
            " word in a non-empty list, using max() with key=len. On a tie"
            " the first of the longest is returned:\n\n"
            "  longest([\"Barry\", \"Nightingale\", \"Bevan\"]) ->"
            " \"Nightingale\"\n\n"
            "Return: the word."
        ),
        solution="def longest(words):\n    return max(words, key=len)\n",
        trap="def longest(words):\n    return max(words)\n",
        note="max(words) compares the strings themselves, alphabetically,"
             " so 'Nightingale' loses to 'Bevan'. key=len says compare by"
             " length and return the word, not the length. max() keeps the"
             " first of equal maximums, which is the tie rule here.",
    ),
    dict(
        id=10, ledger="P080", concept="PY3 count", tier="3 - Lists",
        title="count(): how many of one value", kind="function",
        func="count_of",
        cases=[(["day", "night", "day", "day"], "day"), (["day"], "night"), ([], "day")],
        prompt=(
            "Write a function `count_of(items, value)` that returns how"
            " many times the value appears in the list, using the list's"
            " count() method:\n\n"
            "  count_of([\"day\", \"night\", \"day\"], \"day\") -> 2\n\n"
            "Return: the count, 0 when it never appears."
        ),
        solution="def count_of(items, value):\n    return items.count(value)\n",
        trap="def count_of(items, value):\n    return len(items)\n",
        note="len() is how many items there are; count(value) is how many"
             " of them equal the value. They agree only when every item"
             " matches. count() returns 0 for a value that is not there,"
             " unlike index(), which raises.",
    ),
    dict(
        id=11, ledger="P081", concept="PY3 negative index", tier="3 - Lists",
        title="[-1]: the last item", kind="function",
        func="last",
        cases=[([72, 118, 65],), (["only"],), ([1, 2],)],
        prompt=(
            "Write a function `last(items)` that returns the last item of a"
            " non-empty list, using a negative index:\n\n"
            "  last([72, 118, 65]) -> 65\n\n"
            "Return: the item."
        ),
        solution="def last(items):\n    return items[-1]\n",
        trap="def last(items):\n    return items[len(items)]\n",
        note="Indexes run from 0 to len - 1, so items[len(items)] is one"
             " past the end and an IndexError. items[-1] counts from the"
             " end: -1 is the last, -2 the one before. It works for any"
             " non-empty sequence, strings included.",
    ),
    dict(
        id=12, ledger="P082", concept="PY3 comprehension", tier="3 - Lists",
        title="[... for ...]: a list from a list", kind="function",
        func="doubled",
        cases=[([1, 2, 3],), ([],), ([10],)],
        prompt=(
            "Write a function `doubled(nums)` that returns a NEW list with"
            " every number doubled, using a list comprehension:\n\n"
            "  doubled([1, 2, 3]) -> [2, 4, 6]\n\n"
            "Return: the new list; an empty list stays empty."
        ),
        solution="def doubled(nums):\n    return [n * 2 for n in nums]\n",
        trap="def doubled(nums):\n    return nums * 2\n",
        note="A list times 2 is the list REPEATED -- [1, 2, 3, 1, 2, 3] --"
             " not each item doubled. A comprehension, [expression for"
             " item in list], builds a new list by applying the expression"
             " to each item; it is the one-line form of a for loop with"
             " append().",
    ),
    dict(
        id=13, ledger="P083", concept="PY3 set", tier="3 - Lists",
        title="set(): the distinct values, sorted", kind="function",
        func="distinct_sorted",
        cases=[(["day", "night", "day"],), ([3, 1, 3, 2, 1],), ([],)],
        prompt=(
            "Write a function `distinct_sorted(items)` that returns the"
            " distinct values of the list, sorted, as a LIST -- set() to"
            " drop the repeats, sorted() to order them:\n\n"
            "  distinct_sorted([\"day\", \"night\", \"day\"]) ->"
            " [\"day\", \"night\"]\n\n"
            "Return: a sorted list."
        ),
        solution="def distinct_sorted(items):\n    return sorted(set(items))\n",
        trap="def distinct_sorted(items):\n    return set(items)\n",
        note="set(items) drops the repeats but has no order, and it is a"
             " different type from a list -- a caller indexing result[0]"
             " would fail. sorted() accepts a set and returns a list, so"
             " the two together are the idiom. On an empty list it"
             " returns [].",
    ),
    # ========================================================= 4 Dictionaries
    dict(
        id=14, ledger="P084", concept="PY3 dict get", tier="4 - Dictionaries",
        title="get(): a lookup with a fallback", kind="function",
        func="beds_for",
        cases=[("Fleming", {"Fleming": 16, "Barry": 30}),
               ("Bevan", {"Fleming": 16, "Barry": 30}),
               ("Barry", {})],
        prompt=(
            "Write a function `beds_for(ward, beds)` that returns the beds"
            " for the ward from the dictionary, or 0 when the ward is not"
            " in it, using get():\n\n"
            "  beds_for(\"Bevan\", {\"Fleming\": 16}) -> 0\n\n"
            "Return: a number."
        ),
        solution="def beds_for(ward, beds):\n    return beds.get(ward, 0)\n",
        trap="def beds_for(ward, beds):\n    return beds[ward]\n",
        note="beds[ward] raises KeyError when the ward is missing; get(ward,"
             " 0) returns the 0 instead. The second argument is the"
             " fallback, and it is None if you leave it out -- which a"
             " caller adding the result to a number would then trip over.",
    ),
    dict(
        id=15, ledger="P085", concept="PY3 max key dict", tier="4 - Dictionaries",
        title="max(key=d.get): the key with the biggest value", kind="function",
        func="fullest",
        cases=[({"Fleming": 16, "Barry": 30, "Jenner": 18},),
               ({"Zed": 1, "Amy": 2},), ({"one": 5},)],
        prompt=(
            "Write a function `fullest(beds)` that returns the KEY with the"
            " largest value in a non-empty dictionary, using max() with"
            " key=beds.get:\n\n"
            "  fullest({\"Fleming\": 16, \"Barry\": 30}) -> \"Barry\"\n\n"
            "Return: the key."
        ),
        solution="def fullest(beds):\n    return max(beds, key=beds.get)\n",
        trap="def fullest(beds):\n    return max(beds.values())\n",
        note="max(beds.values()) is the largest NUMBER, 30, but the"
             " question wants the ward. Looping over a dict gives its"
             " keys, and key=beds.get tells max() to judge each key by its"
             " value while returning the key. The same key= works with"
             " min() and sorted().",
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
