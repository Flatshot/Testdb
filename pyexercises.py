"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-third Python set, at the easy level of the last three -- no
statistics, no dicts -- in the courier's terms, on tasks the earlier sets
did not cover. Counting and finding: the status before a given one, the
attempts before delivery, parcels that stayed local, the n-th scan from the
end, words across several lines. Labels: grams as a weight label, a route
label that says 'local', a status code as words, an address from its
parts, whether a box fits. Checks and filters: the codes of one depot,
codes sorted by weight, overweight flags, the first and last date, the
depots a list of codes mentions.

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
        id=1, ledger="P491", concept="PY4 item before a value", tier="1 - Counting and finding",
        title="What happened just before the delivery", kind="function",
        func="status_before",
        cases=[(["collected", "departed", "arrived", "out_for_delivery", "delivered"], "delivered"), (["collected", "delivered"], "collected"), (["collected", "departed"], "delivered"), ([], "delivered")],
        prompt=(
            "A parcel's trail is a list of status words in time order."
            " Write a function `status_before(trail, status)` that"
            " returns the status that came right before the FIRST"
            " appearance of the given one, or None when it is missing"
            " or was the first entry.\n\n"
            "  status_before([\"collected\", \"departed\", \"arrived\", \"out_for_delivery\", \"delivered\"], \"delivered\") -> \"out_for_delivery\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def status_before(trail, status):\n"
                  "    if status not in trail:\n"
                  "        return None\n"
                  "    i = trail.index(status)\n"
                  "    if i == 0:\n"
                  "        return None\n"
                  "    return trail[i - 1]\n"),
        trap=("def status_before(trail, status):\n"
              "    return trail[trail.index(status) - 1]\n"),
        note="Two things can go wrong with trail[index - 1]: index()"
             " raises when the status is missing, and when the status is"
             " first, index - 1 is -1, which Python reads as the LAST item"
             " -- so the trap answers 'delivered' for the status before"
             " 'collected', which is backwards. The two checks catch"
             " both.",
    ),
    dict(
        id=2, ledger="P492", concept="PY4 count before a value", tier="1 - Counting and finding",
        title="How many attempts it took", kind="function",
        func="attempts",
        cases=[(["collected", "out_for_delivery", "failed", "out_for_delivery", "delivered"],), (["collected", "out_for_delivery", "delivered"],), (["collected", "out_for_delivery", "failed"],), ([],)],
        prompt=(
            "Write a function `attempts(trail)` that returns how many"
            " 'out_for_delivery' entries come before the first"
            " 'delivered' -- or in the whole trail if the parcel was"
            " never delivered. Cut the list at the delivery with a"
            " slice, then count().\n\n"
            "  attempts([\"collected\", \"out_for_delivery\", \"failed\", \"out_for_delivery\", \"delivered\"]) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def attempts(trail):\n"
                  "    if \"delivered\" in trail:\n"
                  "        trail = trail[:trail.index(\"delivered\")]\n"
                  "    return trail.count(\"out_for_delivery\")\n"),
        trap=("def attempts(trail):\n"
              "    return trail.index(\"delivered\")\n"),
        note="The position of 'delivered' is not the number of attempts:"
             " the trap counts every entry before it, collected and"
             " failed included, and crashes when the parcel was never"
             " delivered. Slicing up to the delivery and counting the"
             " one status answers exactly the question, and a trail with"
             " no 'delivered' is counted whole.",
    ),
    dict(
        id=3, ledger="P493", concept="PY4 zip and compare", tier="1 - Counting and finding",
        title="Parcels that never left their depot", kind="function",
        func="local_count",
        cases=[(["Millbank", "Central Hub", "Westway"], ["Millbank", "Northgate", "Westway"]), (["Millbank", "Central Hub"], ["Central Hub", "Millbank"]), ([], []), (["Hub", "Hub"], ["Hub", "Hub"])],
        prompt=(
            "Two lists line up parcel by parcel: where each was"
            " collected and where it was delivered. Write a function"
            " `local_count(origins, dests)` that returns how many"
            " parcels had the same depot at both ends. zip() walks the"
            " two lists together; a sum of comparisons counts.\n\n"
            "  local_count([\"Millbank\", \"Central Hub\", \"Westway\"], [\"Millbank\", \"Northgate\", \"Westway\"]) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def local_count(origins, dests):\n"
                  "    return sum(a == b for a, b in zip(origins, dests))\n"),
        trap=("def local_count(origins, dests):\n"
              "    return sum(o in dests for o in origins)\n"),
        note="`o in dests` asks whether the origin appears ANYWHERE in"
             " the destinations, not at the same position: two parcels"
             " that swapped depots -- Millbank to Central Hub and Central"
             " Hub to Millbank -- are both counted local by the trap,"
             " when neither stayed put. zip() pairs position with"
             " position, which is what 'the same parcel' means here, and"
             " a bool sums as 1 or 0.",
    ),
    dict(
        id=4, ledger="P494", concept="PY3 nth from the end", tier="1 - Counting and finding",
        title="The second-last scan", kind="function",
        func="from_end",
        cases=[(["collected", "departed", "arrived", "delivered"], 2), (["collected", "delivered"], 1), (["collected"], 2), ([], 1)],
        prompt=(
            "Write a function `from_end(trail, n)` that returns the"
            " n-th entry counting from the end -- 1 for the last, 2"
            " for the one before it -- or None when the trail is too"
            " short. A negative index, behind a length check.\n\n"
            "  from_end([\"collected\", \"departed\", \"arrived\", \"delivered\"], 2) -> \"arrived\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def from_end(trail, n):\n"
                  "    if n > len(trail):\n"
                  "        return None\n"
                  "    return trail[-n]\n"),
        trap=("def from_end(trail, n):\n"
              "    return trail[-n]\n"),
        note="trail[-1] is the last item and trail[-2] the one before, so"
             " trail[-n] is the n-th from the end -- until n is bigger"
             " than the list, when it raises IndexError, which is the"
             " trap's failure on a one-entry trail. One comparison with"
             " len() turns that into None.",
    ),
    dict(
        id=5, ledger="P495", concept="PY3 sum of word counts", tier="1 - Counting and finding",
        title="Words across every line of a label", kind="function",
        func="total_words",
        cases=[(["Flat 2", "14 Harbour Street", "Millbank"],), (["", "  "],), ([],), (["one"],)],
        prompt=(
            "An address label is a list of lines. Write a function"
            " `total_words(lines)` that returns how many words there"
            " are across all the lines. split() with no argument"
            " handles any spacing; sum() over a generator adds the"
            " counts.\n\n"
            "  total_words([\"Flat 2\", \"14 Harbour Street\", \"Millbank\"]) -> 6\n\n"
            "Return: an int."
        ),
        solution=("def total_words(lines):\n"
                  "    return sum(len(line.split()) for line in lines)\n"),
        trap=("def total_words(lines):\n"
              "    return len(lines)\n"),
        note="len(lines) counts the LINES, three for the example where"
             " there are six words. Each line has to be split into words"
             " and the lengths added up; a blank line splits to [] and"
             " contributes 0, and an empty list sums to 0.",
    ),
    # ================================================================ 2 Labels
    dict(
        id=6, ledger="P496", concept="PY3 unit label by threshold", tier="2 - Labels",
        title="Grams or kilograms, whichever reads better", kind="function",
        func="weight_label",
        cases=[(750,), (2500,), (1000,), (30000,)],
        prompt=(
            "Write a function `weight_label(grams)` that returns '750 g'"
            " for anything under a kilogram and '2.5 kg' from a"
            " kilogram up, the kilograms to one decimal. An if on the"
            " threshold; division by 1000 and round(..., 1) for the"
            " heavier case.\n\n"
            "  weight_label(2500) -> \"2.5 kg\"\n\n"
            "Return: a str."
        ),
        solution=("def weight_label(grams):\n"
                  "    if grams < 1000:\n"
                  "        return f\"{grams} g\"\n"
                  "    return f\"{round(grams / 1000, 1)} kg\"\n"),
        trap=("def weight_label(grams):\n"
              "    return f\"{round(grams / 1000, 1)} kg\"\n"),
        note="Everything in kilograms, the trap, labels a letter '0.8"
             " kg', which nobody writes. The threshold picks the unit"
             " and the shape of the number with it: whole grams below,"
             " one decimal of kilograms above, and exactly 1000 g is"
             " '1.0 kg'.",
    ),
    dict(
        id=7, ledger="P497", concept="PY3 conditional f-string", tier="2 - Labels",
        title="A route label that knows when nothing moved", kind="function",
        func="route_label",
        cases=[("Millbank", "Central Hub"), ("Millbank", "Millbank"), ("Westway", "Hillcrest")],
        prompt=(
            "Write a function `route_label(origin, dest)` that returns"
            " 'Millbank -> Central Hub' for a parcel that moved between"
            " depots and 'Millbank (local)' for one delivered from the"
            " depot it was handed in at. A conditional expression"
            " choosing between two f-strings.\n\n"
            "  route_label(\"Millbank\", \"Millbank\") -> \"Millbank (local)\"\n\n"
            "Return: a str."
        ),
        solution=("def route_label(origin, dest):\n"
                  "    return f\"{origin} (local)\" if origin == dest else f\"{origin} -> {dest}\"\n"),
        trap=("def route_label(origin, dest):\n"
              "    return f\"{origin} -> {dest}\"\n"),
        note="'Millbank -> Millbank' is true but unhelpful, and the"
             " question asks for the special case to be named. A"
             " conditional expression -- one value if the test holds,"
             " another if not -- keeps the two labels side by side on"
             " one line.",
    ),
    dict(
        id=8, ledger="P498", concept="PY3 snake case to words", tier="2 - Labels",
        title="A status code as words", kind="function",
        func="status_words",
        cases=[("out_for_delivery",), ("delivered",), ("failed",), ("collected_at_counter",)],
        prompt=(
            "Status codes are written like 'out_for_delivery'. Write a"
            " function `status_words(code)` that returns them as a"
            " phrase with a capital only at the start: 'Out for"
            " delivery'. replace() the underscores, then capitalize().\n\n"
            "  status_words(\"out_for_delivery\") -> \"Out for delivery\"\n\n"
            "Return: a str."
        ),
        solution=("def status_words(code):\n"
                  "    return code.replace(\"_\", \" \").capitalize()\n"),
        trap=("def status_words(code):\n"
              "    return code.replace(\"_\", \" \").title()\n"),
        note="title() capitalises every word -- 'Out For Delivery' --"
             " where the question wants a sentence-style phrase with one"
             " capital; capitalize() upper-cases the first character and"
             " lower-cases the rest. Both are chained after replace(),"
             " which has already turned the underscores into spaces.",
    ),
    dict(
        id=9, ledger="P499", concept="PY3 join the non-empty", tier="2 - Labels",
        title="An address on one line, blanks skipped", kind="function",
        func="address_line",
        cases=[(["Flat 2", "", "14 Harbour Street", "Millbank"],), (["", ""],), (["Westway"],), ([],)],
        prompt=(
            "Address forms arrive with some lines left blank. Write a"
            " function `address_line(parts)` that joins the non-empty"
            " parts with ', ' into one line, skipping the blanks so no"
            " two commas meet. A generator that keeps the truthy parts,"
            " inside join().\n\n"
            "  address_line([\"Flat 2\", \"\", \"14 Harbour Street\", \"Millbank\"]) -> \"Flat 2, 14 Harbour Street, Millbank\"\n\n"
            "Return: a str."
        ),
        solution=("def address_line(parts):\n"
                  "    return \", \".join(p for p in parts if p)\n"),
        trap=("def address_line(parts):\n"
              "    return \", \".join(parts)\n"),
        note="join() puts the separator between EVERY pair, blanks"
             " included, so the trap writes 'Flat 2, , 14 Harbour"
             " Street, Millbank'. Filtering the parts first -- `if p`"
             " keeps the non-empty strings -- means join() only ever"
             " sees real lines, and a list of blanks gives ''.",
    ),
    dict(
        id=10, ledger="P500", concept="PY3 max of several values", tier="2 - Labels",
        title="Will the box fit through the hatch?", kind="function",
        func="fits",
        cases=[(30, 20, 10, 40), (50, 20, 10, 40), (10, 10, 45, 40), (40, 40, 40, 40)],
        prompt=(
            "A parcel fits through the sorting hatch when NONE of its"
            " three sides is longer than the hatch. Write a function"
            " `fits(length, width, height, hatch)` that returns True or"
            " False. max() takes several arguments, so the longest side"
            " is one call.\n\n"
            "  fits(30, 20, 10, 40) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def fits(length, width, height, hatch):\n"
                  "    return max(length, width, height) <= hatch\n"),
        trap=("def fits(length, width, height, hatch):\n"
              "    return length <= hatch and width <= hatch\n"),
        note="Three sides, three tests, and the trap forgets the height:"
             " a 45-centimetre-tall box is waved through a 40-centimetre"
             " hatch. max() of the three sides against the hatch is the"
             " same as testing all three with and, in one comparison;"
             " <= lets a side exactly the hatch's size through, as the"
             " question says.",
    ),
    # ==================================================== 3 Checks and filters
    dict(
        id=11, ledger="P501", concept="PY3 filter by prefix", tier="3 - Checks and filters",
        title="The parcels from one depot", kind="function",
        func="codes_from",
        cases=[(["MB-0012", "CH-0007", "MB-0031", "WW-0002"], "MB"), (["CH-0007"], "MB"), ([], "MB"), (["MB-0012", "XMB-99"], "MB")],
        prompt=(
            "A parcel code starts with its origin depot's two-letter"
            " code and a hyphen: 'MB-0012'. Write a function"
            " `codes_from(codes, depot)` that returns the codes from"
            " that depot, in order. startswith() with the depot code and"
            " the hyphen, in a comprehension.\n\n"
            "  codes_from([\"MB-0012\", \"CH-0007\", \"MB-0031\", \"WW-0002\"], \"MB\") -> [\"MB-0012\", \"MB-0031\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def codes_from(codes, depot):\n"
                  "    return [c for c in codes if c.startswith(depot + \"-\")]\n"),
        trap=("def codes_from(codes, depot):\n"
              "    return [c for c in codes if depot in c]\n"),
        note="`depot in c` finds the letters ANYWHERE in the code, so"
             " the trap keeps 'XMB-99' for depot MB. startswith() tests"
             " the front only, and adding the hyphen to the prefix stops"
             " 'MB' matching a depot 'MBX'. The comprehension keeps the"
             " order the codes came in.",
    ),
    dict(
        id=12, ledger="P502", concept="PY3 sort one list by another", tier="3 - Checks and filters",
        title="Parcel codes, lightest first", kind="function",
        func="by_weight",
        cases=[(["MB-0012", "CH-0007", "WW-0002"], [2500, 750, 1200]), (["A", "B"], [5, 5]), ([], []), (["Z"], [1])],
        prompt=(
            "Two lists line up: parcel codes and their weights. Write a"
            " function `by_weight(codes, weights)` that returns the"
            " codes in order of weight, lightest first, codes alone."
            " zip() the weights with the codes, sorted(), then take the"
            " codes back out.\n\n"
            "  by_weight([\"MB-0012\", \"CH-0007\", \"WW-0002\"], [2500, 750, 1200]) -> [\"CH-0007\", \"WW-0002\", \"MB-0012\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def by_weight(codes, weights):\n"
                  "    return [c for w, c in sorted(zip(weights, codes))]\n"),
        trap=("def by_weight(codes, weights):\n"
              "    return sorted(codes)\n"),
        note="sorted(codes) sorts the codes alphabetically and never"
             " looks at the weights. Zipping the weights FIRST makes"
             " each pair sort by weight, with the code as a tiebreak,"
             " and the comprehension drops the weights again. The same"
             " thing with a key: sorted(codes, key=lambda c:"
             " weights[codes.index(c)]), but the zip is cleaner.",
    ),
    dict(
        id=13, ledger="P503", concept="PY3 list of booleans", tier="3 - Checks and filters",
        title="Which parcels are over the limit", kind="function",
        func="over_limit",
        cases=[([2500, 750, 12000], 10000), ([], 10000), ([10000], 10000), ([15000, 20000], 10000)],
        prompt=(
            "Write a function `over_limit(weights, limit)` that returns"
            " a list of True and False, one per parcel in order, saying"
            " whether it is over the limit. A comprehension whose"
            " expression is the comparison itself.\n\n"
            "  over_limit([2500, 750, 12000], 10000) -> [False, False, True]\n\n"
            "Return: a list of bool."
        ),
        solution=("def over_limit(weights, limit):\n"
                  "    return [w > limit for w in weights]\n"),
        trap=("def over_limit(weights, limit):\n"
              "    return [w for w in weights if w > limit]\n"),
        note="A comprehension with an `if` FILTERS -- it keeps the heavy"
             " weights themselves, [12000] -- while the question wants a"
             " flag for every parcel, which is a comprehension whose"
             " expression is the test: no if, one result per input. A"
             " comparison is already a bool, so no conditional"
             " expression is needed.",
    ),
    dict(
        id=14, ledger="P504", concept="PY3 min and max of dates", tier="3 - Checks and filters",
        title="The first and last collection", kind="function",
        func="date_range",
        cases=[(["2026-03-04", "2025-11-30", "2026-01-15"],), (["2026-06-30"],), ([],), (["2025-01-01", "2025-01-01"],)],
        prompt=(
            "Write a function `date_range(dates)` that returns the"
            " earliest and latest of a list of ISO dates as a tuple, or"
            " None for an empty list. ISO dates compare correctly as"
            " text, so min() and max() do it without parsing.\n\n"
            "  date_range([\"2026-03-04\", \"2025-11-30\", \"2026-01-15\"]) -> (\"2025-11-30\", \"2026-03-04\")\n\n"
            "Return: a tuple of two str, or None."
        ),
        solution=("def date_range(dates):\n"
                  "    if not dates:\n"
                  "        return None\n"
                  "    return min(dates), max(dates)\n"),
        trap=("def date_range(dates):\n"
              "    if not dates:\n"
              "        return None\n"
              "    return dates[0], dates[-1]\n"),
        note="The first and last ITEMS are the first and last dates only"
             " if the list is sorted, and this one is not: the trap"
             " returns March then January. min() and max() compare the"
             " strings, and 'YYYY-MM-DD' puts the biggest unit first, so"
             " text order is date order.",
    ),
    dict(
        id=15, ledger="P505", concept="PY3 derived set sorted", tier="3 - Checks and filters",
        title="Which depots a batch of codes mentions", kind="function",
        func="depots_in",
        cases=[(["MB-0012", "CH-0007", "MB-0031", "WW-0002"],), (["MB-0001", "MB-0002"],), ([],), (["WW-9"],)],
        prompt=(
            "Write a function `depots_in(codes)` that returns the"
            " distinct depot codes -- the part before the hyphen --"
            " mentioned in a list of parcel codes, in alphabetical"
            " order. Split each code at the hyphen, collect the first"
            " parts in a set, sort.\n\n"
            "  depots_in([\"MB-0012\", \"CH-0007\", \"MB-0031\", \"WW-0002\"]) -> [\"CH\", \"MB\", \"WW\"]\n\n"
            "Return: a sorted list of str."
        ),
        solution=("def depots_in(codes):\n"
                  "    return sorted({c.split(\"-\")[0] for c in codes})\n"),
        trap=("def depots_in(codes):\n"
              "    return sorted(c.split(\"-\")[0] for c in codes)\n"),
        note="Without the set, the trap lists MB twice. The curly"
             " brackets make a set comprehension, which keeps one of"
             " each value, and sorted() turns it back into the ordered"
             " list asked for. split('-')[0] is the text before the"
             " first hyphen.",
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
