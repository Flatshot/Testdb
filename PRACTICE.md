# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on a NEW schema -- a city
bike-hire scheme, replacing the library -- at two tools per question, with
the tiers named by task and three writable questions that each take two
steps. **Fifteen Python** functions each built around one simple for or
while loop over plain numbers or strings, with no imports and the examples
drawn from the scheme.

| Stage | SQL questions |
|---|---|
| 1 - Riding the network | 1-3 |
| 2 - Riders and fares | 4-6 |
| 3 - The fleet | 7-9 |
| 4 - Money | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Counting | 1-4 |
| 2 - Searching | 5-8 |
| 3 - Building | 9-12 |
| 4 - Reducing | 13-15 |

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

**Driver statements.** Question 13 runs two inserts of its own *after* your
script -- a ride on a bike that is out and one on a bike that is docked.
Questions 14 and 15 are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `BEFORE INSERT ON rides WHEN EXISTS (SELECT 1 FROM rides r WHERE r.bike_id = NEW.bike_id AND r.ended_at IS NULL) BEGIN SELECT RAISE(ABORT, ...); END` |
| 14 | `UPDATE rides SET ended_at = ..., end_station_id = start_station_id, distance_m = 0, fare_cents = CASE WHEN member_id IS NULL THEN 200 ELSE 0 END WHERE ended_at IS NULL` |
| 15 | `CREATE VIEW ride_minutes AS ...; CREATE VIEW member_minutes AS SELECT ... FROM ride_minutes WHERE member_id IS NOT NULL GROUP BY member_id` |

## Things the data does on purpose

- **100 of the 900 members have never ridden**, and 86 have no
  district recorded -- the rows a LEFT JOIN keeps and an inner join loses.
- **7 of the 320 bikes have never been ridden and 18 are
  retired**; question 7's average per bike counts the first group as 0.
- **30 per cent of rides are by casual riders**, whose member_id is
  NULL -- a category, not a gap, and the test for it is IS NULL.
- **16 per cent of completed rides end where they began**, which is
  why question 1 excludes them from the routes.
- **59 per cent of members' rides cost nothing**, inside the free half
  hour; pay-as-you-go members pay for every ride, so question 6's list
  never names one.
- **220 monthly members have missed at least one payment** --
  found only by generating each member's due dates, which question 10 does
  by recursion.
- **96 of the 114 open maintenance jobs are on bikes that
  have been ridden since the report**, which question 8's EXISTS has to
  compare timestamps to see.
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
None matches nothing. Each question here is one simple loop -- a for or a
while -- with an if, a counter or a list built up inside it, and nothing to
import.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Riding the network (3)

The graph: a two-column GROUP BY under ROW_NUMBER for the busiest routes, two
scalar subqueries for a station's inflow and outflow where a double join would
multiply, and stations joined twice under two aliases packed into JSON.

1. **The ten busiest routes** (Q1072)

   The ten most ridden station-to-station routes, counting completed rides
   whose start and end stations differ: start station, end station, rides --
   ties by the lower start id, then end id. GROUP BY both stations, ROW_NUMBER
   over the counts, keep ten.

   *Return: start_station_id, end_station_id, rides*

2. **Where the bikes pile up** (Q1073)

   For each station: rides that started there, rides that ended there, and the
   difference, ends minus starts -- a positive number means bikes accumulate.
   Rides reference stations twice, so count each direction with its own scalar
   subquery rather than joining rides to stations.

   *Return: station_id, starts, ends, net*

3. **Zone to zone, as JSON** (Q1074)

   For each zone a ride can start in, a JSON object whose keys are the zones
   rides END in and whose values are the counts -- completed rides only. Join
   stations TWICE, under two aliases, for the start zone and the end zone;
   count per pair in a CTE; json_group_object grouped by the start zone.

   *Return: start_zone, by_end_zone*

## 2 - Riders and fares (3)

The NULL that is a category: AVG(member_id IS NULL) for the casual share,
minutes from julianday banded by CASE for casual fares, and HAVING with AVG of a
comparison for the members who ride free.

4. **How much of each month is casual** (Q1075)

   For each month rides started: how many rides, and the percentage by CASUAL
   riders -- member_id NULL -- to one decimal. strftime for the month, AVG of
   member_id IS NULL for the share.

   *Return: month, rides, pct_casual*

5. **What a casual ride costs, by length** (Q1076)

   Completed CASUAL rides banded by length in minutes -- 'under 10', '10 to
   30' (10 up to and including 30), 'over 30' -- with the count and the
   average fare in whole cents. Minutes are (julianday(ended_at) -
   julianday(started_at)) * 1440; the band is a CASE with the shortest band
   first.

   *Return: band, rides, avg_fare*

6. **The members who ride for free** (Q1077)

   The ten members with the highest share of free rides -- fare 0 -- among
   members with at least 10 completed rides, ties by lower member_id:
   member_id, rides, and the free share as a percentage to one decimal. HAVING
   on the count, AVG of the comparison, ORDER BY and LIMIT.

   *Return: member_id, rides, pct_free*

## 3 - The fleet (3)

