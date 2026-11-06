# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
ninth set on it, at two tools per question with the tiers named by task,
on tools no bike set had used, and three writable questions; the prompts
name the tool but do not write the statement. **Fifteen Python** at the
easy level of the last set: everyday tasks over plain lists and strings,
with no maths and no dicts, on tasks that set did not cover.

| Stage | SQL questions |
|---|---|
| 1 - Finding the rows | 1-3 |
| 2 - Patterns and parts | 4-6 |
| 3 - Ordered by time | 7-9 |
| 4 - Branches, distinct and difference | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Counting and finding | 1-5 |
| 2 - Labels | 6-10 |
| 3 - Checks and filters | 11-15 |

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
instead is constraints, triggers and DDL -- and each of questions 13 to 15
is one of those.

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

**Driver statements.** All three questions run statements of their own
*after* your script: question 13 deletes jobs 9 and 19 and every open
battery job, question 14 inserts three dock counts of which 'twelve' must
be refused, and question 15 inserts three daily rows of which the third
repeats a key. The probes read what the trigger, the STRICT table and the
composite key left behind, so each refusal or log entry shows.

| # | Construct |
|---|---|
| 13 | `CREATE TABLE deleted_jobs (...); CREATE TRIGGER log_deleted_job AFTER DELETE ON maintenance BEGIN INSERT INTO deleted_jobs (...) VALUES (OLD.job_id, ...); END` |
| 14 | `CREATE TABLE dock_counts (count_id INTEGER PRIMARY KEY, ..., bikes INTEGER NOT NULL) STRICT` |
| 15 | `CREATE TABLE daily_use (bike_id ..., day ..., rides ..., PRIMARY KEY (bike_id, day)) WITHOUT ROWID` |

## Things the data does on purpose

- **The busiest route is Market Square back to Market Square, 592 rides**, and
  58 of them were in March 2026, the month Old Mill closed; question 1 matches
  the pair as one row value.
- **100 rides started on 30 June 2026**, every one of them after midnight,
  which a BETWEEN that ends at '2026-06-30' loses and question 3's half-open
  range keeps.
- **Rosa, Zara and Umar are the only four-letter first names, 122 members
  between them**, the ones LIKE's underscores find in question 4.
- **5,801 subscription payments are spread across the month, 126 of them on a
  31st**, question 5's lightest day because only seven months have one.
- **Only 13 members joined in the first week of a year, across four years**,
  question 6's count; the first week of every MONTH would be a quarter of the
  members.
- **The longest ride is 240 minutes and the longest distance 65,956 metres**,
  set in October 2025, the record question 8's running MAX carries forward to
  June.
- **15,873 rides were free**, the band that question 10's CASE must test
  first; 163 different members started at Market Square in June, the most
  anywhere, and none at Old Mill.
- **23 routes ridden in June 2025 were not ridden in June 2026, every one
  touching Old Mill**, which question 12's EXCEPT finds; the other way round
  there are none.
- **Only 1 battery job is open**, so question 13's log holds three rows, two
  of them jobs 9 and 19.
- **The data ends at 2026-06-30 23:59**, with 35 rides still out and 114 jobs
  open.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, and 0 is not False. A
function that prints its answer instead of returning it returns None, and
None matches nothing. The inputs are everyday values: a list of station
names for questions 1 to 5, an hour, a name or a few words for 6 to 10, a
list of stops for 11 to 15. Each prompt shows one example call with its
answer, and Run adds a few more, including the empty list or the edge the
question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Finding the rows (3)

Two columns compared as one row value against a subquery, json_each turning a
JSON array into rows to join on, and >= the first day with < the day after
instead of BETWEEN.

1. **The busiest route, month by month** (Q1192)

   For each month: how many rides took the single busiest route, the (start,
   end) pair with the most finished rides overall. Compare the two columns as
   one ROW VALUE against a subquery that returns that pair, rather than
   testing start and end separately.

   *Return: month, rides*

