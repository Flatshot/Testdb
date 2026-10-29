# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
fourth set on it, at two tools per question with the tiers named by task,
on tools no bike set had used, and three writable questions that each take
two steps. **Fifteen Python** in three shapes: five functions that are one
tool each, on tools no earlier set used; four built around one simple loop
and ONE whole program graded on what it prints; and five over lists of
payment dicts shaped like the scheme's rows, with a member or a ride that
is None.

| Stage | SQL questions |
|---|---|
| 1 - Streaks and spells | 1-3 |
| 2 - Labels and text | 4-6 |
| 3 - Counting with conditions | 7-9 |
| 4 - The fleet's calendar | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - One tool | 1-5 |
| 2 - A simple loop | 6-10 |
| 3 - Payment rows | 11-15 |

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

**Driver statements.** Question 14 runs four INSERTs of its own *after* your
script: one good move, one from a station to itself, one for a bike that
does not exist and one to a station that does not exist. The probe lists
the moves that got in, so each constraint shows. Questions 13 and 15 are
graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `ALTER TABLE rides ADD COLUMN minutes REAL GENERATED ALWAYS AS ((julianday(ended_at) - julianday(started_at)) * 1440) VIRTUAL` |
| 14 | `CREATE TABLE bike_moves (move_id INTEGER PRIMARY KEY, bike_id INTEGER NOT NULL REFERENCES bikes(bike_id), ..., CHECK (from_station <> to_station))` |
| 15 | `CREATE TEMP TABLE gone AS SELECT bike_id FROM bikes WHERE retired_on IS NOT NULL; DELETE FROM maintenance WHERE fixed_at IS NULL AND bike_id IN (SELECT bike_id FROM gone)` |

## Things the data does on purpose

- **100 of the 900 members have never ridden**, and 86 have no
  district recorded -- question 5 files those 86 under the zone of
  their home station instead of losing them to a NULL group.
- **7 of the 320 bikes have never been ridden and 18 are
  retired**; question 12's average age needs the 18 retired bikes'
  retirement dates and a fallback for the rest, and question 15 deletes
  the retired bikes' open jobs, which are seven of their sixty-four.
- **A bike is ridden on 9 per cent of its active days more than once**,
  which is why question 1's islands need DISTINCT days; the best run anyone
  manages is 8 days.
- **22,732 of the payments name a ride and no member**, so
  payments.member_id is full of NULLs: a NOT IN over it returns nothing,
  and question 8's NOT EXISTS finds 215 members never named on a
  payment, 10 of them subscribers whom every charge missed.
- **30 per cent of rides are by casual riders**, and the share is
  much the same at every station, which question 7's FILTER shows.
- **Two of the 31 cargo bikes arrived on the same day**, the one tie in
  question 10's arrival order, broken by bike_id so that the numbering is
  reproducible.
- **Only 90 rides start before six in the morning**, and the day's
  rides run to 240 minutes at the longest, question 13's maximum.
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
needs an import, the question says the line to write. Questions 6 to 9 and
11 to 15 are one simple loop each, the last five over lists of payment
dicts: the prompt shows a list called PAYMENTS as its example, and Run
passes your function that list and a few shorter ones. Question 10 is a
**program**: the editor holds a whole program and Check compares what it
prints, line by line, with the reference, ignoring trailing spaces.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Streaks and spells (3)

The gaps-and-islands trick, which needs one row per day; a ROWS frame computed
over every day and filtered afterwards; and FIRST_VALUE with LAST_VALUE, whose
default frame stops at the current row.

1. **Each bike's longest run of days in use** (Q1117)

   For bikes 1 to 10: the most CONSECUTIVE days on which the bike started at
   least one ride. The gaps-and-islands trick: a CTE of DISTINCT bike-and-day
   pairs, then date(day, '-' || ROW_NUMBER() OVER (PARTITION BY bike_id ORDER
   BY day) || ' days') as a group key that is the same for every day of a run,
   COUNT per group, MAX per bike.

   *Return: bike_id, longest_run*

