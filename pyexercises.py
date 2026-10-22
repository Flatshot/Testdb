"""Python practice exercises: fifteen functions, one simple loop each.

The twenty-first Python set, the fourth of single loops: every question
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
        id=1, ledger="P311", concept="PY4 for count char", tier="1 - Counting",
        title="How many spaces", kind="function",
        func="count_spaces",
        cases=[("the glass path",), ("one",), ("",), ("  two  ",)],
        prompt=(
            "Write a function `count_spaces(s)` that returns how many"
            " space characters s contains. A for loop over the characters,"
            " an if on ch == \" \", and a counter.\n\n"
            "  count_spaces(\"the glass path\") -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_spaces(s):\n"
                  "    n = 0\n"
                  "    for ch in s:\n"
                  "        if ch == \" \":\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_spaces(s):\n"
              "    n = 0\n"
              "    for ch in s:\n"
              "        if ch == \" \":\n"
              "            n = 1\n"
              "    return n\n"),
        note="n = 1 sets the counter rather than adding to it, so the"
             " answer is 1 whenever there is any space at all. n += 1 is"
             " the increment. Leading and trailing spaces count like any"
             " other, so '  two  ' has four.",
    ),
    dict(
        id=2, ledger="P312", concept="PY4 for sum if positive", tier="1 - Counting",
        title="The sum of the positive values", kind="function",
        func="sum_positive",
        cases=[([3, -1, 4, -1, 5],), ([],), ([-2, -3],), ([0, 7],)],
        prompt=(
            "Write a function `sum_positive(values)` that returns the"
            " total of the values above zero only. A for loop with an if"
            " on v > 0 and a running total.\n\n"
            "  sum_positive([3, -1, 4, -1, 5]) -> 12\n\n"
            "Return: the total."
        ),
        solution=("def sum_positive(values):\n"
                  "    total = 0\n"
                  "    for v in values:\n"
                  "        if v > 0:\n"
                  "            total += v\n"
                  "    return total\n"),
        trap=("def sum_positive(values):\n"
              "    total = 0\n"
              "    for v in values:\n"
              "        if v > 0:\n"
              "            total += v\n"
              "        else:\n"
              "            total -= v\n"
              "    return total\n"),
        note="The if decides which values join the total; there is no"
             " else, because the others are simply skipped. Subtracting"
             " the negatives adds their size instead and turns the"
             " function into a sum of absolute values -- 14 rather than"
             " 12.",
    ),
    dict(
        id=3, ledger="P313", concept="PY4 for count range", tier="1 - Counting",
        title="Values inside a range", kind="function",
        func="count_between",
        cases=[([1, 5, 10, 15, 20], 5, 15), ([], 0, 1), ([3, 3, 3], 3, 3), ([1, 2], 5, 9)],
        prompt=(
            "Write a function `count_between(values, lo, hi)` that"
            " returns how many values lie between lo and hi INCLUSIVE. A"
            " for loop with a chained comparison lo <= v <= hi under an"
            " if, and a counter.\n\n"
            "  count_between([1, 5, 10, 15, 20], 5, 15) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def count_between(values, lo, hi):\n"
                  "    n = 0\n"
                  "    for v in values:\n"
                  "        if lo <= v <= hi:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_between(values, lo, hi):\n"
              "    n = 0\n"
              "    for v in values:\n"
              "        if lo < v < hi:\n"
              "            n += 1\n"
              "    return n\n"),
        note="Python lets a comparison chain, so lo <= v <= hi reads as"
             " the mathematics does. Inclusive means both ends count, and"
             " the strict version drops 5 and 15 -- and says [3, 3, 3]"
             " has nothing between 3 and 3.",
    ),
    dict(
        id=4, ledger="P314", concept="PY4 for endswith count", tier="1 - Counting",
        title="Words that end a certain way", kind="function",
        func="count_ending",
        cases=[(["Cookbook", "Notebook", "Map", "book"], "book"), ([], "s"), (["bookshelf", "Books"], "book"), (["a", "ba"], "a")],
        prompt=(
            "Write a function `count_ending(words, suffix)` that returns"
            " how many words end with the suffix, case-sensitively. A for"
            " loop with an if on w.endswith(suffix) and a counter.\n\n"
            "  count_ending([\"Cookbook\", \"Notebook\", \"Map\", \"book\"],"
            " \"book\") -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def count_ending(words, suffix):\n"
                  "    n = 0\n"
                  "    for w in words:\n"
                  "        if w.endswith(suffix):\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_ending(words, suffix):\n"
              "    n = 0\n"
              "    for w in words:\n"
              "        if suffix in w:\n"
              "            n += 1\n"
              "    return n\n"),
        note="endswith() looks at the tail only; 'in' finds the suffix"
             " anywhere, so 'bookshelf' counts for 'book' under 'in' and"
             " not under endswith(). Case-sensitive means 'Books' does"
             " not end with 'book' -- the B is upper case and the s is"
             " extra.",
    ),
    # ========================================================= 2 Searching
    dict(
        id=5, ledger="P315", concept="PY4 for max len", tier="2 - Searching",
        title="The length of the longest word", kind="function",
        func="longest_length",
        cases=[(["pen", "paper", "ink"],), ([],), ([""],), (["notebook"],)],
        prompt=(
            "Write a function `longest_length(words)` that returns the"
            " length of the longest word, 0 for an empty list. A for loop"
            " with a best so far that starts at 0 and is replaced when"
            " len(w) is bigger. Do not use max() for this one.\n\n"
            "  longest_length([\"pen\", \"paper\", \"ink\"]) -> 5\n\n"
            "Return: an integer."
        ),
        solution=("def longest_length(words):\n"
                  "    best = 0\n"
                  "    for w in words:\n"
                  "        if len(w) > best:\n"
                  "            best = len(w)\n"
                  "    return best\n"),
        trap=("def longest_length(words):\n"
              "    best = 0\n"
              "    for w in words:\n"
              "        if len(w) > best:\n"
              "            best = w\n"
              "    return best\n"),
        note="Here a start of 0 is right, because lengths cannot be"
             " negative and 0 is the answer for an empty list. The best"
             " has to hold the LENGTH, len(w), not the word -- storing"
             " the word returns 'paper' instead of 5, and then compares"
             " a number with a string next time round.",
    ),
    dict(
        id=6, ledger="P316", concept="PY4 for first index over", tier="2 - Searching",
        title="Where the first value over the limit is", kind="function",
        func="first_index_over",
        cases=[([3, 8, 12, 5], 7), ([1, 2], 7), ([], 7), ([9], 7)],
        prompt=(
            "Write a function `first_index_over(values, limit)` that"
            " returns the POSITION of the first value strictly greater"
            " than limit, or -1 if there is none. A for loop over"
            " enumerate(values) that returns the index at the first"
            " match.\n\n"
            "  first_index_over([3, 8, 12, 5], 7) -> 1\n\n"
            "Return: an integer."
        ),
        solution=("def first_index_over(values, limit):\n"
                  "    for i, v in enumerate(values):\n"
                  "        if v > limit:\n"
                  "            return i\n"
                  "    return -1\n"),
        trap=("def first_index_over(values, limit):\n"
              "    for i, v in enumerate(values):\n"
              "        if v > limit:\n"
              "            return v\n"
              "    return -1\n"),
        note="enumerate() hands over both the index and the value, and"
             " the question wants the index: return i. Returning v gives"
             " the value 8 where position 1 was asked. The -1 after the"
             " loop is the no-match answer.",
    ),
    dict(
        id=7, ledger="P317", concept="PY4 for sorted check", tier="2 - Searching",
        title="Is the list in order?", kind="function",
        func="is_sorted",
        cases=[([1, 2, 2, 5],), ([3, 1, 2],), ([],), ([7],), ([2, 1],)],
        prompt=(
            "Write a function `is_sorted(values)` that returns True when"
            " each value is at least as big as the one before it -- and"
            " True for an empty or one-item list. A for loop over"
            " range(1, len(values)) that returns False at the first"
            " value smaller than its predecessor, then True after the"
            " loop.\n\n"
            "  is_sorted([3, 1, 2]) -> False\n\n"
            "Return: True or False."
        ),
        solution=("def is_sorted(values):\n"
                  "    for i in range(1, len(values)):\n"
                  "        if values[i] < values[i - 1]:\n"
                  "            return False\n"
                  "    return True\n"),
        trap=("def is_sorted(values):\n"
              "    for i in range(1, len(values)):\n"
              "        if values[i] <= values[i - 1]:\n"
              "            return False\n"
              "    return True\n"),
        note="'At least as big' allows equal neighbours, so the"
             " counter-example is a value strictly SMALLER than the one"
             " before: <, not <=. The strict version says [1, 2, 2, 5]"
             " is out of order. True is only reached once no"
             " counter-example was found.",
    ),
    dict(
        id=8, ledger="P318", concept="PY4 for min by hand", tier="2 - Searching",
        title="The smallest value, by hand", kind="function",
        func="smallest",
        cases=[([3, 9, 2],), ([5, 1, 7],), ([4],), ([-1, -9, 0],)],
        prompt=(
            "Write a function `smallest(values)` that returns the smallest"
            " value in a non-empty list WITHOUT using min(). Start a best"
            " at values[0], then a for loop that replaces it whenever a"
            " value is smaller.\n\n"
            "  smallest([5, 1, 7]) -> 1\n\n"
            "Return: the value."
        ),
        solution=("def smallest(values):\n"
                  "    best = values[0]\n"
                  "    for v in values:\n"
                  "        if v < best:\n"
                  "            best = v\n"
                  "    return best\n"),
        trap=("def smallest(values):\n"
              "    best = values[0]\n"
              "    for v in values:\n"
              "        if v > best:\n"
              "            best = v\n"
              "    return best\n"),
        note="The mirror of 'largest by hand': the same shape with the"
             " comparison turned round. With > the function tracks the"
             " biggest value instead. Starting from values[0] rather than"
             " 0 is what makes [-1, -9, 0] come out as -9.",
    ),
    # ========================================================== 3 Building
    dict(
        id=9, ledger="P319", concept="PY4 for reverse string", tier="3 - Building",
        title="A string reversed, by loop", kind="function",
        func="reversed_text",
        cases=[("leeds",), ("",), ("a",), ("ab cd",)],
        prompt=(
            "Write a function `reversed_text(s)` that returns s backwards,"
            " using a for loop over the characters that builds the result"
            " by putting each character in FRONT of what has been built so"
            " far: out = ch + out. Do not use s[::-1] for this one.\n\n"
            "  reversed_text(\"leeds\") -> \"sdeel\"\n\n"
            "Return: the new string."
        ),
        solution=("def reversed_text(s):\n"
                  "    out = \"\"\n"
                  "    for ch in s:\n"
                  "        out = ch + out\n"
                  "    return out\n"),
        trap=("def reversed_text(s):\n"
              "    out = \"\"\n"
              "    for ch in s:\n"
              "        out = out + ch\n"
              "    return out\n"),
        note="ch + out puts the newest character first, so the last"
             " character of s ends up at the front; out + ch rebuilds s"
             " in the same order. The same trick as insert(0) for a list"
             " in an earlier set.",
    ),
    dict(
        id=10, ledger="P320", concept="PY4 for even positions", tier="3 - Building",
        title="The items at even positions", kind="function",
        func="even_positions",
        cases=[(["a", "b", "c", "d", "e"],), ([],), ([1],), ([1, 2],)],
        prompt=(
            "Write a function `even_positions(values)` that returns a"
            " list of the items at positions 0, 2, 4, ... A for loop over"
            " enumerate(values) with an if on i % 2 == 0 and an append."
            " Do not use a slice for this one.\n\n"
            "  even_positions([\"a\", \"b\", \"c\", \"d\", \"e\"]) -> [\"a\","
            " \"c\", \"e\"]\n\n"
            "Return: the new list."
        ),
        solution=("def even_positions(values):\n"
                  "    out = []\n"
                  "    for i, v in enumerate(values):\n"
                  "        if i % 2 == 0:\n"
                  "            out.append(v)\n"
                  "    return out\n"),
        trap=("def even_positions(values):\n"
              "    out = []\n"
              "    for i, v in enumerate(values):\n"
              "        if v % 2 == 0:\n"
              "            out.append(v)\n"
              "    return out\n"),
        note="The parity test is on the INDEX i, not the value v: the"
             " question is about positions. Testing v % 2 picks even"
             " values instead, and fails outright on a list of strings."
             " values[::2] is the slice form of the same thing.",
    ),
    dict(
        id=11, ledger="P321", concept="PY4 for triangle numbers", tier="3 - Building",
        title="The first n triangle numbers", kind="function",
        func="triangle_numbers",
        cases=[(5,), (1,), (0,), (3,)],
        prompt=(
            "Write a function `triangle_numbers(n)` that returns the"
            " first n triangle numbers 1, 3, 6, 10, ... -- each the sum of"
            " the whole numbers up to its position. A for loop over"
            " range(1, n + 1) with a running total that is appended each"
            " time.\n\n"
            "  triangle_numbers(5) -> [1, 3, 6, 10, 15]\n\n"
            "Return: the list."
        ),
        solution=("def triangle_numbers(n):\n"
                  "    out = []\n"
                  "    total = 0\n"
                  "    for i in range(1, n + 1):\n"
                  "        total += i\n"
                  "        out.append(total)\n"
                  "    return out\n"),
        trap=("def triangle_numbers(n):\n"
              "    out = []\n"
              "    total = 0\n"
              "    for i in range(n):\n"
              "        total += i\n"
              "        out.append(total)\n"
              "    return out\n"),
        note="A running total over 1 to n gives the triangle numbers"
             " directly. range(n) starts the loop at 0, so the first"
             " triangle number comes out as 0 and every one after is one"
             " step behind: [0, 1, 3, 6, 10] for 5.",
    ),
    dict(
        id=12, ledger="P322", concept="PY4 for strip digits", tier="3 - Building",
        title="A string without its digits", kind="function",
        func="without_digits",
        cases=[("LS15",), ("2026-06-30",), ("Leeds",), ("",)],
        prompt=(
            "Write a function `without_digits(s)` that returns s with"
            " every digit removed. A for loop over the characters that"
            " adds each NON-digit to a result string, using ch.isdigit()"
            " under a 'not'.\n\n"
            "  without_digits(\"LS15\") -> \"LS\"\n\n"
            "Return: the new string."
        ),
        solution=("def without_digits(s):\n"
                  "    out = \"\"\n"
                  "    for ch in s:\n"
                  "        if not ch.isdigit():\n"
                  "            out += ch\n"
                  "    return out\n"),
        trap=("def without_digits(s):\n"
              "    out = \"\"\n"
              "    for ch in s:\n"
              "        if ch.isdigit():\n"
              "            out += ch\n"
              "    return out\n"),
        note="A filtering loop keeps what passes the if; 'not"
             " ch.isdigit()' keeps the letters and punctuation, and"
             " without the 'not' it keeps the digits and throws away"
             " everything else -- '15' for 'LS15'.",
    ),
    # ========================================================== 4 Reducing
    dict(
        id=13, ledger="P323", concept="PY4 for distinct count", tier="4 - Reducing",
        title="How many different values, by loop", kind="function",
        func="distinct_count",
        cases=[(["LS1", "LS1", "BD3"],), ([],), ([1, 1, 1],), (["a", "b", "a", "c"],)],
        prompt=(
            "Write a function `distinct_count(values)` that returns how"
            " many different values the list holds, WITHOUT using set()"
            " on the whole list at once: a for loop that keeps a set of"
            " values seen so far and adds one to a counter only when the"
            " value is new.\n\n"
            "  distinct_count([\"LS1\", \"LS1\", \"BD3\"]) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def distinct_count(values):\n"
                  "    seen = set()\n"
                  "    n = 0\n"
                  "    for v in values:\n"
                  "        if v not in seen:\n"
                  "            seen.add(v)\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def distinct_count(values):\n"
              "    seen = set()\n"
              "    n = 0\n"
              "    for v in values:\n"
              "        seen.add(v)\n"
              "        n += 1\n"
              "    return n\n"),
        note="The counter must move only on a NEW value, which is what"
             " the 'not in seen' test decides; counting every value gives"
             " len(values). The seen set does the remembering, as in the"
             " repeat-finding questions. len(set(values)) is the one-line"
             " form.",
    ),
    dict(
        id=14, ledger="P324", concept="PY4 for sum within limit", tier="4 - Reducing",
        title="Add up while it still fits", kind="function",
        func="sum_within",
        cases=[([4, 5, 3, 9], 10), ([1, 1, 1], 10), ([20], 10), ([], 5)],
        prompt=(
            "Write a function `sum_within(values, limit)` that adds up"
            " values from the front for as long as the running total"
            " stays at or below limit, and returns the total at the point"
            " it would have gone over. A for loop with a running total"
            " and a break when total + v would exceed limit.\n\n"
            "  sum_within([4, 5, 3, 9], 10) -> 9\n\n"
            "Return: the total."
        ),
        solution=("def sum_within(values, limit):\n"
                  "    total = 0\n"
                  "    for v in values:\n"
                  "        if total + v > limit:\n"
                  "            break\n"
                  "        total += v\n"
                  "    return total\n"),
        trap=("def sum_within(values, limit):\n"
              "    total = 0\n"
              "    for v in values:\n"
              "        total += v\n"
              "        if total > limit:\n"
              "            break\n"
              "    return total\n"),
        note="The test has to happen BEFORE the value is added: check"
             " whether total + v would overshoot, and stop if so. Adding"
             " first and checking afterwards leaves the total already over"
             " the limit when the loop stops -- 12 instead of 9.",
    ),
    dict(
        id=15, ledger="P325", concept="PY4 for power by loop", tier="4 - Reducing",
        title="A power, by repeated multiplication", kind="function",
        func="power",
        cases=[(2, 10), (5, 0), (3, 3), (10, 1)],
        prompt=(
            "Write a function `power(base, exp)` that returns base to the"
            " power exp for a non-negative whole exp, WITHOUT using **: a"
            " result that starts at 1 and a for loop over range(exp) that"
            " multiplies it by base each time.\n\n"
            "  power(2, 10) -> 1024\n\n"
            "Return: an integer."
        ),
        solution=("def power(base, exp):\n"
                  "    result = 1\n"
                  "    for _ in range(exp):\n"
                  "        result *= base\n"
                  "    return result\n"),
        trap=("def power(base, exp):\n"
              "    result = 0\n"
              "    for _ in range(exp):\n"
              "        result *= base\n"
              "    return result\n"),
        note="A product starts at 1 for the same reason a sum starts at"
             " 0: it is the value that leaves the operation unchanged."
             " Starting at 0 keeps the result at 0 forever, and even the"
             " empty loop for exp = 0 should give 1, which is anything to"
             " the power zero.",
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
