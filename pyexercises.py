"""Python practice exercises: fifteen tiny functions, one tool each.

The twelfth Python set, back to one-tool functions: every question asks
for a function of one or two lines that returns a value, built around one
named tool no earlier set used -- strip() with an argument, istitle(),
replace() with a count, removesuffix(), isspace(), int() with a base,
format() with 'b', math.gcd(), the .1% format spec, sorted() with
key=str.lower, list.count(), range() with a step, set <= for subset,
dict.setdefault(), and the in test on a dictionary. The title names the
tool, so the tree on the left reads like a list of tools.

Two kinds of question, told apart by `kind`:

  "program"   the editor holds a whole program, graded on what it prints.
              Not used in this set.
  "function"  the editor defines a function named `func`. Run calls it once
              per case in `cases` and shows each call and its result; Check
              compares each result with the reference function's. Values
              are compared, not their printed form -- a dict in another
              order is the same dict -- but the container type counts, so a
              tuple is not a list, and 0 is not False.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py).
"""

import pyrun

EXERCISES = [
    # ============================================================== 1 Strings
    dict(
        id=1, ledger="P176", concept="PY3 strip chars", tier="1 - Strings",
        title="strip(chars): quotes off both ends", kind="function",
        func="unquote",
        cases=[('"Leeds"',), ('"a" and "b"',), ("plain",), ('""',)],
        prompt=(
            "Write a function `unquote(s)` that returns s with any double"
            " quote characters removed from its two ENDS -- and nothing"
            " removed from the middle -- using strip() with the quote as"
            " its argument:\n\n"
            "  unquote('\"Leeds\"') -> 'Leeds'\n\n"
            "Return: the new string."
        ),
        solution="def unquote(s):\n    return s.strip(\"\\\"\")\n",
        trap="def unquote(s):\n    return s.replace(\"\\\"\", \"\")\n",
        note="strip(chars) takes the given characters off both ends and"
             " stops at the first character that is not one of them;"
             " replace() removes every occurrence, including the quotes"
             " INSIDE the text. The two agree on '\"Leeds\"' and"
             " disagree the moment a quote appears in the middle.",
    ),
    dict(
        id=2, ledger="P177", concept="PY3 istitle", tier="1 - Strings",
        title="istitle(): is every word capitalised?", kind="function",
        func="is_title_case",
        cases=[("The Glass Path",), ("The glass path",), ("THE GLASS PATH",), ("",)],
        prompt=(
            "Write a function `is_title_case(s)` that returns True when"
            " every word in s starts with a capital and continues in"
            " lower case, using istitle():\n\n"
            "  is_title_case(\"The glass path\") -> False\n\n"
            "Return: True or False."
        ),
        solution="def is_title_case(s):\n    return s.istitle()\n",
        trap="def is_title_case(s):\n    return s[:1].isupper()\n",
        note="istitle() checks every word, and also that the letters"
             " after each capital are lower case -- so 'THE GLASS PATH'"
             " is False. Testing the first character alone says yes to"
             " both of the wrong cases. The empty string is False: there"
             " is no cased character in it.",
    ),
    dict(
        id=3, ledger="P178", concept="PY3 replace count", tier="1 - Strings",
        title="replace(old, new, 1): only the first one", kind="function",
        func="replace_first",
        cases=[("a-b-c", "-", "+"), ("none here", "x", "y"), ("aaa", "a", "b"), ("", "a", "b")],
        prompt=(
            "Write a function `replace_first(s, old, new)` that returns s"
            " with only the FIRST occurrence of old replaced by new,"
            " using replace() with its count argument:\n\n"
            "  replace_first(\"a-b-c\", \"-\", \"+\") -> \"a+b-c\"\n\n"
            "Return: the new string."
        ),
        solution="def replace_first(s, old, new):\n    return s.replace(old, new, 1)\n",
        trap="def replace_first(s, old, new):\n    return s.replace(old, new)\n",
        note="replace() has a third argument, the maximum number of"
             " replacements, and 1 means the first match only. Without"
             " it every match is replaced. A string with no match is"
             " returned unchanged either way.",
    ),
    dict(
        id=4, ledger="P179", concept="PY3 removesuffix", tier="1 - Strings",
        title="removesuffix(): the extension off the end", kind="function",
        func="drop_txt",
        cases=[("notes.txt",), ("notes.csv",), ("txt",), ("a.txt.txt",)],
        prompt=(
            "Write a function `drop_txt(filename)` that returns the name"
            " without a trailing '.txt' -- and unchanged when it does not"
            " end in that -- using removesuffix():\n\n"
            "  drop_txt(\"notes.txt\") -> \"notes\"\n"
            "  drop_txt(\"notes.csv\") -> \"notes.csv\"\n\n"
            "Return: the new string."
        ),
        solution="def drop_txt(filename):\n    return filename.removesuffix(\".txt\")\n",
        trap="def drop_txt(filename):\n    return filename[:-4]\n",
        note="removesuffix() removes the ending only when it is there,"
             " and only once. Slicing off the last four characters cuts"
             " 'notes.csv' down to 'notes' as well, and takes 'txt' to"
             " nothing. The pair to removeprefix() from an earlier set.",
    ),
    dict(
        id=5, ledger="P180", concept="PY3 isspace", tier="1 - Strings",
        title="isspace(): nothing but whitespace", kind="function",
        func="is_blank",
        cases=[("   ",), ("",), (" a ",), ("\t\n",)],
        prompt=(
            "Write a function `is_blank(s)` that returns True when s is"
            " made only of whitespace -- spaces, tabs, newlines -- and"
            " has at least one character, using isspace():\n\n"
            "  is_blank(\"   \") -> True\n"
            "  is_blank(\"\") -> False\n\n"
            "Return: True or False."
        ),
        solution="def is_blank(s):\n    return s.isspace()\n",
        trap="def is_blank(s):\n    return s.strip() == \"\"\n",
        note="isspace() is True only when every character is whitespace"
             " AND there is at least one -- the empty string is False,"
             " like the other is...() methods. strip() == '' is also"
             " True for the empty string, which the question excludes.",
    ),
    # ============================================================== 2 Numbers
    dict(
        id=6, ledger="P181", concept="PY3 int base", tier="2 - Numbers",
        title="int(s, 2): a binary string to a number", kind="function",
        func="from_binary",
        cases=[("101",), ("0",), ("11111111",), ("10",)],
        prompt=(
            "Write a function `from_binary(s)` that returns the integer a"
            " string of 0s and 1s stands for in base two, using int()"
            " with a base:\n\n"
            "  from_binary(\"101\") -> 5\n\n"
            "Return: an integer."
        ),
        solution="def from_binary(s):\n    return int(s, 2)\n",
        trap="def from_binary(s):\n    return int(s)\n",
        note="int() takes an optional base, and 2 reads the digits as"
             " binary. Without it the string is read as decimal, so"
             " '101' is a hundred and one. The same call with 16 reads"
             " hexadecimal.",
    ),
    dict(
        id=7, ledger="P182", concept="PY3 format binary", tier="2 - Numbers",
        title="format(n, 'b'): a number as binary digits", kind="function",
        func="to_binary",
        cases=[(5,), (0,), (255,), (2,)],
        prompt=(
            "Write a function `to_binary(n)` that returns the binary"
            " digits of a non-negative integer as a string, with no"
            " prefix, using format() with the 'b' spec:\n\n"
            "  to_binary(5) -> \"101\"\n\n"
            "Return: the string."
        ),
        solution="def to_binary(n):\n    return format(n, \"b\")\n",
        trap="def to_binary(n):\n    return bin(n)\n",
        note="bin() returns '0b101', with the prefix that marks a binary"
             " literal in source code. format(n, 'b') is the bare digits"
             " -- the same spec as f'{n:b}'. 'x' gives hexadecimal and"
             " 'o' octal the same way.",
    ),
    dict(
        id=8, ledger="P183", concept="PY3 math gcd", tier="2 - Numbers",
        title="math.gcd(): the greatest common divisor", kind="function",
        func="common_factor",
        cases=[(12, 18), (7, 13), (0, 9), (100, 75)],
        prompt=(
            "Write a function `common_factor(a, b)` that returns the"
            " largest whole number that divides both a and b, using"
            " math.gcd(). Remember the import.\n\n"
            "  common_factor(12, 18) -> 6\n\n"
            "Return: an integer."
        ),
        solution=("import math\n\n"
                  "def common_factor(a, b):\n"
                  "    return math.gcd(a, b)\n"),
        trap="def common_factor(a, b):\n    return min(a, b)\n",
        note="The smaller number is the gcd only when it divides the"
             " larger: 12 and 18 share 6, not 12. math.gcd() does the"
             " Euclidean algorithm for you, and gcd(0, n) is n.",
    ),
    dict(
        id=9, ledger="P184", concept="PY3 percent spec", tier="2 - Numbers",
        title="f'{x:.1%}': a fraction as a percentage", kind="function",
        func="as_percent",
        cases=[(0.258,), (1.0,), (0.0,), (0.04567,)],
        prompt=(
            "Write a function `as_percent(x)` that returns the fraction x"
            " as a percentage string with one decimal and a % sign,"
            " using the .1% format spec in an f-string:\n\n"
            "  as_percent(0.258) -> \"25.8%\"\n\n"
            "Return: the string."
        ),
        solution="def as_percent(x):\n    return f\"{x:.1%}\"\n",
        trap="def as_percent(x):\n    return f\"{x:.1f}%\"\n",
        note="The % spec multiplies by 100, rounds to the decimals asked"
             " for and appends the sign, all in one. .1f with a % typed"
             " after it formats the raw fraction, so 0.258 becomes"
             " '0.3%'.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=10, ledger="P185", concept="PY3 sorted key lower", tier="3 - Lists",
        title="sorted(key=str.lower): alphabetical, not ASCII", kind="function",
        func="alphabetical",
        cases=[(["banana", "Apple", "cherry"],), (["b", "A", "C", "a"],), ([],)],
        prompt=(
            "Write a function `alphabetical(words)` that returns the"
            " words sorted alphabetically IGNORING case, using sorted()"
            " with key=str.lower:\n\n"
            "  alphabetical([\"banana\", \"Apple\", \"cherry\"]) ->"
            " [\"Apple\", \"banana\", \"cherry\"]\n\n"
            "Return: the new list."
        ),
        solution="def alphabetical(words):\n    return sorted(words, key=str.lower)\n",
        trap="def alphabetical(words):\n    return sorted(words)\n",
        note="Plain sorted() orders by character code, and every capital"
             " comes before every lower-case letter, so 'Zoo' sorts"
             " before 'apple'. key=str.lower sorts by the lower-cased"
             " word while returning the original spelling. Equal keys"
             " keep their original order.",
    ),
    dict(
        id=11, ledger="P186", concept="PY3 list count", tier="3 - Lists",
        title="list.count(): how many times", kind="function",
        func="times",
        cases=[(["LS1", "BD3", "LS1"], "LS1"), ([1, 2, 3], 4), ([], "x"), ([None, None], None)],
        prompt=(
            "Write a function `times(values, x)` that returns how many"
            " times x appears in the list, as an integer, using the"
            " list's count() method:\n\n"
            "  times([\"LS1\", \"BD3\", \"LS1\"], \"LS1\") -> 2\n\n"
            "Return: an integer."
        ),
        solution="def times(values, x):\n    return values.count(x)\n",
        trap="def times(values, x):\n    return x in values\n",
        note="count() returns a number, 0 when the value is absent; the"
             " in test returns True or False and says nothing about how"
             " many. True is not 2, and the grader keeps bool and int"
             " apart. Lists and strings both have a count() method.",
    ),
    dict(
        id=12, ledger="P187", concept="PY3 range step", tier="3 - Lists",
        title="range(start, stop, step): the even numbers", kind="function",
        func="evens_up_to",
        cases=[(10,), (7,), (0,), (1,)],
        prompt=(
            "Write a function `evens_up_to(n)` that returns the list of"
            " even numbers from 0 up to and INCLUDING n when n is even,"
            " using list() over range() with a step of 2:\n\n"
            "  evens_up_to(10) -> [0, 2, 4, 6, 8, 10]\n\n"
            "Return: the list."
        ),
        solution="def evens_up_to(n):\n    return list(range(0, n + 1, 2))\n",
        trap="def evens_up_to(n):\n    return list(range(0, n, 2))\n",
        note="range() stops BEFORE its stop value, so including n means"
             " stopping at n + 1. The third argument is the step. list()"
             " is needed because range() is a lazy sequence, not a list.",
    ),
    # ========================================================= 4 Sets and dicts
    dict(
        id=13, ledger="P188", concept="PY3 set subset", tier="4 - Sets and dictionaries",
        title="<= on sets: is everything wanted available?", kind="function",
        func="all_available",
        cases=[(["pen", "ink"], ["ink", "pen", "paper"]), (["pen", "glue"], ["ink", "pen"]),
               ([], ["ink"]), (["ink"], [])],
        prompt=(
            "Write a function `all_available(wanted, stock)` that returns"
            " True when every wanted item is in stock, using set() on"
            " each and the <= operator -- subset:\n\n"
            "  all_available([\"pen\", \"ink\"], [\"ink\", \"pen\","
            " \"paper\"]) -> True\n\n"
            "Return: True or False."
        ),
        solution="def all_available(wanted, stock):\n    return set(wanted) <= set(stock)\n",
        trap="def all_available(wanted, stock):\n    return set(stock) <= set(wanted)\n",
        note="a <= b on sets asks whether a is a subset of b -- every"
             " member of a is in b. Reversed, it asks whether the whole"
             " stock is wanted, a different question. The empty set is a"
             " subset of everything, so wanting nothing is always"
             " satisfied. issubset() is the same test spelled out.",
    ),
    dict(
        id=14, ledger="P189", concept="PY3 dict setdefault", tier="4 - Sets and dictionaries",
        title="setdefault(): a list for each key, made on demand", kind="function",
        func="add_to_group",
        cases=[({"fiction": ["A"]}, "fiction", "B"), ({"fiction": ["A"]}, "poetry", "C"),
               ({}, "x", 1)],
        prompt=(
            "Write a function `add_to_group(groups, key, item)` that"
            " appends item to the list stored under key in the dict,"
            " creating an empty list there first if the key is new, and"
            " returns the dict -- using setdefault():\n\n"
            "  add_to_group({\"fiction\": [\"A\"]}, \"fiction\", \"B\")"
            " -> {\"fiction\": [\"A\", \"B\"]}\n\n"
            "Return: the dictionary."
        ),
        solution=("def add_to_group(groups, key, item):\n"
                  "    groups.setdefault(key, []).append(item)\n"
                  "    return groups\n"),
        trap=("def add_to_group(groups, key, item):\n"
              "    groups[key] = [item]\n"
              "    return groups\n"),
        note="setdefault(key, []) returns the list already under key, or"
             " stores and returns a new empty one -- so the append lands"
             " in the right place either way. Assigning a fresh [item]"
             " throws away whatever the key already held.",
    ),
    dict(
        id=15, ledger="P190", concept="PY3 in dict", tier="4 - Sets and dictionaries",
        title="in on a dict: is the key there?", kind="function",
        func="has_area",
        cases=[({"LS1": 95, "BD3": 90}, "LS1"), ({"LS1": 95}, "95"), ({}, "LS1"), ({"a": None}, "a")],
        prompt=(
            "Write a function `has_area(counts, area)` that returns True"
            " when area is a KEY of the dict, whatever its value, using"
            " the in test on the dict itself:\n\n"
            "  has_area({\"LS1\": 95}, \"LS1\") -> True\n\n"
            "Return: True or False."
        ),
        solution="def has_area(counts, area):\n    return area in counts\n",
        trap="def has_area(counts, area):\n    return area in counts.values()\n",
        note="in on a dict tests the KEYS; counts.values() tests the"
             " values, and counts.items() the pairs. A key whose value is"
             " None is still present, which is why 'in' and not 'get()'"
             " is the test for presence.",
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