2. **Rides at the stations on a list** (Q1193)

   A caller hands you station ids as a JSON array, '[2, 5, 7, 99]'. For each
   station on the list that exists: its name and how many rides started there.
   json_each() turns the array into rows you can join on.

   *Return: name, rides*

3. **June's rides, and the day BETWEEN loses** (Q1194)

   For each zone, of the start station: the rides that started in June 2026.
   Timestamps carry a time of day, so a range that ends at '2026-06-30' stops
   at midnight on the 30th; use a half-open range instead, up to but not
   including the first of July.

   *Return: zone, rides*

## 2 - Patterns and parts (3)

LIKE's _ for exactly one character, strftime's %d for the day of the month, and
'start of year' chained with '+7 days'.

4. **Four-letter first names** (Q1195)

   For each plan: its members, and how many have a first name of exactly four
   letters. LIKE's other wildcard, _, matches exactly one character; the first
   name ends at the first space.

   *Return: plan, members, four_letter*

5. **Which day of the month subscriptions are paid** (Q1196)

   For each day of the month, '01' to '31': how many SUBSCRIPTION payments
   fell on it. A subscription payment names a member; strftime has a format
   code for the day of the month.

   *Return: day, payments*

6. **Joined in the first week of the year** (Q1197)

   For each year members joined in: how many joined, and how many of them
   within the first seven days of that year. A date modifier walks any date
   back to the start of its year; a second one moves forward from there.

   *Return: year, joined, first_week*

## 3 - Ordered by time (3)

unixepoch for seconds that divide cleanly into minutes, a window MAX whose ORDER
BY makes it the record so far, and LAG with an offset of 2 and a default of 0.

7. **The longest ride of each month, in minutes** (Q1198)

   For each month: the length in whole minutes of its longest finished ride.
   unixepoch() turns a timestamp into seconds, and seconds subtract cleanly.

   *Return: month, longest_minutes*

8. **The record ride, month by month** (Q1199)

   For each month: the longest distance ridden that month, and the longest
   ridden in ANY month up to and including it -- the record to date. A monthly
   MAX in a CTE, then a window MAX ordered by month over it.

   *Return: month, longest_m, record_m*

9. **Where bike 7 was two rides ago** (Q1200)

   For each ride bike 7 started in June 2026: where it started, and where it
   started TWO rides earlier, with 0 when there is no such ride. LAG takes an
   offset and a default as its second and third arguments; compute over all of
   bike 7's rides and filter to June afterwards.

   *Return: ride_id, started_at, start_station_id, two_back*

## 4 - Branches, distinct and difference (3)

A CASE tested from the narrowest band out, COUNT of a DISTINCT CASE with no
ELSE, and EXCEPT subtracting whole (start, end) rows with the operands the right
way round.

10. **Fares in four bands** (Q1201)

    Every ride in one of four bands: 'free', 'under $2', 'under $5' and '$5
    and up' -- with how many rides and the fares added up in dollars. One
    CASE; its WHEN tests are checked in order and the first true one wins, so
    think about which band has to be tested first.

    *Return: band, rides, fares*

11. **June's riders against all riders, per station** (Q1202)

    For every station: how many different members have ever started a ride
    there, and how many different members did so in June 2026. Both from one
    pass over rides: the second count is a COUNT of DISTINCT over a CASE that
    yields the member only for June rows.

    *Return: name, riders_ever, riders_june*

12. **The routes that Old Mill's closure took away** (Q1203)

    Every route -- a start station and an end station, by name -- that was
    ridden in June 2025 but not in June 2026. EXCEPT works on rows of two
    columns as well as one; join to stations for the names afterwards.

    *Return: from_station, to_station*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. An AFTER DELETE trigger reading OLD, a
STRICT table, and a composite PRIMARY KEY on a WITHOUT ROWID table.

