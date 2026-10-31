# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
fifth set on it, at two tools per question with the tiers named by task,
on tools no bike set had used, and three writable questions of one
statement each. **Fifteen Python**, every one a function over the SAME
list of bike dicts -- seven bikes with a model, dates, a ride count,
kilometres and the stations reached -- ramping from one line through one
loop to two steps.

| Stage | SQL questions |
|---|---|
| 1 - Reach and traffic | 1-3 |
| 2 - Averages, done right | 4-6 |
| 3 - Between events | 7-9 |
| 4 - Names, pairs and first months | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - One line | 1-5 |
| 2 - One loop | 6-10 |
| 3 - Two steps | 11-15 |

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
questions 13 to 15 is one DML statement with a trick in it.

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
script leaves behind: question 13 on the fares' total and the number of
free rides, 14 and 15 on the job count, the open jobs and how many bikes
have more than one open job.

| # | Construct |
|---|---|
| 13 | `UPDATE rides SET fare_cents = 0 FROM members m WHERE rides.member_id = m.member_id AND m.plan = 'annual' AND ...` |
| 14 | `INSERT INTO maintenance (bike_id, station_id, reported_at, kind, cost_cents) SELECT ... FROM bikes b WHERE ... AND NOT EXISTS (...)` |
| 15 | `DELETE FROM maintenance WHERE job_id IN (SELECT job_id FROM (SELECT job_id, ROW_NUMBER() OVER (...) AS rn FROM maintenance WHERE fixed_at IS NULL) WHERE rn > 1)` |

## Things the data does on purpose

- **147 of the 237 centre members have started from all three centre
  stations**, which question 1's division finds; the same trick on bikes would
  say little, since only 3 bikes have not ended at every station.
- **Three months of 2026 had no battery job**, so a plain GROUP BY gives
  question 2 twenty-seven cells and the CROSS JOIN gives thirty, 3 of them
  zero.
- **The classic's median ride is 2,322 metres against a mean of 3,317**: the
  long rides pull every average up, which is the gap question 4 measures and
  the reason question 5's integer division loses so much.
- **64 fixed jobs were never followed by a ride**, so question 8's subquery
  returns NULL for them and AVG leaves them out; a bike that is ridden again
  goes out within four to five days of its fix.
- **49 members are called Xiu**, the commonest first name, which a fixed-
  length SUBSTR splits three ways in question 10; 4 stations opened on the
  scheme's first day, question 11's six pairs.
- **530 of the 900 members joined before the rides begin in 2025**, so their
  first thirty days hold no ride at all, and question 12's per-member figure
  is honest only with the condition in ON.
- **18 bikes have more than one open job, 23 jobs between them**, which
  question 15 removes; 19 of the 29 cargo bikes in service have no open job,
  which question 14 opens one on; and 22 short June rides by annual members
  were charged, against 264 by members of any plan, the difference question
  13's FROM clause makes.
- **The data ends at 2026-06-30 23:59**, with 35 rides still out and 114 jobs
  open.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, 2024 is not "2024",
and 0 is not False. A function that prints its answer instead of returning
it returns None, and None matches nothing. All fifteen work the same data:
the prompt of question 1 describes a list called BIKES, seven dicts with
bike_id, model, acquired, retired (None while in service), rides, km and
stations, and Run passes your function that list, parts of it, or one bike
from it. Questions 1 to 5 are one expression each, 6 to 10 one loop each,
11 to 15 a loop and then a second step. Where a tool needs an import, the
question says the line to write.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Reach and traffic (3)

Relational division as a count compared with a count, a CROSS JOIN that builds
the grid before a LEFT JOIN fills it, and UNION ALL, which keeps the rows UNION
would fold together.

1. **Riders who know their whole zone** (Q1132)

   For each zone: how many members have a home station in it, and how many of
   THOSE have started a ride from EVERY station of the zone. Relational
   division: a CTE counting the stations per zone, a CTE of the (member, home
   zone) pairs whose COUNT(DISTINCT start station in that zone) equals the
   zone's count, then one row per zone.

   *Return: zone, members, complete*

2. **Every kind, every month, zeros included** (Q1133)

   For each month of 2026 and each of the five kinds of job: how many jobs
   were reported, with 0 where there were none. A CROSS JOIN of the distinct
   months -- strftime('%Y-%m', reported_at) for 2026 -- and the distinct kinds
   makes the full grid of thirty; a LEFT JOIN of maintenance onto it and
   COUNT(job_id) fills it in.

   *Return: month, kind, jobs*

