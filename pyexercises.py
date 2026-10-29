"""Python practice exercises: fifteen questions in three shapes and a program.

The twenty-sixth Python set: five one-tool functions on tools no earlier
set used (str.translate with maketrans, collections.deque with maxlen,
datetime.timedelta, sorted with a tuple key, str.isdigit), four functions
with one simple loop plus ONE whole program graded on what it prints, and
five over BIKE-SCHEME ROWS -- this time payments, lists of dicts with a
member or a ride that is None, an amount and a method.

Two kinds of question, told apart by `kind`:

  "program"   the editor holds a whole program, graded on what it prints:
              the lines must match the reference program's, trailing
              spaces and blank lines ignored.
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

PAYMENTS = [{"payment_id": 1, "member": 7, "ride": None, "amount": 1200, "method": "app"},
            {"payment_id": 2, "member": None, "ride": 410, "amount": 350, "method": "card"},
            {"payment_id": 3, "member": 9, "ride": None, "amount": 9900, "method": "card"},
            {"payment_id": 4, "member": None, "ride": 411, "amount": 200, "method": "app"},
            {"payment_id": 5, "member": 7, "ride": None, "amount": 1200, "method": "app"},
            {"payment_id": 6, "member": None, "ride": 412, "amount": 250, "method": "app"}]

EXERCISES = [
    # ============================================================= 1 One tool
    dict(
        id=1, ledger="P386", concept="PY3 translate", tier="1 - One tool",
        title="str.translate(): strip the punctuation", kind="function",
        func="plain_name",
        cases=[("St. Mary's-on-Hill",), ("Harbour",), ("",), ("O'Neil Rd.",)],
        prompt=(
            "Write a function `plain_name(name)` that returns the name"
            " with every '.', apostrophe and '-' removed, by"
            " name.translate(str.maketrans(\"\", \"\", \".'-\")) -- a"
            " table whose third argument lists the characters to delete."
            " No import is needed.\n\n"
            "  plain_name(\"St. Mary's-on-Hill\") -> \"St MarysonHill\"\n\n"
            "Return: the new string."
        ),
        solution="def plain_name(name):\n    return name.translate(str.maketrans(\"\", \"\", \".'-\"))\n",
        trap="def plain_name(name):\n    return name.replace(\".'-\", \"\")\n",
        note="replace() looks for the three characters as one SEQUENCE,"
             " which never occurs, so nothing changes. A translation"
             " table built with the three-argument maketrans deletes each"
             " listed character wherever it appears, in one pass. Three"
             " chained replace() calls would also do it.",
    ),
    dict(
        id=2, ledger="P387", concept="PY3 deque maxlen", tier="1 - One tool",
        title="deque(maxlen=3): only the last three", kind="function",
        func="last_three",
        cases=[([4, 8, 15, 16, 23, 42],), ([1, 2],), ([],), ([7, 7, 7, 7],)],
        prompt=(
            "Write a function `last_three(ride_ids)` that returns a list"
            " of the last three ids fed to it in order, fewer if there"
            " were fewer, using collections.deque(ride_ids, maxlen=3) --"
            " a queue that drops from the left when a fourth item"
            " arrives -- turned back into a list. Write `from collections"
            " import deque` as the first line.\n\n"
            "  last_three([4, 8, 15, 16, 23, 42]) -> [16, 23, 42]\n\n"
            "Return: the list."
        ),
        solution=("from collections import deque\n\n"
                  "def last_three(ride_ids):\n"
                  "    return list(deque(ride_ids, maxlen=3))\n"),
        trap=("from collections import deque\n\n"
              "def last_three(ride_ids):\n"
              "    return deque(ride_ids, maxlen=3)\n"),
        note="A deque with a maxlen keeps only the newest items, which is"
             " the point; but it is a deque, not a list, and the grader"
             " asks for a list -- hence list(...) around it. ride_ids[-3:]"
             " is the slice that does the same for a list already in"
             " hand; the deque shines when items arrive one at a time.",
    ),
    dict(
        id=3, ledger="P388", concept="PY3 timedelta", tier="1 - One tool",
        title="timedelta(): the next payment date", kind="function",
        func="next_due",
        cases=[("2026-01-31", 30), ("2025-12-15", 30), ("2026-02-28", 1), ("2024-02-28", 365)],
        prompt=(
            "Write a function `next_due(paid_on, days)` that returns the"
            " date days after paid_on, both as 'YYYY-MM-DD' text:"
            " date.fromisoformat() to parse, + timedelta(days=days) to"
            " move, .isoformat() to print. Write `from datetime import"
            " date, timedelta` as the first line.\n\n"
            "  next_due(\"2026-01-31\", 30) -> \"2026-03-02\"\n\n"
            "Return: the new date as text."
        ),
        solution=("from datetime import date, timedelta\n\n"
                  "def next_due(paid_on, days):\n"
                  "    return (date.fromisoformat(paid_on) + timedelta(days=days)).isoformat()\n"),
        trap=("def next_due(paid_on, days):\n"
              "    return paid_on[:8] + str(int(paid_on[8:]) + days)\n"),
        note="Adding to the day number as text gives '2026-01-61': dates"
             " are not strings, and month ends and leap years are exactly"
             " what timedelta handles for you. Parse, add, format. str()"
             " of a date is its ISO form too, so str(d) would also do in"
             " place of isoformat().",
    ),
    dict(
        id=4, ledger="P389", concept="PY3 sorted tuple key", tier="1 - One tool",
        title="sorted() with two keys: dearest first, then by id", kind="function",
        func="by_fare",
        cases=[([(3, 200), (1, 350), (2, 200)],), ([],), ([(9, 0)],), ([(5, 100), (4, 100), (6, 100)],)],
        prompt=(
            "Write a function `by_fare(rides)` that takes [ride_id, fare]"
            " pairs and returns them sorted by fare from highest to"
            " lowest, ties by ride_id from lowest up, in ONE sorted() call"
            " whose key is a tuple: key=lambda r: (-r[1], r[0]). No import"
            " is needed.\n\n"
            "  by_fare([[3, 200], [1, 350], [2, 200]]) -> [[1, 350],"
            " [2, 200], [3, 200]]\n\n"
            "Return: the sorted list."
        ),
        solution="def by_fare(rides):\n    return sorted(rides, key=lambda r: (-r[1], r[0]))\n",
        trap="def by_fare(rides):\n    return sorted(rides, key=lambda r: r[1], reverse=True)\n",
        note="A tuple key sorts by its first item and breaks ties by the"
             " second. Negating the fare puts the biggest first while the"
             " id still rises -- reverse=True would flip BOTH, and tied"
             " fares stay in the order they arrived -- [3, 200] before"
             " [2, 200] -- because Python's sort is stable and reverse=True"
             " does not reverse equal keys.",
    ),
    dict(
        id=5, ledger="P390", concept="PY3 isdigit", tier="1 - One tool",
        title="str.isdigit(): is it a bike number?", kind="function",
        func="is_bike_number",
        cases=[("0042",), ("B12",), ("",), ("7",), ("12 ",)],
        prompt=(
            "Write a function `is_bike_number(code)` that returns True"
            " when the code is made of digits only and is not empty, in"
            " one call of the string's isdigit() method. No import is"
            " needed.\n\n"
            "  is_bike_number(\"0042\") -> True\n\n"
            "Return: True or False."
        ),
        solution="def is_bike_number(code):\n    return code.isdigit()\n",
        trap="def is_bike_number(code):\n    return code.isalnum()\n",
        note="isdigit() is True only for a non-empty string of digits;"
             " isalnum() also accepts letters, so 'B12' passes. A trailing"
             " space fails both, and the empty string fails both, which is"
             " what the question wants. int(code) in a try is the other"
             " way, and accepts '-5'.",
    ),
    # ======================================================= 2 A simple loop
    dict(
        id=6, ledger="P391", concept="PY4 for vowels", tier="2 - A simple loop",
        title="How many vowels in a station name", kind="function",
        func="vowels",
        cases=[("Botanic Gardens",), ("",), ("Rhythm",), ("AEIOU aeiou",)],
        prompt=(
            "Write a function `vowels(name)` that returns how many"
            " characters of the name are vowels, either case. A for loop"
            " over the characters, an if on ch.lower() in \"aeiou\", and"
            " a counter.\n\n"
            "  vowels(\"Botanic Gardens\") -> 5\n\n"
            "Return: an integer."
        ),
        solution=("def vowels(name):\n"
                  "    n = 0\n"
                  "    for ch in name:\n"
                  "        if ch.lower() in \"aeiou\":\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def vowels(name):\n"
              "    n = 0\n"
              "    for ch in name:\n"
              "        if ch in \"aeiou\":\n"
              "            n += 1\n"
              "    return n\n"),
        note="Without the lower() a capital vowel is missed -- 'AEIOU"
             " aeiou' counts 5 instead of 10. Testing membership in a"
             " string of the vowels is shorter than five comparisons, and"
             " a for over a string visits each character.",
    ),
    dict(
        id=7, ledger="P392", concept="PY4 for interleave", tier="2 - A simple loop",
        title="Starts and ends, interleaved", kind="function",
        func="interleave",
        cases=[(["A", "B", "C"], ["X", "Y", "Z"]), ([], []), (["A"], ["B"]), ([1, 2], [3, 4])],
        prompt=(
            "Write a function `interleave(starts, ends)` that takes two"
            " lists of the SAME length and returns one list alternating"
            " start, end, start, end. A for loop over range(len(starts))"
            " appending two items per turn.\n\n"
            "  interleave([\"A\", \"B\", \"C\"], [\"X\", \"Y\", \"Z\"]) ->"
            " [\"A\", \"X\", \"B\", \"Y\", \"C\", \"Z\"]\n\n"
            "Return: the new list."
        ),
        solution=("def interleave(starts, ends):\n"
                  "    out = []\n"
                  "    for i in range(len(starts)):\n"
                  "        out.append(starts[i])\n"
                  "        out.append(ends[i])\n"
                  "    return out\n"),
        trap=("def interleave(starts, ends):\n"
              "    out = []\n"
              "    for i in range(len(starts)):\n"
              "        out.append((starts[i], ends[i]))\n"
              "    return out\n"),
        note="Two appends per turn make a flat list; appending a tuple"
             " makes a list of pairs, which is zip, not interleaving. The"
             " index loop is the plain way; for s, e in zip(starts, ends)"
             " with the same two appends is the idiomatic one.",
    ),
    dict(
        id=8, ledger="P393", concept="PY4 for running total", tier="2 - A simple loop",
        title="The balance after each payment", kind="function",
        func="running_total",
        cases=[([1200, 350, 200],), ([],), ([5],), ([10, -4, 1],)],
        prompt=(
            "Write a function `running_total(amounts)` that returns a list"
            " of the cumulative total after each amount. A for loop with"
            " a total that grows and a list that collects it after each"
            " step.\n\n"
            "  running_total([1200, 350, 200]) -> [1200, 1550, 1750]\n\n"
            "Return: the new list."
        ),
        solution=("def running_total(amounts):\n"
                  "    out = []\n"
                  "    total = 0\n"
                  "    for a in amounts:\n"
                  "        total += a\n"
                  "        out.append(total)\n"
                  "    return out\n"),
        trap=("def running_total(amounts):\n"
              "    out = []\n"
              "    total = 0\n"
              "    for a in amounts:\n"
              "        out.append(total)\n"
              "        total += a\n"
              "    return out\n"),
        note="Add first, then record: the other way round records the"
             " total BEFORE each amount, starting at 0 and missing the"
             " last. This is SUM(...) OVER (ORDER BY ...) by hand, and"
             " itertools.accumulate in one call.",
    ),
    dict(
        id=9, ledger="P394", concept="PY4 for ties at top", tier="2 - A simple loop",
        title="How many share the longest ride", kind="function",
        func="ties_at_top",
        cases=[([30, 45, 12, 45, 45],), ([7],), ([],), ([2, 2],)],
        prompt=(
            "Write a function `ties_at_top(minutes)` that returns how"
            " many entries equal the largest value, 0 for an empty list,"
            " in ONE for loop: a best that starts as None and a count"
            " that resets to 1 on a new best and grows by 1 on an"
            " equal.\n\n"
            "  ties_at_top([30, 45, 12, 45, 45]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def ties_at_top(minutes):\n"
                  "    best = None\n"
                  "    count = 0\n"
                  "    for m in minutes:\n"
                  "        if best is None or m > best:\n"
                  "            best = m\n"
                  "            count = 1\n"
                  "        elif m == best:\n"
                  "            count += 1\n"
                  "    return count\n"),
        trap=("def ties_at_top(minutes):\n"
              "    best = None\n"
              "    count = 0\n"
              "    for m in minutes:\n"
              "        if best is None or m >= best:\n"
              "            best = m\n"
              "            count += 1\n"
              "    return count\n"),
        note="A new best must RESET the count to 1, since the earlier"
             " entries were ties with a smaller value; with >= and a bare"
             " += the count keeps the 30 that was best for a moment and"
             " says 4. minutes.count(max(minutes)) is the two-pass"
             " version.",
    ),
    dict(
        id=10, ledger="P395", concept="PY4 program bar chart", tier="2 - A simple loop",
        title="A bar chart of the week", kind="program",
        prompt=(
            "Write a program that prints one line per day for this"
            " dictionary of rides per weekday, in this order:\n\n"
            "  rides = {\"Mon\": 5647, \"Tue\": 5595, \"Wed\": 5452,"
            " \"Thu\": 5391, \"Fri\": 5559, \"Sat\": 5433, \"Sun\": 5528}\n\n"
            "Each line is the day, a space, and one '#' for every full 500"
            " rides -- rides // 500 of them -- so Monday has eleven."
            " A for loop over rides.items().\n\n"
            "Print: seven lines like\n\n"
            "  Mon ###########"
        ),
        solution=("rides = {\"Mon\": 5647, \"Tue\": 5595, \"Wed\": 5452, \"Thu\": 5391,"
                  " \"Fri\": 5559, \"Sat\": 5433, \"Sun\": 5528}\n"
                  "for day, n in rides.items():\n"
                  "    print(day, \"#\" * (n // 500))\n"),
        trap=("rides = {\"Mon\": 5647, \"Tue\": 5595, \"Wed\": 5452, \"Thu\": 5391,"
              " \"Fri\": 5559, \"Sat\": 5433, \"Sun\": 5528}\n"
              "for day, n in rides.items():\n"
              "    print(day, \"#\" * round(n / 500))\n"),
        note="'One for every FULL 500' is a floor, which // gives;"
             " round() takes Wednesday's 10.9, Thursday's 10.8 and"
             " Saturday's 10.9 UP to eleven bars, one too many each. A"
             " string times an integer repeats it, and print with two"
             " arguments puts the space in.",
    ),
    # ======================================================== 3 Payment rows
    dict(
        id=11, ledger="P396", concept="PY5 sum by key", tier="3 - Payment rows",
        title="What came in by card and by app", kind="function",
        func="total_by_method",
        cases=[(PAYMENTS,), ([],), (PAYMENTS[:2],)],
        prompt=(
            "Each payment is a dict with keys payment_id, member (None"
            " for a casual rider's fare), ride (None for a subscription),"
            " amount and method. Write a function `total_by_method("
            "payments)` that returns a dict mapping each method to the"
            " total amount. A for loop and get(method, 0) + amount.\n\n"
            "  total_by_method(PAYMENTS) -> {\"app\": 2850, \"card\":"
            " 10250}\n\n"
            "Return: the dictionary."
        ),
        solution=("def total_by_method(payments):\n"
                  "    totals = {}\n"
                  "    for p in payments:\n"
                  "        totals[p[\"method\"]] = totals.get(p[\"method\"], 0) + p[\"amount\"]\n"
                  "    return totals\n"),
        trap=("def total_by_method(payments):\n"
              "    totals = {}\n"
              "    for p in payments:\n"
              "        totals[p[\"method\"]] = totals.get(p[\"method\"], 0) + 1\n"
              "    return totals\n"),
        note="+ 1 counts the payments; + amount totals them. The shape is"
             " the same as every GROUP BY SUM in this track: a dict keyed"
             " by the group, get(key, 0) to start each one at zero.",
    ),
    dict(
        id=12, ledger="P397", concept="PY5 count None", tier="3 - Payment rows",
        title="How many were subscriptions", kind="function",
        func="subscription_count",
        cases=[(PAYMENTS,), ([],), (PAYMENTS[1:2],), ([{"payment_id": 9, "member": 3, "ride": 0, "amount": 100, "method": "app"}],)],
        prompt=(
            "Using the same payment dicts, write a function"
            " `subscription_count(payments)` that returns how many"
            " payments are subscriptions -- their ride is None. A for"
            " loop with an if on p[\"ride\"] is None and a counter. A ride"
            " id of 0 is a ride.\n\n"
            "  subscription_count(PAYMENTS) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def subscription_count(payments):\n"
                  "    n = 0\n"
                  "    for p in payments:\n"
                  "        if p[\"ride\"] is None:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def subscription_count(payments):\n"
              "    n = 0\n"
              "    for p in payments:\n"
              "        if not p[\"ride\"]:\n"
              "            n += 1\n"
              "    return n\n"),
        note="'is None' asks whether the ride is missing; 'not' is also"
             " true for 0, so a ride numbered 0 would be counted as a"
             " subscription. The schema's rule is that a payment names a"
             " ride or a member, never both: ride IS NULL is the"
             " subscription test there too.",
    ),
    dict(
        id=13, ledger="P398", concept="PY5 argmax", tier="3 - Payment rows",
        title="The biggest payment", kind="function",
        func="biggest_payment_id",
        cases=[(PAYMENTS,), (PAYMENTS[:2],), (PAYMENTS[3:4],), (PAYMENTS[::4],)],
        prompt=(
            "Using the same payment dicts, write a function"
            " `biggest_payment_id(payments)` that returns the payment_id"
            " of the largest amount in a non-empty list, the FIRST if"
            " several tie. A for loop with a best row so far, starting at"
            " payments[0], replaced only on a strictly bigger amount.\n\n"
            "  biggest_payment_id(PAYMENTS) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def biggest_payment_id(payments):\n"
                  "    best = payments[0]\n"
                  "    for p in payments:\n"
                  "        if p[\"amount\"] > best[\"amount\"]:\n"
                  "            best = p\n"
                  "    return best[\"payment_id\"]\n"),
        trap=("def biggest_payment_id(payments):\n"
              "    best = payments[0]\n"
              "    for p in payments:\n"
              "        if p[\"amount\"] >= best[\"amount\"]:\n"
              "            best = p\n"
              "    return best[\"payment_id\"]\n"),
        note="> keeps the first of equals, >= takes the last: payments 1"
             " and 5 are both 1200, and on a list of just those two the"
             " trap answers 5. ORDER BY amount DESC, payment_id LIMIT 1"
             " says the same in SQL.",
    ),
    dict(
        id=14, ledger="P399", concept="PY5 distinct sorted", tier="3 - Payment rows",
        title="The members who have been billed", kind="function",
        func="members_billed",
        cases=[(PAYMENTS,), ([],), (PAYMENTS[1:2],)],
        prompt=(
            "Using the same payment dicts, write a function"
            " `members_billed(payments)` that returns a sorted list of"
            " the DISTINCT members who appear on a payment, leaving out"
            " the None of the casual fares. A for loop adding to a set"
            " under an if, then sorted().\n\n"
            "  members_billed(PAYMENTS) -> [7, 9]\n\n"
            "Return: the sorted list."
        ),
        solution=("def members_billed(payments):\n"
                  "    members = set()\n"
                  "    for p in payments:\n"
                  "        if p[\"member\"] is not None:\n"
                  "            members.add(p[\"member\"])\n"
                  "    return sorted(members)\n"),
        trap=("def members_billed(payments):\n"
              "    members = set()\n"
              "    for p in payments:\n"
              "        members.add(p[\"member\"])\n"
              "    return sorted(members)\n"),
        note="Without the if, None goes into the set and sorted() then"
             " raises a TypeError, because None and an integer cannot be"
             " ordered -- the crash, not a wrong list, is what the trap"
             " produces. Filter the NULLs before sorting, as SQL's ORDER"
             " BY would quietly have put them first.",
    ),
    dict(
        id=15, ledger="P400", concept="PY5 share", tier="3 - Payment rows",
        title="What share of payments came by app", kind="function",
        func="app_share",
        cases=[(PAYMENTS,), ([],), (PAYMENTS[1:2],), (PAYMENTS[:3],)],
        prompt=(
            "Using the same payment dicts, write a function `app_share("
            "payments)` that returns the percentage of payments whose"
            " method is 'app', to one decimal, or None for an empty list."
            " A loop counting the app payments, then 100 * app /"
            " len(payments) rounded, behind a guard.\n\n"
            "  app_share(PAYMENTS) -> 66.7\n\n"
            "Return: a float, or None."
        ),
        solution=("def app_share(payments):\n"
                  "    if not payments:\n"
                  "        return None\n"
                  "    app = 0\n"
                  "    for p in payments:\n"
                  "        if p[\"method\"] == \"app\":\n"
                  "            app += 1\n"
                  "    return round(100 * app / len(payments), 1)\n"),
        trap=("def app_share(payments):\n"
              "    app = 0\n"
              "    for p in payments:\n"
              "        if p[\"method\"] == \"app\":\n"
              "            app += 1\n"
              "    return round(100 * app / len(payments), 1)\n"),
        note="The guard is the whole difference: on an empty list"
             " len(payments) is 0 and the division raises"
             " ZeroDivisionError. Check for the empty case before any"
             " arithmetic that depends on the size.",
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