2. **A week's average, rolling** (Q1118)

   For each day of June 2026: the rides started that day and the average over
   that day and the six before it, to one decimal. A CTE of rides per day over
   ALL days, AVG with ROWS BETWEEN 6 PRECEDING AND CURRENT ROW, and the filter
   to June applied OUTSIDE, so that June 1st can see the end of May.

   *Return: day, rides, avg_7d*

3. **The first and last ride of every month** (Q1119)

   For each month: the ride_id of the first ride started in it and of the
   last. FIRST_VALUE and LAST_VALUE over a window partitioned by month and
   ordered by started_at, with the frame opened to ROWS BETWEEN UNBOUNDED
   PRECEDING AND UNBOUNDED FOLLOWING, and DISTINCT.

   *Return: month, first_ride, last_ride*

## 2 - Labels and text (3)

GROUP_CONCAT with its own ORDER BY, COALESCE grouped on the result rather than
the raw column, and FORMAT, which prints the decimals only if the division left
any.

4. **The stations of each zone, in one cell** (Q1120)

   For each zone: how many stations, and their names in one text,
   alphabetical, separated by ', '. GROUP_CONCAT with a separator and an ORDER
   BY inside the brackets.

   *Return: zone, stations, names*

5. **Where the members live, with a fallback** (Q1121)

   Members counted by district, except that a member with no district is
   counted under 'zone ' followed by the zone of their home station. COALESCE
   over the district and the concatenation, with a join to stations.

   *Return: place, members*

6. **Fares by plan, in dollars** (Q1122)

   For each plan: the members' fares in all, as TEXT like '$12345.50' --
   FORMAT('$%.2f', ...) over the cents divided by 100.0. A join from rides to
   members for the plan.

   *Return: plan, fares*

## 3 - Counting with conditions (3)

FILTER on one aggregate against WHERE on the whole query, NOT EXISTS where NOT
IN meets a NULL and returns nothing, and CUME_DIST, whose ORDER BY direction
decides which end 0.9 names.

7. **How casual each station is** (Q1123)

   For each start station: all rides started there, those by casual riders
   (member_id NULL), and the casual share as a percentage to one decimal.
   COUNT(*) FILTER (WHERE ...) for the casual count, in one pass over rides.

   *Return: station_id, rides, casual, casual_pct*

8. **Members never named on a payment** (Q1124)

   Members with no payment carrying their member_id, counted by plan -- fare
   payments name the ride, not the rider, so pay-as-you-go members are mostly
   here. Use NOT EXISTS; a NOT IN over payments.member_id would meet the NULLs
   of the fare payments and return nothing.

   *Return: plan, members*

9. **What it takes to be a top-ten-per-cent rider** (Q1125)

   For each plan: the ride count that puts a member in the top ten per cent of
   that plan's riders, and the plan's maximum. A CTE of rides per member,
   CUME_DIST() OVER (PARTITION BY plan ORDER BY rides), then the smallest
   count whose CUME_DIST is at least 0.9 -- MIN with a FILTER -- and MAX.

   *Return: plan, top_decile_rides, max_rides*

## 4 - The fleet's calendar (3)

A named WINDOW shared by ROW_NUMBER and LAG, 'weekday 0' then '-6 days' for the
Monday that began a week, and COALESCE inside julianday so the bikes still in
service count.

10. **The cargo bikes, in order of arrival** (Q1126)

    The cargo bikes in the order they were acquired: bike_id, acquired_on,
    their place in that order, and the days since the previous cargo bike
    arrived (NULL for the first). ROW_NUMBER and LAG over ONE named window --
    WINDOW w AS (ORDER BY acquired_on, bike_id) after the WHERE -- and
    julianday for the gap.

    *Return: bike_id, acquired_on, nth, days_since_previous*

11. **Weeks that start on Monday** (Q1127)

    Rides per week for the weeks touching June 2026 -- rides started from
    2026-05-25 up to but not including 2026-07-01 -- labelled by the MONDAY
    the week began: date(started_at, 'weekday 0', '-6 days') moves forward to
    the Sunday and back six days. GROUP BY that.

    *Return: week_of, rides*

12. **How old the fleet is** (Q1128)

    For each model: the bikes, how many are retired, and the average age in
    whole days -- a retired bike's age at retirement, an in-service bike's age
    at 2026-06-30. COALESCE(retired_on, '2026-06-30') inside julianday.

    *Return: model, bikes, retired, avg_age_days*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A VIRTUAL generated column, a CREATE
