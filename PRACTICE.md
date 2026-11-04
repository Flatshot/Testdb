# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
eighth set on it, at two tools per question with the tiers named by task,
on tools no bike set had used, and three writable questions. From this set
on the prompts name the tool but do not write the statement. **Fifteen
Python**, easier by request: everyday tasks over plain lists and strings,
with no maths beyond adding and taking away and no dicts.

| Stage | SQL questions |
|---|---|
| 1 - Nearest and next | 1-3 |
| 2 - Text and type | 4-6 |
| 3 - Per group, per station | 7-9 |
| 4 - Ratios and buckets | 10-12 |
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
instead is constraints, triggers, views and DDL -- and each of questions 13
to 15 is one of those.

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

**Driver statements.** Question 13 runs two DELETEs against your view
*after* your script, and question 15 runs three INSERTs, the last of
which the table must refuse. The probes read what the triggers and the
defaults left behind, so each refusal or fill-in shows. Question 14 is
graded on the table the script creates.

| # | Construct |
|---|---|
| 13 | `CREATE VIEW open_jobs AS ...; CREATE TRIGGER ... INSTEAD OF DELETE ON open_jobs BEGIN UPDATE maintenance ... WHERE job_id = OLD.job_id; END` |
| 14 | `CREATE TABLE bike_stats AS SELECT ..., (SELECT COUNT(*) FROM rides ...) AS rides, (SELECT COUNT(*) FROM maintenance ...) AS jobs FROM bikes` |
| 15 | `CREATE TABLE incidents (..., status TEXT NOT NULL DEFAULT 'open' CHECK (...), cost_cents INTEGER NOT NULL DEFAULT 0 ...)` |

## Things the data does on purpose

- **Old Mill, closed since March 2026, is still the south's runner-up**, with
  2,500 rides to the Stadium's more; question 1's NTH_VALUE finds it only once
  the frame is opened to the whole zone.
- **Bike 2 has 43 rides against about 121 for a classic**, the comparison
  question 2 makes with the bike itself left out of the average.
- **Only 7 of members 1 to 10 have ever ridden**, so question 3 returns seven
  rows, one per member, and none for the rest.
- **45 members are called Uddin**, found by question 5 only when the
  comparison ignores case; question 6 finds 35 NULL distances, the rides still
  out, and 11,513 rides with no member.
- **Every rider's first ride falls in the first five months of the data, 584
  of them in January 2025**, so question 8 has five rows and its running total
  ends at the 800 members who have ever ridden.
- **With 25 surnames across 900 members, sharing one is common**: 1,354 pairs
  of members share a surname and a home station, question 9's count, which a
  <> in the join would double.
- **Casual riders pay 79.21 cents a kilometre as a ratio of sums**, and 173.62
  as an average of each ride's own rate, the gap question 10 is about: short
  rides at a minimum fare have wild rates.
- **12 bikes have never had a job and 7 have never been ridden**, which
  question 14's snapshot must still list; joined to both tables at once, the
  counts multiply to about 130,000 each.
- **The data ends at 2026-06-30 23:59**, with 35 rides still out and 114 jobs
  open, two of which question 13 closes.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, and 0 is not False. A
function that prints its answer instead of returning it returns None, and
None matches nothing. The inputs are everyday values: a list of station
names or bike ids for questions 1 to 5, a name or a message for 6 to 10, a
list of minutes, stops, codes or ids for 11 to 15. Each prompt shows one
example call with its answer, and Run adds a few more, including the empty
list or the edge the question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Nearest and next (3)

NTH_VALUE, whose default frame stops at the current row; EXCLUDE CURRENT ROW,
which leaves a row out of its own comparison; and a correlated MAX for the
latest row per group.

1. **The runner-up station in each zone** (Q1177)

   For each zone: the station with the SECOND most rides started there, and
   that count. Count rides per station in a CTE, then NTH_VALUE over a window
   partitioned by zone; the frame has to be opened to the whole partition, or
   the first row of each zone cannot see its runner-up.

   *Return: zone, runner_up, rides*

