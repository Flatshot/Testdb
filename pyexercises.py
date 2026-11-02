"""Python practice exercises: fifteen small functions over plain values.

The twenty-eighth Python set, and a simpler one: no dicts, no rows, no
dates. Every function takes a list of numbers, a list of strings, a single
string or a couple of numbers, dressed in the bike scheme's terms -- metres
ridden, minutes out, a card number on a receipt, a member's name. Numbers:
a unit conversion with round, a mean with the extremes dropped, the three
largest added up, the commonest value with ties to the smallest, a median
by hand. Text: a card number masked, a bike code validated, a name cut to
fit, a plural, a surname-first name turned round. Lists: shares of a total,
weekly totals from daily figures, names sorted by surname, a spread with a
guard, a percentage change with a guard.

Every question is a `kind="function"`: the editor defines a function named
`func`. Run calls it once per case in `cases` and shows each call and its
result; Check compares each result with the reference function's. Values
are compared, not their printed form, but the container type counts, so a
tuple is not a list, 2.0 is not 2, and 0 is not False.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py).
"""

import pyrun

EXERCISES = [
    # ============================================================== 1 Numbers
    dict(
        id=1, ledger="P416", concept="PY3 transform with round", tier="1 - Numbers",
        title="Metres into kilometres", kind="function",
        func="to_km",
        cases=[([6478, 3833, 962, 12050],), ([999, 1000, 1001],), ([],), ([250],)],
        prompt=(
            "Rides are recorded in metres. Write a function `to_km("
            "distances)` that returns the same distances in kilometres,"
            " each rounded to one decimal, in the same order. A list"
            " comprehension with round(d / 1000, 1).\n\n"
            "  to_km([6478, 3833, 962, 12050]) -> [6.5, 3.8, 1.0, 12.1]\n\n"
            "Return: a list of floats."
        ),
        solution=("def to_km(distances):\n"
                  "    return [round(d / 1000, 1) for d in distances]\n"),
        trap=("def to_km(distances):\n"
              "    return [d // 1000 for d in distances]\n"),
        note="// is floor division and gives whole kilometres: 962 metres"
             " becomes 0 and 6,478 becomes 6, so the trap loses the"
             " decimal the question asks for. / gives a float, and"
             " round(x, 1) keeps one decimal of it; round(1000 / 1000,"
             " 1) is 1.0, still a float.",
    ),
    dict(
        id=2, ledger="P417", concept="PY3 trimmed mean", tier="1 - Numbers",
        title="The average with the extremes left out", kind="function",
        func="trimmed_mean",
        cases=[([12, 31, 27, 240, 19],), ([5, 5, 5],), ([8, 90],), ([],)],
        prompt=(
            "A few very long rides spoil an average. Write a function"
            " `trimmed_mean(minutes)` that drops ONE smallest and ONE"
            " largest value and returns the mean of the rest, rounded to"
            " two decimals -- or None when there are fewer than three"
            " values, since nothing would be left. sorted(), a slice"
            " [1:-1], then sum and len.\n\n"
            "  trimmed_mean([12, 31, 27, 240, 19]) -> 25.67\n\n"
            "Return: a float, or None."
        ),
        solution=("def trimmed_mean(minutes):\n"
                  "    if len(minutes) < 3:\n"
                  "        return None\n"
                  "    middle = sorted(minutes)[1:-1]\n"
                  "    return round(sum(middle) / len(middle), 2)\n"),
        trap=("def trimmed_mean(minutes):\n"
              "    if len(minutes) < 3:\n"
              "        return None\n"
              "    middle = minutes[1:-1]\n"
              "    return round(sum(middle) / len(middle), 2)\n"),
        note="The slice [1:-1] drops the first and last items, which are"
             " the smallest and largest only once the list is sorted:"
             " the trap slices the list as given and drops 12 and 19,"
             " keeping the 240 it was meant to lose. sorted() returns a"
             " new list and leaves the caller's alone.",
    ),
    dict(
        id=3, ledger="P418", concept="PY3 sorted slice sum", tier="1 - Numbers",
        title="The three biggest fares added up", kind="function",
        func="top_three_total",
        cases=[([350, 1200, 200, 990, 250, 1200],), ([300, 100],), ([],), ([400, 400, 400, 400],)],
        prompt=(
            "Write a function `top_three_total(fares)` that returns the"
            " sum of the three largest fares -- or of all of them when"
            " there are fewer than three. sorted(fares, reverse=True)"
            " and a slice [:3] inside sum().\n\n"
            "  top_three_total([350, 1200, 200, 990, 250, 1200]) -> 3390\n\n"
            "Return: an int."
        ),
        solution=("def top_three_total(fares):\n"
                  "    return sum(sorted(fares, reverse=True)[:3])\n"),
        trap=("def top_three_total(fares):\n"
              "    return sum(fares[:3])\n"),
        note="A slice takes positions, not sizes: fares[:3] is the first"
             " three fares in the list, whichever they are, and the trap"
             " adds 350, 1200 and 200. Sorting largest-first puts the"
             " three biggest at the front, and a slice past the end of a"
             " short list just stops at the end, so no guard is needed"
             " for two fares or none -- sum([]) is 0.",
    ),
    dict(
        id=4, ledger="P419", concept="PY3 max key count", tier="1 - Numbers",
        title="The usual length of a ride", kind="function",
        func="most_common",
        cases=[([30, 12, 30, 45, 12, 30],), ([7, 7, 3, 3],), ([],), ([15],)],
        prompt=(
            "Write a function `most_common(minutes)` that returns the"
            " value that appears most often, the SMALLEST of them when"
            " several tie, or None for an empty list. max(set(minutes),"
            " key=minutes.count) finds a most common value; the tie rule"
            " needs the candidates sorted first, because max() keeps the"
            " first of equals.\n\n"
            "  most_common([30, 12, 30, 45, 12, 30]) -> 30\n\n"
            "Return: an int, or None."
        ),
        solution=("def most_common(minutes):\n"
                  "    if not minutes:\n"
                  "        return None\n"
                  "    return max(sorted(set(minutes)), key=minutes.count)\n"),
        trap=("def most_common(minutes):\n"
              "    if not minutes:\n"
              "        return None\n"
              "    return max(minutes, key=minutes.count)\n"),
        note="max() with a key returns the FIRST item that reaches the"
             " best key, so which of two equally common values wins"
             " depends on the order they are visited in. Over the list"
             " itself the trap visits 7 before 3 and answers 7; over"
             " sorted(set(...)) the candidates come smallest first, each"
             " once, so the tie goes to 3. list.count works as a key"
             " because it is a function of one argument.",
    ),
    dict(
        id=5, ledger="P420", concept="PY3 median by hand", tier="1 - Numbers",
        title="The middle ride", kind="function",
        func="middle",
        cases=[([12, 31, 27, 240, 19],), ([8, 50, 20, 30],), ([15],), ([],), ([40, 10, 90, 20, 30],)],
        prompt=(
            "Write a function `middle(minutes)` that returns the median:"
            " sort the values, take the middle one when the count is"
            " odd, and the mean of the two middle ones when it is even"
            " -- always as a float -- or None for an empty list. With n"
            " = len(values), the middle indexes are n // 2 and (n - 1)"
            " // 2, which are the same index when n is odd.\n\n"
            "  middle([12, 31, 27, 240, 19]) -> 27.0\n\n"
            "Return: a float, or None."
        ),
        solution=("def middle(minutes):\n"
                  "    if not minutes:\n"
                  "        return None\n"
                  "    s = sorted(minutes)\n"
                  "    n = len(s)\n"
                  "    return (s[n // 2] + s[(n - 1) // 2]) / 2\n"),
        trap=("def middle(minutes):\n"
              "    if not minutes:\n"
              "        return None\n"
              "    n = len(minutes)\n"
              "    return (minutes[n // 2] + minutes[(n - 1) // 2]) / 2\n"),
        note="The median is a property of the SORTED values. The trap"
             " takes the middle of the list as given, and on the first"
             " case it gets 27 by luck of position; on [8, 50, 20, 30]"
             " it answers 35.0 where the sorted middle pair 20 and 30"
             " give 25.0. Adding the two middle indexes and halving"
             " handles odd and even in one line: for odd n they are the"
             " same element, and x + x over 2 is x, as a float.",
    ),
    # ================================================================= 2 Text
    dict(
        id=6, ledger="P421", concept="PY3 mask with slice", tier="2 - Text",
        title="A card number, hidden", kind="function",
        func="mask",
        cases=[("4929123456781234",), ("1234",), ("98765",), ("",)],
        prompt=(
            "A receipt shows only the last four digits of the card."
            " Write a function `mask(number)` that returns the number"
            " with every character but the last four replaced by '*':"
            " '*' * (len(number) - 4) joined to number[-4:].\n\n"
            "  mask(\"4929123456781234\") -> \"************1234\"\n\n"
            "Return: a str."
        ),
        solution=("def mask(number):\n"
                  "    return \"*\" * (len(number) - 4) + number[-4:]\n"),
        trap=("def mask(number):\n"
              "    return \"****\" + number[-4:]\n"),
        note="The number of stars has to come from the length, so the"
             " masked string is as long as the original: the trap's"
             " fixed four stars give '****1234' for a sixteen-digit"
             " card. '*' * n with n at zero or below is the empty string,"
             " so a four-digit number comes back as itself and nothing"
             " crashes on short input.",
    ),
    dict(
        id=7, ledger="P422", concept="PY3 validate format", tier="2 - Text",
        title="Is it a bike code?", kind="function",
        func="is_bike_code",
        cases=[("BK-0042",), ("BK-42",), ("bk-0042",), ("BK-00A2",), ("BK-0042X",)],
        prompt=(
            "A bike code is 'BK-' followed by exactly four digits, seven"
            " characters in all. Write a function `is_bike_code(code)`"
            " that returns True for a code in that form and False"
            " otherwise: len(code) == 7 and code.startswith('BK-') and"
            " code[3:].isdigit(), joined with and.\n\n"
            "  is_bike_code(\"BK-0042\") -> True\n\n"
            "Return: True or False."
        ),
        solution=("def is_bike_code(code):\n"
                  "    return len(code) == 7 and code.startswith(\"BK-\") and code[3:].isdigit()\n"),
        trap=("def is_bike_code(code):\n"
              "    return code.startswith(\"BK-\") and code[3:].isdigit()\n"),
        note="startswith and isdigit between them accept 'BK-42' and"
             " 'BK-00421', because neither says how many digits there"
             " are: the length test is the third condition. The three"
             " tests are each a bool, and `and` combines them, stopping"
             " at the first False. startswith is case-sensitive, so"
             " 'bk-0042' fails, as it should.",
    ),
    dict(
        id=8, ledger="P423", concept="PY3 slice with marker", tier="2 - Text",
        title="A name cut to fit", kind="function",
        func="cut_to_fit",
        cases=[("Station Approach", 10), ("Harbour", 10), ("Botanic Gardens", 15), ("Old Mill", 3)],
        prompt=(
            "A display has room for a fixed number of characters. Write"
            " a function `cut_to_fit(name, width)` that returns the name"
            " unchanged when it fits, and otherwise the first width - 1"
            " characters followed by '~', so that the result is exactly"
            " width long. A conditional expression on len(name) <="
            " width.\n\n"
            "  cut_to_fit(\"Station Approach\", 10) -> \"Station A~\"\n\n"
            "Return: a str."
        ),
        solution=("def cut_to_fit(name, width):\n"
                  "    return name if len(name) <= width else name[:width - 1] + \"~\"\n"),
        trap=("def cut_to_fit(name, width):\n"
              "    return name if len(name) <= width else name[:width] + \"~\"\n"),
        note="The marker takes a character of its own, so the slice has"
             " to stop one short: name[:width] + '~' is width + 1 long,"
             " and the trap overflows the display by one. A name that"
             " exactly fills the width is kept whole -- 'Botanic"
             " Gardens' is fifteen characters -- which is why the test is"
             " <= and not <.",
    ),
    dict(
        id=9, ledger="P424", concept="PY3 conditional plural", tier="2 - Text",
        title="One ride, two rides", kind="function",
        func="plural",
        cases=[(1, "ride"), (2, "ride"), (0, "dock"), (140, "bike")],
        prompt=(
            "Write a function `plural(n, word)` that returns the count"
            " and the word as one string, with an 's' on the word unless"
            " n is exactly 1: '1 ride', '2 rides', '0 docks'. An"
            " f-string with a conditional expression for the ending.\n\n"
            "  plural(2, \"ride\") -> \"2 rides\"\n\n"
            "Return: a str."
        ),
        solution=("def plural(n, word):\n"
                  "    return f\"{n} {word}{'' if n == 1 else 's'}\"\n"),
        trap=("def plural(n, word):\n"
              "    return f\"{n} {word}{'s' if n > 1 else ''}\"\n"),
        note="English pluralises everything but exactly one: zero takes"
             " the s ('0 docks'), so the test is n == 1, not n > 1 --"
             " the trap says '0 dock'. A conditional expression inside"
             " an f-string's braces is allowed, and the quotes inside"
             " must differ from the ones around the string.",
    ),
    dict(
        id=10, ledger="P425", concept="PY3 split and reorder", tier="2 - Text",
        title="Surname first, turned round", kind="function",
        func="natural_order",
        cases=[("Uddin, Hamid",), ("Villanueva, Rosa",), ("Baxter,Yusuf",), ("de la Cruz, Ana",)],
        prompt=(
            "The members file lists names as 'Uddin, Hamid'. Write a"
            " function `natural_order(name)` that returns them as"
            " 'Hamid Uddin': split at the comma, strip the spaces off"
            " each part, and join them the other way round.\n\n"
            "  natural_order(\"Uddin, Hamid\") -> \"Hamid Uddin\"\n\n"
            "Return: a str."
        ),
        solution=("def natural_order(name):\n"
                  "    last, first = name.split(\",\")\n"
                  "    return first.strip() + \" \" + last.strip()\n"),
        trap=("def natural_order(name):\n"
              "    last, first = name.split(\",\")\n"
              "    return first + \" \" + last\n"),
        note="Splitting at ',' leaves the space that followed it on the"
             " front of the first name, so the trap returns ' Hamid"
             " Uddin' with a leading space -- and 'Yusuf Baxter' is"
             " right only because that entry had no space to begin with."
             " strip() on each part makes the result the same whatever"
             " the spacing was. Unpacking the split into two names fails"
             " loudly if there is more than one comma, which is better"
             " than guessing.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=11, ledger="P426", concept="PY3 share of total list", tier="3 - Lists",
        title="Each zone's share, as percentages", kind="function",
        func="shares",
        cases=[([10361, 6491, 9716, 5756, 6281],), ([1, 1, 2],), ([50],), ([],)],
        prompt=(
            "Write a function `shares(counts)` that returns each count"
            " as a percentage of their total, rounded to one decimal, in"
            " the same order -- and [] for an empty list. Take the total"
            " once with sum(), then a comprehension.\n\n"
            "  shares([10361, 6491, 9716, 5756, 6281]) -> [26.8, 16.8, 25.2, 14.9, 16.3]\n\n"
            "Return: a list of floats."
        ),
        solution=("def shares(counts):\n"
                  "    total = sum(counts)\n"
                  "    return [round(100 * c / total, 1) for c in counts]\n"),
        trap=("def shares(counts):\n"
              "    total = sum(counts)\n"
              "    return [round(100 * c / total) for c in counts]\n"),
        note="round(x) with no second argument gives an int, and the"
             " grader keeps 27 and 26.8 apart; round(x, 1) keeps the"
             " decimal and the float. Computing the total once outside"
             " the comprehension saves re-adding the list for every"
             " item. An empty list never reaches the division, because"
             " the comprehension has nothing to loop over.",
    ),
    dict(
        id=12, ledger="P427", concept="PY3 chunk and sum", tier="3 - Lists",
        title="Weekly totals from daily counts", kind="function",
        func="weekly_totals",
        cases=[([3, 4, 2, 5, 6, 1, 2, 7, 8, 1, 2, 3, 4, 5, 9, 9],), ([1, 2, 3, 4, 5, 6, 7],), ([],), ([10, 20],)],
        prompt=(
            "Daily ride counts arrive as one long list. Write a function"
            " `weekly_totals(daily)` that returns the sum of each block"
            " of seven days, the last block included even if it is"
            " short. range(0, len(daily), 7) gives the start of each"
            " block, and daily[i:i + 7] is the block.\n\n"
            "  weekly_totals([3, 4, 2, 5, 6, 1, 2, 7, 8, 1, 2, 3, 4, 5, 9, 9]) -> [23, 30, 18]\n\n"
            "Return: a list of ints."
        ),
        solution=("def weekly_totals(daily):\n"
                  "    return [sum(daily[i:i + 7]) for i in range(0, len(daily), 7)]\n"),
        trap=("def weekly_totals(daily):\n"
              "    return [sum(daily[i:i + 7]) for i in range(0, len(daily) // 7 * 7, 7)]\n"),
        note="range(0, len(daily), 7) stops at the length, so the last"
             " start may be fewer than seven from the end, and the slice"
             " simply takes what is there: the two-day week of 9 and 9"
             " comes out as 18. The trap rounds the length down to whole"
             " weeks and drops it. A slice beyond the end of a list is"
             " never an error -- unlike an index.",
    ),
    dict(
        id=13, ledger="P428", concept="PY3 sorted key last word", tier="3 - Lists",
        title="Members in surname order", kind="function",
        func="by_surname",
        cases=[(["Hamid Uddin", "Rosa Villanueva", "Yusuf Baxter"],), (["Zara Achebe", "Aisha Zielinski"],), ([],), (["Grace Sowerby"],)],
        prompt=(
            "Write a function `by_surname(names)` that returns the"
            " names sorted by their last word, the surname, as a new"
            " list. sorted() with key=lambda n: n.split()[-1].\n\n"
            "  by_surname([\"Hamid Uddin\", \"Rosa Villanueva\", \"Yusuf Baxter\"]) -> [\"Yusuf Baxter\", \"Hamid Uddin\", \"Rosa Villanueva\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def by_surname(names):\n"
                  "    return sorted(names, key=lambda n: n.split()[-1])\n"),
        trap=("def by_surname(names):\n"
              "    return sorted(names)\n"),
        note="sorted(names) compares whole strings from their first"
             " character, which is the FIRST name: the trap puts Zara"
             " Achebe after Aisha Zielinski. A key function is called"
             " once per item and its results are what get compared, so"
             " split()[-1] sorts by surname while the list still holds"
             " the full names.",
    ),
    dict(
        id=14, ledger="P429", concept="PY3 max minus min guard", tier="3 - Lists",
        title="How far apart the fares are", kind="function",
        func="spread",
        cases=[([350, 1200, 200, 990],), ([400],), ([],), ([0, 0, 5],)],
        prompt=(
            "Write a function `spread(fares)` that returns the"
            " difference between the largest and the smallest fare, or"
            " None for an empty list. max() minus min(), behind a"
            " guard.\n\n"
            "  spread([350, 1200, 200, 990]) -> 1000\n\n"
            "Return: an int, or None."
        ),
        solution=("def spread(fares):\n"
                  "    if not fares:\n"
                  "        return None\n"
                  "    return max(fares) - min(fares)\n"),
        trap=("def spread(fares):\n"
              "    return max(fares) - min(fares)\n"),
        note="max() and min() of an empty list raise ValueError, so the"
             " guard is the whole difference between the two versions."
             " A single fare has a spread of 0, which the guard"
             " correctly lets through: `if not fares` is False for a"
             " list with one item.",
    ),
    dict(
        id=15, ledger="P430", concept="PY3 percentage change", tier="3 - Lists",
        title="Up or down on last year", kind="function",
        func="pct_change",
        cases=[(1943, 2184), (2260, 2071), (500, 500), (0, 120)],
        prompt=(
            "Write a function `pct_change(before, after)` that returns"
            " the change from before to after as a percentage of before,"
            " rounded to one decimal -- positive for a rise, negative"
            " for a fall -- or None when before is 0, since there is"
            " nothing to compare with.\n\n"
            "  pct_change(1943, 2184) -> 12.4\n\n"
            "Return: a float, or None."
        ),
        solution=("def pct_change(before, after):\n"
                  "    if before == 0:\n"
                  "        return None\n"
                  "    return round(100 * (after - before) / before, 1)\n"),
        trap=("def pct_change(before, after):\n"
              "    if before == 0:\n"
              "        return None\n"
              "    return round(100 * (after - before) / after, 1)\n"),
        note="A change is measured against where it started, so the"
             " divisor is before: the trap divides by after and reports"
             " 11.0 for January's rise instead of 12.4, and would make"
             " every fall look smaller than it was. The guard catches"
             " the division by zero before it happens; 0 to 120 is not"
             " a percentage of anything.",
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
