"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-second Python set, at the easy level of the last two -- no
statistics, no dicts -- on tasks they did not cover. Counting and finding:
the stops after a station, how long the last stop was repeated, the
halfway stop, today's visits against yesterday's, names that start with a
vowel. Labels: a whole-number percentage with a guard, cents as dollars,
a name turned surname-first, minutes since midnight as a clock time, a
bulleted list. Checks and filters: the stops between two stations, legs
from one list, blanks filled in, names from a comma-separated line, a
list with one position removed.

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
        id=1, ledger="P476", concept="PY3 slice after a value", tier="1 - Counting and finding",
        title="Everywhere the bike went after Harbour", kind="function",
        func="after",
        cases=[(["Parkway", "Harbour", "Stadium", "Hilltop"], "Harbour"), (["Parkway", "Harbour"], "Harbour"), (["Parkway", "Stadium"], "Harbour"), ([], "Harbour")],
        prompt=(
            "Write a function `after(stops, station)` that returns the"
            " stops that came after the station's FIRST appearance, not"
            " including it, or [] if the station never appears. A"
            " membership test, then index() and a slice.\n\n"
            "  after([\"Parkway\", \"Harbour\", \"Stadium\", \"Hilltop\"], \"Harbour\") -> [\"Stadium\", \"Hilltop\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def after(stops, station):\n"
                  "    if station not in stops:\n"
                  "        return []\n"
                  "    return stops[stops.index(station) + 1:]\n"),
        trap=("def after(stops, station):\n"
              "    return stops[stops.index(station) + 1:]\n"),
        note="stops[i + 1:] is everything past position i, and it is"
             " [] when i was the last position, with no special case."
             " index() raises when the station is missing, so the trap"
             " crashes on a day that never reached Harbour; the `in`"
             " test first turns that into the [] the question asks for.",
    ),
    dict(
        id=2, ledger="P477", concept="PY4 run at the end", tier="1 - Counting and finding",
        title="How long the bike sat at its last stop", kind="function",
        func="final_streak",
        cases=[(["Harbour", "Stadium", "Stadium", "Stadium"],), (["Stadium", "Harbour", "Stadium"],), (["Harbour"],), ([],)],
        prompt=(
            "Write a function `final_streak(stops)` that returns how"
            " many times the LAST stop is repeated at the end of the"
            " list, in a row -- 3 for a list ending Stadium, Stadium,"
            " Stadium -- and 0 for an empty list. A loop backwards from"
            " the end that stops at the first different stop.\n\n"
            "  final_streak([\"Harbour\", \"Stadium\", \"Stadium\", \"Stadium\"]) -> 3\n\n"
            "Return: an int."
        ),
        solution=("def final_streak(stops):\n"
                  "    n = 0\n"
                  "    for s in reversed(stops):\n"
                  "        if stops and s == stops[-1]:\n"
                  "            n += 1\n"
                  "        else:\n"
                  "            break\n"
                  "    return n\n"),
        trap=("def final_streak(stops):\n"
              "    if not stops:\n"
              "        return 0\n"
              "    return stops.count(stops[-1])\n"),
        note="count() counts the last stop everywhere in the day, not"
             " only at the end: the trap says 2 for a day that went"
             " Stadium, Harbour, Stadium, where the final run is one."
             " Walking backwards with reversed() and breaking at the"
             " first stop that differs counts just the run; an empty"
             " list never enters the loop and returns 0.",
    ),
    dict(
        id=3, ledger="P478", concept="PY3 middle item with guard", tier="1 - Counting and finding",
        title="The halfway stop", kind="function",
        func="halfway",
        cases=[(["Harbour", "Stadium", "Parkway"],), (["Harbour", "Stadium", "Parkway", "Hilltop"],), (["Harbour"],), ([],)],
        prompt=(
            "Write a function `halfway(stops)` that returns the stop in"
            " the middle of the day -- position len // 2, which for an"
            " even count is the later of the two middle stops -- or"
            " None for an empty list.\n\n"
            "  halfway([\"Harbour\", \"Stadium\", \"Parkway\"]) -> \"Stadium\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def halfway(stops):\n"
                  "    if not stops:\n"
                  "        return None\n"
                  "    return stops[len(stops) // 2]\n"),
        trap=("def halfway(stops):\n"
              "    return stops[len(stops) // 2]\n"),
        note="len // 2 is the middle index for an odd count and the"
             " later middle for an even one, which is what the question"
             " fixes so that there is one right answer. For an empty"
             " list the index is 0 and there is nothing at 0: the trap"
             " raises IndexError where None was asked for.",
    ),
    dict(
        id=4, ledger="P479", concept="PY3 difference of two counts", tier="1 - Counting and finding",
        title="More visits today than yesterday?", kind="function",
        func="visits_change",
        cases=[(["Harbour", "Harbour", "Stadium"], ["Harbour"], "Harbour"), (["Stadium"], ["Harbour", "Harbour"], "Harbour"), ([], [], "Harbour"), (["Harbour"], ["Harbour"], "Harbour")],
        prompt=(
            "Write a function `visits_change(today, yesterday,"
            " station)` that returns how many more times the station"
            " was visited today than yesterday -- negative if fewer."
            " Two count() calls and a subtraction, today's first.\n\n"
            "  visits_change([\"Harbour\", \"Harbour\", \"Stadium\"], [\"Harbour\"], \"Harbour\") -> 1\n\n"
            "Return: an int."
        ),
        solution=("def visits_change(today, yesterday, station):\n"
                  "    return today.count(station) - yesterday.count(station)\n"),
        trap=("def visits_change(today, yesterday, station):\n"
              "    return yesterday.count(station) - today.count(station)\n"),
        note="'How many more today' is today minus yesterday; the trap"
             " subtracts the other way and reports a rise as a fall."
             " count() on a list that lacks the station is 0, so the"
             " empty days need no guard.",
    ),
    dict(
        id=5, ledger="P480", concept="PY4 count by first letter", tier="1 - Counting and finding",
        title="How many names start with a vowel", kind="function",
        func="vowel_names",
        cases=[(["Aisha", "Umar", "Rosa", "Eleanor"],), (["rosa", "zara"],), ([],), (["Imogen", ""],)],
        prompt=(
            "Write a function `vowel_names(names)` that returns how"
            " many of the names begin with a vowel, in either case; an"
            " empty string does not count. A sum over a generator that"
            " tests the first character lower-cased, with a guard for"
            " the empty string.\n\n"
            "  vowel_names([\"Aisha\", \"Umar\", \"Rosa\", \"Eleanor\"]) -> 3\n\n"
            "Return: an int."
        ),
        solution=("def vowel_names(names):\n"
                  "    return sum(1 for n in names if n and n[0].lower() in \"aeiou\")\n"),
        trap=("def vowel_names(names):\n"
              "    return sum(1 for n in names if n and n[0] in \"aeiou\")\n"),
        note="Names are capitalised, and 'A' is not in 'aeiou': the"
             " trap counts none of Aisha, Umar and Eleanor. lower()"
             " first, then test. The `n and` guard runs before n[0], so"
             " an empty string is skipped rather than raising, because"
             " `and` stops at the first false value.",
    ),
    # ================================================================ 2 Labels
    dict(
        id=6, ledger="P481", concept="PY3 whole percentage with guard", tier="2 - Labels",
        title="A percentage, rounded, as a label", kind="function",
        func="percent_label",
        cases=[(2, 3), (1, 4), (0, 5), (3, 0)],
        prompt=(
            "Write a function `percent_label(part, whole)` that returns"
            " the share as a whole-number percentage with a percent"
            " sign, '67%' for 2 of 3, or 'n/a' when the whole is 0."
            " round() to no decimals, inside an f-string.\n\n"
            "  percent_label(2, 3) -> \"67%\"\n\n"
            "Return: a str."
        ),
        solution=("def percent_label(part, whole):\n"
                  "    if whole == 0:\n"
                  "        return \"n/a\"\n"
                  "    return f\"{round(100 * part / whole)}%\"\n"),
        trap=("def percent_label(part, whole):\n"
              "    if whole == 0:\n"
              "        return \"n/a\"\n"
              "    return f\"{int(100 * part / whole)}%\"\n"),
        note="int() truncates towards zero, so 66.67 becomes 66 and the"
             " trap labels two thirds as '66%'; round() gives 67. The"
             " guard comes first because 100 * part / 0 raises before"
             " any rounding could happen. A '%' inside an f-string's"
             " text is just a character.",
    ),
    dict(
        id=7, ledger="P482", concept="PY3 cents to dollars text", tier="2 - Labels",
        title="Cents as dollars on a receipt", kind="function",
        func="dollars",
        cases=[(350,), (1200,), (5,), (0,)],
        prompt=(
            "Write a function `dollars(cents)` that returns the amount"
            " as '$3.50': a dollar sign, the whole dollars, a point, and"
            " the cents left over always as two digits. // and % give"
            " the two parts; a format spec pads the second.\n\n"
            "  dollars(350) -> \"$3.50\"\n\n"
            "Return: a str."
        ),
        solution=("def dollars(cents):\n"
                  "    return f\"${cents // 100}.{cents % 100:02d}\"\n"),
        trap=("def dollars(cents):\n"
              "    return f\"${cents / 100}\"\n"),
        note="cents / 100 is a float, and a float prints as 3.5, not"
             " 3.50, and 0.05 for five cents: the trap's receipts have"
             " the wrong number of digits. Splitting into dollars and"
             " cents with // and % keeps everything an int, and :02d pads"
             " the cents to two digits with a leading zero when needed.",
    ),
    dict(
        id=8, ledger="P483", concept="PY3 surname first", tier="2 - Labels",
        title="A name the way the register writes it", kind="function",
        func="register_name",
        cases=[("Hamid Uddin",), ("Ana de la Cruz",), ("Cher",), ("Rosa Villanueva",)],
        prompt=(
            "Write a function `register_name(name)` that turns 'Hamid"
            " Uddin' into 'Uddin, Hamid': the LAST word first, a comma"
            " and a space, then everything before it. A one-word name"
            " is returned unchanged. split(), a slice, and join().\n\n"
            "  register_name(\"Hamid Uddin\") -> \"Uddin, Hamid\"\n\n"
            "Return: a str."
        ),
        solution=("def register_name(name):\n"
                  "    words = name.split()\n"
                  "    if len(words) < 2:\n"
                  "        return name\n"
                  "    return words[-1] + \", \" + \" \".join(words[:-1])\n"),
        trap=("def register_name(name):\n"
              "    words = name.split()\n"
              "    return words[1] + \", \" + words[0]\n"),
        note="words[1] is the SECOND word, which is the surname only"
             " for a two-word name: the trap turns 'Ana de la Cruz' into"
             " 'de, Ana' and crashes on 'Cher'. words[-1] is the last"
             " word whatever the count, words[:-1] is everything before"
             " it, and ' '.join puts the spaces back. The one-word guard"
             " handles the name with nothing to turn round.",
    ),
    dict(
        id=9, ledger="P484", concept="PY3 minutes to clock text", tier="2 - Labels",
        title="Minutes since midnight as a clock time", kind="function",
        func="clock",
        cases=[(485,), (0,), (1439,), (600,)],
        prompt=(
            "Write a function `clock(minutes)` that turns minutes since"
            " midnight into 'HH:MM' with both parts two digits: 485 is"
            " '08:05'. divmod() by 60 gives hours and minutes at once;"
            " a format spec pads each.\n\n"
            "  clock(485) -> \"08:05\"\n\n"
            "Return: a str."
        ),
        solution=("def clock(minutes):\n"
                  "    h, m = divmod(minutes, 60)\n"
                  "    return f\"{h:02d}:{m:02d}\"\n"),
        trap=("def clock(minutes):\n"
              "    h, m = divmod(minutes, 60)\n"
              "    return f\"{h}:{m}\"\n"),
        note="A clock pads with zeros: '8:5' is not a time. The :02d"
             " spec means 'at least two digits, zero-filled', and it"
             " applies to each part separately. divmod(485, 60) is (8,"
             " 5) in one call, the same pair as 485 // 60 and 485 % 60.",
    ),
    dict(
        id=10, ledger="P485", concept="PY3 join with prefix", tier="2 - Labels",
        title="A bulleted list of names", kind="function",
        func="bulleted",
        cases=[(["Hamid", "Rosa"],), (["Yusuf"],), ([],)],
        prompt=(
            "Write a function `bulleted(names)` that returns the names"
            " as a bulleted list in one string: each name on its own"
            " line, starting with '- ', lines separated by newlines and"
            " no newline at the end; '' for no names. A comprehension"
            " to add the dash, then '\\n'.join.\n\n"
            "  bulleted([\"Hamid\", \"Rosa\"]) -> \"- Hamid\\n- Rosa\"\n\n"
            "Return: a str."
        ),
        solution=("def bulleted(names):\n"
                  "    return \"\\n\".join(\"- \" + n for n in names)\n"),
        trap=("def bulleted(names):\n"
              "    return \"\\n\".join(names)\n"),
        note="join() puts the separator BETWEEN items, never before the"
             " first or after the last, which is why there is no"
             " trailing newline and why the dash has to be added to"
             " each name before joining: the trap's lines have no"
             " bullets. join() of nothing is '', which is the empty"
             " case for free.",
    ),
    # ==================================================== 3 Checks and filters
    dict(
        id=11, ledger="P486", concept="PY3 slice between two values", tier="3 - Checks and filters",
        title="The stops between Harbour and Stadium", kind="function",
        func="between",
        cases=[(["Parkway", "Harbour", "Hilltop", "Riverside", "Stadium", "Parkway"], "Harbour", "Stadium"), (["Harbour", "Stadium"], "Harbour", "Stadium"), (["Harbour", "Hilltop"], "Harbour", "Stadium"), (["Stadium", "Hilltop", "Harbour"], "Harbour", "Stadium")],
        prompt=(
            "Write a function `between(stops, a, b)` that returns the"
            " stops strictly between the first a and the first b --"
            " neither included -- and [] when either is missing or b"
            " comes before a. Two index() calls and one slice, after"
            " the checks.\n\n"
            "  between([\"Parkway\", \"Harbour\", \"Hilltop\", \"Riverside\", \"Stadium\", \"Parkway\"], \"Harbour\", \"Stadium\") -> [\"Hilltop\", \"Riverside\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def between(stops, a, b):\n"
                  "    if a not in stops or b not in stops:\n"
                  "        return []\n"
                  "    i, j = stops.index(a), stops.index(b)\n"
                  "    return stops[i + 1:j]\n"),
        trap=("def between(stops, a, b):\n"
              "    if a not in stops or b not in stops:\n"
              "        return []\n"
              "    return stops[stops.index(a):stops.index(b)]\n"),
        note="A slice starts AT its first index and stops BEFORE its"
             " second, so stops[i:j] includes a and excludes b -- the"
             " trap returns Harbour with the answer. Starting at i + 1"
             " excludes both ends. When b comes before a the slice is"
             " empty by itself, since a start past the stop gives [].",
    ),
    dict(
        id=12, ledger="P487", concept="PY3 zip with an offset", tier="3 - Checks and filters",
        title="The legs of a day, from one list", kind="function",
        func="legs_of",
        cases=[(["Harbour", "Stadium", "Parkway"],), (["Harbour", "Stadium"],), (["Harbour"],), ([],)],
        prompt=(
            "Write a function `legs_of(stops)` that returns one string"
            " per leg between consecutive stops, 'Harbour -> Stadium',"
            " from a single list of stops; one stop or none gives []."
            " zip the list with itself shifted by one.\n\n"
            "  legs_of([\"Harbour\", \"Stadium\", \"Parkway\"]) -> [\"Harbour -> Stadium\", \"Stadium -> Parkway\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def legs_of(stops):\n"
                  "    return [f\"{a} -> {b}\" for a, b in zip(stops, stops[1:])]\n"),
        trap=("def legs_of(stops):\n"
              "    return [f\"{a} -> {b}\" for a, b in zip(stops, stops)]\n"),
        note="zip(stops, stops[1:]) pairs each stop with the NEXT one,"
             " because the second list starts one position later and"
             " zip stops at the shorter, so a list of n stops gives n -"
             " 1 legs and a list of one gives none. zip(stops, stops),"
             " the trap, pairs each stop with itself: 'Harbour ->"
             " Harbour'.",
    ),
    dict(
        id=13, ledger="P488", concept="PY3 fill blanks", tier="3 - Checks and filters",
        title="Blanks in the log filled in", kind="function",
        func="fill_blanks",
        cases=[(["Harbour", "", "Stadium", ""], "unknown"), ([], "unknown"), (["", ""], "?"), (["Harbour"], "unknown")],
        prompt=(
            "Some stops were left blank -- an empty string. Write a"
            " function `fill_blanks(stops, default)` that returns the"
            " list with every empty string replaced by the default and"
            " everything else unchanged. A comprehension with a"
            " conditional expression, or with `or`.\n\n"
            "  fill_blanks([\"Harbour\", \"\", \"Stadium\", \"\"], \"unknown\") -> [\"Harbour\", \"unknown\", \"Stadium\", \"unknown\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def fill_blanks(stops, default):\n"
                  "    return [s if s else default for s in stops]\n"),
        trap=("def fill_blanks(stops, default):\n"
              "    return [s if s is not None else default for s in stops]\n"),
        note="An empty string is not None, so the trap's test never"
             " fires and the blanks stay blank. `s if s else default`"
             " uses the empty string's falsiness, and `s or default` is"
             " the same thing shorter. Either builds a new list and"
             " leaves the caller's alone.",
    ),
    dict(
        id=14, ledger="P489", concept="PY3 split on comma and strip", tier="3 - Checks and filters",
        title="Names from a comma-separated line", kind="function",
        func="names_from",
        cases=[("Hamid, Rosa,Yusuf , Zara",), ("Hamid",), ("",), (" Rosa , ",)],
        prompt=(
            "A form sends names as one line, 'Hamid, Rosa,Yusuf ,"
            " Zara', with the spacing all over the place. Write a"
            " function `names_from(line)` that returns the names as a"
            " list, each stripped of spaces, empty pieces dropped. split"
            " on the comma, then strip, then keep the non-empty ones.\n\n"
            "  names_from(\"Hamid, Rosa,Yusuf , Zara\") -> [\"Hamid\", \"Rosa\", \"Yusuf\", \"Zara\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def names_from(line):\n"
                  "    return [p.strip() for p in line.split(\",\") if p.strip()]\n"),
        trap=("def names_from(line):\n"
              "    return line.split(\",\")\n"),
        note="split(',') keeps whatever surrounded each comma, so the"
             " trap returns ' Rosa' and 'Yusuf ' with their spaces, and"
             " a trailing comma gives an empty last piece. strip() on"
             " each piece and an if that drops the empty ones make the"
             " list clean, and ''.split(',') is [''], which the if"
             " turns into [].",
    ),
    dict(
        id=15, ledger="P490", concept="PY3 remove by position on a copy", tier="3 - Checks and filters",
        title="A stop struck out", kind="function",
        func="without_position",
        cases=[(["Harbour", "Stadium", "Parkway"], 1), (["Harbour", "Stadium", "Parkway"], 0), (["Harbour", "Stadium", "Parkway"], 7), ([], 0)],
        prompt=(
            "Write a function `without_position(stops, i)` that returns"
            " a NEW list with the stop at position i left out, or an"
            " unchanged copy if there is no such position. Two slices"
            " joined: everything before i and everything after it.\n\n"
            "  without_position([\"Harbour\", \"Stadium\", \"Parkway\"], 1) -> [\"Harbour\", \"Parkway\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def without_position(stops, i):\n"
                  "    return stops[:i] + stops[i + 1:]\n"),
        trap=("def without_position(stops, i):\n"
              "    return stops[:i] + stops[i:]\n"),
        note="stops[:i] ends before position i and stops[i + 1:] begins"
             " after it, so joining them skips exactly one item. The"
             " trap's second slice begins AT i and keeps the stop it was"
             " meant to drop, returning the list unchanged. A position"
             " past the end makes both slices harmless -- all of the"
             " list, then nothing -- so no guard is needed, and the"
             " caller's list is never touched.",
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
