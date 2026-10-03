"""Python practice exercises: fifteen functions over hospital-shaped data.

The seventh Python set. Every question hands a function the kind of rows
the database holds -- admissions as dictionaries with a ward, a patient
and a length of stay, ward stays as (admission, sequence, ward) tuples,
patients as an id-to-name dictionary -- and asks for the sort of answer the
SQL tab asks for: a count per ward, the open admissions, a total, the
longest, an average, patients over a threshold, the route through the
wards, a grouping, the busiest ward, readmissions within a window, a
filter, a join, a top-N, an occupancy, and a validation. The functions are
three to eight lines, with loops and ifs, graded on what they return.

The rows arrive as plain Python values, not from the database: a list of
dicts is what a query result looks like once fetched, and these are the
operations a program does with one. The two tabs ask the same questions
in two languages.

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

ADM = [{"id": 1, "patient": 7, "ward": "Fleming", "days": 3.5, "priority": "urgent"},
          {"id": 2, "patient": 9, "ward": "Barry", "days": None, "priority": "routine"},
          {"id": 3, "patient": 7, "ward": "Fleming", "days": 1.0, "priority": "immediate"},
          {"id": 4, "patient": 2, "ward": "Jenner", "days": 8.25, "priority": "routine"},
          {"id": 5, "patient": 9, "ward": "Barry", "days": 2.0, "priority": "urgent"}]

EXERCISES = [
    # ========================================================= 1 One list
    dict(
        id=1, ledger="P101", concept="PY5 count by key", tier="1 - One list of rows",
        title="Admissions per ward", kind="function",
        func="count_by_ward",
        cases=[(ADM,), ([],), ([ADM[0]],)],
        prompt=(
            "Each admission is a dict with keys id, patient, ward, days"
            " and priority; days is None while the patient is still in."
            " Write `count_by_ward(admissions)` returning a dict from ward"
            " name to how many admissions it has -- GROUP BY ward,"
            " COUNT(*):\n\n"
            "  count_by_ward(ADM) -> {'Fleming': 2, 'Barry': 2, 'Jenner': 1}\n\n"
            "Return: the dict; an empty list gives an empty dict."
        ),
        solution=('def count_by_ward(admissions):\n'
                  '    counts = {}\n'
                  '    for a in admissions:\n'
                  '        counts[a["ward"]] = counts.get(a["ward"], 0) + 1\n'
                  '    return counts\n'),
        trap=('def count_by_ward(admissions):\n'
              '    counts = {}\n'
              '    for a in admissions:\n'
              '        counts[a["ward"]] = 1\n'
              '    return counts\n'),
        note="A dict keyed on the grouping column with get(key, 0) + 1 is"
             " the Python shape of GROUP BY ... COUNT(*). Assigning 1 each"
             " time records that the ward exists and forgets how often."
             " a[\"ward\"] reads one field of one row, the way a.ward_id"
             " does in SQL.",
    ),
    dict(
        id=2, ledger="P102", concept="PY5 filter None", tier="1 - One list of rows",
        title="Still in: the open admissions", kind="function",
        func="open_admissions",
        cases=[(ADM,), ([],), ([ADM[0]],)],
        prompt=(
            "Write `open_admissions(admissions)` returning a list of the"
            " ids of admissions whose days is None -- the patient has not"
            " been discharged -- in the order given. WHERE discharged_at"
            " IS NULL:\n\n"
            "  open_admissions(ADM) -> [2]\n\n"
            "Return: a list of ids."
        ),
        solution=('def open_admissions(admissions):\n'
                  '    return [a["id"] for a in admissions if a["days"] is None]\n'),
        trap=('def open_admissions(admissions):\n'
              '    return [a["id"] for a in admissions if a["days"] == 0]\n'),
        note="None is Python's NULL and is tested with `is None`, not with"
             " == 0: a stay of zero days would be a real value, and None"
             " == 0 is False anyway. The comprehension filters and"
             " projects in one line, the same two jobs as WHERE and the"
             " SELECT list.",
    ),
    dict(
        id=3, ledger="P103", concept="PY5 sum with filter", tier="1 - One list of rows",
        title="Total days on one ward", kind="function",
        func="total_days",
        cases=[(ADM, "Fleming"), (ADM, "Barry"), (ADM, "Lister")],
        prompt=(
            "Write `total_days(admissions, ward)` returning the sum of"
            " days for completed admissions to that ward, skipping the"
            " open ones (days None). SUM(days) WHERE ward = ? AND days IS"
            " NOT NULL:\n\n"
            "  total_days(ADM, 'Fleming') -> 4.5\n\n"
            "Return: the total; 0 for a ward with none."
        ),
        solution=('def total_days(admissions, ward):\n'
                  '    total = 0\n'
                  '    for a in admissions:\n'
                  '        if a["ward"] == ward and a["days"] is not None:\n'
                  '            total += a["days"]\n'
                  '    return total\n'),
        trap=('def total_days(admissions, ward):\n'
              '    total = 0\n'
              '    for a in admissions:\n'
              '        if a["ward"] == ward:\n'
              '            total += a["days"]\n'
              '    return total\n'),
        note="SQL's SUM skips NULLs for you; Python's += does not, and"
             " adding None to a number is a TypeError on the first open"
             " admission it meets. Two conditions joined by and, one on"
             " the ward and one on the value being present, is the"
             " Python WHERE clause.",
    ),
    dict(
        id=4, ledger="P104", concept="PY5 max by field", tier="1 - One list of rows",
        title="The longest completed stay", kind="function",
        func="longest_stay",
        cases=[(ADM,), ([ADM[1], ADM[2]],), ([ADM[1]],)],
        prompt=(
            "Write `longest_stay(admissions)` returning the id of the"
            " completed admission with the most days, or None if there is"
            " no completed admission. Open ones (days None) do not"
            " count:\n\n"
            "  longest_stay(ADM) -> 4\n\n"
            "Return: an id, or None."
        ),
        solution=('def longest_stay(admissions):\n'
                  '    best = None\n'
                  '    for a in admissions:\n'
                  '        if a["days"] is None:\n'
                  '            continue\n'
                  '        if best is None or a["days"] > best["days"]:\n'
                  '            best = a\n'
                  '    return None if best is None else best["id"]\n'),
        trap=('def longest_stay(admissions):\n'
              '    best = None\n'
              '    for a in admissions:\n'
              '        if best is None or a["days"] > best["days"]:\n'
              '            best = a\n'
              '    return None if best is None else best["id"]\n'),
        note="ORDER BY days DESC LIMIT 1, by hand: keep the best row seen"
             " and replace it on a strictly greater value. The open"
             " admission has to be skipped first -- comparing None with a"
             " number is a TypeError -- and `continue` jumps to the next"
             " row. max(rows, key=...) does the same once the open ones"
             " are filtered out.",
    ),
    dict(
        id=5, ledger="P105", concept="PY5 average", tier="1 - One list of rows",
        title="Average stay, rounded", kind="function",
        func="average_days",
        cases=[(ADM,), ([ADM[1]],), ([],)],
        prompt=(
            "Write `average_days(admissions)` returning the mean days of"
            " the completed admissions rounded to one decimal, or None if"
            " there are none to average -- AVG(days):\n\n"
            "  average_days(ADM) -> 3.7\n\n"
            "Return: the mean, or None."
        ),
        solution=('def average_days(admissions):\n'
                  '    values = [a["days"] for a in admissions if a["days"] is not None]\n'
                  '    if not values:\n'
                  '        return None\n'
                  '    return round(sum(values) / len(values), 1)\n'),
        trap=('def average_days(admissions):\n'
              '    values = [a["days"] for a in admissions if a["days"] is not None]\n'
              '    return round(sum(values) / len(admissions), 1)\n'),
        note="AVG divides by the rows it did not skip, so the denominator"
             " is the number of VALUES, not the number of rows -- the open"
             " admission is left out of both. The empty case has to be"
             " caught before the division: sum([]) is 0 but len([]) is 0"
             " too, and 0 / 0 is a ZeroDivisionError. SQL's AVG of no rows"
             " is NULL; here that is None.",
    ),
    # ================================================ 2 Grouping and ranking
    dict(
        id=6, ledger="P106", concept="PY5 having", tier="2 - Grouping and ranking",
        title="Patients admitted more than n times", kind="function",
        func="frequent_patients",
        cases=[(ADM, 1), (ADM, 2), ([], 0)],
        prompt=(
            "Write `frequent_patients(admissions, n)` returning a SORTED"
            " list of the patient ids with more than n admissions -- GROUP"
            " BY patient HAVING COUNT(*) > n:\n\n"
            "  frequent_patients(ADM, 1) -> [7, 9]\n\n"
            "Return: a sorted list of patient ids."
        ),
        solution=('def frequent_patients(admissions, n):\n'
                  '    counts = {}\n'
                  '    for a in admissions:\n'
                  '        counts[a["patient"]] = counts.get(a["patient"], 0) + 1\n'
                  '    return sorted(p for p, c in counts.items() if c > n)\n'),
        trap=('def frequent_patients(admissions, n):\n'
              '    counts = {}\n'
              '    for a in admissions:\n'
              '        counts[a["patient"]] = counts.get(a["patient"], 0) + 1\n'
              '    return sorted(p for p, c in counts.items() if c >= n)\n'),
        note="Count first, then filter the counts: two passes, like GROUP"
             " BY then HAVING. 'More than n' is > n; >= n admits every"
             " patient with exactly n. sorted() over the surviving keys"
             " gives the list a fixed order, which the grader needs and a"
             " caller usually wants.",
    ),
    dict(
        id=7, ledger="P107", concept="PY5 group to lists", tier="2 - Grouping and ranking",
        title="Ids grouped by priority", kind="function",
        func="by_priority",
        cases=[(ADM,), ([],), ([ADM[3]],)],
        prompt=(
            "Write `by_priority(admissions)` returning a dict from each"
            " priority to the LIST of admission ids with it, in the order"
            " given:\n\n"
            "  by_priority(ADM) -> {'urgent': [1, 5], 'routine': [2, 4],"
            " 'immediate': [3]}\n\n"
            "setdefault(key, []) gives you the list to append to, creating"
            " it the first time.\n\n"
            "Return: the dict of lists."
        ),
        solution=('def by_priority(admissions):\n'
                  '    groups = {}\n'
                  '    for a in admissions:\n'
                  '        groups.setdefault(a["priority"], []).append(a["id"])\n'
                  '    return groups\n'),
        trap=('def by_priority(admissions):\n'
              '    groups = {}\n'
              '    for a in admissions:\n'
              '        groups[a["priority"]] = [a["id"]]\n'
              '    return groups\n'),
        note="Grouping rows rather than counting them: the value in the"
             " dict is a list, and each row is appended to its group's"
             " list. Assigning a fresh one-item list each time keeps only"
             " the last id per priority. setdefault returns the existing"
             " list or installs the empty one you pass; the if-not-in"
             " form says the same in two lines.",
    ),
    dict(
        id=8, ledger="P108", concept="PY5 argmax", tier="2 - Grouping and ranking",
        title="The busiest ward", kind="function",
        func="busiest_ward",
        cases=[(ADM,), ([ADM[3]],), ([ADM[0], ADM[1]],)],
        prompt=(
            "Write `busiest_ward(admissions)` returning the ward with the"
            " most admissions; on a tie, the one that appears FIRST in the"
            " list. The list is never empty:\n\n"
            "  busiest_ward(ADM) -> 'Fleming'\n\n"
            "Return: the ward name."
        ),
        solution=('def busiest_ward(admissions):\n'
                  '    counts = {}\n'
                  '    for a in admissions:\n'
                  '        counts[a["ward"]] = counts.get(a["ward"], 0) + 1\n'
                  '    return max(counts, key=counts.get)\n'),
        trap=('def busiest_ward(admissions):\n'
              '    counts = {}\n'
              '    for a in admissions:\n'
              '        counts[a["ward"]] = counts.get(a["ward"], 0) + 1\n'
              '    return max(counts.values())\n'),
        note="Count, then max(counts, key=counts.get): iterate the keys,"
             " judge each by its count, return the key. max(counts.values"
             "()) is the count itself, 2, not the ward. Because dicts keep"
             " insertion order and max() keeps the first of equal values,"
             " the tie goes to the ward seen first -- ORDER BY n DESC,"
             " first_seen LIMIT 1.",
    ),
    dict(
        id=9, ledger="P109", concept="PY5 top n", tier="2 - Grouping and ranking",
        title="The n longest stays", kind="function",
        func="top_n",
        cases=[(ADM, 2), (ADM, 10), (ADM, 0)],
        prompt=(
            "Write `top_n(admissions, n)` returning the ids of the n"
            " completed admissions with the most days, longest first --"
            " ORDER BY days DESC LIMIT n. Open admissions are excluded,"
            " and fewer than n are returned if fewer exist:\n\n"
            "  top_n(ADM, 2) -> [4, 1]\n\n"
            "Return: a list of ids."
        ),
        solution=('def top_n(admissions, n):\n'
                  '    done = [a for a in admissions if a["days"] is not None]\n'
                  '    done.sort(key=lambda a: a["days"], reverse=True)\n'
                  '    return [a["id"] for a in done[:n]]\n'),
        trap=('def top_n(admissions, n):\n'
              '    done = [a for a in admissions if a["days"] is not None]\n'
              '    done.sort(key=lambda a: a["days"])\n'
              '    return [a["id"] for a in done[:n]]\n'),
        note="Filter, sort, slice: the three clauses in Python's order."
             " sort(key=..., reverse=True) is ORDER BY days DESC; without"
             " reverse it is ascending and the slice takes the shortest."
             " A slice past the end returns what there is, so LIMIT 10 on"
             " four rows needs no special case. The lambda names the"
             " field to sort by.",
    ),
    # ========================================================= 3 Two tables
    dict(
        id=10, ledger="P110", concept="PY5 ordered sequence", tier="3 - Two tables",
        title="The route through the wards", kind="function",
        func="route",
        cases=[([(1, 2, "Fleming"), (1, 1, "Barry"), (2, 1, "Jenner"), (1, 3, "Lister")], 1),
               ([(1, 2, "Fleming"), (1, 1, "Barry")], 2)],
        prompt=(
            "Ward stays are tuples (admission_id, stay_seq, ward), not"
            " necessarily in order. Write `route(stays, admission_id)`"
            " returning the wards of that admission in stay_seq order:\n\n"
            "  route([(1, 2, 'Fleming'), (1, 1, 'Barry'), (2, 1, 'Jenner')],"
            " 1) -> ['Barry', 'Fleming']\n\n"
            "Return: a list of ward names; empty if the admission has none."
        ),
        solution=('def route(stays, admission_id):\n'
                  '    mine = [s for s in stays if s[0] == admission_id]\n'
                  '    mine.sort(key=lambda s: s[1])\n'
                  '    return [s[2] for s in mine]\n'),
        trap=('def route(stays, admission_id):\n'
              '    return [s[2] for s in stays if s[0] == admission_id]\n'),
        note="Rows have no order until you sort them -- in SQL or in"
             " Python. The trap keeps the wards in the order the tuples"
             " happened to arrive, which here is wrong. Tuple fields are"
             " reached by position, s[1] for the sequence, so the sort key"
             " is a lambda picking that position. WHERE, then ORDER BY,"
             " then SELECT.",
    ),
    dict(
        id=11, ledger="P111", concept="PY5 dict join", tier="3 - Two tables",
        title="Admissions with the patient's name", kind="function",
        func="with_names",
        cases=[(ADM[:3], {7: "Ada Byron", 9: "Mary Seacole"}),
               (ADM[:2], {7: "Ada Byron"}), ([], {})],
        prompt=(
            "Patients are a dict from patient id to name. Write"
            " `with_names(admissions, patients)` returning a list of"
            " (admission id, patient name) tuples, one per admission in"
            " order, with None for a patient not in the dict -- a LEFT"
            " JOIN:\n\n"
            "  with_names(ADM[:2], {7: 'Ada Byron'}) -> [(1, 'Ada Byron'),"
            " (2, None)]\n\n"
            "Return: a list of tuples."
        ),
        solution=('def with_names(admissions, patients):\n'
                  '    return [(a["id"], patients.get(a["patient"])) for a in admissions]\n'),
        trap=('def with_names(admissions, patients):\n'
              '    return [(a["id"], patients[a["patient"]]) for a in admissions]\n'),
        note="A join in Python is a dict lookup per row, and the"
             " dictionary keyed on the join column is the index. Square"
             " brackets are the INNER join that fails loudly -- KeyError"
             " -- on a missing patient; get() is the LEFT join that fills"
             " in None. The result rows are tuples, as the question asks.",
    ),
    dict(
        id=12, ledger="P112", concept="PY5 interval count", tier="3 - Two tables",
        title="Who was on the ward on day d", kind="function",
        func="occupancy_on",
        cases=[([(1, 3, 7), (2, 5, None), (3, 8, 9)], 5), ([(1, 3, 7), (2, 5, None), (3, 8, 9)], 9),
               ([], 1)],
        prompt=(
            "Stays on one ward are tuples (admission_id, from_day, to_day),"
            " with to_day None while the stay is open. Write"
            " `occupancy_on(stays, day)` returning how many stays cover"
            " that day: began on or before it, and either open or ending"
            " AFTER it:\n\n"
            "  occupancy_on([(1, 3, 7), (2, 5, None), (3, 8, 9)], 5) -> 2\n\n"
            "Return: the count."
        ),
        solution=('def occupancy_on(stays, day):\n'
                  '    count = 0\n'
                  '    for _, start, end in stays:\n'
                  '        if start <= day and (end is None or end > day):\n'
                  '            count += 1\n'
                  '    return count\n'),
        trap=('def occupancy_on(stays, day):\n'
              '    count = 0\n'
              '    for _, start, end in stays:\n'
              '        if start <= day and end > day:\n'
              '            count += 1\n'
              '    return count\n'),
        note="The interval test from the SQL tab, in Python: start <= day"
             " and not yet ended. The open end is None, and None > day is"
             " a TypeError rather than SQL's quiet NULL -- so the None"
             " case is spelled out with `or`, and it goes first, because"
             " `or` stops at the first true operand. Unpacking the tuple"
             " in the for line names the three fields.",
    ),
    # ================================================= 4 Checks and windows
    dict(
        id=13, ledger="P113", concept="PY5 readmission", tier="4 - Checks and windows",
        title="Readmitted within a window", kind="function",
        func="readmitted_within",
        cases=[([(7, 1, 4), (9, 2, 6), (7, 20, 22), (9, 30, 31)], 14),
               ([(7, 1, 20), (7, 30, 32)], 14), ([(7, 1, 4), (7, 30, 32)], 14), ([], 7)],
        prompt=(
            "Admissions are tuples (patient, admitted_day, discharged_day)"
            " in admission order. Write `readmitted_within(admissions,"
            " window)` returning the sorted list of patients who were"
            " admitted again within `window` days of a previous"
            " discharge -- admitted_day minus the earlier discharged_day"
            " at most window:\n\n"
            "  readmitted_within([(7, 1, 4), (9, 2, 6), (7, 20, 22),"
            " (9, 30, 31)], 14) -> []\n"
            "  readmitted_within([(7, 1, 4), (7, 10, 12)], 14) -> [7]\n\n"
            "Return: a sorted list of patient ids, each once."
        ),
        solution=('def readmitted_within(admissions, window):\n'
                  '    last_out = {}\n'
                  '    hits = set()\n'
                  '    for patient, start, end in admissions:\n'
                  '        if patient in last_out and start - last_out[patient] <= window:\n'
                  '            hits.add(patient)\n'
                  '        last_out[patient] = end\n'
                  '    return sorted(hits)\n'),
        trap=('def readmitted_within(admissions, window):\n'
              '    last_in = {}\n'
              '    hits = set()\n'
              '    for patient, start, end in admissions:\n'
              '        if patient in last_in and start - last_in[patient] <= window:\n'
              '            hits.add(patient)\n'
              '        last_in[patient] = start\n'
              '    return sorted(hits)\n'),
        note="A dict remembering each patient's LAST DISCHARGE plays the"
             " part LAG played in SQL: one pass, look up the previous"
             " value, then store this row's. Remembering the previous"
             " admission instead measures start to start, which includes"
             " the stay and over-counts -- the second trap case. A set"
             " collects each patient once; sorted() fixes the order.",
    ),
    dict(
        id=14, ledger="P114", concept="PY5 generic filter", tier="4 - Checks and windows",
        title="WHERE column = value, for any column", kind="function",
        func="where_equal",
        cases=[(ADM, "ward", "Barry"), (ADM, "priority", "immediate"), (ADM, "ward", "Lister")],
        prompt=(
            "Write `where_equal(rows, key, value)` returning the rows --"
            " the dicts themselves -- whose field `key` equals `value`, in"
            " order. The column name arrives as a string, so it indexes"
            " the dict:\n\n"
            "  where_equal(ADM, 'priority', 'immediate') -> [{'id': 3, ...}]\n\n"
            "Return: a list of dicts."
        ),
        solution=('def where_equal(rows, key, value):\n'
                  '    return [r for r in rows if r[key] == value]\n'),
        trap=('def where_equal(rows, key, value):\n'
              '    return [r[key] for r in rows if r[key] == value]\n'),
        note="r[key] with key a variable is what makes the filter generic:"
             " the same function serves any column. The trap projects the"
             " matched column instead of returning the row, so the result"
             " is ['Barry', 'Barry'] where the rows were wanted. In SQL"
             " the column name cannot be a parameter; in Python it is just"
             " a string.",
    ),
    dict(
        id=15, ledger="P115", concept="PY5 validation", tier="4 - Checks and windows",
        title="Problems with a row", kind="function",
        func="problems",
        cases=[({"id": 1, "patient": 7, "ward": "Fleming", "days": 3.5, "priority": "urgent"},),
               ({"id": 2, "ward": "", "days": -1, "priority": "high"},),
               ({"id": 3, "patient": 1, "ward": "Barry", "days": None, "priority": "routine"},)],
        prompt=(
            "Write `problems(row)` returning a list of the things wrong"
            " with one admission dict, in this order and with these exact"
            " strings: 'no patient' if the key patient is missing, 'no"
            " ward' if ward is missing or empty, 'negative days' if days"
            " is a number below 0 (None is fine), 'bad priority' if"
            " priority is not one of immediate, urgent, routine:\n\n"
            "  problems({'id': 2, 'ward': '', 'days': -1, 'priority':"
            " 'high'}) -> ['no patient', 'no ward', 'negative days', 'bad"
            " priority']\n\n"
            "Return: the list; empty for a good row."
        ),
        solution=('def problems(row):\n'
                  '    out = []\n'
                  '    if "patient" not in row:\n'
                  '        out.append("no patient")\n'
                  '    if not row.get("ward"):\n'
                  '        out.append("no ward")\n'
                  '    days = row.get("days")\n'
                  '    if days is not None and days < 0:\n'
                  '        out.append("negative days")\n'
                  '    if row.get("priority") not in ("immediate", "urgent", "routine"):\n'
                  '        out.append("bad priority")\n'
                  '    return out\n'),
        trap=('def problems(row):\n'
              '    out = []\n'
              '    if "patient" not in row:\n'
              '        out.append("no patient")\n'
              '    if not row.get("ward"):\n'
              '        out.append("no ward")\n'
              '    if row.get("days") < 0:\n'
              '        out.append("negative days")\n'
              '    if row.get("priority") not in ("immediate", "urgent", "routine"):\n'
              '        out.append("bad priority")\n'
              '    return out\n'),
        note="A CHECK constraint as a function: each rule appends its"
             " message, and the list is the verdict. `key in row` tests"
             " for a key; row.get() reads one that may be missing without"
             " a KeyError; `not row.get('ward')` catches both missing and"
             " empty. None < 0 is a TypeError, so the days rule has to"
             " test for None first -- the third case is a valid open"
             " admission that the trap crashes on.",
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
