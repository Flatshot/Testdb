# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
seventh set on it, at two tools per question with the tiers named by
task, on tools no bike set had used, and three writable questions.
**Fifteen Python** at the simpler level of the last set: small functions
over plain values -- a list of numbers, a list of strings, one string, or
a couple of numbers -- with no dicts, on constructs that set did not use.

| Stage | SQL questions |
|---|---|
| 1 - Ties, pages and matches | 1-3 |
| 2 - Counting what's distinct | 4-6 |
| 3 - Shaping the output | 7-9 |
| 4 - The calendar, differently | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Numbers | 1-5 |
| 2 - Text | 6-10 |
| 3 - Lists | 11-15 |

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
instead is constraints, DDL, DML and conflict clauses -- and each of
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

**No driver statements this time.** All three are graded on what your
script leaves behind: question 13 on the payments that remain, 14 on the
stations table, and 15 on the members table's column names, read from
pragma_table_info.

| # | Construct |
|---|---|
| 13 | `WITH short AS (SELECT ride_id FROM rides WHERE ...) DELETE FROM payments WHERE ride_id IN (SELECT ride_id FROM short)` |
| 14 | `INSERT OR IGNORE INTO stations (name, zone, docks, opened_on) VALUES (...), (...), (...)` |
| 15 | `ALTER TABLE members RENAME COLUMN district TO area; ALTER TABLE members DROP COLUMN born_on` |

## Things the data does on purpose

- **The busiest bike has 159 rides and the next two counts are each shared by
  two bikes**, so question 1's three highest counts are five bikes, which
  DENSE_RANK keeps and ROW_NUMBER cuts to three.
- **4 rides started at 2025-12-15 06:01**, the minute question 2 pages from: a
  comparison on started_at alone skips three of them, and the row-value
  comparison does not.
- **734 of the 900 members have ridden a cargo bike**, which question 3 counts
  once each by EXISTS; a join would count their rides.
- **About 700 members have started a ride at each station, 730 at Market
  Square**, the riders question 4 sets against rides.
- **The quietest month is 9.4 per cent below the average month**, question 5's
  scale; no month is ten per cent out either way.
- **Old Mill closed on 2026-03-01 and has no June ride**, so question 6's SUM
  for it is NULL and its TOTAL is 0.0; 3 stations have never reported a
  battery job, so question 7's objects for them have four keys.
- **45 monthly members joined in the last three days of a month**, against 55
  whose day number is 28 or more, the gap question 10's 'start of month'
  arithmetic closes.
- **16.9 per cent of rides start between 07:30 and 09:00**, the same in every
  zone, question 11's rush; the hour alone would double it.
- **Riders have spanned 499 of the data's 546 days on average**, measured from
  their first ride, which question 12 does; measured from joining it would
  include the years before 2025 for 530 members.
- **6,098 rides lasted under five minutes, 2,791 of them paid**, the payments
  question 13 deletes; every finished ride lasted under five DAYS, which is
  what the trap's CTE selects.
- **The data ends at 2026-06-30 23:59**, with 35 rides still out and 114 jobs
  open.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, 2.0 is not 2, and 0 is
not False. A function that prints its answer instead of returning it
returns None, and None matches nothing. The inputs are plain values: one or
two numbers or a list of numbers for questions 1 to 5, a string (and
sometimes a second one) for 6 to 10, a list and perhaps a number for 11 to
15. Each prompt shows one example call with its answer, and Run adds a few
more, including the empty list or the edge the question warns about. Where
a tool needs an import, the question says the line to write.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Ties, pages and matches (3)

DENSE_RANK against ROW_NUMBER when counts tie, a row-value comparison that means
'after this row in the ORDER BY', and EXISTS where a join would count a member
once per ride.

1. **The busiest bikes, ties and all** (Q1162)

   The bikes with the three highest ride counts -- every bike that shares one
   of those counts, not just three bikes. A CTE of rides per bike,
   DENSE_RANK() OVER (ORDER BY rides DESC) in a second CTE, then the rows
   ranked 3 or better. DENSE_RANK gives tied bikes the same rank and does not
   skip numbers after a tie.

   *Return: bike_id, rides, rank*

