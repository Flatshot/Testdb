"""Python practice exercises: fifteen functions in three shapes.

The twenty-fourth Python set, and a MIXED one: five one-tool functions on
tools no earlier set used (itertools.combinations, zip(*rows), bisect_left,
sum() with a start, list.sort(reverse=True)), five functions with one
simple loop, and five functions over BIKE-SCHEME ROWS -- lists of dicts
shaped like rides, with a member that is None for a casual rider: counting
the casual rides, a total per member, the longest ride's id, the members
who rode free, the members' average length.

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

RIDES = [{"ride_id": 1, "member": 7, "minutes": 12, "fare": 0},
         {"ride_id": 2, "member": None, "minutes": 25, "fare": 350},
         {"ride_id": 3, "member": 9, "minutes": 45, "fare": 100},
         {"ride_id": 4, "member": 7, "minutes": 60, "fare": 200},
         {"ride_id": 5, "member": None, "minutes": 8, "fare": 250},
         {"ride_id": 6, "member": 2, "minutes": 20, "fare": 0}]

EXERCISES = [
    # ============================================================= 1 One tool
    dict(
        id=1, ledger="P356", concept="PY3 combinations", tier="1 - One tool",
        title="itertools.combinations(): every pair of stations", kind="function",
        func="station_pairs",
        cases=[(["Harbour", "Stadium", "Hilltop"],), ([],), (["Solo"],), (["A", "B"],)],
        prompt=(
            "Write a function `station_pairs(stations)` that returns a"
            " list of every pair of stations as tuples, each pair once"
            " and in the order the stations were given, using list() over"
            " itertools.combinations(stations, 2). Write `import"
            " itertools` as the first line.\n\n"
            "  station_pairs([\"Harbour\", \"Stadium\", \"Hilltop\"]) ->"
            " [(\"Harbour\", \"Stadium\"), (\"Harbour\", \"Hilltop\"),"
            " (\"Stadium\", \"Hilltop\")]\n\n"
            "Return: the list of tuples."
        ),
        solution=("import itertools\n\n"
                  "def station_pairs(stations):\n"
                  "    return list(itertools.combinations(stations, 2))\n"),
        trap=("import itertools\n\n"
              "def station_pairs(stations):\n"
              "    return list(itertools.permutations(stations, 2))\n"),
        note="combinations() gives each pair once, in the order met;"
             " permutations() gives each pair both ways round, twice as"
             " many. The SQL side's self-join with < is the same idea."
             " Fewer than two stations means no pairs at all.",
    ),
    dict(
        id=2, ledger="P357", concept="PY3 zip star", tier="1 - One tool",
        title="zip(*rows): rows into columns", kind="function",
        func="columns",
        cases=[([[1, 2, 3], [4, 5, 6]],), ([[1, 2]],), ([],), ([["a", "b"], ["c", "d"], ["e", "f"]],)],
        prompt=(
            "Write a function `columns(rows)` that turns a list of"
            " equal-length rows into a list of columns, each column a"
            " LIST, using a list comprehension over zip(*rows) -- the"
            " star hands each row to zip as a separate argument. No"
            " import is needed.\n\n"
            "  columns([[1, 2, 3], [4, 5, 6]]) -> [[1, 4], [2, 5], [3, 6]]\n\n"
            "Return: the list of lists."
        ),
        solution="def columns(rows):\n    return [list(c) for c in zip(*rows)]\n",
        trap="def columns(rows):\n    return [list(c) for c in zip(rows)]\n",
        note="zip(*rows) unpacks the outer list so zip sees the rows side"
             " by side and pairs their first items, their second items,"
             " and so on -- the transpose. zip(rows) sees ONE argument"
             " and wraps each row in a tuple of one. The comprehension"
             " turns the tuples into lists.",
    ),
    dict(
        id=3, ledger="P358", concept="PY3 bisect", tier="1 - One tool",
        title="bisect.bisect_left(): how many are below", kind="function",
        func="count_below",
        cases=[([100, 200, 200, 350, 600], 200), ([100, 200], 50), ([], 10), ([5, 5, 5], 5)],
        prompt=(
            "Write a function `count_below(sorted_fares, x)` that returns"
            " how many fares in an already-SORTED list are strictly less"
            " than x, using bisect.bisect_left() -- the position where x"
            " would be inserted to keep the order, which is exactly that"
            " count. Write `import bisect` as the first line.\n\n"
            "  count_below([100, 200, 200, 350, 600], 200) -> 1\n\n"
            "Return: an integer."
        ),
        solution=("import bisect\n\n"
                  "def count_below(sorted_fares, x):\n"
                  "    return bisect.bisect_left(sorted_fares, x)\n"),
        trap=("import bisect\n\n"
              "def count_below(sorted_fares, x):\n"
              "    return bisect.bisect_right(sorted_fares, x)\n"),
        note="bisect_left finds the first position at or after which x"
             " belongs, so everything before it is strictly smaller;"
             " bisect_right goes past the equal values and counts them"
             " too -- 3 instead of 1 for the example. Both are binary"
             " searches and need the list sorted.",
    ),
    dict(
        id=4, ledger="P359", concept="PY3 sum start", tier="1 - One tool",
        title="sum(values, start): a total with an opening balance", kind="function",
        func="total_with_unlock",
        cases=[([50, 50, 100], 200), ([], 200), ([25], 0), ([10, 10], 150)],
        prompt=(
            "Write a function `total_with_unlock(charges, unlock)` that"
            " returns the unlock fee plus all the per-minute charges, in"
            " one call of sum() with its second argument, the START"
            " value. No import is needed.\n\n"
            "  total_with_unlock([50, 50, 100], 200) -> 400\n\n"
            "Return: an integer."
        ),
        solution="def total_with_unlock(charges, unlock):\n    return sum(charges, unlock)\n",
        trap="def total_with_unlock(charges, unlock):\n    return sum(charges)\n",
        note="sum() takes an optional start value that the total begins"
             " from -- 0 unless you say otherwise. The trap forgets the"
             " unlock fee entirely. sum(charges) + unlock says the same"
             " in two steps.",
    ),
    dict(
        id=5, ledger="P360", concept="PY3 sort reverse", tier="1 - One tool",
        title="sort(reverse=True): biggest first, in place", kind="function",
        func="longest_first",
        cases=[([12, 45, 8],), ([],), ([3, 3],), ([1, 2, 3],)],
        prompt=(
            "Write a function `longest_first(minutes)` that sorts the"
            " list itself from longest to shortest with sort(reverse="
            "True) and then returns that same list. No import is"
            " needed.\n\n"
            "  longest_first([12, 45, 8]) -> [45, 12, 8]\n\n"
            "Return: the list."
        ),
        solution="def longest_first(minutes):\n    minutes.sort(reverse=True)\n    return minutes\n",
        trap="def longest_first(minutes):\n    return minutes.sort(reverse=True)\n",
        note="list.sort() changes the list in place and returns None, so"
             " 'return minutes.sort(...)' returns nothing. Two lines:"
             " sort, then return the list. reverse=True flips the order"
             " without a second pass.",
    ),
    # ======================================================= 2 A simple loop
    dict(
        id=6, ledger="P361", concept="PY4 for count in tuple", tier="2 - A simple loop",
        title="How many rides were at the weekend", kind="function",
        func="weekend_rides",
        cases=[([1, 6, 0, 3, 6],), ([],), ([2, 3, 4],), ([0],)],
        prompt=(
            "Write a function `weekend_rides(days)` that returns how many"
            " of the weekday numbers are 0 or 6 -- Sunday or Saturday, as"
            " SQLite's strftime('%w') numbers them. A for loop with an if"
            " on d in (0, 6) and a counter.\n\n"
            "  weekend_rides([1, 6, 0, 3, 6]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def weekend_rides(days):\n"
                  "    n = 0\n"
                  "    for d in days:\n"
                  "        if d in (0, 6):\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def weekend_rides(days):\n"
              "    n = 0\n"
              "    for d in days:\n"
              "        if d == 0 or 6:\n"
              "            n += 1\n"
              "    return n\n"),
        note="'d == 0 or 6' is read as '(d == 0) or 6', and 6 is truthy,"
             " so the test is always true and every ride counts. 'd in"
             " (0, 6)' asks the question that was meant; so does"
             " 'd == 0 or d == 6'.",
    ),
    dict(
        id=7, ledger="P362", concept="PY4 for first repeat", tier="2 - A simple loop",
        title="The first station reached twice", kind="function",
        func="first_revisit",
        cases=[(["Harbour", "Stadium", "Harbour", "Stadium"],), (["A", "B"],), ([],), (["X", "X"],)],
        prompt=(
            "Write a function `first_revisit(stops)` that returns the"
            " first station whose SECOND visit comes earliest, or None"
            " when no station is visited twice. A for loop with a seen"
            " set, returning the stop the moment it is already in the"
            " set.\n\n"
            "  first_revisit([\"Harbour\", \"Stadium\", \"Harbour\","
            " \"Stadium\"]) -> \"Harbour\"\n\n"
            "Return: the station, or None."
        ),
        solution=("def first_revisit(stops):\n"
                  "    seen = set()\n"
                  "    for s in stops:\n"
                  "        if s in seen:\n"
                  "            return s\n"
                  "        seen.add(s)\n"
                  "    return None\n"),
        trap=("def first_revisit(stops):\n"
              "    seen = set()\n"
              "    for s in stops:\n"
              "        seen.add(s)\n"
              "        if s in seen:\n"
              "            return s\n"
              "    return None\n"),
        note="Check, then add. Adding first means every stop is 'already"
             " seen' the moment it is tested, so the first stop is"
             " returned whatever it is. The return after the loop is the"
             " no-revisit answer.",
    ),
    dict(
        id=8, ledger="P363", concept="PY4 for transform int", tier="2 - A simple loop",
        title="Fares after a discount", kind="function",
        func="discounted",
        cases=[([200, 350, 100], 10), ([], 50), ([99], 50), ([250], 0)],
        prompt=(
            "Write a function `discounted(fares, pct)` that returns a new"
            " list of the fares each reduced by pct per cent and rounded"
            " to a whole number of cents. A for loop that appends"
            " round(f * (100 - pct) / 100) for each fare.\n\n"
            "  discounted([200, 350, 100], 10) -> [180, 315, 90]\n\n"
            "Return: the new list."
        ),
        solution=("def discounted(fares, pct):\n"
                  "    out = []\n"
                  "    for f in fares:\n"
                  "        out.append(round(f * (100 - pct) / 100))\n"
                  "    return out\n"),
        trap=("def discounted(fares, pct):\n"
              "    out = []\n"
              "    for f in fares:\n"
              "        out.append(f * (100 - pct) / 100)\n"
              "    return out\n"),
        note="Division produces a float, so 200 * 90 / 100 is 180.0, and"
             " the question wants whole cents: round() brings it back to"
             " an int. 99 at 50 per cent is 49.5, which round() takes to"
             " 50 -- halves go to the even neighbour.",
    ),
    dict(
        id=9, ledger="P364", concept="PY4 for rising run", tier="2 - A simple loop",
        title="The longest run of ever-longer rides", kind="function",
        func="longest_rising",
        cases=[([5, 8, 12, 3, 4, 9, 10, 2],), ([],), ([7],), ([9, 8, 7],)],
        prompt=(
            "Write a function `longest_rising(minutes)` that returns the"
            " length of the longest stretch in which each ride is longer"
            " than the one before it, 0 for an empty list and 1 for a"
            " single ride. A for loop over range(1, len(minutes)) with a"
            " run that grows on a rise and resets to 1 otherwise, and a"
            " best so far.\n\n"
            "  longest_rising([5, 8, 12, 3, 4, 9, 10, 2]) -> 4\n\n"
            "Return: an integer."
        ),
        solution=("def longest_rising(minutes):\n"
                  "    if not minutes:\n"
                  "        return 0\n"
                  "    best = 1\n"
                  "    run = 1\n"
                  "    for i in range(1, len(minutes)):\n"
                  "        if minutes[i] > minutes[i - 1]:\n"
                  "            run += 1\n"
                  "        else:\n"
                  "            run = 1\n"
                  "        if run > best:\n"
                  "            best = run\n"
                  "    return best\n"),
        trap=("def longest_rising(minutes):\n"
              "    if not minutes:\n"
              "        return 0\n"
              "    best = 1\n"
              "    run = 1\n"
              "    for i in range(1, len(minutes)):\n"
              "        if minutes[i] > minutes[i - 1]:\n"
              "            run += 1\n"
              "        else:\n"
              "            run = 0\n"
              "        if run > best:\n"
              "            best = run\n"
              "    return best\n"),
        note="A run is measured in rides, and the ride that breaks the"
             " streak is itself the start of the next one, so the reset"
             " is to 1, not 0. Resetting to 0 counts every later run one"
             " short -- 3 for the example's 3, 4, 9, 10.",
    ),
    dict(
        id=10, ledger="P365", concept="PY4 while digits product", tier="2 - A simple loop",
        title="The digits of a bike number, multiplied", kind="function",
        func="digit_product",
        cases=[(234,), (7,), (105,), (999,)],
        prompt=(
            "Write a function `digit_product(n)` that returns the product"
            " of the decimal digits of a positive integer, using a while"
            " loop that multiplies in n % 10 and then replaces n with"
            " n // 10, running while n is above zero.\n\n"
            "  digit_product(234) -> 24\n\n"
            "Return: an integer."
        ),
        solution=("def digit_product(n):\n"
                  "    product = 1\n"
                  "    while n > 0:\n"
                  "        product *= n % 10\n"
                  "        n //= 10\n"
                  "    return product\n"),
        trap=("def digit_product(n):\n"
              "    product = 0\n"
              "    while n > 0:\n"
              "        product *= n % 10\n"
              "        n //= 10\n"
              "    return product\n"),
        note="A product starts at 1; starting at 0 keeps it at 0 forever."
             " The digit-peeling loop is the same as for a digit sum, with"
             " *= in place of +=. A 0 among the digits makes the answer 0,"
             " as it should.",
    ),
    # ========================================================== 3 Ride rows
    dict(
        id=11, ledger="P366", concept="PY5 count None", tier="3 - Ride rows",
        title="How many rides were casual", kind="function",
        func="casual_count",
        cases=[(RIDES,), ([],), (RIDES[:1],), ([{"ride_id": 9, "member": 0, "minutes": 5, "fare": 0}],)],
        prompt=(
            "Each ride is a dict with keys ride_id, member, minutes and"
            " fare, where member is None for a casual rider. Write a"
            " function `casual_count(rides)` that returns how many rides"
            " were casual: a for loop with an if on r[\"member\"] is None"
            " and a counter. A member id can be 0, and 0 is a member.\n\n"
            "  casual_count(RIDES) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def casual_count(rides):\n"
                  "    n = 0\n"
                  "    for r in rides:\n"
                  "        if r[\"member\"] is None:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def casual_count(rides):\n"
              "    n = 0\n"
              "    for r in rides:\n"
              "        if not r[\"member\"]:\n"
              "            n += 1\n"
              "    return n\n"),
        note="'is None' is the test for the missing member; 'not' is"
             " true for 0 as well, and a member whose id happened to be 0"
             " would be counted as casual. This is SQL's member_id IS"
             " NULL from the bike questions.",
    ),
    dict(
        id=12, ledger="P367", concept="PY5 sum by key", tier="3 - Ride rows",
        title="What each member paid in all", kind="function",
        func="fares_by_member",
        cases=[(RIDES,), ([],), (RIDES[1:2],)],
        prompt=(
            "Using the same ride dicts, write a function `fares_by_member("
            "rides)` that returns a dict mapping each MEMBER to the total"
            " of their fares -- casual rides, with member None, are left"
            " out. A for loop with an if on the member, and a dict built"
            " with get(member, 0) + fare.\n\n"
            "  fares_by_member(RIDES) -> {7: 200, 9: 100, 2: 0}\n\n"
            "Return: the dictionary."
        ),
        solution=("def fares_by_member(rides):\n"
                  "    totals = {}\n"
                  "    for r in rides:\n"
                  "        if r[\"member\"] is not None:\n"
                  "            totals[r[\"member\"]] = totals.get(r[\"member\"], 0) + r[\"fare\"]\n"
                  "    return totals\n"),
        trap=("def fares_by_member(rides):\n"
              "    totals = {}\n"
              "    for r in rides:\n"
              "        totals[r[\"member\"]] = totals.get(r[\"member\"], 0) + r[\"fare\"]\n"
              "    return totals\n"),
        note="A total per key is a dict with get(key, 0) to start each"
             " member at zero. Without the if, None becomes a key and the"
             " casual riders' fares are totalled under it -- a GROUP BY"
             " that forgot its WHERE. A member whose rides were all free"
             " still appears, with 0.",
    ),
    dict(
        id=13, ledger="P368", concept="PY5 argmax", tier="3 - Ride rows",
        title="The longest ride's id", kind="function",
        func="longest_ride_id",
        cases=[(RIDES,), (RIDES[:2],), (RIDES[4:5],)],
        prompt=(
            "Using the same ride dicts, write a function `longest_ride_id("
            "rides)` that returns the ride_id of the ride with the most"
            " minutes in a non-empty list, the first one if several tie."
            " A for loop with a best ride so far, starting at rides[0]."
            "\n\n"
            "  longest_ride_id(RIDES) -> 4\n\n"
            "Return: an integer."
        ),
        solution=("def longest_ride_id(rides):\n"
                  "    best = rides[0]\n"
                  "    for r in rides:\n"
                  "        if r[\"minutes\"] > best[\"minutes\"]:\n"
                  "            best = r\n"
                  "    return best[\"ride_id\"]\n"),
        trap=("def longest_ride_id(rides):\n"
              "    best = rides[0]\n"
              "    for r in rides:\n"
              "        if r[\"minutes\"] > best[\"minutes\"]:\n"
              "            best = r\n"
              "    return best[\"minutes\"]\n"),
        note="Tracking the whole best ROW keeps every field of the"
             " winner to hand, and the question asks for its id -- the"
             " trap returns its minutes, 60 rather than 4. The strict >"
             " keeps the first of equals. max(rides, key=lambda r:"
             " r['minutes']) is the one-line form.",
    ),
    dict(
        id=14, ledger="P369", concept="PY5 filter distinct sorted", tier="3 - Ride rows",
        title="The members who have ridden for free", kind="function",
        func="free_riders",
        cases=[(RIDES,), ([],), (RIDES[1:3],)],
        prompt=(
            "Using the same ride dicts, write a function `free_riders("
            "rides)` that returns a sorted list of the DISTINCT members"
            " who have at least one ride with fare 0 -- casual rides"
            " cannot be free, but guard against None anyway. A for loop"
            " adding to a set under an if, then sorted() of the set.\n\n"
            "  free_riders(RIDES) -> [2, 7]\n\n"
            "Return: the sorted list."
        ),
        solution=("def free_riders(rides):\n"
                  "    members = set()\n"
                  "    for r in rides:\n"
                  "        if r[\"fare\"] == 0 and r[\"member\"] is not None:\n"
                  "            members.add(r[\"member\"])\n"
                  "    return sorted(members)\n"),
        trap=("def free_riders(rides):\n"
              "    members = []\n"
              "    for r in rides:\n"
              "        if r[\"fare\"] == 0 and r[\"member\"] is not None:\n"
              "            members.append(r[\"member\"])\n"
              "    return members\n"),
        note="A set collects each member once, however many free rides"
             " they had, and sorted() returns it as an ordered list. A"
             " list keeps repeats and the order of arrival -- [7, 2] for"
             " the example, with a second 7 whenever member 7 rides free"
             " again. SELECT DISTINCT ... ORDER BY, in Python.",
    ),
    dict(
        id=15, ledger="P370", concept="PY5 average filtered", tier="3 - Ride rows",
        title="How long members ride, on average", kind="function",
        func="average_member_minutes",
        cases=[(RIDES,), ([],), (RIDES[1:2],), (RIDES[2:4],)],
        prompt=(
            "Using the same ride dicts, write a function"
            " `average_member_minutes(rides)` that returns the mean"
            " minutes of the rides that have a member, to one decimal,"
            " or None when there are no member rides. A for loop keeping"
            " a total and a count under an if, then the guarded"
            " division.\n\n"
            "  average_member_minutes(RIDES) -> 34.2\n\n"
            "Return: a float, or None."
        ),
        solution=("def average_member_minutes(rides):\n"
                  "    total = 0\n"
                  "    count = 0\n"
                  "    for r in rides:\n"
                  "        if r[\"member\"] is not None:\n"
                  "            total += r[\"minutes\"]\n"
                  "            count += 1\n"
                  "    if count == 0:\n"
                  "        return None\n"
                  "    return round(total / count, 1)\n"),
        trap=("def average_member_minutes(rides):\n"
              "    total = 0\n"
              "    count = 0\n"
              "    for r in rides:\n"
              "        if r[\"member\"] is not None:\n"
              "            total += r[\"minutes\"]\n"
              "        count += 1\n"
              "    if count == 0:\n"
              "        return None\n"
              "    return round(total / count, 1)\n"),
        note="Both the total and the count belong under the if: counting"
             " every ride while totalling only the members' divides by"
             " the wrong number -- 22.8 instead of 34.2. The guard"
             " before the division is what makes a list with no member"
             " rides return None rather than crash.",
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
