"""Python practice exercises: fifteen small functions over plain values.

The twenty-ninth Python set, at the simpler level of the last one -- no
dicts, no rows, no dates -- on constructs that set did not use, dressed in
the bike scheme's terms. Numbers: rounding UP to the next half hour by
floor division of a negative, a fare in tiers by if/elif, a standard
deviation in two passes with math.sqrt, a total split fairly with the
remainder spread, and whether a run of ids is unbroken. Text: an ordinal
suffix with the eleven-to-thirteen exception, a URL slug, a clock time
validated by int() and range checks, a word blanked out with stars of its
own length, and the longest common prefix of two names. Lists: a nested
list flattened by a double comprehension, a rota rotated by two slices,
a weighted average over zip, a moving average by windowed slices, and the
ids missing from a range by set difference.

Every question is a `kind="function"`: the editor defines a function named
`func`. Run calls it once per case in `cases` and shows each call and its
result; Check compares each result with the reference function's. Values
are compared, not their printed form, but the container type counts, so a
tuple is not a list, 2.0 is not 2, and 0 is not False.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py).
"""

import pyrun

EXERCISES = [
    # ============================================================== 1 Numbers
    dict(
        id=1, ledger="P431", concept="PY3 ceiling by floor division", tier="1 - Numbers",
        title="Billed to the next half hour", kind="function",
        func="billed_minutes",
        cases=[(31,), (30,), (0,), (61,), (89,)],
        prompt=(
            "Rides are billed in half hours, always rounded UP: 31"
            " minutes is billed as 60, 30 as 30, 0 as 0. Write a"
            " function `billed_minutes(minutes)` that returns the billed"
            " figure. The trick is -(-minutes // 30) * 30: floor"
            " division of the negative rounds towards minus infinity,"
            " which is up once the sign is flipped back.\n\n"
            "  billed_minutes(31) -> 60\n\n"
            "Return: an int."
        ),
        solution=("def billed_minutes(minutes):\n"
                  "    return -(-minutes // 30) * 30\n"),
        trap=("def billed_minutes(minutes):\n"
              "    return minutes // 30 * 30\n"),
        note="minutes // 30 * 30 rounds DOWN, so 31 minutes is billed as"
             " 30 and 89 as 60: the trap gives every ride a free part"
             " half hour. Negating before and after the floor division"
             " turns the floor into a ceiling without importing"
             " math.ceil, and 30 // 30 is exactly 1, so a whole half"
             " hour is not rounded up to the next.",
    ),
    dict(
        id=2, ledger="P432", concept="PY3 if/elif tiers", tier="1 - Numbers",
        title="A fare in three tiers", kind="function",
        func="tiered_fare",
        cases=[(20,), (30,), (45,), (60,), (90,)],
        prompt=(
            "A casual fare: the first 30 minutes are free, minutes 31"
            " to 60 cost 10 cents each, and every minute after 60 costs"
            " 20. Write a function `tiered_fare(minutes)` that returns"
            " the fare in cents: an if/elif/else on the minutes, each"
            " branch computing its own tier on top of the ones below.\n\n"
            "  tiered_fare(45) -> 150\n\n"
            "Return: an int."
        ),
        solution=("def tiered_fare(minutes):\n"
                  "    if minutes <= 30:\n"
                  "        return 0\n"
                  "    elif minutes <= 60:\n"
                  "        return (minutes - 30) * 10\n"
                  "    else:\n"
                  "        return 300 + (minutes - 60) * 20\n"),
        trap=("def tiered_fare(minutes):\n"
              "    if minutes <= 30:\n"
              "        return 0\n"
              "    elif minutes <= 60:\n"
              "        return (minutes - 30) * 10\n"
              "    else:\n"
              "        return (minutes - 60) * 20\n"),
        note="The top tier sits on top of the middle one: a 90-minute"
             " ride pays the full 300 cents for minutes 31 to 60 AND 600"
             " for the thirty after, so the trap, which forgets the 300,"
             " charges a 61-minute ride 20 cents when a 60-minute ride"
             " pays 300. The boundaries are <= on both tests so that"
             " exactly 30 is free and exactly 60 is in the middle tier.",
    ),
    dict(
        id=3, ledger="P433", concept="PY3 two-pass std dev", tier="1 - Numbers",
        title="How much ride lengths vary", kind="function",
        func="std_dev",
        cases=[([10, 20, 30, 40, 50],), ([25, 25, 25],), ([3, 9],), ([],)],
        prompt=(
            "Write a function `std_dev(minutes)` that returns the"
            " population standard deviation to two decimals, or None for"
            " an empty list. Two passes: the mean first, then the mean"
            " of the squared differences from it, and math.sqrt of that"
            " -- write `import math` at the top.\n\n"
            "  std_dev([10, 20, 30, 40, 50]) -> 14.14\n\n"
            "Return: a float, or None."
        ),
        solution=("import math\n\n"
                  "def std_dev(minutes):\n"
                  "    if not minutes:\n"
                  "        return None\n"
                  "    mean = sum(minutes) / len(minutes)\n"
                  "    var = sum((m - mean) ** 2 for m in minutes) / len(minutes)\n"
                  "    return round(math.sqrt(var), 2)\n"),
        trap=("def std_dev(minutes):\n"
              "    if not minutes:\n"
              "        return None\n"
              "    mean = sum(minutes) / len(minutes)\n"
              "    var = sum((m - mean) ** 2 for m in minutes) / len(minutes)\n"
              "    return round(var, 2)\n"),
        note="The mean of the squared differences is the VARIANCE, in"
             " squared minutes; the standard deviation is its square"
             " root, back in minutes, which is why the trap's 200.0 is"
             " not the 14.14 asked for. The squaring needs the mean"
             " first, hence two passes over the list. Identical values"
             " have a deviation of 0.0.",
    ),
    dict(
        id=4, ledger="P434", concept="PY3 fair split with remainder", tier="1 - Numbers",
        title="A group fare split fairly", kind="function",
        func="split_fare",
        cases=[(1000, 3), (1000, 4), (7, 3), (0, 2)],
        prompt=(
            "A group's fare in cents is split between n riders so that"
            " the shares add up EXACTLY and differ by at most one cent,"
            " the extra cents going to the first riders. Write a"
            " function `split_fare(total, n)` that returns the n"
            " shares: total // n each, plus 1 for the first total % n"
            " of them -- a comprehension over range(n) with a"
            " conditional.\n\n"
            "  split_fare(1000, 3) -> [334, 333, 333]\n\n"
            "Return: a list of ints."
        ),
        solution=("def split_fare(total, n):\n"
                  "    base, extra = divmod(total, n)\n"
                  "    return [base + 1 if i < extra else base for i in range(n)]\n"),
        trap=("def split_fare(total, n):\n"
              "    return [total // n] * n\n"),
        note="total // n alone loses the remainder: the trap splits"
             " 1,000 into three 333s and a cent goes missing. divmod"
             " gives the base share and the leftover cents in one call,"
             " and `i < extra` hands one cent each to the first `extra`"
             " riders. The shares always sum back to the total, which"
             " is the whole point of splitting money this way.",
    ),
    dict(
        id=5, ledger="P435", concept="PY3 unbroken run check", tier="1 - Numbers",
        title="Are the ride ids unbroken?", kind="function",
        func="is_unbroken",
        cases=[([3, 1, 2],), ([1, 2, 4],), ([1, 1, 3],), ([],), ([9],)],
        prompt=(
            "A day's ride ids should run without gaps or repeats,"
            " whatever order they were logged in. Write a function"
            " `is_unbroken(ids)` that returns True when the ids are"
            " exactly the integers from the smallest to the largest,"
            " each once, and True for an empty list. Three facts have"
            " to hold at once: no duplicates (len of the set equals"
            " len of the list) and the count equals max - min + 1.\n\n"
            "  is_unbroken([3, 1, 2]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def is_unbroken(ids):\n"
                  "    if not ids:\n"
                  "        return True\n"
                  "    return len(set(ids)) == len(ids) and max(ids) - min(ids) + 1 == len(ids)\n"),
        trap=("def is_unbroken(ids):\n"
              "    if not ids:\n"
              "        return True\n"
              "    return max(ids) - min(ids) + 1 == len(ids)\n"),
        note="The span test alone is fooled by a duplicate standing in"
             " for a missing number: [1, 1, 3] spans three values and"
             " has three items, so the trap says True although 2 is"
             " missing. The set test catches the repeat, and the two"
             " tests together pin the list down to a run. The empty"
             " list needs its own answer, since max() of nothing is an"
             " error.",
    ),
    # ================================================================= 2 Text
    dict(
        id=6, ledger="P436", concept="PY3 ordinal suffix", tier="2 - Text",
        title="1st, 2nd, 3rd, 11th", kind="function",
        func="ordinal",
        cases=[(1,), (2,), (3,), (4,), (11,), (12,), (13,), (21,), (22,), (23,), (101,), (111,), (112,)],
        prompt=(
            "Write a function `ordinal(n)` that returns the number with"
            " its English suffix: 1st, 2nd, 3rd, 4th, 11th, 12th, 13th,"
            " 21st, 101st, 111th. The suffix depends on n % 10 -- 1,"
            " 2, 3 for st, nd, rd, anything else th -- EXCEPT that 11,"
            " 12 and 13 (n % 100) take th.\n\n"
            "  ordinal(22) -> \"22nd\"\n\n"
            "Return: a str."
        ),
        solution=("def ordinal(n):\n"
                  "    if n % 100 in (11, 12, 13):\n"
                  "        suffix = \"th\"\n"
                  "    else:\n"
                  "        suffix = {1: \"st\", 2: \"nd\", 3: \"rd\"}.get(n % 10, \"th\")\n"
                  "    return f\"{n}{suffix}\"\n"),
        trap=("def ordinal(n):\n"
              "    suffix = {1: \"st\", 2: \"nd\", 3: \"rd\"}.get(n % 10, \"th\")\n"
              "    return f\"{n}{suffix}\"\n"),
        note="The last digit decides the suffix for every number but the"
             " teens: 11, 12 and 13 end in 1, 2 and 3 yet take th, and"
             " so do 111, 112, 113 and every other hundred. The trap"
             " writes 11st and 112nd. Testing n % 100 first and then"
             " n % 10 gets both rules in two lines; the small dict with"
             " a default is a tidy way to write the three special"
             " endings.",
    ),
    dict(
        id=7, ledger="P437", concept="PY3 slug", tier="2 - Text",
        title="A station name as a web address", kind="function",
        func="slug",
        cases=[("Market Square",), ("Old Mill",), ("Harbour",), ("Station Approach",)],
        prompt=(
            "Write a function `slug(name)` that turns a station name"
            " into the form used in a web address: all lower case,"
            " spaces replaced by hyphens. lower() and replace(), in"
            " either order.\n\n"
            "  slug(\"Market Square\") -> \"market-square\"\n\n"
            "Return: a str."
        ),
        solution=("def slug(name):\n"
                  "    return name.lower().replace(\" \", \"-\")\n"),
        trap=("def slug(name):\n"
              "    return name.replace(\" \", \"-\")\n"),
        note="Two string methods chained: each returns a new string,"
             " and the next method is called on that, so the order does"
             " not matter here. The trap keeps the capitals, and"
             " 'Market-Square' is a different address from"
             " 'market-square' on most servers. Strings are never"
             " changed in place; the result has to be returned.",
    ),
    dict(
        id=8, ledger="P438", concept="PY3 validate a clock time", tier="2 - Text",
        title="Is it a time of day?", kind="function",
        func="is_clock_time",
        cases=[("08:05",), ("23:59",), ("24:00",), ("8:05",), ("12:60",), ("ab:cd",)],
        prompt=(
            "Write a function `is_clock_time(s)` that returns True for"
            " a five-character 'HH:MM' with hours 00 to 23 and minutes"
            " 00 to 59, and False for anything else. Check the shape"
            " first -- length 5, a colon at position 2, digits either"
            " side -- and only then convert with int() and test the"
            " ranges.\n\n"
            "  is_clock_time(\"08:05\") -> True\n\n"
            "Return: True or False."
        ),
        solution=("def is_clock_time(s):\n"
                  "    if len(s) != 5 or s[2] != \":\" or not (s[:2].isdigit() and s[3:].isdigit()):\n"
                  "        return False\n"
                  "    return int(s[:2]) < 24 and int(s[3:]) < 60\n"),
        trap=("def is_clock_time(s):\n"
              "    return len(s) == 5 and s[2] == \":\" and s[:2].isdigit() and s[3:].isdigit()\n"),
        note="The shape test is only half of it: '24:00' and '12:60'"
             " are five characters, a colon and four digits, and the"
             " trap accepts both. The ranges need numbers, so int()"
             " comes after the digit check -- int('ab') would raise --"
             " and the function returns False early when the shape is"
             " wrong so that the conversion is never reached.",
    ),
    dict(
        id=9, ledger="P439", concept="PY3 replace with computed string", tier="2 - Text",
        title="A word blanked out", kind="function",
        func="censor",
        cases=[("ride to Harbour then Harbour again", "Harbour"), ("Market Square", "Square"), ("no match here", "bike"), ("aaa", "a")],
        prompt=(
            "Write a function `censor(text, word)` that returns the text"
            " with every occurrence of the word replaced by stars, as"
            " many stars as the word has characters, so the line keeps"
            " its length. One replace() whose replacement is '*' *"
            " len(word).\n\n"
            "  censor(\"Market Square\", \"Square\") -> \"Market ******\"\n\n"
            "Return: a str."
        ),
        solution=("def censor(text, word):\n"
                  "    return text.replace(word, \"*\" * len(word))\n"),
        trap=("def censor(text, word):\n"
              "    return text.replace(word, \"***\")\n"),
        note="replace() swaps every occurrence, not just the first, so"
             " one call handles 'Harbour' twice. The replacement is"
             " computed from the word's length; the trap's fixed three"
             " stars shorten the line and give away how long the word"
             " was not. Replacing 'a' in 'aaa' gives '***' either way,"
             " which is why that case alone would not catch it.",
    ),
    dict(
        id=10, ledger="P440", concept="PY3 common prefix by loop", tier="2 - Text",
        title="Where two names stop agreeing", kind="function",
        func="common_prefix",
        cases=[("Harbour", "Harbourside"), ("Hilltop", "Hillside"), ("Stadium", "Station Approach"), ("Parkway", "Riverside")],
        prompt=(
            "Write a function `common_prefix(a, b)` that returns the"
            " characters the two strings share at the start, up to the"
            " first position where they differ. A loop over zip(a, b)"
            " comparing character by character, break on the first"
            " mismatch, and a slice of a up to that point.\n\n"
            "  common_prefix(\"Hilltop\", \"Hillside\") -> \"Hill\"\n\n"
            "Return: a str, possibly empty."
        ),
        solution=("def common_prefix(a, b):\n"
                  "    n = 0\n"
                  "    for x, y in zip(a, b):\n"
                  "        if x != y:\n"
                  "            break\n"
                  "        n += 1\n"
                  "    return a[:n]\n"),
        trap=("def common_prefix(a, b):\n"
              "    if b.startswith(a):\n"
              "        return a\n"
              "    if a.startswith(b):\n"
              "        return b\n"
              "    return \"\"\n"),
        note="startswith only knows whether ONE string is wholly at the"
             " front of the other: it finds 'Harbour' inside"
             " 'Harbourside' but answers nothing for Hilltop and"
             " Hillside, which share four characters and then part. zip"
             " stops at the shorter string, so no index can run off the"
             " end, and break leaves n at the first mismatch.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=11, ledger="P441", concept="PY3 nested comprehension flatten", tier="3 - Lists",
        title="Every stop on every route, in one list", kind="function",
        func="flatten",
        cases=[([[1, 3, 5], [5, 9], [2]],), ([[], [7, 7]],), ([],), ([[4]],)],
        prompt=(
            "Routes are lists of station ids, and a day's routes are a"
            " list of those lists. Write a function `flatten(routes)`"
            " that returns all the stops in one flat list, in order,"
            " repeats kept. One comprehension with two for clauses:"
            " [s for route in routes for s in route].\n\n"
            "  flatten([[1, 3, 5], [5, 9], [2]]) -> [1, 3, 5, 5, 9, 2]\n\n"
            "Return: a list of ints."
        ),
        solution=("def flatten(routes):\n"
                  "    return [s for route in routes for s in route]\n"),
        trap=("def flatten(routes):\n"
              "    return [route for route in routes]\n"),
        note="Two for clauses in one comprehension nest like two loops,"
             " outer first: for each route, for each stop in it, take"
             " the stop. A single clause, the trap, copies the list of"
             " lists as it is, still nested. An empty inner list"
             " contributes nothing and an empty outer list gives [].",
    ),
    dict(
        id=12, ledger="P442", concept="PY3 rotate by slices", tier="3 - Lists",
        title="The rota, rotated", kind="function",
        func="rotate",
        cases=[([1, 2, 3, 4, 5], 2), ([1, 2, 3, 4, 5], 0), ([1, 2, 3], 1), ([], 3)],
        prompt=(
            "Each week the duty rota moves on: the first k names go to"
            " the end. Write a function `rotate(names, k)` that returns"
            " the rotated list without changing the original: the"
            " slice from k onwards, then the slice up to k, added"
            " together.\n\n"
            "  rotate([1, 2, 3, 4, 5], 2) -> [3, 4, 5, 1, 2]\n\n"
            "Return: a list."
        ),
        solution=("def rotate(names, k):\n"
                  "    return names[k:] + names[:k]\n"),
        trap=("def rotate(names, k):\n"
              "    return names[-k:] + names[:-k]\n"),
        note="names[k:] + names[:k] moves the FIRST k items to the end;"
             " the trap's names[-k:] + names[:-k] moves the last k to"
             " the front, a rotation the other way -- and with k = 0,"
             " names[-0:] is the whole list, so it returns the list"
             " doubled. Slicing makes new lists, so the caller's rota is"
             " untouched.",
    ),
    dict(
        id=13, ledger="P443", concept="PY3 weighted average over zip", tier="3 - Lists",
        title="An average that counts the busy stations more", kind="function",
        func="weighted_average",
        cases=[([3.2, 3.7, 2.7], [100, 300, 50]), ([5.0, 1.0], [1, 1]), ([4.0], [10]), ([], [])],
        prompt=(
            "Each station has an average ride length and a number of"
            " rides. Write a function `weighted_average(values,"
            " weights)` that returns the average of the values with"
            " each one counted as many times as its weight -- sum of"
            " value times weight over zip, divided by the sum of the"
            " weights -- rounded to two decimals, or None when the lists"
            " are empty.\n\n"
            "  weighted_average([3.2, 3.7, 2.7], [100, 300, 50]) -> 3.48\n\n"
            "Return: a float, or None."
        ),
        solution=("def weighted_average(values, weights):\n"
                  "    if not values:\n"
                  "        return None\n"
                  "    return round(sum(v * w for v, w in zip(values, weights)) / sum(weights), 2)\n"),
        trap=("def weighted_average(values, weights):\n"
              "    if not values:\n"
              "        return None\n"
              "    return round(sum(values) / len(values), 2)\n"),
        note="A plain average treats a station with 50 rides the same as"
             " one with 300: the trap answers 3.2 where the weighted"
             " figure is 3.48, pulled towards the busy station. zip"
             " walks the two lists in step so each value meets its own"
             " weight, and dividing by the sum of the weights, not the"
             " count, is what makes it an average again.",
    ),
    dict(
        id=14, ledger="P444", concept="PY3 moving average by windows", tier="3 - Lists",
        title="A smoothed line of daily rides", kind="function",
        func="moving_average",
        cases=[([10, 20, 30, 40, 50], 3), ([4, 8], 2), ([7, 7, 7], 1), ([1, 2], 3)],
        prompt=(
            "Write a function `moving_average(counts, k)` that returns"
            " the average of each run of k consecutive values, as"
            " floats: for k = 3 the first is the mean of items 0 to 2,"
            " the next of 1 to 3, and so on, with len(counts) - k + 1"
            " results -- none when the list is shorter than k. A"
            " comprehension over range(len(counts) - k + 1) with a"
            " slice counts[i:i + k].\n\n"
            "  moving_average([10, 20, 30, 40, 50], 3) -> [20.0, 30.0, 40.0]\n\n"
            "Return: a list of floats."
        ),
        solution=("def moving_average(counts, k):\n"
                  "    return [sum(counts[i:i + k]) / k for i in range(len(counts) - k + 1)]\n"),
        trap=("def moving_average(counts, k):\n"
              "    return [sum(counts[i:i + k]) / k for i in range(len(counts))]\n"),
        note="A window has to be full: the last one starts k - 1 from"
             " the end, so there are len - k + 1 of them. The trap runs"
             " a window from every position, and the final ones are"
             " short slices still divided by k, so the line tails off to"
             " values no real day had. When the list is shorter than k"
             " the range is empty and the result is [], which is"
             " correct.",
    ),
    dict(
        id=15, ledger="P445", concept="PY3 set difference against range", tier="3 - Lists",
        title="The ride ids missing from the log", kind="function",
        func="missing_ids",
        cases=[([5, 7, 8, 10],), ([1, 2, 3],), ([],), ([12, 10],)],
        prompt=(
            "Write a function `missing_ids(ids)` that returns the"
            " integers between the smallest and largest id that are"
            " absent, in ascending order, and [] for an empty list."
            " sorted(set(range(min(ids), max(ids) + 1)) - set(ids)),"
            " behind a guard.\n\n"
            "  missing_ids([5, 7, 8, 10]) -> [6, 9]\n\n"
            "Return: a list of ints."
        ),
        solution=("def missing_ids(ids):\n"
                  "    if not ids:\n"
                  "        return []\n"
                  "    return sorted(set(range(min(ids), max(ids) + 1)) - set(ids))\n"),
        trap=("def missing_ids(ids):\n"
              "    if not ids:\n"
              "        return []\n"
              "    return sorted(set(range(1, max(ids) + 1)) - set(ids))\n"),
        note="The range has to start at the smallest id present, not at"
             " 1: the trap reports 1 to 4 as missing from a log that"
             " begins at 5. range() stops before its end, hence the +"
             " 1 on the maximum. Set difference keeps what is in the"
             " first set and not the second, and sorted() turns the"
             " result back into the ordered list asked for.",
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
