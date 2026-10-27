# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
second set on it, at two tools per question with the tiers named by task,
bringing in the tools the first bike set left out, and three writable
questions that each take two steps. **Fifteen Python** in three shapes:
five functions that are one tool each, on tools no earlier set used; five
built around one simple loop; and five over lists of ride dicts shaped
like the scheme's rows, with a member that is None for a casual rider.

| Stage | SQL questions |
|---|---|
| 1 - Stations and docks | 1-3 |
| 2 - Members and plans | 4-6 |
| 3 - Bikes on the road | 7-9 |
| 4 - Time of day | 10-12 |
| 5 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - One tool | 1-5 |
| 2 - A simple loop | 6-10 |
| 3 - Ride rows | 11-15 |

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
script, ending a casual ride and a member's ride, both seventy-five minutes
long; the probe reads the fares your trigger set. Questions 14 and 15 are
graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE TRIGGER ... AFTER UPDATE OF ended_at ON rides WHEN NEW.ended_at IS NOT NULL BEGIN UPDATE rides SET fare_cents = CASE WHEN NEW.member_id IS NULL THEN ... ELSE ... END WHERE ride_id = NEW.ride_id; END` |
| 14 | `DELETE FROM maintenance WHERE fixed_at IS NULL AND julianday(...) - julianday(reported_at) > 90 AND EXISTS (SELECT 1 FROM rides r WHERE r.bike_id = maintenance.bike_id AND r.started_at > maintenance.reported_at)` |
| 15 | `CREATE TABLE station_rank AS SELECT start_station_id, COUNT(*), RANK() OVER (ORDER BY COUNT(*) DESC) FROM rides GROUP BY start_station_id` |

## Things the data does on purpose

- **100 of the 900 members have never ridden**, and 86 have no
  district recorded -- the rows a LEFT JOIN keeps and an inner join loses.
  Question 4's quartiles are of the members who HAVE completed rides.
- **7 of the 320 bikes have never been ridden and 18 are
  retired**; question 8 wants neither, and the bike idle longest has sat
  18.1 days.
- **30 per cent of rides are by casual riders**, whose member_id is
  NULL -- a category, not a gap, and the test for it is IS NULL. 312
  of the 320 bikes have carried one, which is why question 3's UNION is
  nearly the whole fleet and its INTERSECT only 88.
- **16 per cent of completed rides end where they began**, so
  starts and ends per station are different counts of the same rides, and
  question 15's table has to say which it holds.
- **59 per cent of members' rides cost nothing**, inside the free half
  hour; regulars keep inside it, which is why question 4's heaviest
  quartile pays least per ride.
- **Only 90 rides start before six in the morning**, and 53 per
  cent start before noon: question 10's cumulative share is nearly flat
  until the morning and then climbs steeply.
- **86 of the 114 open maintenance jobs are more than ninety
  days old, and 77 of those are on bikes ridden since the report** --
  the ones question 14 deletes; the rest are bikes waiting for a mechanic.
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
one simple loop each, the last five over lists of ride dicts: the prompt
shows a list called RIDES as its example, and Run passes your function
that list and a few shorter ones.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Stations and docks (3)

SQLite's bare column beside MAX, which Postgres refuses; a scalar subquery
ranked by DENSE_RANK, where per dock and in total give different orders; and
INTERSECT against UNION, one a hundred bikes and the other the whole fleet.

1. **The biggest station in each zone** (Q1087)

   For each zone: the name and dock count of its station with the most docks.
   MAX(docks) with name as a bare column -- SQLite brings the name from the
   row the MAX came from. No zone has a tie.

   *Return: zone, name, docks*

2. **Rides per dock, ranked** (Q1088)

   For each station: its docks, the rides that have started there, rides per
   dock to one decimal, and the station's place by that ratio, 1 for the
   hardest-worked. A scalar subquery for the starts, and DENSE_RANK over the
   ratio.

   *Return: station_id, docks, starts, per_dock, place*

3. **Bikes casual riders have used that also need fixing** (Q1089)

   Bikes that have been ridden by a CASUAL rider -- a ride with member_id NULL
   -- AND have a maintenance job still open: INTERSECT between a query over
   rides and one over maintenance, each bike once.

   *Return: bike_id*

## 2 - Members and plans (3)

NTILE(4) dealing riders into bands with the direction of the ORDER BY deciding
which band is 1, a pivot built from one conditional SUM per column, and a GROUP
BY on a plain column and a SUBSTR together.

4. **Riders in quartiles, and what they pay** (Q1090)

   Split the members who have completed rides into four equal groups by ride
   count, quartile 1 the LIGHTEST riders: for each quartile, the smallest and
   largest ride count in it and their average fare per ride in whole cents. A
   CTE per member with the count and the average, NTILE(4) over it, then a
   GROUP BY the tile.

   *Return: quartile, min_rides, max_rides, avg_fare*

5. **Plans by home zone, as a pivot** (Q1091)

   For each plan, one row with the number of members whose home station is in
   each zone, as five columns: centre, north, south, east, west. A join to
   stations for the zone, and SUM over a comparison for each column.

   *Return: plan, centre, north, south, east, west*

6. **Surnames shared within a plan** (Q1092)

   Plan-and-surname pairs where MORE THAN ONE member on that plan has that
   surname -- the surname being the part of name after the space: plan,
   surname, how many members. GROUP BY the plan and the SUBSTR together,
   HAVING COUNT(*) > 1.

   *Return: plan, surname, members*

## 3 - Bikes on the road (3)

A WHERE on the bare column so the covering index is searched, graded on EXPLAIN
QUERY PLAN; idle time from MAX(ended_at) under a NOT EXISTS for the bikes out
now; ROW_NUMBER partitioned by bike over a CTE that grouped by bike and month.

7. **Bike 7's rides, through the index** (Q1093)

   Every ride of bike 7: ride_id and started_at. The query in the editor is
   correct and reads all 38,000 rides, because it wraps bike_id in arithmetic.
   There is an index on rides(bike_id, started_at); write the WHERE on the
   bare column so it is searched. Your plan must say SEARCH with
   idx_rides_bike.

   *Return: ride_id, started_at*

8. **The bikes that have sat longest** (Q1094)

   The ten in-service bikes -- not retired, not out on a ride -- that have
   waited longest since their last ride ended, as of 2026-06-30 23:59: bike_id
   and the days idle to one decimal, ties by lower bike_id. MAX(ended_at) per
   bike, julianday for the gap, a NOT EXISTS for 'not out', ORDER BY and
   LIMIT.

   *Return: bike_id, days_idle*

9. **Each bike's busiest month** (Q1095)

   For bikes 1 to 10: the month in which each started the most rides, and how
   many -- ties to the earlier month. A CTE of rides per bike and month,
   ROW_NUMBER partitioned by bike ordered by rides descending then month, keep
   rank 1.

   *Return: bike_id, month, rides*

## 4 - Time of day (3)

A running SUM over grouped counts for a cumulative share, two CASEs crossed in
one GROUP BY with strftime's TEXT compared to text, and LAG partitioned by
station under a MAX.

10. **Rides by hour, and the share of the day so far** (Q1096)

    For each hour of the day -- strftime's %H -- how many rides started in it,
    and the cumulative percentage of all rides started by the end of that
    hour, to one decimal. A running window SUM over the grouped counts,
    divided by the total.

    *Return: hour, rides, cum_pct*

11. **Weekday or weekend, member or casual** (Q1097)

    Completed rides in four groups -- weekday or weekend by the start day,
    member or casual by member_id -- with the count and the average length in
    minutes to one decimal. Two CASEs, one on strftime('%w') tested against
    the TEXT values '0' and '6', one on member_id IS NULL.

    *Return: day_type, rider, rides, avg_minutes*

12. **The longest quiet spell at each station** (Q1098)

    For each station, the longest gap in hours between one ride starting there
    and the next, to one decimal. LAG over started_at partitioned by the start
    station in a CTE, julianday times 24 for hours, then MAX per station.

    *Return: station_id, max_gap_hours*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. An AFTER UPDATE trigger that prices the
row that fired it with integer round-up arithmetic, a DELETE with three
conditions of which the EXISTS is the one that means 'stale', and CREATE TABLE
AS SELECT holding a RANK.

13. **Price the ride when it ends** (Q1099)

    Write an AFTER UPDATE OF ended_at trigger on rides that sets the ride's
    fare_cents when ended_at is set: minutes are (julianday(NEW.ended_at) -
    julianday(NEW.started_at)) * 1440; a CASUAL rider (member_id NULL) pays
    200 plus 50 per started 10 minutes; a member pays 100 per started 15
    minutes beyond the first 30, else 0. 'Per started' means rounded UP:
    (minutes + 9) / 10 in integer arithmetic. The question then ends ride 1253
    (casual) and ride 884 (a member), both 75 minutes long.

    *Checked: the two rides' fares*

14. **Clear the stale repair reports** (Q1100)

    Delete the maintenance jobs that are still OPEN, were reported more than
    90 days before 2026-06-30 23:59, AND whose bike has started a ride since
    the report -- the problem evidently did not stop it. julianday for the
    age, a correlated EXISTS for the ride.

    *Checked: how many jobs remain, and how many of them are open*

15. **A league table of stations** (Q1101)

    Create a table `station_rank (station_id, starts, place)` with CREATE
    TABLE ... AS SELECT: every station's rides STARTED there and its place by
    that count, 1 for the most, RANK over the grouped counts. Rides are
    grouped by their start station.

    *Checked: the table's rows*

# Python

## 1 - One tool (5)

Five tools no earlier set used, each the whole answer: combinations against
permutations, zip with a star, bisect_left against bisect_right, sum's start
value, and a sort that returns None.

1. **itertools.combinations(): every pair of stations** (P356)

   Write a function `station_pairs(stations)` that returns a list of every
   pair of stations as tuples, each pair once and in the order the stations
   were given, using list() over itertools.combinations(stations, 2). Write
   `import itertools` as the first line.

   ```
   station_pairs(["Harbour", "Stadium", "Hilltop"]) -> [("Harbour", "Stadium"), ("Harbour", "Hilltop"), ("Stadium", "Hilltop")]
   ```

   *Return: the list of tuples.*

2. **zip(*rows): rows into columns** (P357)

   Write a function `columns(rows)` that turns a list of equal-length rows
   into a list of columns, each column a LIST, using a list comprehension over
   zip(*rows) -- the star hands each row to zip as a separate argument. No
   import is needed.

   ```
   columns([[1, 2, 3], [4, 5, 6]]) -> [[1, 4], [2, 5], [3, 6]]
   ```

   *Return: the list of lists.*

3. **bisect.bisect_left(): how many are below** (P358)

   Write a function `count_below(sorted_fares, x)` that returns how many fares
   in an already-SORTED list are strictly less than x, using
   bisect.bisect_left() -- the position where x would be inserted to keep the
   order, which is exactly that count. Write `import bisect` as the first
   line.

   ```
   count_below([100, 200, 200, 350, 600], 200) -> 1
   ```

   *Return: an integer.*

4. **sum(values, start): a total with an opening balance** (P359)

   Write a function `total_with_unlock(charges, unlock)` that returns the
   unlock fee plus all the per-minute charges, in one call of sum() with its
   second argument, the START value. No import is needed.

   ```
   total_with_unlock([50, 50, 100], 200) -> 400
   ```

   *Return: an integer.*

5. **sort(reverse=True): biggest first, in place** (P360)

   Write a function `longest_first(minutes)` that sorts the list itself from
   longest to shortest with sort(reverse=True) and then returns that same
   list. No import is needed.

   ```
   longest_first([12, 45, 8]) -> [45, 12, 8]
   ```

   *Return: the list.*

## 2 - A simple loop (5)

'd == 0 or 6' always true, a seen set checked before it is added to, round() to
bring a division back to cents, a run that resets to 1 not 0, and a product that
starts at 1.

6. **How many rides were at the weekend** (P361)

   Write a function `weekend_rides(days)` that returns how many of the weekday
   numbers are 0 or 6 -- Sunday or Saturday, as SQLite's strftime('%w')
   numbers them. A for loop with an if on d in (0, 6) and a counter.

   ```
   weekend_rides([1, 6, 0, 3, 6]) -> 3
   ```

   *Return: an integer.*

7. **The first station reached twice** (P362)

   Write a function `first_revisit(stops)` that returns the first station
   whose SECOND visit comes earliest, or None when no station is visited
   twice. A for loop with a seen set, returning the stop the moment it is
   already in the set.

   ```
   first_revisit(["Harbour", "Stadium", "Harbour", "Stadium"]) -> "Harbour"
   ```

   *Return: the station, or None.*

8. **Fares after a discount** (P363)

   Write a function `discounted(fares, pct)` that returns a new list of the
   fares each reduced by pct per cent and rounded to a whole number of cents.
   A for loop that appends round(f * (100 - pct) / 100) for each fare.

   ```
   discounted([200, 350, 100], 10) -> [180, 315, 90]
   ```

   *Return: the new list.*

9. **The longest run of ever-longer rides** (P364)

   Write a function `longest_rising(minutes)` that returns the length of the
   longest stretch in which each ride is longer than the one before it, 0 for
   an empty list and 1 for a single ride. A for loop over range(1,
   len(minutes)) with a run that grows on a rise and resets to 1 otherwise,
   and a best so far.

   ```
   longest_rising([5, 8, 12, 3, 4, 9, 10, 2]) -> 4
   ```

   *Return: an integer.*

10. **The digits of a bike number, multiplied** (P365)

    Write a function `digit_product(n)` that returns the product of the
    decimal digits of a positive integer, using a while loop that multiplies
    in n % 10 and then replaces n with n // 10, running while n is above zero.

    ```
    digit_product(234) -> 24
    ```

    *Return: an integer.*

## 3 - Ride rows (5)

Ride dicts with a member that is None for a casual rider: 'is None' against
'not', a WHERE before the GROUP BY, the winner's id rather than its minutes, a
set then sorted(), and a count kept under the same if as the total.

11. **How many rides were casual** (P366)

    Each ride is a dict with keys ride_id, member, minutes and fare, where
    member is None for a casual rider. Write a function `casual_count(rides)`
    that returns how many rides were casual: a for loop with an if on
    r["member"] is None and a counter. A member id can be 0, and 0 is a
    member.

    ```
    casual_count(RIDES) -> 2
    ```

    *Return: an integer.*

12. **What each member paid in all** (P367)

    Using the same ride dicts, write a function `fares_by_member(rides)` that
    returns a dict mapping each MEMBER to the total of their fares -- casual
    rides, with member None, are left out. A for loop with an if on the
    member, and a dict built with get(member, 0) + fare.

    ```
    fares_by_member(RIDES) -> {7: 200, 9: 100, 2: 0}
    ```

    *Return: the dictionary.*

13. **The longest ride's id** (P368)

    Using the same ride dicts, write a function `longest_ride_id(rides)` that
    returns the ride_id of the ride with the most minutes in a non-empty list,
    the first one if several tie. A for loop with a best ride so far, starting
    at rides[0].

    ```
    longest_ride_id(RIDES) -> 4
    ```

    *Return: an integer.*

14. **The members who have ridden for free** (P369)

    Using the same ride dicts, write a function `free_riders(rides)` that
    returns a sorted list of the DISTINCT members who have at least one ride
    with fare 0 -- casual rides cannot be free, but guard against None anyway.
    A for loop adding to a set under an if, then sorted() of the set.

    ```
    free_riders(RIDES) -> [2, 7]
    ```

    *Return: the sorted list.*

15. **How long members ride, on average** (P370)

    Using the same ride dicts, write a function
    `average_member_minutes(rides)` that returns the mean minutes of the rides
    that have a member, to one decimal, or None when there are no member
    rides. A for loop keeping a total and a count under an if, then the
    guarded division.

    ```
    average_member_minutes(RIDES) -> 34.2
    ```

    *Return: a float, or None.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,441 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
