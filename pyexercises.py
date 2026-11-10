"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-fourth Python set, at the easy level of the last four -- no
statistics, no dicts -- in the courier's terms, on tasks the earlier sets
did not cover. Counting and finding: two statuses in a row, the heaviest
parcel's code, the number inside a code, trails that end delivered, the
longest trail. Labels: a billing period as words, a check digit, a box
label, a status badge, a tracking message. Checks and filters: the codes
over a limit, a trail checked for shape, the trail since the last failure,
codes sorted by their number, repeats flagged.

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
        id=1, ledger="P506", concept="PY4 adjacent pair exists", tier="1 - Counting and finding",
        title="Did a failure come straight after an attempt?", kind="function",
        func="has_pair",
        cases=[(["collected", "out_for_delivery", "failed", "delivered"], "out_for_delivery", "failed"), (["collected", "failed", "arrived", "out_for_delivery"], "out_for_delivery", "failed"), (["collected"], "collected", "departed"), ([], "a", "b")],
        prompt=(
            "Write a function `has_pair(trail, first, second)` that"
            " returns True when the second status comes IMMEDIATELY"
            " after the first somewhere in the trail, and False"
            " otherwise. zip the trail with itself shifted by one to"
            " walk the consecutive pairs; any() over them.\n\n"
            "  has_pair([\"collected\", \"out_for_delivery\", \"failed\", \"delivered\"], \"out_for_delivery\", \"failed\") -> True\n\n"
            "Return: True or False."
        ),
        solution=("def has_pair(trail, first, second):\n"
                  "    return any(a == first and b == second for a, b in zip(trail, trail[1:]))\n"),
        trap=("def has_pair(trail, first, second):\n"
              "    return first in trail and second in trail\n"),
        note="Both statuses being somewhere in the trail is not the same"
             " as one following the other: the trap says True for a trail"
             " where the failure came BEFORE the attempt. zip(trail,"
             " trail[1:]) yields each entry with the next, so the pair"
             " test is on neighbours only, and any() stops at the first"
             " match.",
    ),
    dict(
        id=2, ledger="P507", concept="PY3 argmax via zip", tier="1 - Counting and finding",
        title="The code of the heaviest parcel", kind="function",
        func="heaviest",
        cases=[(["MB-0012", "CH-0007", "WW-0002"], [2500, 7500, 1200]), (["A", "B"], [5, 5]), (["Z"], [1]), ([], [])],
        prompt=(
            "Two lists line up: parcel codes and their weights. Write a"
            " function `heaviest(codes, weights)` that returns the code"
            " of the heaviest parcel -- on a tie, the one whose code"
            " sorts last -- or None when the lists are empty. max() over"
            " the zipped pairs with the weight first, then the code out"
            " of the winning pair.\n\n"
            "  heaviest([\"MB-0012\", \"CH-0007\", \"WW-0002\"], [2500, 7500, 1200]) -> \"CH-0007\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def heaviest(codes, weights):\n"
                  "    if not codes:\n"
                  "        return None\n"
                  "    return max(zip(weights, codes))[1]\n"),
        trap=("def heaviest(codes, weights):\n"
              "    if not codes:\n"
              "        return None\n"
              "    return max(weights)\n"),
        note="max(weights) is the heaviest WEIGHT, 7500, not the parcel"
             " that has it. Zipping the weights first makes each pair"
             " compare by weight and then by code, so max() finds the"
             " heaviest parcel and settles a tie by the code, and [1]"
             " takes the code out of the pair. The guard is for max()"
             " of nothing, which raises.",
    ),
    dict(
        id=3, ledger="P508", concept="PY3 int of a split part", tier="1 - Counting and finding",
        title="The number inside a parcel code", kind="function",
        func="code_number",
        cases=[("MB-0012",), ("CHB-0007",), ("WW-100",), ("X-0",)],
        prompt=(
            "A parcel code is a depot code, a hyphen and a number with"
            " leading zeros: 'MB-0012', 'CHB-0007'. Write a function"
            " `code_number(code)` that returns the number as an int."
            " Split at the hyphen and convert the part after it; the"
            " depot code can be any length.\n\n"
            "  code_number(\"MB-0012\") -> 12\n\n"
            "Return: an int."
        ),
        solution=("def code_number(code):\n"
                  "    return int(code.split(\"-\")[1])\n"),
        trap=("def code_number(code):\n"
              "    return int(code[3:])\n"),
        note="Slicing from position 3 assumes a two-letter depot code"
             " and a hyphen: 'CHB-0007' slices to '-0007' and int()"
             " refuses it, and the trap crashes. split('-') finds the"
             " hyphen wherever it is, and int() of '0012' is 12 -- the"
             " leading zeros are no trouble to int().",
    ),
    dict(
        id=4, ledger="P509", concept="PY4 count by last item", tier="1 - Counting and finding",
        title="How many trails end in a delivery", kind="function",
        func="completed",
        cases=[([["collected", "delivered"], ["collected", "failed"], []],), ([],), ([["delivered"]],), ([["collected", "delivered", "failed"]],)],
        prompt=(
            "Write a function `completed(trails)` that takes a list of"
            " trails -- each a list of status words -- and returns how"
            " many end with 'delivered'. An empty trail has no last"
            " entry and does not count; test the trail is non-empty"
            " before looking at its last item.\n\n"
            "  completed([[\"collected\", \"delivered\"], [\"collected\", \"failed\"], []]) -> 1\n\n"
            "Return: an int."
        ),
        solution=("def completed(trails):\n"
                  "    return sum(1 for t in trails if t and t[-1] == \"delivered\")\n"),
        trap=("def completed(trails):\n"
              "    return sum(1 for t in trails if t[-1] == \"delivered\")\n"),
        note="t[-1] on an empty trail raises IndexError, and the trap"
             " falls over on the third trail. `t and t[-1] == ...` tests"
             " the trail first and only reaches the index when there is"
             " something to index, because `and` stops at the first"
             " false value. A trail that was delivered and then failed"
             " ends on the failure, so it does not count.",
    ),
    dict(
        id=5, ledger="P510", concept="PY3 max of lengths with default", tier="1 - Counting and finding",
        title="The longest trail in the batch", kind="function",
        func="longest_trail",
        cases=[([["collected", "delivered"], ["collected", "departed", "arrived"], ["collected"]],), ([],), ([[]],), ([["a"], ["b"]],)],
        prompt=(
            "Write a function `longest_trail(trails)` that returns the"
            " number of scans in the longest trail, or 0 when there are"
            " no trails at all. max() over the lengths, with a default"
            " for the empty case.\n\n"
            "  longest_trail([[\"collected\", \"delivered\"], [\"collected\", \"departed\", \"arrived\"], [\"collected\"]]) -> 3\n\n"
            "Return: an int."
        ),
        solution=("def longest_trail(trails):\n"
                  "    return max((len(t) for t in trails), default=0)\n"),
        trap=("def longest_trail(trails):\n"
              "    return max(len(t) for t in trails)\n"),
        note="max() of an empty sequence raises ValueError, and the trap"
             " crashes on a batch with no trails. The default= argument"
             " is what max() returns when there is nothing to compare,"
             " and 0 is the right answer for no trails. A batch holding"
             " one empty trail is different: its longest trail has 0"
             " scans, and max() finds that without the default.",
    ),
    # ================================================================ 2 Labels
    dict(
        id=6, ledger="P511", concept="PY3 list lookup by index", tier="2 - Labels",
        title="A billing period as words", kind="function",
        func="period_words",
        cases=[("2026-05",), ("2025-12",), ("2026-01",)],
        prompt=(
            "Invoices carry a period like '2026-05'. Write a function"
            " `period_words(period)` that returns it as 'May 2026'."
            " A list of the twelve month names, indexed by the month"
            " number -- mind that lists start at 0 -- after split('-')"
            " and int().\n\n"
            "  period_words(\"2026-05\") -> \"May 2026\"\n\n"
            "Return: a str."
        ),
        solution=("MONTHS = [\"January\", \"February\", \"March\", \"April\", \"May\", \"June\",\n"
                  "          \"July\", \"August\", \"September\", \"October\", \"November\", \"December\"]\n\n"
                  "def period_words(period):\n"
                  "    year, month = period.split(\"-\")\n"
                  "    return f\"{MONTHS[int(month) - 1]} {year}\"\n"),
        trap=("MONTHS = [\"January\", \"February\", \"March\", \"April\", \"May\", \"June\",\n"
              "          \"July\", \"August\", \"September\", \"October\", \"November\", \"December\"]\n\n"
              "def period_words(period):\n"
              "    year, month = period.split(\"-\")\n"
              "    return f\"{MONTHS[int(month)]} {year}\"\n"),
        note="Month 5 is the FIFTH name, which sits at index 4: the trap"
             " forgets the - 1 and labels May as June, and December,"
             " month 12, raises IndexError on a twelve-item list. A list"
             " indexed by a number is the simplest lookup table there is,"
             " as long as the off-by-one is handled once.",
    ),
    dict(
        id=7, ledger="P512", concept="PY3 check digit", tier="2 - Labels",
        title="A check digit on the end", kind="function",
        func="with_check_digit",
        cases=[("0012",), ("0007",), ("1234",), ("9999",)],
        prompt=(
            "To catch typing mistakes, a parcel number gets a check"
            " digit: the sum of its digits, modulo 10, written on the"
            " end. Write a function `with_check_digit(number)` that"
            " returns the number with that digit appended: '0012'"
            " becomes '00123'. sum() over the digits as ints, then %"
            " 10, then str().\n\n"
            "  with_check_digit(\"0012\") -> \"00123\"\n\n"
            "Return: a str."
        ),
        solution=("def with_check_digit(number):\n"
                  "    return number + str(sum(int(d) for d in number) % 10)\n"),
        trap=("def with_check_digit(number):\n"
              "    return number + str(sum(int(d) for d in number))\n"),
        note="The check digit is ONE digit, and the sum can be more:"
             " '1234' sums to 10 and '9999' to 36, so the trap appends"
             " two digits and the number grows by a different amount"
             " each time. % 10 keeps the last digit of the sum. Iterating"
             " a string gives its characters, and int() turns each back"
             " into a number to add.",
    ),
    dict(
        id=8, ledger="P513", concept="PY3 f-string with units", tier="2 - Labels",
        title="A box's size on the label", kind="function",
        func="box_label",
        cases=[(30, 20, 10), (100, 5, 5), (1, 1, 1)],
        prompt=(
            "Write a function `box_label(length, width, height)` that"
            " returns the dimensions as '30 x 20 x 10 cm' -- the three"
            " numbers joined by ' x ', then a space and 'cm'. One"
            " f-string.\n\n"
            "  box_label(30, 20, 10) -> \"30 x 20 x 10 cm\"\n\n"
            "Return: a str."
        ),
        solution=("def box_label(length, width, height):\n"
                  "    return f\"{length} x {width} x {height} cm\"\n"),
        trap=("def box_label(length, width, height):\n"
              "    return f\"{length}x{width}x{height}\"\n"),
        note="The grader compares the whole string, so the spaces round"
             " each x and the unit on the end are part of the answer:"
             " '30x20x10' is a different string. An f-string puts the"
             " numbers where its braces are and leaves every other"
             " character exactly as typed.",
    ),
    dict(
        id=9, ledger="P514", concept="PY3 replace upper wrap", tier="2 - Labels",
        title="A status as a badge", kind="function",
        func="badge",
        cases=[("out_for_delivery",), ("delivered",), ("failed",)],
        prompt=(
            "Write a function `badge(status)` that turns a status code"
            " into a badge for a screen: capitals, underscores as"
            " spaces, square brackets round it -- '[OUT FOR DELIVERY]'."
            " replace(), upper(), and an f-string for the brackets.\n\n"
            "  badge(\"out_for_delivery\") -> \"[OUT FOR DELIVERY]\"\n\n"
            "Return: a str."
        ),
        solution=("def badge(status):\n"
                  "    return f\"[{status.replace('_', ' ').upper()}]\"\n"),
        trap=("def badge(status):\n"
              "    return f\"[{status.upper()}]\"\n"),
        note="upper() leaves the underscores where they are, so the trap"
             " prints '[OUT_FOR_DELIVERY]'. replace('_', ' ') first, then"
             " upper(), chained on the same expression inside the"
             " braces; the brackets are plain characters of the f-string."
             " The quotes inside the braces have to differ from the ones"
             " round the string.",
    ),
    dict(
        id=10, ledger="P515", concept="PY3 sentence from parts", tier="2 - Labels",
        title="A tracking message", kind="function",
        func="tracking_message",
        cases=[("MB-0012", "out_for_delivery"), ("CH-0007", "delivered"), ("WW-0002", "failed")],
        prompt=(
            "Write a function `tracking_message(code, status)` that"
            " returns a sentence for the customer: 'Parcel MB-0012 is"
            " out for delivery.' -- the status with its underscores"
            " turned to spaces, a full stop at the end.\n\n"
            "  tracking_message(\"MB-0012\", \"out_for_delivery\") -> \"Parcel MB-0012 is out for delivery.\"\n\n"
            "Return: a str."
        ),
        solution=("def tracking_message(code, status):\n"
                  "    return f\"Parcel {code} is {status.replace('_', ' ')}.\"\n"),
        trap=("def tracking_message(code, status):\n"
              "    return f\"Parcel {code} is {status}.\"\n"),
        note="The status code is for the database, not the customer:"
             " the trap writes 'is out_for_delivery.' and the underscores"
             " show. A method call is allowed inside an f-string's"
             " braces, so the replace happens where the value is used."
             " The full stop is part of the sentence the question asks"
             " for.",
    ),
    # ==================================================== 3 Checks and filters
    dict(
        id=11, ledger="P516", concept="PY3 filter one list by another", tier="3 - Checks and filters",
        title="The codes of the parcels over the limit", kind="function",
        func="heavy_codes",
        cases=[(["MB-0012", "CH-0007", "WW-0002"], [2500, 12000, 11000], 10000), (["A"], [1], 10000), ([], [], 1), (["A", "B"], [10000, 10001], 10000)],
        prompt=(
            "Two lists line up: parcel codes and their weights. Write a"
            " function `heavy_codes(codes, weights, limit)` that returns"
            " the codes of the parcels weighing MORE than the limit, in"
            " order. zip() the two lists in a comprehension, test the"
            " weight, keep the code.\n\n"
            "  heavy_codes([\"MB-0012\", \"CH-0007\", \"WW-0002\"], [2500, 12000, 11000], 10000) -> [\"CH-0007\", \"WW-0002\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def heavy_codes(codes, weights, limit):\n"
                  "    return [c for c, w in zip(codes, weights) if w > limit]\n"),
        trap=("def heavy_codes(codes, weights, limit):\n"
              "    return [w for c, w in zip(codes, weights) if w > limit]\n"),
        note="The comprehension's first part says what goes into the"
             " list, and the trap puts the weights there -- [12000,"
             " 11000] -- when the codes were asked for. zip pairs each"
             " code with its own weight; the `if` tests one, the"
             " expression keeps the other. Exactly the limit is not"
             " over it, so > rather than >=.",
    ),
    dict(
        id=12, ledger="P517", concept="PY4 shape check with guards", tier="3 - Checks and filters",
        title="Is the trail well formed?", kind="function",
        func="trail_ok",
        cases=[(["collected", "departed", "delivered"],), (["departed", "delivered"],), (["collected", "delivered", "failed"],), (["collected", "departed"],), ([],)],
        prompt=(
            "A trail is well formed when it starts with 'collected' and,"
            " if 'delivered' appears at all, it is the LAST entry. Write"
            " a function `trail_ok(trail)` that returns True or False;"
            " an empty trail is not well formed. Guard the empty case,"
            " then test the first entry, then the delivery rule.\n\n"
            "  trail_ok([\"collected\", \"departed\", \"delivered\"]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def trail_ok(trail):\n"
                  "    if not trail or trail[0] != \"collected\":\n"
                  "        return False\n"
                  "    if \"delivered\" in trail and trail[-1] != \"delivered\":\n"
                  "        return False\n"
                  "    return True\n"),
        trap=("def trail_ok(trail):\n"
              "    return trail[0] == \"collected\" and trail[-1] == \"delivered\"\n"),
        note="The trap requires a delivery at the end, but a trail still"
             " in transit -- collected, departed -- is well formed too,"
             " and the trap also crashes on the empty trail. The"
             " delivery rule is conditional: ONLY IF 'delivered' is"
             " present must it be last. Three checks in order, each"
             " returning False early, and True when none fails.",
    ),
    dict(
        id=13, ledger="P518", concept="PY4 after the last occurrence", tier="3 - Checks and filters",
        title="The trail since the last failure", kind="function",
        func="since_last_failure",
        cases=[(["collected", "out_for_delivery", "failed", "out_for_delivery", "failed", "out_for_delivery", "delivered"],), (["collected", "delivered"],), (["collected", "failed"],), ([],)],
        prompt=(
            "Write a function `since_last_failure(trail)` that returns"
            " the entries after the LAST 'failed' -- or the whole trail"
            " if there is none. index() finds the first occurrence only,"
            " so find the last by searching the reversed trail, or by"
            " looping to remember the latest position.\n\n"
            "  since_last_failure([\"collected\", \"out_for_delivery\", \"failed\", \"out_for_delivery\", \"failed\", \"out_for_delivery\", \"delivered\"]) -> [\"out_for_delivery\", \"delivered\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def since_last_failure(trail):\n"
                  "    last = -1\n"
                  "    for i, s in enumerate(trail):\n"
                  "        if s == \"failed\":\n"
                  "            last = i\n"
                  "    return trail[last + 1:]\n"),
        trap=("def since_last_failure(trail):\n"
              "    if \"failed\" not in trail:\n"
              "        return trail\n"
              "    return trail[trail.index(\"failed\") + 1:]\n"),
        note="index() stops at the FIRST failure, so the trap returns"
             " everything after it, the second failure included. A loop"
             " that overwrites `last` on every failure ends holding the"
             " final one, and starting `last` at -1 makes trail[0:] --"
             " the whole trail -- the answer when there was none. A"
             " trail ending in a failure gives [].",
    ),
    dict(
        id=14, ledger="P519", concept="PY3 sort by a numeric key", tier="3 - Checks and filters",
        title="Codes in numeric order, not text order", kind="function",
        func="by_number",
        cases=[(["MB-100", "MB-7", "MB-23"],), (["A-2", "A-10", "A-1"],), ([],), (["X-5"],)],
        prompt=(
            "Parcel codes are not always zero-padded, and 'MB-100'"
            " sorts before 'MB-7' as text. Write a function"
            " `by_number(codes)` that returns the codes sorted by the"
            " NUMBER after the hyphen. sorted() with a key that splits"
            " and converts.\n\n"
            "  by_number([\"MB-100\", \"MB-7\", \"MB-23\"]) -> [\"MB-7\", \"MB-23\", \"MB-100\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def by_number(codes):\n"
                  "    return sorted(codes, key=lambda c: int(c.split(\"-\")[1]))\n"),
        trap=("def by_number(codes):\n"
              "    return sorted(codes)\n"),
        note="Text compares character by character, so '1' beats '7'"
             " and 'MB-100' comes first: the trap's order is 100, 23, 7."
             " A key function turns each code into the number it should"
             " sort by, and sorted() compares those while returning the"
             " codes. The codes themselves are never changed.",
    ),
    dict(
        id=15, ledger="P520", concept="PY4 flag repeats with a set", tier="3 - Checks and filters",
        title="Which scans are repeats", kind="function",
        func="repeat_flags",
        cases=[(["MB-1", "CH-2", "MB-1", "MB-1"],), (["A", "B"],), ([],), (["A", "A"],)],
        prompt=(
            "A scanner sometimes reads the same code twice. Write a"
            " function `repeat_flags(codes)` that returns a list of"
            " True and False, one per code, True when that code has"
            " ALREADY appeared earlier in the list. A loop with a set"
            " of what has been seen so far.\n\n"
            "  repeat_flags([\"MB-1\", \"CH-2\", \"MB-1\", \"MB-1\"]) -> [False, False, True, True]\n\n"
            "Return: a list of bool."
        ),
        solution=("def repeat_flags(codes):\n"
                  "    seen = set()\n"
                  "    flags = []\n"
                  "    for c in codes:\n"
                  "        flags.append(c in seen)\n"
                  "        seen.add(c)\n"
                  "    return flags\n"),
        trap=("def repeat_flags(codes):\n"
              "    return [codes.count(c) > 1 for c in codes]\n"),
        note="count() > 1 flags EVERY copy of a repeated code, the first"
             " one included: the trap marks the first 'MB-1' as a repeat"
             " of itself. The set holds what came before, and the test"
             " runs before the add, so the first sighting is False and"
             " every later one True. Order matters here, which is why it"
             " is a loop rather than a comprehension.",
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