2. **Each bike against its model-mates** (Q1178)

   For bikes 1 to 10: the model, the bike's rides, and the average rides of
   the OTHER bikes of that model, to one decimal. A window frame over the
   whole partition with EXCLUDE CURRENT ROW leaves the bike itself out of its
   own comparison. Count over every bike first, including the ones never
   ridden, and filter to 1 to 10 afterwards.

   *Return: bike_id, model, rides, others_avg*

3. **Each member's latest ride** (Q1179)

   For members 1 to 10 who have ridden: the ride_id and start of their most
   recent ride. No window function: a correlated scalar subquery in WHERE that
   finds the member's latest started_at, matched against the row's own.

   *Return: member_id, ride_id, started_at*

## 2 - Text and type (3)

MIN and MAX on text rather than on ids, COLLATE NOCASE on a comparison, and
typeof, which reports the type of each VALUE and counts NULL as one.

4. **First and last in the register, by plan** (Q1180)

   For each plan: the member whose name comes first alphabetically and the one
   whose name comes last. MIN and MAX work on text as well as numbers.

   *Return: plan, first_name, last_name*

5. **The Uddins, however the name was typed** (Q1181)

   Every member whose surname is Uddin, found with the search term typed in
   lower case: 'uddin'. The surname is the text after the first space; compare
   it with COLLATE NOCASE so that case does not matter.

   *Return: member_id, name*

6. **What the rides table actually holds** (Q1182)

   For three columns of rides -- distance_m, member_id and fare_cents -- the
   storage types found in them and how many rows hold each. typeof() names a
   value's type, and NULL is one of them; one GROUP BY per column, stacked.

   *Return: column_name, storage_type, rows*

## 3 - Per group, per station (3)

ORDER BY and LIMIT inside a correlated subquery, a MIN per member before
anything is counted per month, and a self-join on two conditions with < to count
each pair once.

7. **The three latest jobs at each station** (Q1183)

   For every station: its three most recently reported jobs. No window
   function: a subquery correlated on station_id with its own ORDER BY and
   LIMIT 3, used as an IN list of job_ids.

   *Return: station_id, job_id, reported_at*

8. **New riders by month, and the running total** (Q1184)

   For each month in which some member took their FIRST ride: how many members
   did, and how many members had ridden by the end of that month. A CTE of
   each member's first ride month, a count per month, and a running SUM over
   the months.

   *Return: month, new_riders, riders_so_far*

9. **Family at the same station** (Q1185)

   For every station: how many PAIRS of its members share a surname. A self-
   join of members on two conditions, the home station and the surname (the
   text after the first space), each pair counted once.

   *Return: name, pairs*

## 4 - Ratios and buckets (3)

A rate as total over total rather than an average of rates, GROUP BY on a
comparison, and (month + 2) / 3 in integer arithmetic.

10. **What a kilometre costs, by plan** (Q1186)

    For each plan, with the casual riders as a fourth group labelled 'casual':
    the fare per kilometre in cents, to two decimals, over the finished rides.
    A ratio of SUMS -- all the fares over all the distance -- not an average
    of each ride's own ratio.

    *Return: plan, cents_per_km*

11. **Members and casuals, model by model** (Q1187)

    For each model and, within it, members against casual riders: the finished
    rides and their average length in minutes to one decimal. GROUP BY the
    model and a BOOLEAN expression -- whether member_id is NULL -- rather than
    a column; six rows.

    *Return: model, casual, rides, avg_minutes*

12. **Rides and fares by quarter** (Q1188)

    For each quarter in the data, labelled '2025-Q1' and so on: the rides, and
    the fares in dollars. The quarter number comes from the month by integer
    arithmetic -- think about what to add before dividing by three so that
    months 1 to 3 give 1 and 10 to 12 give 4.

    *Return: quarter, rides, fares*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. An INSTEAD OF trigger on a view, CREATE
