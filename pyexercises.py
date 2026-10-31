"""Python practice exercises: fifteen functions over one list of bikes.

The twenty-seventh Python set, and the first in which every question works
the SAME data: BIKES, a list of seven dicts shaped like the scheme's bikes
table with a few things bolted on -- a ride count, kilometres ridden and
the stations the bike has reached, in the order it first reached them.
One bike has never been ridden, one has retired, two tie on rides. The
questions ramp from a single line (a comprehension, a sum, a guard) through
one loop each (a union, an intersection, a count that breaks ties) to two
steps (aggregate per model, then pick; bucket, then count).

Every question is a `kind="function"`: the editor defines a function named
`func`. Run calls it once per case in `cases` and shows each call and its
result; Check compares each result with the reference function's. Values
are compared, not their printed form -- a dict in another order is the same
dict -- but the container type counts, so a tuple is not a list, 2024 is
not "2024", and 0 is not False.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py).
"""

import pyrun

BIKES = [{"bike_id": 1, "model": "classic", "acquired": "2024-09-22", "retired": None, "rides": 140, "km": 412.5, "stations": [1, 3, 5, 7]},
         {"bike_id": 2, "model": "classic", "acquired": "2022-10-31", "retired": "2023-07-27", "rides": 61, "km": 150.2, "stations": [3, 5]},
         {"bike_id": 3, "model": "electric", "acquired": "2022-02-04", "retired": None, "rides": 388, "km": 1480.9, "stations": [1, 2, 3, 5, 9]},
         {"bike_id": 4, "model": "cargo", "acquired": "2025-03-15", "retired": None, "rides": 44, "km": 96.0, "stations": [5, 9]},
         {"bike_id": 5, "model": "electric", "acquired": "2023-06-30", "retired": "2026-01-10", "rides": 275, "km": 1012.4, "stations": [9, 7, 5, 2]},
         {"bike_id": 6, "model": "cargo", "acquired": "2025-11-02", "retired": None, "rides": 0, "km": 0.0, "stations": []},
         {"bike_id": 7, "model": "classic", "acquired": "2023-01-19", "retired": None, "rides": 140, "km": 530.0, "stations": [1, 5, 7, 11]}]

