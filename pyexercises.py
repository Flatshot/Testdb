"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-fifth Python set, at the easy level of the last five -- no
statistics, no dicts -- in the courier's terms, on tasks the earlier sets
did not cover. Counting and finding: a search that starts part-way along,
the n-th heaviest, codes numbered above a line, dates before a cut-off,
whether any trail ends lost. Labels: an invoice number from its parts, a
summary with a plural and a price, a text bar, a CSV line with quoting, a
name masked to initials. Checks and filters: the codes that are well
formed, services in priority order, a trail split at a status, prefixes
stripped, the latest delivery date from paired lists.

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
        id=1, ledger="P521", concept="PY3 index with a start", tier="1 - Counting and finding",
        title="The next attempt after a point in the trail", kind="function",
        func="next_after",
        cases=[(["out_for_delivery", "failed", "out_for_delivery", "delivered"], "out_for_delivery", 1), (["out_for_delivery", "failed"], "out_for_delivery", 1), (["collected"], "collected", 0), ([], "collected", 0)],
        prompt=(
            "Write a function `next_after(trail, status, start)` that"
            " returns the position of the first occurrence of the"
            " status at or after position `start`, or -1 if there is"
            " none from there on. index() takes a second argument that"
            " says where to begin looking; test with `in` on a slice"
            " first.\n\n"
            "  next_after([\"out_for_delivery\", \"failed\", \"out_for_delivery\", \"delivered\"], \"out_for_delivery\", 1) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def next_after(trail, status, start):\n"
                  "    if status not in trail[start:]:\n"
                  "        return -1\n"
                  "    return trail.index(status, start)\n"),
        trap=("def next_after(trail, status, start):\n"
              "    if status not in trail:\n"
              "        return -1\n"
              "    return trail.index(status)\n"),
        note="index() without a start finds the FIRST occurrence in the"
             " whole list, which may be before the point you asked from:"
             " the trap answers 0 for the example, where the attempt"
             " after position 1 is at 2. index(value, start) begins its"
             " search at start, and testing membership on the same"
             " slice, trail[start:], keeps the two in step.",
    ),
    dict(
        id=2, ledger="P522", concept="PY3 nth largest", tier="1 - Counting and finding",
        title="The second-heaviest parcel", kind="function",
        func="nth_heaviest",
        cases=[([2500, 7500, 1200, 3000], 2), ([2500, 7500], 1), ([2500], 2), ([], 1)],
        prompt=(
            "Write a function `nth_heaviest(weights, n)` that returns"
            " the n-th largest weight -- 1 for the heaviest, 2 for the"
            " next -- or None when there are fewer than n weights."
            " sorted() largest first, then an index, behind a length"
            " check.\n\n"
            "  nth_heaviest([2500, 7500, 1200, 3000], 2) -> 3000\n\n"
            "Return: an int, or None."
        ),
        solution=("def nth_heaviest(weights, n):\n"
                  "    if n > len(weights):\n"
                  "        return None\n"
                  "    return sorted(weights, reverse=True)[n - 1]\n"),
        trap=("def nth_heaviest(weights, n):\n"
              "    if n > len(weights):\n"
              "        return None\n"
              "    return sorted(weights, reverse=True)[n]\n"),
        note="The heaviest is at index 0 of a list sorted largest-first,"
             " so the n-th is at n - 1: the trap's [n] returns the"
             " third-heaviest for n = 2 and raises IndexError for the"
             " last one. The length check turns 'not enough weights'"
             " into None before any indexing happens.",
    ),
    dict(
        id=3, ledger="P523", concept="PY3 filter by a converted part", tier="1 - Counting and finding",
        title="Codes numbered above a line", kind="function",
        func="numbered_above",
        cases=[(["MB-0012", "CH-0100", "WW-0099"], 50), (["MB-0012"], 50), ([], 1), (["A-7", "B-70"], 7)],
        prompt=(
            "A parcel code's number follows the hyphen, zero-padded."
            " Write a function `numbered_above(codes, n)` that returns"
            " the codes whose number is greater than n, in order. Split"
            " at the hyphen and convert the part after it inside the"
            " comprehension's test.\n\n"
            "  numbered_above([\"MB-0012\", \"CH-0100\", \"WW-0099\"], 50) -> [\"CH-0100\", \"WW-0099\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def numbered_above(codes, n):\n"
                  "    return [c for c in codes if int(c.split(\"-\")[1]) > n]\n"),
        trap=("def numbered_above(codes, n):\n"
              "    return [c for c in codes if c.split(\"-\")[1] > str(n)]\n"),
        note="Comparing the text '0099' with the text '50' is a"
             " character-by-character comparison, where '0' comes before"
             " '5', so the trap says 0099 is NOT above 50 and 7 IS above"
             " 70. Converting to int before the comparison makes it"
             " numeric; the zero padding is no trouble to int().",
    ),
    dict(
        id=4, ledger="P524", concept="PY3 count by text date", tier="1 - Counting and finding",
        title="Deliveries before the cut-off", kind="function",
        func="before",
        cases=[(["2026-03-04", "2025-11-30", "2026-01-15"], "2026-01-01"), (["2026-01-01"], "2026-01-01"), ([], "2026-01-01"), (["2025-12-31", "2025-12-31"], "2026-01-01")],
        prompt=(
            "Write a function `before(dates, cutoff)` that returns how"
            " many of the ISO dates fall strictly before the cut-off"
            " date. ISO dates compare correctly as text, so a sum of"
            " comparisons does it with no parsing.\n\n"
            "  before([\"2026-03-04\", \"2025-11-30\", \"2026-01-15\"], \"2026-01-01\") -> 1\n\n"
            "Return: an int."
        ),
        solution=("def before(dates, cutoff):\n"
                  "    return sum(d < cutoff for d in dates)\n"),
        trap=("def before(dates, cutoff):\n"
              "    return sum(d <= cutoff for d in dates)\n"),
        note="'Strictly before' excludes the cut-off day itself: a"
             " delivery dated 2026-01-01 is not before 2026-01-01, and"
             " the trap's <= counts it. Text comparison works because"
             " 'YYYY-MM-DD' puts the biggest unit first; a bool sums as"
             " 1 or 0, so sum() of the comparisons is the count.",
    ),
    dict(
        id=5, ledger="P525", concept="PY4 any over last items", tier="1 - Counting and finding",
        title="Is anything in the batch lost?", kind="function",
        func="any_lost",
        cases=[([["collected", "delivered"], ["collected", "out_for_delivery", "failed"]],), ([["collected", "failed", "delivered"]],), ([],), ([[], ["collected"]],)],
        prompt=(
            "A parcel is lost when its trail ENDS on 'failed'. Write a"
            " function `any_lost(trails)` that returns True when any"
            " trail in the list ends that way and False otherwise,"
            " empty trails ignored. any() over a generator that tests"
            " each trail's last entry behind a non-empty check.\n\n"
            "  any_lost([[\"collected\", \"delivered\"], [\"collected\", \"out_for_delivery\", \"failed\"]]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def any_lost(trails):\n"
                  "    return any(t and t[-1] == \"failed\" for t in trails)\n"),
        trap=("def any_lost(trails):\n"
              "    return any(\"failed\" in t for t in trails)\n"),
        note="A failure in the MIDDLE of a trail is a parcel that came"
             " back and was delivered later, not a lost one: the trap"
             " says True for a trail that ends 'delivered'. Testing the"
             " last entry is the question's definition, and `t and` in"
             " front of t[-1] keeps an empty trail from raising. any()"
             " of nothing is False.",
    ),
    # ================================================================ 2 Labels
    dict(
        id=6, ledger="P526", concept="PY3 padded id in a label", tier="2 - Labels",
        title="An invoice number from its parts", kind="function",
        func="invoice_number",
        cases=[(4, "2026-05"), (123, "2025-12"), (8, "2026-01")],
        prompt=(
            "Invoices are numbered 'INV-202605-0004': the period with"
            " its hyphen removed, then the customer id padded with zeros"
            " to four digits. Write a function `invoice_number("
            "customer_id, period)` that builds it. replace() for the"
            " period and a format spec for the padding.\n\n"
            "  invoice_number(4, \"2026-05\") -> \"INV-202605-0004\"\n\n"
            "Return: a str."
        ),
        solution=("def invoice_number(customer_id, period):\n"
                  "    return f\"INV-{period.replace('-', '')}-{customer_id:04d}\"\n"),
        trap=("def invoice_number(customer_id, period):\n"
              "    return f\"INV-{period}-{customer_id}\"\n"),
        note="The trap keeps the period's hyphen and leaves the id"
             " unpadded: 'INV-2026-05-4', which no longer lines up or"
             " sorts. :04d pads an int with zeros to four places, and"
             " replace('-', '') takes the hyphen out of the period; both"
             " happen inside the braces where the values are used.",
    ),
    dict(
        id=7, ledger="P527", concept="PY3 plural and money together", tier="2 - Labels",
        title="A one-line summary of the month", kind="function",
        func="month_summary",
        cases=[(18, 14820), (1, 350), (0, 0), (2, 1005)],
        prompt=(
            "Write a function `month_summary(parcels, cents)` that"
            " returns '18 parcels, $148.20': the count with 'parcel'"
            " made plural unless it is exactly 1, then the money as"
            " dollars with two digits of cents. An if for the plural,"
            " // and % with a :02d for the money.\n\n"
            "  month_summary(18, 14820) -> \"18 parcels, $148.20\"\n\n"
            "Return: a str."
        ),
        solution=("def month_summary(parcels, cents):\n"
                  "    word = \"parcel\" if parcels == 1 else \"parcels\"\n"
                  "    return f\"{parcels} {word}, ${cents // 100}.{cents % 100:02d}\"\n"),
        trap=("def month_summary(parcels, cents):\n"
              "    return f\"{parcels} parcels, ${cents / 100}\"\n"),
        note="Two things in the trap: '1 parcels', and cents / 100 as a"
             " float prints 10.05 as '10.05' but 350 as '3.5' and 0 as"
             " '0.0'. The plural is a one-word choice on == 1, and the"
             " money is whole dollars from // 100 with the remainder"
             " from % 100 padded to two digits.",
    ),
    dict(
        id=8, ledger="P528", concept="PY3 text bar", tier="2 - Labels",
        title="A percentage as a bar of hashes", kind="function",
        func="bar",
        cases=[(45, 20), (100, 10), (0, 10), (33, 30)],
        prompt=(
            "Write a function `bar(pct, width)` that returns a bar of"
            " '#' characters whose length is the percentage of the"
            " width, rounded to the nearest whole character, padded"
            " with '.' to the full width: bar(45, 20) is nine hashes"
            " and eleven dots. round(), then string multiplication for"
            " each part.\n\n"
            "  bar(45, 20) -> \"#########...........\"\n\n"
            "Return: a str."
        ),
        solution=("def bar(pct, width):\n"
                  "    filled = round(pct / 100 * width)\n"
                  "    return \"#\" * filled + \".\" * (width - filled)\n"),
        trap=("def bar(pct, width):\n"
              "    filled = pct // 100 * width\n"
              "    return \"#\" * filled + \".\" * (width - filled)\n"),
        note="pct // 100 is integer division: 0 for anything under 100,"
             " so the trap's bar is empty for 45 per cent and full only"
             " at 100. pct / 100 * width is the filled length as a"
             " float, round() makes it a whole number of characters, and"
             " the dots are whatever width is left.",
    ),
    dict(
        id=9, ledger="P529", concept="PY3 join with conditional quoting", tier="2 - Labels",
        title="An address as a CSV line", kind="function",
        func="csv_line",
        cases=[(["Flat 2, 14 Harbour Street", "Millbank", "NG1"],), (["Westway"],), ([],), (["a,b", "c,d"],)],
        prompt=(
            "Write a function `csv_line(fields)` that joins the fields"
            " with commas, wrapping in double quotes any field that"
            " itself contains a comma, so the line can be read back."
            " A comprehension with a conditional expression, inside"
            " join().\n\n"
            "  csv_line([\"Flat 2, 14 Harbour Street\", \"Millbank\", \"NG1\"]) -> '\"Flat 2, 14 Harbour Street\",Millbank,NG1'\n\n"
            "Return: a str."
        ),
        solution=("def csv_line(fields):\n"
                  "    return \",\".join(f'\"{f}\"' if \",\" in f else f for f in fields)\n"),
        trap=("def csv_line(fields):\n"
              "    return \",\".join(fields)\n"),
        note="A comma inside a field is indistinguishable from the"
             " separator once joined: the trap's line reads back as four"
             " fields, not three. Quoting the fields that contain a"
             " comma is what CSV does about it, and a conditional"
             " expression inside the generator quotes only those. The"
             " outer quotes are single so the double quotes can go"
             " inside.",
    ),
    dict(
        id=10, ledger="P530", concept="PY3 mask each word", tier="2 - Labels",
        title="A name reduced to initials and stars", kind="function",
        func="mask_name",
        cases=[("Hamid Uddin",), ("Ana de la Cruz",), ("Cher",), ("",)],
        prompt=(
            "For a screen that must not show a full name, write a"
            " function `mask_name(name)` that keeps the first letter of"
            " each word and replaces the rest with stars, one per"
            " letter: 'H**** U****'. A comprehension over split(),"
            " joined with spaces.\n\n"
            "  mask_name(\"Hamid Uddin\") -> \"H**** U****\"\n\n"
            "Return: a str."
        ),
        solution=("def mask_name(name):\n"
                  "    return \" \".join(w[0] + \"*\" * (len(w) - 1) for w in name.split())\n"),
        trap=("def mask_name(name):\n"
              "    return \" \".join(w[0] + \"****\" for w in name.split())\n"),
        note="A fixed four stars gives away nothing about the length"
             " only by accident: 'de' becomes 'd****' and 'Cher' loses"
             " its length too. len(w) - 1 stars keeps each word's length."
             " split() with no argument handles the empty string -- no"
             " words, so join() returns '' -- and w[0] is always safe"
             " because split() never yields an empty word.",
    ),
    # ==================================================== 3 Checks and filters
    dict(
        id=11, ledger="P531", concept="PY3 filter by a format test", tier="3 - Checks and filters",
        title="Only the codes that are well formed", kind="function",
        func="well_formed",
        cases=[(["MB-0012", "CH0007", "WW-00A2", "HC-7"],), ([],), (["-12", "MB-"],), (["ab-12"],)],
        prompt=(
            "A well-formed code is letters, a hyphen, then digits:"
            " 'MB-0012', 'HC-7'. Write a function `well_formed(codes)`"
            " that keeps only the codes that have exactly one hyphen"
            " with letters before it and digits after it. split('-')"
            " into two parts, then isalpha() and isdigit() on them.\n\n"
            "  well_formed([\"MB-0012\", \"CH0007\", \"WW-00A2\", \"HC-7\"]) -> [\"MB-0012\", \"HC-7\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def well_formed(codes):\n"
                  "    out = []\n"
                  "    for c in codes:\n"
                  "        parts = c.split(\"-\")\n"
                  "        if len(parts) == 2 and parts[0].isalpha() and parts[1].isdigit():\n"
                  "            out.append(c)\n"
                  "    return out\n"),
        trap=("def well_formed(codes):\n"
              "    return [c for c in codes if \"-\" in c]\n"),
        note="A hyphen alone is not a format: the trap keeps 'WW-00A2',"
             " '-12' and 'MB-'. Splitting gives the two parts to test"
             " separately, and the length check first makes parts[1]"
             " safe to read. isalpha() and isdigit() are both False for"
             " an empty string, so '-12' and 'MB-' fail on their own;"
             " 'ab-12' passes, since the question says letters, not"
             " capitals.",
    ),
    dict(
        id=12, ledger="P532", concept="PY3 sort by a custom order", tier="3 - Checks and filters",
        title="Services in priority order", kind="function",
        func="by_priority",
        cases=[(["economy", "express", "standard", "express"],), (["standard"],), ([],), (["economy", "economy"],)],
        prompt=(
            "Parcels are loaded express first, then standard, then"
            " economy. Write a function `by_priority(services)` that"
            " returns the services sorted into that order, repeats"
            " kept. A list of the three names in priority order, and"
            " sorted() with its index() as the key.\n\n"
            "  by_priority([\"economy\", \"express\", \"standard\", \"express\"]) -> [\"express\", \"express\", \"standard\", \"economy\"]\n\n"
            "Return: a list of str."
        ),
        solution=("ORDER = [\"express\", \"standard\", \"economy\"]\n\n"
                  "def by_priority(services):\n"
                  "    return sorted(services, key=ORDER.index)\n"),
        trap=("def by_priority(services):\n"
              "    return sorted(services)\n"),
        note="Alphabetical order puts economy first, which is the"
             " opposite of the loading order: the trap unloads the vans"
             " backwards. A key function maps each service to its"
             " position in the priority list, and sorted() orders by"
             " those positions. ORDER.index is already a function of one"
             " argument, so no lambda is needed.",
    ),
    dict(
        id=13, ledger="P533", concept="PY3 split a list at a value", tier="3 - Checks and filters",
        title="The trail before and after arrival", kind="function",
        func="split_at",
        cases=[(["collected", "departed", "arrived", "out_for_delivery", "delivered"], "arrived"), (["collected", "delivered"], "arrived"), (["arrived"], "arrived"), ([], "arrived")],
        prompt=(
            "Write a function `split_at(trail, status)` that returns"
            " two lists as a tuple: the entries before the status's"
            " first appearance, and the entries after it -- the status"
            " itself in neither. When the status is missing, the first"
            " list is the whole trail and the second is empty. `in`,"
            " index() and two slices.\n\n"
            "  split_at([\"collected\", \"departed\", \"arrived\", \"out_for_delivery\", \"delivered\"], \"arrived\") -> ([\"collected\", \"departed\"], [\"out_for_delivery\", \"delivered\"])\n\n"
            "Return: a tuple of two lists."
        ),
        solution=("def split_at(trail, status):\n"
                  "    if status not in trail:\n"
                  "        return trail[:], []\n"
                  "    i = trail.index(status)\n"
                  "    return trail[:i], trail[i + 1:]\n"),
        trap=("def split_at(trail, status):\n"
              "    i = trail.index(status)\n"
              "    return trail[:i], trail[i:]\n"),
        note="Two slips in the trap: index() raises when the status is"
             " missing, and trail[i:] starts AT the status, so it ends up"
             " in the second list. The membership test handles the"
             " missing case, and i + 1 leaves the status out. Returning"
             " `a, b` makes a tuple, which is what the question asks for.",
    ),
    dict(
        id=14, ledger="P534", concept="PY3 removeprefix over a list", tier="3 - Checks and filters",
        title="Codes with the depot stripped off", kind="function",
        func="strip_depot",
        cases=[(["MB-0012", "MB-0031", "CH-0007"], "MB-"), (["CH-0007"], "MB-"), ([], "MB-"), (["MB-MB-1"], "MB-")],
        prompt=(
            "Write a function `strip_depot(codes, prefix)` that returns"
            " each code with the prefix removed from its FRONT if it is"
            " there, and unchanged otherwise. str.removeprefix() does"
            " exactly that for one string; a comprehension applies it"
            " to all.\n\n"
            "  strip_depot([\"MB-0012\", \"MB-0031\", \"CH-0007\"], \"MB-\") -> [\"0012\", \"0031\", \"CH-0007\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def strip_depot(codes, prefix):\n"
                  "    return [c.removeprefix(prefix) for c in codes]\n"),
        trap=("def strip_depot(codes, prefix):\n"
              "    return [c.replace(prefix, \"\") for c in codes]\n"),
        note="replace() removes the prefix EVERYWHERE in the code, so"
             " the trap turns 'MB-MB-1' into '1' where only the front"
             " should go, and it would strip a depot code that appears"
             " in the middle of a longer id. removeprefix() takes it off"
             " the front only, once, and leaves a code that does not"
             " start with it alone.",
    ),
    dict(
        id=15, ledger="P535", concept="PY3 max over a filtered zip", tier="3 - Checks and filters",
        title="The latest delivery in the batch", kind="function",
        func="latest_delivery",
        cases=[(["2026-03-04", "2026-03-06", "2026-03-05"], ["delivered", "failed", "delivered"]), (["2026-01-01"], ["failed"]), ([], []), (["2025-12-31", "2026-01-01"], ["delivered", "delivered"])],
        prompt=(
            "Two lists line up scan by scan: the date and the status."
            " Write a function `latest_delivery(dates, statuses)` that"
            " returns the most recent date among the scans whose status"
            " is 'delivered', or None if there is none. zip() the lists,"
            " keep the delivered dates, and max() with a default.\n\n"
            "  latest_delivery([\"2026-03-04\", \"2026-03-06\", \"2026-03-05\"], [\"delivered\", \"failed\", \"delivered\"]) -> \"2026-03-05\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def latest_delivery(dates, statuses):\n"
                  "    return max((d for d, s in zip(dates, statuses) if s == \"delivered\"), default=None)\n"),
        trap=("def latest_delivery(dates, statuses):\n"
              "    return max(dates, default=None)\n"),
        note="max(dates) is the latest scan of ANY kind -- the trap"
             " returns the failed attempt of 6 March. Filtering the"
             " zipped pairs on the status first leaves only the"
             " delivery dates, and default=None covers a batch with no"
             " delivery, where max() would otherwise raise. ISO dates"
             " compare as text, so no parsing is needed.",
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
