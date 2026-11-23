"""Python practice exercises: fifteen everyday functions over plain values.

The forty-third Python set, at the easy level of the last thirteen -- no
statistics, no dicts, nothing to import -- and the third in a hotel's
terms. Numbers at the desk: night or nights, cents written as money, a
late check-out charged by bands, the position of the longest stay,
whether every bill is settled. Words and names: a name listed surname
first turned round, initials, a key-card code, a yes typed any old way,
a word counted in a note. Lists on the board: the last few entries of a
log, the rooms not taken, a guest list with no repeats, names paired
with rooms, a party split into tables.

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
    # ================================================ 1 Numbers at the desk
    dict(
        id=1, ledger="P641", concept="PY3 one night, two nights", tier="1 - Numbers at the desk",
        title="One night or two nights", kind="function",
        func="nights_label",
        cases=[(1,), (3,), (0,), (2,), (14,)],
        prompt=(
            "A confirmation says how long the stay is. Write a"
            " function `nights_label(n)` that returns the number"
            " followed by the word 'night' when n is exactly 1 and"
            " 'nights' for any other number, 0 included. An f-string"
            " puts the number into the text.\n\n"
            "  nights_label(1) -> '1 night'\n"
            "  nights_label(3) -> '3 nights'\n\n"
            "Return: a string."
        ),
        solution=("def nights_label(n):\n"
                  "    if n == 1:\n"
                  "        return \"1 night\"\n"
                  "    return f\"{n} nights\"\n"),
        trap=("def nights_label(n):\n"
              "    return f\"{n} nights\"\n"),
        note="An f-string is ordinary text with holes in braces, and"
             " each hole is filled with the value of what is written"
             " in it. The only decision is the s, and it turns on one"
             " value: 1. Zero takes the plural -- '0 nights' -- which"
             " is why the test is n == 1 and not n <= 1. The trap"
             " skips the decision and sends out '1 nights', the small"
             " mistake that makes a letter look machine-made. The"
             " whole thing fits on one line as f\"{n} night{'' if n =="
             " 1 else 's'}\", if you like that sort of thing.",
    ),
    dict(
        id=2, ledger="P642", concept="PY3 cents to money text, padded", tier="1 - Numbers at the desk",
        title="Cents as a number, money as text", kind="function",
        func="format_cents",
        cases=[(123450,), (5,), (7900,), (100000000,), (99,), (1005,)],
        prompt=(
            "Last time money text became cents; now the other way."
            " Write a function `format_cents(cents)` that takes a"
            " whole number of cents, never negative, and returns it"
            " as text: the dollars with a comma between each group of"
            " three digits, a point, and always two digits of cents."
            " // and % split the number in two. Inside an f-string's"
            " braces a format spec after a colon does the rest: a"
            " comma asks for thousands separators, and 02d pads a"
            " number to two digits with a zero. No floats.\n\n"
            "  format_cents(123450) -> '1,234.50'\n"
            "  format_cents(5) -> '0.05'\n\n"
            "Return: a string."
        ),
        solution=("def format_cents(cents):\n"
                  "    return f\"{cents // 100:,}.{cents % 100:02d}\"\n"),
        trap=("def format_cents(cents):\n"
              "    return f\"{cents // 100:,}.{cents % 100}\"\n"),
        note="cents // 100 is the dollars and cents % 100 what is left"
             " over, both whole numbers. {...:,} writes the first with"
             " commas and {...:02d} writes the second at least two"
             " digits wide, filling with a zero. The trap leaves the"
             " padding off: five cents come out as '0.5', which reads"
             " as fifty, and 1,005 cents as '10.5'. It is right for"
             " every amount whose cents are 10 or more, which is nine"
             " in ten of them, so it survives a quick test. Dividing"
             " by 100 with a single slash would bring in a float and"
             " print 79.0 for 7,900.",
    ),
    dict(
        id=3, ledger="P643", concept="PY3 bands with if, elif, else", tier="1 - Numbers at the desk",
        title="What a late check-out costs", kind="function",
        func="late_charge",
        cases=[(0, 9000), (1, 9000), (2, 9000), (4, 9000), (5, 9000), (3, 7500), (10, 6000)],
        prompt=(
            "Guests should be out by eleven. Up to and including 1"
            " hour late costs nothing. More than 1 hour and up to and"
            " including 4 hours costs half the nightly rate. More than"
            " 4 hours costs the whole rate. Write a function"
            " `late_charge(hours, rate)` that returns the charge in"
            " cents; hours is a whole number and rate is in cents,"
            " and half of it is rate // 2. An if, an elif and an else"
            " -- and mind which side of each line 1 and 4 fall.\n\n"
            "  late_charge(1, 9000) -> 0\n"
            "  late_charge(4, 9000) -> 4500\n"
            "  late_charge(5, 9000) -> 9000\n\n"
            "Return: an int."
        ),
        solution=("def late_charge(hours, rate):\n"
                  "    if hours <= 1:\n"
                  "        return 0\n"
                  "    elif hours <= 4:\n"
                  "        return rate // 2\n"
                  "    else:\n"
                  "        return rate\n"),
        trap=("def late_charge(hours, rate):\n"
              "    if hours < 1:\n"
              "        return 0\n"
              "    elif hours < 4:\n"
              "        return rate // 2\n"
              "    else:\n"
              "        return rate\n"),
        note="The tests run from the top and the first true one wins,"
             " so the elif need not say 'more than 1': anything that"
             " reaches it already is. That leaves each band one"
             " comparison, and the whole question is whether it is <"
             " or <=. 'Up to and including' is <=. The trap writes <"
             " and is right for 0, 2, 3 and 5 hours and wrong exactly"
             " at 1 and 4, charging a guest one hour late half a"
             " night and one four hours late a whole one. Mistakes in"
             " bands live on the boundaries, so those are the values"
             " to test. This is CASE WHEN ... WHEN ... ELSE in SQL,"
             " which also takes the first true branch.",
    ),
    dict(
        id=4, ledger="P644", concept="PY4 position of the largest", tier="1 - Numbers at the desk",
        title="Which stay was the longest?", kind="function",
        func="longest_stay",
        cases=[([2, 5, 3],), ([4, 7, 7, 1],), ([],), ([3],), ([1, 1, 1],), ([9, 2, 9],)],
        prompt=(
            "A guest's stays are listed in order, as numbers of"
            " nights. Write a function `longest_stay(nights)` that"
            " returns the POSITION of the longest one, counting from"
            " 0; the first of them if several are equally long; and"
            " None when the list is empty. max finds the largest"
            " value and a list's index method finds where a value"
            " first appears.\n\n"
            "  longest_stay([2, 5, 3]) -> 1\n"
            "  longest_stay([4, 7, 7, 1]) -> 1\n\n"
            "Return: an int, or None."
        ),
        solution=("def longest_stay(nights):\n"
                  "    if not nights:\n"
                  "        return None\n"
                  "    return nights.index(max(nights))\n"),
        trap=("def longest_stay(nights):\n"
              "    best = None\n"
              "    for i in range(len(nights)):\n"
              "        if best is None or nights[i] >= nights[best]:\n"
              "            best = i\n"
              "    return best\n"),
        note="max(nights) is the longest stay and nights.index(...)"
             " the first place it occurs, which settles ties without"
             " another word. max of an empty list is an error, so the"
             " empty case is turned away first; `not nights` is true"
             " for an empty list. The trap does it by hand and keeps"
             " the position whenever a stay is at least as long as"
             " the best so far: with >= a later equal stay replaces"
             " an earlier one, and [4, 7, 7, 1] gives 2. With > it"
             " would be right. Which of two equals wins is decided by"
             " one character.",
    ),
    dict(
        id=5, ledger="P645", concept="PY4 every item passes a test", tier="1 - Numbers at the desk",
        title="Has everyone settled up?", kind="function",
        func="all_settled",
        cases=[([0, 0, 0],), ([0, 250, 0],), ([],), ([0],), ([1200],), ([0, 0, 5],)],
        prompt=(
            "Before a coach party leaves, the desk checks the balance"
            " on every room, in cents. Write a function"
            " `all_settled(balances)` that returns True when every"
            " balance is 0 and False when any is not. With no rooms"
            " at all there is nothing outstanding: True. One"
            " unsettled room is enough to answer False, but True can"
            " only be said after the last one has been looked at.\n\n"
            "  all_settled([0, 0, 0]) -> True\n"
            "  all_settled([0, 250, 0]) -> False\n\n"
            "Return: a bool."
        ),
        solution=("def all_settled(balances):\n"
                  "    for b in balances:\n"
                  "        if b != 0:\n"
                  "            return False\n"
                  "    return True\n"),
        trap=("def all_settled(balances):\n"
              "    for b in balances:\n"
              "        if b == 0:\n"
              "            return True\n"
              "        else:\n"
              "            return False\n"),
        note="The loop looks for a reason to say no and returns the"
             " moment it finds one; `return True` sits AFTER the"
             " loop, where it is reached only if nothing objected,"
             " and that covers the empty list too. The trap answers"
             " inside the loop both ways, so it never gets past the"
             " first room: [0, 250, 0] is True because the first"
             " balance is 0, and an empty list falls out of the"
             " bottom with None. The built-in all(b == 0 for b in"
             " balances) is this loop in one line. In SQL the same"
             " question is NOT EXISTS: no row that breaks the rule.",
    ),
    # ================================================== 2 Words and names
    dict(
        id=6, ledger="P646", concept="PY3 split in two and swap", tier="2 - Words and names",
        title="Surname first, turned round", kind="function",
        func="swap_name",
        cases=[("Lovelace, Ada",), ("Hopper,Grace",), ("  de la Cruz ,  Maria",), ("Wu, Li",)],
        prompt=(
            "The agent's list gives names surname first, with a comma:"
            " 'Lovelace, Ada'. Write a function `swap_name(listed)`"
            " that returns the first name, one space, and the surname."
            " There is always exactly one comma, but the spaces round"
            " it and at the ends are as the agent happened to type"
            " them. split cuts a string at a separator, and strip"
            " removes spaces from both ends.\n\n"
            "  swap_name('Lovelace, Ada') -> 'Ada Lovelace'\n"
            "  swap_name('Hopper,Grace') -> 'Grace Hopper'\n\n"
            "Return: a string."
        ),
        solution=("def swap_name(listed):\n"
                  "    last, first = listed.split(\",\")\n"
                  "    return first.strip() + \" \" + last.strip()\n"),
        trap=("def swap_name(listed):\n"
              "    last, first = listed.split(\",\")\n"
              "    return first + \" \" + last\n"),
        note="split(\",\") gives a list of two pieces and `last, first"
             " = ...` unpacks them into two names in one line. The"
             " pieces keep whatever spaces lay beside the comma, so"
             " each is stripped before they are joined with a single"
             " space. The trap joins them as they come: 'Hopper,Grace'"
             " happens to work, and 'Lovelace, Ada' becomes ' Ada"
             " Lovelace', with a space in front that nobody sees until"
             " the name fails to match one in another list. strip"
             " touches only the ends, so the spaces inside 'de la"
             " Cruz' are safe.",
    ),
    dict(
        id=7, ledger="P647", concept="PY4 first letter of each word", tier="2 - Words and names",
        title="Initials for the luggage tag", kind="function",
        func="initials",
        cases=[("ada mary lovelace",), ("Grace Hopper",), ("",), ("cher",), ("  li   wu ",)],
        prompt=(
            "A luggage tag carries initials. Write a function"
            " `initials(name)` that returns the first letter of each"
            " word of the name, as a capital, each followed by a full"
            " stop. The name may have any number of words, extra"
            " spaces, or be empty, which gives ''. split with no"
            " argument cuts at any run of spaces, and word[0] is a"
            " word's first letter.\n\n"
            "  initials('ada mary lovelace') -> 'A.M.L.'\n"
            "  initials('cher') -> 'C.'\n\n"
            "Return: a string."
        ),
        solution=("def initials(name):\n"
                  "    out = \"\"\n"
                  "    for word in name.split():\n"
                  "        out += word[0].upper() + \".\"\n"
                  "    return out\n"),
        trap=("def initials(name):\n"
              "    return \".\".join(word[0].upper() for word in name.split())\n"),
        note="The string is built up a piece at a time: for each word,"
             " its first letter in capitals and a full stop. split()"
             " never produces an empty word, so word[0] is always"
             " there, and an empty name simply gives no turns of the"
             " loop. The trap reaches for join, which puts its"
             " separator BETWEEN the items and nowhere else: 'A.M.L',"
             " with no stop after the last letter. join is the right"
             " tool when the thing goes between, as commas do; here"
             " it goes after each one, which is a different job.",
    ),
    dict(
        id=8, ledger="P648", concept="PY3 slice, upper and zero padding", tier="2 - Words and names",
        title="The code on a key card", kind="function",
        func="key_code",
        cases=[("Fellfoot Inn", 7), ("Spa Gardens", 312), ("castle view", 45), ("Abbey Steps", 100),
               ("The Old Mill", 1)],
        prompt=(
            "Each key card is printed with a code: the first three"
            " letters of the hotel's name in capitals, a hyphen, and"
            " the room number written with three digits, zeros in"
            " front if it needs them. Write a function"
            " `key_code(hotel, room)`, where hotel is the name and"
            " room is a whole number from 1 to 999. A slice takes the"
            " first three letters; the number has to become text"
            " before it can be padded, and strings have a method that"
            " fills with zeros on the left.\n\n"
            "  key_code('Fellfoot Inn', 7) -> 'FEL-007'\n"
            "  key_code('Spa Gardens', 312) -> 'SPA-312'\n\n"
            "Return: a string."
        ),
        solution=("def key_code(hotel, room):\n"
                  "    return hotel[:3].upper() + \"-\" + str(room).zfill(3)\n"),
        trap=("def key_code(hotel, room):\n"
              "    return hotel[:3].upper() + \"-\" + str(room)\n"),
        note="hotel[:3] is the first three characters and .upper()"
             " makes them capitals whatever was typed. A number"
             " cannot be glued to text, so str(room) comes first, and"
             " .zfill(3) then pads it on the left with zeros to three"
             " characters, leaving anything already that long alone."
             " The trap forgets the padding and is right for every"
             " room from 100 up -- most rooms in most hotels -- and"
             " prints 'FEL-7' for the ground floor. f\"{room:03d}\""
             " does the same padding inside an f-string. Codes of a"
             " fixed width also sort properly as text, which 'FEL-7'"
             " and 'FEL-45' do not.",
    ),
    dict(
        id=9, ledger="P649", concept="PY3 membership after tidying text", tier="2 - Words and names",
        title="Did the guest say yes?", kind="function",
        func="said_yes",
        cases=[("yes",), (" Y ",), ("no",), ("YES",), ("yes please",), ("",), ("y",)],
        prompt=(
            "The kiosk asks 'Breakfast? (y/n)' and guests type what"
            " they like. Write a function `said_yes(answer)` that"
            " returns True when the answer is 'y' or 'yes' -- in any"
            " mixture of capitals, with or without spaces at the"
            " ends -- and False for anything else at all, 'yes"
            " please' included. Tidy the text first; then `in` tests"
            " whether a value is one of several.\n\n"
            "  said_yes(' Y ') -> True\n"
            "  said_yes('no') -> False\n\n"
            "Return: a bool."
        ),
        solution=("def said_yes(answer):\n"
                  "    return answer.strip().lower() in (\"y\", \"yes\")\n"),
        trap=("def said_yes(answer):\n"
              "    answer = answer.strip().lower()\n"
              "    return answer == \"y\" or \"yes\"\n"),
        note="strip and lower turn every acceptable spelling into one"
             " of two, and `in (\"y\", \"yes\")` asks whether the"
             " result is either. The trap reads the way the sentence"
             " is spoken -- answer equals y or yes -- but Python"
             " takes it as (answer == \"y\") or (\"yes\"): when the"
             " first half is False the whole expression is the string"
             " \"yes\", which counts as true in an if. So 'no' gets"
             " breakfast, and what the function returns is not even a"
             " bool. Each side of an `or` has to be a whole test:"
             " answer == \"y\" or answer == \"yes\". The `in` form is"
             " shorter and harder to get wrong; SQL has it too.",
    ),
    dict(
        id=10, ledger="P650", concept="PY4 count whole words, not substrings", tier="2 - Words and names",
        title="How often does the note say it?", kind="function",
        func="count_word",
        cases=[("Extra bed please. Bed by the window, not the bedroom door!", "bed"),
               ("late late LATE check-out", "late"), ("", "bed"), ("No towels? No soap.", "no"),
               ("quiet room", "bed")],
        prompt=(
            "Housekeeping scans booking notes for a word. Write a"
            " function `count_word(note, word)` that returns how many"
            " times the word appears in the note as a WHOLE word."
            " Capitals do not matter, and a full stop, comma,"
            " exclamation mark or question mark stuck to the end of a"
            " word is not part of it. 'bedroom' is not 'bed'. Split"
            " the note into words and compare each one; strip can be"
            " told which characters to remove.\n\n"
            "  count_word('Extra bed please. Bed by the window, not the bedroom door!', 'bed') -> 2\n"
            "  count_word('quiet room', 'bed') -> 0\n\n"
            "Return: an int."
        ),
        solution=("def count_word(note, word):\n"
                  "    n = 0\n"
                  "    for w in note.lower().split():\n"
                  "        if w.strip(\".,!?\") == word.lower():\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_word(note, word):\n"
              "    return note.lower().count(word.lower())\n"),
        note="Lower-casing both sides takes care of capitals, split()"
             " gives the words, and strip(\".,!?\") removes any of"
             " those four characters from a word's two ends, so"
             " 'please.' can equal 'please'. Then it is a count with"
             " an if. The trap uses the string's own count method,"
             " which counts the letters b-e-d wherever they occur:"
             " the bedroom makes three. It is right about the towels"
             " and the soap only because no longer word in that note"
             " happens to contain 'no'. Text matched as a substring"
             " is the same trap as LIKE '%bed%' in SQL.",
    ),
    # ================================================ 3 Lists on the board
    dict(
        id=11, ledger="P651", concept="PY3 the last n of a list, and none", tier="3 - Lists on the board",
        title="The last few lines of the log", kind="function",
        func="last_entries",
        cases=[(["in 101", "out 204", "in 305", "out 101"], 2), (["in 101", "out 204", "in 305", "out 101"], 0),
               (["in 101"], 5), ([], 3), (["x", "y", "z"], 3), (["x", "y", "z"], 1)],
        prompt=(
            "The night porter wants the end of the door log. Write a"
            " function `last_entries(log, n)` that returns a new list"
            " of the last n entries, in their original order. If the"
            " log has fewer than n, return them all; if n is 0,"
            " return an empty list. n is never negative. A slice with"
            " a negative start counts from the end -- but try it with"
            " 0 before you trust it.\n\n"
            "  last_entries(['in 101', 'out 204', 'in 305', 'out 101'], 2) -> ['in 305', 'out 101']\n"
            "  last_entries(['in 101'], 5) -> ['in 101']\n\n"
            "Return: a list of strings."
        ),
        solution=("def last_entries(log, n):\n"
                  "    if n == 0:\n"
                  "        return []\n"
                  "    return log[-n:]\n"),
        trap=("def last_entries(log, n):\n"
              "    return log[-n:]\n"),
        note="log[-n:] starts n places from the end and runs to it,"
             " and a slice that asks for more than there is just"
             " gives what there is, so a short log needs no special"
             " care. Zero does. -0 is 0, so log[-0:] is log[0:], the"
             " whole list: asked for none, the trap returns every"
             " entry. It is the one value where 'count from the end'"
             " and 'count from the start' mean the same place. The"
             " guard is one line; log[len(log) - n:] avoids the"
             " problem at 0 and creates another when n is bigger than"
             " the list.",
    ),
    dict(
        id=12, ledger="P652", concept="PY4 keep what is not in another list", tier="3 - Lists on the board",
        title="The rooms nobody has taken", kind="function",
        func="still_free",
        cases=[([101, 102, 103, 104], [102, 103]), ([305, 101, 204], [101]), ([], [101]), ([101, 102], []),
               ([201, 202, 203], [201, 202, 203])],
        prompt=(
            "One list holds a floor's rooms and another the rooms"
            " already taken. Write a function `still_free(rooms,"
            " taken)` that returns a NEW list of the rooms that are"
            " not in taken, in the order they had in rooms. `not in`"
            " tests whether a value is missing from a list. Build the"
            " answer up; do not take things out of a list you are"
            " walking through.\n\n"
            "  still_free([101, 102, 103, 104], [102, 103]) -> [101, 104]\n\n"
            "Return: a list of ints."
        ),
        solution=("def still_free(rooms, taken):\n"
                  "    out = []\n"
                  "    for r in rooms:\n"
                  "        if r not in taken:\n"
                  "            out.append(r)\n"
                  "    return out\n"),
        trap=("def still_free(rooms, taken):\n"
              "    for r in rooms:\n"
              "        if r in taken:\n"
              "            rooms.remove(r)\n"
              "    return rooms\n"),
        note="A new list, filled with the rooms that pass the test:"
             " the pattern behind most list questions. The trap edits"
             " the list it is looping over. When 102 is removed"
             " everything after it moves down one place, the loop"
             " steps on to the next position, and 103 -- now sitting"
             " where 102 was -- is never looked at: the answer comes"
             " back [101, 103, 104]. It only shows when two rooms to"
             " go are side by side, and it also changes the caller's"
             " list behind their back. [r for r in rooms if r not in"
             " taken] is the same loop on one line. In SQL this is"
             " WHERE room NOT IN (...).",
    ),
    dict(
        id=13, ledger="P653", concept="PY4 drop repeats, keep the order", tier="3 - Lists on the board",
        title="A guest list with nobody on it twice", kind="function",
        func="no_repeats",
        cases=[(["Mei", "Ada", "Mei", "Hugo", "Ada"],), ([],), (["Zeno"],), (["Li", "Li", "Li"],),
               (["Hugo", "Ada", "Zeno", "Ada", "Bo", "Hugo"],)],
        prompt=(
            "The dinner list was written as guests rang down, and"
            " some rang twice. Write a function `no_repeats(names)`"
            " that returns a new list with each name once, in the"
            " order of its FIRST appearance. Keep a list of the names"
            " already seen and add a name only when it is not there"
            " yet.\n\n"
            "  no_repeats(['Mei', 'Ada', 'Mei', 'Hugo', 'Ada']) -> ['Mei', 'Ada', 'Hugo']\n\n"
            "Return: a list of strings."
        ),
        solution=("def no_repeats(names):\n"
                  "    out = []\n"
                  "    for name in names:\n"
                  "        if name not in out:\n"
                  "            out.append(name)\n"
                  "    return out\n"),
        trap=("def no_repeats(names):\n"
              "    return sorted(set(names))\n"),
        note="The answer list doubles as the memory: a name goes in"
             " only if it is not in already, so each appears once and"
             " in the order it first turned up. The trap knows that a"
             " set holds no duplicates, and that is true, but a set"
             " has no order either; sorting it gives the names"
             " alphabetically -- Ada, Hugo, Mei -- which is an order,"
             " just not the one asked for, and without the sort the"
             " order can change from one run to the next. This is"
             " SELECT DISTINCT, and the same warning applies there:"
             " DISTINCT promises no repeats and says nothing about"
             " order.",
    ),
    dict(
        id=14, ledger="P654", concept="PY3 zip two lists into lines", tier="3 - Lists on the board",
        title="Who is in which room?", kind="function",
        func="pair_up",
        cases=[(["Ada", "Hugo"], [101, 204]), (["Ada", "Hugo", "Mei"], [101, 204]), (["Ada"], [101, 204, 305]),
               ([], []), (["Zeno"], [7])],
        prompt=(
            "Two lists run side by side: guests' names, and the rooms"
            " given out in the same order. Write a function"
            " `pair_up(names, rooms)` that returns a list of lines,"
            " each a name, a colon and a space, and the room. If one"
            " list is longer than the other, stop when the shorter"
            " runs out. zip walks two lists together and hands over"
            " one item from each on every turn.\n\n"
            "  pair_up(['Ada', 'Hugo'], [101, 204]) -> ['Ada: 101', 'Hugo: 204']\n"
            "  pair_up(['Ada', 'Hugo', 'Mei'], [101, 204]) -> ['Ada: 101', 'Hugo: 204']\n\n"
            "Return: a list of strings."
        ),
        solution=("def pair_up(names, rooms):\n"
                  "    out = []\n"
                  "    for name, room in zip(names, rooms):\n"
                  "        out.append(f\"{name}: {room}\")\n"
                  "    return out\n"),
        trap=("def pair_up(names, rooms):\n"
              "    out = []\n"
              "    for i in range(len(names)):\n"
              "        out.append(f\"{names[i]}: {rooms[i]}\")\n"
              "    return out\n"),
        note="zip(names, rooms) gives pairs -- the first of each, the"
             " second of each -- and the for unpacks every pair into"
             " two names, as it did with the stays last time. It"
             " stops when either list runs out, which is the rule"
             " asked for, free. The trap walks by position, counting"
             " up to the length of names: with three guests and two"
             " rooms it asks for rooms[2], which does not exist, and"
             " the function ends in an IndexError. Counting to the"
             " shorter length would mend it; zip never needed the"
             " lengths at all. The f-string turns the room number"
             " into text without being asked.",
    ),
    dict(
        id=15, ledger="P655", concept="PY4 split a list into groups of n", tier="3 - Lists on the board",
        title="A party seated at tables", kind="function",
        func="tables_of",
        cases=[(["Ada", "Hugo", "Mei", "Zeno", "Li"], 2), (["Ada", "Hugo", "Mei", "Zeno"], 2), ([], 3),
               (["Ada"], 4), (["a", "b", "c", "d", "e", "f", "g"], 3)],
        prompt=(
            "The restaurant seats a party in the order of the list,"
            " filling one table before starting the next. Write a"
            " function `tables_of(guests, size)` that returns a list"
            " of lists: each inner list one table of `size` guests,"
            " except that the last table takes whoever is left and"
            " may be smaller. Nobody is left standing, and an empty"
            " party needs no tables. range can count in steps, and a"
            " slice that runs past the end simply stops there.\n\n"
            "  tables_of(['Ada', 'Hugo', 'Mei', 'Zeno', 'Li'], 2) -> [['Ada', 'Hugo'], ['Mei', 'Zeno'], ['Li']]\n\n"
            "Return: a list of lists of strings."
        ),
        solution=("def tables_of(guests, size):\n"
                  "    out = []\n"
                  "    for i in range(0, len(guests), size):\n"
                  "        out.append(guests[i:i + size])\n"
                  "    return out\n"),
        trap=("def tables_of(guests, size):\n"
              "    out = []\n"
              "    for t in range(len(guests) // size):\n"
              "        out.append(guests[t * size:(t + 1) * size])\n"
              "    return out\n"),
        note="range(0, len(guests), size) counts 0, 2, 4 ...: the"
             " position where each table starts. guests[i:i + size]"
             " is that table, and for the last one the slice runs off"
             " the end and returns what is there, so the short table"
             " needs no special case. The trap works out how many"
             " FULL tables there are, with //, and makes exactly"
             " those: five guests at tables of two give two tables"
             " and Li is left standing. It is right whenever the"
             " party divides evenly. Rounding the count up would mend"
             " it, as in the rooms a party needs; stepping through"
             " the starts avoids the sum altogether.",
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
