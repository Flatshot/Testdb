"""Python practice exercises: fifteen everyday functions over plain values.

The forty-first Python set, at the easy level of the last eleven -- no
statistics, no dicts -- and the first in a hotel's terms, to go with the
new SQL schema. Dates, with the datetime module: the nights between two
dates, the date so many nights on, the day of the week, every night of a
stay, whether two stays collide. Guests and bills: a bill split to the
cent, a party counted into adults and children, a booking's guests on one
line, something shaped like an email address, a long list cut short.
Rooms and floors: the floor from a room number, the next room type up,
the odd-numbered rooms, every room on every floor, two guests swapped.

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
    # ======================================== 1 Dates, with the datetime module
    dict(
        id=1, ledger="P611", concept="PY3 days between two dates", tier="1 - Dates, with datetime",
        title="How many nights is the stay?", kind="function",
        func="nights",
        cases=[("2026-03-06", "2026-03-13"), ("2026-01-30", "2026-02-02"), ("2025-12-31", "2026-01-01"), ("2024-02-27", "2024-03-01"), ("2026-06-01", "2026-06-02")],
        prompt=(
            "Dates arrive as 'YYYY-MM-DD' text. Write a function"
            " `nights(check_in, check_out)` that returns the number of"
            " nights between them. `from datetime import date` gives"
            " you date.fromisoformat(text); one date minus another is"
            " a length of time with a .days.\n\n"
            "  nights(\"2026-03-06\", \"2026-03-13\") -> 7\n"
            "  nights(\"2026-01-30\", \"2026-02-02\") -> 3\n\n"
            "Return: an int."
        ),
        solution=("from datetime import date\n"
                  "\n"
                  "def nights(check_in, check_out):\n"
                  "    return (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days\n"),
        trap=("def nights(check_in, check_out):\n"
              "    return int(check_out[8:]) - int(check_in[8:])\n"),
        note="A date is not a number, and the day of the month is not"
             " the date. Subtracting the last two digits, the trap,"
             " works inside one month and gives -28 for a stay from 30"
             " January to 2 February. date.fromisoformat turns the"
             " text into a real date, and subtracting two dates gives"
             " a timedelta whose .days already knows how long each"
             " month is, and that 2024 had a 29th of February.",
    ),
    dict(
        id=2, ledger="P612", concept="PY3 add days to a date", tier="1 - Dates, with datetime",
        title="The morning they leave", kind="function",
        func="check_out_date",
        cases=[("2026-03-06", 7), ("2026-01-30", 3), ("2025-12-31", 1), ("2026-06-10", 1), ("2024-02-28", 2)],
        prompt=(
            "Write a function `check_out_date(check_in, nights)` that"
            " returns the date so many nights after check_in, as"
            " 'YYYY-MM-DD' text. From datetime, a timedelta(days=n)"
            " can be added to a date, and a date has .isoformat() to"
            " turn it back into text.\n\n"
            "  check_out_date(\"2026-01-30\", 3) -> \"2026-02-02\"\n\n"
            "Return: a str."
        ),
        solution=("from datetime import date, timedelta\n"
                  "\n"
                  "def check_out_date(check_in, nights):\n"
                  "    return (date.fromisoformat(check_in) + timedelta(days=nights)).isoformat()\n"),
        trap=("def check_out_date(check_in, nights):\n"
              "    return check_in[:8] + f\"{int(check_in[8:]) + nights:02d}\"\n"),
        note="Text in, date arithmetic in the middle, text out:"
             " fromisoformat and isoformat are the two doors, and"
             " timedelta is the only thing you may add to a date. The"
             " trap does the sum on the day digits and cheerfully"
             " returns 2026-01-33; it has no idea where a month ends."
             " The real version rolls 31 December into the next year"
             " and gets the leap day right without being told.",
    ),
    dict(
        id=3, ledger="P613", concept="PY3 weekday of a date", tier="1 - Dates, with datetime",
        title="What day of the week is that?", kind="function",
        func="day_name",
        cases=[("2026-06-01",), ("2025-12-31",), ("2026-03-08",), ("2026-03-07",), ("2026-06-30",)],
        prompt=(
            "Write a function `day_name(day)` that returns the English"
            " name of the weekday for a 'YYYY-MM-DD' date. A date has"
            " a .weekday() method that gives a number: 0 for Monday up"
            " to 6 for Sunday. Use it to pick from a list of names.\n\n"
            "  day_name(\"2026-06-01\") -> \"Monday\"\n"
            "  day_name(\"2026-03-08\") -> \"Sunday\"\n\n"
            "Return: a str."
        ),
        solution=("from datetime import date\n"
                  "\n"
                  "DAYS = [\"Monday\", \"Tuesday\", \"Wednesday\", \"Thursday\", \"Friday\", \"Saturday\", \"Sunday\"]\n"
                  "\n"
                  "def day_name(day):\n"
                  "    return DAYS[date.fromisoformat(day).weekday()]\n"),
        trap=("from datetime import date\n"
              "\n"
              "DAYS = [\"Sunday\", \"Monday\", \"Tuesday\", \"Wednesday\", \"Thursday\", \"Friday\", \"Saturday\"]\n"
              "\n"
              "def day_name(day):\n"
              "    return DAYS[date.fromisoformat(day).weekday()]\n"),
        note="weekday() counts from Monday as 0, so the list of names"
             " has to start with Monday as well. The trap's list"
             " starts on Sunday, the way a wall calendar often does,"
             " and every answer comes out a day early. A list is the"
             " simplest lookup there is when the keys are 0, 1, 2...:"
             " the number IS the position. SQLite's strftime('%w')"
             " counts the other way, from Sunday as 0.",
    ),
    dict(
        id=4, ledger="P614", concept="PY3 list of dates from a range", tier="1 - Dates, with datetime",
        title="Every night of the stay", kind="function",
        func="stay_nights",
        cases=[("2026-03-06", "2026-03-09"), ("2026-01-30", "2026-02-02"), ("2026-06-01", "2026-06-02"), ("2025-12-30", "2026-01-01")],
        prompt=(
            "Write a function `stay_nights(check_in, check_out)` that"
            " returns the date of every night of the stay as"
            " 'YYYY-MM-DD' text, in order. The first night is"
            " check_in; check_out is the morning of departure and is"
            " NOT a night. range, and a timedelta for each step.\n\n"
            "  stay_nights(\"2026-03-06\", \"2026-03-09\") -> [\"2026-03-06\", \"2026-03-07\", \"2026-03-08\"]\n\n"
            "Return: a list of str."
        ),
        solution=("from datetime import date, timedelta\n"
                  "\n"
                  "def stay_nights(check_in, check_out):\n"
                  "    first = date.fromisoformat(check_in)\n"
                  "    count = (date.fromisoformat(check_out) - first).days\n"
                  "    return [(first + timedelta(days=n)).isoformat() for n in range(count)]\n"),
        trap=("from datetime import date, timedelta\n"
              "\n"
              "def stay_nights(check_in, check_out):\n"
              "    first = date.fromisoformat(check_in)\n"
              "    count = (date.fromisoformat(check_out) - first).days\n"
              "    return [(first + timedelta(days=n)).isoformat() for n in range(count + 1)]\n"),
        note="range(count) gives 0 up to count - 1, which is exactly"
             " the nights: the first is 0 days after check-in and the"
             " last is the day before check-out. The trap's + 1"
             " 'includes the end' and lists the morning of departure"
             " as a night, so a three-night stay is billed for four."
             " A stay is a half-open range, start included and end"
             " not, and range() is half-open the same way.",
    ),
    dict(
        id=5, ledger="P615", concept="PY3 overlap of two ranges", tier="1 - Dates, with datetime",
        title="Do the two stays collide?", kind="function",
        func="collide",
        cases=[("2026-08-04", "2026-08-05", "2026-08-05", "2026-08-09"), ("2026-08-05", "2026-08-09", "2026-08-08", "2026-08-10"),
               ("2026-08-01", "2026-08-10", "2026-08-03", "2026-08-04"), ("2026-08-09", "2026-08-11", "2026-08-05", "2026-08-09"),
               ("2026-08-01", "2026-08-02", "2026-09-01", "2026-09-02"), ("2026-08-01", "2026-08-03", "2026-08-01", "2026-08-03")],
        prompt=(
            "Two stays in the same room, each a check-in and a"
            " check-out as 'YYYY-MM-DD' text. Write a function"
            " `collide(in_a, out_a, in_b, out_b)` that returns True if"
            " they share at least one night. One guest leaving on the"
            " morning the other arrives is NOT a collision. Dates in"
            " this form compare correctly as plain text, so no"
            " conversion is needed.\n\n"
            "  collide(\"2026-08-05\", \"2026-08-09\", \"2026-08-08\", \"2026-08-10\") -> True\n"
            "  collide(\"2026-08-04\", \"2026-08-05\", \"2026-08-05\", \"2026-08-09\") -> False\n\n"
            "Return: a bool."
        ),
        solution=("def collide(in_a, out_a, in_b, out_b):\n"
                  "    return in_a < out_b and in_b < out_a\n"),
        trap=("def collide(in_a, out_a, in_b, out_b):\n"
              "    return in_a <= out_b and in_b <= out_a\n"),
        note="Two ranges overlap when each starts before the other"
             " ends. That one line covers every arrangement -- one"
             " inside the other, either end sticking out, identical --"
             " where listing the cases one by one always misses some."
             " The comparisons are strict because check-out is a"
             " morning: with <=, the trap, a room could never be let"
             " to a new guest on the day the last one leaves. Year"
             " first, zero-padded text sorts in date order.",
    ),
    # ==================================================== 2 Guests and bills
    dict(
        id=6, ledger="P616", concept="PY3 split an amount exactly", tier="2 - Guests and bills",
        title="A bill split so that it adds up", kind="function",
        func="split_bill",
        cases=[(10000, 3), (9000, 3), (100, 1), (5, 4), (0, 2)],
        prompt=(
            "Write a function `split_bill(total_cents, people)` that"
            " returns a list of what each person pays, in whole cents."
            " The shares must add up to the total exactly: everyone"
            " pays the same, except that the first few pay one cent"
            " more when the total does not divide evenly. // and %"
            " give the share and what is left over.\n\n"
            "  split_bill(10000, 3) -> [3334, 3333, 3333]\n\n"
            "Return: a list of int."
        ),
        solution=("def split_bill(total_cents, people):\n"
                  "    share = total_cents // people\n"
                  "    extra = total_cents % people\n"
                  "    return [share + 1 if i < extra else share for i in range(people)]\n"),
        trap=("def split_bill(total_cents, people):\n"
              "    return [total_cents // people] * people\n"),
        note="// throws the remainder away, so three shares of 3333"
             " come to 9999 and a cent has gone missing -- the trap."
             " % says how many cents were left over, and that many"
             " people pay one more: the remainder is always smaller"
             " than the number of people, so nobody pays two extra."
             " Money is kept in whole cents so that this can be exact;"
             " dividing 100.00 by 3 as a decimal never is.",
    ),
    dict(
        id=7, ledger="P617", concept="PY3 two counts returned together", tier="2 - Guests and bills",
        title="Adults and children in the party", kind="function",
        func="party",
        cases=[([34, 36, 8, 5],), ([18],), ([17, 18, 19],), ([],), ([4, 6],)],
        prompt=(
            "Write a function `party(ages)` that takes the ages of the"
            " guests in a booking and returns two numbers: how many"
            " are adults and how many are children. Anyone aged 18 or"
            " over is an adult.\n\n"
            "  party([34, 36, 8, 5]) -> (2, 2)\n"
            "  party([18]) -> (1, 0)\n\n"
            "Return: a tuple of two ints, adults first."
        ),
        solution=("def party(ages):\n"
                  "    adults = sum(age >= 18 for age in ages)\n"
                  "    return adults, len(ages) - adults\n"),
        trap=("def party(ages):\n"
              "    adults = sum(age > 18 for age in ages)\n"
              "    return adults, len(ages) - adults\n"),
        note="'18 or over' is >=, and the difference from > is exactly"
             " one age: the trap turns every eighteen-year-old into a"
             " child. The boundary value is the one to test. Counting"
             " the adults and subtracting from the total guarantees"
             " the two numbers add up to the party, where two separate"
             " counts could disagree. `return a, b` builds a tuple, so"
             " the caller can write adults, children = party(ages).",
    ),
    dict(
        id=8, ledger="P618", concept="PY4 first name plus a count", tier="2 - Guests and bills",
        title="A booking's guests on one line", kind="function",
        func="guest_line",
        cases=[(["Agnes Devlin", "Hugo Devlin", "Mei Devlin"],), (["Agnes Devlin"],), ([],), (["Agnes Devlin", "Hugo Devlin"],)],
        prompt=(
            "The arrivals list has room for one line per booking."
            " Write a function `guest_line(names)` that returns the"
            " first guest's name, followed by ' + ' and the number of"
            " OTHER guests when there are any. A single guest is just"
            " their name; no guests is the empty string.\n\n"
            "  guest_line([\"Agnes Devlin\", \"Hugo Devlin\", \"Mei Devlin\"]) -> \"Agnes Devlin + 2\"\n"
            "  guest_line([\"Agnes Devlin\"]) -> \"Agnes Devlin\"\n\n"
            "Return: a str."
        ),
        solution=("def guest_line(names):\n"
                  "    if not names:\n"
                  "        return \"\"\n"
                  "    if len(names) == 1:\n"
                  "        return names[0]\n"
                  "    return f\"{names[0]} + {len(names) - 1}\"\n"),
        trap=("def guest_line(names):\n"
              "    if not names:\n"
              "        return \"\"\n"
              "    return f\"{names[0]} + {len(names) - 1}\"\n"),
        note="Three cases, each with its own return: nothing, one,"
             " several. The empty list has to be dealt with first,"
             " because names[0] raises on it. The trap forgets the"
             " middle case and prints 'Agnes Devlin + 0', which is"
             " true and looks like a mistake to everyone who reads it."
             " When a label describes a count, zero and one nearly"
             " always need words of their own.",
    ),
    dict(
        id=9, ledger="P619", concept="PY4 shape of an email address", tier="2 - Guests and bills",
        title="Does that look like an email address?", kind="function",
        func="looks_like_email",
        cases=[("agnes.devlin7@example.org",), ("agnes.devlin",), ("@example.org",), ("agnes@example",), ("a@b@example.org",), ("agnes@.org",), ("agnes@example.",), ("",)],
        prompt=(
            "Write a function `looks_like_email(text)` for a first"
            " check on a form. It returns True only if the text has"
            " exactly ONE '@', something before it, and after it a"
            " part that contains a dot which is neither its first nor"
            " its last character.\n\n"
            "  looks_like_email(\"agnes.devlin7@example.org\") -> True\n"
            "  looks_like_email(\"@example.org\") -> False\n"
            "  looks_like_email(\"agnes@example\") -> False\n\n"
            "Return: a bool."
        ),
        solution=("def looks_like_email(text):\n"
                  "    if text.count(\"@\") != 1:\n"
                  "        return False\n"
                  "    name, domain = text.split(\"@\")\n"
                  "    if not name:\n"
                  "        return False\n"
                  "    return \".\" in domain and not domain.startswith(\".\") and not domain.endswith(\".\")\n"),
        trap=("def looks_like_email(text):\n"
              "    return \"@\" in text and \".\" in text\n"),
        note="The trap asks whether the two characters are there at"
             " all, and says yes to '@example.org' and to"
             " 'agnes.devlin@example', where the dot is on the wrong"
             " side. Checking that there is exactly one @ first makes"
             " the split safe to unpack into two names, and each rule"
             " after that is one short test. This is a check of"
             " shape, not of truth: only sending a message shows"
             " whether an address exists.",
    ),
    dict(
        id=10, ledger="P620", concept="PY3 truncate a list with a count", tier="2 - Guests and bills",
        title="A long guest list, cut short", kind="function",
        func="short_list",
        cases=[(["Agnes", "Hugo", "Mei", "Niall", "Pavel"], 3), (["Agnes", "Hugo"], 3), (["Agnes", "Hugo", "Mei"], 3), ([], 2), (["Agnes", "Hugo"], 1)],
        prompt=(
            "Write a function `short_list(names, limit)` that returns"
            " the names unchanged if there are no more than `limit` of"
            " them. If there are more, it returns the first `limit`"
            " names followed by one extra item saying how many were"
            " left off: 'and 2 more'.\n\n"
            "  short_list([\"Agnes\", \"Hugo\", \"Mei\", \"Niall\", \"Pavel\"], 3) -> [\"Agnes\", \"Hugo\", \"Mei\", \"and 2 more\"]\n"
            "  short_list([\"Agnes\", \"Hugo\"], 3) -> [\"Agnes\", \"Hugo\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def short_list(names, limit):\n"
                  "    if len(names) <= limit:\n"
                  "        return list(names)\n"
                  "    return names[:limit] + [f\"and {len(names) - limit} more\"]\n"),
        trap=("def short_list(names, limit):\n"
              "    return names[:limit] + [f\"and {len(names) - limit} more\"]\n"),
        note="The slice is safe on a short list -- names[:3] of two"
             " names is those two -- but the count is not: without"
             " the first test, the trap, a list that fits ends with"
             " 'and 0 more', and one shorter still with 'and -1 more'."
             " Decide first whether anything is being cut. The"
             " comparison is <=, since a list of exactly the limit"
             " fits and needs no footnote.",
    ),
    # ==================================================== 3 Rooms and floors
    dict(
        id=11, ledger="P621", concept="PY3 slice from the end", tier="3 - Rooms and floors",
        title="Which floor is the room on?", kind="function",
        func="floor_of",
        cases=[("204",), ("1204",), ("101",), ("312",), ("1001",)],
        prompt=(
            "A room number is the floor followed by a two-digit room:"
            " '204' is floor 2, room 4, and in a tall hotel '1204' is"
            " floor 12. Write a function `floor_of(room_no)` that"
            " returns the floor as an int. Count from the END of the"
            " string, where the layout is fixed.\n\n"
            "  floor_of(\"204\") -> 2\n"
            "  floor_of(\"1204\") -> 12\n\n"
            "Return: an int."
        ),
        solution=("def floor_of(room_no):\n"
                  "    return int(room_no[:-2])\n"),
        trap=("def floor_of(room_no):\n"
              "    return int(room_no[0])\n"),
        note="The room part is always the last two characters; the"
             " floor is everything in front of them, however long."
             " room_no[:-2] says exactly that: all but the last two."
             " The first character alone, the trap, is right for"
             " every hotel under ten storeys and puts room 1204 on"
             " floor 1. When one end of a string has a fixed width,"
             " measure from that end.",
    ),
    dict(
        id=12, ledger="P622", concept="PY3 next in a list, stopping at the top", tier="3 - Rooms and floors",
        title="An upgrade, if there is one", kind="function",
        func="upgrade",
        cases=[("twin", ["single", "twin", "double", "family", "suite"]), ("suite", ["single", "twin", "double", "family", "suite"]),
               ("single", ["single", "twin", "double", "family", "suite"]), ("family", ["single", "twin", "double", "family", "suite"]), ("a", ["a"])],
        prompt=(
            "Room types run from the plainest to the best in a list."
            " Write a function `upgrade(kind, ladder)` that returns"
            " the type one step up from `kind`. A guest already in the"
            " best type stays where they are. kind is always in the"
            " list.\n\n"
            "  upgrade(\"twin\", [\"single\", \"twin\", \"double\", \"family\", \"suite\"]) -> \"double\"\n"
            "  upgrade(\"suite\", [\"single\", \"twin\", \"double\", \"family\", \"suite\"]) -> \"suite\"\n\n"
            "Return: a str."
        ),
        solution=("def upgrade(kind, ladder):\n"
                  "    position = ladder.index(kind)\n"
                  "    return ladder[min(position + 1, len(ladder) - 1)]\n"),
        trap=("def upgrade(kind, ladder):\n"
              "    position = ladder.index(kind)\n"
              "    return ladder[(position + 1) % len(ladder)]\n"),
        note="min(position + 1, last) moves up one and stops at the"
             " top: the one position that does not exist is replaced"
             " by the last that does. The trap uses the remainder,"
             " which is right for a rota that goes round and wrong"
             " for a ladder -- it 'upgrades' a guest from the suite to"
             " a single. Both are one-line ways of handling the end of"
             " a list; which one depends on whether the end joins up"
             " with the beginning.",
    ),
    dict(
        id=13, ledger="P623", concept="PY3 filter by odd or even", tier="3 - Rooms and floors",
        title="The rooms that face the sea", kind="function",
        func="sea_view",
        cases=[(["201", "202", "203", "210", "215"],), (["312", "104"],), ([],), (["120", "121", "301"],), (["1205", "1206"],)],
        prompt=(
            "At Harbour Lights the odd-numbered rooms face the sea."
            " Write a function `sea_view(rooms)` that takes room"
            " numbers as strings and returns the odd-numbered ones, in"
            " order, still as strings. A whole number is odd when the"
            " remainder on dividing by 2 is 1.\n\n"
            "  sea_view([\"201\", \"202\", \"203\", \"210\", \"215\"]) -> [\"201\", \"203\", \"215\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def sea_view(rooms):\n"
                  "    return [room for room in rooms if int(room) % 2 == 1]\n"),
        trap=("def sea_view(rooms):\n"
              "    return [room for room in rooms if int(room[0]) % 2 == 1]\n"),
        note="The test needs a number, so int(room) is used inside the"
             " condition, while the list is built from `room`, the"
             " original string: convert to decide, keep what you were"
             " given. The trap tests the first digit, which is the"
             " floor, and returns every room on floors 1 and 3."
             " Whether a number is odd depends only on its last digit;"
             " int(room) % 2 looks at the whole number and cannot get"
             " that wrong.",
    ),
    dict(
        id=14, ledger="P624", concept="PY3 flatten a list of lists", tier="3 - Rooms and floors",
        title="Every room on every floor", kind="function",
        func="all_rooms",
        cases=[([["101", "102"], ["201"], ["301", "302", "303"]],), ([[], ["201"]],), ([],), ([["101"]],)],
        prompt=(
            "The housekeeping sheet lists rooms floor by floor: a list"
            " of lists. Write a function `all_rooms(floors)` that"
            " returns every room number in ONE flat list, in the same"
            " order. A list has two ways of adding to itself, and they"
            " differ on exactly this.\n\n"
            "  all_rooms([[\"101\", \"102\"], [\"201\"], [\"301\", \"302\", \"303\"]]) -> [\"101\", \"102\", \"201\", \"301\", \"302\", \"303\"]\n\n"
            "Return: a list of str."
        ),
        solution=("def all_rooms(floors):\n"
                  "    rooms = []\n"
                  "    for floor in floors:\n"
                  "        rooms.extend(floor)\n"
                  "    return rooms\n"),
        trap=("def all_rooms(floors):\n"
              "    rooms = []\n"
              "    for floor in floors:\n"
              "        rooms.append(floor)\n"
              "    return rooms\n"),
        note="append adds ONE item to the end, whatever it is; given a"
             " list, it adds that list as a single item, and the trap"
             " hands back the same list of lists it started with."
             " extend adds each item of what it is given, which is the"
             " flattening. rooms += floor is extend spelled another"
             " way, and [room for floor in floors for room in floor]"
             " does it in one line, reading the two fors in the order"
             " you would nest them.",
    ),
    dict(
        id=15, ledger="P625", concept="PY3 swap two positions on a copy", tier="3 - Rooms and floors",
        title="Two guests swap rooms", kind="function",
        func="swap_guests",
        cases=[(["Agnes", "Hugo", "Mei", "Niall"], 0, 2), (["Agnes", "Hugo"], 0, 1), (["Agnes", "Hugo", "Mei"], 1, 1), (["Agnes", "Hugo", "Mei"], 2, 0)],
        prompt=(
            "A list holds the guest in each room, room by room. Write"
            " a function `swap_guests(guests, i, j)` that returns a"
            " NEW list in which the guests at positions i and j have"
            " changed places. The list passed in is not altered."
            " Python can assign to two things at once.\n\n"
            "  swap_guests([\"Agnes\", \"Hugo\", \"Mei\", \"Niall\"], 0, 2) -> [\"Mei\", \"Hugo\", \"Agnes\", \"Niall\"]\n\n"
            "Return: a list."
        ),
        solution=("def swap_guests(guests, i, j):\n"
                  "    out = list(guests)\n"
                  "    out[i], out[j] = out[j], out[i]\n"
                  "    return out\n"),
        trap=("def swap_guests(guests, i, j):\n"
              "    out = list(guests)\n"
              "    out[i] = out[j]\n"
              "    out[j] = out[i]\n"
              "    return out\n"),
        note="Two assignments one after the other, the trap, lose a"
             " guest: once out[i] has been overwritten, its old value"
             " is gone, and the second line copies the new one back --"
             " Mei is in both rooms and Agnes in neither. The paired"
             " assignment reads both right-hand values BEFORE storing"
             " either, so nothing is lost. It is the same problem as"
             " swapping two rows' values in SQL, and Python's answer"
             " needs no third place to stand.",
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