2. **The next page of rides, keyset style** (Q1163)

   The ten rides that come after ride 1095 in start order, started_at then
   ride_id. Not OFFSET: compare ROW VALUES, WHERE (started_at, ride_id) >
   (SELECT started_at, ride_id FROM rides WHERE ride_id = 1095), ORDER BY the
   same two columns, LIMIT 10. Three other rides started in the same minute as
   1095 and have higher ids, so they are the page's first three rows.

   *Return: ride_id, started_at*

3. **Members who have tried a cargo bike** (Q1164)

   For each plan: how many of its members have ridden a cargo bike at least
   once. An EXISTS against rides joined to bikes, correlated on member_id -- a
   join from members would count every cargo RIDE, once per ride, not the
   members.

   *Return: plan, members*

## 2 - Counting what's distinct (3)

COUNT(*), COUNT(column) and COUNT(DISTINCT column) side by side, one CTE read
for its rows and again for its average, and TOTAL, which returns 0.0 where SUM
returns NULL.

4. **Riders against rides at each station** (Q1165)

   For every station: the rides that started there, how many DIFFERENT members
   started a ride there, and the member rides per member to two decimals.
   COUNT(*) against COUNT(DISTINCT member_id); the casual rides, whose
   member_id is NULL, are in the first count and in neither of the others, so
   the ratio is COUNT(member_id) over the distinct count.

   *Return: name, rides, riders, per_rider*

5. **Each month against the average month** (Q1166)

   For every month in the data: its rides, and how far above or below the
   average month it is, as a percentage to one decimal. ONE CTE of rides per
   month, used twice: in FROM for the rows, and in a scalar subquery (SELECT
   AVG(n) FROM m) for the average -- 100.0 * n / avg - 100.

   *Return: month, rides, vs_avg*

6. **June's fares at every station, zero included** (Q1167)

   For every station, the closed one included: the fares of the rides that
   started there in June 2026, in dollars. A LEFT JOIN from stations with the
   June condition in ON, and TOTAL(fare_cents) rather than SUM: SUM of no rows
   is NULL, TOTAL of no rows is 0.0.

   *Return: name, june_fares*

## 3 - Shaping the output (3)

json_group_object with its keys put in order, printf's %04d where || cannot pad,
and DISTINCT with ORDER BY inside GROUP_CONCAT.

7. **Each station's jobs, as one JSON object** (Q1168)

   For every station: a JSON object whose keys are the kinds of job reported
   there and whose values are the counts, keys in alphabetical order --
   {"battery":2,"brakes":14,...}. A subquery of counts per station and kind,
   then json_group_object(kind, cnt ORDER BY kind) per station.

   *Return: name, jobs*

8. **Fleet labels for the cargo bikes** (Q1169)

   A label for every cargo bike: the model in capitals, a hyphen, and the
   bike_id padded with zeros to four digits -- CARGO-0010. printf('%s-%04d',
   UPPER(model), bike_id), or UPPER(model) || '-' || printf('%04d', bike_id).

   *Return: bike_id, label*

9. **What has gone wrong with each bike** (Q1170)

   For bikes 1 to 12 that have had a job: the kinds of job reported on the
   bike, each once, alphabetical, in one comma-separated cell.
   GROUP_CONCAT(DISTINCT kind ORDER BY kind) over maintenance, grouped by
   bike.

   *Return: bike_id, kinds*

## 4 - The calendar, differently (3)

'start of month' chained with '+1 month' and '-3 days', a BETWEEN on 'HH:MM'
text, and MAX minus MIN per member before a second level of grouping.

10. **Joined in the last three days of a month** (Q1171)

    For each plan: its members, and how many joined in the last three days of
    a month -- the 29th to the 31st of January, the 26th to the 28th of a
    February. The last day of a month is date(d, 'start of month', '+1 month',
    '-1 day'), so the window opens at '-3 days' from the start of the next
    month; a SUM of joined_on >= that.

    *Return: plan, members, month_end*

11. **The morning rush, zone by zone** (Q1172)

    For each zone, of the start station: its rides, those that started between
    07:30 and 09:00 inclusive, and that as a percentage to one decimal.
    strftime('%H:%M', started_at) is the time of day as text, and 'HH:MM' text
    compares correctly, so BETWEEN '07:30' AND '09:00' is the test.

    *Return: zone, rides, rush, rush_pct*

