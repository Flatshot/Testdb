"""Python practice exercises: fifteen everyday functions over plain values.

The forty-fourth Python set, at the easy level of the last fourteen -- no
statistics, no dicts, nothing to import -- and the fourth in a hotel's
terms. Times and numbers: a clock time turned into minutes, a price with
a percentage off, the nights left counted down, the first amount over a
limit, a meter's readings turned into daily use. Text as it is typed:
runs of spaces tidied, a label cut to fit, whether a text has a digit in
it, a range of rooms written '101-105', names joined with commas and an
'and'. Lists and registers: a place in a queue, the three best scores,
whether a list is in order, one column out of a register, the longest
run of nights a room was let.

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
    # ================================================ 1 Times and numbers
    dict(
        id=1, ledger="P656", concept="PY3 clock text to minutes", tier="1 - Times and numbers",
        title="Half past two, in minutes", kind="function",
        func="to_minutes",
        cases=[("14:30",), ("00:05",), ("9:00",), ("23:59",), ("00:00",)],
        prompt=(
            "Times are easier to compare as one number. Write a"
            " function `to_minutes(clock)` that takes a time written"
            " as hours, a colon and minutes, and returns the number"
            " of minutes since midnight. split cuts the text at the"
            " colon; the two pieces are still text, and int turns"
            " each into a number, leading zero or not.\n\n"
            "  to_minutes('14:30') -> 870\n"
            "  to_minutes('00:05') -> 5\n\n"
            "Return: an int."
        ),
        solution=("def to_minutes(clock):\n"
                  "    hours, minutes = clock.split(\":\")\n"
                  "    return int(hours) * 60 + int(minutes)\n"),
        trap=("def to_minutes(clock):\n"
              "    return int(clock.replace(\":\", \"\"))\n"),
        note="split(\":\") gives two pieces of text and the"
             " assignment unpacks them into two names. int('05') is"
             " 5, so the leading zeros look after themselves, and an"
             " hour is 60 minutes. The trap takes the colon out and"
             " reads what is left as a number: 1430 for half past"
             " two. It even sorts correctly, which is why it"
             " survives, but an hour in it is worth 100, so 14:30"
             " less 13:45 comes to 85 minutes when it is 45. Before"
             " doing sums with a time, turn it into one unit.",
    ),
    dict(
        id=2, ledger="P657", concept="PY3 a percentage off, in whole cents", tier="1 - Times and numbers",
        title="Fifteen per cent off", kind="function",
        func="discounted",
        cases=[(10000, 15), (9990, 10), (5000, 0), (8000, 100), (333, 50), (12550, 20)],
        prompt=(
            "A rate in cents is reduced by a whole-number percentage."
            " Write a function `discounted(cents, percent)` that"
            " returns the reduced price in whole cents, any fraction"
            " of a cent dropped. percent runs from 0 to 100. What is"
            " left after 15 per cent off is 85 per cent: multiply by"
            " that first, then divide by 100 with the operator that"
            " keeps the answer a whole number.\n\n"
            "  discounted(10000, 15) -> 8500\n"
            "  discounted(333, 50) -> 166\n\n"
            "Return: an int."
        ),
        solution=("def discounted(cents, percent):\n"
                  "    return cents * (100 - percent) // 100\n"),
        trap=("def discounted(cents, percent):\n"
              "    return cents - cents * percent / 100\n"),
        note="cents * (100 - percent) is still a whole number, and"
             " // 100 divides it and drops the remainder, so nothing"
             " ever leaves whole numbers. The trap is the sum as it"
             " is said aloud -- the price less the discount -- with a"
             " single slash, and one slash always makes a float:"
             " 8500.0, which is not the int 8500, and 166.5 for half"
             " of 333, a price with half a cent in it. Multiply"
             " before dividing as well: (100 - percent) // 100 worked"
             " out first is 0 for every percentage but 0. Money stays"
             " in whole cents from one end to the other.",
    ),
    dict(
        id=3, ledger="P658", concept="PY3 range counting down", tier="1 - Times and numbers",
        title="Three nights left, two, one", kind="function",
        func="nights_left",
        cases=[(3,), (1,), (0,), (5,)],
        prompt=(
            "The lobby screen counts a guest's stay down. Write a"
            " function `nights_left(n)` that returns a list of the"
            " whole numbers from n down to 1. With n of 0 the list is"
            " empty. range can count backwards if its third argument"
            " is negative; it still stops BEFORE its second argument,"
            " so think about what that has to be.\n\n"
            "  nights_left(3) -> [3, 2, 1]\n"
            "  nights_left(0) -> []\n\n"
            "Return: a list of ints."
        ),
        solution=("def nights_left(n):\n"
                  "    return list(range(n, 0, -1))\n"),
        trap=("def nights_left(n):\n"
              "    return list(range(n, 1, -1))\n"),
        note="range(start, stop, step) begins at start, moves by"
             " step, and stops before it reaches stop, whichever way"
             " it is travelling. To finish ON 1 going down, stop has"
             " to be 0. The trap writes 1 because 1 is the last"
             " number wanted, and gets [3, 2]: the guest's final"
             " night never shows. It is the same rule as counting up,"
             " where range(1, n + 1) is needed to include n, seen"
             " from the other end. list() turns the range into a real"
             " list, which is what is compared.",
    ),
    dict(
        id=4, ledger="P659", concept="PY4 the first item that passes, or None", tier="1 - Times and numbers",
        title="The first charge over the limit", kind="function",
        func="first_over",
        cases=[([1200, 4500, 800, 9000], 4000), ([1200, 800], 4000), ([], 100), ([5000, 5000], 5000),
               ([100, 200, 300], 150), ([7000], 10)],
        prompt=(
            "The night auditor reads down a bill looking for the"
            " first charge that needs a manager's signature. Write a"
            " function `first_over(amounts, limit)` that returns the"
            " FIRST amount in the list that is greater than limit, or"
            " None if no amount is. An amount equal to the limit is"
            " not over it. A return inside a loop ends the function"
            " there and then.\n\n"
            "  first_over([1200, 4500, 800, 9000], 4000) -> 4500\n"
            "  first_over([1200, 800], 4000) -> None\n\n"
            "Return: an int, or None."
        ),
        solution=("def first_over(amounts, limit):\n"
                  "    for a in amounts:\n"
                  "        if a > limit:\n"
                  "            return a\n"
                  "    return None\n"),
        trap=("def first_over(amounts, limit):\n"
              "    found = None\n"
              "    for a in amounts:\n"
              "        if a > limit:\n"
              "            found = a\n"
              "    return found\n"),
        note="The loop returns the moment an amount passes, so the"
             " rest of the list is never looked at, and the return"
             " None after the loop is reached only when nothing"
             " passed. The trap remembers the amount and carries on:"
             " each later one that passes overwrites it, and what"
             " comes back is the LAST over the limit, 9000 where the"
             " answer is 4500. It is right whenever only one amount"
             " qualifies. Whether you want the first or the last"
             " decides whether the loop stops or keeps going. This is"
             " the mirror of 'has everyone settled up': there, one"
             " failure answered False early.",
    ),
    dict(
        id=5, ledger="P660", concept="PY4 differences between neighbours", tier="1 - Times and numbers",
        title="What the meter says each morning", kind="function",
        func="daily_use",
        cases=[([100, 130, 135, 180],), ([50],), ([],), ([10, 10, 25],), ([0, 7],)],
        prompt=(
            "The laundry's water meter is read every morning and only"
            " ever goes up. Write a function `daily_use(readings)`"
            " that returns a list of how much was used between each"
            " reading and the next: each reading less the one before"
            " it. Four readings give three differences; one reading,"
            " or none, gives an empty list. Walk the positions with"
            " range -- and choose where to start.\n\n"
            "  daily_use([100, 130, 135, 180]) -> [30, 5, 45]\n"
            "  daily_use([50]) -> []\n\n"
            "Return: a list of ints."
        ),
        solution=("def daily_use(readings):\n"
                  "    out = []\n"
                  "    for i in range(1, len(readings)):\n"
                  "        out.append(readings[i] - readings[i - 1])\n"
                  "    return out\n"),
        trap=("def daily_use(readings):\n"
              "    out = []\n"
              "    for i in range(len(readings)):\n"
              "        out.append(readings[i] - readings[i - 1])\n"
              "    return out\n"),
        note="Each difference needs a reading and the one before it,"
             " and the first reading has nothing before it, so the"
             " loop starts at position 1. The trap starts at 0, where"
             " i - 1 is -1 -- and Python does not complain, because"
             " position -1 is the LAST item. The first 'difference'"
             " is the first reading less the last, -80, and there is"
             " one answer too many. An index that goes negative fails"
             " silently, which is worse than failing. zip(readings,"
             " readings[1:]) pairs each reading with the next and"
             " needs no positions at all.",
    ),
    # ============================================== 2 Text as it is typed
    dict(
        id=6, ledger="P661", concept="PY3 split and join to tidy spaces", tier="2 - Text as it is typed",
        title="One space between words, none at the ends", kind="function",
        func="tidy_spaces",
        cases=[("  late   check-out  please ",), ("one two",), ("",), ("   ",), ("a    b     c",), ("quiet",)],
        prompt=(
            "Notes typed in a hurry have spaces everywhere. Write a"
            " function `tidy_spaces(text)` that returns the text with"
            " exactly one space between words and none at either"
            " end. A text of nothing but spaces becomes ''. split"
            " with no argument cuts at any run of spaces, however"
            " long, and join puts the pieces back with whatever you"
            " choose between them.\n\n"
            "  tidy_spaces('  late   check-out  please ') -> 'late check-out please'\n"
            "  tidy_spaces('   ') -> ''\n\n"
            "Return: a string."
        ),
        solution=("def tidy_spaces(text):\n"
                  "    return \" \".join(text.split())\n"),
        trap=("def tidy_spaces(text):\n"
              "    return text.strip().replace(\"  \", \" \")\n"),
        note="text.split() gives the words alone, with every space"
             " gone, and \" \".join(...) puts exactly one back between"
             " each pair. The ends take care of themselves, since a"
             " separator only goes BETWEEN items. The trap swaps two"
             " spaces for one, which sounds right and goes through"
             " the text once: three spaces become two, five become"
             " three, and 'late  check-out' still has a gap. Running"
             " it in a loop until nothing changes would work; taking"
             " the text apart and building it again cannot fail."
             " split and join are a pair worth remembering together.",
    ),
    dict(
        id=7, ledger="P662", concept="PY3 cut to a width, dots included", tier="2 - Text as it is typed",
        title="A name that fits on the label", kind="function",
        func="fit_label",
        cases=[("Lakeside Lodge", 10), ("Spa", 10), ("Castle View", 11), ("Station House", 12),
               ("Fellfoot Inn", 3), ("", 5)],
        prompt=(
            "A label printer has room for `width` characters. Write a"
            " function `fit_label(text, width)`: a text that fits is"
            " returned as it is; a longer one is cut short and ends"
            " in three full stops, and the result -- dots included --"
            " is exactly width characters long. width is never less"
            " than 3. len measures a string and a slice takes the"
            " front of it.\n\n"
            "  fit_label('Lakeside Lodge', 10) -> 'Lakesid...'\n"
            "  fit_label('Spa', 10) -> 'Spa'\n\n"
            "Return: a string."
        ),
        solution=("def fit_label(text, width):\n"
                  "    if len(text) <= width:\n"
                  "        return text\n"
                  "    return text[:width - 3] + \"...\"\n"),
        trap=("def fit_label(text, width):\n"
              "    if len(text) <= width:\n"
              "        return text\n"
              "    return text[:width] + \"...\"\n"),
        note="The dots are part of the label, so they come out of the"
             " width: width - 3 characters of the text, then three"
             " dots. The trap keeps width characters and THEN adds"
             " the dots, making 'Lakeside L...', thirteen characters"
             " for a label ten wide -- the one thing the function was"
             " for. A text exactly as long as the width fits and is"
             " left alone, which is why the test is <= and not <."
             " With a width of 3 the slice is text[:0], empty, and"
             " the label is just the dots.",
    ),
    dict(
        id=8, ledger="P663", concept="PY4 any character passes a test", tier="2 - Text as it is typed",
        title="Is there a number in it?", kind="function",
        func="has_digit",
        cases=[("Room 12 please",), ("no number here",), ("",), ("7",), ("flat B",), ("B2",)],
        prompt=(
            "A form rejects an address line with no number anywhere"
            " in it. Write a function `has_digit(text)` that returns"
            " True if at least one character of the text is a digit,"
            " and False otherwise, the empty text included. A for"
            " loop over a string hands over one character at a time,"
            " and a string has a method that says whether it is made"
            " of digits.\n\n"
            "  has_digit('Room 12 please') -> True\n"
            "  has_digit('no number here') -> False\n\n"
            "Return: a bool."
        ),
        solution=("def has_digit(text):\n"
                  "    for ch in text:\n"
                  "        if ch.isdigit():\n"
                  "            return True\n"
                  "    return False\n"),
        trap=("def has_digit(text):\n"
              "    return text.isdigit()\n"),
        note="isdigit asked of ONE character says whether that"
             " character is a digit, and the loop returns True at the"
             " first that is; False waits until every character has"
             " been looked at. The trap asks the whole text, and"
             " isdigit on a longer string means 'is EVERY character a"
             " digit': '7' passes, 'Room 12 please' does not. The"
             " method is the same and the question is opposite -- all"
             " against any. any(ch.isdigit() for ch in text) is the"
             " loop in one line. In SQL the pair is EXISTS and NOT"
             " EXISTS.",
    ),
    dict(
        id=9, ledger="P664", concept="PY3 a range written as text", tier="2 - Text as it is typed",
        title="Rooms 101 to 105", kind="function",
        func="room_range",
        cases=[("101-105",), ("204-204",), ("7 - 9",), ("310-312",)],
        prompt=(
            "Housekeeping's job sheet says '101-105', meaning every"
            " room from 101 to 105, BOTH ends included. Write a"
            " function `room_range(text)` that returns those room"
            " numbers as a list of ints. The first number is never"
            " larger than the second; there may be spaces round the"
            " hyphen, which int ignores. split, int, and range --"
            " remembering where range stops.\n\n"
            "  room_range('101-105') -> [101, 102, 103, 104, 105]\n"
            "  room_range('204-204') -> [204]\n\n"
            "Return: a list of ints."
        ),
        solution=("def room_range(text):\n"
                  "    first, last = text.split(\"-\")\n"
                  "    return list(range(int(first), int(last) + 1))\n"),
        trap=("def room_range(text):\n"
              "    first, last = text.split(\"-\")\n"
              "    return list(range(int(first), int(last)))\n"),
        note="split(\"-\") gives the two ends as text, int makes them"
             " numbers -- int(' 9') is 9, spaces and all -- and range"
             " runs from the first up to but NOT including its second"
             " argument, so that has to be last + 1. The trap forgets"
             " the + 1: room 105 is never cleaned, and '204-204', one"
             " room, becomes no rooms at all. People say ranges with"
             " both ends in; range, slices and the hotel's own"
             " check_in and check_out leave the far end out. Each"
             " time one is turned into the other, a 1 is owed.",
    ),
    dict(
        id=10, ledger="P665", concept="PY3 commas, then 'and' before the last", tier="2 - Text as it is typed",
        title="Ada, Hugo and Mei", kind="function",
        func="name_list",
        cases=[(["Ada", "Hugo", "Mei"],), (["Ada", "Hugo"],), (["Ada"],), ([],),
               (["Ada", "Hugo", "Mei", "Zeno"],)],
        prompt=(
            "A welcome card lists the party the way a person would"
            " write it. Write a function `name_list(names)` that"
            " joins the names with a comma and a space, except that"
            " the last two are joined by the word 'and' with a space"
            " each side. One name is returned by itself, and an empty"
            " list gives ''. names[:-1] is every name but the last"
            " and names[-1] is the last.\n\n"
            "  name_list(['Ada', 'Hugo', 'Mei']) -> 'Ada, Hugo and Mei'\n"
            "  name_list(['Ada', 'Hugo']) -> 'Ada and Hugo'\n"
            "  name_list(['Ada']) -> 'Ada'\n\n"
            "Return: a string."
        ),
        solution=("def name_list(names):\n"
                  "    if not names:\n"
                  "        return \"\"\n"
                  "    if len(names) == 1:\n"
                  "        return names[0]\n"
                  "    return \", \".join(names[:-1]) + \" and \" + names[-1]\n"),
        trap=("def name_list(names):\n"
              "    if not names:\n"
              "        return \"\"\n"
              "    return \", \".join(names[:-1]) + \" and \" + names[-1]\n"),
        note="For two names or more the rule is one line: everything"
             " but the last joined with commas, then ' and ', then"
             " the last. With two names, names[:-1] holds one and the"
             " join adds no comma, so 'Ada and Hugo' needs no case of"
             " its own. One name does: names[:-1] is empty, the join"
             " gives '', and the trap sends out ' and Ada'. The empty"
             " list would be worse, since names[-1] of nothing is an"
             " error. The small sizes -- none, one, two -- are where"
             " a rule about 'the last two' runs out of things to"
             " apply to, so they are the ones to try.",
    ),
    # ============================================ 3 Lists and registers
    dict(
        id=11, ledger="P666", concept="PY3 position counted from one, or zero", tier="3 - Lists and registers",
        title="Where am I in the queue?", kind="function",
        func="queue_place",
        cases=[(["Ada", "Hugo", "Mei"], "Hugo"), (["Ada", "Hugo", "Mei"], "Ada"), (["Ada", "Hugo", "Mei"], "Zeno"),
               ([], "Ada"), (["Li", "Li"], "Li")],
        prompt=(
            "Guests wait for a taxi in the order of a list. Write a"
            " function `queue_place(queue, name)` that returns the"
            " guest's place counted the way people count -- 1 for the"
            " front -- and 0 if the name is not in the queue. If the"
            " name is there twice, the first one counts. A list's"
            " index method finds a value's position, counted from 0,"
            " and raises an error when the value is missing, so ask"
            " with `in` first.\n\n"
            "  queue_place(['Ada', 'Hugo', 'Mei'], 'Hugo') -> 2\n"
            "  queue_place(['Ada', 'Hugo', 'Mei'], 'Zeno') -> 0\n\n"
            "Return: an int."
        ),
        solution=("def queue_place(queue, name):\n"
                  "    if name not in queue:\n"
                  "        return 0\n"
                  "    return queue.index(name) + 1\n"),
        trap=("def queue_place(queue, name):\n"
              "    if name in queue:\n"
              "        return queue.index(name)\n"
              "    return 0\n"),
        note="index counts from 0 and people count from 1, so the"
             " place is index + 1. That is also what frees 0 to mean"
             " 'not here'. The trap returns the index as it comes:"
             " Hugo, second in line, is told 1, and Ada at the front"
             " is told 0 -- the very answer that means she is not in"
             " the queue at all. Two different facts with one value"
             " cannot be told apart by whoever reads it. The `in`"
             " test comes first because index does not return a"
             " polite 'no': it stops the program with a ValueError.",
    ),
    dict(
        id=12, ledger="P667", concept="PY3 sorted, reversed, and sliced", tier="3 - Lists and registers",
        title="The three best scores", kind="function",
        func="top_three",
        cases=[([3, 5, 1, 4, 2],), ([4, 4, 5, 1],), ([2],), ([],), ([1, 2, 3],)],
        prompt=(
            "A hotel wants its three best review scores for the"
            " poster. Write a function `top_three(scores)` that"
            " returns a NEW list of the three highest scores, the"
            " highest first. With fewer than three scores it returns"
            " them all, still highest first. Equal scores each count."
            " sorted returns a new sorted list and can be told to"
            " sort downwards; a slice takes the front.\n\n"
            "  top_three([3, 5, 1, 4, 2]) -> [5, 4, 3]\n"
            "  top_three([2]) -> [2]\n\n"
            "Return: a list of ints."
        ),
        solution=("def top_three(scores):\n"
                  "    return sorted(scores, reverse=True)[:3]\n"),
        trap=("def top_three(scores):\n"
              "    return sorted(scores)[-3:]\n"),
        note="sorted(scores, reverse=True) is a new list from the"
             " highest down, and [:3] takes its first three, or"
             " however many there are. The trap sorts upwards and"
             " takes the last three: the right three scores, in the"
             " wrong order, [3, 4, 5]. A list is its items AND their"
             " order, and [3, 4, 5] is not [5, 4, 3]. sorted leaves"
             " the caller's list alone; scores.sort() would rearrange"
             " it and return None. This is ORDER BY score DESC LIMIT"
             " 3, and there too the direction is half the answer.",
    ),
    dict(
        id=13, ledger="P668", concept="PY4 is each item at least the one before", tier="3 - Lists and registers",
        title="Is the list in order?", kind="function",
        func="in_order",
        cases=[([101, 102, 205],), ([101, 205, 102],), ([],), ([7],), ([101, 101, 102],), ([102, 101],),
               ([1, 2, 3, 2],)],
        prompt=(
            "The cleaning round should run through the rooms in"
            " rising order. Write a function `in_order(rooms)` that"
            " returns True when no room number is lower than the one"
            " before it, and False as soon as one is. Two equal"
            " numbers in a row are in order. An empty list and a list"
            " of one are in order too. Compare each item with its"
            " neighbour.\n\n"
            "  in_order([101, 102, 205]) -> True\n"
            "  in_order([101, 205, 102]) -> False\n\n"
            "Return: a bool."
        ),
        solution=("def in_order(rooms):\n"
                  "    for i in range(1, len(rooms)):\n"
                  "        if rooms[i] < rooms[i - 1]:\n"
                  "            return False\n"
                  "    return True\n"),
        trap=("def in_order(rooms):\n"
              "    return rooms == rooms.sort()\n"),
        note="The loop starts at position 1, as the meter did, and"
             " looks for one pair the wrong way round. Finding it"
             " answers False at once; True is only said after the"
             " last pair. The trap means to compare the list with a"
             " sorted version of itself, a fair idea, but .sort()"
             " sorts the list in place and returns None, so the"
             " comparison is always list == None: False every time,"
             " and the caller's list has been rearranged as well."
             " sorted(rooms) == rooms is the idea done properly."
             " Methods that change a thing usually return nothing;"
             " functions that return a new thing leave the old one"
             " alone.",
    ),
    dict(
        id=14, ledger="P669", concept="PY4 one column from a list of rows", tier="3 - Lists and registers",
        title="Just the names from the register", kind="function",
        func="names_only",
        cases=[([["Ada", 101, 2], ["Hugo", 204, 1]],), ([],), ([["Mei", 305, 7]],),
               ([["Li", 7, 1], ["Li", 8, 1], ["Zeno", 9, 3]],)],
        prompt=(
            "The register is a list of rows, and each row is a small"
            " list: a name, a room and a number of nights. Write a"
            " function `names_only(register)` that returns a list of"
            " just the names, one for each row, in order, repeats and"
            " all. The loop hands over one ROW at a time; the name is"
            " the first thing in it.\n\n"
            "  names_only([['Ada', 101, 2], ['Hugo', 204, 1]]) -> ['Ada', 'Hugo']\n"
            "  names_only([]) -> []\n\n"
            "Return: a list of strings."
        ),
        solution=("def names_only(register):\n"
                  "    out = []\n"
                  "    for row in register:\n"
                  "        out.append(row[0])\n"
                  "    return out\n"),
        trap=("def names_only(register):\n"
              "    return register[0]\n"),
        note="A list of lists has two levels: register[0] is the"
             " first ROW, and row[0] is the first thing IN a row. The"
             " answer wants the second kind of [0] taken from every"
             " row, which takes a loop. The trap takes the first kind"
             " once and returns ['Ada', 101, 2], everything about one"
             " guest in place of one thing about every guest -- and"
             " an error for an empty register. It is the difference"
             " between a row and a column. In SQL the loop is simply"
             " SELECT name FROM register.",
    ),
    dict(
        id=15, ledger="P670", concept="PY4 longest run, carrying two counts", tier="3 - Lists and registers",
        title="The longest run of nights let", kind="function",
        func="longest_run",
        cases=[([1, 1, 0, 1, 1, 1, 0],), ([0, 0],), ([],), ([1, 1, 1],), ([1, 0, 1, 0, 1],), ([0, 1, 1],),
               ([1, 1, 0, 1],)],
        prompt=(
            "A room's month is a list with a 1 for each night it was"
            " let and a 0 for each night it stood empty. Write a"
            " function `longest_run(nights)` that returns the length"
            " of the longest unbroken run of 1s, and 0 if there is"
            " none. Carry two numbers through the loop: the length of"
            " the run you are in, and the best seen so far. A 0 ends"
            " a run -- and so does the end of the list.\n\n"
            "  longest_run([1, 1, 0, 1, 1, 1, 0]) -> 3\n"
            "  longest_run([0, 1, 1]) -> 2\n\n"
            "Return: an int."
        ),
        solution=("def longest_run(nights):\n"
                  "    best = 0\n"
                  "    run = 0\n"
                  "    for n in nights:\n"
                  "        if n == 1:\n"
                  "            run += 1\n"
                  "            if run > best:\n"
                  "                best = run\n"
                  "        else:\n"
                  "            run = 0\n"
                  "    return best\n"),
        trap=("def longest_run(nights):\n"
              "    best = 0\n"
              "    run = 0\n"
              "    for n in nights:\n"
              "        if n == 1:\n"
              "            run += 1\n"
              "        else:\n"
              "            if run > best:\n"
              "                best = run\n"
              "            run = 0\n"
              "    return best\n"),
        note="`run` grows with each 1 and goes back to nothing at a"
             " 0; `best` only ever rises. The solution compares the"
             " two every time the run grows, so best is right at"
             " every moment. The trap compares only when a 0 arrives"
             " to end the run, which reads sensibly -- a run is"
             " measured when it is over -- but a run that reaches the"
             " end of the list is never followed by a 0 and is never"
             " measured: [1, 1, 1] gives 0. It is right for every"
             " month that ends on an empty night. Whatever a loop"
             " does 'when the group ends' has to happen once more"
             " after the loop, or else be done as you go.",
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
