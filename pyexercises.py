"""Python practice exercises: fifteen functions, one simple loop each.

The nineteenth Python set, the second of single loops: every question
asks for a function built around ONE for or while loop over plain numbers
or strings -- counting, searching, building, tracking -- with no import
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
        id=1, ledger="P281", concept="PY4 for count if", tier="1 - Counting",
        title="Words longer than a limit", kind="function",
        func="long_words",
        cases=[(["pen", "paper", "ink", "notebook"], 3), ([], 3), (["abc", "abcd"], 3), (["a"], 0)],
        prompt=(
            "Write a function `long_words(words, limit)` that returns how"
            " many words have MORE than limit characters. A for loop"
            " over the words, an if on len(word) > limit, and a"
            " counter.\n\n"
            "  long_words([\"pen\", \"paper\", \"ink\", \"notebook\"], 3) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def long_words(words, limit):\n"
                  "    n = 0\n"
                  "    for w in words:\n"
                  "        if len(w) > limit:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def long_words(words, limit):\n"
              "    n = 0\n"
              "    for w in words:\n"
              "        if len(w) >= limit:\n"
              "            n += 1\n"
              "    return n\n"),
        note="'More than' is a strict >; with >= a word of exactly limit"
             " characters is counted, so 'pen' and 'ink' are long words"
             " at limit 3. The counter starts at 0 and the loop adds one"
             " per match.",
    ),
    dict(
        id=2, ledger="P282", concept="PY4 for neighbours differ", tier="1 - Counting",
        title="How often the value changes", kind="function",
        func="count_changes",
        cases=[([1, 1, 2, 2, 3, 3],), ([],), ([5],), (["a", "b", "a"],)],
        prompt=(
            "Write a function `count_changes(values)` that returns how"
            " many times the value at a position differs from the value"
            " at the position before it. A for loop over range(1,"
            " len(values)), comparing values[i] with values[i - 1] with"
            " !=.\n\n"
            "  count_changes([1, 1, 2, 2, 3, 3]) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_changes(values):\n"
                  "    n = 0\n"
                  "    for i in range(1, len(values)):\n"
                  "        if values[i] != values[i - 1]:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_changes(values):\n"
              "    n = 0\n"
              "    for i in range(1, len(values)):\n"
              "        if values[i] == values[i - 1]:\n"
              "            n += 1\n"
              "    return n\n"),
        note="This is the mirror of counting repeats: the same loop from"
             " position 1, with != in the if. Counting the equal"
             " neighbours instead gives the number of positions that did"
             " NOT change. A list of one has no neighbours and no changes.",
    ),
    dict(
        id=3, ledger="P283", concept="PY4 for divisors", tier="1 - Counting",
        title="How many numbers divide n", kind="function",
        func="count_divisors",
        cases=[(12,), (1,), (7,), (36,)],
        prompt=(
            "Write a function `count_divisors(n)` that returns how many"
            " whole numbers from 1 to n divide n exactly. A for loop over"
            " range(1, n + 1) and an if on n % i == 0.\n\n"
            "  count_divisors(12) -> 6\n\n"
            "Return: an integer."
        ),
        solution=("def count_divisors(n):\n"
                  "    count = 0\n"
                  "    for i in range(1, n + 1):\n"
                  "        if n % i == 0:\n"
                  "            count += 1\n"
                  "    return count\n"),
        trap=("def count_divisors(n):\n"
              "    count = 0\n"
              "    for i in range(1, n):\n"
              "        if n % i == 0:\n"
              "            count += 1\n"
              "    return count\n"),
        note="n divides itself, and range(1, n) stops before n, so the"
             " trap is always one short -- and says 1 and 7 have no"
             " divisors at all. % is the remainder, and a remainder of 0"
             " means an exact division.",
    ),
    dict(
        id=4, ledger="P284", concept="PY4 for above mean", tier="1 - Counting",
        title="Values above the average", kind="function",
        func="count_above_average",
        cases=[([1, 2, 3, 10],), ([5, 5, 5],), ([2, 4],), ([7],)],
        prompt=(
            "Write a function `count_above_average(values)` that returns"
            " how many values in a non-empty list are STRICTLY above the"
            " list's mean. Work the mean out first with sum() and len(),"
            " then a for loop with an if and a counter.\n\n"
            "  count_above_average([1, 2, 3, 10]) -> 1\n\n"
            "Return: an integer."
        ),
        solution=("def count_above_average(values):\n"
                  "    mean = sum(values) / len(values)\n"
                  "    n = 0\n"
                  "    for v in values:\n"
                  "        if v > mean:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_above_average(values):\n"
              "    mean = sum(values) / len(values)\n"
              "    n = 0\n"
              "    for v in values:\n"
              "        if v >= mean:\n"
              "            n += 1\n"
              "    return n\n"),
        note="The mean has to be known before the loop starts, which is"
             " why it is computed first. Strictly above means >; with >="
             " a list of equal values counts every one of them as above"
             " its own average.",
    ),
    # ========================================================= 2 Searching
    dict(
        id=5, ledger="P285", concept="PY4 for mirror compare", tier="2 - Searching",
        title="Is it a palindrome? By loop", kind="function",
        func="is_palindrome",
        cases=[("level",), ("noon",), ("leeds",), ("",), ("ab",)],
        prompt=(
            "Write a function `is_palindrome(s)` that returns True when s"
            " reads the same backwards, using a for loop over range(len("
            "s) // 2) that compares s[i] with s[-1 - i] and returns False"
            " at the first mismatch, then True after the loop. Do not"
            " use s[::-1] for this one.\n\n"
            "  is_palindrome(\"noon\") -> True\n\n"
            "Return: True or False."
        ),
        solution=("def is_palindrome(s):\n"
                  "    for i in range(len(s) // 2):\n"
                  "        if s[i] != s[-1 - i]:\n"
                  "            return False\n"
                  "    return True\n"),
        trap=("def is_palindrome(s):\n"
              "    for i in range(len(s) // 2):\n"
              "        if s[i] != s[-i]:\n"
              "            return False\n"
              "    return True\n"),
        note="The mirror of position i is -1 - i: position 0 pairs with"
             " -1, the last character. s[-i] is off by one -- s[-0] is"
             " s[0] -- so the first comparison is a character with"
             " itself and 'ab' passes. Half the length is enough, because"
             " the second half is the same pairs again.",
    ),
    dict(
        id=6, ledger="P286", concept="PY4 for first repeat", tier="2 - Searching",
        title="The first value that repeats", kind="function",
        func="first_repeat",
        cases=[([3, 1, 4, 1, 5, 3],), ([1, 2, 3],), ([],), (["b", "a", "b", "a"],)],
        prompt=(
            "Write a function `first_repeat(values)` that returns the"
            " first value whose second appearance comes earliest, or"
            " None when nothing repeats. A for loop with a seen set,"
            " returning the value the moment it is already in the set.\n\n"
            "  first_repeat([3, 1, 4, 1, 5, 3]) -> 1\n\n"
            "Return: the value, or None."
        ),
        solution=("def first_repeat(values):\n"
                  "    seen = set()\n"
                  "    for v in values:\n"
                  "        if v in seen:\n"
                  "            return v\n"
                  "        seen.add(v)\n"
                  "    return None\n"),
        trap=("def first_repeat(values):\n"
              "    seen = set()\n"
              "    for v in values:\n"
              "        if v in seen:\n"
              "            return True\n"
              "        seen.add(v)\n"
              "    return None\n"),
        note="The same loop as 'is anything repeated', but what it"
             " returns is the VALUE, not True. 1 repeats before 3 does,"
             " even though 3 came first, because the question is about"
             " the earliest second appearance -- which is exactly what"
             " returning at the first hit gives.",
    ),
    dict(
        id=7, ledger="P287", concept="PY4 for find index", tier="2 - Searching",
        title="Where a value first appears", kind="function",
        func="position_of",
        cases=[(7, [3, 7, 9, 7]), (2, [3, 7]), ("a", ["b", "a"]), (1, [])],
        prompt=(
            "Write a function `position_of(target, values)` that returns"
            " the index of the FIRST occurrence of target, or -1 if it is"
            " absent. A for loop over range(len(values)) that returns the"
            " index as soon as values[i] equals target.\n\n"
            "  position_of(7, [3, 7, 9, 7]) -> 1\n\n"
            "Return: an integer."
        ),
        solution=("def position_of(target, values):\n"
                  "    for i in range(len(values)):\n"
                  "        if values[i] == target:\n"
                  "            return i\n"
                  "    return -1\n"),
        trap=("def position_of(target, values):\n"
              "    found = -1\n"
              "    for i in range(len(values)):\n"
              "        if values[i] == target:\n"
              "            found = i\n"
              "    return found\n"),
        note="Returning inside the loop stops at the first match. Saving"
             " the index and carrying on overwrites it with every later"
             " match, so the trap reports the LAST position, 3 instead of"
             " 1. This is list.index() written out, with -1 instead of"
             " an error.",
    ),
    dict(
        id=8, ledger="P288", concept="PY4 for running target", tier="2 - Searching",
        title="How many items until the total reaches a target", kind="function",
        func="items_to_reach",
        cases=[([3, 4, 5, 6], 10), ([1, 1, 1], 10), ([10], 10), ([], 1)],
        prompt=(
            "Write a function `items_to_reach(values, target)` that"
            " returns how many items from the front are needed before"
            " their running total is AT LEAST target, or -1 if the whole"
            " list never gets there. A for loop over enumerate(values,"
            " start=1) adding to a total and returning the count the"
            " moment the total reaches target.\n\n"
            "  items_to_reach([3, 4, 5, 6], 10) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def items_to_reach(values, target):\n"
                  "    total = 0\n"
                  "    for i, v in enumerate(values, start=1):\n"
                  "        total += v\n"
                  "        if total >= target:\n"
                  "            return i\n"
                  "    return -1\n"),
        trap=("def items_to_reach(values, target):\n"
              "    total = 0\n"
              "    for i, v in enumerate(values, start=1):\n"
              "        total += v\n"
              "        if total > target:\n"
              "            return i\n"
              "    return -1\n"),
        note="'At least' is >=: a running total that lands exactly on"
             " the target has reached it, so [10] reaches 10 with one"
             " item, not never. enumerate with start=1 counts the items"
             " for you; the add comes before the test so the current"
             " item is included.",
    ),
    # ========================================================== 3 Building
    dict(
        id=9, ledger="P289", concept="PY4 while multiples", tier="3 - Building",
        title="The multiples below a limit", kind="function",
        func="multiples_below",
        cases=[(3, 10), (5, 5), (4, 1), (7, 22)],
        prompt=(
            "Write a function `multiples_below(k, limit)` that returns"
            " the list of positive multiples of k that are strictly LESS"
            " than limit, in order. A while loop with a running multiple"
            " that starts at k and grows by k each time.\n\n"
            "  multiples_below(3, 10) -> [3, 6, 9]\n\n"
            "Return: the list."
        ),
        solution=("def multiples_below(k, limit):\n"
                  "    out = []\n"
                  "    m = k\n"
                  "    while m < limit:\n"
                  "        out.append(m)\n"
                  "        m += k\n"
                  "    return out\n"),
        trap=("def multiples_below(k, limit):\n"
              "    out = []\n"
              "    m = k\n"
              "    while m <= limit:\n"
              "        out.append(m)\n"
              "        m += k\n"
              "    return out\n"),
        note="The while condition is the question's own words, m <"
             " limit; with <= a multiple equal to the limit is included,"
             " so multiples_below(5, 5) gives [5]. The step m += k is"
             " what ends the loop. range(k, limit, k) would do the same"
             " without a loop -- this one is about the loop.",
    ),
    dict(
        id=10, ledger="P290", concept="PY4 for build lines", tier="3 - Building",
        title="A bar chart in stars", kind="function",
        func="bar_lines",
        cases=[({"good": 3, "worn": 1},), ({},), ({"x": 0},), ({"a": 2, "b": 5, "c": 1},)],
        prompt=(
            "Write a function `bar_lines(counts)` that returns a list of"
            " strings, one per key in the dictionary's order, each of the"
            " form 'key: ***' with as many stars as the value. A for loop"
            " over counts.items() appending a string built with"
            " '*' * value.\n\n"
            "  bar_lines({\"good\": 3, \"worn\": 1}) -> [\"good: ***\","
            " \"worn: *\"]\n\n"
            "Return: the list of strings."
        ),
        solution=("def bar_lines(counts):\n"
                  "    out = []\n"
                  "    for k, v in counts.items():\n"
                  "        out.append(k + \": \" + \"*\" * v)\n"
                  "    return out\n"),
        trap=("def bar_lines(counts):\n"
              "    out = []\n"
              "    for k, v in counts.items():\n"
              "        out.append(k + \": \" + \"*\" + str(v))\n"
              "    return out\n"),
        note="items() hands over each key with its value, and '*' * v"
             " repeats the star v times -- zero times gives ''. Writing"
             " the number after one star is a label, not a bar. The"
             " dictionary's own order is the order of the lines.",
    ),
    dict(
        id=11, ledger="P291", concept="PY4 for transform", tier="3 - Building",
        title="Each word with a capital", kind="function",
        func="capitalised",
        cases=[(["aisha", "kwame"],), ([],), (["LEEDS"],), (["mixed", "Case"],)],
        prompt=(
            "Write a function `capitalised(words)` that returns a new"
            " list with each word's first letter upper case and the rest"
            " lower case. A for loop that appends word.capitalize() to a"
            " result list.\n\n"
            "  capitalised([\"aisha\", \"kwame\"]) -> [\"Aisha\", \"Kwame\"]\n\n"
            "Return: the new list."
        ),
        solution=("def capitalised(words):\n"
                  "    out = []\n"
                  "    for w in words:\n"
                  "        out.append(w.capitalize())\n"
                  "    return out\n"),
        trap=("def capitalised(words):\n"
              "    out = []\n"
              "    for w in words:\n"
              "        out.append(w.upper())\n"
              "    return out\n"),
        note="A loop that builds a new list from the old one item by"
             " item is the long form of a comprehension, and the pattern"
             " to know before the short form. capitalize() lowers the"
             " rest of the word as well; upper() shouts the whole thing.",
    ),
    dict(
        id=12, ledger="P292", concept="PY4 for running total list", tier="3 - Building",
        title="A balance after each change", kind="function",
        func="running_balance",
        cases=[([100, -30, 50],), ([],), ([5],), ([-10, -10, 25],)],
        prompt=(
            "Write a function `running_balance(changes)` that returns a"
            " list holding the balance after each change, starting from"
            " zero. A for loop with a running total that is appended"
            " after every addition.\n\n"
            "  running_balance([100, -30, 50]) -> [100, 70, 120]\n\n"
            "Return: the new list."
        ),
        solution=("def running_balance(changes):\n"
                  "    out = []\n"
                  "    total = 0\n"
                  "    for c in changes:\n"
                  "        total += c\n"
                  "        out.append(total)\n"
                  "    return out\n"),
        trap=("def running_balance(changes):\n"
              "    out = []\n"
              "    total = 0\n"
              "    for c in changes:\n"
              "        total += c\n"
              "        out.append(c)\n"
              "    return out\n"),
        note="Two variables do the work: the total carries across the"
             " loop, and the list records the total after each step."
             " Appending the change itself just copies the input. This"
             " is SUM() OVER (ORDER BY ...) written as a loop.",
    ),
    dict(
        id=13, ledger="P293", concept="PY4 for filter chars", tier="3 - Building",
        title="A word without its vowels", kind="function",
        func="without_vowels",
        cases=[("library",), ("AEIOU",), ("rhythm",), ("",)],
        prompt=(
            "Write a function `without_vowels(s)` that returns s with"
            " every vowel removed, upper or lower case. A for loop over"
            " the characters that adds each NON-vowel to a result string,"
            " testing ch.lower() against 'aeiou'.\n\n"
            "  without_vowels(\"library\") -> \"lbrry\"\n\n"
            "Return: the new string."
        ),
        solution=("def without_vowels(s):\n"
                  "    out = \"\"\n"
                  "    for ch in s:\n"
                  "        if ch.lower() not in \"aeiou\":\n"
                  "            out += ch\n"
                  "    return out\n"),
        trap=("def without_vowels(s):\n"
              "    out = \"\"\n"
              "    for ch in s:\n"
              "        if ch.lower() in \"aeiou\":\n"
              "            out += ch\n"
              "    return out\n"),
        note="A string can be built up with += inside a loop just as a"
             " list can with append. The if decides what is KEPT: 'not"
             " in' keeps the consonants, 'in' keeps the vowels and hands"
             " back 'ia' for library.",
    ),
    # ========================================================== 4 Tracking
    dict(
        id=14, ledger="P294", concept="PY4 for longest run", tier="4 - Tracking",
        title="The longest run of equal values", kind="function",
        func="longest_run",
        cases=[([1, 1, 2, 2, 2, 3],), ([],), ([7],), (["a", "b", "a"],), ([4, 4, 4, 4],)],
        prompt=(
            "Write a function `longest_run(values)` that returns the"
            " length of the longest stretch of equal values sitting next"
            " to each other, 0 for an empty list. A for loop over range("
            "1, len(values)) with a current run length that grows when"
            " values[i] equals values[i - 1] and resets to 1 when it"
            " does not, and a best so far.\n\n"
            "  longest_run([1, 1, 2, 2, 2, 3]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def longest_run(values):\n"
                  "    if not values:\n"
                  "        return 0\n"
                  "    best = 1\n"
                  "    run = 1\n"
                  "    for i in range(1, len(values)):\n"
                  "        if values[i] == values[i - 1]:\n"
                  "            run += 1\n"
                  "        else:\n"
                  "            run = 1\n"
                  "        if run > best:\n"
                  "            best = run\n"
                  "    return best\n"),
        trap=("def longest_run(values):\n"
              "    if not values:\n"
              "        return 0\n"
              "    best = 1\n"
              "    run = 1\n"
              "    for i in range(1, len(values)):\n"
              "        if values[i] == values[i - 1]:\n"
              "            run += 1\n"
              "        if run > best:\n"
              "            best = run\n"
              "    return best\n"),
        note="Two trackers: the current run and the best run. The reset"
             " to 1 when the value changes is the line that is easy to"
             " forget -- without it the run keeps growing across"
             " different values and [1, 1, 2, 2, 2, 3] comes out as 5."
             " The empty-list guard handles the one case the loop cannot.",
    ),
    dict(
        id=15, ledger="P295", concept="PY4 for digits to number", tier="4 - Tracking",
        title="Digits back into a number", kind="function",
        func="digits_to_number",
        cases=[([1, 2, 3, 4],), ([0],), ([9, 0, 0],), ([],)],
        prompt=(
            "Write a function `digits_to_number(digits)` that turns a"
            " list of single digits into the integer they spell, 0 for"
            " an empty list. A for loop that keeps a number n, replacing"
            " it with n * 10 + digit at each step.\n\n"
            "  digits_to_number([1, 2, 3, 4]) -> 1234\n\n"
            "Return: an integer."
        ),
        solution=("def digits_to_number(digits):\n"
                  "    n = 0\n"
                  "    for d in digits:\n"
                  "        n = n * 10 + d\n"
                  "    return n\n"),
        trap=("def digits_to_number(digits):\n"
              "    n = 0\n"
              "    for d in digits:\n"
              "        n += d\n"
              "    return n\n"),
        note="Multiplying by 10 before adding shifts the digits already"
             " collected one place left, so each new digit lands in the"
             " units. Just adding the digits gives their sum, 10 for"
             " 1234. This is the reverse of peeling digits with % and //.",
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
