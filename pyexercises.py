"""Python practice exercises: fifteen tiny functions, one tool each.

The eighth Python set, and a step back DOWN after the row-shaped set: every
question asks for a function of one or two lines that returns a value, and
each is built around one named tool the earlier function sets did not use
-- round(), abs(), min(key=len), sorted(key=len), startswith(), the in
test, dict(zip()), title(), index(), a filtering comprehension, [::-1],
count(), split()[-1], and min() with max() for a clamp. The title names
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

ADM = [{"id": 1, "patient": 7, "ward": "Fleming", "days": 3.5, "priority": "urgent"},
          {"id": 2, "patient": 9, "ward": "Barry", "days": None, "priority": "routine"},
          {"id": 3, "patient": 7, "ward": "Fleming", "days": 1.0, "priority": "immediate"},
          {"id": 4, "patient": 2, "ward": "Jenner", "days": 8.25, "priority": "routine"},
          {"id": 5, "patient": 9, "ward": "Barry", "days": 2.0, "priority": "urgent"}]

EXERCISES = [
    # ============================================================== 1 Numbers
    dict(
        id=1, ledger="P116", concept="PY3 round", tier="1 - Numbers",
        title="round(): to the nearest whole number", kind="function",
        func="nearest_whole",
        cases=[(3.7,), (2.2,), (9.5,), (4,)],
        prompt=(
            "Write a function `nearest_whole(x)` that returns x rounded to"
            " the nearest whole number, as an integer, using round():\n\n"
            "  nearest_whole(3.7) -> 4\n\n"
            "Return: an integer."
        ),
        solution="def nearest_whole(x):\n    return round(x)\n",
        trap="def nearest_whole(x):\n    return round(x, 0)\n",
        note="round(x) with no second argument returns an int; round(x, 0)"
             " rounds to no decimals but keeps the float type, so 4.0 comes"
             " back where 4 was asked. Note the half-way rule: Python rounds"
             " 9.5 to 10 and 8.5 to 8 -- to the nearest EVEN number -- which"
             " surprises people expecting schoolbook rounding.",
    ),
    dict(
        id=2, ledger="P117", concept="PY3 abs", tier="1 - Numbers",
        title="abs(): how far apart", kind="function",
        func="distance",
        cases=[(3, 10), (10, 3), (5, 5), (-2.5, 1)],
        prompt=(
            "Write a function `distance(a, b)` that returns how far apart"
            " two numbers are, always as a positive number, using abs():\n\n"
            "  distance(10, 3) -> 7\n"
            "  distance(3, 10) -> 7\n\n"
            "Return: the distance."
        ),
        solution="def distance(a, b):\n    return abs(a - b)\n",
        trap="def distance(a, b):\n    return a - b\n",
        note="a - b changes sign with the order of the arguments, and a"
             " distance should not. abs() drops the sign. It works on"
             " floats as well as ints, and abs(-2.5 - 1) is 3.5.",
    ),
    dict(
        id=3, ledger="P118", concept="PY3 percent", tier="1 - Numbers",
        title="round(x, 1): a percentage to one decimal", kind="function",
        func="percent",
        cases=[(1, 3), (50, 200), (7, 7), (0, 5)],
        prompt=(
            "Write a function `percent(part, whole)` that returns part as a"
            " percentage of whole, rounded to one decimal place. whole is"
            " never 0:\n\n"
            "  percent(1, 3) -> 33.3\n\n"
            "Return: the percentage."
        ),
        solution="def percent(part, whole):\n    return round(100 * part / whole, 1)\n",
        trap="def percent(part, whole):\n    return round(100 * part // whole, 1)\n",
        note="/ keeps the fraction and // throws it away, so 100 * 1 // 3"
             " is 33, not 33.3. The multiplication by 100 before the"
             " division keeps the arithmetic simple; round(..., 1) then"
             " trims to one decimal. 100 * 7 / 7 is 100.0, a float, which"
             " the grader treats as equal to 100.",
    ),
    dict(
        id=4, ledger="P119", concept="PY3 min max", tier="1 - Numbers",
        title="min() and max(): keep a value in range", kind="function",
        func="clamp",
        cases=[(5, 0, 10), (-3, 0, 10), (42, 0, 10), (10, 0, 10)],
        prompt=(
            "Write a function `clamp(x, lo, hi)` that returns x if it is"
            " between lo and hi, lo if it is below, and hi if it is above,"
            " using min() and max() rather than an if:\n\n"
            "  clamp(42, 0, 10) -> 10\n\n"
            "Return: the clamped value."
        ),
        solution="def clamp(x, lo, hi):\n    return min(hi, max(lo, x))\n",
        trap="def clamp(x, lo, hi):\n    return max(hi, min(lo, x))\n",
        note="max(lo, x) lifts x up to lo if it is too low; min(hi, ...)"
             " then brings it down to hi if it is too high. The other way"
             " round -- min(lo, x) first -- pins everything to lo and then"
             " max(hi, ...) pins it to hi, so every input returns hi."
             " Read it inside out: the inner call runs first.",
    ),
    # ============================================================== 2 Strings
    dict(
        id=5, ledger="P120", concept="PY3 startswith", tier="2 - Strings",
        title="startswith(): does it begin with", kind="function",
        func="has_prefix",
        cases=[("SRG-04", "SRG"), ("DIA-01", "SRG"), ("SRG-04", "RG"), ("", "a"), ("abc", "")],
        prompt=(
            "Write a function `has_prefix(text, prefix)` that returns True"
            " if text begins with prefix and False otherwise, using"
            " startswith():\n\n"
            "  has_prefix(\"SRG-04\", \"SRG\") -> True\n\n"
            "Return: True or False."
        ),
        solution="def has_prefix(text, prefix):\n    return text.startswith(prefix)\n",
        trap="def has_prefix(text, prefix):\n    return prefix in text\n",
        note="in asks whether prefix appears ANYWHERE in text; startswith()"
             " asks about the beginning only, so 'RG' in 'SRG-04' is True"
             " where has_prefix should be False. Every string starts with"
             " the empty string, so the last case is True. endswith() is"
             " the mirror.",
    ),
    dict(
        id=6, ledger="P121", concept="PY3 title", tier="2 - Strings",
        title="title(): a capital on each word", kind="function",
        func="tidy_name",
        cases=[("florence nightingale",), ("MARY SEACOLE",), ("ada",)],
        prompt=(
            "Write a function `tidy_name(name)` that returns the name with"
            " the first letter of each word in capitals and the rest in"
            " lower case, using title():\n\n"
            "  tidy_name(\"MARY SEACOLE\") -> \"Mary Seacole\"\n\n"
            "Return: the tidied string."
        ),
        solution="def tidy_name(name):\n    return name.title()\n",
        trap="def tidy_name(name):\n    return name.capitalize()\n",
        note="title() capitalises every word and lower-cases the rest of"
             " each; capitalize() does only the first letter of the whole"
             " string, giving 'Mary seacole'. Both return a new string and"
             " leave name alone.",
    ),
    dict(
        id=7, ledger="P122", concept="PY3 count", tier="2 - Strings",
        title="count(): how many of one letter", kind="function",
        func="letters",
        cases=[("observation", "o"), ("Observation", "o"), ("rhythm", "e")],
        prompt=(
            "Write a function `letters(text, ch)` that returns how many"
            " times the character ch appears in text, case-sensitive,"
            " using the string's count() method:\n\n"
            "  letters(\"observation\", \"o\") -> 2\n\n"
            "Return: the count, 0 when absent."
        ),
        solution="def letters(text, ch):\n    return text.count(ch)\n",
        trap="def letters(text, ch):\n    return text.find(ch)\n",
        note="count() counts occurrences; find() returns the POSITION of"
             " the first one, or -1, which happens to look plausible on"
             " small inputs. 'Observation' with a capital O has one lower"
             " o, because count() is case-sensitive; lower() the text"
             " first if case should not matter.",
    ),
    dict(
        id=8, ledger="P123", concept="PY3 split last", tier="2 - Strings",
        title="split()[-1]: the last word", kind="function",
        func="last_word",
        cases=[("the ward round starts at nine",), ("single",), ("  padded words  ",)],
        prompt=(
            "Write a function `last_word(text)` that returns the last word"
            " of a non-empty sentence, using split() and a negative"
            " index:\n\n"
            "  last_word(\"the ward round starts at nine\") -> \"nine\"\n\n"
            "Return: the word."
        ),
        solution="def last_word(text):\n    return text.split()[-1]\n",
        trap="def last_word(text):\n    return text[-1]\n",
        note="text[-1] is the last CHARACTER, 'e'. split() turns the text"
             " into a list of words, and [-1] on that list is the last"
             " word. With no argument split() ignores leading and trailing"
             " spaces, so the padded case still gives 'words'.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=9, ledger="P124", concept="PY3 min key", tier="3 - Lists",
        title="min(key=len): the shortest", kind="function",
        func="shortest",
        cases=[(["Nightingale", "Barry", "Bevan"],), (["aa", "b", "cc"],), (["only"],)],
        prompt=(
            "Write a function `shortest(words)` that returns the shortest"
            " word in a non-empty list, the first of them on a tie, using"
            " min() with key=len:\n\n"
            "  shortest([\"Nightingale\", \"Barry\", \"Bevan\"]) -> \"Barry\"\n\n"
            "Return: the word."
        ),
        solution="def shortest(words):\n    return min(words, key=len)\n",
        trap="def shortest(words):\n    return min(words)\n",
        note="min(words) compares the strings alphabetically and returns"
             " 'Barry' here by coincidence -- on ['aa', 'b', 'cc'] it"
             " returns 'aa'. key=len compares by length and returns the"
             " word; on a tie min() keeps the first it met.",
    ),
    dict(
        id=10, ledger="P125", concept="PY3 sorted key", tier="3 - Lists",
        title="sorted(key=len): shortest to longest", kind="function",
        func="by_length",
        cases=[(["Nightingale", "Barry", "Jenner"],), (["Zed", "ab", "Mo"],), ([],)],
        prompt=(
            "Write a function `by_length(words)` that returns a new list"
            " of the words ordered from shortest to longest, using"
            " sorted() with key=len:\n\n"
            "  by_length([\"Nightingale\", \"Barry\", \"Jenner\"]) ->"
            " [\"Barry\", \"Jenner\", \"Nightingale\"]\n\n"
            "Return: the sorted list."
        ),
        solution="def by_length(words):\n    return sorted(words, key=len)\n",
        trap="def by_length(words):\n    return sorted(words)\n",
        note="sorted(words) orders alphabetically; key=len says order by"
             " the length instead and leaves the words themselves in the"
             " result. The key is a function applied to each item, not"
             " called -- len, not len(). sorted() returns a new list and"
             " does not change the one passed in.",
    ),
    dict(
        id=11, ledger="P126", concept="PY3 index", tier="3 - Lists",
        title="index(): where in the list", kind="function",
        func="position",
        cases=[(["Barry", "Bevan", "Cavell"], "Bevan"), ([3, 1, 4, 1], 1), (["x"], "x")],
        prompt=(
            "Write a function `position(items, value)` that returns the"
            " index of the first occurrence of value in the list, which is"
            " always present, using the list's index() method:\n\n"
            "  position([\"Barry\", \"Bevan\", \"Cavell\"], \"Bevan\") -> 1\n\n"
            "Return: an index, counting from 0."
        ),
        solution="def position(items, value):\n    return items.index(value)\n",
        trap="def position(items, value):\n    return items.index(value) + 1\n",
        note="Positions count from 0 in Python, so the second item is at"
             " 1 -- adding 1 to make it 'human' puts the answer out of"
             " step with every other index in the language. index() finds"
             " the FIRST match, which is 1 in [3, 1, 4, 1], and raises"
             " ValueError if the value is absent.",
    ),
    dict(
        id=12, ledger="P127", concept="PY3 filter comprehension", tier="3 - Lists",
        title="[x for x in ... if ...]: everything but one value", kind="function",
        func="without",
        cases=[(["day", "night", "day"], "day"), ([1, 2, 3], 4), ([],  "x")],
        prompt=(
            "Write a function `without(items, value)` that returns a new"
            " list with every occurrence of value removed, in one"
            " comprehension:\n\n"
            "  without([\"day\", \"night\", \"day\"], \"day\") -> [\"night\"]\n\n"
            "Return: the new list."
        ),
        solution="def without(items, value):\n    return [x for x in items if x != value]\n",
        trap="def without(items, value):\n    items.remove(value)\n    return items\n",
        note="remove() takes out only the FIRST match, raises ValueError if"
             " there is none, and changes the caller's list. The"
             " comprehension builds a new list of the items that are not"
             " the value, handling zero matches and many matches the same"
             " way.",
    ),
    dict(
        id=13, ledger="P128", concept="PY3 reverse slice", tier="3 - Lists",
        title="[::-1]: back to front", kind="function",
        func="backwards",
        cases=[([1, 2, 3],), (["a"],), ([],)],
        prompt=(
            "Write a function `backwards(items)` that returns a NEW list"
            " with the items in reverse order, using a slice with a step"
            " of -1:\n\n"
            "  backwards([1, 2, 3]) -> [3, 2, 1]\n\n"
            "Return: the reversed list."
        ),
        solution="def backwards(items):\n    return items[::-1]\n",
        trap="def backwards(items):\n    return items.reverse()\n",
        note="reverse() reverses the list in place and returns None, so"
             " returning its result returns None. items[::-1] is a slice"
             " from end to start, a new list, leaving the original alone."
             " reversed(items) is a third form, which gives an iterator"
             " you would wrap in list().",
    ),
    # ========================================================== 4 Membership
    dict(
        id=14, ledger="P129", concept="PY3 in", tier="4 - Membership and pairs",
        title="in: is it there", kind="function",
        func="contains",
        cases=[(["Morphine", "Codeine"], "Codeine"), (["Morphine"], "codeine"), ([], "x")],
        prompt=(
            "Write a function `contains(items, value)` that returns True"
            " if value is in the list and False otherwise, using the in"
            " operator:\n\n"
            "  contains([\"Morphine\", \"Codeine\"], \"Codeine\") -> True\n\n"
            "Return: True or False."
        ),
        solution="def contains(items, value):\n    return value in items\n",
        trap="def contains(items, value):\n    return items.count(value)\n",
        note="`value in items` is already a boolean, so it can be returned"
             " as it is. count() returns a NUMBER -- 1 or 0 -- and the"
             " grader, like a caller comparing with True, tells them apart."
             " in compares with ==, so case has to match.",
    ),
    dict(
        id=15, ledger="P130", concept="PY3 dict zip", tier="4 - Membership and pairs",
        title="dict(zip()): two lists into a dictionary", kind="function",
        func="pair_up",
        cases=[(["Fleming", "Barry"], [16, 30]), ([], []), (["a"], [1])],
        prompt=(
            "Write a function `pair_up(keys, values)` that returns a"
            " dictionary mapping each key to the value at the same"
            " position, using dict() over zip():\n\n"
            "  pair_up([\"Fleming\", \"Barry\"], [16, 30]) -> {\"Fleming\": 16,"
            " \"Barry\": 30}\n\n"
            "Return: the dictionary."
        ),
        solution="def pair_up(keys, values):\n    return dict(zip(keys, values))\n",
        trap="def pair_up(keys, values):\n    return list(zip(keys, values))\n",
        note="zip() pairs the lists position by position; dict() turns"
             " pairs into a dictionary, and list() turns them into a list"
             " of tuples -- the right pairs in the wrong container. Two"
             " parallel lists into a lookup is what dict(zip(...)) is for.",
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
