"""Python practice exercises: fifteen everyday functions over plain values.

The forty-second Python set, at the easy level of the last twelve -- no
statistics, no dicts -- and the second in a hotel's terms. Bills and
counting: a bill as it mounts up, nights as weeks and nights, the rooms a
party needs, every seventh night free, how many nights a budget covers.
Names and notes: a request split at its first colon, a greeting for a
guest with no name, a name typed carelessly put right, money text turned
into whole cents, room numbers joined into a line. Rooms and rotas: the
position of every free room, a rota moved on by some days, every room
number in a building, a corridor walked from the far end, one guest's
nights added up from pairs.

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
    # ================================================= 1 Bills and counting
    dict(
        id=1, ledger="P626", concept="PY4 running total as a list", tier="1 - Bills and counting",
        title="The bill as it mounts up", kind="function",
        func="running_bill",
        cases=[([1200, 450, 800],), ([500],), ([],), ([100, 100, 100, 100],), ([2500, 0, 300],)],
        prompt=(
            "A list holds the charges put on a room, in order, in"
            " cents. Write a function `running_bill(charges)` that"
            " returns a list of the same length: what the bill stood"
            " at after each charge. Keep one total going and add to"
            " it.\n\n"
            "  running_bill([1200, 450, 800]) -> [1200, 1650, 2450]\n\n"
            "Return: a list of ints."
        ),
        solution=("def running_bill(charges):\n"
                  "    out = []\n"
                  "    total = 0\n"
                  "    for c in charges:\n"
                  "        total += c\n"
                  "        out.append(total)\n"
                  "    return out\n"),
        trap=("def running_bill(charges):\n"
              "    return [sum(charges[:i]) for i in range(len(charges))]\n"),
        note="One variable carries the total from one turn of the loop"
             " to the next, and what gets appended is the total, not"
             " the charge. The trap adds up a slice each time and is"
             " one place out: charges[:0] is empty, so its list begins"
             " with 0 and never reaches the final bill. charges[:i +"
             " 1] would mend it, at the cost of adding the early"
             " charges up again and again. This is the list SUM ..."
             " OVER (ORDER BY ...) builds in SQL.",
    ),
    dict(
        id=2, ledger="P627", concept="PY3 divmod into a pair", tier="1 - Bills and counting",
        title="Weeks and odd nights", kind="function",
        func="weeks_and_nights",
        cases=[(10,), (7,), (6,), (0,), (30,), (14,)],
        prompt=(
            "The weekly rate applies to each full week of a stay."
            " Write a function `weeks_and_nights(nights)` that returns"
            " a tuple: the number of full weeks, and the nights left"
            " over. Both are whole numbers. // divides and drops the"
            " remainder, % gives the remainder, and divmod does both"
            " at once.\n\n"
            "  weeks_and_nights(10) -> (1, 3)\n"
            "  weeks_and_nights(14) -> (2, 0)\n\n"
            "Return: a tuple of two ints."
        ),
        solution=("def weeks_and_nights(nights):\n"
                  "    return divmod(nights, 7)\n"),
        trap=("def weeks_and_nights(nights):\n"
              "    return (nights / 7, nights % 7)\n"),
        note="divmod(a, b) is the pair (a // b, a % b), already a"
             " tuple. The trap divides with a single slash, which in"
             " Python always gives a float: ten nights become"
             " 1.4285714285714286 weeks, and even fourteen come out as"
             " 2.0, which is not the int 2 when the type counts. //"
             " is the division that stays in whole numbers, and it is"
             " the one to use whenever the answer is a count.",
    ),
    dict(
        id=3, ledger="P628", concept="PY3 round up with floor division", tier="1 - Bills and counting",
        title="How many rooms does the party need?", kind="function",
        func="rooms_needed",
        cases=[(7, 2), (8, 2), (1, 4), (0, 2), (9, 3), (10, 3)],
        prompt=(
            "A party of `guests` people is put in rooms that each"
            " sleep `sleeps`. Write a function `rooms_needed(guests,"
            " sleeps)` that returns the smallest number of rooms that"
            " holds everyone. A room that is only part full is still a"
            " room; nobody needs no rooms. Use whole-number"
            " arithmetic only.\n\n"
            "  rooms_needed(7, 2) -> 4\n"
            "  rooms_needed(8, 2) -> 4\n\n"
            "Return: an int."
        ),
        solution=("def rooms_needed(guests, sleeps):\n"
                  "    return (guests + sleeps - 1) // sleeps\n"),
        trap=("def rooms_needed(guests, sleeps):\n"
              "    return guests // sleeps + 1\n"),
        note="// rounds down, and seven people in twos need the fourth"
             " room. Adding one afterwards, the trap, is right exactly"
             " when there is a remainder and wrong when there is not:"
             " eight people get five rooms and nobody gets one. Adding"
             " sleeps - 1 BEFORE dividing pushes any part-full room"
             " over the line and leaves exact fits alone. -(-guests //"
             " sleeps) is the same trick written with two minus"
             " signs.",
    ),
    dict(
        id=4, ledger="P629", concept="PY3 every nth free by floor division", tier="1 - Bills and counting",
        title="Every seventh night is free", kind="function",
        func="nights_charged",
        cases=[(6,), (7,), (13,), (14,), (3,), (21,), (1,)],
        prompt=(
            "The group's offer: every seventh night of a stay is free."
            " Write a function `nights_charged(nights)` that returns"
            " how many nights the guest pays for. A fortnight has two"
            " free nights in it, not one.\n\n"
            "  nights_charged(7) -> 6\n"
            "  nights_charged(14) -> 12\n"
            "  nights_charged(6) -> 6\n\n"
            "Return: an int."
        ),
        solution=("def nights_charged(nights):\n"
                  "    return nights - nights // 7\n"),
        trap=("def nights_charged(nights):\n"
              "    if nights >= 7:\n"
              "        return nights - 1\n"
              "    return nights\n"),
        note="nights // 7 is the number of complete sevens in the stay,"
             " which is the number of free nights, with no if needed:"
             " for a short stay it is simply 0. The trap takes one"
             " night off any stay of a week or more and charges"
             " thirteen nights for a fortnight and twenty for three"
             " weeks. When a rule says 'every so many', reach for //"
             " before reaching for if.",
    ),
    dict(
        id=5, ledger="P630", concept="PY4 count while a running total fits", tier="1 - Bills and counting",
        title="How many nights can they afford?", kind="function",
        func="nights_afforded",
        cases=[([100, 300, 50], 200), ([80, 80, 80], 240), ([80, 80, 80], 239), ([], 500), ([500], 100),
               ([60, 70, 80, 90], 1000)],
        prompt=(
            "`prices` holds the price of each night of a stay, in"
            " order; they differ, weekends cost more. Write a function"
            " `nights_afforded(prices, budget)` that returns how many"
            " nights, starting from the first, can be paid for without"
            " going over budget. The stay has to be unbroken: the"
            " first night that does not fit ends it, however cheap the"
            " nights after it are. Spending the budget exactly is"
            " allowed.\n\n"
            "  nights_afforded([100, 300, 50], 200) -> 1\n"
            "  nights_afforded([80, 80, 80], 240) -> 3\n\n"
            "Return: an int."
        ),
        solution=("def nights_afforded(prices, budget):\n"
                  "    total = 0\n"
                  "    count = 0\n"
                  "    for p in prices:\n"
                  "        if total + p > budget:\n"
                  "            break\n"
                  "        total += p\n"
                  "        count += 1\n"
                  "    return count\n"),
        trap=("def nights_afforded(prices, budget):\n"
              "    total = 0\n"
              "    count = 0\n"
              "    for p in prices:\n"
              "        if total + p <= budget:\n"
              "            total += p\n"
              "            count += 1\n"
              "    return count\n"),
        note="break leaves the loop for good, and that is the whole"
             " difference. The trap skips the night it cannot afford"
             " and carries on, so with 200 to spend it pays for the"
             " first night, steps over the second at 300, buys the"
             " third at 50 and reports two nights -- with a night in"
             " the middle spent somewhere else. Skipping and stopping"
             " look alike in the code and are different rules.",
    ),
    # ==================================================== 2 Names and notes
    dict(
        id=6, ledger="P631", concept="PY3 partition at the first separator", tier="2 - Names and notes",
        title="A request and its detail", kind="function",
        func="split_request",
        cases=[("late checkout: after 2pm",), ("note: call at 10:30",), ("cot",), ("allergy :nuts",),
               ("  quiet room  ",)],
        prompt=(
            "Requests on a booking are typed as 'kind: detail'. Write"
            " a function `split_request(text)` that returns a tuple of"
            " the two parts, each with the spaces round it removed."
            " Only the FIRST colon divides them -- the detail may hold"
            " a time. With no colon at all the whole text is the kind"
            " and the detail is the empty string. A string has a"
            " method that cuts at the first occurrence of a separator"
            " and always gives three pieces.\n\n"
            "  split_request(\"late checkout: after 2pm\") -> (\"late checkout\", \"after 2pm\")\n"
            "  split_request(\"cot\") -> (\"cot\", \"\")\n\n"
            "Return: a tuple of two strs."
        ),
        solution=("def split_request(text):\n"
                  "    kind, _, detail = text.partition(\":\")\n"
                  "    return (kind.strip(), detail.strip())\n"),
        trap=("def split_request(text):\n"
              "    parts = text.split(\":\")\n"
              "    return (parts[0].strip(), parts[-1].strip())\n"),
        note="text.partition(':') always returns three pieces: before,"
             " the separator, after. With no colon the last two are"
             " empty, so neither special case needs an if. split, the"
             " trap, cuts at EVERY colon and returns as many pieces as"
             " that makes: 'call at 10:30' loses everything before the"
             " 30, and a request with no colon is one piece that is"
             " both first and last, so 'cot' comes back as its own"
             " detail.",
    ),
    dict(
        id=7, ledger="P632", concept="PY3 or as a fallback for an empty value", tier="2 - Names and notes",
        title="Dear whoever you are", kind="function",
        func="greeting",
        cases=[("Ada",), ("",), (None,), ("   ",), (" Hugo ",)],
        prompt=(
            "A letter opens 'Dear NAME,'. Write a function"
            " `greeting(name)` that returns that line with the name's"
            " surrounding spaces removed. The name may be missing in"
            " three ways -- None, an empty string, or nothing but"
            " spaces -- and then the letter opens 'Dear Guest,'. `a or"
            " b` gives b whenever a is empty or None.\n\n"
            "  greeting(\"Ada\") -> \"Dear Ada,\"\n"
            "  greeting(\"\") -> \"Dear Guest,\"\n\n"
            "Return: a str."
        ),
        solution=("def greeting(name):\n"
                  "    name = (name or \"\").strip()\n"
                  "    return f\"Dear {name or 'Guest'},\"\n"),
        trap=("def greeting(name):\n"
              "    if name is None:\n"
              "        name = \"Guest\"\n"
              "    return f\"Dear {name.strip()},\"\n"),
        note="None and '' both count as false, so `name or ''` turns"
             " either into a string that is safe to strip, and a"
             " second `or` catches what is left empty after the"
             " stripping. The trap tests for None alone: an empty"
             " string and a string of spaces sail past it and the"
             " letter opens 'Dear ,'. It is COALESCE again, with the"
             " difference that Python's or also replaces the empty"
             " string, which SQL's COALESCE does not.",
    ),
    dict(
        id=8, ledger="P633", concept="PY3 capitalise each word of a name", tier="2 - Names and notes",
        title="A name typed in a hurry", kind="function",
        func="tidy_name",
        cases=[("  aDA   loveLACE ",), ("hugo",), ("MEI LING CHEN",), ("niall  o",), ("",)],
        prompt=(
            "Names arrive from the web form in any state. Write a"
            " function `tidy_name(name)` that returns the name with"
            " each word starting with a capital and the rest of it in"
            " small letters, exactly one space between words, and"
            " none at the ends. split with no argument, a method that"
            " capitalises one word, and join.\n\n"
            "  tidy_name(\"  aDA   loveLACE \") -> \"Ada Lovelace\"\n\n"
            "Return: a str."
        ),
        solution=("def tidy_name(name):\n"
                  "    return \" \".join(word.capitalize() for word in name.split())\n"),
        trap=("def tidy_name(name):\n"
              "    return name.strip().capitalize()\n"),
        note="split() with no argument cuts at any run of spaces and"
             " drops the ones at the ends, so the words come out"
             " clean; capitalize() does one word; join puts single"
             " spaces back. Applied to the whole string, the trap,"
             " capitalize sees ONE thing to capitalise: the first"
             " letter goes up, every other letter goes down, the"
             " surname loses its capital and the spaces in the middle"
             " are still there.",
    ),
    dict(
        id=9, ledger="P634", concept="PY3 money text to whole cents", tier="2 - Names and notes",
        title="Money as text, cents as a number", kind="function",
        func="to_cents",
        cases=[("$12.05",), ("$1,250.50",), ("$19.99",), ("$1.15",), ("$45",), ("$0.07",)],
        prompt=(
            "Amounts are typed as text such as '$1,250.50': a dollar"
            " sign, perhaps commas, and either no decimal point or a"
            " point followed by exactly two digits. Write a function"
            " `to_cents(text)` that returns the amount as a whole"
            " number of cents. Keep it in whole numbers all the way:"
            " take the two sides of the point apart as text and"
            " convert each with int.\n\n"
            "  to_cents(\"$12.05\") -> 1205\n"
            "  to_cents(\"$1,250.50\") -> 125050\n"
            "  to_cents(\"$45\") -> 4500\n\n"
            "Return: an int."
        ),
        solution=("def to_cents(text):\n"
                  "    whole, _, part = text.replace(\"$\", \"\").replace(\",\", \"\").partition(\".\")\n"
                  "    return int(whole) * 100 + int(part or 0)\n"),
        trap=("def to_cents(text):\n"
              "    return int(float(text.replace(\"$\", \"\").replace(\",\", \"\")) * 100)\n"),
        note="The obvious route, the trap, goes through float, and a"
             " float cannot hold most decimal fractions exactly: 19.99"
             " is stored as a hair under, times 100 it is"
             " 1998.9999999999998, and int cuts that down to 1998. A"
             " cent has gone missing, on a value picked by nobody."
             " Dollars and cents taken apart as text and converted"
             " separately never leave whole numbers, which is the"
             " reason the database keeps money in cents to begin"
             " with.",
    ),
    dict(
        id=10, ledger="P635", concept="PY3 join numbers after str", tier="2 - Names and notes",
        title="The rooms on one line", kind="function",
        func="room_list",
        cases=[([101, 102, 205],), ([7],), ([],), ([312, 12],)],
        prompt=(
            "A confirmation lists the rooms booked. Write a function"
            " `room_list(rooms)` that takes a list of room numbers,"
            " which are ints, and returns them as one string with a"
            " comma and a space BETWEEN them: nothing at the start,"
            " nothing at the end. An empty list gives the empty"
            " string. join does the between part, but it will only"
            " join strings.\n\n"
            "  room_list([101, 102, 205]) -> \"101, 102, 205\"\n\n"
            "Return: a str."
        ),
        solution=("def room_list(rooms):\n"
                  "    return \", \".join(str(r) for r in rooms)\n"),
        trap=("def room_list(rooms):\n"
              "    text = \"\"\n"
              "    for r in rooms:\n"
              "        text += str(r) + \", \"\n"
              "    return text\n"),
        note="join puts the separator between items and nowhere else,"
             " which a loop that adds ', ' after every item, the trap,"
             " cannot do without cutting the last one off again. join"
             " refuses anything that is not a string -- ', '.join([101,"
             " 102]) is a TypeError -- so each number goes through str"
             " on the way in. One item gives no separator at all and"
             " no items gives '', both without an if.",
    ),
    # ===================================================== 3 Rooms and rotas
    dict(
        id=11, ledger="P636", concept="PY4 every position of a value", tier="3 - Rooms and rotas",
        title="Which rooms are free?", kind="function",
        func="free_rooms",
        cases=[(["free", "taken", "free", "free"],), (["taken", "taken"],), ([],), (["free"],),
               (["taken", "free", "taken", "free"],)],
        prompt=(
            "A list holds the state of each room along a corridor,"
            " 'free' or 'taken'. Write a function `free_rooms(states)`"
            " that returns the positions of ALL the free ones,"
            " counting from 0. enumerate hands you each item together"
            " with its position.\n\n"
            "  free_rooms([\"free\", \"taken\", \"free\", \"free\"]) -> [0, 2, 3]\n\n"
            "Return: a list of ints."
        ),
        solution=("def free_rooms(states):\n"
                  "    return [i for i, state in enumerate(states) if state == \"free\"]\n"),
        trap=("def free_rooms(states):\n"
              "    return [states.index(state) for state in states if state == \"free\"]\n"),
        note="states.index('free') answers one question only: where is"
             " the FIRST 'free'? Asked three times, the trap, it says 0"
             " three times. A position is not something you can"
             " recover from a value when values repeat; it has to be"
             " carried along, and enumerate is what carries it, giving"
             " (0, 'free'), (1, 'taken') and so on to unpack in the"
             " for.",
    ),
    dict(
        id=12, ledger="P637", concept="PY3 rotate a list, wrapping round", tier="3 - Rooms and rotas",
        title="The rota moves on", kind="function",
        func="rota",
        cases=[(["Ana", "Bo", "Cy"], 1), (["Ana", "Bo", "Cy"], 5), (["Ana", "Bo", "Cy"], 3), ([], 4),
               (["Ana"], 9), (["Ana", "Bo", "Cy", "Di"], 0)],
        prompt=(
            "The early-shift rota is a list of names; each day the"
            " person at the front goes to the back. Write a function"
            " `rota(staff, days)` that returns a NEW list showing the"
            " rota after that many days. days can be more than the"
            " number of staff -- the rota simply goes round again --"
            " and an empty rota stays empty. Two slices joined, and a"
            " remainder.\n\n"
            "  rota([\"Ana\", \"Bo\", \"Cy\"], 1) -> [\"Bo\", \"Cy\", \"Ana\"]\n"
            "  rota([\"Ana\", \"Bo\", \"Cy\"], 5) -> [\"Cy\", \"Ana\", \"Bo\"]\n\n"
            "Return: a list."
        ),
        solution=("def rota(staff, days):\n"
                  "    if not staff:\n"
                  "        return []\n"
                  "    k = days % len(staff)\n"
                  "    return staff[k:] + staff[:k]\n"),
        trap=("def rota(staff, days):\n"
              "    return staff[days:] + staff[:days]\n"),
        note="staff[k:] + staff[:k] is the list cut at k with the two"
             " pieces swapped. A slice never complains about a number"
             " that is too big, it just stops at the end, so with days"
             " = 5 the trap's first piece is empty, its second is"
             " everyone, and the rota appears not to have moved at"
             " all. The remainder brings 5 back to 2. It needs a"
             " length to divide by, hence the guard for the empty"
             " list.",
    ),
    dict(
        id=13, ledger="P638", concept="PY4 nested loops building labels", tier="3 - Rooms and rotas",
        title="Every door in the building", kind="function",
        func="room_numbers",
        cases=[(2, 3), (1, 1), (3, 2), (0, 5), (1, 12)],
        prompt=(
            "A new hotel has `floors` floors, numbered from 1, and"
            " `per_floor` rooms on each, numbered from 1. A door"
            " number is the floor followed by the room as two digits:"
            " floor 2, room 4 is '204'. Write a function"
            " `room_numbers(floors, per_floor)` that returns every"
            " door number as text, floor by floor. A loop inside a"
            " loop; an f-string can pad a number to two digits.\n\n"
            "  room_numbers(2, 3) -> [\"101\", \"102\", \"103\", \"201\", \"202\", \"203\"]\n\n"
            "Return: a list of strs."
        ),
        solution=("def room_numbers(floors, per_floor):\n"
                  "    out = []\n"
                  "    for floor in range(1, floors + 1):\n"
                  "        for n in range(1, per_floor + 1):\n"
                  "            out.append(f\"{floor}{n:02d}\")\n"
                  "    return out\n"),
        trap=("def room_numbers(floors, per_floor):\n"
              "    out = []\n"
              "    for floor in range(floors):\n"
              "        for n in range(per_floor):\n"
              "            out.append(f\"{floor}{n:02d}\")\n"
              "    return out\n"),
        note="The inner loop runs in full for every turn of the outer"
             " one, which is what puts all of floor 1 before any of"
             " floor 2. range(n) counts from 0 to n - 1, the right"
             " thing for positions in a list and the wrong thing for"
             " floors: the trap opens a hotel with a floor 0 and a"
             " room 000 and no top floor. range(1, n + 1) is the"
             " counting people do. {n:02d} pads to two digits with a"
             " zero.",
    ),
    dict(
        id=14, ledger="P639", concept="PY3 reverse into a new list", tier="3 - Rooms and rotas",
        title="Starting from the far end", kind="function",
        func="cleaning_order",
        cases=[(["101", "102", "103"],), ([],), (["201"],), (["305", "301", "303", "302"],)],
        prompt=(
            "Housekeeping is given the rooms to clean in the order"
            " they lie along the corridor, and today starts from the"
            " far end. Write a function `cleaning_order(rooms)` that"
            " returns a NEW list with the same rooms in the opposite"
            " order -- the order they were given in, backwards, not"
            " sorted. A slice can step backwards.\n\n"
            "  cleaning_order([\"101\", \"102\", \"103\"]) -> [\"103\", \"102\", \"101\"]\n\n"
            "Return: a list."
        ),
        solution=("def cleaning_order(rooms):\n"
                  "    return rooms[::-1]\n"),
        trap=("def cleaning_order(rooms):\n"
              "    return rooms.reverse()\n"),
        note="rooms.reverse() turns the list round where it stands and"
             " returns None, as every list method that changes the"
             " list does -- sort, append and extend too -- so the trap"
             " hands back None and has altered the caller's list on"
             " the way. rooms[::-1] and list(reversed(rooms)) each"
             " build a new one. sorted(rooms, reverse=True) is a"
             " different thing: it would put 305 first whether or not"
             " it is at the far end.",
    ),
    dict(
        id=15, ledger="P640", concept="PY4 sum from pairs with a filter", tier="3 - Rooms and rotas",
        title="One guest's nights, added up", kind="function",
        func="nights_for",
        cases=[([["Ada", 3], ["Hugo", 2], ["Ada", 4]], "Ada"), ([["Ada", 3], ["Hugo", 2]], "Mei"), ([], "Ada"),
               ([["Hugo", 2], ["Hugo", 1], ["Hugo", 7]], "Hugo"), ([["Ada", 1]], "Ada")],
        prompt=(
            "`stays` is a list of pairs, each a guest's name and a"
            " number of nights: [[\"Ada\", 3], [\"Hugo\", 2]]. A guest"
            " can appear more than once. Write a function"
            " `nights_for(stays, guest)` that returns the total nights"
            " of all the stays under that name, and 0 when there are"
            " none. A for loop can unpack each pair into two names as"
            " it goes.\n\n"
            "  nights_for([[\"Ada\", 3], [\"Hugo\", 2], [\"Ada\", 4]], \"Ada\") -> 7\n\n"
            "Return: an int."
        ),
        solution=("def nights_for(stays, guest):\n"
                  "    total = 0\n"
                  "    for name, nights in stays:\n"
                  "        if name == guest:\n"
                  "            total += nights\n"
                  "    return total\n"),
        trap=("def nights_for(stays, guest):\n"
              "    for name, nights in stays:\n"
              "        if name == guest:\n"
              "            return nights\n"
              "    return 0\n"),
        note="`for name, nights in stays` unpacks each pair as it"
             " arrives, so the body can talk about a name and a number"
             " where it would otherwise say stay[0] and stay[1]. A"
             " return inside the loop, the trap, ends the function at"
             " the first match: Ada's three nights are reported and"
             " her other four never looked at. Find-the-first and"
             " add-them-all start out as the same loop; the difference"
             " is whether anything is kept between turns. In SQL this"
             " is SUM with a WHERE.",
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