A LEFT JOIN that keeps the bikes never ridden, an EXISTS that compares
timestamps for 'ridden since', and two children of a bike totalled by scalar
subqueries.

7. **Rides per bike, by model** (Q1078)

   For each model: how many bikes, and the average rides per bike to one
   decimal, counting a bike that has never been ridden as 0. A LEFT JOIN from
   bikes to rides, COUNT of the ride id over COUNT(DISTINCT bike_id).

   *Return: model, bikes, avg_rides*

8. **Jobs still open, and bikes that went out anyway** (Q1079)

   Every maintenance job still OPEN -- fixed_at NULL: job_id, bike_id, whole
   days since it was reported as of 2026-06-30 23:59, and 1 or 0 for whether
   the bike has started a ride SINCE the report. julianday for the days, an
   EXISTS over rides for the flag.

   *Return: job_id, bike_id, days_open, ridden_since*

9. **Maintenance cost per thousand rides** (Q1080)

   For each model: the total maintenance cost of its bikes in cents, its total
   rides, and the cost per THOUSAND rides as a whole number. Jobs and rides
   are two children of a bike, so total each with its own scalar subquery over
   the model.

   *Return: model, cost_cents, rides, cost_per_1000*

## 4 - Money (3)

A recursive calendar that carries a member id along, two conditional SUMs under
a running window SUM, and two LEFT JOINs with two COALESCEs to name a payer.

10. **Monthly members who have missed a payment** (Q1081)

    A monthly member owes 1,200 cents every 30 days from the day they joined.
    For each monthly member who has MISSED at least one payment due between
    2025-01-01 and 2026-06-30: member_id and how many due dates have no
    payment on that day. A recursive CTE generates each member's due dates,
    stepping date(d, '+30 days') from joined_on; a NOT EXISTS over payments
    with date(paid_at) = the due date finds the misses.

    *Return: member_id, missed*

11. **Revenue by month, fares against subscriptions** (Q1082)

    For each month payments were made: the fare revenue -- payments with a
    ride_id -- the subscription revenue -- payments with a member_id -- and
    the running total of ALL revenue so far, all in cents. Two conditional
    SUMs and a window SUM over their total, ordered by month.

    *Return: month, fares, subscriptions, running_total*

12. **Who pays by app** (Q1083)

    For each kind of payer -- 'annual', 'monthly', 'pay-as-you-go', or
    'casual' for a fare paid by a rider with no membership: how many payments,
    and the percentage made by app to one decimal. A fare payment reaches its
    member through its ride, so LEFT JOIN rides, then LEFT JOIN members on
    COALESCE(payments.member_id, rides.member_id), and COALESCE(plan,
    'casual') for the label.

    *Return: payer, payments, pct_app*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger whose WHEN looks for an open
ride of the same bike, an UPDATE that copies a column and chooses a fare by
CASE, and a view of minutes per ride under a view of minutes per member.

13. **One rider per bike** (Q1084)

    Write a BEFORE INSERT trigger on rides that refuses -- RAISE(ABORT, ...)
    -- a ride on a bike that is already OUT: a ride of the same bike with
    ended_at NULL exists. The question then starts a ride on bike 8, which is
    out, and on bike 1, which is docked.

    *Checked: the bike_ids of any rides added*

14. **Close the rides still out at the end of the data** (Q1085)

    Every ride with ended_at NULL is closed at '2026-06-30 23:59', returned to
    its own start station, with distance_m 0 and a fare of 200 cents for a
    CASUAL rider (member_id NULL) or 0 for a member. One UPDATE whose SET uses
    the row's own start_station_id and a CASE on member_id.

    *Checked: how many rides are still out, the fares the closed rides were charged, and how many of them end where they began*

15. **Minutes per ride, then minutes per member** (Q1086)

    Create a view `ride_minutes (ride_id, member_id, minutes)` of the
    COMPLETED rides with the ride's length in minutes -- (julianday(ended_at)
    - julianday(started_at)) * 1440 -- then a second view `member_minutes
    (member_id, rides, total_minutes)` that reads ride_minutes, keeps the rows
    with a member, and sums per member with the total rounded to a whole
    number.

    *Checked: how many members the second view holds, and member 608's rides and minutes*

# Python

## 1 - Counting (4)

A strict > for 'over', += against =, a seen set that counts only new names, and
ends[i - 1] against ends[0].

1. **Rides longer than the free half hour** (P341)

   Write a function `count_over(minutes, limit)` that returns how many ride
   lengths are STRICTLY longer than limit. A for loop with an if on m > limit
   and a counter; a ride of exactly the limit is not over it.

   ```
   count_over([12, 31, 45, 30], 30) -> 2
   ```

   *Return: an integer.*

2. **The fares added up** (P342)

   Write a function `total_fares(fares)` that returns the sum of a list of
   fares in cents, 0 for an empty list, using a for loop and a running total
   rather than sum().

   ```
   total_fares([200, 0, 350, 0]) -> 550
   ```

   *Return: an integer.*