3. **Each station's traffic, both ends counted** (Q1134)

   For every station: the rides that started there, the rides that ended
   there, and the two added together. A UNION ALL of (start_station_id, 1 AS
   starts, 0 AS ends) from every ride and (end_station_id, 0, 1) from the
   finished ones, then one GROUP BY over the stacked rows, joined to stations
   for the name.

   *Return: name, starts, ends, traffic*

## 2 - Averages, done right (3)

A median from ROW_NUMBER and COUNT over the same partition, division by 1000.0
after the average rather than by 1000 inside it, and a VALUES CTE joined with an
ON like any table.

4. **The middle ride of each model** (Q1135)

   For each model: the MEDIAN distance of its finished rides, in metres.
   SQLite has no MEDIAN: in a CTE give every ride ROW_NUMBER() OVER (PARTITION
   BY model ORDER BY distance_m) and COUNT(*) OVER (PARTITION BY model), keep
   the rows numbered (n + 1) / 2 and (n + 2) / 2 -- the same row when n is
   odd, the two middle ones when it is even -- and AVG them per model.

   *Return: model, median_m*

5. **Kilometres per ride, by zone** (Q1136)

   For each zone, of the start station: the average distance of its finished
   rides in KILOMETRES, to two decimals. Average the metres, then divide by
   1000.0 -- distance_m / 1000 inside the AVG is integer division, which
   throws away the fraction of every ride before the average is taken.

   *Return: zone, avg_km*

6. **What distance pricing would have raised** (Q1137)

   A tariff that exists nowhere in the database: 40 cents per kilometre on a
   classic, 60 on an electric, 80 on a cargo bike. Write it as a CTE of
   literal rows -- WITH tariff(model, cents_per_km) AS (VALUES ('classic',
   40), ('electric', 60), ('cargo', 80)) -- join it to bikes ON model, and for
   each model return what the tariff would have charged for the finished
   rides, in dollars to two decimals (distance_m / 1000.0 * cents_per_km,
   summed, / 100), beside what their fares actually came to.

   *Return: model, by_distance, charged*

## 3 - Between events (3)

A RANGE frame that counts days back rather than rows, computed before the
filter; a correlated scalar subquery in the SELECT list; and LEAD, whose NULL on
the last row COUNT(column) skips.

7. **A week's worth of rides, by the clock** (Q1138)

   For each ride bike 7 started in June 2026: how many rides the bike had
   started in the SEVEN DAYS before it. A RANGE frame over
   julianday(started_at): COUNT(*) OVER (ORDER BY julianday(started_at) RANGE
   BETWEEN 7 PRECEDING AND CURRENT ROW) - 1, computed over ALL of bike 7's
   rides in a CTE and filtered to June afterwards -- the ride of 6 June has
   one of 31 May in its week.

   *Return: ride_id, started_at, prior_week*

8. **How soon a mended bike goes out again** (Q1139)

   For each kind of job: how many have been fixed, and the average DAYS from
   the fix to the bike's next ride, to two decimals. A correlated scalar
   subquery in the SELECT list finds the next ride -- (SELECT MIN(started_at)
   FROM rides r WHERE r.bike_id = m.bike_id AND r.started_at > m.fixed_at) --
   and julianday of that minus julianday(fixed_at) is the wait. The 64 fixes
   never followed by a ride give NULL, which AVG skips.

   *Return: kind, fixed, avg_days*

9. **Days until the bike is back in the shop** (Q1140)

   For each kind of job: how many jobs of that kind were followed by another
   job on the same bike, and the average days until that next job, to one
   decimal. LEAD(reported_at) OVER (PARTITION BY bike_id ORDER BY reported_at)
   in a CTE puts the next job's date on each row; COUNT of that column counts
   only the rows that have one, and the last job on every bike has none.

   *Return: kind, followed, avg_days*

## 4 - Names, pairs and first months (3)

SUBSTR cut at INSTR's space rather than at a fixed length, a self-join with < so
each pair comes once, and a LEFT JOIN whose condition lives in ON because WHERE
would make it inner.

