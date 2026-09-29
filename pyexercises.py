"""Python practice exercises: fifteen short programs, one tool each.

The fourth Python set, at the level of the two before it: every question
is a program of two to four lines that prints a result, and every question
names the one function, method, type or keyword it is about -- in the
title, so the tree on the left reads like a list of tools, and in the
prompt. This set's ground is dictionaries, tuples, slices and a few more
string tools: a dict lookup, get(), adding a key, keys(), values() with
sum(), items() in a loop, len() on a dict, a tuple unpacked, slicing a
string, endswith(), isdigit(), zip(), max() with a key, string
multiplication, and if/else.

Two kinds of question, told apart by `kind`:

  "program"   the editor holds a whole program. Run executes it and shows
              what it printed; Check compares that, line for line, with what
              the reference program prints. `stdin`, where present, is the
              text the program can read with input().
  "function"  the editor defines a function named `func`. Run calls it once
              per case in `cases` and shows each call and its result; Check
              compares each result with the reference function's. Not used
              in this set, but the grader still supports it.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py),
so an infinite loop or a print in a loop is stopped, not fatal.
"""

import pyrun

EXERCISES = [
    # ========================================================= 1 Dictionaries
    dict(
        id=1, ledger="P056", concept="PY3 dict lookup", tier="1 - Dictionaries",
        title="dict: a value by its key", kind="program",
        prompt=(
            "Make a dictionary from ward names to beds: 'Fleming' 16,"
            " 'Barry' 30, 'Jenner' 18. Look up Fleming with square brackets"
            " and print its beds:\n\n"
            "  16\n\n"
            "Print: the number."
        ),
        solution='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(beds["Fleming"])\n',
        trap='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(beds("Fleming"))\n',
        note="A dictionary is looked up with square brackets, like a list,"
             " but by key rather than by position. Round brackets would"
             " CALL it, and a dict is not callable -- a TypeError. The"
             " literal is {key: value, ...}; keys are usually strings or"
             " numbers, values can be anything.",
    ),
    dict(
        id=2, ledger="P057", concept="PY3 dict get", tier="1 - Dictionaries",
        title="get(): a lookup that may miss", kind="program",
        prompt=(
            "With the same dictionary -- 'Fleming' 16, 'Barry' 30,"
            " 'Jenner' 18 -- use the get() method to print the beds for"
            " 'Bevan', which is not there, with 0 as the fallback; then"
            " get() 'Barry' the same way:\n\n"
            "  0\n"
            "  30\n\n"
            "Print: the two lines."
        ),
        solution=('beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\n'
                  'print(beds.get("Bevan", 0))\nprint(beds.get("Barry", 0))\n'),
        trap=('beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\n'
              'print(beds["Bevan"])\nprint(beds["Barry"])\n'),
        note="Square brackets on a missing key raise KeyError and stop the"
             " program. get(key, default) returns the default instead, and"
             " the default is None when you give none. Use brackets when a"
             " missing key would be a bug; get() when it is an ordinary"
             " outcome.",
    ),
    dict(
        id=3, ledger="P058", concept="PY3 dict assign", tier="1 - Dictionaries",
        title="dict[key] = value: adding an entry", kind="program",
        prompt=(
            "Start with the dictionary 'Fleming' 16, 'Barry' 30. Add"
            " 'Jenner' with 18 by assigning to a new key, then print the"
            " dictionary:\n\n"
            "  {'Fleming': 16, 'Barry': 30, 'Jenner': 18}\n\n"
            "Print: the dictionary, as print() shows one."
        ),
        solution='beds = {"Fleming": 16, "Barry": 30}\nbeds["Jenner"] = 18\nprint(beds)\n',
        trap='beds = {"Fleming": 16, "Barry": 30}\nbeds.append("Jenner", 18)\nprint(beds)\n',
        note="A dictionary has no append(): assigning to a key that does"
             " not exist creates it, and assigning to one that does"
             " replaces its value. New keys go on the end, and a dict"
             " remembers insertion order, which is why the printed order"
             " is the order you added them.",
    ),
    dict(
        id=4, ledger="P059", concept="PY3 dict keys", tier="1 - Dictionaries",
        title="keys(): the keys as a list", kind="program",
        prompt=(
            "With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18,"
            " use the keys() method inside list() to print the ward names"
            " as a list:\n\n"
            "  ['Fleming', 'Barry', 'Jenner']\n\n"
            "Print: the list."
        ),
        solution='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(list(beds.keys()))\n',
        trap='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(beds.keys())\n',
        note="keys() returns a view, and a view prints as"
             " dict_keys(['Fleming', ...]) rather than as a list. list()"
             " turns it into one. A view is fine to loop over directly --"
             " for ward in beds.keys(), or just for ward in beds, which"
             " means the same.",
    ),
    dict(
        id=5, ledger="P060", concept="PY3 dict values", tier="1 - Dictionaries",
        title="values(): adding them up", kind="program",
        prompt=(
            "With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18,"
            " use sum() over the values() method to print the total"
            " beds:\n\n"
            "  64\n\n"
            "Print: the number."
        ),
        solution='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(sum(beds.values()))\n',
        trap='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(sum(beds))\n',
        note="Looping over a dictionary -- and sum() loops -- gives its"
             " KEYS. sum(beds) tries to add up the ward names, and adding"
             " a string to a number is a TypeError. values() is the view"
             " of the numbers; sum(), max() and min() all take it.",
    ),
    dict(
        id=6, ledger="P061", concept="PY3 dict items", tier="1 - Dictionaries",
        title="items(): key and value together", kind="program",
        prompt=(
            "With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18,"
            " loop over the items() method to print one line per ward:\n\n"
            "  Fleming: 16\n"
            "  Barry: 30\n"
            "  Jenner: 18\n\n"
            "Print: the three lines."
        ),
        solution=('beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\n'
                  'for ward, n in beds.items():\n'
                  '    print(f"{ward}: {n}")\n'),
        trap=('beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\n'
              'for ward, n in beds:\n'
              '    print(f"{ward}: {n}")\n'),
        note="items() yields (key, value) pairs, which the for loop"
             " unpacks into two names. Looping over the dictionary itself"
             " yields keys only, so unpacking 'Fleming' into two names"
             " fails -- a string of seven characters into two variables"
             " is a ValueError. If you only need the keys, drop the"
             " second name and the items().",
    ),
    dict(
        id=7, ledger="P062", concept="PY3 len dict", tier="1 - Dictionaries",
        title="len(): how many entries", kind="program",
        prompt=(
            "With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18,"
            " use len() to print how many wards it holds:\n\n"
            "  3\n\n"
            "Print: the number."
        ),
        solution='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(len(beds))\n',
        trap='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(len(beds.items))\n',
        note="len() on a dictionary counts its entries. beds.items without"
             " parentheses is the method itself, not the pairs, and a"
             " method has no length -- a TypeError. len(beds.items()) would"
             " work but says nothing len(beds) does not.",
    ),
    # ==================================================== 2 Tuples and slices
    dict(
        id=8, ledger="P063", concept="PY3 tuple", tier="2 - Tuples and slices",
        title="tuple: a pair that cannot change", kind="program",
        prompt=(
            "Put the blood pressure reading 120 over 80 in a tuple called"
            " bp. Unpack it into two names, systolic and diastolic, and"
            " print them as:\n\n"
            "  120/80\n\n"
            "Print: that one line."
        ),
        solution='bp = (120, 80)\nsystolic, diastolic = bp\nprint(f"{systolic}/{diastolic}")\n',
        trap='bp = (120, 80)\nsystolic, diastolic = bp\nprint(systolic / diastolic)\n',
        note="A tuple is a fixed sequence written with round brackets, and"
             " unpacking assigns its items to names in one line. The slash"
             " in the output is a character, not a division: f\"{a}/{b}\""
             " prints 120/80, while a / b computes 1.5. Tuples cannot be"
             " changed after they are made, which is what makes them safe"
             " to pass around.",
    ),
    dict(
        id=9, ledger="P064", concept="PY1 slicing", tier="2 - Tuples and slices",
        title="[start:stop]: a piece of a string", kind="program",
        prompt=(
            "Put the procedure code 'SRG-04' in a variable. Use slicing to"
            " print the first three characters, then the last two:\n\n"
            "  SRG\n"
            "  04\n\n"
            "Print: the two lines."
        ),
        solution='code = "SRG-04"\nprint(code[:3])\nprint(code[-2:])\n',
        trap='code = "SRG-04"\nprint(code[0:2])\nprint(code[-2:])\n',
        note="A slice [start:stop] runs from start up to but NOT including"
             " stop, so the first three characters are [0:3] or [:3];"
             " [0:2] is two. A negative index counts from the end, so"
             " [-2:] is the last two. Strings, lists and tuples all slice"
             " the same way.",
    ),
    dict(
        id=10, ledger="P065", concept="PY1 string multiply", tier="2 - Tuples and slices",
        title="'-' * n: repeating a string", kind="program",
        prompt=(
            "Print a line of 20 hyphens, then the word Ward, then another"
            " line of 20 hyphens, using multiplication to make the"
            " lines:\n\n"
            "  --------------------\n"
            "  Ward\n"
            "  --------------------\n\n"
            "Print: the three lines."
        ),
        solution='print("-" * 20)\nprint("Ward")\nprint("-" * 20)\n',
        trap='print("-" + 20)\nprint("Ward")\nprint("-" + 20)\n',
        note="A string times an integer repeats it; a string plus an"
             " integer is a TypeError. The same trick makes a list of"
             " repeated items, [0] * 5. Useful for rulers, padding and"
             " simple bars.",
    ),
    # ==================================================== 3 String tests
    dict(
        id=11, ledger="P066", concept="PY1 endswith", tier="3 - String tests",
        title="endswith(): the end of a string", kind="program",
        prompt=(
            "Two file names: 'report.pdf' and 'pdf_notes.txt'. Use the"
            " endswith() method to print whether each ends with"
            " '.pdf':\n\n"
            "  True\n"
            "  False\n\n"
            "Print: the two lines."
        ),
        solution='print("report.pdf".endswith(".pdf"))\nprint("pdf_notes.txt".endswith(".pdf"))\n',
        trap='print("pdf" in "report.pdf")\nprint("pdf" in "pdf_notes.txt")\n',
        note="in asks whether the text appears ANYWHERE, so 'pdf' is in"
             " 'pdf_notes.txt' too. endswith() asks about the tail only,"
             " and startswith() about the head. Include the dot in the"
             " test, or 'mypdf' would pass.",
    ),
    dict(
        id=12, ledger="P067", concept="PY1 isdigit", tier="3 - String tests",
        title="isdigit(): is it all digits", kind="program",
        prompt=(
            "Two strings read from a form: '0420' and '42a'. Use the"
            " isdigit() method to print whether each is made of digits"
            " only:\n\n"
            "  True\n"
            "  False\n\n"
            "Print: the two lines."
        ),
        solution='print("0420".isdigit())\nprint("42a".isdigit())\n',
        trap='print(type("0420") == int)\nprint(type("42a") == int)\n',
        note="Text read from a form or input() is always a str, so asking"
             " its type says nothing about what it contains. isdigit()"
             " looks at the characters. It is false for '-5' and '3.5',"
             " so it is a check for whole non-negative numbers; for"
             " anything else, try int() and catch the ValueError.",
    ),
    dict(
        id=13, ledger="P068", concept="PY2 if/else", tier="3 - String tests",
        title="if/else: one of two lines", kind="program",
        prompt=(
            "Put 'Codeine' in a variable and the list ['Morphine',"
            " 'Codeine', 'Fentanyl'] in another. Use if/else with the in"
            " test to print 'controlled' when the drug is in the list and"
            " 'not controlled' otherwise:\n\n"
            "  controlled\n\n"
            "Print: the one line that applies."
        ),
        solution=('drug = "Codeine"\ncontrolled = ["Morphine", "Codeine", "Fentanyl"]\n'
                  'if drug in controlled:\n    print("controlled")\n'
                  'else:\n    print("not controlled")\n'),
        trap=('drug = "Codeine"\ncontrolled = ["Morphine", "Codeine", "Fentanyl"]\n'
              'if drug in controlled:\n    print("controlled")\n'
              'print("not controlled")\n'),
        note="Without the else, the second print is not part of the"
             " choice: it sits after the if at the left margin and runs"
             " every time, so both lines appear. else: introduces the"
             " block that runs only when the condition was false, and the"
             " two blocks are exclusive.",
    ),
    # ================================================== 4 Two lists at once
    dict(
        id=14, ledger="P069", concept="PY2 zip", tier="4 - Two lists at once",
        title="zip(): walking two lists together", kind="program",
        prompt=(
            "Two lists in step: wards ['Fleming', 'Barry', 'Jenner'] and"
            " beds [16, 30, 18]. Use zip() in a for loop to print each"
            " ward with its beds:\n\n"
            "  Fleming 16\n"
            "  Barry 30\n"
            "  Jenner 18\n\n"
            "Print: the three lines."
        ),
        solution=('wards = ["Fleming", "Barry", "Jenner"]\nbeds = [16, 30, 18]\n'
                  'for ward, n in zip(wards, beds):\n    print(ward, n)\n'),
        trap=('wards = ["Fleming", "Barry", "Jenner"]\nbeds = [16, 30, 18]\n'
              'for ward in wards:\n    for n in beds:\n        print(ward, n)\n'),
        note="zip() pairs the first items, then the second, then the third,"
             " and stops at the shorter list. Two nested loops pair EVERY"
             " ward with EVERY bed count -- nine lines. When two lists"
             " line up position by position, zip() is the loop; dict"
             "(zip(wards, beds)) turns the pairs into a dictionary.",
    ),
    dict(
        id=15, ledger="P070", concept="PY3 max key", tier="4 - Two lists at once",
        title="max(key=): the biggest by a rule", kind="program",
        prompt=(
            "With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18,"
            " use max() with key=beds.get to print the name of the ward"
            " with the most beds:\n\n"
            "  Barry\n\n"
            "Print: the name."
        ),
        solution='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(max(beds, key=beds.get))\n',
        trap='beds = {"Fleming": 16, "Barry": 30, "Jenner": 18}\nprint(max(beds))\n',
        note="max(beds) compares the KEYS, and 'Jenner' is the largest"
             " string alphabetically. key= names a function that turns"
             " each item into the thing to compare -- beds.get maps a"
             " ward to its beds -- and max() returns the original item,"
             " the ward name, not the number. min() and sorted() take"
             " the same key= argument.",
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
