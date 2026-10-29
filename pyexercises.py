"""Python practice exercises: fifteen functions in three shapes.

The twenty-fifth Python set, mixed like the last: five one-tool functions
on tools no earlier set used (divmod, collections.defaultdict,
date.fromisoformat with weekday, itertools.product, itertools.zip_longest),
five functions with one simple loop, and five over BIKE-SCHEME ROWS -- this
time maintenance jobs, lists of dicts with a kind, a cost and a fixed flag:
cost per kind, the open jobs, the bikes back more than once, the dearest
kind, the share fixed.

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

JOBS = [{"job_id": 1, "bike_id": 12, "kind": "puncture", "cost": 800, "fixed": True},
        {"job_id": 2, "bike_id": 7, "kind": "brakes", "cost": 2600, "fixed": True},
        {"job_id": 3, "bike_id": 12, "kind": "chain", "cost": 1900, "fixed": False},
        {"job_id": 4, "bike_id": 30, "kind": "puncture", "cost": 1100, "fixed": True},
        {"job_id": 5, "bike_id": 7, "kind": "battery", "cost": 9800, "fixed": False},
        {"job_id": 6, "bike_id": 45, "kind": "puncture", "cost": 950, "fixed": True}]

EXERCISES = [
    # ============================================================= 1 One tool
    dict(
        id=1, ledger="P371", concept="PY3 divmod", tier="1 - One tool",
        title="divmod(): minutes into hours and minutes", kind="function",
        func="hours_minutes",
        cases=[(135,), (60,), (0,), (59,)],
        prompt=(
            "Write a function `hours_minutes(minutes)` that returns a"
            " tuple (hours, minutes) for a ride length in minutes, in one"
            " call of divmod(minutes, 60), which gives the quotient and"
            " the remainder together. No import is needed.\n\n"
            "  hours_minutes(135) -> (2, 15)\n\n"
            "Return: the tuple."
        ),
        solution="def hours_minutes(minutes):\n    return divmod(minutes, 60)\n",
        trap="def hours_minutes(minutes):\n    return (minutes / 60, minutes % 60)\n",
        note="divmod does the // and the % in one step and returns the"
             " pair as a tuple. A plain / gives 2.25 hours, not 2 -- the"
             " trap's hours are a float with the minutes counted twice."
             " It is the same pattern as julianday times 1440 then"
             " integer arithmetic on the SQL side.",
    ),
    dict(
        id=2, ledger="P372", concept="PY3 defaultdict", tier="1 - One tool",
        title="defaultdict(list): rides grouped by station", kind="function",
        func="rides_by_station",
        cases=[([("Harbour", 1), ("Stadium", 2), ("Harbour", 3)],), ([],), ([("Hilltop", 9)],)],
        prompt=(
            "Write a function `rides_by_station(pairs)` that takes"
            " (station, ride_id) tuples and returns a dict mapping each"
            " station to the list of its ride_ids in order, using"
            " collections.defaultdict(list) so that the first append to"
            " a new station needs no check; return dict(groups) at the"
            " end. Write `from collections import defaultdict` as the"
            " first line.\n\n"
            "  rides_by_station([(\"Harbour\", 1), (\"Stadium\", 2),"
            " (\"Harbour\", 3)]) -> {\"Harbour\": [1, 3], \"Stadium\": [2]}\n\n"
            "Return: the dictionary."
        ),
        solution=("from collections import defaultdict\n\n"
                  "def rides_by_station(pairs):\n"
                  "    groups = defaultdict(list)\n"
                  "    for station, ride_id in pairs:\n"
                  "        groups[station].append(ride_id)\n"
                  "    return dict(groups)\n"),
        trap=("from collections import defaultdict\n\n"
              "def rides_by_station(pairs):\n"
              "    groups = defaultdict(list)\n"
              "    for station, ride_id in pairs:\n"
              "        groups[station] = [ride_id]\n"
              "    return dict(groups)\n"),
        note="A defaultdict(list) makes an empty list the moment a new key"
             " is touched, so groups[station].append(...) works on the"
             " first visit. Assigning a fresh [ride_id] each time throws"
             " away the earlier rides -- Harbour keeps only 3. The"
             " dict(...) at the end hands back an ordinary dictionary.",
    ),
    dict(
        id=3, ledger="P373", concept="PY3 date weekday", tier="1 - One tool",
        title="date.fromisoformat(): is it a weekend?", kind="function",
        func="is_weekend",
        cases=[("2026-06-27",), ("2026-06-29",), ("2026-06-28",), ("2025-01-01",)],
        prompt=(
            "Write a function `is_weekend(day)` that takes a date as"
            " 'YYYY-MM-DD' text and returns True when it is a Saturday or"
            " Sunday. date.fromisoformat(day) parses the text and"
            " .weekday() numbers Monday 0 to Sunday 6, so the test is >="
            " 5. Write `from datetime import date` as the first"
            " line.\n\n"
            "  is_weekend(\"2026-06-27\") -> True\n\n"
            "Return: True or False."
        ),
        solution=("from datetime import date\n\n"
                  "def is_weekend(day):\n"
                  "    return date.fromisoformat(day).weekday() >= 5\n"),
        trap=("from datetime import date\n\n"
              "def is_weekend(day):\n"
              "    return date.fromisoformat(day).weekday() in (0, 6)\n"),
        note="Python's weekday() starts the week on Monday as 0, so"
             " Saturday is 5 and Sunday 6; SQLite's strftime('%w') starts"
             " on Sunday as 0. The trap uses SQLite's numbering and calls"
             " Monday a weekend day. isoweekday() runs 1 to 7 if you"
             " prefer Sunday as 7.",
    ),
    dict(
        id=4, ledger="P374", concept="PY3 product", tier="1 - One tool",
        title="itertools.product(): every route", kind="function",
        func="routes",
        cases=[(["Harbour", "Stadium"], ["Hilltop", "Stadium"]), ([], ["A"]), (["A"], ["A"])],
        prompt=(
            "Write a function `routes(starts, ends)` that returns a list"
            " of every (start, end) pair, one from each list, in order,"
            " INCLUDING a start paired with the same station as end,"
            " using list() over itertools.product(starts, ends). Write"
            " `import itertools` as the first line.\n\n"
            "  routes([\"Harbour\", \"Stadium\"], [\"Hilltop\","
            " \"Stadium\"]) -> [(\"Harbour\", \"Hilltop\"),"
            " (\"Harbour\", \"Stadium\"), (\"Stadium\", \"Hilltop\"),"
            " (\"Stadium\", \"Stadium\")]\n\n"
            "Return: the list of tuples."
        ),
        solution=("import itertools\n\n"
                  "def routes(starts, ends):\n"
                  "    return list(itertools.product(starts, ends))\n"),
        trap=("import itertools\n\n"
              "def routes(starts, ends):\n"
              "    return list(zip(starts, ends))\n"),
        note="product pairs every start with every end -- the CROSS JOIN"
             " -- while zip pairs them up position by position and stops"
             " at the shorter list: two pairs instead of four. Last set's"
             " combinations picked pairs from ONE list without repeats;"
             " product takes one from each.",
    ),
    dict(
        id=5, ledger="P375", concept="PY3 zip_longest", tier="1 - One tool",
        title="zip_longest(): two columns of unequal length", kind="function",
        func="side_by_side",
        cases=[([1, 2, 3], [10, 20]), ([], [5]), ([7], [8]), ([1], [2, 3, 4])],
        prompt=(
            "Write a function `side_by_side(a, b)` that pairs the items"
            " of two lists position by position as tuples, padding the"
            " SHORTER list with 0 so nothing is dropped: list() over"
            " itertools.zip_longest(a, b, fillvalue=0). Write `import"
            " itertools` as the first line.\n\n"
            "  side_by_side([1, 2, 3], [10, 20]) -> [(1, 10), (2, 20),"
            " (3, 0)]\n\n"
            "Return: the list of tuples."
        ),
        solution=("import itertools\n\n"
                  "def side_by_side(a, b):\n"
                  "    return list(itertools.zip_longest(a, b, fillvalue=0))\n"),
        trap=("import itertools\n\n"
              "def side_by_side(a, b):\n"
              "    return list(itertools.zip_longest(a, b))\n"),
        note="zip stops at the shorter list; zip_longest carries on and"
             " fills the gaps -- with None unless fillvalue says"
             " otherwise, so the trap returns (3, None) where (3, 0) was"
             " asked for. It is the FULL OUTER JOIN of the pairing tools.",
    ),
    # ======================================================= 2 A simple loop
    dict(
        id=6, ledger="P376", concept="PY4 for running max", tier="2 - A simple loop",
        title="The record so far", kind="function",
        func="records",
        cases=[([12, 9, 15, 15, 30, 4],), ([],), ([5],), ([3, 2, 1],)],
        prompt=(
            "Write a function `records(distances)` that returns a list"
            " the same length as the input, where each position holds the"
            " longest distance seen SO FAR, that one included. A for loop"
            " with a best that starts as None and a list built up.\n\n"
            "  records([12, 9, 15, 15, 30, 4]) -> [12, 12, 15, 15, 30,"
            " 30]\n\n"
            "Return: the new list."
        ),
        solution=("def records(distances):\n"
                  "    out = []\n"
                  "    best = None\n"
                  "    for d in distances:\n"
                  "        if best is None or d > best:\n"
                  "            best = d\n"
                  "        out.append(best)\n"
                  "    return out\n"),
        trap=("def records(distances):\n"
              "    out = []\n"
              "    best = None\n"
              "    for d in distances:\n"
              "        if best is None or d > best:\n"
              "            best = d\n"
              "            out.append(best)\n"
              "    return out\n"),
        note="The append belongs outside the if: every distance gets an"
             " entry, a new record or the old one repeated. Indented"
             " under the if, only the records themselves are kept and the"
             " list comes back shorter -- three items for six. This is"
             " MAX(...) OVER (ORDER BY ...) as a loop.",
    ),
    dict(
        id=7, ledger="P377", concept="PY4 for adjacent dedupe", tier="2 - A simple loop",
        title="Collapse the repeated stops", kind="function",
        func="collapse",
        cases=[(["A", "A", "B", "B", "B", "A"],), ([],), (["X"],), (["A", "B", "A"],)],
        prompt=(
            "Write a function `collapse(stops)` that returns the stops"
            " with each run of CONSECUTIVE repeats reduced to one -- a"
            " station that comes back later stays. A for loop that"
            " appends a stop only when it differs from the last item"
            " appended, with the empty list handled.\n\n"
            "  collapse([\"A\", \"A\", \"B\", \"B\", \"B\", \"A\"]) ->"
            " [\"A\", \"B\", \"A\"]\n\n"
            "Return: the new list."
        ),
        solution=("def collapse(stops):\n"
                  "    out = []\n"
                  "    for s in stops:\n"
                  "        if not out or s != out[-1]:\n"
                  "            out.append(s)\n"
                  "    return out\n"),
        trap=("def collapse(stops):\n"
              "    out = []\n"
              "    for s in stops:\n"
              "        if s not in out:\n"
              "            out.append(s)\n"
              "    return out\n"),
        note="'s not in out' removes every repeat anywhere, so the A that"
             " comes back at the end is lost -- that is DISTINCT, not a"
             " collapse of runs. Comparing with out[-1], the last item"
             " kept, is the test for 'same as the one before', and 'not"
             " out' guards the first stop.",
    ),
    dict(
        id=8, ledger="P378", concept="PY4 for count changes", tier="2 - A simple loop",
        title="How many times the bike changed station", kind="function",
        func="station_changes",
        cases=[([3, 3, 5, 5, 5, 2, 3],), ([],), ([7],), ([1, 1, 1],), ([1, 2],), ([2, 2, 9],)],
        prompt=(
            "Write a function `station_changes(stations)` that returns"
            " how many times consecutive entries differ -- the number of"
            " moves between stations. A for loop over range(1,"
            " len(stations)) comparing each entry with the one before,"
            " and a counter.\n\n"
            "  station_changes([3, 3, 5, 5, 5, 2, 3]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def station_changes(stations):\n"
                  "    n = 0\n"
                  "    for i in range(1, len(stations)):\n"
                  "        if stations[i] != stations[i - 1]:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def station_changes(stations):\n"
              "    n = 0\n"
              "    for i in range(len(stations)):\n"
              "        if stations[i] != stations[i - 1]:\n"
              "            n += 1\n"
              "    return n\n"),
        note="Starting the range at 0 compares the first entry with"
             " stations[-1], the LAST one -- Python's negative index"
             " wraps round rather than failing -- and counts a phantom"
             " change whenever the list ends somewhere else. Start at 1"
             " so every comparison has a real predecessor.",
    ),
    dict(
        id=9, ledger="P379", concept="PY4 for second largest", tier="2 - A simple loop",
        title="The second-longest ride", kind="function",
        func="second_longest",
        cases=[([12, 45, 8, 30],), ([45, 45, 10],), ([7],), ([],), ([5, 5],)],
        prompt=(
            "Write a function `second_longest(minutes)` that returns the"
            " second-largest DISTINCT value, or None when there are fewer"
            " than two distinct values. One for loop keeping a first and"
            " a second, both starting as None, with an elif for a value"
            " between them that is not equal to the first.\n\n"
            "  second_longest([12, 45, 8, 30]) -> 30\n\n"
            "Return: an integer, or None."
        ),
        solution=("def second_longest(minutes):\n"
                  "    first = None\n"
                  "    second = None\n"
                  "    for m in minutes:\n"
                  "        if first is None or m > first:\n"
                  "            second = first\n"
                  "            first = m\n"
                  "        elif m != first and (second is None or m > second):\n"
                  "            second = m\n"
                  "    return second\n"),
        trap=("def second_longest(minutes):\n"
              "    first = None\n"
              "    second = None\n"
              "    for m in minutes:\n"
              "        if first is None or m > first:\n"
              "            second = first\n"
              "            first = m\n"
              "        elif second is None or m > second:\n"
              "            second = m\n"
              "    return second\n"),
        note="Without the m != first test a repeat of the maximum is"
             " taken as the runner-up, so [45, 45, 10] gives 45 instead"
             " of 10. The order of the two assignments on a new record"
             " matters too: the old first becomes second BEFORE first is"
             " replaced. sorted(set(minutes))[-2] is the short form, with"
             " a length check.",
    ),
    dict(
        id=10, ledger="P380", concept="PY4 while halving", tier="2 - A simple loop",
        title="How many charges until the battery is below the limit", kind="function",
        func="halvings",
        cases=[(100, 20), (100, 100), (5, 10), (64, 1)],
        prompt=(
            "A battery's range halves with every cycle of a test. Write"
            " a function `halvings(start, limit)` that returns how many"
            " halvings it takes for start to drop BELOW limit -- 0 when"
            " it already is. A while loop that runs while the value is"
            " >= limit, halving with //= 2 and counting.\n\n"
            "  halvings(100, 20) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def halvings(start, limit):\n"
                  "    n = 0\n"
                  "    while start >= limit:\n"
                  "        start //= 2\n"
                  "        n += 1\n"
                  "    return n\n"),
        trap=("def halvings(start, limit):\n"
              "    n = 0\n"
              "    while start > limit:\n"
              "        start //= 2\n"
              "        n += 1\n"
              "    return n\n"),
        note="'Below the limit' means strictly less, so the loop must keep"
             " going while the value is still >= limit; with > it stops"
             " one halving early when the value lands exactly on the"
             " limit -- halvings(100, 100) is 1, not 0. 100 -> 50 -> 25"
             " -> 12 is three halvings to get under 20.",
    ),
    # =========================================================== 3 Job rows
    dict(
        id=11, ledger="P381", concept="PY5 sum by key", tier="3 - Job rows",
        title="What each kind of repair has cost", kind="function",
        func="cost_by_kind",
        cases=[(JOBS,), ([],), (JOBS[:2],)],
        prompt=(
            "Each job is a dict with keys job_id, bike_id, kind, cost and"
            " fixed (True or False). Write a function `cost_by_kind(jobs)`"
            " that returns a dict mapping each kind to the total cost of"
            " its jobs, fixed or not. A for loop and get(kind, 0) +"
            " cost.\n\n"
            "  cost_by_kind(JOBS) -> {\"puncture\": 2850, \"brakes\": 2600,"
            " \"chain\": 1900, \"battery\": 9800}\n\n"
            "Return: the dictionary."
        ),
        solution=("def cost_by_kind(jobs):\n"
                  "    totals = {}\n"
                  "    for j in jobs:\n"
                  "        totals[j[\"kind\"]] = totals.get(j[\"kind\"], 0) + j[\"cost\"]\n"
                  "    return totals\n"),
        trap=("def cost_by_kind(jobs):\n"
              "    totals = {}\n"
              "    for j in jobs:\n"
              "        totals[j[\"kind\"]] = j[\"cost\"]\n"
              "    return totals\n"),
        note="get(kind, 0) reads the running total, 0 for a kind not yet"
             " seen, and the cost is added to it; a plain assignment"
             " keeps only the LAST job of each kind, so puncture shows"
             " 950 rather than 2850. SUM(cost) GROUP BY kind, by hand.",
    ),
    dict(
        id=12, ledger="P382", concept="PY5 filter False sorted", tier="3 - Job rows",
        title="The jobs still open", kind="function",
        func="open_jobs",
        cases=[(JOBS,), ([],), (JOBS[:2],)],
        prompt=(
            "Using the same job dicts, write a function `open_jobs(jobs)`"
            " that returns the job_ids of the jobs NOT yet fixed, in"
            " ascending order. A for loop with an if on not j[\"fixed\"],"
            " then sorted().\n\n"
            "  open_jobs(JOBS) -> [3, 5]\n\n"
            "Return: the sorted list."
        ),
        solution=("def open_jobs(jobs):\n"
                  "    ids = []\n"
                  "    for j in jobs:\n"
                  "        if not j[\"fixed\"]:\n"
                  "            ids.append(j[\"job_id\"])\n"
                  "    return sorted(ids)\n"),
        trap=("def open_jobs(jobs):\n"
              "    ids = []\n"
              "    for j in jobs:\n"
              "        if j[\"fixed\"]:\n"
              "            ids.append(j[\"job_id\"])\n"
              "    return sorted(ids)\n"),
        note="'Still open' is the FALSE side of the flag, so the test is"
             " 'not fixed'; testing 'fixed' lists the four finished jobs"
             " instead. This is fixed_at IS NULL in the schema, where the"
             " flag is a missing timestamp rather than a boolean.",
    ),
    dict(
        id=13, ledger="P383", concept="PY5 count by key filter", tier="3 - Job rows",
        title="Bikes that have been in more than once", kind="function",
        func="repeat_bikes",
        cases=[(JOBS,), ([],), (JOBS[:1],)],
        prompt=(
            "Using the same job dicts, write a function `repeat_bikes("
            "jobs)` that returns a sorted list of the bike_ids with MORE"
            " THAN ONE job. One loop counting jobs per bike in a dict,"
            " then a list of the keys whose count is above 1, sorted."
            "\n\n"
            "  repeat_bikes(JOBS) -> [7, 12]\n\n"
            "Return: the sorted list."
        ),
        solution=("def repeat_bikes(jobs):\n"
                  "    counts = {}\n"
                  "    for j in jobs:\n"
                  "        counts[j[\"bike_id\"]] = counts.get(j[\"bike_id\"], 0) + 1\n"
                  "    return sorted(b for b in counts if counts[b] > 1)\n"),
        trap=("def repeat_bikes(jobs):\n"
              "    counts = {}\n"
              "    for j in jobs:\n"
              "        counts[j[\"bike_id\"]] = counts.get(j[\"bike_id\"], 0) + 1\n"
              "    return sorted(b for b in counts if counts[b] >= 1)\n"),
        note="'More than one' is > 1; >= 1 is every bike that has ever"
             " had a job. Count first, filter second -- the HAVING"
             " COUNT(*) > 1 of the SQL side, which also cannot be decided"
             " until the counting is done.",
    ),
    dict(
        id=14, ledger="P384", concept="PY5 argmax dict", tier="3 - Job rows",
        title="The dearest kind of repair", kind="function",
        func="priciest_kind",
        cases=[(JOBS,), (JOBS[:1],), ([JOBS[0], JOBS[3], JOBS[5], JOBS[2]],)],
        prompt=(
            "Using the same job dicts, write a function `priciest_kind("
            "jobs)` that returns the kind with the highest TOTAL cost in"
            " a non-empty list -- the first kind met if several tie. Total"
            " per kind in a dict with one loop, then a second loop over"
            " the dict keeping the best kind so far.\n\n"
            "  priciest_kind(JOBS) -> \"battery\"\n\n"
            "Return: the kind."
        ),
        solution=("def priciest_kind(jobs):\n"
                  "    totals = {}\n"
                  "    for j in jobs:\n"
                  "        totals[j[\"kind\"]] = totals.get(j[\"kind\"], 0) + j[\"cost\"]\n"
                  "    best = None\n"
                  "    for kind in totals:\n"
                  "        if best is None or totals[kind] > totals[best]:\n"
                  "            best = kind\n"
                  "    return best\n"),
        trap=("def priciest_kind(jobs):\n"
              "    best = None\n"
              "    for j in jobs:\n"
              "        if best is None or j[\"cost\"] > best[\"cost\"]:\n"
              "            best = j\n"
              "    return best[\"kind\"]\n"),
        note="The question is about TOTALS per kind, so the jobs have to"
             " be grouped before anything is compared; the trap finds the"
             " single most expensive job, which happens to agree on the"
             " full list and disagrees on three punctures and a chain,"
             " where the punctures together outcost the chain. max(totals,"
             " key=totals.get) is the one-line second loop.",
    ),
    dict(
        id=15, ledger="P385", concept="PY5 share", tier="3 - Job rows",
        title="What share of jobs are fixed", kind="function",
        func="fixed_share",
        cases=[(JOBS,), ([],), (JOBS[2:3],), (JOBS[:2],)],
        prompt=(
            "Using the same job dicts, write a function `fixed_share("
            "jobs)` that returns the percentage of jobs that are fixed,"
            " to one decimal, or None for an empty list. A loop counting"
            " the fixed ones, then 100 * fixed / len(jobs) rounded, behind"
            " a guard.\n\n"
            "  fixed_share(JOBS) -> 66.7\n\n"
            "Return: a float, or None."
        ),
        solution=("def fixed_share(jobs):\n"
                  "    if not jobs:\n"
                  "        return None\n"
                  "    fixed = 0\n"
                  "    for j in jobs:\n"
                  "        if j[\"fixed\"]:\n"
                  "            fixed += 1\n"
                  "    return round(100 * fixed / len(jobs), 1)\n"),
        trap=("def fixed_share(jobs):\n"
              "    if not jobs:\n"
              "        return None\n"
              "    fixed = 0\n"
              "    for j in jobs:\n"
              "        if j[\"fixed\"]:\n"
              "            fixed += 1\n"
              "    return round(100 * fixed // len(jobs), 1)\n"),
        note="// is integer division: 400 // 6 is 66, and round() cannot"
             " bring back the .7 that was already thrown away. A"
             " percentage wants the real division, rounded afterwards."
             " The guard comes first because len(jobs) of an empty list"
             " would divide by zero.",
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
