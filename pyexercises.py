"""Python practice exercises: fifteen functions in three shapes.

The eleventh Python set, and a MIXED one: five one-tool functions on tools
no earlier set used (endswith() with a tuple, round() to a negative place,
split() with maxsplit, enumerate() with start, ljust() with a fill), five
functions with one loop or one if inside -- the longest word, a capped
late fee, overdue dates counted, the first negative found, squares under a
limit -- and five functions over LIBRARY ROWS, lists of dicts shaped like
loans, fines, copies and holds: open loans, what each member owes, the
busiest branch, late returns counted, members with enough holds.

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

LOANS = [{"loan_id": 1, "member": 7, "due": "2026-03-10", "returned": "2026-03-08"},
         {"loan_id": 2, "member": 9, "due": "2026-03-12", "returned": None},
         {"loan_id": 3, "member": 7, "due": "2026-04-01", "returned": "2026-04-05"},
         {"loan_id": 4, "member": 2, "due": "2026-04-20", "returned": "2026-04-20"},
         {"loan_id": 5, "member": 9, "due": "2026-05-02", "returned": None}]

FINES = [{"fine_id": 1, "member": 7, "pence": 220, "paid": "2026-03-12"},
         {"fine_id": 2, "member": 9, "pence": 200, "paid": None},
         {"fine_id": 3, "member": 7, "pence": 60, "paid": None},
         {"fine_id": 4, "member": 2, "pence": 1000, "paid": "2026-05-01"},
         {"fine_id": 5, "member": 9, "pence": 40, "paid": None}]

COPIES = [{"copy_id": 1, "branch": "Central"}, {"copy_id": 2, "branch": "Hilltop"},
          {"copy_id": 3, "branch": "Central"}, {"copy_id": 4, "branch": "Riverside"},
          {"copy_id": 5, "branch": "Central"}, {"copy_id": 6, "branch": "Hilltop"}]

HOLDS = [{"hold_id": 1, "member": 7, "book": 12}, {"hold_id": 2, "member": 9, "book": 12},
         {"hold_id": 3, "member": 7, "book": 40}, {"hold_id": 4, "member": 7, "book": 55},
         {"hold_id": 5, "member": 2, "book": 12}, {"hold_id": 6, "member": 9, "book": 7}]

EXERCISES = [
    # ============================================================= 1 One tool
    dict(
        id=1, ledger="P161", concept="PY3 endswith tuple", tier="1 - One tool",
        title="endswith(tuple): is it an image file?", kind="function",
        func="is_image",
        cases=[("cover.jpg",), ("map.png",), ("cover.PNG",), ("notes.txt",), ("photo.gif",)],
        prompt=(
            "Write a function `is_image(filename)` that returns True when"
            " the name ends in '.jpg', '.png' or '.gif' -- exactly those,"
            " lower case -- using endswith() with a TUPLE of endings:\n\n"
            "  is_image(\"cover.jpg\") -> True\n"
            "  is_image(\"cover.PNG\") -> False\n\n"
            "Return: True or False."
        ),
        solution="def is_image(filename):\n    return filename.endswith((\".jpg\", \".png\", \".gif\"))\n",
        trap="def is_image(filename):\n    return filename.endswith(\".jpg\" or \".png\" or \".gif\")\n",
        note="endswith() accepts a tuple and is true if ANY of its"
             " members matches. Written with 'or', the expression"
             " '.jpg' or '.png' is evaluated first and is just '.jpg' --"
             " a non-empty string is truthy, so 'or' stops there -- and"
             " the .png and .gif names are refused.",
    ),
    dict(
        id=2, ledger="P162", concept="PY3 round negative", tier="1 - One tool",
        title="round(n, -2): to the nearest hundred", kind="function",
        func="nearest_hundred",
        cases=[(1234,), (1250,), (49,), (99950,)],
        prompt=(
            "Write a function `nearest_hundred(n)` that returns n rounded"
            " to the nearest hundred, using round() with a NEGATIVE"
            " second argument:\n\n"
            "  nearest_hundred(1234) -> 1200\n\n"
            "Return: an integer."
        ),
        solution="def nearest_hundred(n):\n    return round(n, -2)\n",
        trap="def nearest_hundred(n):\n    return round(n, 2)\n",
        note="The second argument of round() is the decimal place, and a"
             " negative one counts to the LEFT of the point: -2 is the"
             " hundreds. round(n, 2) rounds to two decimals, which for an"
             " integer changes nothing. Half-way values go to the even"
             " hundred, so 1250 becomes 1200.",
    ),
    dict(
        id=3, ledger="P163", concept="PY3 split maxsplit", tier="1 - One tool",
        title="split(maxsplit=1): the first word and the rest", kind="function",
        func="first_and_rest",
        cases=[("The Glass Path",), ("Hidden",), ("A History of Stone Doors",), ("",)],
        prompt=(
            "Write a function `first_and_rest(title)` that returns a list"
            " of at most two strings: the first word, and everything"
            " after it as ONE string, using split() with maxsplit=1:\n\n"
            "  first_and_rest(\"The Glass Path\") -> [\"The\", \"Glass"
            " Path\"]\n\n"
            "A one-word title gives a one-item list; '' gives [].\n\n"
            "Return: the list."
        ),
        solution="def first_and_rest(title):\n    return title.split(maxsplit=1)\n",
        trap="def first_and_rest(title):\n    return title.split()\n",
        note="maxsplit limits how many splits happen, so the remainder"
             " stays in one piece; split() with no limit breaks at every"
             " space. The empty string splits to [] either way, and a"
             " single word has nothing to split.",
    ),
    dict(
        id=4, ledger="P164", concept="PY3 enumerate start", tier="1 - One tool",
        title="enumerate(start=1): numbering from one", kind="function",
        func="numbered",
        cases=[(["Aisha", "Kwame"],), ([],), (["solo"],)],
        prompt=(
            "Write a function `numbered(names)` that returns a list of"
            " (position, name) tuples with positions starting at 1, using"
            " list() over enumerate() with start=1:\n\n"
            "  numbered([\"Aisha\", \"Kwame\"]) -> [(1, \"Aisha\"), (2,"
            " \"Kwame\")]\n\n"
            "Return: the list of tuples."
        ),
        solution="def numbered(names):\n    return list(enumerate(names, start=1))\n",
        trap="def numbered(names):\n    return list(enumerate(names))\n",
        note="enumerate() pairs each item with a counter that starts at 0"
             " unless told otherwise; start=1 is the keyword for the"
             " human numbering a list on screen wants. list() is needed"
             " because enumerate() returns an iterator, not a list.",
    ),
    dict(
        id=5, ledger="P165", concept="PY3 ljust fill", tier="1 - One tool",
        title="ljust(width, '.'): a dotted leader", kind="function",
        func="leader",
        cases=[("Fiction", 12), ("Travel", 12), ("Biographies", 12), ("Far too long", 5)],
        prompt=(
            "Write a function `leader(label, width)` that returns label"
            " padded on the RIGHT with dots to the given width -- like a"
            " line in a contents page -- using ljust() with '.' as the"
            " fill character:\n\n"
            "  leader(\"Travel\", 12) -> \"Travel......\"\n\n"
            "A label already wider than width is returned unchanged.\n\n"
            "Return: the string."
        ),
        solution="def leader(label, width):\n    return label.ljust(width, \".\")\n",
        trap="def leader(label, width):\n    return label.rjust(width, \".\")\n",
        note="ljust() keeps the text on the LEFT and pads to its right;"
             " rjust() puts the dots in front. Both take an optional fill"
             " character, default a space, and neither truncates.",
    ),
    # ======================================================= 2 A loop or an if
    dict(
        id=6, ledger="P166", concept="PY4 loop max", tier="2 - A loop or an if",
        title="The longest word, by a loop", kind="function",
        func="longest",
        cases=[(["pen", "paper", "ink"],), (["ab", "cd"],), (["zebra", "apple", "mango"],), (["x"],)],
        prompt=(
            "Write a function `longest(words)` that returns the longest"
            " word in a non-empty list, the FIRST one when several share"
            " the length, using a for loop that keeps the best so far."
            " Do not use max() for this one.\n\n"
            "  longest([\"pen\", \"paper\", \"ink\"]) -> \"paper\"\n\n"
            "Return: the word."
        ),
        solution=("def longest(words):\n"
                  "    best = words[0]\n"
                  "    for w in words:\n"
                  "        if len(w) > len(best):\n"
                  "            best = w\n"
                  "    return best\n"),
        trap=("def longest(words):\n"
              "    best = words[0]\n"
              "    for w in words:\n"
              "        if w > best:\n"
              "            best = w\n"
              "    return best\n"),
        note="Comparing the words themselves, w > best, is alphabetical:"
             " 'zebra' beats 'apple' whatever their lengths. The"
             " comparison has to be of len(w) and len(best). The strict"
             " > is what keeps the FIRST of equals -- a later word of"
             " the same length does not replace it.",
    ),
    dict(
        id=7, ledger="P167", concept="PY4 if cap", tier="2 - A loop or an if",
        title="A late fee with a cap", kind="function",
        func="late_fee",
        cases=[(3,), (0,), (-2,), (80,), (50,)],
        prompt=(
            "Write a function `late_fee(days_late)` that returns the fee"
            " in pence: 20 a day, but never more than 1000, and 0 when"
            " days_late is zero or negative. An if for the no-fee case,"
            " then the cap.\n\n"
            "  late_fee(3) -> 60\n"
            "  late_fee(80) -> 1000\n\n"
            "Return: an integer."
        ),
        solution=("def late_fee(days_late):\n"
                  "    if days_late <= 0:\n"
                  "        return 0\n"
                  "    return min(20 * days_late, 1000)\n"),
        trap=("def late_fee(days_late):\n"
              "    if days_late <= 0:\n"
              "        return 0\n"
              "    return 20 * days_late\n"),
        note="Two rules, two places: the early return handles 'no fee',"
             " and min(fee, 1000) is the cap -- the smaller of the"
             " computed fee and the ceiling. Without the cap eighty days"
             " costs 1600, which the library's own fines never reach.",
    ),
    dict(
        id=8, ledger="P168", concept="PY4 loop count if", tier="2 - A loop or an if",
        title="Overdue dates, counted", kind="function",
        func="count_overdue",
        cases=[(["2026-06-01", "2026-06-30", "2026-07-02"], "2026-06-30"),
               ([], "2026-06-30"), (["2026-01-01"], "2026-06-30"), (["2026-06-30"], "2026-06-30")],
        prompt=(
            "Write a function `count_overdue(due_dates, today)` that"
            " returns how many of the 'YYYY-MM-DD' strings are BEFORE"
            " today -- a loan due today is not yet overdue. A loop with"
            " an if and a counter; the strings compare correctly as they"
            " are.\n\n"
            "  count_overdue([\"2026-06-01\", \"2026-06-30\","
            " \"2026-07-02\"], \"2026-06-30\") -> 1\n\n"
            "Return: an integer."
        ),
        solution=("def count_overdue(due_dates, today):\n"
                  "    n = 0\n"
                  "    for d in due_dates:\n"
                  "        if d < today:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_overdue(due_dates, today):\n"
              "    n = 0\n"
              "    for d in due_dates:\n"
              "        if d <= today:\n"
              "            n += 1\n"
              "    return n\n"),
        note="Overdue means the due date has passed, so the test is"
             " strictly before: d < today. With <= a loan due today is"
             " counted, which is the same off-by-one as the SQL version"
             " of this question. ISO dates sort as text because the"
             " biggest unit comes first.",
    ),
    dict(
        id=9, ledger="P169", concept="PY4 loop find index", tier="2 - A loop or an if",
        title="Where the first negative is", kind="function",
        func="first_negative",
        cases=[([3, 1, -4, 1, -5],), ([1, 2, 3],), ([],), ([-7],)],
        prompt=(
            "Write a function `first_negative(values)` that returns the"
            " POSITION of the first value below zero, or -1 if there is"
            " none, using a loop over enumerate() that returns as soon as"
            " it finds one:\n\n"
            "  first_negative([3, 1, -4, 1, -5]) -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def first_negative(values):\n"
                  "    for i, v in enumerate(values):\n"
                  "        if v < 0:\n"
                  "            return i\n"
                  "    return -1\n"),
        trap=("def first_negative(values):\n"
              "    for i, v in enumerate(values):\n"
              "        if v < 0:\n"
              "            return v\n"
              "    return -1\n"),
        note="enumerate() gives both the position and the value, and the"
             " question asks for the position: return i, not v. A return"
             " inside the loop ends the search at the first match, and"
             " the return after the loop is only reached when nothing"
             " matched.",
    ),
    dict(
        id=10, ledger="P170", concept="PY4 while", tier="2 - A loop or an if",
        title="Squares below a limit", kind="function",
        func="squares_below",
        cases=[(30,), (1,), (0,), (100,)],
        prompt=(
            "Write a function `squares_below(limit)` that returns the"
            " list of square numbers 1, 4, 9, ... that are strictly LESS"
            " than limit, using a while loop that stops as soon as the"
            " next square is too big:\n\n"
            "  squares_below(30) -> [1, 4, 9, 16, 25]\n\n"
            "Return: the list."
        ),
        solution=("def squares_below(limit):\n"
                  "    out = []\n"
                  "    n = 1\n"
                  "    while n * n < limit:\n"
                  "        out.append(n * n)\n"
                  "        n += 1\n"
                  "    return out\n"),
        trap=("def squares_below(limit):\n"
              "    out = []\n"
              "    n = 1\n"
              "    while n * n <= limit:\n"
              "        out.append(n * n)\n"
              "        n += 1\n"
              "    return out\n"),
        note="A while loop runs for as long as its condition holds, and"
             " the condition is the question's own words: n * n < limit."
             " With <= a limit that is itself a square, like 100, is"
             " included. For limit 1 the loop body never runs and the"
             " empty list is right.",
    ),
    # ========================================================= 3 Library rows
    dict(
        id=11, ledger="P171", concept="PY5 filter None", tier="3 - Library rows",
        title="Loans still out", kind="function",
        func="open_loans",
        cases=[(LOANS,), ([],), (LOANS[:1],)],
        prompt=(
            "Each loan is a dict with keys loan_id, member, due and"
            " returned, where returned is None while the book is out."
            " Write a function `open_loans(loans)` that returns a list of"
            " the loan_ids of the loans still out, in the order given:\n\n"
            "  open_loans(LOANS) -> [2, 5]\n\n"
            "Return: a list of integers."
        ),
        solution=("def open_loans(loans):\n"
                  "    return [l[\"loan_id\"] for l in loans if l[\"returned\"] is None]\n"),
        trap=("def open_loans(loans):\n"
              "    return [l for l in loans if l[\"returned\"] is None]\n"),
        note="The filter is right in both; the difference is what is"
             " collected. The question asks for ids, and a list of whole"
             " dicts is a different answer however right the rows are."
             " 'is None' is the test for a missing value -- SQL's IS"
             " NULL.",
    ),
    dict(
        id=12, ledger="P172", concept="PY5 sum by key", tier="3 - Library rows",
        title="Unpaid fines, per member", kind="function",
        func="owed_by_member",
        cases=[(FINES,), ([],), (FINES[:2],)],
        prompt=(
            "Each fine is a dict with keys fine_id, member, pence and"
            " paid, where paid is None while the fine is unpaid. Write a"
            " function `owed_by_member(fines)` that returns a dict"
            " mapping each member to the total pence of their UNPAID"
            " fines -- members with nothing unpaid are left out:\n\n"
            "  owed_by_member(FINES) -> {9: 240, 7: 60}\n\n"
            "Return: the dictionary."
        ),
        solution=("def owed_by_member(fines):\n"
                  "    owed = {}\n"
                  "    for f in fines:\n"
                  "        if f[\"paid\"] is None:\n"
                  "            owed[f[\"member\"]] = owed.get(f[\"member\"], 0) + f[\"pence\"]\n"
                  "    return owed\n"),
        trap=("def owed_by_member(fines):\n"
              "    owed = {}\n"
              "    for f in fines:\n"
              "        owed[f[\"member\"]] = owed.get(f[\"member\"], 0) + f[\"pence\"]\n"
              "    return owed\n"),
        note="A total per key is a dict and get(key, 0): the first time a"
             " member appears the 0 starts the sum. The if is the WHERE"
             " paid IS NULL of this question -- without it the dict is"
             " each member's lifetime fines, and member 2, who has paid,"
             " appears when they should not.",
    ),
    dict(
        id=13, ledger="P173", concept="PY5 argmax count", tier="3 - Library rows",
        title="The branch with the most copies", kind="function",
        func="busiest_branch",
        cases=[(COPIES,), (COPIES[1:2],), (COPIES[1:4],)],
        prompt=(
            "Each copy is a dict with keys copy_id and branch. Write a"
            " function `busiest_branch(copies)` that returns the NAME of"
            " the branch holding the most copies in a non-empty list --"
            " count per branch first, then pick the largest, the first"
            " such branch if two tie:\n\n"
            "  busiest_branch(COPIES) -> \"Central\"\n\n"
            "Return: the branch name."
        ),
        solution=("def busiest_branch(copies):\n"
                  "    counts = {}\n"
                  "    for c in copies:\n"
                  "        counts[c[\"branch\"]] = counts.get(c[\"branch\"], 0) + 1\n"
                  "    return max(counts, key=counts.get)\n"),
        trap=("def busiest_branch(copies):\n"
              "    counts = {}\n"
              "    for c in copies:\n"
              "        counts[c[\"branch\"]] = counts.get(c[\"branch\"], 0) + 1\n"
              "    return max(counts.values())\n"),
        note="max(counts.values()) is the biggest COUNT, a number; the"
             " question wants the branch that has it. max(counts,"
             " key=counts.get) iterates the keys and compares them by"
             " their counts, returning the key -- and for a tie, the"
             " first key encountered, which is the first branch seen.",
    ),
    dict(
        id=14, ledger="P174", concept="PY5 count with None", tier="3 - Library rows",
        title="Late returns, counted", kind="function",
        func="late_returns",
        cases=[(LOANS,), ([],), (LOANS[1:2],), (LOANS[2:4],)],
        prompt=(
            "Using the same loan dicts (loan_id, member, due, returned,"
            " with returned None while out), write a function"
            " `late_returns(loans)` that returns how many loans came back"
            " AFTER their due date. A loan still out is not late -- and"
            " None cannot be compared with a string, so test it first:\n\n"
            "  late_returns(LOANS) -> 1\n\n"
            "Return: an integer."
        ),
        solution=("def late_returns(loans):\n"
                  "    n = 0\n"
                  "    for l in loans:\n"
                  "        if l[\"returned\"] is not None and l[\"returned\"] > l[\"due\"]:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def late_returns(loans):\n"
              "    n = 0\n"
              "    for l in loans:\n"
              "        if l[\"returned\"] > l[\"due\"]:\n"
              "            n += 1\n"
              "    return n\n"),
        note="SQL quietly makes NULL > 'date' false; Python raises"
             " TypeError when None meets a string in >. The 'is not None'"
             " goes FIRST in the and, because 'and' stops at the first"
             " false operand and the comparison is never attempted for"
             " an open loan.",
    ),
    dict(
        id=15, ledger="P175", concept="PY5 having", tier="3 - Library rows",
        title="Members with enough holds", kind="function",
        func="members_with_holds",
        cases=[(HOLDS, 2), (HOLDS, 3), (HOLDS, 1), ([], 1)],
        prompt=(
            "Each hold is a dict with keys hold_id, member and book."
            " Write a function `members_with_holds(holds, at_least)` that"
            " returns a sorted list of the members who have placed"
            " at_least holds OR MORE -- count per member, then keep the"
            " ones that reach the threshold:\n\n"
            "  members_with_holds(HOLDS, 2) -> [7, 9]\n\n"
            "Return: a sorted list of member ids."
        ),
        solution=("def members_with_holds(holds, at_least):\n"
                  "    counts = {}\n"
                  "    for h in holds:\n"
                  "        counts[h[\"member\"]] = counts.get(h[\"member\"], 0) + 1\n"
                  "    return sorted(m for m, n in counts.items() if n >= at_least)\n"),
        trap=("def members_with_holds(holds, at_least):\n"
              "    counts = {}\n"
              "    for h in holds:\n"
              "        counts[h[\"member\"]] = counts.get(h[\"member\"], 0) + 1\n"
              "    return sorted(m for m, n in counts.items() if n > at_least)\n"),
        note="This is GROUP BY member HAVING COUNT(*) >= n in Python: a"
             " counting dict, then a filter over its items. 'At least'"
             " is >=, and the strict > drops every member who has"
             " exactly the threshold -- with at_least 1 that is member"
             " 2, who has one hold.",
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
