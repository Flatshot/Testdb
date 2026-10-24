"""Python practice exercises: fifteen functions, one simple loop each.

The twenty-second Python set, the fifth of single loops: every question
asks for a function built around ONE for or while loop over plain numbers
or strings -- counting, searching, building, reducing -- with no import
and no row-shaped data. The loop body is an if, an accumulator, or both.
The title names the task; the prompt says which kind of loop and what it
keeps track of.

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
    # ======================================================== 1 Counting
    dict(
        id=1, ledger="P326", concept="PY4 for count isupper", tier="1 - Counting",
        title="How many capital letters", kind="function",
        func="count_upper",
        cases=[("The Glass Path",), ("leeds",), ("LS15",), ("",)],
        prompt=(
            "Write a function `count_upper(s)` that returns how many"
            " characters of s are upper-case letters. A for loop over the"
            " characters, an if on ch.isupper(), and a counter.\n\n"
            "  count_upper(\"The Glass Path\") -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def count_upper(s):\n"
                  "    n = 0\n"
                  "    for ch in s:\n"
                  "        if ch.isupper():\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_upper(s):\n"
              "    n = 0\n"
              "    for ch in s:\n"
              "        if ch == ch.upper():\n"
              "            n += 1\n"
              "    return n\n"),
        note="isupper() is True only for a cased character that is upper"
             " case; ch == ch.upper() is also True for digits and spaces,"
             " which are unchanged by upper(), so 'LS15' counts 4 and the"
             " spaces in a title are counted too.",
    ),
    dict(
        id=2, ledger="P327", concept="PY4 for range odd sum", tier="1 - Counting",
        title="The sum of the odd numbers below n", kind="function",
        func="sum_odds_below",
        cases=[(10,), (1,), (0,), (7,)],
        prompt=(
            "Write a function `sum_odds_below(n)` that returns the sum of"
            " the odd whole numbers that are less than n. A for loop over"
            " range(n) with an if on i % 2 == 1 and a running total.\n\n"
            "  sum_odds_below(10) -> 25\n\n"
            "Return: an integer."
        ),
        solution=("def sum_odds_below(n):\n"
                  "    total = 0\n"
                  "    for i in range(n):\n"
                  "        if i % 2 == 1:\n"
                  "            total += i\n"
                  "    return total\n"),
        trap=("def sum_odds_below(n):\n"
              "    total = 0\n"
              "    for i in range(n + 1):\n"
              "        if i % 2 == 1:\n"
              "            total += i\n"
              "    return total\n"),
        note="'Below n' means n itself is excluded, and range(n) stops"
             " before n -- exactly right for once. range(n + 1) reaches n,"
             " so for an odd n the answer is too big: 16 instead of 9 for"
             " n = 7.",
    ),
    dict(
        id=3, ledger="P328", concept="PY4 for count true", tier="1 - Counting",
        title="How many are True", kind="function",
        func="count_true",
        cases=[([True, False, True],), ([],), ([False],), ([True, True, True],)],
        prompt=(
            "Write a function `count_true(flags)` that returns how many"
            " items in a list of booleans are True. A for loop with an if"
            " on the flag itself -- if flag: -- and a counter.\n\n"
            "  count_true([True, False, True]) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_true(flags):\n"
                  "    n = 0\n"
                  "    for f in flags:\n"
                  "        if f:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_true(flags):\n"
              "    n = 0\n"
              "    for f in flags:\n"
              "        if f == \"True\":\n"
              "            n += 1\n"
              "    return n\n"),
        note="A boolean is its own condition: 'if f:' is the whole test."
             " Comparing with the STRING 'True' is never true for a real"
             " boolean, so the trap counts nothing. sum(flags) would do"
             " the same in one call, because True adds as 1.",
    ),
    dict(
        id=4, ledger="P329", concept="PY4 for contains count", tier="1 - Counting",
        title="Words that contain a letter", kind="function",
        func="count_containing",
        cases=[(["pen", "paper", "ink"], "p"), ([], "a"), (["Paper"], "p"), (["aa", "b"], "a")],
        prompt=(
            "Write a function `count_containing(words, letter)` that"
            " returns how many words contain the letter at least once,"
            " case-sensitively. A for loop with an if on letter in w and"
            " a counter.\n\n"
            "  count_containing([\"pen\", \"paper\", \"ink\"], \"p\") -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_containing(words, letter):\n"
                  "    n = 0\n"
                  "    for w in words:\n"
                  "        if letter in w:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_containing(words, letter):\n"
              "    n = 0\n"
              "    for w in words:\n"
              "        n += w.count(letter)\n"
              "    return n\n"),
        note="'in' asks whether the letter is there at all, once per"
             " word; count() adds up every occurrence, so 'paper' adds 2"
             " and 'aa' adds 2 where the question wants 1. Case-sensitive"
             " means 'Paper' does not contain 'p' -- it contains 'P'.",
    ),
    # ========================================================= 2 Searching
    dict(
        id=5, ledger="P330", concept="PY4 for index of max", tier="2 - Searching",
        title="Where the largest value is", kind="function",
        func="index_of_max",
        cases=[([3, 9, 2, 9],), ([1],), ([-4, -2, -8],), ([5, 5],)],
        prompt=(
            "Write a function `index_of_max(values)` that returns the"
            " POSITION of the largest value in a non-empty list, the"
            " first such position if it appears more than once. A for"
            " loop over range(1, len(values)) that remembers the best"
            " position so far, starting at 0.\n\n"
            "  index_of_max([3, 9, 2, 9]) -> 1\n\n"
            "Return: an integer."
        ),
        solution=("def index_of_max(values):\n"
                  "    best = 0\n"
                  "    for i in range(1, len(values)):\n"
                  "        if values[i] > values[best]:\n"
                  "            best = i\n"
                  "    return best\n"),
        trap=("def index_of_max(values):\n"
              "    best = 0\n"
              "    for i in range(1, len(values)):\n"
              "        if values[i] >= values[best]:\n"
              "            best = i\n"
              "    return best\n"),
        note="The strict > keeps the FIRST of equal maxima; with >= a"
             " later equal value takes over, and [3, 9, 2, 9] answers 3"
             " instead of 1. Tracking an index means comparing values[i]"
             " with values[best], not with best itself.",
    ),
    dict(
        id=6, ledger="P331", concept="PY4 for any check", tier="2 - Searching",
        title="Is any of them negative?", kind="function",
        func="any_negative",
        cases=[([1, -2, 3],), ([1, 2],), ([],), ([-1],)],
        prompt=(
            "Write a function `any_negative(values)` that returns True"
            " when at least one value is below zero, and False otherwise"
            " -- including for an empty list. A for loop that returns"
            " True at the first negative value, then False after the"
            " loop. Do not use any() for this one.\n\n"
            "  any_negative([1, -2, 3]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def any_negative(values):\n"
                  "    for v in values:\n"
                  "        if v < 0:\n"
                  "            return True\n"
                  "    return False\n"),
        trap=("def any_negative(values):\n"
              "    for v in values:\n"
              "        if v < 0:\n"
              "            return True\n"
              "        else:\n"
              "            return False\n"),
        note="'Any' is proved by finding one example, so the loop returns"
             " True as soon as it sees one and False only after looking"
             " at them all. An else that returns False inside the loop"
             " gives up after the FIRST value, so [1, -2, 3] is answered"
             " False.",
    ),
    dict(
        id=7, ledger="P332", concept="PY4 for last match", tier="2 - Searching",
        title="The last word longer than n", kind="function",
        func="last_long_word",
        cases=[(["pen", "paper", "ink", "notebook", "map"], 3), (["a", "b"], 1), ([], 3), (["four"], 3)],
        prompt=(
            "Write a function `last_long_word(words, n)` that returns the"
            " LAST word with more than n characters, or None if there is"
            " none. A for loop that records each match in a variable and"
            " returns it after the loop.\n\n"
            "  last_long_word([\"pen\", \"paper\", \"ink\", \"notebook\","
            " \"map\"], 3) -> \"notebook\"\n\n"
            "Return: the word, or None."
        ),
        solution=("def last_long_word(words, n):\n"
                  "    found = None\n"
                  "    for w in words:\n"
                  "        if len(w) > n:\n"
                  "            found = w\n"
                  "    return found\n"),
        trap=("def last_long_word(words, n):\n"
              "    for w in words:\n"
              "        if len(w) > n:\n"
              "            return w\n"
              "    return None\n"),
        note="To find the LAST match the loop has to keep going past the"
             " first one, overwriting a variable each time and returning"
             " it at the end. A return inside the loop gives the FIRST"
             " match, 'paper'. Starting the variable at None covers the"
             " no-match case without a flag.",
    ),
    dict(
        id=8, ledger="P333", concept="PY4 for closest", tier="2 - Searching",
        title="The value nearest a target", kind="function",
        func="nearest_to",
        cases=[([3, 9, 14], 10), ([1, 5], 3), ([7], 0), ([10, 20], 15)],
        prompt=(
            "Write a function `nearest_to(values, target)` that returns"
            " the value in a non-empty list closest to target -- the"
            " FIRST such value when two are equally close. A for loop"
            " with a best so far that starts at values[0] and is replaced"
            " when abs(v - target) is strictly smaller than abs(best -"
            " target).\n\n"
            "  nearest_to([3, 9, 14], 10) -> 9\n\n"
            "Return: the value."
        ),
        solution=("def nearest_to(values, target):\n"
                  "    best = values[0]\n"
                  "    for v in values:\n"
                  "        if abs(v - target) < abs(best - target):\n"
                  "            best = v\n"
                  "    return best\n"),
        trap=("def nearest_to(values, target):\n"
              "    best = values[0]\n"
              "    for v in values:\n"
              "        if v - target < best - target:\n"
              "            best = v\n"
              "    return best\n"),
        note="Distance is the ABSOLUTE difference: without abs() the"
             " comparison prefers the most negative difference, which is"
             " the smallest value, not the nearest. The strict < keeps"
             " the first of two equally close values, 10 rather than 20"
             " for a target of 15.",
    ),
    # ========================================================== 3 Building
    dict(
        id=9, ledger="P334", concept="PY4 for squares list", tier="3 - Building",
        title="The first n squares", kind="function",
        func="squares",
        cases=[(5,), (1,), (0,), (3,)],
        prompt=(
            "Write a function `squares(n)` that returns the list of the"
            " squares of 1 to n. A for loop over range(1, n + 1) that"
            " appends i * i.\n\n"
            "  squares(5) -> [1, 4, 9, 16, 25]\n\n"
            "Return: the list."
        ),
        solution=("def squares(n):\n"
                  "    out = []\n"
                  "    for i in range(1, n + 1):\n"
                  "        out.append(i * i)\n"
                  "    return out\n"),
        trap=("def squares(n):\n"
              "    out = []\n"
              "    for i in range(1, n + 1):\n"
              "        out.append(i * 2)\n"
              "    return out\n"),
        note="i * i is the square; i * 2 is the double, and the two agree"
             " only at i = 2. range(1, n + 1) gives 1 to n inclusive, and"
             " for n = 0 an empty list.",
    ),
    dict(
        id=10, ledger="P335", concept="PY4 for build initials", tier="3 - Building",
        title="Initials, built up by loop", kind="function",
        func="initials",
        cases=[(["Aisha", "Ekwueme"],), ([],), (["x"],), (["Old", "Town", "Branch"],)],
        prompt=(
            "Write a function `initials(words)` that returns a string of"
            " the first character of each word, in order. A for loop that"
            " adds w[0] to a result string that starts empty. Every word"
            " has at least one character.\n\n"
            "  initials([\"Aisha\", \"Ekwueme\"]) -> \"AE\"\n\n"
            "Return: the string."
        ),
        solution=("def initials(words):\n"
                  "    out = \"\"\n"
                  "    for w in words:\n"
                  "        out += w[0]\n"
                  "    return out\n"),
        trap=("def initials(words):\n"
              "    out = \"\"\n"
              "    for w in words:\n"
              "        out += w[1]\n"
              "    return out\n"),
        note="Positions start at 0, so the first character is w[0]; w[1]"
             " is the second, and fails outright on a one-letter word."
             " A string grows with += just as a list grows with append.",
    ),
    dict(
        id=11, ledger="P336", concept="PY4 for repeat each", tier="3 - Building",
        title="Each item twice", kind="function",
        func="repeat_each",
        cases=[([1, 2, 3],), ([],), (["a"],), ([0, 0],)],
        prompt=(
            "Write a function `repeat_each(values)` that returns a new"
            " list with every item appearing twice in a row. A for loop"
            " that appends each item two times.\n\n"
            "  repeat_each([1, 2, 3]) -> [1, 1, 2, 2, 3, 3]\n\n"
            "Return: the new list."
        ),
        solution=("def repeat_each(values):\n"
                  "    out = []\n"
                  "    for v in values:\n"
                  "        out.append(v)\n"
                  "        out.append(v)\n"
                  "    return out\n"),
        trap=("def repeat_each(values):\n"
              "    out = []\n"
              "    for v in values:\n"
              "        out.append(v)\n"
              "    return out + out\n"),
        note="Two appends inside the loop put the copies NEXT to each"
             " other; building the list once and adding it to itself"
             " gives [1, 2, 3, 1, 2, 3], the same items in a different"
             " order. Order is part of the answer.",
    ),
    dict(
        id=12, ledger="P337", concept="PY4 while step down", tier="3 - Building",
        title="Counting down in steps", kind="function",
        func="countdown_by",
        cases=[(10, 3), (5, 5), (4, 10), (9, 4)],
        prompt=(
            "Write a function `countdown_by(n, step)` that returns the"
            " list n, n - step, n - 2 * step, ... for as long as the value"
            " stays above zero. A while loop on n > 0 that appends n and"
            " then subtracts step.\n\n"
            "  countdown_by(10, 3) -> [10, 7, 4, 1]\n\n"
            "Return: the list."
        ),
        solution=("def countdown_by(n, step):\n"
                  "    out = []\n"
                  "    while n > 0:\n"
                  "        out.append(n)\n"
                  "        n -= step\n"
                  "    return out\n"),
        trap=("def countdown_by(n, step):\n"
              "    out = []\n"
              "    while n > 0:\n"
              "        n -= step\n"
              "        out.append(n)\n"
              "    return out\n"),
        note="The order of the two lines inside the loop decides which"
             " values are recorded: append first and n itself is the"
             " first item; subtract first and the list starts at n - step"
             " and ends with a value at or below zero.",
    ),
    # ========================================================== 4 Reducing
    dict(
        id=13, ledger="P338", concept="PY4 for max gap", tier="4 - Reducing",
        title="The biggest jump between neighbours", kind="function",
        func="max_gap",
        cases=[([1, 4, 9, 11],), ([5],), ([],), ([10, 2, 7],)],
        prompt=(
            "Write a function `max_gap(values)` that returns the largest"
            " absolute difference between two neighbouring values, 0 for"
            " a list of fewer than two. A for loop over range(1,"
            " len(values)) comparing abs(values[i] - values[i - 1]) with"
            " a best so far that starts at 0.\n\n"
            "  max_gap([1, 4, 9, 11]) -> 5\n\n"
            "Return: the gap."
        ),
        solution=("def max_gap(values):\n"
                  "    best = 0\n"
                  "    for i in range(1, len(values)):\n"
                  "        gap = abs(values[i] - values[i - 1])\n"
                  "        if gap > best:\n"
                  "            best = gap\n"
                  "    return best\n"),
        trap=("def max_gap(values):\n"
              "    best = 0\n"
              "    for i in range(1, len(values)):\n"
              "        gap = values[i] - values[i - 1]\n"
              "        if gap > best:\n"
              "            best = gap\n"
              "    return best\n"),
        note="A downward step is still a gap, so the difference needs"
             " abs(): without it [10, 2, 7] reports 5 for the rise and"
             " ignores the fall of 8. Starting best at 0 handles the"
             " short lists, where the loop never runs.",
    ),
    dict(
        id=14, ledger="P339", concept="PY4 for digits in text", tier="4 - Reducing",
        title="The digits in a string, added up", kind="function",
        func="sum_digits_in",
        cases=[("LS15",), ("2026-06-30",), ("Leeds",), ("",)],
        prompt=(
            "Write a function `sum_digits_in(s)` that returns the sum of"
            " the digit characters in s, 0 if there are none. A for loop"
            " over the characters with an if on ch.isdigit() that adds"
            " int(ch) to a total.\n\n"
            "  sum_digits_in(\"LS15\") -> 6\n\n"
            "Return: an integer."
        ),
        solution=("def sum_digits_in(s):\n"
                  "    total = 0\n"
                  "    for ch in s:\n"
                  "        if ch.isdigit():\n"
                  "            total += int(ch)\n"
                  "    return total\n"),
        trap=("def sum_digits_in(s):\n"
              "    total = 0\n"
              "    for ch in s:\n"
              "        if ch.isdigit():\n"
              "            total += 1\n"
              "    return total\n"),
        note="int(ch) turns the digit character into its value; adding 1"
             " instead counts the digits, 2 for 'LS15' rather than 6."
             " The isdigit() guard is what lets int() be called safely.",
    ),
    dict(
        id=15, ledger="P340", concept="PY4 for running check", tier="4 - Reducing",
        title="Does the balance ever go below zero?", kind="function",
        func="stays_positive",
        cases=[([10, -3, -5, 2],), ([10, -20, 15],), ([],), ([-1],)],
        prompt=(
            "Write a function `stays_positive(changes)` that returns True"
            " when a balance starting at zero never drops below zero as"
            " the changes are applied in order, and False as soon as it"
            " does. A for loop with a running total and a return of False"
            " inside it, then True after the loop.\n\n"
            "  stays_positive([10, -20, 15]) -> False\n\n"
            "Return: True or False."
        ),
        solution=("def stays_positive(changes):\n"
                  "    total = 0\n"
                  "    for c in changes:\n"
                  "        total += c\n"
                  "        if total < 0:\n"
                  "            return False\n"
                  "    return True\n"),
        trap=("def stays_positive(changes):\n"
              "    total = 0\n"
              "    for c in changes:\n"
              "        total += c\n"
              "    return total >= 0\n"),
        note="The question is about every point along the way, not the"
             " end: [10, -20, 15] finishes at 5 but dipped to -10 in the"
             " middle. Checking inside the loop catches the dip; checking"
             " only the final total misses it.",
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
