"""Python practice exercises: fifteen short programs, one built-in each.

The third Python set, at the level of the second: every question is a
program of two to four lines that prints a result, and every question names
the one function, method or keyword it is about -- in the title, so the
tree on the left reads like a list of tools, and in the prompt. The tools
are ones the previous set did not cover: title(), startswith(), find(), the
in test, index(), pop(), insert(), remove(), sorted() in reverse, len() on
a list, a format spec, divmod(), type(), enumerate() and while.

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
    # ========================================================= 1 More strings
    dict(
        id=1, ledger="P041", concept="PY1 title", tier="1 - More strings",
        title="title(): a capital on every word", kind="program",
        prompt=(
            "Put 'florence nightingale' in a variable and use the title()"
            " method to print it with a capital letter on each word:\n\n"
            "  Florence Nightingale\n\n"
            "Print: that one line."
        ),
        solution='name = "florence nightingale"\nprint(name.title())\n',
        trap='name = "florence nightingale"\nprint(name.capitalize())\n',
        note="title() capitalises the first letter of EVERY word;"
             " capitalize() does only the first letter of the string and"
             " lower-cases the rest, giving 'Florence nightingale'. Both"
             " return a new string. upper() and lower() are the other two"
             " in the family.",
    ),
    dict(
        id=2, ledger="P042", concept="PY1 startswith", tier="1 - More strings",
        title="startswith(): does it begin with", kind="program",
        prompt=(
            "Put the procedure code 'SRG-04' in a variable. Use the"
            " startswith() method to print whether it begins with 'SRG',"
            " then whether it begins with 'DIA':\n\n"
            "  True\n"
            "  False\n\n"
            "Print: the two lines."
        ),
        solution='code = "SRG-04"\nprint(code.startswith("SRG"))\nprint(code.startswith("DIA"))\n',
        trap='code = "SRG-04"\nprint(code == "SRG")\nprint(code == "DIA")\n',
        note="== asks whether the whole string is 'SRG', and 'SRG-04' is"
             " not, so both lines come out False. startswith() asks about"
             " the beginning only, and returns a boolean you can print or"
             " put straight into an if. endswith() is its mirror.",
    ),
    dict(
        id=3, ledger="P043", concept="PY1 find", tier="1 - More strings",
        title="find(): where a character is", kind="program",
        prompt=(
            "Put 'SRG-04' in a variable. Use the find() method to print the"
            " position of the hyphen, then the result of looking for a"
            " letter that is not there, 'X':\n\n"
            "  3\n"
            "  -1\n\n"
            "Positions count from 0.\n\n"
            "Print: the two lines."
        ),
        solution='code = "SRG-04"\nprint(code.find("-"))\nprint(code.find("X"))\n',
        trap='code = "SRG-04"\nprint(code.index("-"))\nprint(code.index("X"))\n',
        note="find() and index() both give the position of the first"
             " match, counting from 0. They differ on a miss: find()"
             " returns -1, index() raises ValueError and stops the program."
             " Use find() when a miss is an ordinary outcome, index() when"
             " it would be a bug.",
    ),
    # ================================================================ 2 Lists
    dict(
        id=4, ledger="P044", concept="PY2 in", tier="2 - Lists",
        title="in: is it in the list", kind="program",
        prompt=(
            "Put the list ['Morphine', 'Codeine', 'Diazepam'] in a variable."
            " Use the in test to print whether 'Codeine' is in it, then"
            " whether 'Aspirin' is:\n\n"
            "  True\n"
            "  False\n\n"
            "Print: the two lines."
        ),
        solution=('drugs = ["Morphine", "Codeine", "Diazepam"]\n'
                  'print("Codeine" in drugs)\nprint("Aspirin" in drugs)\n'),
        trap=('drugs = ["Morphine", "Codeine", "Diazepam"]\n'
              'print("codeine" in drugs)\nprint("Aspirin" in drugs)\n'),
        note="in is an operator, not a method: value in list. It compares"
             " with ==, so the case has to match -- 'codeine' is not in a"
             " list that holds 'Codeine'. The same in works on strings"
             " ('od' in 'Codeine'), tuples, sets and dictionary keys.",
    ),
    dict(
        id=5, ledger="P045", concept="PY2 index", tier="2 - Lists",
        title="index(): where in the list", kind="program",
        prompt=(
            "Put ['Morphine', 'Codeine', 'Diazepam'] in a variable and use"
            " the index() method to print the position of 'Codeine':\n\n"
            "  1\n\n"
            "Print: the number."
        ),
        solution='drugs = ["Morphine", "Codeine", "Diazepam"]\nprint(drugs.index("Codeine"))\n',
        trap='drugs = ["Morphine", "Codeine", "Diazepam"]\nprint(drugs.find("Codeine"))\n',
        note="Lists have index() but not find(): drugs.find(...) is an"
             " AttributeError. Positions count from 0, so the second item"
             " is at 1. index() raises ValueError when the value is not"
             " there; test with in first if that is possible.",
    ),
    dict(
        id=6, ledger="P046", concept="PY2 pop", tier="2 - Lists",
        title="pop(): take the last one off", kind="program",
        prompt=(
            "Put [72, 118, 65] in a variable. Use the pop() method to remove"
            " the LAST item, print the item that was removed, then print"
            " the list:\n\n"
            "  65\n"
            "  [72, 118]\n\n"
            "Print: the two lines."
        ),
        solution='rates = [72, 118, 65]\nlast = rates.pop()\nprint(last)\nprint(rates)\n',
        trap='rates = [72, 118, 65]\nfirst = rates.pop(0)\nprint(first)\nprint(rates)\n',
        note="pop() with no argument removes and RETURNS the last item --"
             " the one method that both changes the list and hands"
             " something back. pop(0) removes the first instead; any index"
             " works. append() and pop() together make a list behave as a"
             " stack.",
    ),
    dict(
        id=7, ledger="P047", concept="PY2 insert", tier="2 - Lists",
        title="insert(): put it at a position", kind="program",
        prompt=(
            "Put ['Barry', 'Cavell'] in a variable. Use the insert() method"
            " to put 'Bevan' at position 1 -- between the two -- then print"
            " the list:\n\n"
            "  ['Barry', 'Bevan', 'Cavell']\n\n"
            "Print: the list."
        ),
        solution='wards = ["Barry", "Cavell"]\nwards.insert(1, "Bevan")\nprint(wards)\n',
        trap='wards = ["Barry", "Cavell"]\nwards.append("Bevan")\nprint(wards)\n',
        note="insert(position, value) puts the value at that index and"
             " shifts the rest along; append() only ever adds at the end."
             " Like append(), insert() changes the list in place and"
             " returns None, so do not assign its result.",
    ),
    dict(
        id=8, ledger="P048", concept="PY2 remove", tier="2 - Lists",
        title="remove(): take out by value", kind="program",
        prompt=(
            "Put ['Barry', 'Bevan', 'Cavell'] in a variable. Use the"
            " remove() method to take out 'Bevan' -- by its value, not its"
            " position -- then print the list:\n\n"
            "  ['Barry', 'Cavell']\n\n"
            "Print: the list."
        ),
        solution='wards = ["Barry", "Bevan", "Cavell"]\nwards.remove("Bevan")\nprint(wards)\n',
        trap='wards = ["Barry", "Bevan", "Cavell"]\nwards.remove(1)\nprint(wards)\n',
        note="remove() takes the VALUE to remove and deletes the first"
             " match; remove(1) looks for the number 1, finds none, and"
             " raises ValueError. To remove by position use pop(1) or"
             " del wards[1]. remove() returns None, like the other"
             " in-place methods.",
    ),
    dict(
        id=9, ledger="P049", concept="PY2 sorted reverse", tier="2 - Lists",
        title="sorted(reverse=True): largest first", kind="program",
        prompt=(
            "Put [72, 118, 65, 90] in a variable and use sorted() with its"
            " reverse= option to print the list from largest to"
            " smallest:\n\n"
            "  [118, 90, 72, 65]\n\n"
            "Print: the sorted list."
        ),
        solution="rates = [72, 118, 65, 90]\nprint(sorted(rates, reverse=True))\n",
        trap="rates = [72, 118, 65, 90]\nprint(sorted(rates, reverse=true))\n",
        note="Python's booleans are True and False with a capital letter;"
             " true on its own is an undefined name and a NameError."
             " reverse=True is a keyword argument, written with its name,"
             " and the same option works on list.sort().",
    ),
    dict(
        id=10, ledger="P050", concept="PY2 len list", tier="2 - Lists",
        title="len(): how many in the list", kind="program",
        prompt=(
            "Put ['Barry', 'Bevan', 'Cavell', 'Fleming'] in a variable and"
            " use len() to print how many wards the list holds:\n\n"
            "  4\n\n"
            "Print: the number."
        ),
        solution='wards = ["Barry", "Bevan", "Cavell", "Fleming"]\nprint(len(wards))\n',
        trap='wards = ["Barry", "Bevan", "Cavell", "Fleming"]\nprint(wards.count())\n',
        note="len() is the one way to ask how many items a list holds, and"
             " it works on strings, tuples and dictionaries too. count()"
             " exists on lists but answers a different question -- how many"
             " times one particular value appears -- and needs that value"
             " as its argument, so calling it empty is a TypeError.",
    ),
    # ==================================================== 3 Numbers and types
    dict(
        id=11, ledger="P051", concept="PY1 format spec", tier="3 - Numbers and types",
        title="f'{x:.2f}': two decimal places", kind="program",
        prompt=(
            "A dose costs 180 pence. Put that in a variable, divide by 100"
            " to get pounds, and use an f-string with the format spec .2f"
            " to print it with two decimal places and a pound sign:\n\n"
            "  £1.80\n\n"
            "Print: that one line."
        ),
        solution='pence = 180\nprint(f"£{pence / 100:.2f}")\n',
        trap='pence = 180\nprint(f"£{round(pence / 100, 2)}")\n',
        note="round(1.8, 2) is still 1.8 -- rounding does not add trailing"
             " zeros, because a number has no notion of how many digits to"
             " show. Formatting does: :.2f always writes two decimals. The"
             " spec goes after a colon inside the braces, and other specs"
             " exist, such as :, for thousands separators and :>8 to pad.",
    ),
    dict(
        id=12, ledger="P052", concept="PY1 divmod", tier="3 - Numbers and types",
        title="divmod(): quotient and remainder at once", kind="program",
        prompt=(
            "A shift lasted 155 minutes. Use divmod() to get the whole"
            " hours and the minutes left over in ONE call, unpack the pair"
            " into two variables, and print:\n\n"
            "  2 h 35 min\n\n"
            "Print: that one line."
        ),
        solution='hours, mins = divmod(155, 60)\nprint(hours, "h", mins, "min")\n',
        trap='result = divmod(155, 60)\nprint(result, "h", "min")\n',
        note="divmod(a, b) returns a tuple (a // b, a %% b), and a tuple"
             " can be unpacked into two names on the left of the ="
             " sign. Printing the tuple itself shows '(2, 35) h min'."
             " Unpacking is how a function hands back more than one"
             " value.",
    ),
    dict(
        id=13, ledger="P053", concept="PY1 type", tier="3 - Numbers and types",
        title="type(): what kind of value", kind="program",
        prompt=(
            "Use type() to print the type of 3, of 3.0 and of '3', one per"
            " line, exactly as Python shows them:\n\n"
            "  <class 'int'>\n"
            "  <class 'float'>\n"
            "  <class 'str'>\n\n"
            "Print: the three lines."
        ),
        solution="print(type(3))\nprint(type(3.0))\nprint(type('3'))\n",
        trap="print(type(3))\nprint(type(3.0))\nprint(type(int('3')))\n",
        note="Three values that look alike are three types: an integer, a"
             " float, and a string of one character. int('3') converts the"
             " string, so its type is int again -- the trap prints the type"
             " of the converted value, not of the string. type() is a"
             " debugging tool; in code, isinstance(x, int) is the test.",
    ),
    # ================================================================ 4 Loops
    dict(
        id=14, ledger="P054", concept="PY2 enumerate", tier="4 - Loops",
        title="enumerate(): numbering as you loop", kind="program",
        prompt=(
            "Put ['Fleming', 'Jenner', 'Lister'] in a variable and use a"
            " for loop with enumerate() to print each ward with its number,"
            " counting from 1:\n\n"
            "  1. Fleming\n"
            "  2. Jenner\n"
            "  3. Lister\n\n"
            "enumerate() takes a second argument for where to start.\n\n"
            "Print: the three lines."
        ),
        solution=('wards = ["Fleming", "Jenner", "Lister"]\n'
                  'for n, ward in enumerate(wards, 1):\n'
                  '    print(f"{n}. {ward}")\n'),
        trap=('wards = ["Fleming", "Jenner", "Lister"]\n'
              'for n, ward in enumerate(wards):\n'
              '    print(f"{n}. {ward}")\n'),
        note="enumerate() yields (number, item) pairs, and the for loop"
             " unpacks each pair into two names. It counts from 0 unless"
             " told otherwise; enumerate(wards, 1) starts at 1. It replaces"
             " the older habit of range(len(wards)) with an index lookup.",
    ),
    dict(
        id=15, ledger="P055", concept="PY2 while", tier="4 - Loops",
        title="while: repeat until a condition fails", kind="program",
        prompt=(
            "Start a variable at 3 and use a while loop to count down,"
            " printing the number each time, until it reaches 0; then"
            " print Go:\n\n"
            "  3\n"
            "  2\n"
            "  1\n"
            "  Go\n\n"
            "Something inside the loop has to change the variable, or the"
            " loop never ends.\n\n"
            "Print: the four lines."
        ),
        solution='n = 3\nwhile n > 0:\n    print(n)\n    n = n - 1\nprint("Go")\n',
        trap='n = 3\nwhile n > 0:\n    print(n)\nprint("Go")\n',
        note="A while loop tests its condition before every pass. Nothing"
             " in the trap changes n, so the condition stays true and the"
             " loop prints 3 forever -- the runner stops it at the time"
             " limit. Every while needs a line in its body that moves it"
             " towards the exit; n -= 1 is the short form.",
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
