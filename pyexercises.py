"""Python practice exercises: fourteen single-loop functions and FizzBuzz.

The twentieth Python set, the third of single loops: fourteen functions
each built around ONE for or while loop over plain numbers or strings --
counting, searching, building, reducing -- with no import and no
row-shaped data, and one PROGRAM: the classic FizzBuzz, printed, graded on
its output. The title names the task; the prompt says which kind of loop
and what it keeps track of.

Two kinds of question, told apart by `kind`:

  "program"   the editor holds a whole program, graded on what it prints.
              FizzBuzz is the one of these in this set.
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
        id=1, ledger="P296", concept="PY4 for count if", tier="1 - Counting",
        title="How many are negative", kind="function",
        func="count_negatives",
        cases=[([3, -1, -4, 0, 5],), ([],), ([0, 0],), ([-2],)],
        prompt=(
            "Write a function `count_negatives(values)` that returns how"
            " many values are below zero. A for loop with an if on"
            " v < 0 and a counter; zero itself is not negative.\n\n"
            "  count_negatives([3, -1, -4, 0, 5]) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_negatives(values):\n"
                  "    n = 0\n"
                  "    for v in values:\n"
                  "        if v < 0:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_negatives(values):\n"
              "    n = 0\n"
              "    for v in values:\n"
              "        if v <= 0:\n"
              "            n += 1\n"
              "    return n\n"),
        note="Negative means strictly below zero, so the test is <; with"
             " <= every 0 is counted too and [0, 0] gives 2. The counting"
             " loop is the same shape every time: start at 0, add one"
             " under an if.",
    ),
    dict(
        id=2, ledger="P297", concept="PY4 for sum if", tier="1 - Counting",
        title="The sum of the even numbers", kind="function",
        func="sum_even",
        cases=[([1, 2, 3, 4, 5, 6],), ([],), ([1, 3],), ([-2, 2],)],
        prompt=(
            "Write a function `sum_even(values)` that returns the total"
            " of the even values only. A for loop with an if on"
            " v % 2 == 0 and a running total.\n\n"
            "  sum_even([1, 2, 3, 4, 5, 6]) -> 12\n\n"
            "Return: the total."
        ),
        solution=("def sum_even(values):\n"
                  "    total = 0\n"
                  "    for v in values:\n"
                  "        if v % 2 == 0:\n"
                  "            total += v\n"
                  "    return total\n"),
        trap=("def sum_even(values):\n"
              "    total = 0\n"
              "    for v in values:\n"
              "        if v % 2 == 1:\n"
              "            total += v\n"
              "    return total\n"),
        note="v % 2 is 0 for an even number, including negative ones; the"
             " trap sums the odd values instead. An empty list, or one"
             " with no even values, totals 0 because the total never"
             " moves from where it started.",
    ),
    dict(
        id=3, ledger="P298", concept="PY4 for count until", tier="1 - Counting",
        title="How many come before the stop value", kind="function",
        func="count_before",
        cases=[(["a", "b", "stop", "c"], "stop"), (["x", "y"], "stop"), ([], "stop"), (["stop"], "stop")],
        prompt=(
            "Write a function `count_before(values, stop)` that returns"
            " how many items come before the first one equal to stop --"
            " all of them when stop never appears. A for loop that breaks"
            " at the stop value and counts otherwise.\n\n"
            "  count_before([\"a\", \"b\", \"stop\", \"c\"], \"stop\") -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_before(values, stop):\n"
                  "    n = 0\n"
                  "    for v in values:\n"
                  "        if v == stop:\n"
                  "            break\n"
                  "        n += 1\n"
                  "    return n\n"),
        trap=("def count_before(values, stop):\n"
              "    n = 0\n"
              "    for v in values:\n"
              "        if v != stop:\n"
              "            n += 1\n"
              "    return n\n"),
        note="break ends the loop at the stop value; an if that merely"
             " skips it keeps counting the items after it, so 'c' is"
             " counted and the answer is 3. The test comes before the"
             " increment, so the stop value itself is not counted.",
    ),
    dict(
        id=4, ledger="P299", concept="PY4 for startswith count", tier="1 - Counting",
        title="Words that start with a letter", kind="function",
        func="count_starting",
        cases=[(["Beyond", "Bright", "Dark", "blue"], "B"), ([], "B"), (["ABC", "Bb"], "B"), (["b"], "B")],
        prompt=(
            "Write a function `count_starting(words, letter)` that"
            " returns how many words start with the given letter,"
            " case-sensitively. A for loop with an if on"
            " w.startswith(letter) and a counter.\n\n"
            "  count_starting([\"Beyond\", \"Bright\", \"Dark\", \"blue\"],"
            " \"B\") -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_starting(words, letter):\n"
                  "    n = 0\n"
                  "    for w in words:\n"
                  "        if w.startswith(letter):\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_starting(words, letter):\n"
              "    n = 0\n"
              "    for w in words:\n"
              "        if letter in w:\n"
              "            n += 1\n"
              "    return n\n"),
        note="startswith() looks at the front only; 'in' finds the letter"
             " anywhere, so 'Bb' and words with a B in the middle would"
             " count. The question says case-sensitive, so 'blue' is not"
             " counted for 'B'.",
    ),
    # ========================================================= 2 Searching
    dict(
        id=5, ledger="P300", concept="PY4 for max no builtin", tier="2 - Searching",
        title="The largest value, by hand", kind="function",
        func="largest",
        cases=[([3, 9, 2],), ([-5, -1, -7],), ([4],), ([1, 1, 1],)],
        prompt=(
            "Write a function `largest(values)` that returns the biggest"
            " value in a non-empty list WITHOUT using max(). Start a best"
            " at values[0], then a for loop that replaces it whenever a"
            " value is bigger.\n\n"
            "  largest([-5, -1, -7]) -> -1\n\n"
            "Return: the value."
        ),
        solution=("def largest(values):\n"
                  "    best = values[0]\n"
                  "    for v in values:\n"
                  "        if v > best:\n"
                  "            best = v\n"
                  "    return best\n"),
        trap=("def largest(values):\n"
              "    best = 0\n"
              "    for v in values:\n"
              "        if v > best:\n"
              "            best = v\n"
              "    return best\n"),
        note="Starting the best at 0 assumes something positive is in"
             " the list, and [-5, -1, -7] comes back as 0 -- a value"
             " that is not even there. Starting from values[0] makes no"
             " assumption, which is why the question says the list is"
             " non-empty.",
    ),
    dict(
        id=6, ledger="P301", concept="PY4 for all check", tier="2 - Searching",
        title="Are they all positive?", kind="function",
        func="all_positive",
        cases=[([1, 2, 3],), ([1, 0, 3],), ([],), ([5, -1],)],
        prompt=(
            "Write a function `all_positive(values)` that returns True"
            " when every value is above zero -- and True for an empty"
            " list, since nothing fails. A for loop that returns False at"
            " the first value that is not positive, then True after the"
            " loop. Do not use all() for this one.\n\n"
            "  all_positive([1, 0, 3]) -> False\n\n"
            "Return: True or False."
        ),
        solution=("def all_positive(values):\n"
                  "    for v in values:\n"
                  "        if v <= 0:\n"
                  "            return False\n"
                  "    return True\n"),
        trap=("def all_positive(values):\n"
              "    for v in values:\n"
              "        if v > 0:\n"
              "            return True\n"
              "    return False\n"),
        note="'All' is proved by failing to find a counter-example, so"
             " the loop looks for a value that is NOT positive and"
             " returns False when it finds one; True is only reached"
             " after the loop. Returning True at the first positive value"
             " answers 'any positive?' instead, and says [1, 0, 3] is all"
             " positive.",
    ),
    dict(
        id=7, ledger="P302", concept="PY4 for first match len", tier="2 - Searching",
        title="The first long word", kind="function",
        func="first_long_word",
        cases=[(["pen", "ink", "paper", "notebook"], 4), (["a", "b"], 1), ([], 3), (["four"], 4)],
        prompt=(
            "Write a function `first_long_word(words, n)` that returns"
            " the first word with MORE than n characters, or None if"
            " there is none. A for loop with an if on len(w) > n and a"
            " return inside it.\n\n"
            "  first_long_word([\"pen\", \"ink\", \"paper\", \"notebook\"],"
            " 4) -> \"paper\"\n\n"
            "Return: the word, or None."
        ),
        solution=("def first_long_word(words, n):\n"
                  "    for w in words:\n"
                  "        if len(w) > n:\n"
                  "            return w\n"
                  "    return None\n"),
        trap=("def first_long_word(words, n):\n"
              "    for w in words:\n"
              "        if len(w) >= n:\n"
              "            return w\n"
              "    return None\n"),
        note="More than n is a strict >, so a four-letter word is not"
             " long for n = 4 and 'four' gives None. The return inside"
             " the loop stops at the first match; the None after it is"
             " the answer when the loop finishes without one.",
    ),
    dict(
        id=8, ledger="P303", concept="PY4 for last index", tier="2 - Searching",
        title="Where a value LAST appears", kind="function",
        func="last_position_of",
        cases=[(7, [3, 7, 9, 7]), (2, [3, 7]), ("a", ["a", "b", "a", "c"]), (1, [])],
        prompt=(
            "Write a function `last_position_of(target, values)` that"
            " returns the index of the LAST occurrence of target, or -1"
            " if it is absent. A for loop over range(len(values)) that"
            " records the index each time it matches and returns the"
            " record after the loop.\n\n"
            "  last_position_of(7, [3, 7, 9, 7]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def last_position_of(target, values):\n"
                  "    found = -1\n"
                  "    for i in range(len(values)):\n"
                  "        if values[i] == target:\n"
                  "            found = i\n"
                  "    return found\n"),
        trap=("def last_position_of(target, values):\n"
              "    for i in range(len(values)):\n"
              "        if values[i] == target:\n"
              "            return i\n"
              "    return -1\n"),
        note="This is the mirror of 'first position': to find the LAST"
             " match the loop must not stop at the first, so it keeps"
             " overwriting a variable and returns it at the end. A"
             " return inside the loop gives the first position, 1 rather"
             " than 3.",
    ),
    # ========================================================== 3 Building
    dict(
        id=9, ledger="P304", concept="PY4 for build doubled", tier="3 - Building",
        title="Every value doubled", kind="function",
        func="doubled",
        cases=[([1, 2, 3],), ([],), ([0, -4],), ([2.5],)],
        prompt=(
            "Write a function `doubled(values)` that returns a new list"
            " with each value multiplied by 2, in order. A for loop that"
            " appends v * 2 to a result list.\n\n"
            "  doubled([1, 2, 3]) -> [2, 4, 6]\n\n"
            "Return: the new list."
        ),
        solution=("def doubled(values):\n"
                  "    out = []\n"
                  "    for v in values:\n"
                  "        out.append(v * 2)\n"
                  "    return out\n"),
        trap=("def doubled(values):\n"
              "    out = []\n"
              "    for v in values:\n"
              "        out.append(v * 2)\n"
              "        return out\n"),
        note="The return is indented one level too far in the trap, so"
             " it runs inside the loop and the function hands back a"
             " list of one after the first item. The return belongs"
             " after the loop, at the same indentation as the for.",
    ),
    dict(
        id=10, ledger="P305", concept="PY4 for build lengths", tier="3 - Building",
        title="The length of each word", kind="function",
        func="word_lengths",
        cases=[(["pen", "paper", ""],), ([],), (["a"],), (["notebook", "ink"],)],
        prompt=(
            "Write a function `word_lengths(words)` that returns a list"
            " of the lengths of the words, in order. A for loop that"
            " appends len(w) to a result list.\n\n"
            "  word_lengths([\"pen\", \"paper\", \"\"]) -> [3, 5, 0]\n\n"
            "Return: the new list."
        ),
        solution=("def word_lengths(words):\n"
                  "    out = []\n"
                  "    for w in words:\n"
                  "        out.append(len(w))\n"
                  "    return out\n"),
        trap=("def word_lengths(words):\n"
              "    out = []\n"
              "    for w in words:\n"
              "        out.append(len(words))\n"
              "    return out\n"),
        note="len(w) is the length of the current word; len(words) is"
             " the length of the whole list, the same number every time"
             " round. The loop variable is the thing to measure. The"
             " empty string has length 0 and is a perfectly good word"
             " here.",
    ),
    dict(
        id=11, ledger="P306", concept="PY4 for running product", tier="3 - Building",
        title="A running product", kind="function",
        func="running_product",
        cases=[([2, 3, 4],), ([],), ([5],), ([1, 0, 7],)],
        prompt=(
            "Write a function `running_product(values)` that returns a"
            " list where each position holds the product of the values"
            " up to and including it. A for loop with a running product"
            " that starts at 1 and is appended after each multiplication.\n\n"
            "  running_product([2, 3, 4]) -> [2, 6, 24]\n\n"
            "Return: the new list."
        ),
        solution=("def running_product(values):\n"
                  "    out = []\n"
                  "    p = 1\n"
                  "    for v in values:\n"
                  "        p *= v\n"
                  "        out.append(p)\n"
                  "    return out\n"),
        trap=("def running_product(values):\n"
              "    out = []\n"
              "    p = 0\n"
              "    for v in values:\n"
              "        p *= v\n"
              "        out.append(p)\n"
              "    return out\n"),
        note="A running product starts at 1, the number that leaves a"
             " multiplication unchanged; start it at 0 and everything"
             " multiplied into it stays 0. The running total of an"
             " earlier set started at 0 for the same reason in reverse.",
    ),
    dict(
        id=12, ledger="P307", concept="PY4 for build if", tier="3 - Building",
        title="The squares of the odd values", kind="function",
        func="odd_squares",
        cases=[([1, 2, 3, 4, 5],), ([],), ([2, 4],), ([-3],)],
        prompt=(
            "Write a function `odd_squares(values)` that returns a list"
            " of the squares of the ODD values only, in order. A for"
            " loop with an if on v % 2 != 0 and an append of v * v.\n\n"
            "  odd_squares([1, 2, 3, 4, 5]) -> [1, 9, 25]\n\n"
            "Return: the new list."
        ),
        solution=("def odd_squares(values):\n"
                  "    out = []\n"
                  "    for v in values:\n"
                  "        if v % 2 != 0:\n"
                  "            out.append(v * v)\n"
                  "    return out\n"),
        trap=("def odd_squares(values):\n"
              "    out = []\n"
              "    for v in values:\n"
              "        if v % 2 != 0:\n"
              "            out.append(v)\n"
              "    return out\n"),
        note="A building loop with an if both filters and transforms:"
             " the if picks the odd values, the append stores their"
             " squares. Appending v instead of v * v filters without"
             " transforming. v % 2 != 0 is true for negative odd numbers"
             " too, where v % 2 == 1 would miss them in some languages;"
             " Python gives 1 for -3 % 2, but != 0 is the safer habit.",
    ),
    # ========================================================== 4 Reducing
    dict(
        id=13, ledger="P308", concept="PY4 while halving", tier="4 - Reducing",
        title="How many times it halves", kind="function",
        func="times_halvable",
        cases=[(8,), (12,), (7,), (1,)],
        prompt=(
            "Write a function `times_halvable(n)` that returns how many"
            " times a positive integer can be divided by 2 before it"
            " becomes odd. A while loop running while n % 2 == 0, using"
            " n //= 2 and a counter.\n\n"
            "  times_halvable(12) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def times_halvable(n):\n"
                  "    count = 0\n"
                  "    while n % 2 == 0:\n"
                  "        n //= 2\n"
                  "        count += 1\n"
                  "    return count\n"),
        trap=("def times_halvable(n):\n"
              "    count = 0\n"
              "    while n % 2 == 0:\n"
              "        n //= 2\n"
              "        count += 1\n"
              "    return n\n"),
        note="The loop halves n for as long as it is even, and the"
             " counter records how many times that happened. Returning n"
             " hands back what is LEFT -- the odd part, 3 for 12 -- rather"
             " than the count. n //= 2 keeps n a whole number so the %"
             " test stays meaningful; an odd starting value never enters"
             " the loop and the answer is 0.",
    ),
    dict(
        id=14, ledger="P309", concept="PY4 for alternating sum", tier="4 - Reducing",
        title="Add, subtract, add, subtract", kind="function",
        func="alternating_sum",
        cases=[([10, 3, 2, 1],), ([],), ([5],), ([1, 1, 1, 1, 1],)],
        prompt=(
            "Write a function `alternating_sum(values)` that returns the"
            " first value minus the second plus the third minus the"
            " fourth and so on. A for loop over enumerate(values) with an"
            " if on whether the index is even, adding or subtracting"
            " accordingly.\n\n"
            "  alternating_sum([10, 3, 2, 1]) -> 8\n\n"
            "Return: the result."
        ),
        solution=("def alternating_sum(values):\n"
                  "    total = 0\n"
                  "    for i, v in enumerate(values):\n"
                  "        if i % 2 == 0:\n"
                  "            total += v\n"
                  "        else:\n"
                  "            total -= v\n"
                  "    return total\n"),
        trap=("def alternating_sum(values):\n"
              "    total = 0\n"
              "    for i, v in enumerate(values):\n"
              "        if i % 2 == 1:\n"
              "            total += v\n"
              "        else:\n"
              "            total -= v\n"
              "    return total\n"),
        note="enumerate() supplies the position, and the position's"
             " parity decides the sign: index 0 is the first value, which"
             " is added. Getting the parity the other way round negates"
             " the whole answer, -8 for 8.",
    ),
    # ======================================================== 5 The classic
    dict(
        id=15, ledger="P310", concept="PY4 fizzbuzz program", tier="5 - The classic",
        title="FizzBuzz, 1 to 30", kind="program",
        prompt=(
            "Write a program that prints the numbers 1 to 30, one per"
            " line -- except that multiples of 3 print Fizz, multiples of"
            " 5 print Buzz, and multiples of both print FizzBuzz. A for"
            " loop over range(1, 31) with an if / elif / elif / else,"
            " testing 15 first.\n\n"
            "Print: thirty lines, the first five being 1, 2, Fizz, 4,"
            " Buzz."
        ),
        solution=("for i in range(1, 31):\n"
                  "    if i % 15 == 0:\n"
                  "        print(\"FizzBuzz\")\n"
                  "    elif i % 3 == 0:\n"
                  "        print(\"Fizz\")\n"
                  "    elif i % 5 == 0:\n"
                  "        print(\"Buzz\")\n"
                  "    else:\n"
                  "        print(i)\n"),
        trap=("for i in range(1, 31):\n"
              "    if i % 3 == 0:\n"
              "        print(\"Fizz\")\n"
              "    elif i % 5 == 0:\n"
              "        print(\"Buzz\")\n"
              "    elif i % 15 == 0:\n"
              "        print(\"FizzBuzz\")\n"
              "    else:\n"
              "        print(i)\n"),
        note="The interview classic, and the thing it tests is the order"
             " of the branches: an if / elif chain takes the first true"
             " test, so 15 and 30 have to be caught by the FizzBuzz test"
             " before the Fizz test claims them. range(1, 31) is what"
             " reaches 30.",
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
