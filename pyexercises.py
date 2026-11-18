"""Python practice exercises: fifteen everyday functions over plain values.

The fortieth Python set, at the easy level of the last ten -- no
statistics, no dicts -- in the courier's terms, on tasks the earlier sets
did not cover. Text checks and fixes: two codes that are the same once
tidied, a house number at the start of an address, a company name without
its ending, an account number with only its last four showing, a letter
counted in either case. Safe values and labels: a quantity typed into a
form, a number kept within limits, a count with commas, hourly slots,
weekend or not. Lists, split and combined: parcels shelved so many to a
shelf, a load split in two, an item inserted after another, a check that
every status is a known one, numbers lined up on the right.

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
    # ================================================ 1 Text checks and fixes
    dict(
        id=1, ledger="P596", concept="PY3 compare after tidying", tier="1 - Text checks and fixes",
        title="The same code, typed two ways", kind="function",
        func="same_code",
        cases=[("MB-0012", " mb-0012 "), ("MB-0012", "MB-0021"), ("ch-7", "CH-7"), ("", "  "), ("MB-12", "MB -12")],
        prompt=(
            "Write a function `same_code(a, b)` that returns True if"
            " the two codes are the same once spaces at either end are"
            " removed and capitals are ignored. Spaces INSIDE a code"
            " still count as a difference.\n\n"
            "  same_code(\"MB-0012\", \" mb-0012 \") -> True\n"
            "  same_code(\"MB-12\", \"MB -12\") -> False\n\n"
            "Return: a bool."
        ),
        solution=("def same_code(a, b):\n"
                  "    return a.strip().lower() == b.strip().lower()\n"),
        trap=("def same_code(a, b):\n"
              "    return a.lower() == b.lower()\n"),
        note="Tidy both sides the same way, then compare: strip() for"
             " the stray spaces a form or a scanner adds, lower() for"
             " the case. The methods chain because each returns a new"
             " string. The trap lowers and forgets to strip, so the"
             " code somebody typed with a space after it never"
             " matches. Neither argument is changed -- strings cannot"
             " be -- so the caller still has what was typed.",
    ),
    dict(
        id=2, ledger="P597", concept="PY3 leading number or None", tier="1 - Text checks and fixes",
        title="The house number at the start of an address", kind="function",
        func="house_number",
        cases=[("12 High Street",), ("Flat 3, 12 High Street",), ("",), ("12a High Street",), ("  7 Mill Lane",)],
        prompt=(
            "Write a function `house_number(address)` that returns the"
            " house number as an int when the FIRST word of the"
            " address is made of digits only, and None otherwise.\n\n"
            "  house_number(\"12 High Street\") -> 12\n"
            "  house_number(\"Flat 3, 12 High Street\") -> None\n\n"
            "Return: an int, or None."
        ),
        solution=("def house_number(address):\n"
                  "    words = address.split()\n"
                  "    if words and words[0].isdigit():\n"
                  "        return int(words[0])\n"
                  "    return None\n"),
        trap=("def house_number(address):\n"
              "    words = address.split()\n"
              "    if words and words[0].isdigit():\n"
              "        return words[0]\n"
              "    return None\n"),
        note="isdigit() says the text is all digits; it does not turn"
             " it into a number. The trap returns the word itself,"
             " \"12\", which prints the same as 12 and is a different"
             " thing: it will not add, and it sorts \"100\" before"
             " \"12\". int() does the conversion, and is safe here"
             " because isdigit() has already been asked. `words and"
             " ...` covers the empty address, where there is no first"
             " word to look at.",
    ),
    dict(
        id=3, ledger="P598", concept="PY3 remove a known ending", tier="1 - Text checks and fixes",
        title="A company name without its ending", kind="function",
        func="without_ending",
        cases=[("Okonjo Books Ltd", [" Ltd", " & Co", " & Sons"]), ("Brandt Ltd", [" Ltd", " & Co", " & Sons"]), ("Yilmaz Bicycles & Sons", [" Ltd", " & Co", " & Sons"]), ("Achebe Bakery Direct", [" Ltd", " & Co", " & Sons"]), ("Ltd", [" Ltd"])],
        prompt=(
            "Write a function `without_ending(name, endings)` that"
            " returns the name with its ending cut off, if it ends"
            " with one of the endings in the list, and unchanged if it"
            " ends with none of them. Each ending in the list begins"
            " with a space.\n\n"
            "  without_ending(\"Okonjo Books Ltd\", [\" Ltd\", \" & Co\", \" & Sons\"]) -> \"Okonjo Books\"\n\n"
            "Return: a str."
        ),
        solution=("def without_ending(name, endings):\n"
                  "    for ending in endings:\n"
                  "        if name.endswith(ending):\n"
                  "            return name[:-len(ending)]\n"
                  "    return name\n"),
        trap=("def without_ending(name, endings):\n"
              "    for ending in endings:\n"
              "        if name.endswith(ending):\n"
              "            return name.rstrip(ending)\n"
              "    return name\n"),
        note="rstrip(\" Ltd\") does not remove the word ' Ltd'. Its"
             " argument is a SET of characters -- space, L, t, d --"
             " and it strips any of them from the end for as long as"
             " it can: 'Brandt Ltd' loses its ending and then the 'dt'"
             " of Brandt as well. A slice cuts exactly len(ending)"
             " characters. Python 3.9 added removesuffix() because so"
             " many people made this mistake; it does what the slice"
             " does.",
    ),
    dict(
        id=4, ledger="P599", concept="PY3 mask all but the last four", tier="1 - Text checks and fixes",
        title="An account number with its last four showing", kind="function",
        func="masked",
        cases=[("40127766411",), ("12345678",), ("6411",), ("77",), ("",)],
        prompt=(
            "Write a function `masked(number)` that returns the string"
            " with every character except the last four replaced by a"
            " star. The result is the same length as the original; a"
            " string of four characters or fewer comes back"
            " unchanged.\n\n"
            "  masked(\"12345678\") -> \"****5678\"\n\n"
            "Return: a str."
        ),
        solution=("def masked(number):\n"
                  "    return \"*\" * (len(number) - 4) + number[-4:]\n"),
        trap=("def masked(number):\n"
              "    return \"****\" + number[-4:]\n"),
        note="The number of stars depends on the length: len - 4 of"
             " them, then the last four characters. A string times a"
             " negative number is the empty string, and a slice of the"
             " last four from a shorter string is the whole string, so"
             " short inputs need no special case. The trap always"
             " writes four stars, which is right for eight characters"
             " only: an eleven-digit number comes back three short,"
             " and '77' comes back as '****77'.",
    ),
    dict(
        id=5, ledger="P600", concept="PY3 count a letter in either case", tier="1 - Text checks and fixes",
        title="How many times a letter appears", kind="function",
        func="count_letter",
        cases=[("Bartholomew Baxter", "b"), ("Bartholomew Baxter", "B"), ("Northgate", "z"), ("", "a"), ("AaAa", "a")],
        prompt=(
            "Write a function `count_letter(text, letter)` that returns"
            " how many times the letter appears in the text, counting"
            " capitals and small letters as the same, whichever way"
            " the letter itself was given.\n\n"
            "  count_letter(\"Bartholomew Baxter\", \"b\") -> 2\n\n"
            "Return: an int."
        ),
        solution=("def count_letter(text, letter):\n"
                  "    return text.lower().count(letter.lower())\n"),
        trap=("def count_letter(text, letter):\n"
              "    return text.count(letter)\n"),
        note="count() on a string counts exact matches, so 'b' finds"
             " no capital B: the trap answers 0 for a name with two of"
             " them. Lowering BOTH the text and the letter makes the"
             " comparison fair whichever case either arrives in --"
             " lowering only the text would break the call that passes"
             " a capital. No loop is needed; count() is the loop.",
    ),
    # ============================================== 2 Safe values and labels
    dict(
        id=6, ledger="P601", concept="PY3 safe int with a fallback", tier="2 - Safe values and labels",
        title="A quantity typed into a form", kind="function",
        func="quantity",
        cases=[("12",), (" 12 ",), ("abc",), ("",), ("3.5",), ("-2",)],
        prompt=(
            "Write a function `quantity(text)` that returns the whole"
            " number typed into a form field, ignoring spaces around"
            " it, or 0 if what was typed is not made of digits only."
            " Nothing here should ever raise an error.\n\n"
            "  quantity(\" 12 \") -> 12\n"
            "  quantity(\"abc\") -> 0\n\n"
            "Return: an int."
        ),
        solution=("def quantity(text):\n"
                  "    text = text.strip()\n"
                  "    if text.isdigit():\n"
                  "        return int(text)\n"
                  "    return 0\n"),
        trap=("def quantity(text):\n"
              "    if text.isdigit():\n"
              "        return int(text)\n"
              "    return 0\n"),
        note="int() raises on anything that is not a number, so ask"
             " first: isdigit() is True only for a non-empty string of"
             " digits, which rules out 'abc', '', '3.5' and '-2' in"
             " one test. A space is not a digit either -- the trap"
             " skips the strip and turns a perfectly good ' 12 ' into"
             " 0. int() itself would have accepted the spaces; it is"
             " the check in front of it that is strict.",
    ),
    dict(
        id=7, ledger="P602", concept="PY3 clamp to a range", tier="2 - Safe values and labels",
        title="A bay number kept within the depot", kind="function",
        func="within",
        cases=[(5, 1, 10), (0, 1, 10), (15, 1, 10), (1, 1, 10), (10, 1, 10), (-3, 0, 0)],
        prompt=(
            "Write a function `within(n, low, high)` that returns n if"
            " it lies between low and high, low if it is below, and"
            " high if it is above. low is never greater than high."
            " min() and max(), one inside the other.\n\n"
            "  within(15, 1, 10) -> 10\n"
            "  within(0, 1, 10) -> 1\n\n"
            "Return: an int."
        ),
        solution=("def within(n, low, high):\n"
                  "    return max(low, min(n, high))\n"),
        trap=("def within(n, low, high):\n"
              "    return min(low, max(n, high))\n"),
        note="min(n, high) pulls anything too big down to high, and"
             " max(low, ...) then lifts anything too small up to low."
             " It reads backwards at first -- min is used for the"
             " UPPER limit, because the smaller of n and high is what"
             " you want -- and the trap is what happens when the two"
             " are swapped to match the words: it returns low for"
             " everything. An if/elif with two comparisons says the"
             " same and is just as good.",
    ),
    dict(
        id=8, ledger="P603", concept="PY3 thousands separator", tier="2 - Safe values and labels",
        title="A parcel count with commas", kind="function",
        func="count_label",
        cases=[(24000,), (1,), (0,), (999,), (1234567,)],
        prompt=(
            "Write a function `count_label(n)` that returns the number"
            " with commas between the thousands, a space, and the word"
            " parcel -- or parcels for anything but exactly 1. An"
            " f-string's format can put the commas in.\n\n"
            "  count_label(24000) -> \"24,000 parcels\"\n"
            "  count_label(1) -> \"1 parcel\"\n\n"
            "Return: a str."
        ),
        solution=("def count_label(n):\n"
                  "    word = \"parcel\" if n == 1 else \"parcels\"\n"
                  "    return f\"{n:,} {word}\"\n"),
        trap=("def count_label(n):\n"
              "    word = \"parcel\" if n == 1 else \"parcels\"\n"
              "    return f\"{n} {word}\"\n"),
        note="Inside the braces of an f-string, whatever follows the"
             " colon is a format: a comma there groups the digits in"
             " threes. The trap prints 24000 as it comes, which is"
             " readable, and 1234567, which is not. Working out the"
             " word on its own line first keeps the f-string simple,"
             " and 0 takes the plural like every number that is not"
             " 1.",
    ),
    dict(
        id=9, ledger="P604", concept="PY3 labels from a range", tier="2 - Safe values and labels",
        title="Delivery slots, on the hour", kind="function",
        func="slots",
        cases=[(9, 12), (8, 9), (14, 14), (0, 3), (22, 24)],
        prompt=(
            "Write a function `slots(first, last)` that returns the"
            " start time of every one-hour delivery slot from the hour"
            " `first` up to but not including the hour `last`, as"
            " 'HH:00' strings with two digits for the hour.\n\n"
            "  slots(9, 12) -> [\"09:00\", \"10:00\", \"11:00\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def slots(first, last):\n"
                  "    return [f\"{hour:02d}:00\" for hour in range(first, last)]\n"),
        trap=("def slots(first, last):\n"
              "    return [f\"{hour}:00\" for hour in range(first, last)]\n"),
        note="range(first, last) already stops before `last`, which is"
             " exactly the slots wanted, and :02d in the f-string"
             " writes each hour two digits wide with a leading zero."
             " The trap leaves the format out and gives '9:00', which"
             " sorts after '10:00' as text and will not line up in a"
             " column. An empty range, slots(14, 14), gives an empty"
             " list with no special case.",
    ),
    dict(
        id=10, ledger="P605", concept="PY3 membership after normalising", tier="2 - Safe values and labels",
        title="Is it the weekend?", kind="function",
        func="is_weekend",
        cases=[("Saturday",), ("sun",), ("MONDAY",), (" Sat ",), ("Fri",), ("sunday",)],
        prompt=(
            "A day arrives as its full name or its first three"
            " letters, in any mix of capitals, perhaps with spaces"
            " around it. Write a function `is_weekend(day)` that"
            " returns True for Saturday and Sunday. Reduce every way"
            " of writing a day to one form, then test with `in`.\n\n"
            "  is_weekend(\"Saturday\") -> True\n"
            "  is_weekend(\" Sat \") -> True\n"
            "  is_weekend(\"MONDAY\") -> False\n\n"
            "Return: a bool."
        ),
        solution=("def is_weekend(day):\n"
                  "    return day.strip().lower()[:3] in (\"sat\", \"sun\")\n"),
        trap=("def is_weekend(day):\n"
              "    return day in (\"Saturday\", \"Sunday\")\n"),
        note="There are many ways to write Saturday and only one way"
             " to test for it, so bring the input to the test: strip"
             " the spaces, lower the case, keep three letters. Every"
             " spelling then lands on 'sat' or 'sun'. The trap lists"
             " the two spellings it thought of and says False to"
             " 'sun', ' Sat ' and 'sunday'. Order matters in the"
             " chain: strip before slicing, or the three characters"
             " kept from ' Sat ' would be ' sa'.",
    ),
    # ============================================ 3 Lists, split and combined
    dict(
        id=11, ledger="P606", concept="PY3 chunks of n", tier="3 - Lists, split and combined",
        title="Parcels shelved so many to a shelf", kind="function",
        func="shelves",
        cases=[(["a", "b", "c", "d", "e", "f", "g"], 3), (["a", "b", "c", "d"], 2), (["a"], 5), ([], 3), (["a", "b", "c"], 1)],
        prompt=(
            "Write a function `shelves(items, n)` that returns the"
            " items as a list of lists, n to a shelf in order, with"
            " whatever is left over on a last, shorter shelf. No items"
            " means no shelves. range takes a step.\n\n"
            "  shelves([\"a\", \"b\", \"c\", \"d\", \"e\", \"f\", \"g\"], 3) -> [[\"a\", \"b\", \"c\"], [\"d\", \"e\", \"f\"], [\"g\"]]\n\n"
            "Return: a list of lists."
        ),
        solution=("def shelves(items, n):\n"
                  "    return [items[i:i + n] for i in range(0, len(items), n)]\n"),
        trap=("def shelves(items, n):\n"
              "    return [items[i:n] for i in range(0, len(items), n)]\n"),
        note="range(0, len(items), n) gives the position where each"
             " shelf starts -- 0, 3, 6 -- and items[i:i + n] takes n"
             " items from there. The slice's end is a POSITION, not a"
             " length, which is the trap's mistake: items[i:n] is"
             " right for the first shelf, where i is 0, and empty for"
             " every one after it. A slice that runs past the end"
             " just stops, so the short last shelf needs no extra"
             " code.",
    ),
    dict(
        id=12, ledger="P607", concept="PY3 split a list in half", tier="3 - Lists, split and combined",
        title="One load between two vans", kind="function",
        func="halves",
        cases=[(["a", "b", "c", "d", "e"],), (["a", "b", "c", "d"],), (["a"],), ([],)],
        prompt=(
            "Write a function `halves(items)` that splits the list"
            " into a first half and a second half, in order, and"
            " returns the two lists. When the number of items is odd,"
            " the FIRST half gets the extra one.\n\n"
            "  halves([\"a\", \"b\", \"c\", \"d\", \"e\"]) -> ([\"a\", \"b\", \"c\"], [\"d\", \"e\"])\n\n"
            "Return: a tuple of two lists."
        ),
        solution=("def halves(items):\n"
                  "    middle = (len(items) + 1) // 2\n"
                  "    return items[:middle], items[middle:]\n"),
        trap=("def halves(items):\n"
              "    middle = len(items) // 2\n"
              "    return items[:middle], items[middle:]\n"),
        note="// divides and rounds DOWN, so len // 2 of five items is"
             " 2 and the extra item falls into the second half, the"
             " trap. Adding 1 before dividing rounds up instead: 5"
             " gives 3, and an even 4 still gives 2, because the"
             " extra half is thrown away. items[:middle] and"
             " items[middle:] always fit together with nothing lost"
             " and nothing repeated, whatever middle is.",
    ),
    dict(
        id=13, ledger="P608", concept="PY3 insert after a value", tier="3 - Lists, split and combined",
        title="An extra stop, straight after another", kind="function",
        func="insert_after",
        cases=[(["Northgate", "Moorside", "Westway"], "Moorside", "Hillcrest"), (["Northgate", "Moorside"], "Moorside", "Hillcrest"), (["Northgate"], "Docklands", "Hillcrest"), ([], "a", "b"), (["a", "b", "a"], "a", "x")],
        prompt=(
            "Write a function `insert_after(stops, stop, new)` that"
            " returns a NEW list with `new` placed immediately after"
            " the first occurrence of `stop`. If `stop` is not in the"
            " list, the result is an unchanged copy. The list passed"
            " in is not altered.\n\n"
            "  insert_after([\"Northgate\", \"Moorside\", \"Westway\"], \"Moorside\", \"Hillcrest\") -> [\"Northgate\", \"Moorside\", \"Hillcrest\", \"Westway\"]\n\n"
            "Return: a list."
        ),
        solution=("def insert_after(stops, stop, new):\n"
                  "    out = list(stops)\n"
                  "    if stop in out:\n"
                  "        out.insert(out.index(stop) + 1, new)\n"
                  "    return out\n"),
        trap=("def insert_after(stops, stop, new):\n"
              "    out = list(stops)\n"
              "    if stop in out:\n"
              "        out.insert(out.index(stop), new)\n"
              "    return out\n"),
        note="insert(position, item) puts the item BEFORE whatever is"
             " at that position now, so inserting at the stop's own"
             " index, the trap, puts the new stop in front of it."
             " After it means index + 1 -- and when the stop is the"
             " last item that is one past the end, which insert"
             " accepts as 'at the end'. list(stops) makes the copy,"
             " so the caller's route is not rearranged behind their"
             " back.",
    ),
    dict(
        id=14, ledger="P609", concept="PY3 all against an allowed list", tier="3 - Lists, split and combined",
        title="Is every status one we know?", kind="function",
        func="all_known",
        cases=[(["collected", "delivered"], ["collected", "departed", "arrived", "delivered"]), (["collected", "lost"], ["collected", "departed", "arrived", "delivered"]), ([], ["collected"]), (["lost", "found"], ["collected"]), (["collected", "collected"], ["collected"])],
        prompt=(
            "Write a function `all_known(statuses, allowed)` that"
            " returns True if EVERY status in the first list appears"
            " in the list of allowed ones. A trail with no statuses"
            " has nothing wrong with it.\n\n"
            "  all_known([\"collected\", \"lost\"], [\"collected\", \"departed\", \"arrived\", \"delivered\"]) -> False\n\n"
            "Return: a bool."
        ),
        solution=("def all_known(statuses, allowed):\n"
                  "    return all(status in allowed for status in statuses)\n"),
        trap=("def all_known(statuses, allowed):\n"
              "    return any(status in allowed for status in statuses)\n"),
        note="all() is True when no item fails the test; any(), the"
             " trap, is True as soon as one passes, so a trail with"
             " one good status and one unknown one is waved through."
             " They also disagree about nothing at all: all() of an"
             " empty list is True -- there is no counter-example --"
             " and any() is False. 'Is everything valid' is all();"
             " 'is anything valid' is a different question.",
    ),
    dict(
        id=15, ledger="P610", concept="PY3 right-align to the widest", tier="3 - Lists, split and combined",
        title="Numbers lined up on the right", kind="function",
        func="lined_up",
        cases=[([5, 120, 34],), ([7],), ([],), ([1000, 1, 10, 100],), ([0, 0],)],
        prompt=(
            "Write a function `lined_up(numbers)` that returns the"
            " numbers as strings, all the same length -- as wide as"
            " the longest -- with spaces added on the LEFT so that the"
            " last digits line up in a column. An empty list gives an"
            " empty list.\n\n"
            "  lined_up([5, 120, 34]) -> [\"  5\", \"120\", \" 34\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def lined_up(numbers):\n"
                  "    width = max((len(str(n)) for n in numbers), default=0)\n"
                  "    return [str(n).rjust(width) for n in numbers]\n"),
        trap=("def lined_up(numbers):\n"
              "    width = max((len(str(n)) for n in numbers), default=0)\n"
              "    return [str(n).ljust(width) for n in numbers]\n"),
        note="Two passes: one to find the width of the widest number,"
             " one to pad each to it. rjust pads on the left, pushing"
             " the text to the right, which is how numbers are read;"
             " ljust, the trap, pads on the right and lines up the"
             " FIRST digits, so 5 sits above the 1 of 120. Names take"
             " ljust, numbers take rjust. default=0 is what keeps"
             " max() from raising on an empty list.",
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
