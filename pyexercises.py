"""Python practice exercises: twenty short programs, one built-in each.

The second Python set, and a step DOWN from the first: every question is a
program of two to four lines that prints a result, and every question names
the one function or method it is about -- in the title, so the tree on the
left reads like a list of tools, and in the prompt, which says "Use len()
to ...". There are no functions to define and no loops until the last two.

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
    # ============================================================ 1 Printing
    dict(
        id=1, ledger="P021", concept="PY0 print", tier="1 - Printing",
        title="print(): two things in one call", kind="program",
        prompt=(
            "Use print() with TWO arguments, separated by a comma, to print"
            " the word Ward and the number 5 on one line:\n\n"
            "  Ward 5\n\n"
            "print() puts a space between its arguments for you.\n\n"
            "Print: that one line."
        ),
        solution='print("Ward", 5)\n',
        trap='print("Ward" + 5)\n',
        note="print() takes any number of arguments and writes them"
             " separated by spaces, whatever their types. + is different:"
             " it joins two strings, and \"Ward\" + 5 is a TypeError"
             " because 5 is not a string. When you want things side by"
             " side, the comma is the easy way.",
    ),
    dict(
        id=2, ledger="P022", concept="PY0 print sep", tier="1 - Printing",
        title="print(): choosing the separator", kind="program",
        prompt=(
            "Use print() with three arguments -- the numbers 2026, 6 and 30"
            " -- and its sep= option to print them joined by hyphens:\n\n"
            "  2026-6-30\n\n"
            "Print: that one line."
        ),
        solution='print(2026, 6, 30, sep="-")\n',
        trap='print(2026, "-", 6, "-", 30)\n',
        note="sep is a keyword argument: it names the string print() puts"
             " between the values, and the default is one space. Passing"
             " the hyphens as extra arguments puts a space either side of"
             " each one, giving 2026 - 6 - 30. end= is the other option,"
             " for what comes after the last value; its default is a"
             " newline.",
    ),
    dict(
        id=3, ledger="P023", concept="PY0 str", tier="1 - Printing",
        title="str(): a number inside text", kind="program",
        prompt=(
            "Put the number 16 in a variable called beds. Then use + to"
            " join three pieces into one string -- 'Fleming has ', the"
            " number, and ' beds' -- and print it:\n\n"
            "  Fleming has 16 beds\n\n"
            "+ only joins strings, so use str() to turn the number into"
            " one first.\n\n"
            "Print: that one line."
        ),
        solution='beds = 16\nprint("Fleming has " + str(beds) + " beds")\n',
        trap='beds = 16\nprint("Fleming has " + beds + " beds")\n',
        note="A string plus an integer is a TypeError: Python will not"
             " guess whether you meant to add or to join. str(beds) gives"
             " the text '16', and text plus text joins. The other way"
             " round, int('16') turns text into a number. An f-string does"
             " the str() for you, which is why it is the usual choice.",
    ),
    dict(
        id=4, ledger="P024", concept="PY0 input", tier="1 - Printing",
        title="input(): reading a number", kind="program",
        stdin="24\n",
        prompt=(
            "Use input() to read one line -- it will be the number 24 --"
            " turn it into a number with int(), add 1 to it, and print the"
            " result:\n\n"
            "  25\n\n"
            "When you press Run the program is given the line '24', so you"
            " cannot type it yourself.\n\n"
            "Print: the number one higher than the line read."
        ),
        solution="beds = int(input())\nprint(beds + 1)\n",
        trap="beds = input()\nprint(beds + 1)\n",
        note="input() always returns a string, even when the person typed"
             " digits: '24' is text. Adding 1 to text is a TypeError, and"
             " adding '1' would give '241'. int() converts it, and after"
             " that arithmetic works. Convert at the moment you read, so"
             " the rest of the program never sees the text form.",
    ),
    # ============================================================== 2 Strings
    dict(
        id=5, ledger="P025", concept="PY1 len", tier="2 - Strings",
        title="len(): how long a string is", kind="program",
        prompt=(
            "Put 'Nightingale' in a variable and use len() to print how"
            " many characters it has:\n\n"
            "  11\n\n"
            "Print: the number."
        ),
        solution='ward = "Nightingale"\nprint(len(ward))\n',
        trap='ward = "Nightingale"\nprint(ward.len())\n',
        note="len() is a function you call ON a value -- len(ward) -- not a"
             " method the value has, so ward.len() is an AttributeError."
             " The same len() works on lists, tuples and dictionaries. The"
             " methods that DO belong to strings are called with a dot,"
             " like ward.upper().",
    ),
    dict(
        id=6, ledger="P026", concept="PY1 upper/lower", tier="2 - Strings",
        title="upper() and lower(): changing case", kind="program",
        prompt=(
            "Put 'Seacole Ward' in a variable. Use the upper() method to"
            " print it in capitals, then the lower() method to print it in"
            " small letters:\n\n"
            "  SEACOLE WARD\n"
            "  seacole ward\n\n"
            "Print: the two lines."
        ),
        solution='name = "Seacole Ward"\nprint(name.upper())\nprint(name.lower())\n',
        trap='name = "Seacole Ward"\nprint(name.upper)\nprint(name.lower)\n',
        note="A method is called with parentheses, even when it needs no"
             " arguments. name.upper without them is the method itself,"
             " and printing it shows <built-in method upper of str"
             " object ...> rather than the result. Strings are immutable:"
             " upper() returns a NEW string and leaves name as it was.",
    ),
    dict(
        id=7, ledger="P027", concept="PY1 replace", tier="2 - Strings",
        title="replace(): swapping part of a string", kind="program",
        prompt=(
            "Put 'Bed 3, Bay 3' in a variable and use the replace() method"
            " to change every 3 to a 4, then print the result:\n\n"
            "  Bed 4, Bay 4\n\n"
            "Print: that one line."
        ),
        solution='label = "Bed 3, Bay 3"\nprint(label.replace("3", "4"))\n',
        trap='label = "Bed 3, Bay 3"\nlabel.replace("3", "4")\nprint(label)\n',
        note="replace() returns a new string with the change made; it does"
             " not change the one you called it on. Calling it and then"
             " printing the original prints the original. Either print the"
             " result directly or assign it back: label = label.replace"
             "(...). By default every occurrence is replaced.",
    ),
    dict(
        id=8, ledger="P028", concept="PY1 strip", tier="2 - Strings",
        title="strip(): trimming spaces", kind="program",
        prompt=(
            "Put '   Bay 3   ' -- three spaces either side -- in a"
            " variable. Use the strip() method to remove the outer spaces,"
            " then print the result between square brackets:\n\n"
            "  [Bay 3]\n\n"
            "Print: that one line."
        ),
        solution='bay = "   Bay 3   "\nprint("[" + bay.strip() + "]")\n',
        trap='bay = "   Bay 3   "\nprint("[" + bay.replace(" ", "") + "]")\n',
        note="strip() removes whitespace from both ENDS and nothing in the"
             " middle, which is what you want for input that someone"
             " padded. replace(' ', '') removes every space, including"
             " the one inside the text, giving 'Bay3'. lstrip()"
             " and rstrip() trim one end only.",
    ),
    dict(
        id=9, ledger="P029", concept="PY1 count", tier="2 - Strings",
        title="count(): occurrences of a letter", kind="program",
        prompt=(
            "Put 'observation' in a variable and use the count() method to"
            " print how many times the letter o appears:\n\n"
            "  2\n\n"
            "Print: the number."
        ),
        solution='word = "observation"\nprint(word.count("o"))\n',
        trap='word = "observation"\nprint(word.count(o))\n',
        note="The thing to count is a string, so it goes in quotes: count"
             "('o'). Without quotes, o is the name of a variable, and there"
             " is no variable called o -- a NameError. count() is"
             " case-sensitive and can count longer pieces too, as in"
             " word.count('ti').",
    ),
    # ============================================================== 3 Numbers
    dict(
        id=10, ledger="P030", concept="PY1 round", tier="3 - Numbers",
        title="round(): a set number of decimals", kind="program",
        prompt=(
            "Use round() to print 37.66666 rounded to one decimal place,"
            " and on the next line rounded to a whole number:\n\n"
            "  37.7\n"
            "  38\n\n"
            "Print: the two lines."
        ),
        solution="print(round(37.66666, 1))\nprint(round(37.66666))\n",
        trap="print(round(37.66666, 1))\nprint(round(37.66666, 0))\n",
        note="round(x, 1) keeps one decimal. round(x) with no second"
             " argument returns an INTEGER, 38. round(x, 0) rounds to no"
             " decimals but keeps the float type, 38.0 -- a different line"
             " of output. When you want a whole number, leave the second"
             " argument out.",
    ),
    dict(
        id=11, ledger="P031", concept="PY1 abs", tier="3 - Numbers",
        title="abs(): distance from zero", kind="program",
        prompt=(
            "A patient's temperature is 36.2 and the normal figure is 37.0."
            " Put both in variables and use abs() to print how far apart"
            " they are, as a positive number, rounded to one decimal:\n\n"
            "  0.8\n\n"
            "Print: the number."
        ),
        solution="temp = 36.2\nnormal = 37.0\nprint(round(abs(temp - normal), 1))\n",
        trap="temp = 36.2\nnormal = 37.0\nprint(round(temp - normal, 1))\n",
        note="temp - normal is -0.8, and abs() drops the sign. Without it"
             " the order of the subtraction decides the sign, and 'how far"
             " apart' should not depend on which you wrote first. round()"
             " goes on the outside, because 36.2 - 37.0 in floating point"
             " is -0.7999999999999972.",
    ),
    dict(
        id=12, ledger="P032", concept="PY1 max/min", tier="3 - Numbers",
        title="max() and min(): the largest of several", kind="program",
        prompt=(
            "Three heart-rate readings are 72, 118 and 65. Use max() to"
            " print the highest and min() to print the lowest, passing the"
            " three numbers as three arguments:\n\n"
            "  118\n"
            "  65\n\n"
            "Print: the two lines."
        ),
        solution="print(max(72, 118, 65))\nprint(min(72, 118, 65))\n",
        trap="print(max(72, 118), 65)\nprint(min(72, 118), 65)\n",
        note="max() and min() take any number of arguments, or one list."
             " Close the parentheses too early and 65 becomes a second"
             " argument to print() instead, giving '118 65'. Count the"
             " brackets: every value you want compared goes inside"
             " max(...).",
    ),
    dict(
        id=13, ledger="P033", concept="PY1 int/float", tier="3 - Numbers",
        title="int() and float(): text into numbers", kind="program",
        prompt=(
            "The strings '250' and '2.5' hold a dose and a multiplier."
            " Use int() on the first and float() on the second, multiply"
            " them, and print the result:\n\n"
            "  625.0\n\n"
            "Print: the number."
        ),
        solution='dose = "250"\nfactor = "2.5"\nprint(int(dose) * float(factor))\n',
        trap='dose = "250"\nfactor = "2.5"\nprint(int(dose) * int(factor))\n',
        note="int('2.5') is a ValueError: int() only accepts whole numbers"
             " written as digits. float() accepts either. An int times a"
             " float is a float, so the answer prints as 625.0 -- the .0"
             " is the type showing. Multiplying the strings themselves"
             " would be a TypeError; converting first is the whole point.",
    ),
    dict(
        id=14, ledger="P034", concept="PY1 divmod", tier="3 - Numbers",
        title="// and %: whole hours and the minutes left", kind="program",
        prompt=(
            "A shift lasted 155 minutes. Use // to get the whole hours and"
            " % to get the minutes left over, and print them as:\n\n"
            "  2 h 35 min\n\n"
            "Print: that one line."
        ),
        solution='minutes = 155\nprint(minutes // 60, "h", minutes % 60, "min")\n',
        trap='minutes = 155\nprint(minutes / 60, "h", minutes % 60, "min")\n',
        note="/ always gives a float, so 155 / 60 is 2.5833. // is floor"
             " division: 155 // 60 is 2, the whole hours. % is the"
             " remainder, 35. The pair is so common that divmod(155, 60)"
             " returns both at once as (2, 35).",
    ),
    # ================================================================ 4 Lists
    dict(
        id=15, ledger="P035", concept="PY2 append", tier="4 - Lists",
        title="append(): adding to a list", kind="program",
        prompt=(
            "Start with the list ['Barry', 'Bevan'] in a variable. Use the"
            " append() method to add 'Cavell' to the end, then print the"
            " list:\n\n"
            "  ['Barry', 'Bevan', 'Cavell']\n\n"
            "Print: the list, as print() shows a list."
        ),
        solution='wards = ["Barry", "Bevan"]\nwards.append("Cavell")\nprint(wards)\n',
        trap='wards = ["Barry", "Bevan"]\nwards = wards.append("Cavell")\nprint(wards)\n',
        note="append() changes the list in place and returns None. So"
             " wards = wards.append(...) throws the list away and leaves"
             " wards holding None. Call it on its own line and print the"
             " list afterwards. Methods that change a list -- append,"
             " sort, reverse -- all return None; ones that build a new"
             " value, like sorted(), return it.",
    ),
    dict(
        id=16, ledger="P036", concept="PY2 sorted", tier="4 - Lists",
        title="sorted(): a list in order", kind="program",
        prompt=(
            "Put the list [118, 72, 65, 90] in a variable and use sorted()"
            " to print it from smallest to largest:\n\n"
            "  [65, 72, 90, 118]\n\n"
            "Print: the sorted list."
        ),
        solution="rates = [118, 72, 65, 90]\nprint(sorted(rates))\n",
        trap="rates = [118, 72, 65, 90]\nprint(rates.sort())\n",
        note="sorted(rates) returns a new sorted list and leaves rates"
             " alone. rates.sort() sorts the list IN PLACE and returns"
             " None, so printing its result prints None. Both are right"
             " for different jobs: sort() when you want the list itself"
             " reordered, sorted() when you want a copy. reverse=True"
             " flips the order in either.",
    ),
    dict(
        id=17, ledger="P037", concept="PY2 sum/len", tier="4 - Lists",
        title="sum() and len(): an average", kind="program",
        prompt=(
            "Put the list [36.8, 37.2, 38.1, 36.9] in a variable. Use sum()"
            " and len() to work out the average and print it rounded to"
            " one decimal:\n\n"
            "  37.2\n\n"
            "Print: the number."
        ),
        solution="temps = [36.8, 37.2, 38.1, 36.9]\nprint(round(sum(temps) / len(temps), 1))\n",
        trap="temps = [36.8, 37.2, 38.1, 36.9]\nprint(round(sum(temps) / 4), 1)\n",
        note="sum() adds a list up and len() counts it, so the average is"
             " one over the other -- with len() rather than a typed 4, so"
             " the line stays right when the list changes. The trap's"
             " brackets close round() before the 1, which makes the 1 a"
             " second argument to print(): '37 1'. Bracket mistakes like"
             " this run without error; check the output.",
    ),
    dict(
        id=18, ledger="P038", concept="PY2 split/join", tier="4 - Lists",
        title="split() and join(): text to list and back", kind="program",
        prompt=(
            "Put 'Morphine Codeine Diazepam' in a variable. Use the split()"
            " method to break it into a list and print the list, then use"
            " the join() method with ', ' to put it back together and"
            " print that:\n\n"
            "  ['Morphine', 'Codeine', 'Diazepam']\n"
            "  Morphine, Codeine, Diazepam\n\n"
            "Print: the two lines."
        ),
        solution=('drugs = "Morphine Codeine Diazepam"\n'
                  'names = drugs.split()\n'
                  'print(names)\n'
                  'print(", ".join(names))\n'),
        trap=('drugs = "Morphine Codeine Diazepam"\n'
              'names = drugs.split()\n'
              'print(names)\n'
              'print(names.join(", "))\n'),
        note="split() belongs to the string and returns a list; with no"
             " argument it splits on any whitespace. join() ALSO belongs"
             " to a string -- the separator -- and takes the list as its"
             " argument, so it is ', '.join(names), not names.join(', ')."
             " Lists have no join method, which is the AttributeError the"
             " trap raises.",
    ),
    # ================================================================ 5 Loops
    dict(
        id=19, ledger="P039", concept="PY2 range", tier="5 - Loops",
        title="range(): the numbers 1 to 5", kind="program",
        prompt=(
            "Use range() inside list() to build the list of numbers from 1"
            " to 5 and print it:\n\n"
            "  [1, 2, 3, 4, 5]\n\n"
            "range() itself prints as range(1, 6); list() turns it into a"
            " real list.\n\n"
            "Print: the list."
        ),
        solution="print(list(range(1, 6)))\n",
        trap="print(list(range(1, 5)))\n",
        note="range(start, stop) runs from start up to but NOT including"
             " stop, so 1 to 5 is range(1, 6). With one argument it starts"
             " at 0: range(5) is 0 to 4. A third argument is the step."
             " Wrapping in list() is only for looking at it; a for loop"
             " uses the range directly.",
    ),
    dict(
        id=20, ledger="P040", concept="PY2 for", tier="5 - Loops",
        title="for: one line per item", kind="program",
        prompt=(
            "Put the list ['Fleming', 'Jenner', 'Lister'] in a variable and"
            " use a for loop to print each ward on its own line, followed"
            " by ' ward':\n\n"
            "  Fleming ward\n"
            "  Jenner ward\n"
            "  Lister ward\n\n"
            "Print: the three lines."
        ),
        solution=('wards = ["Fleming", "Jenner", "Lister"]\n'
                  'for ward in wards:\n'
                  '    print(ward, "ward")\n'),
        trap=('wards = ["Fleming", "Jenner", "Lister"]\n'
              'for ward in wards:\n'
              '    pass\n'
              'print(ward, "ward")\n'),
        note="The indented block under for runs once per item, with the"
             " loop variable holding that item. A print AFTER the block,"
             " at the left margin, runs once, after the loop, with the"
             " variable still holding the LAST item -- so only 'Lister"
             " ward' appears. Indentation is what puts a line inside the"
             " loop; four spaces is the convention.",
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
