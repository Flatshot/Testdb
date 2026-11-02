# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
sixth set on it, at two tools per question with the tiers named by task,
on tools no bike set had used, and three writable questions. **Fifteen
Python**, simpler by request: every one a small function over plain
values -- a list of numbers, a list of strings, one string, or two
numbers -- with no dicts and no rows to unpack.

| Stage | SQL questions |
|---|---|
| 1 - Shares and bands | 1-3 |
| 2 - Rows that don't line up | 4-6 |
| 3 - Scalar tools | 7-9 |
| 4 - Across the calendar | 10-12 |
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
instead is constraints, indexes, DML and transactions -- and each of
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

**Driver statements.** Question 13 runs three INSERTs of its own *after*
your script: a second fare for a ride that already has one, which the index
must refuse, and two subscription payments with no ride, which it must let
through. The probe counts what got in, so the refusal shows. Questions 14
and 15 are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CREATE UNIQUE INDEX one_fare_per_ride ON payments(ride_id) WHERE ride_id IS NOT NULL` |
| 14 | `UPDATE stations SET docks = docks + CASE zone WHEN 'centre' THEN 8 ELSE 4 END WHERE closed_on IS NULL` |
| 15 | `DELETE FROM maintenance WHERE kind = 'other'; SAVEPOINT s; DELETE FROM maintenance; ROLLBACK TO s; RELEASE s` |

## Things the data does on purpose

- **26.8 per cent of rides start in the centre zone**, which question 1 reads
  off a window over the grouped rows; the five shares add up to a hundred only
  when the division is real.
- **The one-to-two kilometre band holds 7,426 rides, the fullest**, and the
  average fare climbs about twenty cents a band, which question 2's integer-
  division key shows and a real division would hide in 8,513 rows.
- **75 per cent of subscribers' rides are free**, so their average fare is
  about fifty cents while the rides they pay for cost two dollars; question
  3's NULLIF is the difference between the two.
- **1,068 rides started while the bike's job was open**, about one per fixed
  job (986 of them), which question 4's BETWEEN join counts and a one-sided
  join inflates to tens of thousands.
- **3 members joined on 2023-02-01**, inside question 5's second page, which
  is why the ORDER BY needs member_id as a tiebreak.
- **The average station has 3,217 starts and Old Mill, closed since March
  2026, has 2,500**; question 6 compares each station with that average, and
  dividing the rides by the eleven open stations instead sets the bar too high
  for all but Market Square.
- **296 of the 320 bikes were acquired before the rides begin**, so question
  7's clamp to 2025-01-01 is what keeps the available days inside the period.
- **Five of the twelve station names have two words**, Station Approach the
  longest at fifteen letters; 169 of the 900 members have a first name
  beginning with a vowel, which GLOB's class finds and LIKE cannot.
- **January 2026 is up 12.4 per cent on January 2025 and the other five months
  are flat or down**; the data ends in June, so the second half of 2026 must
  be left out of question 10 or it shows a false collapse.
- **91 per cent of rides start somewhere other than where the bike was last
  left**, question 11's measure of how hard the crew works, and 255 members
  joined at a weekend, two sevenths of them near enough.
- **Every ride that was charged has exactly one payment**, which is what lets
  question 13's unique index be created; 100 jobs are of kind 'other', the
  ones question 15 deletes and keeps deleted.
- **The data ends at 2026-06-30 23:59**, with 35 rides still out and 114 jobs
  open.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, 2.0 is not 2, and 0 is
not False. A function that prints its answer instead of returning it
returns None, and None matches nothing. The inputs are plain values: a list
of numbers for questions 1 to 5, a string (and sometimes a width or a word)
for 6 to 10, a list or a pair of numbers for 11 to 15. Each prompt shows one
example call with its answer, and Run adds a few more, including the empty
list or the edge the question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Shares and bands (3)

SUM(COUNT(*)) OVER () for a grand total on every grouped row, integer division
used on purpose as a GROUP BY key, and NULLIF, which takes a value out of an
average without a WHERE.

1. **Each zone's share of the rides** (Q1147)

   For each zone, of the start station: its rides, and its share of ALL rides
   as a percentage to one decimal. The grand total comes from a window over
   the grouped rows -- SUM(COUNT(*)) OVER () -- so one query does both, and
   100.0 keeps the division real.

   *Return: zone, rides, share*

2. **Rides in kilometre bands** (Q1148)

   For the finished rides under ten kilometres: how many fall in each whole-
   kilometre band, and the band's average fare in dollars to two decimals. The
   band is the integer division distance_m / 1000 -- 0 for under a kilometre,
   1 for one to two -- used as the GROUP BY key; for once the truncation is
   the point.

   *Return: km_band, rides, avg_fare*

3. **What a ride costs when it costs anything** (Q1149)

   For each plan: the average fare of its members' rides in dollars to two
   decimals, and the average of the rides that were CHARGED -- the free ones
   left out of the average rather than counted as zero. AVG(NULLIF(fare_cents,
   0)) turns a 0 into NULL, and AVG skips NULLs.

   *Return: plan, avg_fare, avg_paid*

## 2 - Rows that don't line up (3)

A join ON a BETWEEN rather than an equals, OFFSET counting the rows to skip with
a tiebreak in the ORDER BY, and HAVING compared with the average of the per-
station counts.

4. **Rides taken while the bike was in the shop** (Q1150)

   For each kind of job: how many rides started on the bike between the job
   being reported and being fixed. A join that is not on equal keys: rides to
   maintenance ON the same bike_id AND started_at BETWEEN reported_at AND
   fixed_at, counting the fixed jobs only.

   *Return: kind, rides_during*

5. **The second page of members** (Q1151)

   The members in order of joining, ten to a page: page two. ORDER BY
   joined_on, then member_id to settle the members who joined on the same day,
   LIMIT 10 OFFSET 10 -- the offset skips page one.

   *Return: member_id, name, joined_on*

6. **Stations busier than the average station** (Q1152)

   The stations where more rides have started than at the AVERAGE station,
   with their count. The average is an aggregate of an aggregate: a subquery
   counting rides per start station, AVG of those counts, compared with in
   HAVING.

   *Return: name, starts*

## 3 - Scalar tools (3)

The two-argument MAX and MIN that clamp a date to a range, LENGTH minus
LENGTH(REPLACE(...)) to count a character, and GLOB's [AEIOU] where LIKE has no
classes at all.

7. **Days each bike was there to be ridden** (Q1153)

   For each model: its bikes, and the average number of days they were
   available INSIDE the data period, 2025-01-01 to 2026-06-30. The two-
   argument MAX and MIN pick the later of two values and the earlier:
   MAX(acquired_on, '2025-01-01') is when the bike entered the period,
   MIN(COALESCE(retired_on, '2026-06-30'), '2026-06-30') when it left;
   julianday of each, subtracted, averaged, to one decimal.

   *Return: model, bikes, avg_days*

8. **Words and letters in a station's name** (Q1154)

   For every station: how many words its name has, and how many letters. Words
   are spaces plus one -- LENGTH(name) minus LENGTH(REPLACE(name, ' ', ''))
   counts the spaces -- and the letters are the length with the spaces taken
   out.

   *Return: name, words, letters*

9. **First names that start with a vowel** (Q1155)

   For each plan: its members, and how many of them have a first name starting
   with a vowel. GLOB takes a character class -- name GLOB '[AEIOU]*' -- where
   LIKE has only _ and %; SUM of the condition counts the matches.

   *Return: plan, members, vowel_names*

## 4 - Across the calendar (3)

Two years as columns by summing a comparison, LAG fetching the previous row's
END station to compare with this row's start, and strftime('%w'), which runs
from '0' for Sunday to '6'.

10. **This year against last, month by month** (Q1156)

    For each month of the first half of the year, January to June: the rides
    in 2025, the rides in 2026, and the change as a percentage of 2025 to one
    decimal. One GROUP BY on strftime('%m') with two conditional sums --
    SUM(strftime('%Y', started_at) = '2025') and the same for 2026 -- and a
    WHERE that keeps the months the two years share.

    *Return: month, y2025, y2026, change_pct*

11. **How often a bike is moved between rides** (Q1157)

    For each model: the rides that had a previous ride on the same bike, how
    many of them started somewhere other than where that previous ride ENDED
    -- the bike was moved by the crew in between -- and that as a percentage
    to one decimal. LAG(end_station_id) OVER (PARTITION BY bike_id ORDER BY
    started_at) in a CTE, compared with start_station_id.

    *Return: model, rides, moved, moved_pct*

12. **Members who joined at the weekend** (Q1158)

    For each plan: its members, how many joined on a Saturday or Sunday, and
    that as a percentage to one decimal. strftime('%w', joined_on) is the day
    of the week as a digit, '0' for Sunday to '6' for Saturday; a SUM of IN
    ('0', '6') counts the weekend joiners.

    *Return: plan, members, weekend, weekend_pct*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A partial UNIQUE INDEX, a CASE inside
an UPDATE's SET, and a SAVEPOINT rolled back to.

13. **One fare per ride, enforced** (Q1159)

    A ride must not be paid for twice. CREATE UNIQUE INDEX one_fare_per_ride
    ON payments(ride_id) WHERE ride_id IS NOT NULL -- a partial index, so the
    thousands of subscription payments with no ride are left out of it. The
    question then runs three inserts: a second fare for ride 12152, which the
    index must refuse, and two subscription payments for members 1 and 2 with
    no ride, which it must let through.

    *Checked: how many payments there are, how many name a ride, and the highest payment_id*

14. **More docks, more in the centre** (Q1160)

    Every station still open gets more docks: eight more in the centre zone,
    four more elsewhere. ONE UPDATE whose SET adds a CASE on zone -- docks =
    docks + CASE zone WHEN 'centre' THEN 8 ELSE 4 END -- with a WHERE that
    leaves the closed station alone.

    *Checked: each zone's docks added up*

15. **An undo for one statement** (Q1161)

    Delete the 'other' jobs from maintenance -- that is the change you mean to
    keep. Then set a SAVEPOINT named s, run DELETE FROM maintenance with no
    WHERE (the mistake), and take it back with ROLLBACK TO s, then RELEASE s.
    Five statements; the probe should see every kind but 'other' still there.

    *Checked: how many jobs of each kind remain*

# Python

## 1 - Numbers (5)

Lists of numbers: / against //, a slice that is only right after sorted(), a
slice of positions not sizes, max() keeping the first of equals, and a median
that has to be sorted first.

1. **Metres into kilometres** (P416)

   Rides are recorded in metres. Write a function `to_km(distances)` that
   returns the same distances in kilometres, each rounded to one decimal, in
   the same order. A list comprehension with round(d / 1000, 1).

   ```
   to_km([6478, 3833, 962, 12050]) -> [6.5, 3.8, 1.0, 12.1]
   ```

   *Return: a list of floats.*

2. **The average with the extremes left out** (P417)

   A few very long rides spoil an average. Write a function
   `trimmed_mean(minutes)` that drops ONE smallest and ONE largest value and
   returns the mean of the rest, rounded to two decimals -- or None when there
   are fewer than three values, since nothing would be left. sorted(), a slice
   [1:-1], then sum and len.

   ```
   trimmed_mean([12, 31, 27, 240, 19]) -> 25.67
   ```

   *Return: a float, or None.*

3. **The three biggest fares added up** (P418)

   Write a function `top_three_total(fares)` that returns the sum of the three
   largest fares -- or of all of them when there are fewer than three.
   sorted(fares, reverse=True) and a slice [:3] inside sum().

   ```
   top_three_total([350, 1200, 200, 990, 250, 1200]) -> 3390
   ```

   *Return: an int.*

4. **The usual length of a ride** (P419)

   Write a function `most_common(minutes)` that returns the value that appears
   most often, the SMALLEST of them when several tie, or None for an empty
   list. max(set(minutes), key=minutes.count) finds a most common value; the
   tie rule needs the candidates sorted first, because max() keeps the first
   of equals.

   ```
   most_common([30, 12, 30, 45, 12, 30]) -> 30
   ```

   *Return: an int, or None.*

5. **The middle ride** (P420)

   Write a function `middle(minutes)` that returns the median: sort the
   values, take the middle one when the count is odd, and the mean of the two
   middle ones when it is even -- always as a float -- or None for an empty
   list. With n = len(values), the middle indexes are n // 2 and (n - 1) // 2,
   which are the same index when n is odd.

   ```
   middle([12, 31, 27, 240, 19]) -> 27.0
   ```

   *Return: a float, or None.*

## 2 - Text (5)

One string in, one out: stars counted from the length, three tests joined by
and, a slice one short to make room for the marker, == 1 rather than > 1, and
strip() after split().

6. **A card number, hidden** (P421)

   A receipt shows only the last four digits of the card. Write a function
   `mask(number)` that returns the number with every character but the last
   four replaced by '*': '*' * (len(number) - 4) joined to number[-4:].

   ```
   mask("4929123456781234") -> "************1234"
   ```

   *Return: a str.*

7. **Is it a bike code?** (P422)

   A bike code is 'BK-' followed by exactly four digits, seven characters in
   all. Write a function `is_bike_code(code)` that returns True for a code in
   that form and False otherwise: len(code) == 7 and code.startswith('BK-')
   and code[3:].isdigit(), joined with and.

   ```
   is_bike_code("BK-0042") -> True
   ```

   *Return: True or False.*

8. **A name cut to fit** (P423)

   A display has room for a fixed number of characters. Write a function
   `cut_to_fit(name, width)` that returns the name unchanged when it fits, and
   otherwise the first width - 1 characters followed by '~', so that the
   result is exactly width long. A conditional expression on len(name) <=
   width.

   ```
   cut_to_fit("Station Approach", 10) -> "Station A~"
   ```

   *Return: a str.*

9. **One ride, two rides** (P424)

   Write a function `plural(n, word)` that returns the count and the word as
   one string, with an 's' on the word unless n is exactly 1: '1 ride', '2
   rides', '0 docks'. An f-string with a conditional expression for the
   ending.

   ```
   plural(2, "ride") -> "2 rides"
   ```

   *Return: a str.*

10. **Surname first, turned round** (P425)

    The members file lists names as 'Uddin, Hamid'. Write a function
    `natural_order(name)` that returns them as 'Hamid Uddin': split at the
    comma, strip the spaces off each part, and join them the other way round.

    ```
    natural_order("Uddin, Hamid") -> "Hamid Uddin"
    ```

    *Return: a str.*

## 3 - Lists (5)

round(x, 1) against round(x), a range that stops at the length, a key that sorts
by the last word, max() and min() behind a guard, and a change measured against
where it started.

11. **Each zone's share, as percentages** (P426)

    Write a function `shares(counts)` that returns each count as a percentage
    of their total, rounded to one decimal, in the same order -- and [] for an
    empty list. Take the total once with sum(), then a comprehension.

    ```
    shares([10361, 6491, 9716, 5756, 6281]) -> [26.8, 16.8, 25.2, 14.9, 16.3]
    ```

    *Return: a list of floats.*

12. **Weekly totals from daily counts** (P427)

    Daily ride counts arrive as one long list. Write a function
    `weekly_totals(daily)` that returns the sum of each block of seven days,
    the last block included even if it is short. range(0, len(daily), 7) gives
    the start of each block, and daily[i:i + 7] is the block.

    ```
    weekly_totals([3, 4, 2, 5, 6, 1, 2, 7, 8, 1, 2, 3, 4, 5, 9, 9]) -> [23, 30, 18]
    ```

    *Return: a list of ints.*

13. **Members in surname order** (P428)

    Write a function `by_surname(names)` that returns the names sorted by
    their last word, the surname, as a new list. sorted() with key=lambda n:
    n.split()[-1].

    ```
    by_surname(["Hamid Uddin", "Rosa Villanueva", "Yusuf Baxter"]) -> ["Yusuf Baxter", "Hamid Uddin", "Rosa Villanueva"]
    ```

    *Return: a list of str.*

14. **How far apart the fares are** (P429)

    Write a function `spread(fares)` that returns the difference between the
    largest and the smallest fare, or None for an empty list. max() minus
    min(), behind a guard.

    ```
    spread([350, 1200, 200, 990]) -> 1000
    ```

    *Return: an int, or None.*

15. **Up or down on last year** (P430)

    Write a function `pct_change(before, after)` that returns the change from
    before to after as a percentage of before, rounded to one decimal --
    positive for a rise, negative for a fall -- or None when before is 0,
    since there is nothing to compare with.

    ```
    pct_change(1943, 2184) -> 12.4
    ```

    *Return: a float, or None.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,561 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