TABLE ... AS SELECT without the two-join fan-out, and DEFAULTs behind NOT NULL.

13. **Deleting from the open-jobs view closes the job** (Q1189)

    Create a view named open_jobs of the maintenance rows whose fixed_at is
    NULL, then a trigger INSTEAD OF DELETE on that view that, rather than
    deleting anything, sets the job's fixed_at to '2026-07-01 09:00'. The
    question then deletes jobs 9 and 19 from the view.

    *Checked: job 9's fixed_at, how many jobs there are, and how many are open*

14. **A snapshot table of every bike's record** (Q1190)

    Make a table named bike_stats from a query, in one statement: for every
    bike, including the ones never ridden or never repaired, its bike_id,
    model, how many rides it has had and how many maintenance jobs. The
    columns must be called bike_id, model, rides and jobs. Two independent
    counts from two tables for one bike is a place where a single query with
    two joins goes wrong.

    *Checked: how many rows the new table has, and the rides and jobs added up*

15. **A table that fills in what you leave out** (Q1191)

    Create a table incidents with: incident_id as the integer primary key;
    bike_id, required and referencing bikes; reported_on, text, required,
    defaulting to '2026-07-01'; status, text, required, defaulting to 'open'
    and allowed only 'open' or 'closed'; cost_cents, integer, required,
    defaulting to 0 and never negative. The question then inserts three rows:
    one giving only a bike_id, one giving every column, and one with a status
    of 'lost', which must be refused.

    *Checked: the rows that got in, all five columns*

# Python

## 1 - Counting and finding (5)

enumerate() for every position, a counter that returns on the n-th match and -1
after the loop, `not in` to keep the order, `in` before index(), and split()
before len().

1. **Every time the bike stopped at Harbour** (P446)

   A day's stops are a list of station names. Write a function
   `positions_of(stops, station)` that returns every position at which the
   station appears, in order, counting from 0. enumerate() gives each stop
   with its position.

   ```
   positions_of(["Harbour", "Stadium", "Harbour", "Parkway", "Harbour"], "Harbour") -> [0, 2, 4]
   ```

   *Return: a list of ints, possibly empty.*

2. **The second visit** (P447)

   Write a function `nth_visit(stops, station, n)` that returns the position
   of the n-th time the station appears (n = 1 for the first), or -1 if it
   does not appear that many times. A loop with a counter that goes up on each
   match and returns the position when it reaches n.

   ```
   nth_visit(["Harbour", "Stadium", "Harbour", "Parkway", "Harbour"], "Harbour", 2) -> 2
   ```

   *Return: an int.*

3. **The bikes that did not come back** (P448)

   Two lists of bike ids: the ones that went out this morning, in the order
   they left, and the ones back by closing. Write a function
   `not_returned(out, back)` that returns the ids that went out and are not
   back, in the order they went out. A comprehension with `not in`.

   ```
   not_returned([12, 7, 30, 4], [4, 12]) -> [7, 30]
   ```

   *Return: a list of ints.*

4. **Did it reach Harbour before Stadium?** (P449)

   Write a function `reached_before(stops, a, b)` that returns True when
   station a appears in the list before station b, and False otherwise --
   including when either is missing. Check that both are present before
   comparing their index() positions.

   ```
   reached_before(["Parkway", "Harbour", "Stadium"], "Harbour", "Stadium") -> True
   ```

   *Return: True or False.*

5. **How many words in the name** (P450)

   Write a function `word_count(name)` that returns how many words a station
   name has. split() with no argument breaks on any run of spaces and ignores
   spaces at the ends, and len() counts the pieces.

   ```
   word_count("Station Approach") -> 2
   ```

   *Return: an int.*

## 2 - Labels (5)

A guard for the one-word name, a different separator before the last name,
lower() before testing the first letter, a flag that is actually consulted, and
an if that picks the label's shape.

