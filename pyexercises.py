"""Python practice exercises: fifteen everyday functions over plain values.

The thirtieth Python set, easier by request: no statistics, no formulas
beyond adding and taking away, no dicts. Every function is the kind of
small job a bike scheme's staff might ask for -- where a station appears
in a day's stops, which bikes did not come back, a name shortened for a
badge, a list of names joined with 'and', a day's stops split into short
and long rides. Counting and finding: every position of a value, the
n-th visit, what is missing with the order kept, whether one stop came
before another, words in a name. Labels: an initial and a surname, a list
with 'and', a vowel at the front, a message shouted when urgent, minutes
as hours and minutes. Checks and filters: a split into two lists returned
as a tuple, the first and last stop, a round trip, codes tidied, ids kept
within a range.

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
        id=1, ledger="P446", concept="PY4 all positions of a value", tier="1 - Counting and finding",
        title="Every time the bike stopped at Harbour", kind="function",
        func="positions_of",
        cases=[(["Harbour", "Stadium", "Harbour", "Parkway", "Harbour"], "Harbour"), (["Stadium", "Parkway"], "Harbour"), ([], "Harbour"), (["Harbour"], "Harbour")],
        prompt=(
            "A day's stops are a list of station names. Write a"
            " function `positions_of(stops, station)` that returns"
            " every position at which the station appears, in order,"
            " counting from 0. enumerate() gives each stop with its"
            " position.\n\n"
            "  positions_of([\"Harbour\", \"Stadium\", \"Harbour\", \"Parkway\", \"Harbour\"], \"Harbour\") -> [0, 2, 4]\n\n"
            "Return: a list of ints, possibly empty."
        ),
        solution=("def positions_of(stops, station):\n"
                  "    return [i for i, s in enumerate(stops) if s == station]\n"),
        trap=("def positions_of(stops, station):\n"
              "    return [stops.index(station)]\n"),
        note="index() finds the FIRST occurrence only, and raises"
             " ValueError when there is none, so the trap answers [0]"
             " for three visits and crashes on a day with no Harbour."
             " enumerate() pairs each item with its position, and the"
             " comprehension keeps the positions whose item matches --"
             " none, one or many, with no special cases.",
    ),
    dict(
        id=2, ledger="P447", concept="PY4 nth occurrence", tier="1 - Counting and finding",
        title="The second visit", kind="function",
        func="nth_visit",
        cases=[(["Harbour", "Stadium", "Harbour", "Parkway", "Harbour"], "Harbour", 2), (["Harbour", "Stadium", "Harbour"], "Harbour", 3), (["Stadium"], "Harbour", 1), (["Harbour", "Stadium", "Harbour", "Parkway", "Harbour"], "Harbour", 3)],
        prompt=(
            "Write a function `nth_visit(stops, station, n)` that"
            " returns the position of the n-th time the station"
            " appears (n = 1 for the first), or -1 if it does not"
            " appear that many times. A loop with a counter that goes"
            " up on each match and returns the position when it"
            " reaches n.\n\n"
            "  nth_visit([\"Harbour\", \"Stadium\", \"Harbour\", \"Parkway\", \"Harbour\"], \"Harbour\", 2) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def nth_visit(stops, station, n):\n"
                  "    seen = 0\n"
                  "    for i, s in enumerate(stops):\n"
                  "        if s == station:\n"
                  "            seen += 1\n"
                  "            if seen == n:\n"
                  "                return i\n"
                  "    return -1\n"),
        trap=("def nth_visit(stops, station, n):\n"
              "    seen = 0\n"
              "    for i, s in enumerate(stops):\n"
              "        if s == station:\n"
              "            seen += 1\n"
              "            if seen == n:\n"
              "                return i\n"),
        note="A function that reaches its end without a return gives"
             " back None, and None is not -1: the trap is right whenever"
             " the visit exists and wrong whenever it does not. The"
             " `return -1` after the loop is the 'not found' answer, and"
             " it is reached only when the loop runs out without"
             " returning.",
    ),
    dict(
        id=3, ledger="P448", concept="PY4 missing with order kept", tier="1 - Counting and finding",
        title="The bikes that did not come back", kind="function",
        func="not_returned",
        cases=[([12, 7, 30, 4], [4, 12]), ([5, 6], [6, 5]), ([], [1]), ([9, 3, 9], [])],
        prompt=(
            "Two lists of bike ids: the ones that went out this"
            " morning, in the order they left, and the ones back by"
            " closing. Write a function `not_returned(out, back)` that"
            " returns the ids that went out and are not back, in the"
            " order they went out. A comprehension with `not in`.\n\n"
            "  not_returned([12, 7, 30, 4], [4, 12]) -> [7, 30]\n\n"
            "Return: a list of ints."
        ),
        solution=("def not_returned(out, back):\n"
                  "    return [b for b in out if b not in back]\n"),
        trap=("def not_returned(out, back):\n"
              "    return sorted(set(out) - set(back))\n"),
        note="Set difference gives the right MEMBERS but loses the order"
             " and the repeats: the trap sorts them, so [30, 7] becomes"
             " [7, 30] here by luck of the numbers, and a bike that went"
             " out twice is listed once. `not in` on a list, inside a"
             " comprehension over the original, keeps both. On a few"
             " dozen bikes the slower lookup does not matter.",
    ),
    dict(
        id=4, ledger="P449", concept="PY4 order of two values", tier="1 - Counting and finding",
        title="Did it reach Harbour before Stadium?", kind="function",
        func="reached_before",
        cases=[(["Parkway", "Harbour", "Stadium"], "Harbour", "Stadium"), (["Stadium", "Harbour"], "Harbour", "Stadium"), (["Parkway", "Harbour"], "Harbour", "Stadium"), ([], "Harbour", "Stadium")],
        prompt=(
            "Write a function `reached_before(stops, a, b)` that"
            " returns True when station a appears in the list before"
            " station b, and False otherwise -- including when either"
            " is missing. Check that both are present before comparing"
            " their index() positions.\n\n"
            "  reached_before([\"Parkway\", \"Harbour\", \"Stadium\"], \"Harbour\", \"Stadium\") -> True\n\n"
            "Return: True or False."
        ),
        solution=("def reached_before(stops, a, b):\n"
                  "    if a not in stops or b not in stops:\n"
                  "        return False\n"
                  "    return stops.index(a) < stops.index(b)\n"),
        trap=("def reached_before(stops, a, b):\n"
              "    return stops.index(a) < stops.index(b)\n"),
        note="index() raises ValueError for a value that is not there,"
             " so the trap crashes on a day that never reached Stadium."
             " The `in` tests come first and settle the missing cases"
             " as False; only then are the two positions safe to"
             " compare. A question with a yes-or-no answer should return"
             " a bool, not print one.",
    ),
    dict(
        id=5, ledger="P450", concept="PY3 count words", tier="1 - Counting and finding",
        title="How many words in the name", kind="function",
        func="word_count",
        cases=[("Station Approach",), ("Harbour",), ("  Old   Mill ",), ("",)],
        prompt=(
            "Write a function `word_count(name)` that returns how many"
            " words a station name has. split() with no argument"
            " breaks on any run of spaces and ignores spaces at the"
            " ends, and len() counts the pieces.\n\n"
            "  word_count(\"Station Approach\") -> 2\n\n"
            "Return: an int."
        ),
        solution=("def word_count(name):\n"
                  "    return len(name.split())\n"),
        trap=("def word_count(name):\n"
              "    return name.count(\" \") + 1\n"),
        note="Counting spaces assumes exactly one space between words"
             " and none at the ends: the trap says 6 for '  Old   Mill '"
             " and 1 for an empty string. split() with no separator"
             " treats any amount of whitespace as one break and drops"
             " the empty pieces at the ends, so the empty string gives"
             " [] and a count of 0.",
    ),
    # ================================================================ 2 Labels
    dict(
        id=6, ledger="P451", concept="PY3 initial and surname", tier="2 - Labels",
        title="A name shortened for a badge", kind="function",
        func="badge_name",
        cases=[("Hamid Uddin",), ("Rosa Villanueva",), ("Ana de la Cruz",), ("Cher",)],
        prompt=(
            "Write a function `badge_name(name)` that returns the first"
            " initial, a dot, a space and the last word of the name:"
            " 'H. Uddin'. A name with no space is returned as it is.\n\n"
            "  badge_name(\"Hamid Uddin\") -> \"H. Uddin\"\n\n"
            "Return: a str."
        ),
        solution=("def badge_name(name):\n"
                  "    words = name.split()\n"
                  "    if len(words) < 2:\n"
                  "        return name\n"
                  "    return words[0][0] + \". \" + words[-1]\n"),
        trap=("def badge_name(name):\n"
              "    words = name.split()\n"
              "    return words[0][0] + \". \" + words[-1]\n"),
        note="A single-word name has no surname to add, and the trap"
             " turns 'Cher' into 'C. Cher'. words[-1] takes the LAST"
             " word, so 'Ana de la Cruz' gives 'A. Cruz' rather than"
             " 'A. de': the question asks for the last word, and"
             " anything cleverer would need to know which names are"
             " particles.",
    ),
    dict(
        id=7, ledger="P452", concept="PY3 join with and", tier="2 - Labels",
        title="A list of names, with an 'and'", kind="function",
        func="with_and",
        cases=[(["Hamid", "Rosa", "Yusuf"],), (["Hamid", "Rosa"],), (["Hamid"],), ([],)],
        prompt=(
            "Write a function `with_and(names)` that joins names the"
            " way a sentence would: 'Hamid, Rosa and Yusuf', 'Hamid and"
            " Rosa', just 'Hamid' for one, and '' for none. Join all"
            " but the last with ', ', then add ' and ' and the last.\n\n"
            "  with_and([\"Hamid\", \"Rosa\", \"Yusuf\"]) -> \"Hamid, Rosa and Yusuf\"\n\n"
            "Return: a str."
        ),
        solution=("def with_and(names):\n"
                  "    if len(names) < 2:\n"
                  "        return \"\".join(names)\n"
                  "    return \", \".join(names[:-1]) + \" and \" + names[-1]\n"),
        trap=("def with_and(names):\n"
              "    return \", \".join(names)\n"),
        note="join() puts the same separator between every pair, so"
             " the trap writes 'Hamid, Rosa, Yusuf' with no 'and'. The"
             " last name is split off with a slice and joined back with"
             " a different separator. For one name or none there is"
             " nothing to put 'and' between, and ''.join() of a short"
             " list returns the one name or the empty string.",
    ),
    dict(
        id=8, ledger="P453", concept="PY3 first character test", tier="2 - Labels",
        title="Does the name start with a vowel?", kind="function",
        func="starts_with_vowel",
        cases=[("Aisha",), ("umar",), ("Rosa",), ("",)],
        prompt=(
            "Write a function `starts_with_vowel(name)` that returns"
            " True when the name begins with a vowel, in either case,"
            " and False otherwise -- including for an empty string."
            " Guard against the empty string first, then test the first"
            " character, lower-cased, against the five vowels.\n\n"
            "  starts_with_vowel(\"Aisha\") -> True\n\n"
            "Return: True or False."
        ),
        solution=("def starts_with_vowel(name):\n"
                  "    if not name:\n"
                  "        return False\n"
                  "    return name[0].lower() in \"aeiou\"\n"),
        trap=("def starts_with_vowel(name):\n"
              "    if not name:\n"
              "        return False\n"
              "    return name[0] in \"aeiou\"\n"),
        note="'Aisha' starts with a capital A, and 'A' is not in"
             " 'aeiou', so the trap says False for her: lower() first,"
             " then test. The guard matters for another reason than the"
             " obvious one -- name[0] would raise on '', but a slice"
             " such as name[:1] would not, and '' in 'aeiou' is TRUE in"
             " Python, because the empty string is found at the start"
             " of every string. Guard first and neither trap bites.",
    ),
    dict(
        id=9, ledger="P454", concept="PY3 conditional upper", tier="2 - Labels",
        title="Shout it if it is urgent", kind="function",
        func="announce",
        cases=[("bike 7 is missing", True), ("bike 7 is missing", False), ("", True), ("all clear", False)],
        prompt=(
            "Write a function `announce(message, urgent)` that returns"
            " the message in capitals with an exclamation mark on the"
            " end when urgent is True, and the message unchanged"
            " otherwise. A conditional expression.\n\n"
            "  announce(\"bike 7 is missing\", True) -> \"BIKE 7 IS MISSING!\"\n\n"
            "Return: a str."
        ),
        solution=("def announce(message, urgent):\n"
                  "    return message.upper() + \"!\" if urgent else message\n"),
        trap=("def announce(message, urgent):\n"
              "    return message.upper() + \"!\"\n"),
        note="The flag has to be consulted: the trap shouts everything."
             " A conditional expression -- value_if_true if test else"
             " value_if_false -- reads well for a two-way choice like"
             " this. upper() leaves digits and punctuation alone, so the"
             " 7 stays a 7.",
    ),
    dict(
        id=10, ledger="P455", concept="PY3 minutes label", tier="2 - Labels",
        title="Minutes as hours and minutes", kind="function",
        func="duration_label",
        cases=[(32,), (65,), (120,), (0,)],
        prompt=(
            "Write a function `duration_label(minutes)` that returns"
            " '32 min' for under an hour and '1 h 5 min' from an hour"
            " up: whole hours by // 60 and the minutes left by % 60,"
            " with an if on whether there is an hour at all.\n\n"
            "  duration_label(65) -> \"1 h 5 min\"\n\n"
            "Return: a str."
        ),
        solution=("def duration_label(minutes):\n"
                  "    if minutes < 60:\n"
                  "        return f\"{minutes} min\"\n"
                  "    return f\"{minutes // 60} h {minutes % 60} min\"\n"),
        trap=("def duration_label(minutes):\n"
              "    return f\"{minutes // 60} h {minutes % 60} min\"\n"),
        note="The two-part label is wrong for a short ride: the trap"
             " writes '0 h 32 min'. The if chooses the shape, and the"
             " arithmetic is the same // and % pair that splits any"
             " count into a big unit and the remainder. 120 minutes"
             " gives '2 h 0 min', which the question accepts as is.",
    ),
    # ==================================================== 3 Checks and filters
    dict(
        id=11, ledger="P456", concept="PY4 split into two lists", tier="3 - Checks and filters",
        title="Short rides and long rides, sorted into two piles", kind="function",
        func="split_by_length",
        cases=[([12, 45, 30, 31, 7], 30), ([], 30), ([60, 90], 30), ([5, 10], 30)],
        prompt=(
            "Write a function `split_by_length(minutes, limit)` that"
            " returns TWO lists as a tuple: the rides of limit minutes"
            " or less, and the rides over it, each in the original"
            " order. Two comprehensions, or one loop that appends to"
            " one list or the other.\n\n"
            "  split_by_length([12, 45, 30, 31, 7], 30) -> ([12, 30, 7], [45, 31])\n\n"
            "Return: a tuple of two lists."
        ),
        solution=("def split_by_length(minutes, limit):\n"
                  "    short = [m for m in minutes if m <= limit]\n"
                  "    long = [m for m in minutes if m > limit]\n"
                  "    return short, long\n"),
        trap=("def split_by_length(minutes, limit):\n"
              "    short = [m for m in minutes if m <= limit]\n"
              "    long = [m for m in minutes if m > limit]\n"
              "    return [short, long]\n"),
        note="`return short, long` returns a tuple -- the comma makes it"
             " one, with or without brackets -- and that is what the"
             " question asks for. The trap returns a list of two lists,"
             " which holds the same values in a different container,"
             " and the grader keeps the two apart. A caller can unpack"
             " either, but a tuple says 'exactly two things' in a way a"
             " list does not.",
    ),
    dict(
        id=12, ledger="P457", concept="PY4 first and last with guard", tier="3 - Checks and filters",
        title="Where the day began and ended", kind="function",
        func="ends_of_day",
        cases=[(["Harbour", "Stadium", "Parkway"],), (["Harbour"],), ([],), (["Stadium", "Stadium"],)],
        prompt=(
            "Write a function `ends_of_day(stops)` that returns the"
            " first and last stop as a tuple, or None for a day with no"
            " stops. A guard, then indexes 0 and -1.\n\n"
            "  ends_of_day([\"Harbour\", \"Stadium\", \"Parkway\"]) -> (\"Harbour\", \"Parkway\")\n\n"
            "Return: a tuple of two str, or None."
        ),
        solution=("def ends_of_day(stops):\n"
                  "    if not stops:\n"
                  "        return None\n"
                  "    return stops[0], stops[-1]\n"),
        trap=("def ends_of_day(stops):\n"
              "    return stops[0], stops[-1]\n"),
        note="Indexing an empty list raises IndexError, which is why the"
             " guard comes first; the trap crashes on the empty day. A"
             " single stop is both the first and the last, so"
             " ('Harbour', 'Harbour') is the right answer there, and"
             " the guard lets it through because a one-item list is"
             " truthy.",
    ),
    dict(
        id=13, ledger="P458", concept="PY4 round trip check", tier="3 - Checks and filters",
        title="Was it a round trip?", kind="function",
        func="is_round_trip",
        cases=[(["Harbour", "Stadium", "Harbour"],), (["Harbour", "Stadium"],), (["Harbour"],), ([],)],
        prompt=(
            "Write a function `is_round_trip(stops)` that returns True"
            " when a day's stops begin and end at the same station and"
            " there are at least two stops, and False otherwise. Two"
            " tests joined with and, the length first.\n\n"
            "  is_round_trip([\"Harbour\", \"Stadium\", \"Harbour\"]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def is_round_trip(stops):\n"
                  "    return len(stops) >= 2 and stops[0] == stops[-1]\n"),
        trap=("def is_round_trip(stops):\n"
              "    return stops[0] == stops[-1]\n"),
        note="A single stop is equal to itself, so the trap calls"
             " ['Harbour'] a round trip, and it raises IndexError on an"
             " empty day. Putting the length test first matters: `and`"
             " stops at the first False, so stops[0] is never evaluated"
             " on a list too short to have one.",
    ),
    dict(
        id=14, ledger="P459", concept="PY4 strip and upper each", tier="3 - Checks and filters",
        title="Bike codes typed by hand, tidied", kind="function",
        func="clean_codes",
        cases=[([" bk-07 ", "BK-12", "bk-07"],), ([],), (["  BK-01  "],), (["bk-3", " Bk-3"],)],
        prompt=(
            "Codes come in from a form with stray spaces and mixed"
            " case. Write a function `clean_codes(codes)` that returns"
            " each code stripped of spaces at the ends and in capitals,"
            " in the same order, repeats kept. One comprehension"
            " applying both methods.\n\n"
            "  clean_codes([\" bk-07 \", \"BK-12\", \"bk-07\"]) -> [\"BK-07\", \"BK-12\", \"BK-07\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def clean_codes(codes):\n"
                  "    return [c.strip().upper() for c in codes]\n"),
        trap=("def clean_codes(codes):\n"
              "    return [c.upper() for c in codes]\n"),
        note="upper() changes the case and nothing else, so the trap"
             " keeps ' BK-07 ' with its spaces, which would then fail to"
             " match 'BK-07' anywhere. Chaining strip() and upper()"
             " applies both to every code, and the comprehension keeps"
             " the order and the repeats the question asks for.",
    ),
    dict(
        id=15, ledger="P460", concept="PY4 keep within a range", tier="3 - Checks and filters",
        title="Only the ids the fleet actually has", kind="function",
        func="valid_ids",
        cases=[([0, 5, 320, 321, 12], 320), ([], 320), ([1, 320], 320), ([-3, 999], 320)],
        prompt=(
            "The fleet's bike ids run from 1 to a highest id. Write a"
            " function `valid_ids(ids, highest)` that keeps only the ids"
            " in that range, in the original order. A comprehension"
            " with a chained comparison, 1 <= i <= highest.\n\n"
            "  valid_ids([0, 5, 320, 321, 12], 320) -> [5, 320, 12]\n\n"
            "Return: a list of ints."
        ),
        solution=("def valid_ids(ids, highest):\n"
                  "    return [i for i in ids if 1 <= i <= highest]\n"),
        trap=("def valid_ids(ids, highest):\n"
              "    return [i for i in ids if 1 < i < highest]\n"),
        note="The ends of the range are valid ids: bike 1 and bike 320"
             " exist, and the trap's strict comparisons throw both"
             " away. Python's chained comparison 1 <= i <= highest"
             " reads like the maths and means (1 <= i) and (i <="
             " highest).",
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