TABLE whose CHECK and REFERENCES turn three driver inserts away, and a TEMP
table feeding a DELETE.

13. **A minutes column that computes itself** (Q1129)

    Add to rides a column `minutes` that is GENERATED ALWAYS AS the ride's
    length in minutes -- (julianday(ended_at) - julianday(started_at)) * 1440
    -- VIRTUAL, so ALTER TABLE can add it without rewriting the table. Open
    rides get NULL by themselves.

    *Checked: the column's average to one decimal, its rounded maximum, and how many rows have it NULL*

14. **A table that turns bad rows away** (Q1130)

    Create a table `bike_moves (move_id INTEGER PRIMARY KEY, bike_id,
    from_station, to_station, moved_on)` for bikes trucked between stations:
    bike_id REFERENCES bikes, from_station and to_station REFERENCES stations,
    all NOT NULL, moved_on NOT NULL, and a CHECK that from_station <>
    to_station. The question then inserts four rows: a good one, one moving a
    bike to the station it is at, one for a bike 999, and one to a station 99.

    *Checked: the move_ids that got in*

15. **Close the books on the retired bikes** (Q1131)

    Two steps: CREATE TEMP TABLE gone AS the bike_ids of the retired bikes,
    then DELETE the maintenance jobs that are still OPEN (fixed_at NULL) on
    those bikes -- WHERE bike_id IN (SELECT bike_id FROM gone). Fixed jobs on
    retired bikes are history and stay.

    *Checked: how many jobs remain, and how many of them are open*

# Python

## 1 - One tool (5)

Five tools no earlier set used, each the whole answer: a maketrans deletion
table, deque(maxlen=3) turned back into a list, timedelta for date arithmetic, a
tuple key that sorts one way then the other, and isdigit against isalnum.

1. **str.translate(): strip the punctuation** (P386)

   Write a function `plain_name(name)` that returns the name with every '.',
   apostrophe and '-' removed, by name.translate(str.maketrans("", "", ".'-"))
   -- a table whose third argument lists the characters to delete. No import
   is needed.

   ```
   plain_name("St. Mary's-on-Hill") -> "St MarysonHill"
   ```

   *Return: the new string.*

2. **deque(maxlen=3): only the last three** (P387)

   Write a function `last_three(ride_ids)` that returns a list of the last
   three ids fed to it in order, fewer if there were fewer, using
   collections.deque(ride_ids, maxlen=3) -- a queue that drops from the left
   when a fourth item arrives -- turned back into a list. Write `from
   collections import deque` as the first line.

   ```
   last_three([4, 8, 15, 16, 23, 42]) -> [16, 23, 42]
   ```

   *Return: the list.*

3. **timedelta(): the next payment date** (P388)

   Write a function `next_due(paid_on, days)` that returns the date days after
   paid_on, both as 'YYYY-MM-DD' text: date.fromisoformat() to parse, +
   timedelta(days=days) to move, .isoformat() to print. Write `from datetime
   import date, timedelta` as the first line.

   ```
   next_due("2026-01-31", 30) -> "2026-03-02"
   ```

   *Return: the new date as text.*

4. **sorted() with two keys: dearest first, then by id** (P389)

   Write a function `by_fare(rides)` that takes [ride_id, fare] pairs and
   returns them sorted by fare from highest to lowest, ties by ride_id from
   lowest up, in ONE sorted() call whose key is a tuple: key=lambda r: (-r[1],
   r[0]). No import is needed.

   ```
   by_fare([[3, 200], [1, 350], [2, 200]]) -> [[1, 350], [2, 200], [3, 200]]
   ```

   *Return: the sorted list.*

5. **str.isdigit(): is it a bike number?** (P390)

   Write a function `is_bike_number(code)` that returns True when the code is
   made of digits only and is not empty, in one call of the string's isdigit()
   method. No import is needed.

   ```
   is_bike_number("0042") -> True
   ```

   *Return: True or False.*

## 2 - A simple loop (5)

