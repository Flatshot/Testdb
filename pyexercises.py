"""Python practice exercises: fifteen functions, one simple loop each.

The twenty-third Python set, the sixth of single loops: every question
asks for a function built around ONE for or while loop over plain numbers
or strings -- counting, searching, building, reducing -- with no import
and no row-shaped data. The examples lean on the bike scheme on the SQL
tab: ride lengths in minutes, fares in cents, lists of station names.
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
        id=1, ledger="P341", concept="PY4 for count over", tier="1 - Counting",
        title="Rides longer than the free half hour", kind="function",
        func="count_over",
        cases=[([12, 31, 45, 30], 30), ([], 30), ([5, 6], 30), ([31], 30)],
        prompt=(
            "Write a function `count_over(minutes, limit)` that returns"
            " how many ride lengths are STRICTLY longer than limit. A for"
            " loop with an if on m > limit and a counter; a ride of"
            " exactly the limit is not over it.\n\n"
            "  count_over([12, 31, 45, 30], 30) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_over(minutes, limit):\n"
                  "    n = 0\n"
                  "    for m in minutes:\n"
                  "        if m > limit:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_over(minutes, limit):\n"
              "    n = 0\n"
              "    for m in minutes:\n"
              "        if m >= limit:\n"
              "            n += 1\n"
              "    return n\n"),
        note="The scheme's free period is thirty minutes INCLUSIVE, so a"
             " thirty-minute ride is not over it: the test is a strict >."
             " With >= the thirty-minute ride is counted and the answer"
             " for the example is 3.",
    ),
    dict(
        id=2, ledger="P342", concept="PY4 for sum", tier="1 - Counting",
        title="The fares added up", kind="function",
        func="total_fares",
        cases=[([200, 0, 350, 0],), ([],), ([0, 0],), ([999],)],
        prompt=(
            "Write a function `total_fares(fares)` that returns the sum"
            " of a list of fares in cents, 0 for an empty list, using a"
            " for loop and a running total rather than sum().\n\n"
            "  total_fares([200, 0, 350, 0]) -> 550\n\n"
            "Return: an integer."
        ),
        solution=("def total_fares(fares):\n"
                  "    total = 0\n"
                  "    for f in fares:\n"
                  "        total += f\n"
                  "    return total\n"),
        trap=("def total_fares(fares):\n"
              "    total = 0\n"
              "    for f in fares:\n"
              "        total = f\n"
              "    return total\n"),
        note="total = f replaces the total with each fare instead of"
             " adding to it, so the function returns the LAST fare -- 0"
             " for the example. The accumulator pattern is total += f,"
             " starting from 0.",
    ),
    dict(
        id=3, ledger="P343", concept="PY4 for seen count", tier="1 - Counting",
        title="How many different stations were visited", kind="function",
        func="stations_visited",
        cases=[(["Harbour", "Cathedral", "Harbour", "Stadium"],), ([],), (["Hilltop"],), (["A", "A", "A"],)],
        prompt=(
            "Write a function `stations_visited(stops)` that returns how"
            " many DIFFERENT station names appear in a list of stops. A"
            " for loop with a set of names seen so far and a counter"
            " that moves only when the name is new.\n\n"
            "  stations_visited([\"Harbour\", \"Cathedral\", \"Harbour\","
            " \"Stadium\"]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def stations_visited(stops):\n"
                  "    seen = set()\n"
                  "    n = 0\n"
                  "    for s in stops:\n"
                  "        if s not in seen:\n"
                  "            seen.add(s)\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def stations_visited(stops):\n"
              "    seen = set()\n"
              "    n = 0\n"
              "    for s in stops:\n"
              "        if s in seen:\n"
              "            n += 1\n"
              "        seen.add(s)\n"
              "    return n\n"),
        note="The counter moves for a NEW name, which is 'not in seen';"
             " counting the names already seen gives the number of"
             " repeat visits instead, 1 for the example. The set does the"
             " remembering either way.",
    ),
    dict(
        id=4, ledger="P344", concept="PY4 for neighbours same", tier="1 - Counting",
        title="Rides that ended where the last one did", kind="function",
        func="count_same_as_previous",
        cases=[(["Harbour", "Harbour", "Stadium", "Stadium", "Stadium"],), ([],), (["A"],), (["A", "B", "A"],)],
        prompt=(
            "Write a function `count_same_as_previous(ends)` that returns"
            " how many end stations in the list are the same as the one"
            " before them. A for loop over range(1, len(ends)) comparing"
            " ends[i] with ends[i - 1].\n\n"
            "  count_same_as_previous([\"Harbour\", \"Harbour\", \"Stadium\","
            " \"Stadium\", \"Stadium\"]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def count_same_as_previous(ends):\n"
                  "    n = 0\n"
                  "    for i in range(1, len(ends)):\n"
                  "        if ends[i] == ends[i - 1]:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_same_as_previous(ends):\n"
              "    n = 0\n"
              "    for i in range(1, len(ends)):\n"
              "        if ends[i] == ends[0]:\n"
              "            n += 1\n"
              "    return n\n"),
        note="The previous item is ends[i - 1], one step back from"
             " wherever the loop is; ends[0] is always the FIRST item,"
             " which turns the question into 'how many match the first"
             " stop'. Starting the loop at 1 keeps i - 1 inside the list.",
    ),
    # ========================================================= 2 Searching
    dict(
        id=5, ledger="P345", concept="PY4 for first index", tier="2 - Searching",
        title="The first free ride", kind="function",
        func="first_free",
        cases=[([200, 350, 0, 0], ), ([200, 150],), ([],), ([0],)],
        prompt=(
            "Write a function `first_free(fares)` that returns the"
            " POSITION of the first fare that is 0, or -1 if every fare"
            " was charged. A for loop over enumerate(fares) with a return"
            " inside it.\n\n"
            "  first_free([200, 350, 0, 0]) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def first_free(fares):\n"
                  "    for i, f in enumerate(fares):\n"
                  "        if f == 0:\n"
                  "            return i\n"
                  "    return -1\n"),
        trap=("def first_free(fares):\n"
              "    for i, f in enumerate(fares):\n"
              "        if f == 0:\n"
              "            return i\n"
              "    return 0\n"),
        note="The value after the loop is the no-match answer, and the"
             " question says -1. Returning 0 there says 'the first ride"
             " was free' for a list where nothing was -- 0 is a real"
             " position, which is why -1 is the usual sentinel.",
    ),
    dict(
        id=6, ledger="P346", concept="PY4 for max by hand", tier="2 - Searching",
        title="The longest ride, by hand", kind="function",
        func="longest_ride",
        cases=[([12, 31, 8, 45, 20],), ([3],), ([7, 7],), ([240, 1],)],
        prompt=(
            "Write a function `longest_ride(minutes)` that returns the"
            " largest value in a non-empty list WITHOUT max(): a best so"
            " far that starts at minutes[0] and a for loop that replaces"
            " it when a value is bigger.\n\n"
            "  longest_ride([12, 31, 8, 45, 20]) -> 45\n\n"
            "Return: the value."
        ),
        solution=("def longest_ride(minutes):\n"
                  "    best = minutes[0]\n"
                  "    for m in minutes:\n"
                  "        if m > best:\n"
                  "            best = m\n"
                  "    return best\n"),
        trap=("def longest_ride(minutes):\n"
              "    best = minutes[0]\n"
              "    for m in minutes:\n"
              "        if m > best:\n"
              "            best = m\n"
              "        return best\n"),
        note="The return is indented inside the loop in the trap, so the"
             " function answers after looking at the first value only --"
             " 12 for the example. The return belongs after the loop, at"
             " the level of the for.",
    ),
    dict(
        id=7, ledger="P347", concept="PY4 for any match", tier="2 - Searching",
        title="Did any ride end where it started?", kind="function",
        func="any_round_trip",
        cases=[([("A", "B"), ("C", "C")],), ([("A", "B")],), ([],), ([("X", "X")],)],
        prompt=(
            "Write a function `any_round_trip(rides)` that returns True"
            " when any (start, end) pair in the list has the same station"
            " at both ends, and False otherwise. A for loop that unpacks"
            " each pair -- for start, end in rides -- with a return True"
            " at the first match, then False after the loop.\n\n"
            "  any_round_trip([(\"A\", \"B\"), (\"C\", \"C\")]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def any_round_trip(rides):\n"
                  "    for start, end in rides:\n"
                  "        if start == end:\n"
                  "            return True\n"
                  "    return False\n"),
        trap=("def any_round_trip(rides):\n"
              "    for start, end in rides:\n"
              "        if start == end:\n"
              "            return True\n"
              "        return False\n"),
        note="A for loop can unpack each tuple into two names as it goes."
             " The False has to wait until the loop is over; inside the"
             " loop it fires on the first pair that does NOT match, and"
             " the example comes out False.",
    ),
    dict(
        id=8, ledger="P348", concept="PY4 for last match", tier="2 - Searching",
        title="The last station a bike reached", kind="function",
        func="last_visit",
        cases=[(["Harbour", "Stadium", "Harbour", "Cathedral"], "Harbour"), (["A", "B"], "C"), ([], "A"), (["A"], "A")],
        prompt=(
            "Write a function `last_visit(stops, station)` that returns"
            " the POSITION of the last stop equal to station, or -1 if it"
            " never appears. A for loop over range(len(stops)) that"
            " records every match and returns the record after the"
            " loop.\n\n"
            "  last_visit([\"Harbour\", \"Stadium\", \"Harbour\", \"Cathedral\"],"
            " \"Harbour\") -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def last_visit(stops, station):\n"
                  "    found = -1\n"
                  "    for i in range(len(stops)):\n"
                  "        if stops[i] == station:\n"
                  "            found = i\n"
                  "    return found\n"),
        trap=("def last_visit(stops, station):\n"
              "    for i in range(len(stops)):\n"
              "        if stops[i] == station:\n"
              "            return i\n"
              "    return -1\n"),
        note="Returning at the first match gives the FIRST position, 0"
             " for the example; the last match needs the loop to run on,"
             " overwriting a variable, and return after it. Starting that"
             " variable at -1 handles the no-match case.",
    ),
    # ========================================================== 3 Building
    dict(
        id=9, ledger="P349", concept="PY4 for cap values", tier="3 - Building",
        title="Fares capped at a maximum", kind="function",
        func="capped",
        cases=[([200, 650, 300], 500), ([], 500), ([500], 500), ([700, 800], 500)],
        prompt=(
            "Write a function `capped(fares, cap)` that returns a new"
            " list where every fare above cap is replaced by cap and the"
            " rest are unchanged, in order. A for loop with an if / else"
            " and an append.\n\n"
            "  capped([200, 650, 300], 500) -> [200, 500, 300]\n\n"
            "Return: the new list."
        ),
        solution=("def capped(fares, cap):\n"
                  "    out = []\n"
                  "    for f in fares:\n"
                  "        if f > cap:\n"
                  "            out.append(cap)\n"
                  "        else:\n"
                  "            out.append(f)\n"
                  "    return out\n"),
        trap=("def capped(fares, cap):\n"
              "    out = []\n"
              "    for f in fares:\n"
              "        if f > cap:\n"
              "            out.append(cap)\n"
              "    return out\n"),
        note="A transforming loop appends SOMETHING for every item: the"
             " cap when the fare is over it, the fare itself otherwise."
             " Without the else the fares under the cap are dropped and"
             " the list shrinks to the capped ones. min(f, cap) is the"
             " one-expression form of the if / else.",
    ),
    dict(
        id=10, ledger="P350", concept="PY4 for format strings", tier="3 - Building",
        title="Ride lengths as labels", kind="function",
        func="labels",
        cases=[([12, 31],), ([],), ([1],), ([0, 240],)],
        prompt=(
            "Write a function `labels(minutes)` that returns a list of"
            " strings like '12 min' for each ride length, in order. A for"
            " loop that appends an f-string f\"{m} min\".\n\n"
            "  labels([12, 31]) -> [\"12 min\", \"31 min\"]\n\n"
            "Return: the list of strings."
        ),
        solution=("def labels(minutes):\n"
                  "    out = []\n"
                  "    for m in minutes:\n"
                  "        out.append(f\"{m} min\")\n"
                  "    return out\n"),
        trap=("def labels(minutes):\n"
              "    out = []\n"
              "    for m in minutes:\n"
              "        out.append(m + \" min\")\n"
              "    return out\n"),
        note="An f-string converts the number to text as it builds the"
             " label; m + ' min' tries to add an int to a str and raises"
             " TypeError. str(m) + ' min' would also work -- the point is"
             " that the conversion has to happen somewhere.",
    ),
    dict(
        id=11, ledger="P351", concept="PY4 for if else build", tier="3 - Building",
        title="Short or long, ride by ride", kind="function",
        func="classify",
        cases=[([12, 31, 30],), ([],), ([45],), ([1, 2, 3],)],
        prompt=(
            "Write a function `classify(minutes)` that returns a list"
            " with 'long' for each ride over 30 minutes and 'short' for"
            " the rest, in order. A for loop with an if / else deciding"
            " which word to append.\n\n"
            "  classify([12, 31, 30]) -> [\"short\", \"long\", \"short\"]\n\n"
            "Return: the list of strings."
        ),
        solution=("def classify(minutes):\n"
                  "    out = []\n"
                  "    for m in minutes:\n"
                  "        if m > 30:\n"
                  "            out.append(\"long\")\n"
                  "        else:\n"
                  "            out.append(\"short\")\n"
                  "    return out\n"),
        trap=("def classify(minutes):\n"
              "    out = []\n"
              "    for m in minutes:\n"
              "        if m > 30:\n"
              "            out.append(\"long\")\n"
              "        if m < 30:\n"
              "            out.append(\"short\")\n"
              "    return out\n"),
        note="Two separate ifs leave a gap: a ride of exactly 30 minutes"
             " is neither over nor under, so nothing is appended and the"
             " list comes back one short. if / else covers every value"
             " exactly once, which is what a classification needs.",
    ),
    dict(
        id=12, ledger="P352", concept="PY4 for digits only", tier="3 - Building",
        title="Just the digits of a station code", kind="function",
        func="digits_only",
        cases=[("ST-042",), ("Dock 7B",), ("abc",), ("",)],
        prompt=(
            "Write a function `digits_only(s)` that returns a string of"
            " the digit characters of s, in order, with everything else"
            " left out. A for loop over the characters with an if on"
            " ch.isdigit() and a result string built with +=.\n\n"
            "  digits_only(\"ST-042\") -> \"042\"\n\n"
            "Return: the string."
        ),
        solution=("def digits_only(s):\n"
                  "    out = \"\"\n"
                  "    for ch in s:\n"
                  "        if ch.isdigit():\n"
                  "            out += ch\n"
                  "    return out\n"),
        trap=("def digits_only(s):\n"
              "    out = 0\n"
              "    for ch in s:\n"
              "        if ch.isdigit():\n"
              "            out += int(ch)\n"
              "    return out\n"),
        note="The result is a STRING of digits, so the accumulator starts"
             " as '' and the characters are added as characters. Starting"
             " at 0 and adding int(ch) sums the digits instead -- 6 for"
             " 'ST-042' -- and loses the leading zero for good.",
    ),
    # ========================================================== 4 Reducing
    dict(
        id=13, ledger="P353", concept="PY4 for longest run", tier="4 - Reducing",
        title="The longest run of free rides", kind="function",
        func="longest_free_run",
        cases=[([0, 0, 200, 0, 0, 0, 150],), ([],), ([200, 300],), ([0],)],
        prompt=(
            "Write a function `longest_free_run(fares)` that returns the"
            " length of the longest stretch of consecutive fares that are"
            " 0. A for loop with a current run that grows on a 0 and"
            " resets to 0 on anything else, and a best so far.\n\n"
            "  longest_free_run([0, 0, 200, 0, 0, 0, 150]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def longest_free_run(fares):\n"
                  "    best = 0\n"
                  "    run = 0\n"
                  "    for f in fares:\n"
                  "        if f == 0:\n"
                  "            run += 1\n"
                  "        else:\n"
                  "            run = 0\n"
                  "        if run > best:\n"
                  "            best = run\n"
                  "    return best\n"),
        trap=("def longest_free_run(fares):\n"
              "    best = 0\n"
              "    run = 0\n"
              "    for f in fares:\n"
              "        if f == 0:\n"
              "            run += 1\n"
              "        if run > best:\n"
              "            best = run\n"
              "    return best\n"),
        note="The reset is the line that is easy to forget: without it"
             " the run keeps counting across the paid rides and the"
             " example gives 5 instead of 3. Two trackers, the current"
             " run and the best, and the best is updated every pass.",
    ),
    dict(
        id=14, ledger="P354", concept="PY4 for min gap", tier="4 - Reducing",
        title="The shortest wait between rides", kind="function",
        func="min_gap",
        cases=[([10, 25, 27, 60],), ([5],), ([],), ([3, 3, 9],)],
        prompt=(
            "Write a function `min_gap(starts)` that returns the smallest"
            " difference between neighbouring start times in a list"
            " already in order, or None for fewer than two. A for loop"
            " over range(1, len(starts)) with a best that starts as None"
            " and is replaced when the gap is smaller or the best is"
            " still None.\n\n"
            "  min_gap([10, 25, 27, 60]) -> 2\n\n"
            "Return: the gap, or None."
        ),
        solution=("def min_gap(starts):\n"
                  "    best = None\n"
                  "    for i in range(1, len(starts)):\n"
                  "        gap = starts[i] - starts[i - 1]\n"
                  "        if best is None or gap < best:\n"
                  "            best = gap\n"
                  "    return best\n"),
        trap=("def min_gap(starts):\n"
              "    best = 0\n"
              "    for i in range(1, len(starts)):\n"
              "        gap = starts[i] - starts[i - 1]\n"
              "        if gap < best:\n"
              "            best = gap\n"
              "    return best\n"),
        note="A minimum cannot start at 0 -- no positive gap is ever"
             " smaller than that, so the trap returns 0 for every list."
             " Starting at None with 'best is None or' in the test takes"
             " the first gap whatever it is, and gives None when there"
             " are no gaps at all.",
    ),
    dict(
        id=15, ledger="P355", concept="PY4 for budget break", tier="4 - Reducing",
        title="How many rides a balance pays for", kind="function",
        func="rides_affordable",
        cases=[(1000, [200, 350, 300, 400]), (500, [200, 300]), (100, [100]), (0, [])],
        prompt=(
            "Write a function `rides_affordable(balance, fares)` that"
            " returns how many of the fares, taken in order, the balance"
            " can pay before it runs short -- a fare EQUAL to what is left"
            " can still be paid. A for loop that breaks as soon as a fare"
            " is more than the balance, otherwise subtracts it and counts"
            " the ride.\n\n"
            "  rides_affordable(1000, [200, 350, 300, 400]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def rides_affordable(balance, fares):\n"
                  "    n = 0\n"
                  "    for f in fares:\n"
                  "        if f > balance:\n"
                  "            break\n"
                  "        balance -= f\n"
                  "        n += 1\n"
                  "    return n\n"),
        trap=("def rides_affordable(balance, fares):\n"
              "    n = 0\n"
              "    for f in fares:\n"
              "        if f >= balance:\n"
              "            break\n"
              "        balance -= f\n"
              "        n += 1\n"
              "    return n\n"),
        note="The break condition is the whole question: a fare greater"
             " than the balance cannot be paid, a fare equal to it can."
             " With >= the ride that uses up the last cent is refused, so"
             " 500 pays for one of [200, 300] instead of both. The"
             " subtraction and the count come after the test, so a"
             " refused fare is neither paid nor counted.",
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