10. **The first names the scheme is full of** (Q1141)

    The first names shared by 38 or more members, with the count. The first
    name is everything before the first space: SUBSTR(name, 1, INSTR(name, '
    ') - 1), grouped on.

    *Return: first_name, members*

11. **Stations that opened together** (Q1142)

    Every pair of stations that opened on the same day, each pair once, by
    name. A self-join of stations on opened_on with a.station_id <
    b.station_id, so that a station is never paired with itself and (Market
    Square, Cathedral) does not come back again as (Cathedral, Market Square).

    *Return: first, second*

12. **The first month of membership** (Q1143)

    For each plan: its members, the rides they took in their first thirty days
    -- started_at before date(joined_on, '+30 days') -- and the rides per
    member, to two decimals. The thirty-day condition belongs in the LEFT
    JOIN's ON clause: in WHERE it drops every member without such a ride, and
    the per-member figure is for the keen ones only.

    *Return: plan, members, first_month_rides, per_member*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. One statement each: UPDATE ... FROM,
INSERT ... SELECT behind NOT EXISTS, and a DELETE whose ROW_NUMBER runs over
open jobs only.

13. **Short rides go free for annual members** (Q1144)

    From June 2026 an annual member's ride under five kilometres is free. ONE
    statement: UPDATE rides SET fare_cents = 0 FROM members m WHERE the ride's
    member_id is m.member_id, m.plan is 'annual', distance_m < 5000,
    started_at >= '2026-06-01' and fare_cents > 0. The FROM clause joins
    another table into an UPDATE, so the plan can be tested without a
    subquery.

    *Checked: the fares' total, and how many rides are free*

14. **A brake check for every cargo bike without a job** (Q1145)

    Open a 'brakes' job on every cargo bike still in the fleet that has NO
    open job: INSERT INTO maintenance (bike_id, station_id, reported_at, kind,
    cost_cents) SELECT ... FROM bikes b WHERE the model is 'cargo', retired_on
    IS NULL and NOT EXISTS an open job for b.bike_id -- at station 1, reported
    '2026-07-01 09:00', cost 0. job_id numbers itself and fixed_at stays NULL,
    which is what makes the job open.

    *Checked: how many jobs there are, how many open brakes jobs, and how many bikes have more than one open job*

15. **One open job per bike** (Q1146)

    Where a bike has more than one open job, keep the EARLIEST by reported_at
    and delete the rest. DELETE FROM maintenance WHERE job_id IN (...) with a
    subquery that numbers the OPEN jobs -- ROW_NUMBER() OVER (PARTITION BY
    bike_id ORDER BY reported_at), in a subquery whose WHERE keeps fixed_at IS
    NULL -- and returns the job_ids numbered above 1. The numbering must run
    over open jobs only: numbered over every job, a bike's only open job can
    be its third and go.

    *Checked: how many jobs remain, how many are open, and how many bikes still have more than one open job*

# Python

## 1 - One line (5)

One expression each over the bike dicts: a comprehension that yields ids rather
than rows, a sum that keeps the retired bikes, a None test before a string
comparison, a division behind a guard, and all() against any().

1. **The bikes of one model** (P401)

   BIKES is a list of dicts, one per bike, with keys bike_id, model, acquired,
   retired (None while the bike is in the fleet), rides, km and stations (the
   station ids the bike has reached, in the order it first reached them).
   Write a function `ids_by_model(bikes, model)` that returns the bike_ids of
   the bikes of that model, in list order. One list comprehension with an if.

   ```
   ids_by_model(BIKES, "classic") -> [1, 2, 7]
   ```

   *Return: a list of ints, possibly empty.*

2. **How far the fleet has gone** (P402)

   Write a function `fleet_km(bikes)` that returns the kilometres every bike
   has ridden, added up and rounded to one decimal -- retired bikes included,
   since their kilometres were ridden. sum() over a generator, inside round().

   ```
   fleet_km(BIKES) -> 3682.0
   ```

   *Return: a float.*

3. **How many bikes were in the fleet that day** (P403)

   Write a function `in_service_on(bikes, day)` that returns how many bikes
   were in the fleet on that day: acquired on or before it, and either not
   retired or retired after it. Dates are ISO strings, so < and <= compare
   them correctly. One sum() of a generator with the two conditions; the
   retired test has to check for None FIRST, because None < "2026" is a
   TypeError.

   ```
   in_service_on(BIKES, "2026-06-30") -> 5
   ```

   *Return: an int.*

4. **Kilometres per ride** (P404)

   Write a function `km_per_ride(bike)` that returns one bike's kilometres
   divided by its rides, rounded to two decimals -- or None for a bike with no
   rides. A conditional expression: round(...) if bike["rides"] else None.

   ```
   km_per_ride(BIKES[0]) -> 2.95
   ```

   *Return: a float, or None.*

5. **Has every bike been there?** (P405)

   Write a function `all_visited(bikes, station)` that returns True when EVERY
   bike in the list has reached that station -- `station in b["stations"]` for
   all of them -- and False otherwise. all() over a generator; all() of
   nothing is True.

   ```
   all_visited(BIKES, 5) -> False
   ```

   *Return: True or False.*

## 2 - One loop (5)

A set that update()s, an intersection that starts full, a count whose tie goes
to the smallest key rather than the first seen, a date span with `retired or
today`, and a key derived by slicing -- as an int, not a string.

6. **Every station anyone has reached** (P406)

   Write a function `all_stations(bikes)` that returns every station id any of
   the bikes has reached, each once, in ascending order. A loop that update()s
   a set with each bike's stations, then sorted().

   ```
   all_stations(BIKES) -> [1, 2, 3, 5, 7, 9, 11]
   ```

   *Return: a sorted list of ints.*

7. **The stations every bike has reached** (P407)

   Write a function `common_stations(bikes)` that returns the station ids
   EVERY bike in the list has reached, in ascending order, and [] for an empty
   list. Start from the first bike's stations as a set and intersect (`&=` or
   intersection_update) with each of the others.

   ```
   common_stations([BIKES[0], BIKES[2], BIKES[4]]) -> [5]
   ```

   *Return: a sorted list of ints.*

8. **The station most bikes have reached** (P408)

   Write a function `busiest_station(bikes)` that returns the station id that
   appears in the most bikes' station lists, the SMALLEST id when several tie,
   or None when no bike has reached anywhere. A loop counting each station
   into a dict, then the best: the highest count, and among those the lowest
   id.

   ```
   busiest_station(BIKES) -> 5
   ```

   *Return: an int, or None.*

9. **The bike that has served longest** (P409)

   Write a function `longest_lived(bikes, today)` that returns the bike_id of
   the bike with the most days between its acquisition and its retirement --
   or `today` if it has not retired -- and None for an empty list. Write `from
   datetime import date` and use date.fromisoformat() on both strings;
   subtracting two dates gives a timedelta whose .days is the span. A loop
   keeping the best so far.

   ```
   longest_lived(BIKES, "2026-06-30") -> 3
   ```

   *Return: an int, or None.*

10. **How many bikes arrived each year** (P410)

    Write a function `acquired_by_year(bikes)` that returns a dict mapping
    each year, as an INT, to how many bikes were acquired in it. The year is
    the first four characters of the acquired string, so
    int(b["acquired"][:4]) is the key; a loop with get(key, 0) + 1.

    ```
    acquired_by_year(BIKES) -> {2022: 2, 2023: 2, 2024: 1, 2025: 2}
    ```

    *Return: a dict of int to int.*

## 3 - Two steps (5)

Aggregate, then pick: two running values in a list, a tuple key that sorts down
then up, count and count-if per key then round(x, 1), a band key from // and *,
and an average that needs the count as well as the sum.

11. **Bikes and kilometres per model** (P411)

    Write a function `model_summary(bikes)` that returns a dict mapping each
    model to a two-item LIST: how many bikes of that model there are and their
    kilometres added up, the km rounded to one decimal at the end. A loop that
    creates [0, 0.0] for a model the first time it is seen and then adds to
    both items; a second pass rounds the km.

    ```
    model_summary(BIKES) -> {"classic": [3, 1092.7], "electric": [2, 2493.3], "cargo": [2, 96.0]}
    ```

    *Return: a dict of str to [int, float].*

12. **The most-ridden bikes** (P412)

    Write a function `top_n(bikes, n)` that returns the bike_ids of the n
    most-ridden bikes, most rides first, a tie going to the LOWER bike_id.
    sorted() with key=lambda b: (-b["rides"], b["bike_id"]), then take the
    first n and keep only the ids.

    ```
    top_n(BIKES, 3) -> [3, 5, 1]
    ```

    *Return: a list of ints, possibly empty.*

13. **What share of each model has retired** (P413)

    Write a function `retired_share(bikes)` that returns a dict mapping each
    model to the percentage of its bikes that have retired, to one decimal.
    Two counts per model -- all bikes, retired bikes -- then a second pass
    dividing: 100 * retired / total, rounded to 1.

    ```
    retired_share(BIKES) -> {"classic": 33.3, "electric": 50.0, "cargo": 0.0}
    ```

    *Return: a dict of str to float.*

14. **Rides in bands of a hundred** (P414)

    Write a function `rides_histogram(bikes, width)` that returns a dict
    mapping the START of each band of that width to how many bikes fall in it:
    a bike with 140 rides is in band 100 when the width is 100 (140 // 100 *
    100) and in band 100 when it is 50 too; a bike with 0 rides is in band 0.
    A loop with get(band, 0) + 1; bands no bike falls in are absent.

    ```
    rides_histogram(BIKES, 100) -> {100: 2, 0: 3, 300: 1, 200: 1}
    ```

    *Return: a dict of int to int.*

15. **The model that goes furthest per bike** (P415)

    Write a function `best_model(bikes)` that returns the model with the
    highest AVERAGE kilometres per bike -- the model's km added up, divided by
    how many bikes it has -- or None for an empty list. First a loop
    accumulating km and count per model, then max() over the models with a key
    that divides the two.

    ```
    best_model(BIKES) -> "electric"
    ```

    *Return: a str, or None.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,531 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