lower() before testing a vowel, two appends per turn, add then record, a count
that resets on a new best -- and one whole program printing a bar chart with //
not round().

6. **How many vowels in a station name** (P391)

   Write a function `vowels(name)` that returns how many characters of the
   name are vowels, either case. A for loop over the characters, an if on
   ch.lower() in "aeiou", and a counter.

   ```
   vowels("Botanic Gardens") -> 5
   ```

   *Return: an integer.*

7. **Starts and ends, interleaved** (P392)

   Write a function `interleave(starts, ends)` that takes two lists of the
   SAME length and returns one list alternating start, end, start, end. A for
   loop over range(len(starts)) appending two items per turn.

   ```
   interleave(["A", "B", "C"], ["X", "Y", "Z"]) -> ["A", "X", "B", "Y", "C", "Z"]
   ```

   *Return: the new list.*

8. **The balance after each payment** (P393)

   Write a function `running_total(amounts)` that returns a list of the
   cumulative total after each amount. A for loop with a total that grows and
   a list that collects it after each step.

   ```
   running_total([1200, 350, 200]) -> [1200, 1550, 1750]
   ```

   *Return: the new list.*

9. **How many share the longest ride** (P394)

   Write a function `ties_at_top(minutes)` that returns how many entries equal
   the largest value, 0 for an empty list, in ONE for loop: a best that starts
   as None and a count that resets to 1 on a new best and grows by 1 on an
   equal.

   ```
   ties_at_top([30, 45, 12, 45, 45]) -> 3
   ```

   *Return: an integer.*

10. **A bar chart of the week** (P395)

    Write a program that prints one line per day for this dictionary of rides
    per weekday, in this order:

    ```
    rides = {"Mon": 5647, "Tue": 5595, "Wed": 5452, "Thu": 5391, "Fri": 5559, "Sat": 5433, "Sun": 5528}
    ```

    Each line is the day, a space, and one '#' for every full 500 rides --
    rides // 500 of them -- so Monday has eleven. A for loop over
    rides.items().

    Print: seven lines like

    *Mon ###########*

## 3 - Payment rows (5)

Payment dicts with a member or a ride that is None: + amount against + 1, 'is
None' against 'not', > against >= for the first of equals, the None filtered
before sorted() can crash, and the guard before the division.

11. **What came in by card and by app** (P396)

    Each payment is a dict with keys payment_id, member (None for a casual
    rider's fare), ride (None for a subscription), amount and method. Write a
    function `total_by_method(payments)` that returns a dict mapping each
    method to the total amount. A for loop and get(method, 0) + amount.

    ```
    total_by_method(PAYMENTS) -> {"app": 2850, "card": 10250}
    ```

    *Return: the dictionary.*

12. **How many were subscriptions** (P397)

    Using the same payment dicts, write a function
    `subscription_count(payments)` that returns how many payments are
    subscriptions -- their ride is None. A for loop with an if on p["ride"] is
    None and a counter. A ride id of 0 is a ride.

    ```
    subscription_count(PAYMENTS) -> 3
    ```

    *Return: an integer.*

13. **The biggest payment** (P398)

    Using the same payment dicts, write a function
    `biggest_payment_id(payments)` that returns the payment_id of the largest
    amount in a non-empty list, the FIRST if several tie. A for loop with a
    best row so far, starting at payments[0], replaced only on a strictly
    bigger amount.

    ```
    biggest_payment_id(PAYMENTS) -> 3
    ```

    *Return: an integer.*

14. **The members who have been billed** (P399)

    Using the same payment dicts, write a function `members_billed(payments)`
    that returns a sorted list of the DISTINCT members who appear on a
    payment, leaving out the None of the casual fares. A for loop adding to a
    set under an if, then sorted().

    ```
    members_billed(PAYMENTS) -> [7, 9]
    ```

    *Return: the sorted list.*

15. **What share of payments came by app** (P400)

    Using the same payment dicts, write a function `app_share(payments)` that
    returns the percentage of payments whose method is 'app', to one decimal,
    or None for an empty list. A loop counting the app payments, then 100 *
    app / len(payments) rounded, behind a guard.

    ```
    app_share(PAYMENTS) -> 66.7
    ```

    *Return: a float, or None.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,501 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