6. **A name shortened for a badge** (P451)

   Write a function `badge_name(name)` that returns the first initial, a dot,
   a space and the last word of the name: 'H. Uddin'. A name with no space is
   returned as it is.

   ```
   badge_name("Hamid Uddin") -> "H. Uddin"
   ```

   *Return: a str.*

7. **A list of names, with an 'and'** (P452)

   Write a function `with_and(names)` that joins names the way a sentence
   would: 'Hamid, Rosa and Yusuf', 'Hamid and Rosa', just 'Hamid' for one, and
   '' for none. Join all but the last with ', ', then add ' and ' and the
   last.

   ```
   with_and(["Hamid", "Rosa", "Yusuf"]) -> "Hamid, Rosa and Yusuf"
   ```

   *Return: a str.*

8. **Does the name start with a vowel?** (P453)

   Write a function `starts_with_vowel(name)` that returns True when the name
   begins with a vowel, in either case, and False otherwise -- including for
   an empty string. Guard against the empty string first, then test the first
   character, lower-cased, against the five vowels.

   ```
   starts_with_vowel("Aisha") -> True
   ```

   *Return: True or False.*

9. **Shout it if it is urgent** (P454)

   Write a function `announce(message, urgent)` that returns the message in
   capitals with an exclamation mark on the end when urgent is True, and the
   message unchanged otherwise. A conditional expression.

   ```
   announce("bike 7 is missing", True) -> "BIKE 7 IS MISSING!"
   ```

   *Return: a str.*

10. **Minutes as hours and minutes** (P455)

    Write a function `duration_label(minutes)` that returns '32 min' for under
    an hour and '1 h 5 min' from an hour up: whole hours by // 60 and the
    minutes left by % 60, with an if on whether there is an hour at all.

    ```
    duration_label(65) -> "1 h 5 min"
    ```

    *Return: a str.*

## 3 - Checks and filters (5)

A tuple returned, not a list of two; a guard before [0] and [-1]; the length
test first so `and` stops early; strip() as well as upper(); and <= at both ends
of the range.

11. **Short rides and long rides, sorted into two piles** (P456)

    Write a function `split_by_length(minutes, limit)` that returns TWO lists
    as a tuple: the rides of limit minutes or less, and the rides over it,
    each in the original order. Two comprehensions, or one loop that appends
    to one list or the other.

    ```
    split_by_length([12, 45, 30, 31, 7], 30) -> ([12, 30, 7], [45, 31])
    ```

    *Return: a tuple of two lists.*

12. **Where the day began and ended** (P457)

    Write a function `ends_of_day(stops)` that returns the first and last stop
    as a tuple, or None for a day with no stops. A guard, then indexes 0 and
    -1.

    ```
    ends_of_day(["Harbour", "Stadium", "Parkway"]) -> ("Harbour", "Parkway")
    ```

    *Return: a tuple of two str, or None.*

13. **Was it a round trip?** (P458)

    Write a function `is_round_trip(stops)` that returns True when a day's
    stops begin and end at the same station and there are at least two stops,
    and False otherwise. Two tests joined with and, the length first.

    ```
    is_round_trip(["Harbour", "Stadium", "Harbour"]) -> True
    ```

    *Return: True or False.*

14. **Bike codes typed by hand, tidied** (P459)

    Codes come in from a form with stray spaces and mixed case. Write a
    function `clean_codes(codes)` that returns each code stripped of spaces at
    the ends and in capitals, in the same order, repeats kept. One
    comprehension applying both methods.

    ```
    clean_codes([" bk-07 ", "BK-12", "bk-07"]) -> ["BK-07", "BK-12", "BK-07"]
    ```

    *Return: a list of str.*

15. **Only the ids the fleet actually has** (P460)

    The fleet's bike ids run from 1 to a highest id. Write a function
    `valid_ids(ids, highest)` that keeps only the ids in that range, in the
    original order. A comprehension with a chained comparison, 1 <= i <=
    highest.

    ```
    valid_ids([0, 5, 320, 321, 12], 320) -> [5, 320, 12]
    ```

    *Return: a list of ints.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,621 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
