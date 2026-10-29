# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
third set on it, at two tools per question with the tiers named by task,
reaching the tools the first two bike sets did not, and three writable
questions that each take two steps. **Fifteen Python** in three shapes:
five functions that are one tool each, on tools no earlier set used; five
built around one simple loop; and five over lists of maintenance-job dicts
shaped like the scheme's rows, with a kind, a cost and a fixed flag.

| Stage | SQL questions |
|---|---|
| 1 - The fleet in motion | 1-3 |
| 2 - The calendar | 4-6 |
| 3 - Members | 7-9 |
| 4 - Money | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - One tool | 1-5 |
| 2 - A simple loop | 6-10 |
| 3 - Job rows | 11-15 |

## The schema

Six tables. `stations` are the docks, each in a `zone` with so many docks,
opened on a date and perhaps closed. `bikes` are the fleet: a `model`, an
acquisition date, perhaps retired. `members` have a `plan` -- annual,
monthly or pay-as-you-go -- and a home station. `rides` is the centre: a
bike, a member OR NULL for a casual rider, a start station, an end station
that is NULL while the ride is out, `started_at` and `ended_at`
timestamps, metres ridden, and a `fare_cents` that is 0 for a member's
ride inside the free half hour. `maintenance` jobs take a bike off the
road from `reported_at` until `fixed_at`, which is NULL while the job is
open. `payments` are money in: a fare names its ride, a subscription names
its member, never both. Double-click a table in the left pane to see its
columns.

**Dates and times are text**: 'YYYY-MM-DD' for dates, 'YYYY-MM-DD HH:MM'
for timestamps. They compare correctly as text; `julianday()` turns either
into a number of days you can subtract -- multiply by 1440 for minutes --
and `date()` cuts a timestamp to its day.

**The data ends at 2026-06-30 23:59.** Anything that would have ended after
that is open instead -- 35 rides have no end, 11 of them by
casual riders; 114 maintenance jobs are unfixed -- and every
question that measures an open interval says which end to supply.

## The writable stage

SQLite has no stored procedures, variables, loops or TRY/CATCH. What it has
instead is constraints, triggers, views, DDL and plain DML -- and each of
questions 13 to 15 is one of those.

**How they run.** Press Run and your script executes, statement by statement,
in a private in-memory copy of the database. Nothing you write can reach the
real file. The copy **persists across Runs of the same question** -- so you can
run an `UPDATE`, then a `SELECT`, and see what it did -- and **Reset** throws it
away and starts again from the seeded data. Moving to another question also
starts fresh, so no question depends on what another one wrote. If your
script ends in a statement that returns rows, the results pane shows that;
otherwise it shows the question's *probe* query, which is what **Check answer**
compares. Check always grades a fresh copy, so nothing you ran earlier can
affect the grade.

