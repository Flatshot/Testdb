"""Python practice exercises: fifteen functions of two or three tools.

The sixteenth Python set, and a step UP from the one-tool sets: every
question asks for a function that combines two or three tools, and the
prompt NAMES every tool it needs -- split() and join() and title(), a
Counter and its most_common(), sorted() with a lambda key, a set
comprehension with int() and strip(), date.fromisoformat() with strftime(),
dict.fromkeys() for order-keeping deduplication, and so on. The title
names the task; the prompt lists the tools.

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
        id=1, ledger="P236", concept="PY6 split join title", tier="1 - Strings",
        title="A name tidied up", kind="function",
        func="tidy_name",
        cases=[("  aisha   ekwueme ",), ("KWAME BAXTER",), ("rosa",), ("",)],
        prompt=(
            "Write a function `tidy_name(s)` that returns the name with"
            " extra spaces removed -- one space between words, none at"
            " the ends -- and each word capitalised. Tools: split() with"
            " no argument to break on any whitespace, \" \".join() to"
            " put the words back, and title() for the capitals.\n\n"
            "  tidy_name(\"  aisha   ekwueme \") -> \"Aisha Ekwueme\"\n\n"
            "Return: the new string."
        ),
        solution="def tidy_name(s):\n    return \" \".join(s.split()).title()\n",
        trap="def tidy_name(s):\n    return s.title()\n",
        note="split() with no argument splits on any run of whitespace"
             " and drops the empty pieces, so joining the words with one"
             " space normalises the spacing in one move. title() alone"
             " fixes the capitals and leaves every stray space where it"
             " was.",
    ),
    dict(
        id=2, ledger="P237", concept="PY6 split comprehension join", tier="1 - Strings",
        title="Initials from a full name", kind="function",
        func="initials",
        cases=[("aisha ekwueme",), ("Bartholomew van Hollingsworth",), ("Rosa",), ("",)],
        prompt=(
            "Write a function `initials(name)` that returns the first"
            " letter of each word, upper case, run together. Tools:"
            " split() to get the words, a generator or list"
            " comprehension taking w[0] from each, \"\".join() to"
            " combine them, and upper().\n\n"
            "  initials(\"aisha ekwueme\") -> \"AE\"\n\n"
            "Return: the string."
        ),
        solution="def initials(name):\n    return \"\".join(w[0] for w in name.split()).upper()\n",
        trap="def initials(name):\n    return \"\".join(w[0] for w in name.split())\n",
        note="Three tools in a row: split into words, take the first"
             " character of each, join with nothing between. upper()"
             " on the result handles a name typed in lower case; without"
             " it 'aisha ekwueme' gives 'ae'. The empty string splits to"
             " no words and joins to ''.",
    ),
    dict(
        id=3, ledger="P238", concept="PY6 Counter most_common", tier="1 - Strings",
        title="The two commonest words", kind="function",
        func="top_two_words",
        cases=[("the cat and the dog and the bird",), ("The the THE",), ("one",), ("a b b a",)],
        prompt=(
            "Write a function `top_two_words(text)` that returns a list"
            " of the two most frequent words as (word, count) tuples,"
            " commonest first, counting words regardless of case and"
            " reporting them in lower case. Tools: lower(), split(),"
            " collections.Counter and its most_common(2). Remember the"
            " import.\n\n"
            "  top_two_words(\"the cat and the dog and the bird\") ->"
            " [(\"the\", 3), (\"and\", 2)]\n\n"
            "Return: the list of tuples."
        ),
        solution=("from collections import Counter\n\n"
                  "def top_two_words(text):\n"
                  "    return Counter(text.lower().split()).most_common(2)\n"),
        trap=("from collections import Counter\n\n"
              "def top_two_words(text):\n"
              "    return Counter(text.split()).most_common(2)\n"),
        note="lower() BEFORE counting is what makes 'The' and 'the' one"
             " word; counted as typed they are two. most_common(n)"
             " returns the n biggest counts as (value, count) tuples,"
             " ties in first-seen order, and fewer than n when there are"
             " fewer distinct words.",
    ),
    dict(
        id=4, ledger="P239", concept="PY6 format specs", tier="1 - Strings",
        title="A line of a price list", kind="function",
        func="price_line",
        cases=[("Fine", 220), ("Replacement copy", 1500), ("Card", 5)],
        prompt=(
            "Write a function `price_line(label, pence)` that returns the"
            " label padded on the right to 18 characters followed by the"
            " amount in pounds, right-aligned in 8 characters with two"
            " decimals. Tools: an f-string with the :<18 spec for the"
            " label and the :>8.2f spec for pence / 100.\n\n"
            "  price_line(\"Fine\", 220) -> \"Fine                  2.20\"\n\n"
            "Return: the string."
        ),
        solution="def price_line(label, pence):\n    return f\"{label:<18}{pence / 100:>8.2f}\"\n",
        trap="def price_line(label, pence):\n    return f\"{label} {pence / 100:.2f}\"\n",
        note="A format spec can set width and alignment as well as"
             " decimals: <18 pads the label on the right to a fixed"
             " column, >8.2f right-aligns the number in eight characters"
             " with two decimals, so a list of these lines up. Without"
             " the widths the amounts wander with the label's length.",
    ),
    dict(
        id=5, ledger="P240", concept="PY6 lstrip float round", tier="1 - Strings",
        title="Pounds in text to pence", kind="function",
        func="pence_from_text",
        cases=[("£12.40",), ("£0.29",), ("£3",), ("£1.15",)],
        prompt=(
            "Write a function `pence_from_text(s)` that turns an amount"
            " written like '£12.40' into whole pence. Tools: lstrip('£')"
            " to drop the sign, float() to read the number, multiply by"
            " 100, and round() -- NOT int() -- to get back to a whole"
            " number.\n\n"
            "  pence_from_text(\"£12.40\") -> 1240\n\n"
            "Return: an integer."
        ),
        solution="def pence_from_text(s):\n    return round(float(s.lstrip(\"£\")) * 100)\n",
        trap="def pence_from_text(s):\n    return int(float(s.lstrip(\"£\")) * 100)\n",
        note="0.29 is not exactly representable, and 0.29 * 100 comes"
             " out as 28.999999999999996; int() truncates that to 28,"
             " round() takes it to 29. Whenever a float is turned into a"
             " count of smaller units, round, do not truncate.",
    ),
    # ==================================================== 2 Numbers and dates
    dict(
        id=6, ledger="P241", concept="PY6 sum len round", tier="2 - Numbers and dates",
        title="An average to one decimal", kind="function",
        func="average",
        cases=[([3, 4, 5],), ([1, 2],), ([7],), ([1.25, 1.75, 2.5],)],
        prompt=(
            "Write a function `average(values)` that returns the mean of"
            " a non-empty list rounded to one decimal. Tools: sum(),"
            " len() and round() with a second argument.\n\n"
            "  average([1, 2]) -> 1.5\n\n"
            "Return: a float."
        ),
        solution="def average(values):\n    return round(sum(values) / len(values), 1)\n",
        trap="def average(values):\n    return round(sum(values) / len(values))\n",
        note="The second argument of round() is the number of decimals;"
             " without it the mean of 1 and 2 becomes 2 -- an int, and"
             " the wrong one. sum() over len() is the mean; statistics."
             "mean() would say the same.",
    ),
    dict(
        id=7, ledger="P242", concept="PY6 fromisoformat strftime", tier="2 - Numbers and dates",
        title="What day of the week a date falls on", kind="function",
        func="weekday_name",
        cases=[("2026-06-30",), ("2025-01-01",), ("2026-02-28",)],
        prompt=(
            "Write a function `weekday_name(date_str)` that returns the"
            " full English weekday name of a 'YYYY-MM-DD' date. Tools:"
            " datetime.date.fromisoformat() to parse it, then strftime("
            "'%A') for the name. Remember the import.\n\n"
            "  weekday_name(\"2026-06-30\") -> \"Tuesday\"\n\n"
            "Return: the string."
        ),
        solution=("from datetime import date\n\n"
                  "def weekday_name(date_str):\n"
                  "    return date.fromisoformat(date_str).strftime(\"%A\")\n"),
        trap=("from datetime import date\n\n"
              "def weekday_name(date_str):\n"
              "    return date.fromisoformat(date_str).strftime(\"%a\")\n"),
        note="fromisoformat() turns the text into a real date, which"
             " knows its weekday; strftime's %A is the full name, %a the"
             " three-letter one. The pair of tools is the Python form of"
             " SQLite's strftime('%w', ...), with names instead of"
             " numbers.",
    ),
    dict(
        id=8, ledger="P243", concept="PY6 date subtraction abs", tier="2 - Numbers and dates",
        title="Days between two dates, either way round", kind="function",
        func="days_between",
        cases=[("2026-06-01", "2026-06-30"), ("2026-06-30", "2026-06-01"), ("2026-01-01", "2026-01-01"),
               ("2025-12-31", "2026-01-01")],
        prompt=(
            "Write a function `days_between(a, b)` that returns the"
            " number of days between two 'YYYY-MM-DD' dates as a"
            " non-negative integer, whichever is earlier. Tools:"
            " date.fromisoformat() on each, subtraction of the two dates"
            " giving a timedelta whose .days is the count, and abs()."
            " Remember the import.\n\n"
            "  days_between(\"2026-06-30\", \"2026-06-01\") -> 29\n\n"
            "Return: an integer."
        ),
        solution=("from datetime import date\n\n"
                  "def days_between(a, b):\n"
                  "    return abs((date.fromisoformat(b) - date.fromisoformat(a)).days)\n"),
        trap=("from datetime import date\n\n"
              "def days_between(a, b):\n"
              "    return (date.fromisoformat(b) - date.fromisoformat(a)).days\n"),
        note="Subtracting two dates gives a timedelta, and .days is the"
             " whole days in it -- negative when the first date is later."
             " abs() makes the answer a distance. This is julianday(b) -"
             " julianday(a) from the SQL side, with the parsing done"
             " explicitly.",
    ),
    # ================================================================ 3 Lists
    dict(
        id=9, ledger="P244", concept="PY6 min max key len", tier="3 - Lists",
        title="The shortest and the longest", kind="function",
        func="shortest_and_longest",
        cases=[(["pen", "paper", "ink"],), (["zebra", "ox"],), (["one"],)],
        prompt=(
            "Write a function `shortest_and_longest(words)` that returns"
            " a tuple of the shortest word and the longest word in a"
            " non-empty list, the first of each when lengths tie. Tools:"
            " min() and max(), both with key=len, packed into a tuple.\n\n"
            "  shortest_and_longest([\"pen\", \"paper\", \"ink\"]) ->"
            " (\"pen\", \"paper\")\n\n"
            "Return: the tuple."
        ),
        solution="def shortest_and_longest(words):\n    return (min(words, key=len), max(words, key=len))\n",
        trap="def shortest_and_longest(words):\n    return (min(words), max(words))\n",
        note="Without key=len, min() and max() compare the words"
             " alphabetically and return the first and last in"
             " dictionary order, which has nothing to do with length."
             " Both keep the FIRST of equals, so 'pen' beats 'ink' for"
             " shortest.",
    ),
    dict(
        id=10, ledger="P245", concept="PY6 strip int set sorted", tier="3 - Lists",
        title="Ids typed by hand, cleaned up", kind="function",
        func="clean_ids",
        cases=[([" 12", "7 ", "12", "003"],), ([],), (["5"],), (["2", " 1 ", "2 "],)],
        prompt=(
            "Write a function `clean_ids(strings)` that turns a list of"
            " id strings with stray spaces and leading zeros into a"
            " sorted list of distinct integers. Tools: strip() and int()"
            " on each string inside a SET comprehension, then sorted()"
            " over the set.\n\n"
            "  clean_ids([\" 12\", \"7 \", \"12\", \"003\"]) -> [3, 7, 12]\n\n"
            "Return: the list."
        ),
        solution="def clean_ids(strings):\n    return sorted({int(s.strip()) for s in strings})\n",
        trap="def clean_ids(strings):\n    return sorted([int(s.strip()) for s in strings])\n",
        note="A set comprehension, with braces, drops the duplicates as"
             " it builds; a list comprehension keeps them, and 12 appears"
             " twice. int() ignores the leading zeros and strip() the"
             " spaces, and sorted() turns the set back into an ordered"
             " list.",
    ),
    dict(
        id=11, ledger="P246", concept="PY6 sorted lambda tuple key", tier="3 - Lists",
        title="Shortest first, then alphabetical", kind="function",
        func="by_length_then_alpha",
        cases=[(["bb", "aa", "c", "ddd"],), ([],), (["b", "a"],), (["pear", "fig", "kiwi", "date"],)],
        prompt=(
            "Write a function `by_length_then_alpha(words)` that returns"
            " the words sorted by length, and alphabetically among words"
            " of the same length. Tools: sorted() with key=lambda w:"
            " (len(w), w) -- a tuple key, compared item by item.\n\n"
            "  by_length_then_alpha([\"bb\", \"aa\", \"c\"]) -> [\"c\","
            " \"aa\", \"bb\"]\n\n"
            "Return: the new list."
        ),
        solution="def by_length_then_alpha(words):\n    return sorted(words, key=lambda w: (len(w), w))\n",
        trap="def by_length_then_alpha(words):\n    return sorted(words, key=len)\n",
        note="A key that returns a tuple sorts by its first item and"
             " breaks ties by the second, which is ORDER BY length, word"
             " in SQL. key=len alone leaves equal-length words in their"
             " ORIGINAL order -- sorted() is stable -- so 'bb' stays"
             " before 'aa'.",
    ),
    dict(
        id=12, ledger="P247", concept="PY6 fromkeys list", tier="3 - Lists",
        title="Duplicates dropped, order kept", kind="function",
        func="dedupe",
        cases=[(["b", "a", "b", "c", "a"],), ([],), ([3, 1, 3],), (["x"],)],
        prompt=(
            "Write a function `dedupe(values)` that returns the values"
            " with repeats removed, keeping the FIRST occurrence of each"
            " and the original order. Tools: dict.fromkeys() -- a dict"
            " keeps insertion order and cannot repeat a key -- and list()"
            " over it.\n\n"
            "  dedupe([\"b\", \"a\", \"b\", \"c\", \"a\"]) -> [\"b\","
            " \"a\", \"c\"]\n\n"
            "Return: the new list."
        ),
        solution="def dedupe(values):\n    return list(dict.fromkeys(values))\n",
        trap="def dedupe(values):\n    return sorted(set(values))\n",
        note="set() removes repeats but forgets the order, and sorting"
             " afterwards imposes a different one. dict.fromkeys() builds"
             " a dict with the values as keys, in the order first seen,"
             " and list() of a dict is its keys -- the standard idiom for"
             " an order-preserving dedupe.",
    ),
    dict(
        id=13, ledger="P248", concept="PY6 range step slice", tier="3 - Lists",
        title="A list cut into chunks", kind="function",
        func="chunks",
        cases=[([1, 2, 3, 4, 5], 2), ([], 3), (["a", "b", "c"], 3), ([1, 2, 3, 4], 1)],
        prompt=(
            "Write a function `chunks(values, n)` that returns a list of"
            " lists, each holding the next n values, the last one shorter"
            " if the count does not divide. Tools: range() from 0 to"
            " len(values) with a step of n, a slice values[i:i + n] for"
            " each start, inside a list comprehension.\n\n"
            "  chunks([1, 2, 3, 4, 5], 2) -> [[1, 2], [3, 4], [5]]\n\n"
            "Return: the list of lists."
        ),
        solution="def chunks(values, n):\n    return [values[i:i + n] for i in range(0, len(values), n)]\n",
        trap="def chunks(values, n):\n    return [values[i:i + n] for i in range(len(values))]\n",
        note="The step in range() is what makes the starts 0, n, 2n ...;"
             " without it every position starts a chunk and the chunks"
             " overlap. A slice past the end is simply shorter, which is"
             " why the last chunk needs no special case.",
    ),
    # ========================================================= 4 Dictionaries
    dict(
        id=14, ledger="P249", concept="PY6 keys union get comprehension", tier="4 - Dictionaries",
        title="Two tallies added together", kind="function",
        func="merge_counts",
        cases=[({"a": 1, "b": 2}, {"b": 3, "c": 4}), ({}, {"x": 1}), ({"k": 5}, {"k": 5}), ({}, {})],
        prompt=(
            "Write a function `merge_counts(a, b)` that returns a new"
            " dict with every key from either tally and the SUM of its"
            " counts from both. Tools: a.keys() | b.keys() for the set of"
            " all keys, get(k, 0) on each dict, and a dict comprehension"
            " over the keys.\n\n"
            "  merge_counts({\"a\": 1, \"b\": 2}, {\"b\": 3, \"c\": 4}) ->"
            " {\"a\": 1, \"b\": 5, \"c\": 4}\n\n"
            "Return: the new dictionary."
        ),
        solution=("def merge_counts(a, b):\n"
                  "    return {k: a.get(k, 0) + b.get(k, 0) for k in a.keys() | b.keys()}\n"),
        trap="def merge_counts(a, b):\n    return a | b\n",
        note="a | b merges the dicts but lets b's value REPLACE a's where"
             " a key is in both -- 'b' becomes 3, not 5. Adding needs"
             " every key from either side, which keys() | keys() gives,"
             " and get(k, 0) so a key missing from one side contributes"
             " nothing rather than an error.",
    ),
    dict(
        id=15, ledger="P250", concept="PY6 set values comprehension sorted", tier="4 - Dictionaries",
        title="Grouped by value", kind="function",
        func="keys_by_value",
        cases=[({"a": 1, "b": 2, "c": 1},), ({},), ({"x": "y"},), ({"p": 0, "q": 0, "r": 0},)],
        prompt=(
            "Write a function `keys_by_value(d)` that returns a dict"
            " mapping each distinct VALUE of d to the sorted list of the"
            " keys that have it. Tools: set(d.values()) for the distinct"
            " values, a dict comprehension over them, and inside it"
            " sorted() of a comprehension picking the keys k where d[k]"
            " equals the value.\n\n"
            "  keys_by_value({\"a\": 1, \"b\": 2, \"c\": 1}) -> {1: [\"a\","
            " \"c\"], 2: [\"b\"]}\n\n"
            "Return: the new dictionary."
        ),
        solution=("def keys_by_value(d):\n"
                  "    return {v: sorted(k for k in d if d[k] == v) for v in set(d.values())}\n"),
        trap="def keys_by_value(d):\n    return {v: k for k, v in d.items()}\n",
        note="Inverting a dict one-to-one loses every key but the last"
             " for a repeated value. Grouping keeps them all: the outer"
             " comprehension runs once per distinct value, and the inner"
             " one collects the keys that map to it. This is GROUP BY"
             " value with GROUP_CONCAT(key) in SQL.",
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