13. **A log of every deleted job** (Q1204)

    Nothing should vanish from maintenance without a trace. Create a table
    deleted_jobs with job_id (the primary key), bike_id, kind and cost_cents,
    all required, plus a deleted_on text column defaulting to '2026-07-01';
    then an AFTER DELETE trigger on maintenance that copies the removed row's
    four values into it. The question then deletes jobs 9 and 19, and every
    open battery job.

    *Checked: how many rows the log has, its lowest and highest job_id, and how many are battery jobs*

14. **A table that insists on its types** (Q1205)

    Create dock_counts with count_id as the integer primary key, station_id
    (integer, required), counted_on (text, required) and bikes (integer,
    required) -- as a STRICT table, so that a value of the wrong type is
    refused rather than stored as given. The question then inserts three
    counts: 17, the word 'twelve', and the text '9'.

    *Checked: each row's station_id, bikes and typeof(bikes)*

15. **One row per bike per day, keyed by both** (Q1206)

    Create daily_use with bike_id (referencing bikes), day (text) and rides
    (integer), all required, whose PRIMARY KEY is the pair (bike_id, day) -- a
    composite key -- and declared WITHOUT ROWID, as a table keyed by its own
    columns can be. The question then inserts three rows, the third repeating
    a bike-and-day.

    *Checked: the rows that got in*

# Python

## 1 - Counting and finding (5)

`in` before index() and a length check before + 1, count() == 1 rather than
set(), count() on a slice, `in` on the second list to keep the first list's
order, and -1 after the loop.

1. **Where the bike went after Harbour** (P461)

   Write a function `stop_after(stops, station)` that returns the stop that
   came right after the station's FIRST appearance, or None when the station
   is missing or was the last stop. Two things to check before indexing.

   ```
   stop_after(["Parkway", "Harbour", "Stadium"], "Harbour") -> "Stadium"
   ```

   *Return: a str, or None.*

2. **The stations visited only once** (P462)

   Write a function `visited_once(stops)` that returns the stations that
   appear exactly once in the day's stops, in the order they appear. A
   comprehension that keeps a stop when its count() in the list is 1.

   ```
   visited_once(["Harbour", "Stadium", "Harbour", "Parkway"]) -> ["Stadium", "Parkway"]
   ```

   *Return: a list of str.*

3. **Visits before midday** (P463)

   The first n stops of the day happened before midday. Write a function
   `visits_before(stops, station, n)` that returns how many of those first n
   stops were at the station. A slice, then count().

   ```
   visits_before(["Harbour", "Stadium", "Harbour", "Harbour"], "Harbour", 3) -> 2
   ```

   *Return: an int.*

4. **Stations both bikes reached, in the first bike's order** (P464)

   Write a function `both_reached(first, second)` that returns the stops of
   the first bike's day that the second bike also reached, in the first bike's
   order, repeats kept. A comprehension over the first list with `in` on the
   second.

   ```
   both_reached(["Stadium", "Harbour", "Parkway"], ["Parkway", "Stadium"]) -> ["Stadium", "Parkway"]
   ```

   *Return: a list of str.*

5. **When the bike first moved on** (P465)

   Write a function `first_change(stops)` that returns the position of the
   first stop that differs from the first stop of the day, or -1 if every stop
   is the same (or there are none). A loop with enumerate, comparing with
   stops[0].

   ```
   first_change(["Harbour", "Harbour", "Stadium", "Harbour"]) -> 2
   ```

   *Return: an int.*

## 2 - Labels (5)

hour % 12 with 0 shown as 12, a slice then upper(), < 12 and < 18 at the
boundaries, special cases returned early, and an f-string whose brackets and
spaces are part of the answer.

6. **The hour on a 12-hour clock** (P466)

   Write a function `twelve_hour(hour)` that turns an hour from 0 to 23 into
   '3 pm', '12 am', '12 pm' or '8 am': am before 12, pm from 12; the hour
   shown is hour % 12, except that 0 is shown as 12.

   ```
   twelve_hour(15) -> "3 pm"
   ```

   *Return: a str.*