EXERCISES = [
    # ============================================================= 1 One line
    dict(
        id=1, ledger="P401", concept="PY5 filter by argument", tier="1 - One line",
        title="The bikes of one model", kind="function",
        func="ids_by_model",
        cases=[(BIKES, "classic"), (BIKES, "cargo"), (BIKES, "tandem"), ([], "classic")],
        prompt=(
            "BIKES is a list of dicts, one per bike, with keys bike_id,"
            " model, acquired, retired (None while the bike is in the"
            " fleet), rides, km and stations (the station ids the bike"
            " has reached, in the order it first reached them). Write a"
            " function `ids_by_model(bikes, model)` that returns the"
            " bike_ids of the bikes of that model, in list order. One"
            " list comprehension with an if.\n\n"
            "  ids_by_model(BIKES, \"classic\") -> [1, 2, 7]\n\n"
            "Return: a list of ints, possibly empty."
        ),
        solution=("def ids_by_model(bikes, model):\n"
                  "    return [b[\"bike_id\"] for b in bikes if b[\"model\"] == model]\n"),
        trap=("def ids_by_model(bikes, model):\n"
              "    return [b for b in bikes if b[\"model\"] == model]\n"),
        note="The comprehension's first part is what goes INTO the list,"
             " and the question asks for ids, not bikes: the trap returns"
             " the whole dicts. A model nobody has, or an empty list,"
             " gives [] without any special handling, which is the point"
             " of a comprehension over a loop with appends.",
    ),
    dict(
        id=2, ledger="P402", concept="PY5 sum of a field", tier="1 - One line",
        title="How far the fleet has gone", kind="function",
        func="fleet_km",
        cases=[(BIKES,), (BIKES[:3],), ([BIKES[5]],), ([],)],
        prompt=(
            "Write a function `fleet_km(bikes)` that returns the"
            " kilometres every bike has ridden, added up and rounded to"
            " one decimal -- retired bikes included, since their"
            " kilometres were ridden. sum() over a generator, inside"
            " round().\n\n"
            "  fleet_km(BIKES) -> 3682.0\n\n"
            "Return: a float."
        ),
        solution=("def fleet_km(bikes):\n"
                  "    return round(sum(b[\"km\"] for b in bikes), 1)\n"),
        trap=("def fleet_km(bikes):\n"
              "    return round(sum(b[\"km\"] for b in bikes if b[\"retired\"] is None), 1)\n"),
        note="A total of what has been ridden counts every bike that"
             " rode; filtering out the retired ones answers a different"
             " question (how far the CURRENT fleet has gone) and drops"
             " 1,162.6 km. sum() of nothing is 0, and round(0, 1) is 0 --"
             " an int, which the grader treats as equal to 0.0 here"
             " because the reference does the same.",
    ),
    dict(
        id=3, ledger="P403", concept="PY5 None guard in a condition", tier="1 - One line",
        title="How many bikes were in the fleet that day", kind="function",
        func="in_service_on",
        cases=[(BIKES, "2026-06-30"), (BIKES, "2023-03-01"), (BIKES, "2025-10-01"), (BIKES, "2021-01-01")],
        prompt=(
            "Write a function `in_service_on(bikes, day)` that returns"
            " how many bikes were in the fleet on that day: acquired on"
            " or before it, and either not retired or retired after it."
            " Dates are ISO strings, so < and <= compare them correctly."
            " One sum() of a generator with the two conditions; the"
            " retired test has to check for None FIRST, because None <"
            " \"2026\" is a TypeError.\n\n"
            "  in_service_on(BIKES, \"2026-06-30\") -> 5\n\n"
            "Return: an int."
        ),
        solution=("def in_service_on(bikes, day):\n"
                  "    return sum(1 for b in bikes\n"
                  "               if b[\"acquired\"] <= day and (b[\"retired\"] is None or b[\"retired\"] > day))\n"),
        trap=("def in_service_on(bikes, day):\n"
              "    return sum(1 for b in bikes if b[\"acquired\"] <= day and b[\"retired\"] > day)\n"),
        note="Python 3 refuses to compare None with a string, so the"
             " trap raises TypeError on the first bike still in service."
             " `is None or ...` short-circuits: when retired is None the"
             " comparison after the `or` is never evaluated. ISO dates"
             " sort as strings because the biggest unit comes first,"
             " which is why no date parsing is needed.",
    ),
    dict(
        id=4, ledger="P404", concept="PY5 guarded division", tier="1 - One line",
        title="Kilometres per ride", kind="function",
        func="km_per_ride",
        cases=[(BIKES[0],), (BIKES[2],), (BIKES[5],), (BIKES[3],)],
        prompt=(
            "Write a function `km_per_ride(bike)` that returns one bike's"
            " kilometres divided by its rides, rounded to two decimals --"
            " or None for a bike with no rides. A conditional expression:"
            " round(...) if bike[\"rides\"] else None.\n\n"
            "  km_per_ride(BIKES[0]) -> 2.95\n\n"
            "Return: a float, or None."
        ),
        solution=("def km_per_ride(bike):\n"
                  "    return round(bike[\"km\"] / bike[\"rides\"], 2) if bike[\"rides\"] else None\n"),
        trap=("def km_per_ride(bike):\n"
              "    return round(bike[\"km\"] / bike[\"rides\"], 2)\n"),
        note="Bike 6 has never been ridden, and 0.0 / 0 is a"
             " ZeroDivisionError, not 0. The guard goes before the"
             " division, and `if bike[\"rides\"]` is enough because 0 is"
             " the only falsy count. None says 'no figure'; returning 0"
             " would claim the bike covers no distance per ride, which is"
             " a different and wrong thing.",
    ),
    dict(
        id=5, ledger="P405", concept="PY5 all()", tier="1 - One line",
        title="Has every bike been there?", kind="function",
        func="all_visited",
        cases=[(BIKES, 5), ([BIKES[0], BIKES[2]], 1), ([BIKES[0], BIKES[2]], 7), ([], 5)],
        prompt=(
            "Write a function `all_visited(bikes, station)` that returns"
            " True when EVERY bike in the list has reached that station"
            " -- `station in b[\"stations\"]` for all of them -- and"
            " False otherwise. all() over a generator; all() of nothing"
            " is True.\n\n"
            "  all_visited(BIKES, 5) -> False\n\n"
            "Return: True or False."
        ),
        solution=("def all_visited(bikes, station):\n"
                  "    return all(station in b[\"stations\"] for b in bikes)\n"),
        trap=("def all_visited(bikes, station):\n"
              "    return any(station in b[\"stations\"] for b in bikes)\n"),
        note="any() is 'at least one', all() is 'every one', and they"
             " disagree on the full list -- six bikes have reached"
             " station 5 but bike 6 has reached nowhere -- and on an"
             " empty list, where all() is True (nothing fails the test)"
             " and any() is False (nothing passes it). Both stop as soon"
             " as the answer is known.",
    ),
    # ============================================================= 2 One loop
    dict(
        id=6, ledger="P406", concept="PY4 for set union", tier="2 - One loop",
        title="Every station anyone has reached", kind="function",
        func="all_stations",
        cases=[(BIKES,), (BIKES[:2],), ([BIKES[5]],), ([BIKES[3], BIKES[4]],)],
        prompt=(
            "Write a function `all_stations(bikes)` that returns every"
            " station id any of the bikes has reached, each once, in"
            " ascending order. A loop that update()s a set with each"
            " bike's stations, then sorted().\n\n"
            "  all_stations(BIKES) -> [1, 2, 3, 5, 7, 9, 11]\n\n"
            "Return: a sorted list of ints."
        ),
        solution=("def all_stations(bikes):\n"
                  "    seen = set()\n"
                  "    for b in bikes:\n"
                  "        seen.update(b[\"stations\"])\n"
                  "    return sorted(seen)\n"),
        trap=("def all_stations(bikes):\n"
              "    seen = []\n"
              "    for b in bikes:\n"
              "        seen.extend(b[\"stations\"])\n"
              "    return sorted(seen)\n"),
        note="A list keeps every copy, so the trap returns station 5 six"
             " times. A set keeps one of each, update() adds a whole"
             " iterable at once, and sorted() turns it back into the"
             " ordered list the question wants -- a set has no order,"
             " and the grader would reject one.",
    ),
    dict(
        id=7, ledger="P407", concept="PY4 for set intersection", tier="2 - One loop",
        title="The stations every bike has reached", kind="function",
        func="common_stations",
        cases=[([BIKES[0], BIKES[2], BIKES[4]],), ([BIKES[0], BIKES[5]],), ([BIKES[2]],), ([],)],
        prompt=(
            "Write a function `common_stations(bikes)` that returns the"
            " station ids EVERY bike in the list has reached, in"
            " ascending order, and [] for an empty list. Start from the"
            " first bike's stations as a set and intersect"
            " (`&=` or intersection_update) with each of the others.\n\n"
            "  common_stations([BIKES[0], BIKES[2], BIKES[4]]) -> [5]\n\n"
            "Return: a sorted list of ints."
        ),
        solution=("def common_stations(bikes):\n"
                  "    if not bikes:\n"
                  "        return []\n"
                  "    common = set(bikes[0][\"stations\"])\n"
                  "    for b in bikes[1:]:\n"
                  "        common &= set(b[\"stations\"])\n"
                  "    return sorted(common)\n"),
        trap=("def common_stations(bikes):\n"
              "    common = set()\n"
              "    for b in bikes:\n"
              "        common &= set(b[\"stations\"])\n"
              "    return sorted(common)\n"),
        note="An intersection has to START from something full: begun"
             " from the empty set it stays empty whatever is intersected"
             " into it, so the trap answers [] for every list. The"
             " empty-list guard is what makes bikes[0] safe to read. A"
             " union starts from the empty set for the mirror-image"
             " reason.",
    ),
    dict(
        id=8, ledger="P408", concept="PY4 for count then min of max", tier="2 - One loop",
        title="The station most bikes have reached", kind="function",
        func="busiest_station",
        cases=[(BIKES,), ([BIKES[4], BIKES[0]],), ([BIKES[5]],), ([BIKES[1], BIKES[3]],)],
        prompt=(
            "Write a function `busiest_station(bikes)` that returns the"
            " station id that appears in the most bikes' station lists,"
            " the SMALLEST id when several tie, or None when no bike has"
            " reached anywhere. A loop counting each station into a"
            " dict, then the best: the highest count, and among those"
            " the lowest id.\n\n"
            "  busiest_station(BIKES) -> 5\n\n"
            "Return: an int, or None."
        ),
        solution=("def busiest_station(bikes):\n"
                  "    counts = {}\n"
                  "    for b in bikes:\n"
                  "        for s in b[\"stations\"]:\n"
                  "            counts[s] = counts.get(s, 0) + 1\n"
                  "    if not counts:\n"
                  "        return None\n"
                  "    top = max(counts.values())\n"
                  "    return min(s for s in counts if counts[s] == top)\n"),
        trap=("def busiest_station(bikes):\n"
              "    counts = {}\n"
              "    for b in bikes:\n"
              "        for s in b[\"stations\"]:\n"
              "            counts[s] = counts.get(s, 0) + 1\n"
              "    if not counts:\n"
              "        return None\n"
              "    return max(counts, key=counts.get)\n"),
        note="max(counts, key=counts.get) breaks a tie by whichever key"
             " was inserted first, which depends on the order the bikes"
             " are listed in: bikes 5 and 1 together put stations 7 and 5"
             " on two each, and the trap answers 7 because bike 5's list"
             " starts with 9, 7. 'Smallest id among the best' is two"
             " steps -- find the top count, then min() of the keys that"
             " have it -- or one sorted() with a (-count, id) key.",
    ),
    dict(
        id=9, ledger="P409", concept="PY4 for date span with fallback", tier="2 - One loop",
        title="The bike that has served longest", kind="function",
        func="longest_lived",
        cases=[(BIKES, "2026-06-30"), ([BIKES[1], BIKES[3]], "2026-06-30"), ([BIKES[0], BIKES[4]], "2026-06-30"), ([], "2026-06-30")],
        prompt=(
            "Write a function `longest_lived(bikes, today)` that returns"
            " the bike_id of the bike with the most days between its"
            " acquisition and its retirement -- or `today` if it has"
            " not retired -- and None for an empty list. Write `from"
            " datetime import date` and use date.fromisoformat() on both"
            " strings; subtracting two dates gives a timedelta whose"
            " .days is the span. A loop keeping the best so far.\n\n"
            "  longest_lived(BIKES, \"2026-06-30\") -> 3\n\n"
            "Return: an int, or None."
        ),
        solution=("from datetime import date\n\n"
                  "def longest_lived(bikes, today):\n"
                  "    best, best_days = None, -1\n"
                  "    for b in bikes:\n"
                  "        end = b[\"retired\"] or today\n"
                  "        days = (date.fromisoformat(end) - date.fromisoformat(b[\"acquired\"])).days\n"
                  "        if days > best_days:\n"
                  "            best, best_days = b[\"bike_id\"], days\n"
                  "    return best\n"),
        trap=("def longest_lived(bikes, today):\n"
              "    best, best_date = None, today\n"
              "    for b in bikes:\n"
              "        if b[\"acquired\"] < best_date:\n"
              "            best, best_date = b[\"bike_id\"], b[\"acquired\"]\n"
              "    return best\n"),
        note="Longest-serving is not oldest: bike 2 was acquired before"
             " bike 4 but retired after nine months, and bike 4 has been"
             " out for fifteen, so the trap, which only looks at"
             " acquisition dates, picks 2. `b[\"retired\"] or today` is"
             " the fallback in one expression, because None is falsy and"
             " a date string is not.",
    ),
    dict(
        id=10, ledger="P410", concept="PY4 for count by derived key", tier="2 - One loop",
        title="How many bikes arrived each year", kind="function",
        func="acquired_by_year",
        cases=[(BIKES,), (BIKES[:2],), ([],), ([BIKES[3], BIKES[5]],)],
        prompt=(
            "Write a function `acquired_by_year(bikes)` that returns a"
            " dict mapping each year, as an INT, to how many bikes were"
            " acquired in it. The year is the first four characters of"
            " the acquired string, so int(b[\"acquired\"][:4]) is the"
            " key; a loop with get(key, 0) + 1.\n\n"
            "  acquired_by_year(BIKES) -> {2022: 2, 2023: 2, 2024: 1, 2025: 2}\n\n"
            "Return: a dict of int to int."
        ),
        solution=("def acquired_by_year(bikes):\n"
                  "    years = {}\n"
                  "    for b in bikes:\n"
                  "        y = int(b[\"acquired\"][:4])\n"
                  "        years[y] = years.get(y, 0) + 1\n"
                  "    return years\n"),
        trap=("def acquired_by_year(bikes):\n"
              "    years = {}\n"
              "    for b in bikes:\n"
              "        y = b[\"acquired\"][:4]\n"
              "        years[y] = years.get(y, 0) + 1\n"
              "    return years\n"),
        note="A slice of a string is a string: \"2024\" is a different"
             " dict key from 2024, so {\"2024\": 1} is not {2024: 1}, and"
             " the grader keeps the types apart. The key is derived from"
             " the row, not read from it -- a grouping column that does"
             " not exist until you compute it, like strftime('%Y') in"
             " SQL.",
    ),
    # ============================================================ 3 Two steps
    dict(
        id=11, ledger="P411", concept="PY5 accumulate two values", tier="3 - Two steps",
        title="Bikes and kilometres per model", kind="function",
        func="model_summary",
        cases=[(BIKES,), (BIKES[:2],), ([],), ([BIKES[2], BIKES[4], BIKES[5]],)],
        prompt=(
            "Write a function `model_summary(bikes)` that returns a dict"
            " mapping each model to a two-item LIST: how many bikes of"
            " that model there are and their kilometres added up, the"
            " km rounded to one decimal at the end. A loop that creates"
            " [0, 0.0] for a model the first time it is seen and then"
            " adds to both items; a second pass rounds the km.\n\n"
            "  model_summary(BIKES) -> {\"classic\": [3, 1092.7], \"electric\": [2, 2493.3], \"cargo\": [2, 96.0]}\n\n"
            "Return: a dict of str to [int, float]."
        ),
        solution=("def model_summary(bikes):\n"
                  "    out = {}\n"
                  "    for b in bikes:\n"
                  "        if b[\"model\"] not in out:\n"
                  "            out[b[\"model\"]] = [0, 0.0]\n"
                  "        out[b[\"model\"]][0] += 1\n"
                  "        out[b[\"model\"]][1] += b[\"km\"]\n"
                  "    for m in out:\n"
                  "        out[m][1] = round(out[m][1], 1)\n"
                  "    return out\n"),
        trap=("def model_summary(bikes):\n"
              "    out = {}\n"
              "    for b in bikes:\n"
              "        out[b[\"model\"]] = [1, round(b[\"km\"], 1)]\n"
              "    return out\n"),
        note="Assigning a fresh [1, km] on every row overwrites the"
             " previous one, so the trap reports the LAST bike of each"
             " model rather than the sum. Two running values per key"
             " need a container that can be updated in place, which a"
             " list is and a tuple is not: out[m][0] += 1 would fail on"
             " a tuple. Rounding goes at the end, once per model, not on"
             " each addition.",
    ),
    dict(
        id=12, ledger="P412", concept="PY5 sort by two keys and slice", tier="3 - Two steps",
        title="The most-ridden bikes", kind="function",
        func="top_n",
        cases=[(BIKES, 3), ([BIKES[6], BIKES[0]], 2), (BIKES, 1), (BIKES, 0)],
        prompt=(
            "Write a function `top_n(bikes, n)` that returns the bike_ids"
            " of the n most-ridden bikes, most rides first, a tie going"
            " to the LOWER bike_id. sorted() with key=lambda b:"
            " (-b[\"rides\"], b[\"bike_id\"]), then take the first n and"
            " keep only the ids.\n\n"
            "  top_n(BIKES, 3) -> [3, 5, 1]\n\n"
            "Return: a list of ints, possibly empty."
        ),
        solution=("def top_n(bikes, n):\n"
                  "    ranked = sorted(bikes, key=lambda b: (-b[\"rides\"], b[\"bike_id\"]))\n"
                  "    return [b[\"bike_id\"] for b in ranked[:n]]\n"),
        trap=("def top_n(bikes, n):\n"
              "    ranked = sorted(bikes, key=lambda b: b[\"rides\"], reverse=True)\n"
              "    return [b[\"bike_id\"] for b in ranked[:n]]\n"),
        note="reverse=True keeps equal keys in their ORIGINAL order, so a"
             " tie is decided by how the list happened to be arranged:"
             " bikes 7 and 1 both have 140 rides, and listed 7 first the"
             " trap returns [7, 1]. Negating the count in a tuple key"
             " sorts rides descending and id ascending in one go, with"
             " no reverse at all. [:n] on a short list just gives the"
             " whole list, and [:0] gives [].",
    ),
    dict(
        id=13, ledger="P413", concept="PY5 count and count-if per key", tier="3 - Two steps",
        title="What share of each model has retired", kind="function",
        func="retired_share",
        cases=[(BIKES,), ([BIKES[1], BIKES[4]],), ([BIKES[3], BIKES[5]],), ([],)],
        prompt=(
            "Write a function `retired_share(bikes)` that returns a dict"
            " mapping each model to the percentage of its bikes that"
            " have retired, to one decimal. Two counts per model -- all"
            " bikes, retired bikes -- then a second pass dividing: 100 *"
            " retired / total, rounded to 1.\n\n"
            "  retired_share(BIKES) -> {\"classic\": 33.3, \"electric\": 50.0, \"cargo\": 0.0}\n\n"
            "Return: a dict of str to float."
        ),
        solution=("def retired_share(bikes):\n"
                  "    total, gone = {}, {}\n"
                  "    for b in bikes:\n"
                  "        m = b[\"model\"]\n"
                  "        total[m] = total.get(m, 0) + 1\n"
                  "        gone[m] = gone.get(m, 0) + (b[\"retired\"] is not None)\n"
                  "    return {m: round(100 * gone[m] / total[m], 1) for m in total}\n"),
        trap=("def retired_share(bikes):\n"
              "    total, gone = {}, {}\n"
              "    for b in bikes:\n"
              "        m = b[\"model\"]\n"
              "        total[m] = total.get(m, 0) + 1\n"
              "        gone[m] = gone.get(m, 0) + (b[\"retired\"] is not None)\n"
              "    return {m: round(100 * gone[m] / total[m]) for m in total}\n"),
        note="round(x) with no second argument returns an int -- 33, and"
             " 50 rather than 50.0 -- and the grader keeps ints and"
             " floats apart; round(x, 1) returns a float even when the"
             " decimal is 0. Adding a boolean to a count works because"
             " True is 1, which is the FILTER-on-an-aggregate idea in"
             " Python. Every model is in `total`, so no model gets a"
             " division by zero.",
    ),
    dict(
        id=14, ledger="P414", concept="PY5 bucket then count", tier="3 - Two steps",
        title="Rides in bands of a hundred", kind="function",
        func="rides_histogram",
        cases=[(BIKES, 100), (BIKES, 50), (BIKES[:3], 200), ([], 100)],
        prompt=(
            "Write a function `rides_histogram(bikes, width)` that"
            " returns a dict mapping the START of each band of that"
            " width to how many bikes fall in it: a bike with 140 rides"
            " is in band 100 when the width is 100 (140 // 100 * 100)"
            " and in band 100 when it is 50 too; a bike with 0 rides is"
            " in band 0. A loop with get(band, 0) + 1; bands no bike"
            " falls in are absent.\n\n"
            "  rides_histogram(BIKES, 100) -> {100: 2, 0: 3, 300: 1, 200: 1}\n\n"
            "Return: a dict of int to int."
        ),
        solution=("def rides_histogram(bikes, width):\n"
                  "    bands = {}\n"
                  "    for b in bikes:\n"
                  "        band = b[\"rides\"] // width * width\n"
                  "        bands[band] = bands.get(band, 0) + 1\n"
                  "    return bands\n"),
        trap=("def rides_histogram(bikes, width):\n"
              "    bands = {}\n"
              "    for b in bikes:\n"
              "        band = b[\"rides\"] // width\n"
              "        bands[band] = bands.get(band, 0) + 1\n"
              "    return bands\n"),
        note="rides // width is the band's NUMBER (1 for 140 at width"
             " 100); multiplying back by the width gives its start (100),"
             " which is what the question asks for -- the trap's keys"
             " are 0, 1, 2, 3. Bucketing is a derived key like the year"
             " in question 10, and the same get(key, 0) + 1 counts into"
             " it.",
    ),
    dict(
        id=15, ledger="P415", concept="PY5 aggregate then argmax", tier="3 - Two steps",
        title="The model that goes furthest per bike", kind="function",
        func="best_model",
        cases=[(BIKES,), ([BIKES[0], BIKES[1], BIKES[6], BIKES[4]],), ([BIKES[3]],), ([],)],
        prompt=(
            "Write a function `best_model(bikes)` that returns the model"
            " with the highest AVERAGE kilometres per bike -- the model's"
            " km added up, divided by how many bikes it has -- or None"
            " for an empty list. First a loop accumulating km and count"
            " per model, then max() over the models with a key that"
            " divides the two.\n\n"
            "  best_model(BIKES) -> \"electric\"\n\n"
            "Return: a str, or None."
        ),
        solution=("def best_model(bikes):\n"
                  "    km, n = {}, {}\n"
                  "    for b in bikes:\n"
                  "        m = b[\"model\"]\n"
                  "        km[m] = km.get(m, 0.0) + b[\"km\"]\n"
                  "        n[m] = n.get(m, 0) + 1\n"
                  "    if not km:\n"
                  "        return None\n"
                  "    return max(km, key=lambda m: km[m] / n[m])\n"),
        trap=("def best_model(bikes):\n"
              "    km = {}\n"
              "    for b in bikes:\n"
              "        km[b[\"model\"]] = km.get(b[\"model\"], 0.0) + b[\"km\"]\n"
              "    if not km:\n"
              "        return None\n"
              "    return max(km, key=km.get)\n"),
        note="Total and average pick different winners when the groups"
             " are different sizes: three classics together have 1,092.7"
             " km against one electric bike's 1,012.4, so by total the"
             " trap says classic, but per bike the electric wins three"
             " to one. The average needs the count as well as the sum,"
             " which is why there are two dicts -- or one dict of"
             " [sum, count] pairs, as in question 11.",
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
