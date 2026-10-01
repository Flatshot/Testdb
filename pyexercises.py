"""Python practice exercises: fifteen functions with a loop or an if inside.

The sixth Python set, and a step up from the one-line functions before it:
every question asks for a FUNCTION of two to five lines that RETURNS a
value and needs a for loop, a while loop or an if/else to get there --
counting the items that pass a test, finding the first one, filtering a
list, building a running total, clamping values, counting down, summing
digits, banding a value, finding the second largest, spotting a
duplicate, measuring a streak, and three small jobs on dictionaries. The
title names the shape of the loop, so the tree on the left reads like a
list of patterns.

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
so an infinite loop is stopped, not fatal -- and one of the traps here is
exactly that.
"""

import pyrun

EXERCISES = [
    # ================================================ 1 Counting and filtering
    dict(
        id=1, ledger="P086", concept="PY4 for+if count", tier="1 - Counting and filtering",
        title="for + if: count the ones over a limit", kind="function",
        func="count_above",
        cases=[([72, 118, 65, 101], 100), ([100, 100], 100), ([], 50)],
        prompt=(
            "Write a function `count_above(rates, limit)` that returns how"
            " many of the rates are STRICTLY greater than the limit, using"
            " a for loop with an if and a counter:\n\n"
            "  count_above([72, 118, 65, 101], 100) -> 2\n\n"
            "Return: the count; 0 for an empty list."
        ),
        solution=('def count_above(rates, limit):\n'
                  '    count = 0\n'
                  '    for r in rates:\n'
                  '        if r > limit:\n'
                  '            count += 1\n'
                  '    return count\n'),
        trap=('def count_above(rates, limit):\n'
              '    count = 0\n'
              '    for r in rates:\n'
              '        if r >= limit:\n'
              '            count += 1\n'
              '    return count\n'),
        note="The counting pattern: start at 0, add 1 inside the if, return"
             " after the loop. 'Greater than' is >, and the boundary case"
             " -- a rate equal to the limit -- is where >= goes wrong, which"
             " is why the test cases include one. The one-liner is"
             " sum(r > limit for r in rates), once the loop is second"
             " nature.",
    ),
    dict(
        id=2, ledger="P087", concept="PY4 for+return", tier="1 - Counting and filtering",
        title="for + return: the first one over", kind="function",
        func="first_above",
        cases=[([72, 118, 65, 101], 100), ([72, 65], 100), ([], 0)],
        prompt=(
            "Write a function `first_above(rates, limit)` that returns the"
            " FIRST rate greater than the limit, or None if there is"
            " none:\n\n"
            "  first_above([72, 118, 65, 101], 100) -> 118\n\n"
            "Return: the rate, or None."
        ),
        solution=('def first_above(rates, limit):\n'
                  '    for r in rates:\n'
                  '        if r > limit:\n'
                  '            return r\n'
                  '    return None\n'),
        trap=('def first_above(rates, limit):\n'
              '    found = None\n'
              '    for r in rates:\n'
              '        if r > limit:\n'
              '            found = r\n'
              '    return found\n'),
        note="A return inside the loop leaves the function the moment the"
             " first match is found. Recording the match and carrying on"
             " keeps overwriting it, so the LAST match comes back -- 101"
             " instead of 118. The return None after the loop runs only"
             " when nothing matched; a function that falls off the end"
             " returns None anyway, but saying so is clearer.",
    ),
    dict(
        id=3, ledger="P088", concept="PY4 filter list", tier="1 - Counting and filtering",
        title="for + append: keep the evens", kind="function",
        func="evens_only",
        cases=[([1, 2, 3, 4, 6],), ([1, 3],), ([],)],
        prompt=(
            "Write a function `evens_only(nums)` that returns a NEW list"
            " holding only the even numbers, in their original order --"
            " an empty list to start with, append() inside the if:\n\n"
            "  evens_only([1, 2, 3, 4, 6]) -> [2, 4, 6]\n\n"
            "Return: the new list."
        ),
        solution=('def evens_only(nums):\n'
                  '    evens = []\n'
                  '    for n in nums:\n'
                  '        if n % 2 == 0:\n'
                  '            evens.append(n)\n'
                  '    return evens\n'),
        trap=('def evens_only(nums):\n'
              '    for n in nums:\n'
              '        if n % 2 == 1:\n'
              '            nums.remove(n)\n'
              '    return nums\n'),
        note="Build a new list rather than removing from the one you are"
             " looping over: removing shifts the items along, the loop"
             " skips the one that moved into the gap, and [1, 3] comes"
             " back as [3]. The filter pattern -- empty list, loop, if,"
             " append -- is also what a comprehension abbreviates:"
             " [n for n in nums if n % 2 == 0].",
    ),
    dict(
        id=4, ledger="P089", concept="PY4 filter strings", tier="1 - Counting and filtering",
        title="for + if: drop the blank strings", kind="function",
        func="remove_blanks",
        cases=[(["Bay A", "", "   ", "Bay B"],), (["", " "],), (["x"],)],
        prompt=(
            "Write a function `remove_blanks(strings)` that returns a new"
            " list without the strings that are empty or only whitespace."
            " strip() turns a whitespace-only string into an empty one,"
            " and an empty string is false in an if:\n\n"
            "  remove_blanks([\"Bay A\", \"\", \"   \", \"Bay B\"]) ->"
            " [\"Bay A\", \"Bay B\"]\n\n"
            "Return: the new list, with the kept strings unchanged."
        ),
        solution=('def remove_blanks(strings):\n'
                  '    kept = []\n'
                  '    for s in strings:\n'
                  '        if s.strip():\n'
                  '            kept.append(s)\n'
                  '    return kept\n'),
        trap=('def remove_blanks(strings):\n'
              '    kept = []\n'
              '    for s in strings:\n'
              '        if s != "":\n'
              '            kept.append(s)\n'
              '    return kept\n'),
        note="s != '' keeps '   ', which is not empty but is blank."
             " s.strip() is '' for any whitespace-only string, and an"
             " empty string is false, so `if s.strip():` reads 'if there"
             " is anything left after trimming'. The kept strings are"
             " appended as they were, not stripped -- the question says"
             " unchanged.",
    ),
    # =================================================== 2 Building a list
    dict(
        id=5, ledger="P090", concept="PY4 running total", tier="2 - Building a list",
        title="for + accumulator: running totals", kind="function",
        func="running_total",
        cases=[([3, 1, 4, 1],), ([],), ([10],)],
        prompt=(
            "Write a function `running_total(nums)` that returns a list"
            " of the cumulative sums -- each item is the total so far:\n\n"
            "  running_total([3, 1, 4, 1]) -> [3, 4, 8, 9]\n\n"
            "Keep a total that grows as you go, and append it after each"
            " addition.\n\n"
            "Return: the list of totals."
        ),
        solution=('def running_total(nums):\n'
                  '    totals = []\n'
                  '    total = 0\n'
                  '    for n in nums:\n'
                  '        total += n\n'
                  '        totals.append(total)\n'
                  '    return totals\n'),
        trap=('def running_total(nums):\n'
              '    totals = []\n'
              '    total = 0\n'
              '    for n in nums:\n'
              '        totals.append(total)\n'
              '        total += n\n'
              '    return totals\n'),
        note="Two variables: the running total, and the list collecting"
             " it. The order of the two lines in the body matters -- add,"
             " then append -- or every entry is the total BEFORE the"
             " current item and the list starts with 0. itertools."
             "accumulate does this in one call, later.",
    ),
    dict(
        id=6, ledger="P091", concept="PY4 if/elif in loop", tier="2 - Building a list",
        title="for + if/elif: clamp every value", kind="function",
        func="clamp_all",
        cases=[([35.2, 36.8, 42.5], 36.0, 41.0), ([], 0, 1), ([5, 5], 5, 5)],
        prompt=(
            "Write a function `clamp_all(values, lo, hi)` that returns a"
            " new list where every value below lo becomes lo, every value"
            " above hi becomes hi, and the rest are unchanged:\n\n"
            "  clamp_all([35.2, 36.8, 42.5], 36.0, 41.0) -> [36.0, 36.8,"
            " 41.0]\n\n"
            "Return: the new list."
        ),
        solution=('def clamp_all(values, lo, hi):\n'
                  '    out = []\n'
                  '    for v in values:\n'
                  '        if v < lo:\n'
                  '            out.append(lo)\n'
                  '        elif v > hi:\n'
                  '            out.append(hi)\n'
                  '        else:\n'
                  '            out.append(v)\n'
                  '    return out\n'),
        trap=('def clamp_all(values, lo, hi):\n'
              '    out = []\n'
              '    for v in values:\n'
              '        if v < lo:\n'
              '            out.append(lo)\n'
              '        if v > hi:\n'
              '            out.append(hi)\n'
              '        else:\n'
              '            out.append(v)\n'
              '    return out\n'),
        note="if / elif / else is ONE decision with three outcomes, and"
             " exactly one branch runs. Two separate ifs are two decisions:"
             " a value below lo appends lo in the first and then, being"
             " not above hi, appends itself in the second's else -- two"
             " items for one input. When the cases are exclusive, chain"
             " them with elif. min(hi, max(lo, v)) is the one-line clamp.",
    ),
    dict(
        id=7, ledger="P092", concept="PY4 while", tier="2 - Building a list",
        title="while: count down to one", kind="function",
        func="countdown",
        cases=[(3,), (1,), (0,)],
        prompt=(
            "Write a function `countdown(n)` that returns the list n, n-1,"
            " ... down to 1, using a while loop that appends and then"
            " decrements. For 0 or less, return an empty list:\n\n"
            "  countdown(3) -> [3, 2, 1]\n\n"
            "Return: the list."
        ),
        solution=('def countdown(n):\n'
                  '    out = []\n'
                  '    while n > 0:\n'
                  '        out.append(n)\n'
                  '        n -= 1\n'
                  '    return out\n'),
        trap=('def countdown(n):\n'
              '    out = []\n'
              '    while n > 0:\n'
              '        out.append(n)\n'
              '    return out\n'),
        note="A while loop runs until its condition is false, so something"
             " in the body has to move towards that -- n -= 1 here."
             " Without it the loop appends 3 forever, and the runner stops"
             " it at the time limit. With a for loop the same list is"
             " list(range(n, 0, -1)); while is for when the number of"
             " passes is not known up front.",
    ),
    dict(
        id=8, ledger="P093", concept="PY4 while digits", tier="2 - Building a list",
        title="while + // and %: add up the digits", kind="function",
        func="digit_sum",
        cases=[(1234,), (7,), (0,), (9999,)],
        prompt=(
            "Write a function `digit_sum(n)` that returns the sum of the"
            " digits of a non-negative integer, peeling the last digit off"
            " with % 10 and dropping it with // 10 in a while loop:\n\n"
            "  digit_sum(1234) -> 10\n\n"
            "digit_sum(0) is 0.\n\n"
            "Return: the sum."
        ),
        solution=('def digit_sum(n):\n'
                  '    total = 0\n'
                  '    while n > 0:\n'
                  '        total += n % 10\n'
                  '        n = n // 10\n'
                  '    return total\n'),
        trap=('def digit_sum(n):\n'
              '    total = 0\n'
              '    while n > 0:\n'
              '        total += n % 10\n'
              '        n = n / 10\n'
              '    return total\n'),
        note="n % 10 is the last digit and n // 10 is the number without"
             " it. With / instead of //, n becomes 123.4, then 12.34, and"
             " the loop runs on through fractions -- the digits it adds"
             " are of 123.4 % 10, which is 3.4 -- until n underflows to"
             " 0 some three hundred passes later with a nonsense total."
             " Integer arithmetic needs the integer operators. The other"
             " route is sum(int(ch) for ch in str(n)).",
    ),
    # ============================================================ 3 Choosing
    dict(
        id=9, ledger="P094", concept="PY4 if/elif bands", tier="3 - Choosing",
        title="if/elif/else: an age band", kind="function",
        func="band",
        cases=[(7,), (18,), (64,), (65,), (90,)],
        prompt=(
            "Write a function `band(age)` that returns 'child' for an age"
            " under 18, 'adult' for 18 up to and including 64, and"
            " 'senior' for 65 and over:\n\n"
            "  band(64) -> 'adult'\n"
            "  band(65) -> 'senior'\n\n"
            "Return: one of the three strings."
        ),
        solution=('def band(age):\n'
                  '    if age < 18:\n'
                  '        return "child"\n'
                  '    elif age < 65:\n'
                  '        return "adult"\n'
                  '    else:\n'
                  '        return "senior"\n'),
        trap=('def band(age):\n'
              '    if age < 18:\n'
              '        return "child"\n'
              '    elif age <= 65:\n'
              '        return "adult"\n'
              '    else:\n'
              '        return "senior"\n'),
        note="Bands are tested in order, so each elif only sees what the"
             " earlier tests let through: age < 65 already means 18 to 64"
             " once age < 18 has been handled. The boundary is the whole"
             " difficulty -- 65 is a senior, so the adult test is < 65,"
             " not <= 65 -- and the cases probe both edges.",
    ),
    dict(
        id=10, ledger="P095", concept="PY4 two maxima", tier="3 - Choosing",
        title="for + two variables: the second largest", kind="function",
        func="second_largest",
        cases=[([72, 118, 65, 101],), ([5, 5, 3],), ([1, 2],)],
        prompt=(
            "Write a function `second_largest(nums)` that returns the"
            " second-largest DISTINCT value in a list of at least two"
            " distinct numbers:\n\n"
            "  second_largest([72, 118, 65, 101]) -> 101\n"
            "  second_largest([5, 5, 3]) -> 3\n\n"
            "Return: the number."
        ),
        solution=('def second_largest(nums):\n'
                  '    distinct = sorted(set(nums))\n'
                  '    return distinct[-2]\n'),
        trap=('def second_largest(nums):\n'
              '    return sorted(nums)[-2]\n'),
        note="sorted(nums)[-2] is the second item from the end, and when"
             " the largest value appears twice that is the largest again"
             " -- [5, 5, 3] gives 5, not 3. 'Distinct' is the word to act"
             " on: set() drops the repeats first. The loop version keeps"
             " two variables, best and second, and updates both as it"
             " goes.",
    ),
    dict(
        id=11, ledger="P096", concept="PY4 seen set", tier="3 - Choosing",
        title="for + set: is anything repeated", kind="function",
        func="has_duplicates",
        cases=[([1, 2, 3, 2],), ([1, 2, 3],), ([],), (["a", "A"],)],
        prompt=(
            "Write a function `has_duplicates(items)` that returns True if"
            " any value appears more than once, else False. Keep a set of"
            " what you have seen; return True the moment an item is"
            " already in it:\n\n"
            "  has_duplicates([1, 2, 3, 2]) -> True\n\n"
            "Return: True or False."
        ),
        solution=('def has_duplicates(items):\n'
                  '    seen = set()\n'
                  '    for item in items:\n'
                  '        if item in seen:\n'
                  '            return True\n'
                  '        seen.add(item)\n'
                  '    return False\n'),
        trap=('def has_duplicates(items):\n'
              '    seen = set()\n'
              '    for item in items:\n'
              '        seen.add(item)\n'
              '        if item in seen:\n'
              '            return True\n'
              '    return False\n'),
        note="Test, then add. Adding first means the item is always in"
             " the set by the time it is tested, so the very first item"
             " looks like a duplicate and every non-empty list returns"
             " True. The one-liner is len(set(items)) < len(items), which"
             " looks at everything; the loop can stop at the first repeat.",
    ),
    dict(
        id=12, ledger="P097", concept="PY4 streak", tier="3 - Choosing",
        title="for + reset: the longest streak", kind="function",
        func="longest_run",
        cases=[([True, True, False, True, True, True],), ([False, False],),
               ([],), ([True],), ([True, True, True, False, True],)],
        prompt=(
            "Write a function `longest_run(flags)` that returns the length"
            " of the longest unbroken run of True values in the list:\n\n"
            "  longest_run([True, True, False, True, True, True]) -> 3\n\n"
            "Keep a current run that grows on True and resets to 0 on"
            " False, and a best that remembers the highest the current"
            " run has reached.\n\n"
            "Return: the length; 0 if there is no True."
        ),
        solution=('def longest_run(flags):\n'
                  '    best = 0\n'
                  '    current = 0\n'
                  '    for f in flags:\n'
                  '        if f:\n'
                  '            current += 1\n'
                  '            best = max(best, current)\n'
                  '        else:\n'
                  '            current = 0\n'
                  '    return best\n'),
        trap=('def longest_run(flags):\n'
              '    current = 0\n'
              '    for f in flags:\n'
              '        if f:\n'
              '            current += 1\n'
              '        else:\n'
              '            current = 0\n'
              '    return current\n'),
        note="Two counters: the run in progress, and the best run seen."
             " Returning only the current run reports the LAST streak,"
             " which is 0 whenever the list ends on a False. best = max"
             "(best, current) is the update that remembers; it has to"
             " happen as the run grows, not after the loop.",
    ),
    # ========================================================= 4 Dictionaries
    dict(
        id=13, ledger="P098", concept="PY4 dict filter", tier="4 - Dictionaries",
        title="for + items(): keys whose value passes", kind="function",
        func="keys_above",
        cases=[({"Fleming": 16, "Barry": 30, "Jenner": 18}, 17),
               ({"a": 1}, 5), ({}, 0)],
        prompt=(
            "Write a function `keys_above(d, limit)` that returns a list"
            " of the keys whose value is greater than the limit, in the"
            " dictionary's order:\n\n"
            "  keys_above({\"Fleming\": 16, \"Barry\": 30, \"Jenner\": 18},"
            " 17) -> [\"Barry\", \"Jenner\"]\n\n"
            "Return: a list of keys."
        ),
        solution=('def keys_above(d, limit):\n'
                  '    out = []\n'
                  '    for key, value in d.items():\n'
                  '        if value > limit:\n'
                  '            out.append(key)\n'
                  '    return out\n'),
        trap=('def keys_above(d, limit):\n'
              '    out = []\n'
              '    for key, value in d.items():\n'
              '        if value > limit:\n'
              '            out.append(value)\n'
              '    return out\n'),
        note="items() gives both halves of each entry, and the if tests"
             " one while the append collects the other -- the question"
             " asks for the keys, and appending the values gives [30, 18]."
             " A dict keeps insertion order, so the list comes out in the"
             " order the entries were added.",
    ),
    dict(
        id=14, ledger="P099", concept="PY4 dict build", tier="4 - Dictionaries",
        title="for + d[k] = v: invert a dictionary", kind="function",
        func="invert",
        cases=[({"Fleming": 5, "Barry": 4},), ({},), ({"x": 1},)],
        prompt=(
            "Write a function `invert(d)` that returns a new dictionary"
            " with the keys and values swapped. The values are unique:\n\n"
            "  invert({\"Fleming\": 5, \"Barry\": 4}) -> {5: \"Fleming\","
            " 4: \"Barry\"}\n\n"
            "Return: the new dictionary."
        ),
        solution=('def invert(d):\n'
                  '    out = {}\n'
                  '    for key, value in d.items():\n'
                  '        out[value] = key\n'
                  '    return out\n'),
        trap=('def invert(d):\n'
              '    out = {}\n'
              '    for key, value in d.items():\n'
              '        out[key] = value\n'
              '    return out\n'),
        note="Building a dictionary in a loop is assignment to a new key,"
             " out[value] = key -- the value becomes the key. Assigning"
             " out[key] = value just copies the dictionary. The"
             " comprehension form is {v: k for k, v in d.items()}. If two"
             " keys shared a value, the later one would win; the question"
             " promises they do not.",
    ),
    dict(
        id=15, ledger="P100", concept="PY4 dict merge", tier="4 - Dictionaries",
        title="for + get(): add two tallies together", kind="function",
        func="merge_counts",
        cases=[({"day": 3, "night": 1}, {"night": 2, "late": 1}),
               ({}, {"a": 1}), ({"a": 1}, {})],
        prompt=(
            "Write a function `merge_counts(a, b)` that returns a new"
            " dictionary holding the sum of the counts in two tallies -- a"
            " key in both is added up, a key in one keeps its count:\n\n"
            "  merge_counts({\"day\": 3, \"night\": 1}, {\"night\": 2,"
            " \"late\": 1}) -> {\"day\": 3, \"night\": 3, \"late\": 1}\n\n"
            "Start from a copy of a, then loop over b with get(key, 0).\n\n"
            "Return: the merged dictionary."
        ),
        solution=('def merge_counts(a, b):\n'
                  '    out = dict(a)\n'
                  '    for key, n in b.items():\n'
                  '        out[key] = out.get(key, 0) + n\n'
                  '    return out\n'),
        trap=('def merge_counts(a, b):\n'
              '    out = dict(a)\n'
              '    for key, n in b.items():\n'
              '        out[key] = n\n'
              '    return out\n'),
        note="out[key] = n overwrites: night becomes 2, not 3. get(key, 0)"
             " + n reads what is there -- or 0 -- and adds. dict(a) makes"
             " a copy so the caller's dictionary is not changed, which a"
             " function should not do without saying so. collections."
             "Counter supports a + b directly, for later.",
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
