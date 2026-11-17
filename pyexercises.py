"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-ninth Python set, at the easy level of the last nine -- no
statistics, no dicts -- in the courier's terms, on tasks the earlier sets
did not cover. Text, tidied: spacing put right, a first letter
capitalised and nothing else touched, the digits of a phone number, a
note in brackets, a heading underlined. Checks and searches: a code that
starts with any of several prefixes, names containing a search term in
any case, a clock time that is really a time, the last place a value
appears, a form with a blank field. Lists, built and reshaped: bay
numbers from a range written as text, pairs separated into two lists,
two lists merged without repeats, a value removed everywhere, every nth
item.

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
    # ========================================================= 1 Text, tidied
    dict(
        id=1, ledger="P581", concept="PY3 collapse runs of spaces", tier="1 - Text, tidied",
        title="A label with its spacing put right", kind="function",
        func="tidy_spaces",
        cases=[("  Central   Hub ",), ("Old Foundry",), ("",), ("a  b   c",), ("   ",)],
        prompt=(
            "Write a function `tidy_spaces(label)` that returns the"
            " label with no spaces at either end and exactly one space"
            " between words, however many were typed. split() with no"
            " argument, then join.\n\n"
            "  tidy_spaces(\"  Central   Hub \") -> \"Central Hub\"\n\n"
            "Return: a str."
        ),
        solution=("def tidy_spaces(label):\n"
                  "    return \" \".join(label.split())\n"),
        trap=("def tidy_spaces(label):\n"
              "    return label.strip()\n"),
        note="split() with no argument breaks on any run of whitespace"
             " and ignores it at the ends, so what comes back is just"
             " the words; joining them with one space rebuilds the"
             " label the way it should have been typed. strip(), the"
             " trap, only cleans the two ends and leaves 'Central   Hub'"
             " with its three spaces. replace('  ', ' ') is no better:"
             " it halves a run of spaces, it does not remove it.",
    ),
    dict(
        id=2, ledger="P582", concept="PY3 capitalise the first letter only", tier="1 - Text, tidied",
        title="A first letter capitalised, the rest left alone", kind="function",
        func="start_capital",
        cases=[("deliver to Central Hub",), ("urgent: call NG5 depot",), ("",), ("a",), ("Already fine",)],
        prompt=(
            "Write a function `start_capital(text)` that returns the"
            " text with its first character in upper case and every"
            " other character exactly as it was. The empty string"
            " comes back empty. Two slices.\n\n"
            "  start_capital(\"deliver to Central Hub\") -> \"Deliver to Central Hub\"\n\n"
            "Return: a str."
        ),
        solution=("def start_capital(text):\n"
                  "    return text[:1].upper() + text[1:]\n"),
        trap=("def start_capital(text):\n"
              "    return text.capitalize()\n"),
        note="capitalize(), the trap, sounds like the answer and does"
             " two things: it raises the first letter and LOWERS all"
             " the rest, so 'Central Hub' becomes 'central hub' and"
             " 'NG5' becomes 'ng5'. Slicing touches only what you"
             " name. text[:1] rather than text[0] is what makes the"
             " empty string safe: a slice of nothing is an empty"
             " string, where an index would raise.",
    ),
    dict(
        id=3, ledger="P583", concept="PY3 keep only the digits", tier="1 - Text, tidied",
        title="Just the digits of a phone number", kind="function",
        func="digits_only",
        cases=[("0115 496-0123",), ("(020) 7946 0018",), ("",), ("no digits",), ("42",)],
        prompt=(
            "Phone numbers arrive with spaces, hyphens and brackets."
            " Write a function `digits_only(text)` that returns only"
            " the digits, in order, as one string. A string has a"
            " method that says whether it is a digit.\n\n"
            "  digits_only(\"0115 496-0123\") -> \"01154960123\"\n\n"
            "Return: a str."
        ),
        solution=("def digits_only(text):\n"
                  "    return \"\".join(ch for ch in text if ch.isdigit())\n"),
        trap=("def digits_only(text):\n"
              "    return text.replace(\" \", \"\")\n"),
        note="Say what to KEEP, not what to remove: a loop over the"
             " characters that keeps the ones where isdigit() is true"
             " copes with any punctuation anyone ever types. The trap"
             " removes spaces and leaves the hyphen and the brackets;"
             " adding a replace for each of those only waits for the"
             " next surprise, a dot or a plus. The result stays a"
             " string on purpose: as a number, the leading 0 would be"
             " lost.",
    ),
    dict(
        id=4, ledger="P584", concept="PY3 text between two markers", tier="1 - Text, tidied",
        title="The note in brackets", kind="function",
        func="in_brackets",
        cases=[("Parcel 12 (fragile) for Northgate",), ("No note here",), ("(urgent)",), ("Leave with neighbour (no. 4) or (shed)",), ("()",)],
        prompt=(
            "Write a function `in_brackets(text)` that returns what is"
            " between the first '(' and the ')' that follows it, not"
            " including the brackets. If there is no '(' the answer is"
            " the empty string. find() returns a position, or -1.\n\n"
            "  in_brackets(\"Parcel 12 (fragile) for Northgate\") -> \"fragile\"\n\n"
            "Return: a str."
        ),
        solution=("def in_brackets(text):\n"
                  "    start = text.find(\"(\")\n"
                  "    if start == -1:\n"
                  "        return \"\"\n"
                  "    end = text.find(\")\", start)\n"
                  "    return text[start + 1:end]\n"),
        trap=("def in_brackets(text):\n"
              "    return text[text.find(\"(\") + 1:text.find(\")\")]\n"),
        note="find() does not raise when it finds nothing; it returns"
             " -1, and -1 is a perfectly good index, which is the"
             " danger. With no brackets the trap slices from -1 + 1 to"
             " -1 and returns the whole text minus its last character:"
             " 'No note her'. Test for -1 before using the position."
             " The second find starts looking at `start`, so it cannot"
             " be fooled by a ')' that comes before the '('.",
    ),
    dict(
        id=5, ledger="P585", concept="PY3 repeat a character to a length", tier="1 - Text, tidied",
        title="A heading, underlined", kind="function",
        func="underlined",
        cases=[("Northgate",), ("Old Foundry",), ("",), ("A",)],
        prompt=(
            "Write a function `underlined(title)` that returns the"
            " title, a newline, and then a row of '=' signs exactly as"
            " long as the title. A string times a number repeats"
            " it.\n\n"
            "  underlined(\"Northgate\") -> \"Northgate\\n=========\"\n\n"
            "Return: a str, with one newline in it (written \\n above)."
        ),
        solution=("def underlined(title):\n"
                  "    return title + \"\\n\" + \"=\" * len(title)\n"),
        trap=("def underlined(title):\n"
              "    return title + \"\\n\" + \"=\" * 10\n"),
        note="\"=\" * len(title) makes the rule as long as the text"
             " above it, whatever the text is; the trap's fixed ten is"
             " right for exactly one length of title. Return the"
             " string rather than printing it: whoever calls the"
             " function decides where it goes, and \\n inside a"
             " string becomes a line break only when it is printed."
             " An empty title gives an empty underline, with no"
             " special case.",
    ),
    # ================================================ 2 Checks and searches
    dict(
        id=6, ledger="P586", concept="PY3 startswith a tuple", tier="2 - Checks and searches",
        title="Does the code belong to one of our depots?", kind="function",
        func="has_prefix",
        cases=[("NGT-0042", ["MB", "NGT", "CH"]), ("NG-0042", ["MB", "NGT", "CH"]), ("CH-7", ["MB", "NGT", "CH"]), ("CH-7", []), ("X", ["XY"])],
        prompt=(
            "Write a function `has_prefix(code, prefixes)` that"
            " returns True if the code starts with ANY of the prefixes"
            " in the list. The prefixes are not all the same length."
            " startswith accepts several candidates at once, as a"
            " tuple.\n\n"
            "  has_prefix(\"NGT-0042\", [\"MB\", \"NGT\", \"CH\"]) -> True\n"
            "  has_prefix(\"NG-0042\", [\"MB\", \"NGT\", \"CH\"]) -> False\n\n"
            "Return: a bool."
        ),
        solution=("def has_prefix(code, prefixes):\n"
                  "    return code.startswith(tuple(prefixes))\n"),
        trap=("def has_prefix(code, prefixes):\n"
              "    return code[:2] in prefixes\n"),
        note="startswith takes a tuple and answers True if any member"
             " matches, each at its own length -- it will not take a"
             " list, hence tuple(). The trap cuts two characters off"
             " the code and looks them up, which works until a prefix"
             " is three letters long: 'NGT-0042' is cut to 'NG', which"
             " is on nobody's list. any(code.startswith(p) for p in"
             " prefixes) is the same answer spelled out.",
    ),
    dict(
        id=7, ledger="P587", concept="PY3 search ignoring case", tier="2 - Checks and searches",
        title="Names that contain the search term", kind="function",
        func="matching",
        cases=[(["Yilmaz Bicycles", "Achebe Bakery Direct", "Okonjo BAKERY Ltd"], "bakery"), (["Northgate"], "GATE"), ([], "x"), (["abc", "ABC", "xyz"], "B"), (["abc"], "")],
        prompt=(
            "Write a function `matching(names, term)` that returns the"
            " names containing the search term, in their original"
            " order and spelling. Capitals make no difference, in the"
            " names or in the term.\n\n"
            "  matching([\"Yilmaz Bicycles\", \"Achebe Bakery Direct\", \"Okonjo BAKERY Ltd\"], \"bakery\") -> [\"Achebe Bakery Direct\", \"Okonjo BAKERY Ltd\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def matching(names, term):\n"
                  "    return [name for name in names if term.lower() in name.lower()]\n"),
        trap=("def matching(names, term):\n"
              "    return [name for name in names if term in name]\n"),
        note="`in` between two strings asks whether one appears inside"
             " the other, and it is exact about case: 'bakery' is not"
             " in 'Achebe Bakery Direct'. Lower both sides for the"
             " comparison only -- the list is built from `name`, not"
             " from the lowered copy, so every match comes back as it"
             " was written. The trap compares as typed and finds"
             " nothing at all for a lower-case search.",
    ),
    dict(
        id=8, ledger="P588", concept="PY4 validate a clock time", tier="2 - Checks and searches",
        title="Is that really a time?", kind="function",
        func="valid_time",
        cases=[("23:59",), ("00:00",), ("24:00",), ("14:65",), ("9:30",), ("ab:cd",), ("1234",), ("12:3x",)],
        prompt=(
            "Write a function `valid_time(text)` that returns True"
            " only for a real 24-hour clock time written 'HH:MM': five"
            " characters, a colon in the middle, two digits either"
            " side, hours 00 to 23 and minutes 00 to 59. Check the"
            " shape first, the numbers second.\n\n"
            "  valid_time(\"23:59\") -> True\n"
            "  valid_time(\"14:65\") -> False\n"
            "  valid_time(\"9:30\") -> False\n\n"
            "Return: a bool."
        ),
        solution=("def valid_time(text):\n"
                  "    if len(text) != 5 or text[2] != \":\":\n"
                  "        return False\n"
                  "    hours, minutes = text[:2], text[3:]\n"
                  "    if not (hours.isdigit() and minutes.isdigit()):\n"
                  "        return False\n"
                  "    return int(hours) < 24 and int(minutes) < 60\n"),
        trap=("def valid_time(text):\n"
              "    if len(text) != 5 or text[2] != \":\":\n"
              "        return False\n"
              "    return text[:2].isdigit() and text[3:].isdigit()\n"),
        note="Each check makes the next one safe: the length test"
             " means text[2] exists, the isdigit tests mean int()"
             " cannot raise, and only then are the numbers compared."
             " The trap stops after the shape, so anything that LOOKS"
             " like a time passes: 24:00, 14:65, 99:99. Returning"
             " False early, one reason at a time, reads better than"
             " one long condition and fails in the right order.",
    ),
    dict(
        id=9, ledger="P589", concept="PY4 last position of a value", tier="2 - Checks and searches",
        title="The last time the parcel was on a van", kind="function",
        func="last_position",
        cases=[(["van", "depot", "van", "door"], "van"), (["van"], "van"), (["van", "depot"], "door"), ([], "x"), (["a", "a", "a"], "a")],
        prompt=(
            "Write a function `last_position(items, value)` that"
            " returns the position, counting from 0, of the LAST item"
            " equal to value, or -1 if there is none. A range can"
            " count downwards.\n\n"
            "  last_position([\"van\", \"depot\", \"van\", \"door\"], \"van\") -> 2\n\n"
            "Return: an int."
        ),
        solution=("def last_position(items, value):\n"
                  "    for i in range(len(items) - 1, -1, -1):\n"
                  "        if items[i] == value:\n"
                  "            return i\n"
                  "    return -1\n"),
        trap=("def last_position(items, value):\n"
              "    if value in items:\n"
              "        return items.index(value)\n"
              "    return -1\n"),
        note="range(len(items) - 1, -1, -1) starts at the last"
             " position and steps down to 0 -- the stop value, -1, is"
             " never reached -- so the first match met is the last one"
             " in the list, and the function can return at once."
             " index(), the trap, always finds the FIRST match: 0"
             " instead of 2. Lists have no rindex; strings do, which"
             " is why this one has to be written out.",
    ),
    dict(
        id=10, ledger="P590", concept="PY3 any with strip", tier="2 - Checks and searches",
        title="Is any field on the form blank?", kind="function",
        func="any_blank",
        cases=[(["Rosa Baxter", "  ", "NG7"],), (["Rosa Baxter", "NG7"],), ([],), ([""],), (["a", "\t"],)],
        prompt=(
            "Write a function `any_blank(fields)` that returns True if"
            " any field in the list is blank. A field holding only"
            " spaces is as blank as an empty one. An empty form has"
            " no blank fields. any(), over a test on each field.\n\n"
            "  any_blank([\"Rosa Baxter\", \"  \", \"NG7\"]) -> True\n\n"
            "Return: a bool."
        ),
        solution=("def any_blank(fields):\n"
                  "    return any(not field.strip() for field in fields)\n"),
        trap=("def any_blank(fields):\n"
              "    return \"\" in fields\n"),
        note="strip() removes spaces from both ends, so a field of"
             " nothing but spaces becomes the empty string, and an"
             " empty string counts as False: `not field.strip()` is"
             " the whole test for blank. any() stops at the first True"
             " and gives False for an empty list. The trap looks for a"
             " field that is exactly empty and lets through the one"
             " somebody filled in with the space bar.",
    ),
    # ============================================ 3 Lists, built and reshaped
    dict(
        id=11, ledger="P591", concept="PY3 expand a text range", tier="3 - Lists, built and reshaped",
        title="Bay numbers from a range on the rota", kind="function",
        func="bay_numbers",
        cases=[("3-6",), ("4",), ("10-12",), ("7-7",)],
        prompt=(
            "The rota gives bays as text: either one number, '4', or a"
            " first and a last with a hyphen, '3-6'. Write a function"
            " `bay_numbers(text)` that returns every bay meant, as a"
            " list of ints, both ends included.\n\n"
            "  bay_numbers(\"3-6\") -> [3, 4, 5, 6]\n"
            "  bay_numbers(\"4\") -> [4]\n\n"
            "Return: a list of int."
        ),
        solution=("def bay_numbers(text):\n"
                  "    parts = text.split(\"-\")\n"
                  "    first, last = int(parts[0]), int(parts[-1])\n"
                  "    return list(range(first, last + 1))\n"),
        trap=("def bay_numbers(text):\n"
              "    parts = text.split(\"-\")\n"
              "    first, last = int(parts[0]), int(parts[-1])\n"
              "    return list(range(first, last))\n"),
        note="range stops BEFORE its second argument, so a range that"
             " includes its last number needs last + 1. The trap"
             " leaves bay 6 out of '3-6' and returns nothing at all"
             " for a single bay. parts[0] and parts[-1] are the same"
             " item when there is no hyphen, which is how one line"
             " handles both ways of writing it without an if.",
    ),
    dict(
        id=12, ledger="P592", concept="PY3 pairs into two lists", tier="3 - Lists, built and reshaped",
        title="Codes in one list, postage in another", kind="function",
        func="unzip",
        cases=[([["MB-2", 410], ["CH-7", 1200], ["WW-1", 590]],), ([],), ([["A-1", 5]],)],
        prompt=(
            "A batch is a list of [code, cents] pairs. Write a"
            " function `unzip(pairs)` that returns two LISTS, the"
            " codes and the cents, each in the original order. An"
            " empty batch gives two empty lists.\n\n"
            "  unzip([[\"MB-2\", 410], [\"CH-7\", 1200]]) -> ([\"MB-2\", \"CH-7\"], [410, 1200])\n\n"
            "Return: a tuple of two lists."
        ),
        solution=("def unzip(pairs):\n"
                  "    codes = [pair[0] for pair in pairs]\n"
                  "    cents = [pair[1] for pair in pairs]\n"
                  "    return codes, cents\n"),
        trap=("def unzip(pairs):\n"
              "    return list(zip(*pairs))\n"),
        note="Two comprehensions, one per column, and `return a, b`"
             " hands both back as a tuple the caller can unpack:"
             " codes, cents = unzip(batch). zip(*pairs), the trap, is"
             " the well-known shortcut and has two catches: it gives"
             " tuples where lists were asked for, and for an empty"
             " batch it gives nothing at all -- no columns, so no two"
             " lists to unpack, and the caller's line raises.",
    ),
    dict(
        id=13, ledger="P593", concept="PY4 merge two lists without repeats", tier="3 - Lists, built and reshaped",
        title="Two manifests, merged", kind="function",
        func="merged",
        cases=[(["A-1", "B-2"], ["B-2", "C-3", "A-1", "D-4"]), (["A-1", "A-1"], ["A-1"]), ([], ["x", "x", "y"]), ([], []), (["a"], [])],
        prompt=(
            "Write a function `merged(first, second)` that returns one"
            " list holding every code from both lists exactly once:"
            " first's codes in order, then any from second not seen"
            " yet. A code repeated inside either list still appears"
            " once.\n\n"
            "  merged([\"A-1\", \"B-2\"], [\"B-2\", \"C-3\", \"A-1\", \"D-4\"]) -> [\"A-1\", \"B-2\", \"C-3\", \"D-4\"]\n\n"
            "Return: a list."
        ),
        solution=("def merged(first, second):\n"
                  "    out = []\n"
                  "    for code in first + second:\n"
                  "        if code not in out:\n"
                  "            out.append(code)\n"
                  "    return out\n"),
        trap=("def merged(first, second):\n"
              "    return first + [code for code in second if code not in first]\n"),
        note="Testing each code against `out`, the list being built,"
             " catches every kind of repeat: across the two lists and"
             " inside either one. The trap tests second's codes"
             " against first only, so a code that appears twice in"
             " second gets in twice, and first's own repeats are never"
             " looked at. first + second makes a new list, so neither"
             " argument is changed. A set would remove the repeats and"
             " the order with them.",
    ),
    dict(
        id=14, ledger="P594", concept="PY3 remove every occurrence", tier="3 - Lists, built and reshaped",
        title="A status struck from the trail, everywhere", kind="function",
        func="without",
        cases=[(["van", "depot", "van", "door"], "van"), (["depot"], "van"), ([], "van"), (["van", "van"], "van")],
        prompt=(
            "Write a function `without(items, value)` that returns a"
            " NEW list with every item equal to value left out, and"
            " the rest in order. The list passed in is not changed.\n\n"
            "  without([\"van\", \"depot\", \"van\", \"door\"], \"van\") -> [\"depot\", \"door\"]\n\n"
            "Return: a list."
        ),
        solution=("def without(items, value):\n"
                  "    return [item for item in items if item != value]\n"),
        trap=("def without(items, value):\n"
              "    out = list(items)\n"
              "    if value in out:\n"
              "        out.remove(value)\n"
              "    return out\n"),
        note="A comprehension with an if at the end is a filter: it"
             " builds a new list from the items that pass, so there is"
             " no question of how many to remove or of changing the"
             " original. remove(), the trap, takes out the FIRST match"
             " and stops, leaving the second 'van' in place; calling"
             " it in a loop while you walk the same list skips items."
             " Say what stays, and let the rest fall away.",
    ),
    dict(
        id=15, ledger="P595", concept="PY3 every nth item by a stepped slice", tier="3 - Lists, built and reshaped",
        title="Every third parcel is spot-checked", kind="function",
        func="every_nth",
        cases=[(["a", "b", "c", "d", "e", "f", "g"], 3), (["a", "b"], 3), (["a", "b", "c"], 1), ([], 2), (["a", "b", "c", "d"], 2)],
        prompt=(
            "Write a function `every_nth(items, n)` that returns every"
            " nth item, starting with the nth itself: for n = 3, the"
            " 3rd, 6th, 9th and so on. Fewer than n items gives an"
            " empty list. A slice takes a start and a step.\n\n"
            "  every_nth([\"a\", \"b\", \"c\", \"d\", \"e\", \"f\", \"g\"], 3) -> [\"c\", \"f\"]\n\n"
            "Return: a list."
        ),
        solution=("def every_nth(items, n):\n"
                  "    return items[n - 1::n]\n"),
        trap=("def every_nth(items, n):\n"
              "    return items[::n]\n"),
        note="A slice is [start:stop:step]. The 3rd item is at"
             " position 2, so the start is n - 1, and the step n then"
             " lands on every nth after it. items[::n], the trap,"
             " starts at position 0: the 1st, 4th and 7th, the right"
             " spacing on the wrong parcels. Slices never raise for"
             " being out of range, so a list shorter than n simply"
             " gives an empty one.",
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