**Driver statements.** Question 13 runs two UPDATEs of its own *after* your
script, retiring bike 3, which is docked, and bike 8, which is out on a
ride. The probe reads both bikes, so both outcomes show. Questions 14 and 15
are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE TRIGGER ... BEFORE UPDATE OF retired_on ON bikes WHEN NEW.retired_on IS NOT NULL AND EXISTS (SELECT 1 FROM rides WHERE bike_id = OLD.bike_id AND ended_at IS NULL) BEGIN SELECT RAISE(ABORT, ...); END` |
| 14 | `ALTER TABLE bikes ADD COLUMN rides INTEGER NOT NULL DEFAULT 0; UPDATE bikes SET rides = (SELECT COUNT(*) FROM rides r WHERE r.bike_id = bikes.bike_id)` |
| 15 | `INSERT INTO bikes (...) VALUES (1, ...), (321, ...) ON CONFLICT (bike_id) DO UPDATE SET retired_on = excluded.retired_on` |

## Things the data does on purpose

- **100 of the 900 members have never ridden**, and 86 have no
  district recorded. 81 of the never-riders are on a subscription
  and have paid for it, which is question 12; the other never-riders are
  pay-as-you-go and have paid nothing.
- **7 of the 320 bikes have never been ridden and 18 are
  retired**; question 14's new column must show the seven at 0, and
  questions 13 and 15 retire bikes 3 and 1, both in service. Bike 8 is
  one of the 35 out on a ride, which is what question 13 protects.
- **59 of the 82 electric bikes have never had a battery job**,
  and no other model ever has one -- which is why question 3's EXCEPT,
  written backwards, returns nothing.
- **Members start only 8 per cent of their rides at their home station**,
  and 104 riders have never once done so: question 7, if its
  EXISTS is in place.
- **Old Mill closed on 2026-03-01** and its last ride is in February;
  question 4's spine has to make the four months after it appear at 0.
- **Fares come in multiples of 50**, so a pay-as-you-go month of exactly
  1200 cents is common: 225 member-months are over the monthly
  fee and 13 more sit exactly on it, which is the difference
  between > and >= in question 10.
- **67 per cent of members' payments are by app**, in every zone
  alike; question 11's shares are a window over the grouped counts, and
  the casual riders' 30 per cent of rides pay with no member
  attached, so they never reach it.
- **The busiest route carries 417 rides**, Market Square to Station
  Approach; bikes pile up at Station Approach and drain from Market Square.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Questions 1 to 5 are one tool each; where the tool
needs an import, the question says the line to write. Questions 6 to 15 are
one simple loop each, the last five over lists of maintenance-job dicts:
the prompt shows a list called JOBS as its example, and Run passes your
function that list and a few shorter ones.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - The fleet in motion (3)

Speed from an integer distance and a julianday interval, where / 1000 and /
1000.0 give different answers; FIRST_VALUE, whose ORDER BY decides whether
'first' is longest or shortest; and EXCEPT, which is not symmetric.

1. **How fast each model goes** (Q1102)

   For each bike model: completed rides, and the average speed in km/h to one
   decimal -- distance_m / 1000.0 over the hours from julianday, averaged per
   ride. A join to bikes for the model; every completed ride has a distance.

   *Return: model, rides, avg_kmh*

2. **The longest ride out of each station** (Q1103)

   For each start station, the ride_id and distance of the LONGEST ride that
   started there. FIRST_VALUE over a window partitioned by the start station
   and ordered by distance descending, with DISTINCT to keep one row per
   station. No station has a tie at the top.

   *Return: station_id, ride_id, distance_m*

3. **Electric bikes that have never needed a battery** (Q1104)

   The electric bikes with no 'battery' maintenance job on record, ever: the
   electric bike_ids EXCEPT the bike_ids of battery jobs.

   *Return: bike_id*

## 2 - The calendar (3)

A recursive month spine LEFT JOINed to a closed station's rides, with the
station test in the ON clause; LAG against LEAD for month on month; and a simple
CASE on strftime's TEXT, where an unquoted 0 matches nothing.

4. **Old Mill, month by month, to the end** (Q1105)

   Rides started at Old Mill (station 10) in EVERY month from 2025-01 to
   2026-06, including the months after it closed, as 0. A recursive CTE that
   builds the eighteen months -- strftime('%Y-%m', m || '-01', '+1 month')
   steps one on -- LEFT JOINed to the rides, counting a ride column.

   *Return: month, rides*

5. **Month on month** (Q1106)

   For each month, the rides started, the change from the month before, and
   that change as a percentage of the month before to one decimal -- NULL for
   the first month. A grouped CTE, then LAG over it, used twice.

   *Return: month, rides, change, pct*

6. **The week, day by day** (Q1107)

   Rides by day of the week, with the day NAMED: strftime('%w') gives '0' for
   Sunday through '6' for Saturday as TEXT, and a CASE turns it into Sun, Mon,
   Tue, Wed, Thu, Fri, Sat. Count the rides and average the fare in whole
   cents.

   *Return: dow, day, rides, avg_fare*

## 3 - Members (3)

Two correlated EXISTS, one for 'has ridden' and one against the member's own
home station; age bands by julianday rather than birth years; and the window's
ORDER BY picking the rides while json_group_array's ORDER BY packs them.

7. **Riders who never start from home** (Q1108)

   Members who HAVE ridden but have never started a ride at their own home
   station, counted by plan. An EXISTS for 'has ridden' and a NOT EXISTS that
   compares the ride's start station with the member's home station.

   *Return: plan, members*

8. **Members by age, and how much they ride** (Q1109)

   Members in three age bands as of 2026-06-30 -- 'under 30', '30-49', '50+'
   -- with how many members and their average number of rides to one decimal.
   Age in years is the julianday difference divided by 365.25; CASE for the
   band; a scalar subquery for each member's ride count.

   *Return: band, members, avg_rides*

9. **Each member's last three rides, as JSON** (Q1110)

   For members 2 to 6 who have ridden: their member_id and a JSON array of the
   ride_ids of their three most recent rides, most recent first. ROW_NUMBER
   partitioned by member ordered by started_at descending in a CTE, then
   json_group_array with an ORDER BY of its own over the rows numbered 1 to 3.

   *Return: member_id, last_three*

## 4 - Money (3)

A WHERE for the plan and a HAVING for the month's total, strict at the fee;
SUM(COUNT(*)) OVER (PARTITION BY zone) as a denominator; and COUNT(DISTINCT)
where a join to payments has multiplied the members.

10. **Pay-as-you-go months that cost more than a subscription** (Q1111)

    Member-and-month pairs where a pay-as-you-go member's fares in one
    calendar month came to MORE than the 1200-cent monthly fee: member_id, the
    month, and the fares. A join to members for the plan, GROUP BY member and
    strftime month, HAVING on the SUM.

    *Return: member_id, month, fares*

11. **Card or app, zone by zone** (Q1112)

    Members' payments by the zone of their home station and the payment
    method: the count and its share of that ZONE's payments as a percentage to
    one decimal. Two joins, GROUP BY zone and method, and a window SUM of
    COUNT(*) partitioned by zone for the denominator.

    *Return: zone, method, payments, pct*

12. **Paying for nothing** (Q1113)

    Members who have paid a subscription but have never ridden: by plan, how
    many such members and the total they have paid. A join to payments, NOT
    EXISTS over rides, and COUNT DISTINCT of the members.

    *Return: plan, members, paid_cents*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A BEFORE UPDATE trigger whose WHEN
makes the refusal conditional, ALTER TABLE ADD COLUMN filled by an UPDATE that
names the outer row, and ON CONFLICT DO UPDATE against INSERT OR REPLACE.

13. **A bike out on a ride cannot be retired** (Q1114)

    Write a BEFORE UPDATE OF retired_on trigger on bikes that refuses --
    RAISE(ABORT, ...) -- when the bike has a ride still open (ended_at NULL)
    and the new retired_on is not NULL, and lets every other update through.
    The question then retires bikes 3 and 8 in one UPDATE each; bike 8 is out
    on a ride.

    *Checked: bikes 3 and 8*

14. **A ride count on every bike** (Q1115)

    Add an integer column `rides` to bikes with ALTER TABLE ADD COLUMN,
    DEFAULT 0, then fill it with each bike's number of rides by an UPDATE
    whose SET is a correlated subquery over rides. Bikes never ridden must end
    at 0.

    *Checked: the total of the new column, how many bikes are at 0, and the largest value*

15. **Retire one bike and add another, in one statement** (Q1116)

    One INSERT with two VALUES rows -- (1, 'electric', '2026-06-30',
    '2026-06-30') and (321, 'electric', '2026-06-30', NULL) for (bike_id,
    model, acquired_on, retired_on) -- with ON CONFLICT (bike_id) DO UPDATE
    that sets ONLY retired_on from excluded. Bike 1 exists, so its row becomes
    an update that retires it; bike 1's own model and acquisition date must
    survive. Bike 321 is new.

    *Checked: bikes 1 and 321*

# Python

## 1 - One tool (5)

Five tools no earlier set used, each the whole answer: divmod against / and %,
defaultdict(list) appended to rather than assigned, weekday() numbering Monday
0, product against zip, and zip_longest with its fillvalue.

1. **divmod(): minutes into hours and minutes** (P371)

   Write a function `hours_minutes(minutes)` that returns a tuple (hours,
   minutes) for a ride length in minutes, in one call of divmod(minutes, 60),
   which gives the quotient and the remainder together. No import is needed.

   ```
   hours_minutes(135) -> (2, 15)
   ```

   *Return: the tuple.*

2. **defaultdict(list): rides grouped by station** (P372)

   Write a function `rides_by_station(pairs)` that takes (station, ride_id)
   tuples and returns a dict mapping each station to the list of its ride_ids
   in order, using collections.defaultdict(list) so that the first append to a
   new station needs no check; return dict(groups) at the end. Write `from
   collections import defaultdict` as the first line.

   ```
   rides_by_station([("Harbour", 1), ("Stadium", 2), ("Harbour", 3)]) -> {"Harbour": [1, 3], "Stadium": [2]}
   ```

   *Return: the dictionary.*

3. **date.fromisoformat(): is it a weekend?** (P373)

   Write a function `is_weekend(day)` that takes a date as 'YYYY-MM-DD' text
   and returns True when it is a Saturday or Sunday. date.fromisoformat(day)
   parses the text and .weekday() numbers Monday 0 to Sunday 6, so the test is
   >= 5. Write `from datetime import date` as the first line.

   ```
   is_weekend("2026-06-27") -> True
   ```

   *Return: True or False.*

4. **itertools.product(): every route** (P374)

   Write a function `routes(starts, ends)` that returns a list of every
   (start, end) pair, one from each list, in order, INCLUDING a start paired
   with the same station as end, using list() over itertools.product(starts,
   ends). Write `import itertools` as the first line.

   ```
   routes(["Harbour", "Stadium"], ["Hilltop", "Stadium"]) -> [("Harbour", "Hilltop"), ("Harbour", "Stadium"), ("Stadium", "Hilltop"), ("Stadium", "Stadium")]
   ```

   *Return: the list of tuples.*

5. **zip_longest(): two columns of unequal length** (P375)

   Write a function `side_by_side(a, b)` that pairs the items of two lists
   position by position as tuples, padding the SHORTER list with 0 so nothing
   is dropped: list() over itertools.zip_longest(a, b, fillvalue=0). Write
   `import itertools` as the first line.

   ```
   side_by_side([1, 2, 3], [10, 20]) -> [(1, 10), (2, 20), (3, 0)]
   ```

   *Return: the list of tuples.*

## 2 - A simple loop (5)

An append that belongs outside the if, out[-1] against 'not in out', a range
that starts at 1, a runner-up that is not equal to the leader, and a while that
keeps going at >=.

6. **The record so far** (P376)

   Write a function `records(distances)` that returns a list the same length
   as the input, where each position holds the longest distance seen SO FAR,
   that one included. A for loop with a best that starts as None and a list
   built up.

   ```
   records([12, 9, 15, 15, 30, 4]) -> [12, 12, 15, 15, 30, 30]
   ```

   *Return: the new list.*

7. **Collapse the repeated stops** (P377)

   Write a function `collapse(stops)` that returns the stops with each run of
   CONSECUTIVE repeats reduced to one -- a station that comes back later
   stays. A for loop that appends a stop only when it differs from the last
   item appended, with the empty list handled.

   ```
   collapse(["A", "A", "B", "B", "B", "A"]) -> ["A", "B", "A"]
   ```

   *Return: the new list.*

8. **How many times the bike changed station** (P378)

   Write a function `station_changes(stations)` that returns how many times
   consecutive entries differ -- the number of moves between stations. A for
   loop over range(1, len(stations)) comparing each entry with the one before,
   and a counter.

   ```
   station_changes([3, 3, 5, 5, 5, 2, 3]) -> 3
   ```

   *Return: an integer.*

9. **The second-longest ride** (P379)

   Write a function `second_longest(minutes)` that returns the second-largest
   DISTINCT value, or None when there are fewer than two distinct values. One
   for loop keeping a first and a second, both starting as None, with an elif
   for a value between them that is not equal to the first.

   ```
   second_longest([12, 45, 8, 30]) -> 30
   ```

   *Return: an integer, or None.*

10. **How many charges until the battery is below the limit** (P380)

    A battery's range halves with every cycle of a test. Write a function
    `halvings(start, limit)` that returns how many halvings it takes for start
    to drop BELOW limit -- 0 when it already is. A while loop that runs while
    the value is >= limit, halving with //= 2 and counting.

    ```
    halvings(100, 20) -> 3
    ```

    *Return: an integer.*

## 3 - Job rows (5)

Maintenance-job dicts with a kind, a cost and a fixed flag: get(kind, 0) + cost
against a bare assignment, the FALSE side of a flag, count then filter at > 1,
totals before any comparison, and / against // in a percentage.

11. **What each kind of repair has cost** (P381)

    Each job is a dict with keys job_id, bike_id, kind, cost and fixed (True
    or False). Write a function `cost_by_kind(jobs)` that returns a dict
    mapping each kind to the total cost of its jobs, fixed or not. A for loop
    and get(kind, 0) + cost.

    ```
    cost_by_kind(JOBS) -> {"puncture": 2850, "brakes": 2600, "chain": 1900, "battery": 9800}
    ```

    *Return: the dictionary.*

12. **The jobs still open** (P382)

    Using the same job dicts, write a function `open_jobs(jobs)` that returns
    the job_ids of the jobs NOT yet fixed, in ascending order. A for loop with
    an if on not j["fixed"], then sorted().

    ```
    open_jobs(JOBS) -> [3, 5]
    ```

    *Return: the sorted list.*

13. **Bikes that have been in more than once** (P383)

    Using the same job dicts, write a function `repeat_bikes(jobs)` that
    returns a sorted list of the bike_ids with MORE THAN ONE job. One loop
    counting jobs per bike in a dict, then a list of the keys whose count is
    above 1, sorted.

    ```
    repeat_bikes(JOBS) -> [7, 12]
    ```

    *Return: the sorted list.*

14. **The dearest kind of repair** (P384)

    Using the same job dicts, write a function `priciest_kind(jobs)` that
    returns the kind with the highest TOTAL cost in a non-empty list -- the
    first kind met if several tie. Total per kind in a dict with one loop,
    then a second loop over the dict keeping the best kind so far.

    ```
    priciest_kind(JOBS) -> "battery"
    ```

    *Return: the kind.*

15. **What share of jobs are fixed** (P385)

    Using the same job dicts, write a function `fixed_share(jobs)` that
    returns the percentage of jobs that are fixed, to one decimal, or None for
    an empty list. A loop counting the fixed ones, then 100 * fixed /
    len(jobs) rounded, behind a guard.

    ```
    fixed_share(JOBS) -> 66.7
    ```

    *Return: a float, or None.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,471 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