12. **How long each rider has been riding** (Q1173)

    For each plan: the members who have ridden, and the average days between
    their first ride and their latest, to one decimal. A CTE per member of
    julianday(MAX(started_at)) - julianday(MIN(started_at)) over their rides,
    then joined to members and averaged by plan. The span is measured from the
    first RIDE, not from joining.

    *Return: plan, riders, avg_span*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A WITH clause in front of a DELETE,
INSERT OR IGNORE, and RENAME COLUMN with DROP COLUMN.

13. **Refund the rides that never really happened** (Q1174)

    A ride under five minutes is a false start, and its fare is refunded by
    deleting its payment. A CTE in front of the DELETE: WITH short AS (SELECT
    ride_id FROM rides WHERE (julianday(ended_at) - julianday(started_at)) *
    1440 < 5) DELETE FROM payments WHERE ride_id IN (SELECT ride_id FROM
    short). Minutes, not days: julianday differences are in days.

    *Checked: how many payments remain, and how many name a ride*

14. **New stations from a list, skipping the ones we have** (Q1175)

    A list of three stations to add, two of which already exist: Harbour
    (east, 20 docks), Canal Basin (west, 18) and Cathedral (centre, 24), all
    opening 2026-07-01. ONE INSERT OR IGNORE INTO stations (name, zone, docks,
    opened_on) VALUES (...), (...), (...): the name is UNIQUE, and OR IGNORE
    skips the rows that would break that instead of failing.

    *Checked: how many stations there are, the highest station_id, and whether Canal Basin is among them*

15. **A column renamed and a column dropped** (Q1176)

    The members table is being tidied: district is to be called area, and
    born_on is no longer kept. Two statements: ALTER TABLE members RENAME
    COLUMN district TO area, then ALTER TABLE members DROP COLUMN born_on.
    SQLite's ALTER TABLE does these two things and ADD COLUMN, and little
    else.

    *Checked: the table's column names, in order*

# Python

## 1 - Numbers (5)

A ceiling from floor division of a negative, tiers that stack on the ones below,
a square root after the variance, a remainder shared out a cent at a time, and a
run checked for repeats as well as span.