3. **How many different stations were visited** (P343)

   Write a function `stations_visited(stops)` that returns how many DIFFERENT
   station names appear in a list of stops. A for loop with a set of names
   seen so far and a counter that moves only when the name is new.

   ```
   stations_visited(["Harbour", "Cathedral", "Harbour", "Stadium"]) -> 3
   ```

   *Return: an integer.*

4. **Rides that ended where the last one did** (P344)

   Write a function `count_same_as_previous(ends)` that returns how many end
   stations in the list are the same as the one before them. A for loop over
   range(1, len(ends)) comparing ends[i] with ends[i - 1].

   ```
   count_same_as_previous(["Harbour", "Harbour", "Stadium", "Stadium", "Stadium"]) -> 3
   ```

   *Return: an integer.*

## 2 - Searching (4)

-1 after the loop as the sentinel, a best from the first value returned after
the loop, tuple unpacking in a for with False after the loop, and a last match
recorded.

5. **The first free ride** (P345)

   Write a function `first_free(fares)` that returns the POSITION of the first
   fare that is 0, or -1 if every fare was charged. A for loop over
   enumerate(fares) with a return inside it.

   ```
   first_free([200, 350, 0, 0]) -> 2
   ```

   *Return: an integer.*

6. **The longest ride, by hand** (P346)

   Write a function `longest_ride(minutes)` that returns the largest value in
   a non-empty list WITHOUT max(): a best so far that starts at minutes[0] and
   a for loop that replaces it when a value is bigger.

   ```
   longest_ride([12, 31, 8, 45, 20]) -> 45
   ```

   *Return: the value.*

7. **Did any ride end where it started?** (P347)

   Write a function `any_round_trip(rides)` that returns True when any (start,
   end) pair in the list has the same station at both ends, and False
   otherwise. A for loop that unpacks each pair -- for start, end in rides --
   with a return True at the first match, then False after the loop.

   ```
   any_round_trip([("A", "B"), ("C", "C")]) -> True
   ```

   *Return: True or False.*

8. **The last station a bike reached** (P348)

   Write a function `last_visit(stops, station)` that returns the POSITION of
   the last stop equal to station, or -1 if it never appears. A for loop over
   range(len(stops)) that records every match and returns the record after the
   loop.

   ```
   last_visit(["Harbour", "Stadium", "Harbour", "Cathedral"], "Harbour") -> 2
   ```

   *Return: an integer.*

## 3 - Building (4)

An if / else that appends every time, an f-string per item, a classification
with no gap at the boundary, and a string of digits that starts as ''.

9. **Fares capped at a maximum** (P349)

   Write a function `capped(fares, cap)` that returns a new list where every
   fare above cap is replaced by cap and the rest are unchanged, in order. A
   for loop with an if / else and an append.

   ```
   capped([200, 650, 300], 500) -> [200, 500, 300]
   ```

   *Return: the new list.*

10. **Ride lengths as labels** (P350)

    Write a function `labels(minutes)` that returns a list of strings like '12
    min' for each ride length, in order. A for loop that appends an f-string
    f"{m} min".

    ```
    labels([12, 31]) -> ["12 min", "31 min"]
    ```

    *Return: the list of strings.*

11. **Short or long, ride by ride** (P351)

    Write a function `classify(minutes)` that returns a list with 'long' for
    each ride over 30 minutes and 'short' for the rest, in order. A for loop
    with an if / else deciding which word to append.

    ```
    classify([12, 31, 30]) -> ["short", "long", "short"]
    ```

    *Return: the list of strings.*

12. **Just the digits of a station code** (P352)

    Write a function `digits_only(s)` that returns a string of the digit
    characters of s, in order, with everything else left out. A for loop over
    the characters with an if on ch.isdigit() and a result string built with
    +=.

    ```
    digits_only("ST-042") -> "042"
    ```

    *Return: the string.*

## 4 - Reducing (3)

A run that resets, a minimum that starts as None, and a test before the
subtraction.

13. **The longest run of free rides** (P353)

    Write a function `longest_free_run(fares)` that returns the length of the
    longest stretch of consecutive fares that are 0. A for loop with a current
    run that grows on a 0 and resets to 0 on anything else, and a best so far.

    ```
    longest_free_run([0, 0, 200, 0, 0, 0, 150]) -> 3
    ```

    *Return: an integer.*

14. **The shortest wait between rides** (P354)

    Write a function `min_gap(starts)` that returns the smallest difference
    between neighbouring start times in a list already in order, or None for
    fewer than two. A for loop over range(1, len(starts)) with a best that
    starts as None and is replaced when the gap is smaller or the best is
    still None.

    ```
    min_gap([10, 25, 27, 60]) -> 2
    ```

    *Return: the gap, or None.*

15. **How many rides a balance pays for** (P355)

    Write a function `rides_affordable(balance, fares)` that returns how many
    of the fares, taken in order, the balance can pay before it runs short --
    a fare EQUAL to what is left can still be paid. A for loop that breaks as
    soon as a fare is more than the balance, otherwise subtracts it and counts
    the ride.

    ```
    rides_affordable(1000, [200, 350, 300, 400]) -> 3
    ```

    *Return: an integer.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,411 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
