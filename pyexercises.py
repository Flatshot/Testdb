"""Python practice exercises: fifteen everyday functions over plain values.

The thirty-eighth Python set, at the easy level of the last eight -- no
statistics, no dicts -- in the courier's terms, on tasks the earlier sets
did not cover. Finding and counting: the longest word on a label, how
often a status changed, the code seen most, the lowest free bay, how many
positions of two lists agree. Labels and text: a line cut to fit, 1st 2nd
3rd, a numbered list of steps, a depot's initials, the letters of a
postcode. Working with lists: two loads interleaved, a code swapped for
another throughout, who is next on the rota, names sorted whatever their
case, whether two vans carry the same load.

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
    # ================================================== 1 Finding and counting
    dict(
        id=1, ledger="P566", concept="PY3 max with a key", tier="1 - Finding and counting",
        title="The longest word on the label", kind="function",
        func="longest_word",
        cases=[("Yilmaz Garden Supplies Ltd",), ("Old Foundry",), ("Hub",), ("",), ("to be or not",)],
        prompt=(
            "Write a function `longest_word(label)` that returns the"
            " longest word in a label, the words being whatever split()"
            " gives. If several are equally long, the first of them; if"
            " the label has no words, the empty string. max() takes a"
            " key, and a default.\n\n"
            "  longest_word(\"Yilmaz Garden Supplies Ltd\") -> \"Supplies\"\n\n"
            "Return: a str."
        ),
        solution=("def longest_word(label):\n"
                  "    return max(label.split(), key=len, default=\"\")\n"),
        trap=("def longest_word(label):\n"
              "    return max(label.split(), default=\"\")\n"),
        note="max(words, key=len) compares the words by what len gives"
             " and returns the word itself, not its length; on a tie it"
             " keeps the first it met. Without the key, the trap, max"
             " compares the strings themselves and returns the one that"
             " is last in alphabetical order -- 'Yilmaz', which happens"
             " to be long enough to look plausible. default= is what"
             " max returns for an empty list instead of raising.",
    ),
    dict(
        id=2, ledger="P567", concept="PY3 count changes with zip", tier="1 - Finding and counting",
        title="How often the status changed", kind="function",
        func="count_changes",
        cases=[(["depot", "depot", "van", "van", "depot", "door"],), (["van"],), ([],), (["a", "b", "a", "b"],), (["x", "x", "x"],)],
        prompt=(
            "Write a function `count_changes(statuses)` that returns"
            " how many times an item differs from the one just before"
            " it. zip the list with itself, one step along.\n\n"
            "  count_changes([\"depot\", \"depot\", \"van\", \"van\", \"depot\", \"door\"]) -> 3\n\n"
            "Return: an int."
        ),
        solution=("def count_changes(statuses):\n"
                  "    return sum(a != b for a, b in zip(statuses, statuses[1:]))\n"),
        trap=("def count_changes(statuses):\n"
              "    return max(len(set(statuses)) - 1, 0)\n"),
        note="zip(items, items[1:]) pairs every item with its"
             " neighbour, and zip stops at the shorter list, so an empty"
             " list or a single item gives no pairs and a count of 0"
             " with no special case. Counting the different values and"
             " subtracting one, the trap, misses a status that comes"
             " back: depot, van, depot is two changes between two"
             " values.",
    ),
    dict(
        id=3, ledger="P568", concept="PY3 most common by count", tier="1 - Finding and counting",
        title="The code scanned most often", kind="function",
        func="most_scanned",
        cases=[(["MB-2", "CH-7", "MB-2", "WW-1", "CH-7", "MB-2"],), (["WW-1", "CH-7", "CH-7", "WW-1"],), (["A-1"],), ([],), (["b", "a", "a", "c", "c", "c", "z"],)],
        prompt=(
            "Write a function `most_scanned(codes)` that returns the"
            " code that appears most often in the list. On a tie, the"
            " one that appears FIRST in the list; for an empty list,"
            " None. max() again, with the list's own count method as"
            " the key.\n\n"
            "  most_scanned([\"MB-2\", \"CH-7\", \"MB-2\", \"WW-1\", \"CH-7\", \"MB-2\"]) -> \"MB-2\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def most_scanned(codes):\n"
                  "    return max(codes, key=codes.count, default=None)\n"),
        trap=("def most_scanned(codes):\n"
              "    return max(codes, default=None)\n"),
        note="key=codes.count asks, for each code, how many times the"
             " list holds it, and max returns the code with the biggest"
             " answer -- the first such code, because max only replaces"
             " its choice for something strictly bigger. That is what"
             " makes the tie rule free. Going through set(codes) first"
             " would be faster on a long list and would lose it, since"
             " a set has no order. The trap returns the code that sorts"
             " last, whatever its count.",
    ),
    dict(
        id=4, ledger="P569", concept="PY3 first number not in a list", tier="1 - Finding and counting",
        title="The lowest free loading bay", kind="function",
        func="first_free",
        cases=[([1, 2, 4, 5],), ([2, 3],), ([],), ([1, 2, 3],), ([3, 1, 2, 7],)],
        prompt=(
            "Bays are numbered from 1. Write a function"
            " `first_free(taken)` that returns the lowest bay number"
            " that is not in the list. The list is in no particular"
            " order. A while loop that counts up until `not in`.\n\n"
            "  first_free([1, 2, 4, 5]) -> 3\n\n"
            "Return: an int."
        ),
        solution=("def first_free(taken):\n"
                  "    n = 1\n"
                  "    while n in taken:\n"
                  "        n += 1\n"
                  "    return n\n"),
        trap=("def first_free(taken):\n"
              "    return max(taken, default=0) + 1\n"),
        note="A while loop is the right tool when you do not know how"
             " far you will have to go: start at 1 and step past every"
             " number that is taken. One past the highest, the trap, is"
             " free but not the LOWEST free: it answers 6 for [1, 2, 4,"
             " 5] and walks past the gap at 3. With every bay taken the"
             " two agree, which is why a test list needs a hole in it.",
    ),
    dict(
        id=5, ledger="P570", concept="PY3 count matching positions", tier="1 - Finding and counting",
        title="How much of the manifest matches the van", kind="function",
        func="matches",
        cases=[(["A-1", "B-2", "C-3", "D-4"], ["A-1", "C-3", "B-2", "D-4"]), (["A-1"], ["A-1"]), ([], []), (["A-1", "B-2"], ["B-2", "A-1"]), (["A-1", "B-2", "C-3"], ["A-1", "B-2"])],
        prompt=(
            "Write a function `matches(manifest, loaded)` that returns"
            " how many POSITIONS hold the same code in both lists:"
            " first against first, second against second. If one list"
            " is longer, its extra items match nothing.\n\n"
            "  matches([\"A-1\", \"B-2\", \"C-3\", \"D-4\"], [\"A-1\", \"C-3\", \"B-2\", \"D-4\"]) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def matches(manifest, loaded):\n"
                  "    return sum(a == b for a, b in zip(manifest, loaded))\n"),
        trap=("def matches(manifest, loaded):\n"
              "    return len(set(manifest) & set(loaded))\n"),
        note="zip walks the two lists side by side, so a == b compares"
             " the same position in each, and sum counts the Trues. The"
             " trap counts the codes the two lists SHARE, wherever they"
             " sit: 4 for the example, because every code is on the van"
             " somewhere. Same position and same contents are different"
             " questions; sets answer only the second.",
    ),
    # ====================================================== 2 Labels and text
    dict(
        id=6, ledger="P571", concept="PY3 truncate with an ellipsis", tier="2 - Labels and text",
        title="A line cut to fit the label", kind="function",
        func="fit",
        cases=[("Okonjo Garden Supplies & Sons", 16), ("Northgate", 16), ("Northgate", 9), ("Central Hub", 6), ("abcd", 3)],
        prompt=(
            "Write a function `fit(text, width)` for a label `width`"
            " characters wide. Text that fits is returned unchanged."
            " Text that is too long is cut and ended with three dots,"
            " so that the result is EXACTLY width characters, dots"
            " included. width is always 3 or more.\n\n"
            "  fit(\"Okonjo Garden Supplies & Sons\", 16) -> \"Okonjo Garden...\"\n\n"
            "Return: a str."
        ),
        solution=("def fit(text, width):\n"
                  "    if len(text) <= width:\n"
                  "        return text\n"
                  "    return text[:width - 3] + \"...\"\n"),
        trap=("def fit(text, width):\n"
              "    if len(text) <= width:\n"
              "        return text\n"
              "    return text[:width] + \"...\"\n"),
        note="The dots take up room too, so the slice stops three"
             " short: width - 3 characters of text and 3 of dots make"
             " width. The trap cuts at width and then adds the dots, a"
             " line three characters too long for the label it was"
             " meant to fit. The <= matters as well: text of exactly"
             " the width fits, and should not lose its last three"
             " letters to dots.",
    ),
    dict(
        id=7, ledger="P572", concept="PY4 ordinal suffix", tier="2 - Labels and text",
        title="1st, 2nd, 3rd, 4th", kind="function",
        func="ordinal",
        cases=[(1,), (2,), (3,), (4,), (11,), (12,), (13,), (21,), (102,), (111,)],
        prompt=(
            "Write a function `ordinal(n)` that returns a positive"
            " whole number with its ending: 1st, 2nd, 3rd, then th."
            " The last digit decides -- 21st, 32nd, 103rd -- except"
            " that anything ending in 11, 12 or 13 takes th.\n\n"
            "  ordinal(22) -> \"22nd\"\n"
            "  ordinal(12) -> \"12th\"\n\n"
            "Return: a str."
        ),
        solution=("def ordinal(n):\n"
                  "    if n % 100 in (11, 12, 13):\n"
                  "        return f\"{n}th\"\n"
                  "    if n % 10 == 1:\n"
                  "        return f\"{n}st\"\n"
                  "    if n % 10 == 2:\n"
                  "        return f\"{n}nd\"\n"
                  "    if n % 10 == 3:\n"
                  "        return f\"{n}rd\"\n"
                  "    return f\"{n}th\"\n"),
        trap=("def ordinal(n):\n"
              "    if n % 10 == 1:\n"
              "        return f\"{n}st\"\n"
              "    if n % 10 == 2:\n"
              "        return f\"{n}nd\"\n"
              "    if n % 10 == 3:\n"
              "        return f\"{n}rd\"\n"
              "    return f\"{n}th\"\n"),
        note="n % 10 is the last digit and n % 100 the last two. The"
             " exception has to be tested FIRST: once a rule has"
             " returned, the ones below it never run, so the order of"
             " the ifs is the logic. The trap has no exception and"
             " prints 11st, 12nd and 13rd -- and 111st, which is why"
             " the test is on the last two digits and not on n itself.",
    ),
    dict(
        id=8, ledger="P573", concept="PY3 enumerate from one", tier="2 - Labels and text",
        title="The steps of a delivery, numbered", kind="function",
        func="numbered",
        cases=[(["Collect", "Sort", "Deliver"],), (["Scan"],), ([],), (["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],)],
        prompt=(
            "Write a function `numbered(steps)` that returns a new list"
            " with each step's number in front of it, counting from 1,"
            " then a full stop and a space. enumerate can be told where"
            " to start.\n\n"
            "  numbered([\"Collect\", \"Sort\", \"Deliver\"]) -> [\"1. Collect\", \"2. Sort\", \"3. Deliver\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def numbered(steps):\n"
                  "    return [f\"{i}. {step}\" for i, step in enumerate(steps, 1)]\n"),
        trap=("def numbered(steps):\n"
              "    return [f\"{i}. {step}\" for i, step in enumerate(steps)]\n"),
        note="enumerate hands out each item with a counter, and its"
             " second argument is where the counter starts. Left out,"
             " the trap, it starts at 0, because it is usually wanted"
             " as an index -- and a list for people that begins '0."
             " Collect' is the result. enumerate(steps, 1) is tidier"
             " than writing i + 1 inside the f-string, and much tidier"
             " than range(len(steps)).",
    ),
    dict(
        id=9, ledger="P574", concept="PY3 initials of words", tier="2 - Labels and text",
        title="A depot's initials", kind="function",
        func="initials",
        cases=[("Central Hub",), ("old foundry",), ("Harbour  Point",), ("Westway",), ("",), ("north gate depot",)],
        prompt=(
            "Write a function `initials(name)` that returns the first"
            " letter of each word, joined together and in capitals,"
            " whatever case the name was typed in. Extra spaces between"
            " words do not matter.\n\n"
            "  initials(\"Central Hub\") -> \"CH\"\n"
            "  initials(\"old foundry\") -> \"OF\"\n\n"
            "Return: a str."
        ),
        solution=("def initials(name):\n"
                  "    return \"\".join(word[0] for word in name.split()).upper()\n"),
        trap=("def initials(name):\n"
              "    return \"\".join(word[0] for word in name.split())\n"),
        note="split() with no argument breaks on any run of spaces and"
             " never produces an empty word, so word[0] is always safe"
             " -- split(' ') would give '' for a doubled space and"
             " word[0] would raise. join glues the letters with nothing"
             " between, and one upper() at the end covers them all. The"
             " trap forgets it and returns 'of' for a name typed in"
             " lower case.",
    ),
    dict(
        id=10, ledger="P575", concept="PY3 strip characters from the right", tier="2 - Labels and text",
        title="The letters of a postcode area", kind="function",
        func="town",
        cases=[("NG5",), ("DE22",), ("S1",), ("LE4",), ("B",), ("",)],
        prompt=(
            "A postcode area is one or two letters and then digits."
            " Write a function `town(area)` that returns the letters"
            " alone. rstrip takes an argument: the characters to"
            " strip.\n\n"
            "  town(\"DE22\") -> \"DE\"\n"
            "  town(\"S1\") -> \"S\"\n\n"
            "Return: a str."
        ),
        solution=("def town(area):\n"
                  "    return area.rstrip(\"0123456789\")\n"),
        trap=("def town(area):\n"
              "    return area[:2]\n"),
        note="rstrip(chars) removes from the right-hand end every"
             " character that is in chars, in any order, and stops at"
             " the first that is not -- so it does not matter how many"
             " digits there are, or how many letters. The first two"
             " characters, the trap, are right for NG5 and wrong for"
             " S1, where the second character is already a digit. This"
             " is the same tool as RTRIM with a second argument in SQL.",
    ),
    # =================================================== 3 Working with lists
    dict(
        id=11, ledger="P576", concept="PY4 interleave two lists", tier="3 - Working with lists",
        title="Two loads, taken turn about", kind="function",
        func="interleave",
        cases=[(["A-1", "A-2", "A-3"], ["B-1", "B-2", "B-3"]), (["A-1", "A-2", "A-3", "A-4"], ["B-1"]), ([], ["B-1", "B-2"]), ([], []), (["x"], ["y", "z", "w"])],
        prompt=(
            "Write a function `interleave(first, second)` that returns"
            " one list taking items from the two in turn: first's"
            " first, second's first, first's second, and so on. When"
            " one list runs out, the rest of the other follows in"
            " order.\n\n"
            "  interleave([\"A-1\", \"A-2\", \"A-3\", \"A-4\"], [\"B-1\"]) -> [\"A-1\", \"B-1\", \"A-2\", \"A-3\", \"A-4\"]\n\n"
            "Return: a list."
        ),
        solution=("def interleave(first, second):\n"
                  "    out = []\n"
                  "    for a, b in zip(first, second):\n"
                  "        out.append(a)\n"
                  "        out.append(b)\n"
                  "    n = min(len(first), len(second))\n"
                  "    return out + first[n:] + second[n:]\n"),
        trap=("def interleave(first, second):\n"
              "    out = []\n"
              "    for a, b in zip(first, second):\n"
              "        out.append(a)\n"
              "        out.append(b)\n"
              "    return out\n"),
        note="zip pairs the lists up for as long as both have items and"
             " then stops without a word, so the trap silently loses"
             " A-2, A-3 and A-4. The leftovers are whatever lies past"
             " the shorter length: one of the two slices is always"
             " empty, so adding both is safe and needs no if. A slice"
             " past the end of a list is an empty list, never an"
             " error.",
    ),
    dict(
        id=12, ledger="P577", concept="PY3 replace a value throughout", tier="3 - Working with lists",
        title="A relabelled parcel, corrected everywhere", kind="function",
        func="relabel",
        cases=[(["MB-2", "CH-7", "MB-2", "WW-1"], "MB-2", "MB-9"), (["CH-7"], "MB-2", "MB-9"), ([], "a", "b"), (["a", "a", "a"], "a", "b")],
        prompt=(
            "Write a function `relabel(codes, old, new)` that returns a"
            " NEW list in which every item equal to old has become new,"
            " and everything else is as it was. The list passed in is"
            " not changed. A comprehension with a conditional"
            " expression.\n\n"
            "  relabel([\"MB-2\", \"CH-7\", \"MB-2\", \"WW-1\"], \"MB-2\", \"MB-9\") -> [\"MB-9\", \"CH-7\", \"MB-9\", \"WW-1\"]\n\n"
            "Return: a list."
        ),
        solution=("def relabel(codes, old, new):\n"
                  "    return [new if c == old else c for c in codes]\n"),
        trap=("def relabel(codes, old, new):\n"
              "    out = list(codes)\n"
              "    if old in out:\n"
              "        out[out.index(old)] = new\n"
              "    return out\n"),
        note="`new if c == old else c` is an expression with a value,"
             " so it can sit at the front of a comprehension and decide"
             " each item as it goes by. That is different from an `if`"
             " at the END of a comprehension, which filters items out."
             " The trap uses index(), which finds only the first match:"
             " one MB-2 corrected and the other still on the list."
             " Lists have no replace method of their own; strings do.",
    ),
    dict(
        id=13, ledger="P578", concept="PY3 next item, wrapping round", tier="3 - Working with lists",
        title="Who is next on the rota", kind="function",
        func="next_up",
        cases=[(["Grace", "Samir", "Nadia"], "Grace"), (["Grace", "Samir", "Nadia"], "Nadia"), (["Grace"], "Grace"), (["a", "b", "c", "d"], "c"), (["a", "b"], "b")],
        prompt=(
            "The rota is a list of names, each appearing once, and it"
            " goes round: after the last name comes the first again."
            " Write a function `next_up(rota, name)` that returns the"
            " name after the given one. name is always on the rota."
            " index(), and the remainder operator to wrap.\n\n"
            "  next_up([\"Grace\", \"Samir\", \"Nadia\"], \"Nadia\") -> \"Grace\"\n\n"
            "Return: a str."
        ),
        solution=("def next_up(rota, name):\n"
                  "    return rota[(rota.index(name) + 1) % len(rota)]\n"),
        trap=("def next_up(rota, name):\n"
              "    return rota[min(rota.index(name) + 1, len(rota) - 1)]\n"),
        note="index(name) + 1 is the next position, and % len(rota)"
             " turns the one position that does not exist -- one past"
             " the end -- into 0, leaving every other position alone."
             " That is all the remainder is doing here: wrapping. The"
             " trap stops at the end instead of going round, so the"
             " last person on the rota is followed by themselves."
             " Without either guard, rota[index + 1] raises IndexError"
             " for the last name.",
    ),
    dict(
        id=14, ledger="P579", concept="PY3 sort ignoring case", tier="3 - Working with lists",
        title="Names in order, whatever their capitals", kind="function",
        func="in_order",
        cases=[(["westway", "Central Hub", "Millbank", "docklands"],), (["b", "A", "c"],), ([],), (["Zed", "apple", "Mango", "berry"],)],
        prompt=(
            "Write a function `in_order(names)` that returns the names"
            " in alphabetical order as a reader would expect it, taking"
            " no notice of capital letters. Each name comes back"
            " spelled exactly as it went in. sorted() with a key.\n\n"
            "  in_order([\"westway\", \"Central Hub\", \"Millbank\", \"docklands\"]) -> [\"Central Hub\", \"docklands\", \"Millbank\", \"westway\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def in_order(names):\n"
                  "    return sorted(names, key=str.lower)\n"),
        trap=("def in_order(names):\n"
              "    return sorted(names)\n"),
        note="Plain sorted, the trap, compares characters by their"
             " code, and every capital letter comes before every small"
             " one: Central Hub, Millbank, docklands, westway. A key is"
             " used only for comparing -- sorted puts the names in the"
             " order their lower-case versions would take and returns"
             " the originals, untouched. Lower-casing the list first"
             " would sort correctly and hand back names that are no"
             " longer spelled the way they were.",
    ),
    dict(
        id=15, ledger="P580", concept="PY3 same items in any order", tier="3 - Working with lists",
        title="Do the two vans carry the same load?", kind="function",
        func="same_load",
        cases=[(["A-1", "B-2", "A-1"], ["B-2", "A-1", "A-1"]), (["A-1", "B-2", "A-1"], ["A-1", "B-2", "B-2"]), (["A-1", "B-2"], ["B-2", "A-1"]), ([], []), (["A-1"], ["A-1", "A-1"])],
        prompt=(
            "Write a function `same_load(van_a, van_b)` that returns"
            " True if the two lists hold the same codes the same number"
            " of times, in any order. A code that is on one van twice"
            " must be on the other twice.\n\n"
            "  same_load([\"A-1\", \"B-2\", \"A-1\"], [\"B-2\", \"A-1\", \"A-1\"]) -> True\n"
            "  same_load([\"A-1\", \"B-2\", \"A-1\"], [\"A-1\", \"B-2\", \"B-2\"]) -> False\n\n"
            "Return: a bool."
        ),
        solution=("def same_load(van_a, van_b):\n"
                  "    return sorted(van_a) == sorted(van_b)\n"),
        trap=("def same_load(van_a, van_b):\n"
              "    return set(van_a) == set(van_b)\n"),
        note="Two lists are equal when they hold the same items in the"
             " same order, so sorting both removes the one difference"
             " that is not supposed to count and keeps the repeats."
             " Sets, the trap, throw the repeats away: two A-1s and a"
             " B-2 look the same as one A-1 and two B-2s, and one"
             " parcel looks the same as two. sorted() returns new"
             " lists, so neither van's list is disturbed by the check.",
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