1. **Billed to the next half hour** (P431)

   Rides are billed in half hours, always rounded UP: 31 minutes is billed as
   60, 30 as 30, 0 as 0. Write a function `billed_minutes(minutes)` that
   returns the billed figure. The trick is -(-minutes // 30) * 30: floor
   division of the negative rounds towards minus infinity, which is up once
   the sign is flipped back.

   ```
   billed_minutes(31) -> 60
   ```

   *Return: an int.*

2. **A fare in three tiers** (P432)

   A casual fare: the first 30 minutes are free, minutes 31 to 60 cost 10
   cents each, and every minute after 60 costs 20. Write a function
   `tiered_fare(minutes)` that returns the fare in cents: an if/elif/else on
   the minutes, each branch computing its own tier on top of the ones below.

   ```
   tiered_fare(45) -> 150
   ```

   *Return: an int.*

3. **How much ride lengths vary** (P433)

   Write a function `std_dev(minutes)` that returns the population standard
   deviation to two decimals, or None for an empty list. Two passes: the mean
   first, then the mean of the squared differences from it, and math.sqrt of
   that -- write `import math` at the top.

   ```
   std_dev([10, 20, 30, 40, 50]) -> 14.14
   ```

   *Return: a float, or None.*

4. **A group fare split fairly** (P434)

   A group's fare in cents is split between n riders so that the shares add up
   EXACTLY and differ by at most one cent, the extra cents going to the first
   riders. Write a function `split_fare(total, n)` that returns the n shares:
   total // n each, plus 1 for the first total % n of them -- a comprehension
   over range(n) with a conditional.

   ```
   split_fare(1000, 3) -> [334, 333, 333]
   ```

   *Return: a list of ints.*

5. **Are the ride ids unbroken?** (P435)

   A day's ride ids should run without gaps or repeats, whatever order they
   were logged in. Write a function `is_unbroken(ids)` that returns True when
   the ids are exactly the integers from the smallest to the largest, each
   once, and True for an empty list. Three facts have to hold at once: no
   duplicates (len of the set equals len of the list) and the count equals max
   - min + 1.

   ```
   is_unbroken([3, 1, 2]) -> True
   ```

   *Return: True or False.*

## 2 - Text (5)

n % 100 before n % 10, two methods chained, int() only after the digits are
checked, a replacement as long as the word, and zip stopping at the shorter
name.

6. **1st, 2nd, 3rd, 11th** (P436)

   Write a function `ordinal(n)` that returns the number with its English
   suffix: 1st, 2nd, 3rd, 4th, 11th, 12th, 13th, 21st, 101st, 111th. The
   suffix depends on n % 10 -- 1, 2, 3 for st, nd, rd, anything else th --
   EXCEPT that 11, 12 and 13 (n % 100) take th.

   ```
   ordinal(22) -> "22nd"
   ```

   *Return: a str.*

7. **A station name as a web address** (P437)

   Write a function `slug(name)` that turns a station name into the form used
   in a web address: all lower case, spaces replaced by hyphens. lower() and
   replace(), in either order.

   ```
   slug("Market Square") -> "market-square"
   ```

   *Return: a str.*

8. **Is it a time of day?** (P438)

   Write a function `is_clock_time(s)` that returns True for a five-character
   'HH:MM' with hours 00 to 23 and minutes 00 to 59, and False for anything
   else. Check the shape first -- length 5, a colon at position 2, digits
   either side -- and only then convert with int() and test the ranges.

   ```
   is_clock_time("08:05") -> True
   ```

   *Return: True or False.*

9. **A word blanked out** (P439)

   Write a function `censor(text, word)` that returns the text with every
   occurrence of the word replaced by stars, as many stars as the word has
   characters, so the line keeps its length. One replace() whose replacement
   is '*' * len(word).

   ```
   censor("Market Square", "Square") -> "Market ******"
   ```

   *Return: a str.*

10. **Where two names stop agreeing** (P440)

    Write a function `common_prefix(a, b)` that returns the characters the two
    strings share at the start, up to the first position where they differ. A
    loop over zip(a, b) comparing character by character, break on the first
    mismatch, and a slice of a up to that point.

    ```
    common_prefix("Hilltop", "Hillside") -> "Hill"
    ```

    *Return: a str, possibly empty.*

## 3 - Lists (5)

Two for clauses in one comprehension, k from the front to the end, zip pairing
each value with its weight, windows that stop while still full, and a range that
starts at the smallest id.

11. **Every stop on every route, in one list** (P441)

    Routes are lists of station ids, and a day's routes are a list of those
    lists. Write a function `flatten(routes)` that returns all the stops in
    one flat list, in order, repeats kept. One comprehension with two for
    clauses: [s for route in routes for s in route].

    ```
    flatten([[1, 3, 5], [5, 9], [2]]) -> [1, 3, 5, 5, 9, 2]
    ```

    *Return: a list of ints.*

12. **The rota, rotated** (P442)

    Each week the duty rota moves on: the first k names go to the end. Write a
    function `rotate(names, k)` that returns the rotated list without changing
    the original: the slice from k onwards, then the slice up to k, added
    together.

    ```
    rotate([1, 2, 3, 4, 5], 2) -> [3, 4, 5, 1, 2]
    ```

    *Return: a list.*

13. **An average that counts the busy stations more** (P443)

    Each station has an average ride length and a number of rides. Write a
    function `weighted_average(values, weights)` that returns the average of
    the values with each one counted as many times as its weight -- sum of
    value times weight over zip, divided by the sum of the weights -- rounded
    to two decimals, or None when the lists are empty.

    ```
    weighted_average([3.2, 3.7, 2.7], [100, 300, 50]) -> 3.48
    ```

    *Return: a float, or None.*

14. **A smoothed line of daily rides** (P444)

    Write a function `moving_average(counts, k)` that returns the average of
    each run of k consecutive values, as floats: for k = 3 the first is the
    mean of items 0 to 2, the next of 1 to 3, and so on, with len(counts) - k
    + 1 results -- none when the list is shorter than k. A comprehension over
    range(len(counts) - k + 1) with a slice counts[i:i + k].

    ```
    moving_average([10, 20, 30, 40, 50], 3) -> [20.0, 30.0, 40.0]
    ```

    *Return: a list of floats.*

15. **The ride ids missing from the log** (P445)

    Write a function `missing_ids(ids)` that returns the integers between the
    smallest and largest id that are absent, in ascending order, and [] for an
    empty list. sorted(set(range(min(ids), max(ids) + 1)) - set(ids)), behind
    a guard.

    ```
    missing_ids([5, 7, 8, 10]) -> [6, 9]
    ```

    *Return: a list of ints.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,591 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
