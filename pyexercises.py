"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-seventh Python set, at the easy level of the last seven -- no
statistics, no dicts -- in the courier's terms, on tasks the earlier sets
did not cover. Counting and finding: times inside a window, a code found
by its number with a fallback, whether most of a batch was delivered, how
many codes two lists share, the numbers in a batch added up. Labels: a
change with its sign, the minutes between two clock times, a weight range,
a price-list line with dots, a date the British way round. Checks and
filters: repeats dropped whatever their case, a flat list paired up, a
code moved to the front, weights strictly rising, a trail padded out.

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
        id=1, ledger="P551", concept="PY3 count in a half-open window", tier="1 - Counting and finding",
        title="Scans inside a time window", kind="function",
        func="in_window",
        cases=[(["08:05", "09:00", "09:59", "10:00", "11:30"], "09:00", "10:00"), (["08:00"], "08:00", "08:00"), ([], "09:00", "10:00"), (["23:59", "00:00"], "00:00", "12:00")],
        prompt=(
            "Scan times are 'HH:MM' strings. Write a function"
            " `in_window(times, start, end)` that returns how many fall"
            " in the window that includes its start and EXCLUDES its"
            " end. Zero-padded clock text compares correctly, so a"
            " chained comparison inside sum() does it.\n\n"
            "  in_window([\"08:05\", \"09:00\", \"09:59\", \"10:00\", \"11:30\"], \"09:00\", \"10:00\") -> 2\n\n"
            "Return: an int."
        ),
        solution=("def in_window(times, start, end):\n"
                  "    return sum(start <= t < end for t in times)\n"),
        trap=("def in_window(times, start, end):\n"
              "    return sum(start <= t <= end for t in times)\n"),
        note="A window that includes both ends counts a scan at exactly"
             " 10:00 in the nine o'clock window AND in the ten o'clock"
             " one; the trap double-books every boundary. Start"
             " included, end excluded is the shape that lets windows sit"
             " side by side. Python's chained comparison start <= t <"
             " end reads like the maths, and the text compares in time"
             " order because it is zero-padded.",
    ),
    dict(
        id=2, ledger="P552", concept="PY3 next with a default", tier="1 - Counting and finding",
        title="The code with a given number", kind="function",
        func="find_code",
        cases=[(["MB-0012", "CH-0007", "WW-0100"], 7), (["MB-0012"], 99), ([], 1), (["A-5", "B-5"], 5)],
        prompt=(
            "Write a function `find_code(codes, n)` that returns the"
            " first code whose number after the hyphen equals n, or None"
            " if no code has that number. next() over a generator, with"
            " a second argument for the nothing-found case.\n\n"
            "  find_code([\"MB-0012\", \"CH-0007\", \"WW-0100\"], 7) -> \"CH-0007\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def find_code(codes, n):\n"
                  "    return next((c for c in codes if int(c.split(\"-\")[1]) == n), None)\n"),
        trap=("def find_code(codes, n):\n"
              "    return next(c for c in codes if int(c.split(\"-\")[1]) == n)\n"),
        note="next() takes the first item a generator produces and stops"
             " looking, which is 'the first match' in one call. With"
             " nothing to produce it raises StopIteration -- the trap"
             " crashes when the number is not there -- unless it is"
             " given a default as its second argument. The generator"
             " needs its own brackets when next() has two arguments.",
    ),
    dict(
        id=3, ledger="P553", concept="PY3 strict majority", tier="1 - Counting and finding",
        title="Was most of the batch delivered?", kind="function",
        func="mostly_delivered",
        cases=[(["delivered", "delivered", "failed"],), (["delivered", "failed"],), ([],), (["failed", "failed", "delivered"],)],
        prompt=(
            "Write a function `mostly_delivered(statuses)` that returns"
            " True when MORE than half of the statuses are 'delivered',"
            " and False otherwise -- exactly half is not more than half,"
            " and an empty batch is False. count(), doubled, against"
            " the length.\n\n"
            "  mostly_delivered([\"delivered\", \"delivered\", \"failed\"]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def mostly_delivered(statuses):\n"
                  "    return statuses.count(\"delivered\") * 2 > len(statuses)\n"),
        trap=("def mostly_delivered(statuses):\n"
              "    return statuses.count(\"delivered\") * 2 >= len(statuses)\n"),
        note="'More than half' is a strict comparison: one delivered out"
             " of two is half, not most, and the trap's >= calls it a"
             " majority -- and calls an empty batch one too, since 0 >="
             " 0. Doubling the count instead of halving the length keeps"
             " everything in whole numbers.",
    ),
    dict(
        id=4, ledger="P554", concept="PY3 size of an intersection", tier="1 - Counting and finding",
        title="How many codes two vans share", kind="function",
        func="shared",
        cases=[(["MB-1", "MB-2", "MB-2", "CH-3"], ["MB-2", "CH-3", "WW-4"]), (["MB-1"], ["CH-3"]), ([], ["MB-1"]), (["A", "A"], ["A"])],
        prompt=(
            "Two vans' manifests are lists of parcel codes, and a code"
            " may have been scanned twice. Write a function `shared("
            "first, second)` that returns how many DIFFERENT codes"
            " appear on both. Two sets, intersected, measured.\n\n"
            "  shared([\"MB-1\", \"MB-2\", \"MB-2\", \"CH-3\"], [\"MB-2\", \"CH-3\", \"WW-4\"]) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def shared(first, second):\n"
                  "    return len(set(first) & set(second))\n"),
        trap=("def shared(first, second):\n"
              "    return sum(1 for c in first if c in second)\n"),
        note="Looping over the first list counts a code once for every"
             " time it was scanned, so the trap says 3 for the example:"
             " MB-2 twice and CH-3 once. Sets hold each code once, &"
             " keeps what is in both, and len() counts the different"
             " codes, which is what was asked.",
    ),
    dict(
        id=5, ledger="P555", concept="PY3 sum of converted parts", tier="1 - Counting and finding",
        title="The numbers in a batch, added up", kind="function",
        func="number_total",
        cases=[(["MB-0012", "CHB-0007", "WW-100"],), (["MB-0001"],), ([],), (["LONG-5", "X-5"],)],
        prompt=(
            "As a quick check on a batch, the numbers after the hyphens"
            " are added up. Write a function `number_total(codes)` that"
            " returns that sum. The depot code can be any length, so"
            " split at the hyphen rather than slicing.\n\n"
            "  number_total([\"MB-0012\", \"CHB-0007\", \"WW-100\"]) -> 119\n\n"
            "Return: an int."
        ),
        solution=("def number_total(codes):\n"
                  "    return sum(int(c.split(\"-\")[1]) for c in codes)\n"),
        trap=("def number_total(codes):\n"
              "    return sum(int(c[3:]) for c in codes)\n"),
        note="Slicing from position 3 assumes a two-letter depot and a"
             " hyphen: 'CHB-0007' slices to '-0007', which int() reads as"
             " MINUS seven, and 'LONG-5' slices to 'G-5' and crashes."
             " split('-') finds the hyphen wherever it is. sum() of an"
             " empty generator is 0.",
    ),
    # ================================================================ 2 Labels
    dict(
        id=6, ledger="P556", concept="PY3 signed percentage", tier="2 - Labels",
        title="A change with its sign showing", kind="function",
        func="change_label",
        cases=[(1099, 1523), (200, 190), (50, 50), (0, 10)],
        prompt=(
            "Write a function `change_label(before, after)` that returns"
            " the change as a whole-number percentage of before with its"
            " sign: '+39%' for a rise, '-5%' for a fall, '0%' for no"
            " change, and 'n/a' when before is 0. The format spec '+'"
            " shows a plus on positive numbers.\n\n"
            "  change_label(1099, 1523) -> \"+39%\"\n\n"
            "Return: a str."
        ),
        solution=("def change_label(before, after):\n"
                  "    if before == 0:\n"
                  "        return \"n/a\"\n"
                  "    pct = round(100 * (after - before) / before)\n"
                  "    if pct == 0:\n"
                  "        return \"0%\"\n"
                  "    return f\"{pct:+d}%\"\n"),
        trap=("def change_label(before, after):\n"
              "    if before == 0:\n"
              "        return \"n/a\"\n"
              "    pct = round(100 * (after - before) / before)\n"
              "    return f\"{pct}%\"\n"),
        note="A negative number prints its own minus, but a positive one"
             " prints bare: the trap writes '39%', which reads as a level,"
             " not a change. The format spec :+d puts a sign on both."
             " Zero is its own case, because '+0%' is odd, and the guard"
             " for before == 0 comes first so the division never sees"
             " it.",
    ),
    dict(
        id=7, ledger="P557", concept="PY3 minutes between clock times", tier="2 - Labels",
        title="Minutes from one scan to the next", kind="function",
        func="minutes_between",
        cases=[("08:05", "09:20"), ("09:50", "10:10"), ("12:00", "12:00"), ("00:00", "23:59")],
        prompt=(
            "Write a function `minutes_between(start, end)` that takes"
            " two 'HH:MM' times on the same day, the second not before"
            " the first, and returns the minutes between them. Turn each"
            " into minutes since midnight -- hours times 60 plus"
            " minutes -- and subtract.\n\n"
            "  minutes_between(\"08:05\", \"09:20\") -> 75\n\n"
            "Return: an int."
        ),
        solution=("def minutes_between(start, end):\n"
                  "    def mins(t):\n"
                  "        h, m = t.split(\":\")\n"
                  "        return int(h) * 60 + int(m)\n"
                  "    return mins(end) - mins(start)\n"),
        trap=("def minutes_between(start, end):\n"
              "    return (int(end[:2]) - int(start[:2])) * 60\n"),
        note="Subtracting the hours alone, the trap, says an hour for"
             " 08:05 to 09:20 and an hour for 09:50 to 10:10, which is"
             " twenty minutes. Converting both times to minutes since"
             " midnight first makes the subtraction honest whatever the"
             " minutes are. A small helper function inside the function"
             " saves writing the conversion twice.",
    ),
    dict(
        id=8, ledger="P558", concept="PY3 range or single value", tier="2 - Labels",
        title="A weight band as a label", kind="function",
        func="band_label",
        cases=[(2, 5), (3, 3), (0, 1), (10, 30)],
        prompt=(
            "Write a function `band_label(low, high)` that returns a"
            " weight band in kilograms as '2-5 kg', or as just '3 kg'"
            " when the two ends are the same. A conditional expression"
            " between two f-strings.\n\n"
            "  band_label(2, 5) -> \"2-5 kg\"\n\n"
            "Return: a str."
        ),
        solution=("def band_label(low, high):\n"
                  "    return f\"{low} kg\" if low == high else f\"{low}-{high} kg\"\n"),
        trap=("def band_label(low, high):\n"
              "    return f\"{low}-{high} kg\"\n"),
        note="'3-3 kg' is a range with nothing in it, and the question"
             " asks for the plain '3 kg' instead. The special case is one"
             " comparison, and a conditional expression puts the two"
             " labels side by side on a single line.",
    ),
    dict(
        id=9, ledger="P559", concept="PY3 dotted leader", tier="2 - Labels",
        title="A line of the price list", kind="function",
        func="price_line",
        cases=[("Economy", 350, 12), ("Express", 1050, 12), ("Standard", 590, 8), ("A", 5, 3)],
        prompt=(
            "Write a function `price_line(name, cents, width)` that"
            " returns the name padded on the right with dots to the"
            " width, then the price as '$3.50': 'Economy.....$3.50'."
            " str.ljust() takes a fill character; the price is whole"
            " dollars and two-digit cents.\n\n"
            "  price_line(\"Economy\", 350, 12) -> \"Economy.....$3.50\"\n\n"
            "Return: a str."
        ),
        solution=("def price_line(name, cents, width):\n"
                  "    return name.ljust(width, \".\") + f\"${cents // 100}.{cents % 100:02d}\"\n"),
        trap=("def price_line(name, cents, width):\n"
              "    return name.ljust(width) + f\"${cents // 100}.{cents % 100:02d}\"\n"),
        note="ljust(width) pads with spaces unless told otherwise, so the"
             " trap's line has a gap where the dots should lead the eye"
             " across. The second argument is the fill character. A name"
             " already as long as the width gets no padding at all, and"
             " the price follows straight on.",
    ),
    dict(
        id=10, ledger="P560", concept="PY3 reorder a date", tier="2 - Labels",
        title="A date the British way round", kind="function",
        func="uk_date",
        cases=[("2026-03-04",), ("2025-12-31",), ("2026-01-01",)],
        prompt=(
            "Write a function `uk_date(iso)` that turns 'YYYY-MM-DD'"
            " into 'DD/MM/YYYY': the three parts in the opposite order,"
            " joined by slashes. split(), reverse, join().\n\n"
            "  uk_date(\"2026-03-04\") -> \"04/03/2026\"\n\n"
            "Return: a str."
        ),
        solution=("def uk_date(iso):\n"
                  "    return \"/\".join(reversed(iso.split(\"-\")))\n"),
        trap=("def uk_date(iso):\n"
              "    return iso.replace(\"-\", \"/\")\n"),
        note="Swapping the separator changes the punctuation and not the"
             " order: the trap returns '2026/03/04'. The parts have to be"
             " split apart, reversed and joined again. reversed() gives"
             " an iterator, which join() is happy to take; the parts stay"
             " text, so their leading zeros survive.",
    ),
    # ==================================================== 3 Checks and filters
    dict(
        id=11, ledger="P561", concept="PY4 dedupe ignoring case", tier="3 - Checks and filters",
        title="Repeats dropped, whatever their case", kind="function",
        func="unique_codes",
        cases=[(["MB-12", "mb-12", "CH-7", "Mb-12"],), (["a", "A"],), ([],), (["X-1", "Y-2"],)],
        prompt=(
            "A scanner reads the same code in different cases. Write a"
            " function `unique_codes(codes)` that keeps the FIRST"
            " spelling of each code and drops later ones that differ"
            " only in case, order otherwise unchanged. A loop with a set"
            " of the lower-cased codes seen so far.\n\n"
            "  unique_codes([\"MB-12\", \"mb-12\", \"CH-7\", \"Mb-12\"]) -> [\"MB-12\", \"CH-7\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def unique_codes(codes):\n"
                  "    seen = set()\n"
                  "    out = []\n"
                  "    for c in codes:\n"
                  "        if c.lower() not in seen:\n"
                  "            seen.add(c.lower())\n"
                  "            out.append(c)\n"
                  "    return out\n"),
        trap=("def unique_codes(codes):\n"
              "    return list(dict.fromkeys(c.lower() for c in codes))\n"),
        note="Lower-casing everything does remove the repeats, but it"
             " also changes the codes that are kept: the trap returns"
             " 'mb-12' where the first spelling was 'MB-12'. The set"
             " remembers the lower-case form for COMPARING while the"
             " output list keeps each code as it first arrived.",
    ),
    dict(
        id=12, ledger="P562", concept="PY3 pair up a flat list", tier="3 - Checks and filters",
        title="A flat list of scans, paired up", kind="function",
        func="pair_up",
        cases=[(["MB-1", "collected", "MB-2", "delivered"],), (["MB-1", "collected", "MB-2"],), ([],), (["a", "b"],)],
        prompt=(
            "A scanner sends one flat list: a code, its status, the next"
            " code, its status, and so on. Write a function `pair_up("
            "items)` that returns a list of (code, status) tuples; a"
            " code left over at the end with no status is dropped. zip"
            " the even positions with the odd ones, each a slice with a"
            " step.\n\n"
            "  pair_up([\"MB-1\", \"collected\", \"MB-2\", \"delivered\"]) -> [(\"MB-1\", \"collected\"), (\"MB-2\", \"delivered\")]\n\n"
            "Return: a list of tuples."
        ),
        solution=("def pair_up(items):\n"
                  "    return list(zip(items[::2], items[1::2]))\n"),
        trap=("def pair_up(items):\n"
              "    return list(zip(items, items[1:]))\n"),
        note="zip(items, items[1:]) pairs every item with its neighbour,"
             " overlapping: the trap returns three pairs for four items,"
             " the middle one ('collected', 'MB-2'). items[::2] is"
             " positions 0, 2, 4 and items[1::2] is 1, 3, 5, so zipping"
             " those gives pairs that do not overlap, and zip stops at"
             " the shorter slice, which drops an unpaired last code.",
    ),
    dict(
        id=13, ledger="P563", concept="PY3 move to the front", tier="3 - Checks and filters",
        title="An urgent parcel moved to the front", kind="function",
        func="to_front",
        cases=[(["MB-1", "CH-2", "WW-3"], "CH-2"), (["MB-1", "CH-2"], "ZZ-9"), ([], "MB-1"), (["MB-1"], "MB-1")],
        prompt=(
            "Write a function `to_front(codes, urgent)` that returns a"
            " new list with the urgent code first and the others in"
            " their original order -- or an unchanged copy if the urgent"
            " code is not in the list at all. A membership test, then"
            " the code plus everything that is not it.\n\n"
            "  to_front([\"MB-1\", \"CH-2\", \"WW-3\"], \"CH-2\") -> [\"CH-2\", \"MB-1\", \"WW-3\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def to_front(codes, urgent):\n"
                  "    if urgent not in codes:\n"
                  "        return codes[:]\n"
                  "    return [urgent] + [c for c in codes if c != urgent]\n"),
        trap=("def to_front(codes, urgent):\n"
              "    return [urgent] + [c for c in codes if c != urgent]\n"),
        note="Without the membership test the trap ADDS a parcel that"
             " was never on the van: asked to move ZZ-9 to the front of a"
             " list that does not hold it, it returns a list that does."
             " The test first, then the rebuild. codes[:] is a copy, so"
             " the caller's list is never the one handed back.",
    ),
    dict(
        id=14, ledger="P564", concept="PY3 strictly increasing", tier="3 - Checks and filters",
        title="Are the weights strictly rising?", kind="function",
        func="rising",
        cases=[([500, 750, 1200],), ([500, 500, 1200],), ([1200, 750],), ([],), ([42],)],
        prompt=(
            "Parcels are stacked lightest on top. Write a function"
            " `rising(weights)` that returns True when each weight is"
            " STRICTLY greater than the one before -- two equal weights"
            " in a row do not count -- and True for a list of one or"
            " none. all() over the neighbouring pairs from zip.\n\n"
            "  rising([500, 750, 1200]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def rising(weights):\n"
                  "    return all(a < b for a, b in zip(weights, weights[1:]))\n"),
        trap=("def rising(weights):\n"
              "    return weights == sorted(weights)\n"),
        note="A list equal to its sorted self is in NON-DECREASING order,"
             " which allows equal neighbours: the trap says True for 500,"
             " 500, 1200. 'Strictly' needs a < between each pair, and"
             " zip(weights, weights[1:]) supplies the pairs. With fewer"
             " than two weights there are no pairs, and all() of nothing"
             " is True.",
    ),
    dict(
        id=15, ledger="P565", concept="PY3 pad a list", tier="3 - Checks and filters",
        title="A trail padded to a fixed length", kind="function",
        func="pad_to",
        cases=[(["collected", "delivered"], 4, "-"), (["a", "b", "c"], 2, "-"), ([], 2, "?"), (["x"], 1, "-")],
        prompt=(
            "A report needs every trail to have at least n entries."
            " Write a function `pad_to(trail, n, filler)` that returns"
            " the trail with the filler added on the end until it is n"
            " long -- and a trail already n long or longer unchanged,"
            " nothing cut off. A list times a number, added on.\n\n"
            "  pad_to([\"collected\", \"delivered\"], 4, \"-\") -> [\"collected\", \"delivered\", \"-\", \"-\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def pad_to(trail, n, filler):\n"
                  "    return trail + [filler] * (n - len(trail))\n"),
        trap=("def pad_to(trail, n, filler):\n"
              "    return (trail + [filler] * n)[:n]\n"),
        note="Padding generously and slicing back to n looks tidy, but"
             " the slice also CUTS a trail that was longer than n: the"
             " trap loses the third entry of a three-entry trail padded"
             " 'to 2'. A list times a negative number is the empty list,"
             " so [filler] * (n - len(trail)) adds exactly what is"
             " missing and nothing when nothing is.",
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