7. **A three-letter station code** (P467)

   Write a function `station_code(name)` that returns the first three
   characters of the name in capitals, or the whole name in capitals if it is
   shorter. A slice and upper().

   ```
   station_code("Market Square") -> "MAR"
   ```

   *Return: a str.*

8. **Good morning, good afternoon, good evening** (P468)

   Write a function `greeting(name, hour)` that returns 'Good morning, Hamid'
   before 12, 'Good afternoon, ...' from 12 up to but not including 18, and
   'Good evening, ...' from 18. An if/elif/else on the hour inside one
   f-string.

   ```
   greeting("Rosa", 12) -> "Good afternoon, Rosa"
   ```

   *Return: a str.*

9. **Today, tomorrow, in 3 days** (P469)

   Write a function `due_label(days)` that says when a payment is due: 'today'
   for 0, 'tomorrow' for 1, and 'in 3 days' (with the number) for anything
   more. Two special cases, then the general one.

   ```
   due_label(3) -> "in 3 days"
   ```

   *Return: a str.*

10. **A ride in one line** (P470)

    Write a function `ride_summary(start, end, minutes)` that returns 'Harbour
    to Stadium (32 min)': the two stations joined by ' to ', then the minutes
    in brackets with 'min'. One f-string.

    ```
    ride_summary("Harbour", "Stadium", 32) -> "Harbour to Stadium (32 min)"
    ```

    *Return: a str.*

## 3 - Checks and filters (5)

len(set()) <= 1 so the empty day counts, index() only after `in`, two positions
swapped on a copy, n == 0 tested before a negative slice, and zip() into
f-strings rather than tuples.

11. **Did the bike stay put all day?** (P471)

    Write a function `all_same(stops)` that returns True when every stop is
    the same station, and True for an empty list too (nothing differs). The
    number of DIFFERENT values is the thing to test.

    ```
    all_same(["Harbour", "Harbour", "Harbour"]) -> True
    ```

    *Return: True or False.*

12. **The stops before the bike reached Harbour** (P472)

    Write a function `until(stops, station)` that returns the stops before the
    station's first appearance -- not including it -- or the whole list if the
    station never appears. A membership test, then index() and a slice.

    ```
    until(["Parkway", "Stadium", "Harbour", "Hilltop"], "Harbour") -> ["Parkway", "Stadium"]
    ```

    *Return: a list of str.*

13. **The first and last stops swapped** (P473)

    Write a function `swap_ends(stops)` that returns a NEW list with the first
    and last stops exchanged and the middle unchanged; a list of one or none
    comes back as a copy. Copy the list, then assign to positions 0 and -1 in
    one tuple assignment.

    ```
    swap_ends(["Harbour", "Stadium", "Parkway"]) -> ["Parkway", "Stadium", "Harbour"]
    ```

    *Return: a list of str.*

14. **The last few stops** (P474)

    Write a function `last_stops(stops, n)` that returns the last n stops --
    all of them if there are fewer than n, and [] when n is 0. A negative
    slice is the natural tool, but one value of n needs care.

    ```
    last_stops(["Harbour", "Stadium", "Parkway", "Hilltop"], 2) -> ["Parkway", "Hilltop"]
    ```

    *Return: a list of str.*

15. **Each leg of the day, start to end** (P475)

    Two lists of the same length give each ride's start and end station. Write
    a function `legs(starts, ends)` that returns one string per ride, 'Harbour
    -> Stadium'. zip() pairs the lists up; an f-string makes each string. If
    the lists differ in length, stop at the shorter.

    ```
    legs(["Harbour", "Stadium"], ["Stadium", "Parkway"]) -> ["Harbour -> Stadium", "Stadium -> Parkway"]
    ```

    *Return: a list of str.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,651 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
