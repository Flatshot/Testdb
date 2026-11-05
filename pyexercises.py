"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-first Python set, at the easy level of the last one -- no
statistics, no dicts -- on tasks that set did not cover. Counting and
finding: the stop after a station, the stations visited only once, visits
before a point in the day, what two days have in common with the order
kept, where the stops first change. Labels: a 12-hour clock, a station
code, a greeting for the hour, a countdown in words, a one-line ride
summary. Checks and filters: all the same, the stops up to a station, the
ends swapped, the last n, legs from two lists.

Every question is a `kind="function"`: the editor defines a function named
`func`. Run calls it once per case in `cases` and shows each call and its
result; Check compares each result with the reference function's. Values
are compared, not their printed form, but the container type counts, so a
tuple is not a list, and 0 is not False.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py).
"""

import pyrun

EXERCISES = [
    # ================================================= 1 Counting and finding
    dict(
        id=1, ledger="P461", concept="PY4 item after a value", tier="1 - Counting and finding",
        title="Where the bike went after Harbour", kind="function",
        func="stop_after",
        cases=[(["Parkway", "Harbour", "Stadium"], "Harbour"), (["Parkway", "Harbour"], "Harbour"), (["Parkway", "Stadium"], "Harbour"), ([], "Harbour")],
        prompt=(
            "Write a function `stop_after(stops, station)` that returns"
            " the stop that came right after the station's FIRST"
            " appearance, or None when the station is missing or was"
            " the last stop. Two things to check before indexing.\n\n"
            "  stop_after([\"Parkway\", \"Harbour\", \"Stadium\"], \"Harbour\") -> \"Stadium\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def stop_after(stops, station):\n"
                  "    if station not in stops:\n"
                  "        return None\n"
                  "    i = stops.index(station)\n"
                  "    if i == len(stops) - 1:\n"
                  "        return None\n"
                  "    return stops[i + 1]\n"),
        trap=("def stop_after(stops, station):\n"
              "    return stops[stops.index(station) + 1]\n"),
        note="Two different things can go wrong with stops[index + 1]:"
             " index() raises ValueError when the station is not there,"
             " and the + 1 runs off the end when it was the last stop,"
             " an IndexError. The trap hits both. Each needs its own"
             " check, and the order matters -- index() cannot be called"
             " until `in` has said it is safe.",
    ),
    dict(
        id=2, ledger="P462", concept="PY4 items appearing once", tier="1 - Counting and finding",
        title="The stations visited only once", kind="function",
        func="visited_once",
        cases=[(["Harbour", "Stadium", "Harbour", "Parkway"],), (["Harbour", "Harbour"],), ([],), (["Stadium"],)],
        prompt=(
            "Write a function `visited_once(stops)` that returns the"
            " stations that appear exactly once in the day's stops, in"
            " the order they appear. A comprehension that keeps a stop"
            " when its count() in the list is 1.\n\n"
            "  visited_once([\"Harbour\", \"Stadium\", \"Harbour\", \"Parkway\"]) -> [\"Stadium\", \"Parkway\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def visited_once(stops):\n"
                  "    return [s for s in stops if stops.count(s) == 1]\n"),
        trap=("def visited_once(stops):\n"
              "    return list(set(stops))\n"),
        note="set() removes the repeats but keeps one copy of each"
             " station, so Harbour is still there, and a set has no"
             " order, so the trap's list comes out in whatever order"
             " the set holds. count() asks how many times a value"
             " appears, and == 1 is the question's exact meaning of"
             " 'only once'.",
    ),
    dict(
        id=3, ledger="P463", concept="PY3 count in a slice", tier="1 - Counting and finding",
        title="Visits before midday", kind="function",
        func="visits_before",
        cases=[(["Harbour", "Stadium", "Harbour", "Harbour"], "Harbour", 3), (["Harbour", "Stadium", "Harbour", "Harbour"], "Harbour", 0), (["Harbour"], "Harbour", 10), ([], "Harbour", 2)],
        prompt=(
            "The first n stops of the day happened before midday."
            " Write a function `visits_before(stops, station, n)` that"
            " returns how many of those first n stops were at the"
            " station. A slice, then count().\n\n"
            "  visits_before([\"Harbour\", \"Stadium\", \"Harbour\", \"Harbour\"], \"Harbour\", 3) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def visits_before(stops, station, n):\n"
                  "    return stops[:n].count(station)\n"),
        trap=("def visits_before(stops, station, n):\n"
              "    return stops.count(station)\n"),
        note="count() over the whole list ignores the cut-off: the trap"
             " says 3 for the first three stops, which hold only two"
             " Harbours. stops[:n] is the first n items -- all of them"
             " when n is more than the length, none when n is 0 -- and"
             " count() on that slice is the answer, with no loop and no"
             " guard.",
    ),
    dict(
        id=4, ledger="P464", concept="PY4 common items in order", tier="1 - Counting and finding",
        title="Stations both bikes reached, in the first bike's order", kind="function",
        func="both_reached",
        cases=[(["Stadium", "Harbour", "Parkway"], ["Parkway", "Stadium"]), (["Harbour", "Harbour", "Stadium"], ["Harbour"]), (["Stadium"], ["Parkway"]), ([], ["Stadium"])],
        prompt=(
            "Write a function `both_reached(first, second)` that returns"
            " the stops of the first bike's day that the second bike"
            " also reached, in the first bike's order, repeats kept. A"
            " comprehension over the first list with `in` on the"
            " second.\n\n"
            "  both_reached([\"Stadium\", \"Harbour\", \"Parkway\"], [\"Parkway\", \"Stadium\"]) -> [\"Stadium\", \"Parkway\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def both_reached(first, second):\n"
                  "    return [s for s in first if s in second]\n"),
        trap=("def both_reached(first, second):\n"
              "    return sorted(set(first) & set(second))\n"),
        note="Set intersection finds the right stations but drops the"
             " repeats and the order: the trap returns ['Parkway',"
             " 'Stadium'] alphabetically, and one Harbour where the"
             " first bike reached it twice. Looping over the first list"
             " and testing membership in the second keeps the first"
             " list's order and its repeats, which is what was asked.",
    ),
    dict(
        id=5, ledger="P465", concept="PY4 first change", tier="1 - Counting and finding",
        title="When the bike first moved on", kind="function",
        func="first_change",
        cases=[(["Harbour", "Harbour", "Stadium", "Harbour"],), (["Harbour", "Harbour"],), (["Harbour", "Stadium"],), ([],)],
        prompt=(
            "Write a function `first_change(stops)` that returns the"
            " position of the first stop that differs from the first"
            " stop of the day, or -1 if every stop is the same (or"
            " there are none). A loop with enumerate, comparing with"
            " stops[0].\n\n"
            "  first_change([\"Harbour\", \"Harbour\", \"Stadium\", \"Harbour\"]) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def first_change(stops):\n"
                  "    for i, s in enumerate(stops):\n"
                  "        if s != stops[0]:\n"
                  "            return i\n"
                  "    return -1\n"),
        trap=("def first_change(stops):\n"
              "    for i, s in enumerate(stops):\n"
              "        if s != stops[0]:\n"
              "            return i\n"),
        note="A loop that never finds a change falls off the end, and a"
             " function that falls off the end returns None, not -1."
             " The trap is right whenever a change exists and wrong"
             " whenever it does not. On an empty list the loop body"
             " never runs, so stops[0] is never evaluated and the final"
             " return -1 is reached safely.",
    ),
    # ================================================================ 2 Labels
    dict(
        id=6, ledger="P466", concept="PY3 twelve-hour clock", tier="2 - Labels",
        title="The hour on a 12-hour clock", kind="function",
        func="twelve_hour",
        cases=[(15,), (0,), (12,), (8,), (23,)],
        prompt=(
            "Write a function `twelve_hour(hour)` that turns an hour"
            " from 0 to 23 into '3 pm', '12 am', '12 pm' or '8 am':"
            " am before 12, pm from 12; the hour shown is hour % 12,"
            " except that 0 is shown as 12.\n\n"
            "  twelve_hour(15) -> \"3 pm\"\n\n"
            "Return: a str."
        ),
        solution=("def twelve_hour(hour):\n"
                  "    suffix = \"am\" if hour < 12 else \"pm\"\n"
                  "    shown = hour % 12\n"
                  "    if shown == 0:\n"
                  "        shown = 12\n"
                  "    return f\"{shown} {suffix}\"\n"),
        trap=("def twelve_hour(hour):\n"
              "    suffix = \"am\" if hour < 12 else \"pm\"\n"
              "    return f\"{hour % 12} {suffix}\"\n"),
        note="hour % 12 is 0 for both midnight and noon, and a clock"
             " shows those as 12: the trap writes '0 am' and '0 pm'. The"
             " am/pm split and the number shown are two separate"
             " decisions, and the special case is on the number only."
             " 12 is pm (noon) and 0 is am (midnight), which the < 12"
             " test gets right on its own.",
    ),
    dict(
        id=7, ledger="P467", concept="PY3 slice and upper", tier="2 - Labels",
        title="A three-letter station code", kind="function",
        func="station_code",
        cases=[("Market Square",), ("Old Mill",), ("Hilltop",), ("Ab",)],
        prompt=(
            "Write a function `station_code(name)` that returns the"
            " first three characters of the name in capitals, or the"
            " whole name in capitals if it is shorter. A slice and"
            " upper().\n\n"
            "  station_code(\"Market Square\") -> \"MAR\"\n\n"
            "Return: a str."
        ),
        solution=("def station_code(name):\n"
                  "    return name[:3].upper()\n"),
        trap=("def station_code(name):\n"
              "    return name[:3]\n"),
        note="The trap forgets upper() and returns 'Mar'. A slice past"
             " the end of a short string just stops at the end, so 'Ab'"
             " gives 'AB' without any length check. Codes are usually"
             " capitals so that 'MAR' typed in any case can be matched"
             " after upper() on both sides.",
    ),
    dict(
        id=8, ledger="P468", concept="PY4 if/elif by hour", tier="2 - Labels",
        title="Good morning, good afternoon, good evening", kind="function",
        func="greeting",
        cases=[("Hamid", 9), ("Rosa", 12), ("Yusuf", 17), ("Zara", 18), ("Umar", 0)],
        prompt=(
            "Write a function `greeting(name, hour)` that returns 'Good"
            " morning, Hamid' before 12, 'Good afternoon, ...' from 12"
            " up to but not including 18, and 'Good evening, ...' from"
            " 18. An if/elif/else on the hour inside one f-string.\n\n"
            "  greeting(\"Rosa\", 12) -> \"Good afternoon, Rosa\"\n\n"
            "Return: a str."
        ),
        solution=("def greeting(name, hour):\n"
                  "    if hour < 12:\n"
                  "        part = \"morning\"\n"
                  "    elif hour < 18:\n"
                  "        part = \"afternoon\"\n"
                  "    else:\n"
                  "        part = \"evening\"\n"
                  "    return f\"Good {part}, {name}\"\n"),
        trap=("def greeting(name, hour):\n"
              "    if hour <= 12:\n"
              "        part = \"morning\"\n"
              "    elif hour <= 18:\n"
              "        part = \"afternoon\"\n"
              "    else:\n"
              "        part = \"evening\"\n"
              "    return f\"Good {part}, {name}\"\n"),
        note="The boundaries are where these go wrong: noon is"
             " afternoon and 18:00 is evening, so the tests are < 12"
             " and < 18, not <=. The trap greets Rosa with 'Good"
             " morning' at noon and Zara with 'Good afternoon' at six."
             " Picking the word first and formatting once keeps the"
             " f-string in a single place.",
    ),
    dict(
        id=9, ledger="P469", concept="PY4 if/elif countdown words", tier="2 - Labels",
        title="Today, tomorrow, in 3 days", kind="function",
        func="due_label",
        cases=[(0,), (1,), (3,), (14,)],
        prompt=(
            "Write a function `due_label(days)` that says when a"
            " payment is due: 'today' for 0, 'tomorrow' for 1, and 'in"
            " 3 days' (with the number) for anything more. Two special"
            " cases, then the general one.\n\n"
            "  due_label(3) -> \"in 3 days\"\n\n"
            "Return: a str."
        ),
        solution=("def due_label(days):\n"
                  "    if days == 0:\n"
                  "        return \"today\"\n"
                  "    if days == 1:\n"
                  "        return \"tomorrow\"\n"
                  "    return f\"in {days} days\"\n"),
        trap=("def due_label(days):\n"
              "    return f\"in {days} days\"\n"),
        note="'in 0 days' and 'in 1 days' are what the trap says, and"
             " neither is English. Special cases are tested first and"
             " return early, so the general f-string at the end never"
             " sees them. Three returns in one function is fine when"
             " each is a complete answer.",
    ),
    dict(
        id=10, ledger="P470", concept="PY3 f-string summary", tier="2 - Labels",
        title="A ride in one line", kind="function",
        func="ride_summary",
        cases=[("Harbour", "Stadium", 32), ("Market Square", "Market Square", 5), ("Hilltop", "Old Mill", 120)],
        prompt=(
            "Write a function `ride_summary(start, end, minutes)` that"
            " returns 'Harbour to Stadium (32 min)': the two stations"
            " joined by ' to ', then the minutes in brackets with"
            " 'min'. One f-string.\n\n"
            "  ride_summary(\"Harbour\", \"Stadium\", 32) -> \"Harbour to Stadium (32 min)\"\n\n"
            "Return: a str."
        ),
        solution=("def ride_summary(start, end, minutes):\n"
                  "    return f\"{start} to {end} ({minutes} min)\"\n"),
        trap=("def ride_summary(start, end, minutes):\n"
              "    return f\"{start} to {end} {minutes} min\"\n"),
        note="The grader compares the whole string, so the brackets and"
             " every space count: the trap's 'Harbour to Stadium 32 min'"
             " is a different string. An f-string puts each value where"
             " its braces are, numbers converted to text as they go, so"
             " no str() is needed.",
    ),
    # ==================================================== 3 Checks and filters
    dict(
        id=11, ledger="P471", concept="PY3 all the same", tier="3 - Checks and filters",
        title="Did the bike stay put all day?", kind="function",
        func="all_same",
        cases=[(["Harbour", "Harbour", "Harbour"],), (["Harbour", "Stadium"],), (["Harbour"],), ([],)],
        prompt=(
            "Write a function `all_same(stops)` that returns True when"
            " every stop is the same station, and True for an empty"
            " list too (nothing differs). The number of DIFFERENT"
            " values is the thing to test.\n\n"
            "  all_same([\"Harbour\", \"Harbour\", \"Harbour\"]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def all_same(stops):\n"
                  "    return len(set(stops)) <= 1\n"),
        trap=("def all_same(stops):\n"
              "    return len(set(stops)) == 1\n"),
        note="A set of the stops has one member when they are all the"
             " same and none when the list is empty, so <= 1 covers"
             " both; == 1, the trap, calls the empty day False. all(s"
             " == stops[0] for s in stops) is another way, and it is"
             " also True for the empty list, because all() of nothing"
             " is True.",
    ),
    dict(
        id=12, ledger="P472", concept="PY3 slice up to a value", tier="3 - Checks and filters",
        title="The stops before the bike reached Harbour", kind="function",
        func="until",
        cases=[(["Parkway", "Stadium", "Harbour", "Hilltop"], "Harbour"), (["Harbour", "Stadium"], "Harbour"), (["Parkway", "Stadium"], "Harbour"), ([], "Harbour")],
        prompt=(
            "Write a function `until(stops, station)` that returns the"
            " stops before the station's first appearance -- not"
            " including it -- or the whole list if the station never"
            " appears. A membership test, then index() and a slice.\n\n"
            "  until([\"Parkway\", \"Stadium\", \"Harbour\", \"Hilltop\"], \"Harbour\") -> [\"Parkway\", \"Stadium\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def until(stops, station):\n"
                  "    if station not in stops:\n"
                  "        return stops[:]\n"
                  "    return stops[:stops.index(station)]\n"),
        trap=("def until(stops, station):\n"
              "    return stops[:stops.index(station)]\n"),
        note="stops[:i] is everything before position i, which is"
             " exactly 'up to but not including' when i is the"
             " station's index. index() raises when the station is"
             " missing, so the trap crashes on a day that never reached"
             " Harbour; the `in` test first returns the whole list"
             " instead. stops[:] is a copy, so the caller's list is"
             " never handed back to be changed.",
    ),
    dict(
        id=13, ledger="P473", concept="PY4 swap first and last", tier="3 - Checks and filters",
        title="The first and last stops swapped", kind="function",
        func="swap_ends",
        cases=[(["Harbour", "Stadium", "Parkway"],), (["Harbour", "Stadium"],), (["Harbour"],), ([],)],
        prompt=(
            "Write a function `swap_ends(stops)` that returns a NEW"
            " list with the first and last stops exchanged and the"
            " middle unchanged; a list of one or none comes back as a"
            " copy. Copy the list, then assign to positions 0 and -1"
            " in one tuple assignment.\n\n"
            "  swap_ends([\"Harbour\", \"Stadium\", \"Parkway\"]) -> [\"Parkway\", \"Stadium\", \"Harbour\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def swap_ends(stops):\n"
                  "    out = list(stops)\n"
                  "    if len(out) >= 2:\n"
                  "        out[0], out[-1] = out[-1], out[0]\n"
                  "    return out\n"),
        trap=("def swap_ends(stops):\n"
              "    return stops[-1:] + stops[1:-1] + stops[:1]\n"),
        note="Three slices glued together look right until a list of"
             " one: stops[-1:] and stops[:1] are then the same item,"
             " and the trap returns it twice. Copying and swapping two"
             " positions in one assignment -- out[0], out[-1] = out[-1],"
             " out[0] -- changes only the copy, and the length test"
             " leaves a list of one or none alone.",
    ),
    dict(
        id=14, ledger="P474", concept="PY3 last n with zero", tier="3 - Checks and filters",
        title="The last few stops", kind="function",
        func="last_stops",
        cases=[(["Harbour", "Stadium", "Parkway", "Hilltop"], 2), (["Harbour", "Stadium"], 5), (["Harbour", "Stadium"], 0), ([], 3)],
        prompt=(
            "Write a function `last_stops(stops, n)` that returns the"
            " last n stops -- all of them if there are fewer than n,"
            " and [] when n is 0. A negative slice is the natural"
            " tool, but one value of n needs care.\n\n"
            "  last_stops([\"Harbour\", \"Stadium\", \"Parkway\", \"Hilltop\"], 2) -> [\"Parkway\", \"Hilltop\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def last_stops(stops, n):\n"
                  "    if n == 0:\n"
                  "        return []\n"
                  "    return stops[-n:]\n"),
        trap=("def last_stops(stops, n):\n"
              "    return stops[-n:]\n"),
        note="stops[-2:] is the last two, and stops[-5:] of a two-item"
             " list is both items, so the negative slice handles a"
             " short list by itself. But -0 is 0, and stops[0:] is the"
             " WHOLE list: the trap returns everything when asked for"
             " nothing. The one special case has to be tested first;"
             " stops[len(stops) - n:] is another way round it.",
    ),
    dict(
        id=15, ledger="P475", concept="PY3 zip into strings", tier="3 - Checks and filters",
        title="Each leg of the day, start to end", kind="function",
        func="legs",
        cases=[(["Harbour", "Stadium"], ["Stadium", "Parkway"]), (["Harbour"], ["Harbour"]), ([], []), (["A", "B", "C"], ["B", "C"])],
        prompt=(
            "Two lists of the same length give each ride's start and"
            " end station. Write a function `legs(starts, ends)` that"
            " returns one string per ride, 'Harbour -> Stadium'. zip()"
            " pairs the lists up; an f-string makes each string. If the"
            " lists differ in length, stop at the shorter.\n\n"
            "  legs([\"Harbour\", \"Stadium\"], [\"Stadium\", \"Parkway\"]) -> [\"Harbour -> Stadium\", \"Stadium -> Parkway\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def legs(starts, ends):\n"
                  "    return [f\"{a} -> {b}\" for a, b in zip(starts, ends)]\n"),
        trap=("def legs(starts, ends):\n"
              "    return [(a, b) for a, b in zip(starts, ends)]\n"),
        note="zip() walks the two lists in step and stops at the"
             " shorter one, so the mismatched case needs no guard. The"
             " trap builds tuples instead of strings: the pairs are"
             " right but the type is not, and the grader keeps ('Harbour',"
             " 'Stadium') apart from 'Harbour -> Stadium'. The f-string"
             " is where the arrow and the spaces are decided.",
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
