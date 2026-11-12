"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-sixth Python set, at the easy level of the last six -- no
statistics, no dicts -- in the courier's terms, on tasks the earlier sets
did not cover. Counting and finding: a parcel's rank by weight, the first
place two lists disagree, the room left in a van, trails that mention a
status, whether a batch is all from one depot. Labels: a delivery slot
from an hour, the time part of a timestamp, a ratio in lowest terms, a
three-line label, early or late in words. Checks and filters: the trails
not lost, codes sorted by depot then number, a repeat that differs only in
case, codes split into pairs, whether codes are in numeric order.

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
        id=1, ledger="P536", concept="PY3 rank by counting heavier", tier="1 - Counting and finding",
        title="Where a parcel ranks by weight", kind="function",
        func="weight_rank",
        cases=[([2500, 7500, 1200, 3000], 3000), ([2500, 7500, 1200, 3000], 7500), ([500, 500, 500], 500), ([], 100)],
        prompt=(
            "Write a function `weight_rank(weights, w)` that returns the"
            " rank of weight w among the weights, 1 for the heaviest: one"
            " more than the number of weights strictly heavier than w."
            " A sum of comparisons, plus one.\n\n"
            "  weight_rank([2500, 7500, 1200, 3000], 3000) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def weight_rank(weights, w):\n"
                  "    return sum(x > w for x in weights) + 1\n"),
        trap=("def weight_rank(weights, w):\n"
              "    return sorted(weights, reverse=True).index(w) + 1\n"),
        note="index() finds w in the sorted list, which works only when w"
             " is actually in it -- the trap raises ValueError for a"
             " weight that is not -- and sorting is more work than"
             " counting. Counting the heavier weights ranks any w, present"
             " or not, and equal weights share a rank, as they should.",
    ),
    dict(
        id=2, ledger="P537", concept="PY4 first mismatch with zip", tier="1 - Counting and finding",
        title="Where the manifest and the scans first disagree", kind="function",
        func="first_mismatch",
        cases=[(["MB-1", "MB-2", "MB-3"], ["MB-1", "MB-9", "MB-3"]), (["MB-1", "MB-2"], ["MB-1", "MB-2"]), ([], []), (["A", "B"], ["A", "B", "C"]), (["A", "B", "C"], ["A", "B"])],
        prompt=(
            "The manifest lists the codes a van should carry; the scans"
            " list what was actually loaded, in order. Write a function"
            " `first_mismatch(expected, actual)` that returns the"
            " position of the first place the two lists differ, or -1"
            " when they agree as far as the shorter one goes. enumerate"
            " over zip; return inside the loop, -1 after it.\n\n"
            "  first_mismatch([\"MB-1\", \"MB-2\", \"MB-3\"], [\"MB-1\", \"MB-9\", \"MB-3\"]) -> 1\n\n"
            "Return: an int."
        ),
        solution=("def first_mismatch(expected, actual):\n"
                  "    for i, (a, b) in enumerate(zip(expected, actual)):\n"
                  "        if a != b:\n"
                  "            return i\n"
                  "    return -1\n"),
        trap=("def first_mismatch(expected, actual):\n"
              "    for i in range(len(expected)):\n"
              "        if expected[i] != actual[i]:\n"
              "            return i\n"
              "    return -1\n"),
        note="Indexing both lists up to the length of the first raises"
             " IndexError when the second is shorter; zip stops at the"
             " shorter list and never reaches past either end. enumerate"
             " supplies the position, and the tuple in the loop header"
             " unpacks the zipped pair. The question says lists that"
             " agree as far as they go are not a mismatch, so a longer"
             " actual list is -1.",
    ),
    dict(
        id=3, ledger="P538", concept="PY3 capacity minus a sum", tier="1 - Counting and finding",
        title="Room left in the van", kind="function",
        func="room_left",
        cases=[(50000, [12000, 7500, 3000]), (50000, []), (50000, [30000, 25000]), (0, [1])],
        prompt=(
            "A van takes a fixed weight. Write a function `room_left("
            "capacity, weights)` that returns how much weight can still"
            " be loaded after the listed parcels -- which may be"
            " negative if the van is already over. The capacity minus"
            " the sum.\n\n"
            "  room_left(50000, [12000, 7500, 3000]) -> 27500\n\n"
            "Return: an int."
        ),
        solution=("def room_left(capacity, weights):\n"
                  "    return capacity - sum(weights)\n"),
        trap=("def room_left(capacity, weights):\n"
              "    return max(0, capacity - sum(weights))\n"),
        note="The question says the answer may be negative, because an"
             " overloaded van is information: -5000 says how much to take"
             " off. The trap clamps at 0 and hides the overload. sum() of"
             " an empty list is 0, so an empty van has its whole capacity"
             " left.",
    ),
    dict(
        id=4, ledger="P539", concept="PY4 membership over nested lists", tier="1 - Counting and finding",
        title="How many trails had a failure anywhere", kind="function",
        func="trails_with",
        cases=[([["collected", "failed", "delivered"], ["collected", "delivered"], ["failed"]], "failed"), ([], "failed"), ([["collected"]], "failed"), ([["failed", "failed"]], "failed")],
        prompt=(
            "Write a function `trails_with(trails, status)` that returns"
            " how many of the trails contain the status at least once,"
            " wherever it appears. A sum over the trails of `status in"
            " trail`.\n\n"
            "  trails_with([[\"collected\", \"failed\", \"delivered\"], [\"collected\", \"delivered\"], [\"failed\"]], \"failed\") -> 2\n\n"
            "Return: an int."
        ),
        solution=("def trails_with(trails, status):\n"
                  "    return sum(status in t for t in trails)\n"),
        trap=("def trails_with(trails, status):\n"
              "    return sum(t.count(status) for t in trails)\n"),
        note="count() adds up every occurrence, so a trail with two"
             " failures counts twice and the trap answers 2 for a single"
             " trail. `status in t` is True or False once per trail, and"
             " a sum of bools is a count of trails. The question is about"
             " trails, not failures.",
    ),
    dict(
        id=5, ledger="P540", concept="PY3 all share a derived value", tier="1 - Counting and finding",
        title="Is the whole batch from one depot?", kind="function",
        func="one_depot",
        cases=[(["MB-0012", "MB-0031", "MB-0007"],), (["MB-0012", "CH-0007"],), (["WW-1"],), ([],), (["CH-1", "CHB-2"],)],
        prompt=(
            "A parcel code starts with its depot code and a hyphen."
            " Write a function `one_depot(codes)` that returns True"
            " when every code in the batch has the same depot code, and"
            " True for an empty batch. Pull the depot codes out, then"
            " test how many DIFFERENT ones there are.\n\n"
            "  one_depot([\"MB-0012\", \"MB-0031\", \"MB-0007\"]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def one_depot(codes):\n"
                  "    return len({c.split(\"-\")[0] for c in codes}) <= 1\n"),
        trap=("def one_depot(codes):\n"
              "    return len({c[:2] for c in codes}) <= 1\n"),
        note="Slicing two characters assumes every depot code is two"
             " letters; split('-') takes whatever is before the hyphen,"
             " so a three-letter depot is handled too. A set of the depot"
             " codes has one member when they all agree and none for an"
             " empty batch, so <= 1 answers both cases.",
    ),
    # ================================================================ 2 Labels
    dict(
        id=6, ledger="P541", concept="PY3 bucket to a slot label", tier="2 - Labels",
        title="The delivery slot for an hour", kind="function",
        func="slot",
        cases=[(9,), (12,), (15,), (23,), (0,)],
        prompt=(
            "Deliveries are promised in four-hour slots: 08:00-12:00,"
            " 12:00-16:00, 16:00-20:00 and so on, round the clock. Write"
            " a function `slot(hour)` that returns the slot label for"
            " an hour from 0 to 23, both ends zero-padded. Integer"
            " division by 4 and back finds the slot's start; a format"
            " spec pads.\n\n"
            "  slot(9) -> \"08:00-12:00\"\n\n"
            "Return: a str."
        ),
        solution=("def slot(hour):\n"
                  "    start = hour // 4 * 4\n"
                  "    return f\"{start:02d}:00-{start + 4:02d}:00\"\n"),
        trap=("def slot(hour):\n"
              "    start = hour // 4 * 4\n"
              "    return f\"{start}:00-{start + 4}:00\"\n"),
        note="hour // 4 * 4 rounds down to a multiple of four, which is"
             " the slot's start; add 4 for its end. The trap forgets the"
             " padding and writes '8:00-12:00' and '0:00-4:00', which is"
             " not how a clock looks. The last slot runs 20:00-24:00,"
             " which the arithmetic gives for free.",
    ),
    dict(
        id=7, ledger="P542", concept="PY3 slice of a timestamp", tier="2 - Labels",
        title="Just the time of a scan", kind="function",
        func="time_of",
        cases=[("2026-03-04 08:05",), ("2025-12-31 23:59",), ("2026-01-01 00:00",)],
        prompt=(
            "Scans are stamped 'YYYY-MM-DD HH:MM'. Write a function"
            " `time_of(stamp)` that returns just the 'HH:MM' part. The"
            " format is fixed, so a slice does it.\n\n"
            "  time_of(\"2026-03-04 08:05\") -> \"08:05\"\n\n"
            "Return: a str."
        ),
        solution=("def time_of(stamp):\n"
                  "    return stamp[11:]\n"),
        trap=("def time_of(stamp):\n"
              "    return stamp[10:]\n"),
        note="Positions start at 0: the date is ten characters, the space"
             " is at position 10, and the time starts at 11. The trap is"
             " one short and returns ' 08:05' with the space on the"
             " front. stamp.split()[1] is another way, and it does not"
             " depend on counting; either is fine for a fixed format.",
    ),
    dict(
        id=8, ledger="P543", concept="PY3 ratio in lowest terms", tier="2 - Labels",
        title="Parcels per courier, as a ratio", kind="function",
        func="ratio",
        cases=[(24000, 60), (10, 4), (7, 7), (5, 3)],
        prompt=(
            "Write a function `ratio(a, b)` that returns 'a:b' with both"
            " numbers divided by their greatest common divisor, so"
            " ratio(24000, 60) is '400:1'. math.gcd() finds the divisor;"
            " write `import math` at the top.\n\n"
            "  ratio(24000, 60) -> \"400:1\"\n\n"
            "Return: a str."
        ),
        solution=("import math\n\n"
                  "def ratio(a, b):\n"
                  "    g = math.gcd(a, b)\n"
                  "    return f\"{a // g}:{b // g}\"\n"),
        trap=("def ratio(a, b):\n"
              "    return f\"{a}:{b}\"\n"),
        note="A ratio in lowest terms divides both sides by the biggest"
             " number that goes into both, which is the GCD; the trap"
             " writes '24000:60' and '10:4'. // keeps the parts as ints"
             " so they print without a decimal point. Two equal numbers"
             " reduce to '1:1'.",
    ),
    dict(
        id=9, ledger="P544", concept="PY3 multi-line f-string", tier="2 - Labels",
        title="A three-line address label", kind="function",
        func="label",
        cases=[("MB-0012", "Hamid Uddin", "Millbank"), ("CH-7", "Rosa", "Central Hub")],
        prompt=(
            "Write a function `label(code, name, town)` that returns a"
            " three-line label: the code on the first line, the name on"
            " the second, the town in capitals on the third, the lines"
            " separated by newline characters and nothing after the last."
            "\n\n"
            "  label(\"MB-0012\", \"Hamid Uddin\", \"Millbank\") -> \"MB-0012\\nHamid Uddin\\nMILLBANK\"\n\n"
            "Return: a str."
        ),
        solution=("def label(code, name, town):\n"
                  "    return f\"{code}\\n{name}\\n{town.upper()}\"\n"),
        trap=("def label(code, name, town):\n"
              "    return f\"{code}\\n{name}\\n{town.upper()}\\n\"\n"),
        note="'\\n' inside a string is one newline character, and the"
             " question wants two of them, between the lines, with none"
             " at the end: the trap's trailing newline makes a different"
             " string, which the grader sees. print() would show the two"
             " identically, which is exactly why the comparison is on the"
             " value and not on what prints.",
    ),
    dict(
        id=10, ledger="P545", concept="PY3 signed difference in words", tier="2 - Labels",
        title="Early, late, or on time", kind="function",
        func="timing",
        cases=[(3, 5), (5, 3), (4, 4), (0, 1)],
        prompt=(
            "A parcel was promised in one number of days and arrived in"
            " another. Write a function `timing(promised, actual)` that"
            " returns 'on time' when they match, '2 days late' when it"
            " took longer, and '2 days early' when it took less -- with"
            " 'day' for exactly one. Compute the difference, then an"
            " if/elif/else.\n\n"
            "  timing(3, 5) -> \"2 days late\"\n\n"
            "Return: a str."
        ),
        solution=("def timing(promised, actual):\n"
                  "    diff = actual - promised\n"
                  "    if diff == 0:\n"
                  "        return \"on time\"\n"
                  "    n = abs(diff)\n"
                  "    unit = \"day\" if n == 1 else \"days\"\n"
                  "    return f\"{n} {unit} {'late' if diff > 0 else 'early'}\"\n"),
        trap=("def timing(promised, actual):\n"
              "    diff = actual - promised\n"
              "    if diff == 0:\n"
              "        return \"on time\"\n"
              "    return f\"{diff} days {'late' if diff > 0 else 'early'}\"\n"),
        note="The sign says which word to use, and once the word is"
             " chosen the number should be positive: the trap writes '-2"
             " days early'. abs() strips the sign, and the singular is"
             " its own small case. Three outcomes, three branches, and"
             " the difference computed once at the top.",
    ),
    # ==================================================== 3 Checks and filters
    dict(
        id=11, ledger="P546", concept="PY4 filter nested lists by last item", tier="3 - Checks and filters",
        title="The trails that were not lost", kind="function",
        func="not_lost",
        cases=[([["collected", "delivered"], ["collected", "failed"], ["collected"]],), ([],), ([["failed"]],), ([[], ["delivered"]],), ([["collected", "failed", "delivered"]],)],
        prompt=(
            "A trail is lost when it ENDS on 'failed'. Write a function"
            " `not_lost(trails)` that returns the trails that are not"
            " lost, in order, keeping empty trails. A comprehension whose"
            " test is 'empty, or last entry not failed'.\n\n"
            "  not_lost([[\"collected\", \"delivered\"], [\"collected\", \"failed\"], [\"collected\"]]) -> [[\"collected\", \"delivered\"], [\"collected\"]]\n\n"
            "Return: a list of lists."
        ),
        solution=("def not_lost(trails):\n"
                  "    return [t for t in trails if not t or t[-1] != \"failed\"]\n"),
        trap=("def not_lost(trails):\n"
              "    return [t for t in trails if \"failed\" not in t]\n"),
        note="'failed' anywhere in the trail is not the same as 'failed'"
             " at the end: a parcel that failed once and was delivered"
             " later is not lost, and the trap throws it away. The test"
             " `not t or t[-1] != 'failed'` keeps the empty trail by"
             " the first half and never indexes it, because `or` stops"
             " when the first half is true.",
    ),
    dict(
        id=12, ledger="P547", concept="PY3 sort by a tuple key", tier="3 - Checks and filters",
        title="Codes in depot order, then by number", kind="function",
        func="by_depot_then_number",
        cases=[(["MB-100", "CH-7", "MB-23", "CH-100"],), (["WW-9", "WW-10"],), ([],), (["Z-1"],)],
        prompt=(
            "Write a function `by_depot_then_number(codes)` that returns"
            " the codes sorted by depot code alphabetically and, within"
            " a depot, by the NUMBER after the hyphen. sorted() with a"
            " key that returns a tuple of the two parts, the number"
            " converted to int.\n\n"
            "  by_depot_then_number([\"MB-100\", \"CH-7\", \"MB-23\", \"CH-100\"]) -> [\"CH-7\", \"CH-100\", \"MB-23\", \"MB-100\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def by_depot_then_number(codes):\n"
                  "    return sorted(codes, key=lambda c: (c.split(\"-\")[0], int(c.split(\"-\")[1])))\n"),
        trap=("def by_depot_then_number(codes):\n"
              "    return sorted(codes)\n"),
        note="Plain sorting compares the whole code as text, so 'CH-100'"
             " comes before 'CH-7' and the trap's order is wrong within"
             " each depot. A tuple key sorts by its first item and uses"
             " the second to break ties, so (depot, number) is 'depot,"
             " then number' in one expression; int() makes the second"
             " part numeric.",
    ),
    dict(
        id=13, ledger="P548", concept="PY3 duplicates ignoring case", tier="3 - Checks and filters",
        title="The same code typed two ways", kind="function",
        func="case_clash",
        cases=[(["MB-0012", "mb-0012"],), (["MB-0012", "MB-0013"],), ([],), (["ab-1", "AB-1", "Ab-1"],)],
        prompt=(
            "Scanners sometimes read a code in lower case. Write a"
            " function `case_clash(codes)` that returns True when two"
            " codes in the list are the same apart from case, and False"
            " otherwise. Compare how many codes there are with how many"
            " DIFFERENT codes there are once every one is lower-cased.\n\n"
            "  case_clash([\"MB-0012\", \"mb-0012\"]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def case_clash(codes):\n"
                  "    return len({c.lower() for c in codes}) < len(codes)\n"),
        trap=("def case_clash(codes):\n"
              "    return len(set(codes)) < len(codes)\n"),
        note="A set of the codes as typed treats 'MB-0012' and 'mb-0012'"
             " as different, so the trap never sees the clash. Lower-case"
             " every code before putting it in the set, and a repeat in"
             " any case collapses to one member, making the set smaller"
             " than the list. The empty list has no clash: 0 < 0 is"
             " False.",
    ),
    dict(
        id=14, ledger="P549", concept="PY3 split into tuples", tier="3 - Checks and filters",
        title="Codes taken apart", kind="function",
        func="split_codes",
        cases=[(["MB-0012", "CH-7"],), ([],), (["WW-100"],)],
        prompt=(
            "Write a function `split_codes(codes)` that turns each code"
            " into a pair: the depot code and the number as an int --"
            " ('MB', 12). A comprehension that splits at the hyphen and"
            " builds a tuple; the result is a list of tuples.\n\n"
            "  split_codes([\"MB-0012\", \"CH-7\"]) -> [(\"MB\", 12), (\"CH\", 7)]\n\n"
            "Return: a list of (str, int) tuples."
        ),
        solution=("def split_codes(codes):\n"
                  "    return [(c.split(\"-\")[0], int(c.split(\"-\")[1])) for c in codes]\n"),
        trap=("def split_codes(codes):\n"
              "    return [c.split(\"-\") for c in codes]\n"),
        note="split() returns a LIST of two strings, so the trap's items"
             " are ['MB', '0012'] -- the wrong container and the number"
             " still text. The question wants a tuple with the number"
             " converted, which means building it from the two parts;"
             " the grader keeps a list apart from a tuple and '0012'"
             " apart from 12.",
    ),
    dict(
        id=15, ledger="P550", concept="PY3 sorted check on a derived key", tier="3 - Checks and filters",
        title="Are the codes in numeric order?", kind="function",
        func="in_number_order",
        cases=[(["MB-7", "MB-23", "MB-100"],), (["MB-100", "MB-23", "MB-7"],), (["MB-1"],), ([],), (["A-5", "B-5"],)],
        prompt=(
            "Write a function `in_number_order(codes)` that returns True"
            " when the numbers after the hyphens never decrease along the"
            " list, and False otherwise; a list of one or none is in"
            " order. Pull the numbers out as ints, then compare the list"
            " with its sorted self.\n\n"
            "  in_number_order([\"MB-7\", \"MB-23\", \"MB-100\"]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def in_number_order(codes):\n"
                  "    nums = [int(c.split(\"-\")[1]) for c in codes]\n"
                  "    return nums == sorted(nums)\n"),
        trap=("def in_number_order(codes):\n"
              "    return codes == sorted(codes)\n"),
        note="Sorting the codes as text puts 'MB-100' before 'MB-23', so"
             " the trap says the numerically ordered list is out of"
             " order. Convert the numbers first and compare those; a list"
             " equals its sorted copy exactly when it is already in"
             " order, repeats included, and an empty or one-item list"
             " trivially is.",
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
