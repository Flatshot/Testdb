# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the bike-hire scheme, the
tenth set on it, at two tools per question with the tiers named by task,
on tools no bike set had used, and three writable questions; the prompts
name the tool but do not write the statement. **Fifteen Python** at the
easy level of the last two sets: everyday tasks over plain lists and
strings, with no maths and no dicts, on tasks those sets did not cover.

| Stage | SQL questions |
|---|---|
| 1 - Who, exactly | 1-3 |
| 2 - Rank and share | 4-6 |
| 3 - The clock and the calendar | 7-9 |
| 4 - Capacity and balance | 10-12 |
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
instead is conflict clauses, DDL and generated columns -- and each of
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

**Driver statements.** Question 15 inserts two invoice lines *after* your
script, so the probe can add up the generated totals. Questions 13 and 14
are graded on what the script leaves behind: the payments table, and what
sqlite_master says about the two names.

| # | Construct |
|---|---|
| 13 | `REPLACE INTO payments (payment_id, ride_id, amount_cents, paid_at, method) VALUES (1, ...)` |
| 14 | `ALTER TABLE maintenance RENAME TO jobs; CREATE VIEW maintenance AS SELECT * FROM jobs` |
| 15 | `CREATE TABLE invoice_lines (..., total_cents INTEGER GENERATED ALWAYS AS (qty * unit_cents) STORED)` |

## Things the data does on purpose

- **3 stations have never had a battery job reported**, the ones question 1's
  EXISTS flags with 0; a LEFT JOIN's COUNT(*) would flag every station with 1.
- **81 subscribers have paid and never ridden, and 196 riders have never been
  named on a payment**, the two sides question 2's FULL OUTER JOIN keeps; pay-
  as-you-go riders pay per ride, so all of them are on the second side.
- **35 rides are still out with no end station**, which question 3's IS NOT
  counts as not-round-trips and <> would drop.
- **Bike 2 has 43 rides, below 96 per cent of the classics**, question 4's
  PERCENT_RANK; Market Square takes 37.0 per cent of the centre's rides,
  question 5's zone share.
- **386 rides have an id that is a multiple of 100**, question 6's sample,
  which lands within a few per cent of the truth for the big models and misses
  by a sixth for the cargo bikes' 36.
- **Week 00 of 2026 has 291 rides and week 26 has 160**, the short weeks at
  either end of question 7's range; 1.73 per cent of rides start on the hour,
  question 8's figure, close to the one in sixty that chance predicts.
- **256 members were 65 or over on 30 June 2026, against 266 by a plain
  difference of years**, the ten whose birthday had not yet come that question
  9 leaves out.
- **Old Mill was active on 422 days, not 546**, which makes it question 10's
  busiest station per dock per day; Station Approach gains 794 bikes over the
  data and Market Square loses 567, question 11's two biggest imbalances.
- **Every station saw a casual rider and a member within its first week**, the
  two timestamps question 12 pulls from one scan.
- **Payment 1 is 300 cents by app for ride 12152**, the row question 13 re-
  records as 350 by card.
- **The data ends at 2026-06-30 23:59**, with 35 rides still out and 114 jobs
  open.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form -- but the type counts: a tuple is not a list, and 0 is not False. A
function that prints its answer instead of returning it returns None, and
None matches nothing. The inputs are everyday values: lists of station
names for questions 1 to 5, a number or a name for 6 to 10, a list of stops
or a line of text for 11 to 15. Each prompt shows one example call with its
answer, and Run adds a few more, including the empty list or the edge the
question warns about.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Who, exactly (3)

EXISTS as a 1-or-0 column where a LEFT JOIN's COUNT(*) counts the empty match,
FULL OUTER JOIN keeping both sides' strays, and IS NOT treating NULL as a value.

1. **Has this station ever seen a battery job?** (Q1207)

   For every station: a 1 or 0 saying whether a battery job has ever been
   reported there, and how many have. EXISTS is an expression, so it can sit
   in the SELECT list as a column; a scalar subquery gives the count.

   *Return: name, had_battery_job, battery_jobs*

2. **Paid, rode, or both** (Q1208)

   For each plan: members who have paid a subscription but never ridden,
   members who have ridden but never paid one, and members who have done both.
   A FULL OUTER JOIN between the distinct paying members and the distinct
   riding members keeps the members on either side alone; COALESCE the two ids
   to reach the plan.

   *Return: plan, paid_never_rode, rode_never_paid, both*

3. **Rides that went somewhere else, open ones included** (Q1209)

   For each zone, of the start station: its rides, and how many did NOT end
   where they began -- counting a ride still out, whose end station is NULL,
   as not a round trip. The NULL-safe comparison is IS NOT, which <> is not.

   *Return: zone, rides, not_round_trips*

## 2 - Rank and share (3)

PERCENT_RANK as the share strictly below, two SUM windows with different
partitions in one SELECT, and % picking one id in a hundred with a CASE that has
no ELSE.

4. **Where each bike stands among its model** (Q1210)

   For bikes 1 to 10: the model, the bike's rides, and the share of its model-
   mates that have FEWER rides, as a fraction from 0 to 1 to three decimals.
   PERCENT_RANK over the model's bikes, computed over every bike in a CTE and
   filtered afterwards; bikes never ridden count as 0 rides.

   *Return: bike_id, model, rides, pct_rank*

5. **Each station's share of its zone, and of everything** (Q1211)

   For every station: its zone, its rides, its share of the ZONE's rides and
   its share of ALL rides, both as percentages to one decimal. Two window SUMs
   over a CTE of rides per station: one partitioned by zone, one over the
   whole result.

   *Return: name, zone, rides, zone_pct, all_pct*

6. **A one-in-a-hundred sample** (Q1212)

   For each model: how many rides fall in a one-in-a-hundred sample -- the
   rides whose ride_id is a multiple of 100 -- the sample's average distance
   in whole metres, and the average over every ride of the model. The modulo
   operator % picks the sample; a CASE inside AVG keeps the other rides out of
   it.

   *Return: model, sampled, sample_avg_m, all_avg_m*

## 3 - The clock and the calendar (3)

%W against %U, %M against %S, and a year difference corrected by comparing 'MM-
DD' text.

7. **Rides by week of the year, 2026** (Q1213)

   For 2026: rides per week number, weeks starting on Monday, '00' for the
   days before the first Monday. strftime has two week-number codes; one
   counts Monday-led weeks and the other Sunday-led.

   *Return: week, rides*

8. **Rides that began on the hour** (Q1214)

   For each zone, of the start station: its rides, how many started at exactly
   zero minutes past an hour, and that as a percentage to two decimals.
   strftime has a code for the minute of the hour.

   *Return: zone, rides, on_the_hour, pct*

9. **Members who were 65 or over when the data ends** (Q1215)

   For each plan: its members, and how many were 65 or older on 2026-06-30 --
   an EXACT age, so a member whose 65th birthday fell in July 2026 is not
   counted. Take the difference of the years, then subtract one if the
   birthday's month-and-day had not yet come round.

   *Return: plan, members, seniors*

## 4 - Capacity and balance (3)

COUNT(DISTINCT date(...)) for the days a station was really open, ABS for a
difference in either direction, and MIN over a CASE with no ELSE.

10. **How hard each dock works** (Q1216)

    For every station: its docks, its rides, the number of DAYS on which a
    ride started there, and the rides per dock per active day to three
    decimals. The active days are a COUNT of DISTINCT dates; Old Mill's are
    fewer, and dividing by the data's 546 days instead would understate it.

    *Return: name, docks, rides, active_days, per_dock_day*

11. **Stations out of balance** (Q1217)

    The stations where rides ending and rides starting differ by MORE than a
    hundred, in either direction: the starts, the ends, and the net gain (ends
    minus starts, negative for a drain). Two scalar subqueries per station,
    and ABS in the WHERE.

    *Return: name, starts, ends, net*

12. **The first casual ride and the first member ride** (Q1218)

    For every station: when its first ride by a casual rider started, and when
    its first ride by a member did. One pass over rides: MIN of a CASE that
    yields the timestamp only for the rows of each kind, and nothing -- NULL
    -- for the others.

    *Return: name, first_casual, first_member*

## 5 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. REPLACE INTO, RENAME TO with a view
behind the old name, and STORED against VIRTUAL.

13. **A payment re-recorded** (Q1219)

    Payment 1 was keyed in wrong: it was 350 cents by card, not 300 by app.
    Re-record it in ONE statement, keeping payment_id 1, ride 12152 and the
    time '2025-01-01 02:42': REPLACE INTO writes the row as given, removing
    the old row with that id first.

    *Checked: payment 1's amount and method, how many payments there are, and the highest payment_id*

14. **A table renamed, without breaking the old name** (Q1220)

    The maintenance table is to be called jobs from now on, but old reports
    still query maintenance. Rename the table with ALTER TABLE, then create a
    VIEW called maintenance that selects everything from jobs, so both names
    work.

    *Checked: what sqlite_master says the names jobs and maintenance are*

15. **A total that is computed and kept** (Q1221)

    Create invoice_lines with line_id as the integer primary key, job_id
    (required, referencing maintenance), qty and unit_cents (integers,
    required), and total_cents as a GENERATED column equal to qty times
    unit_cents that is STORED -- written to disk when the row is, not
    recomputed on every read. The question then inserts two lines.

    *Checked: the totals added up, and the 'hidden' code pragma_table_xinfo gives the total_cents column (3 for stored, 2 for virtual)*

# Python

## 1 - Counting and finding (5)

`in` before index(), a backwards loop that breaks, len // 2 behind a guard,
today's count minus yesterday's, and lower() before testing a first letter.

1. **Everywhere the bike went after Harbour** (P476)

   Write a function `after(stops, station)` that returns the stops that came
   after the station's FIRST appearance, not including it, or [] if the
   station never appears. A membership test, then index() and a slice.

   ```
   after(["Parkway", "Harbour", "Stadium", "Hilltop"], "Harbour") -> ["Stadium", "Hilltop"]
   ```

   *Return: a list of str.*

2. **How long the bike sat at its last stop** (P477)

   Write a function `final_streak(stops)` that returns how many times the LAST
   stop is repeated at the end of the list, in a row -- 3 for a list ending
   Stadium, Stadium, Stadium -- and 0 for an empty list. A loop backwards from
   the end that stops at the first different stop.

   ```
   final_streak(["Harbour", "Stadium", "Stadium", "Stadium"]) -> 3
   ```

   *Return: an int.*

3. **The halfway stop** (P478)

   Write a function `halfway(stops)` that returns the stop in the middle of
   the day -- position len // 2, which for an even count is the later of the
   two middle stops -- or None for an empty list.

   ```
   halfway(["Harbour", "Stadium", "Parkway"]) -> "Stadium"
   ```

   *Return: a str, or None.*

4. **More visits today than yesterday?** (P479)

   Write a function `visits_change(today, yesterday, station)` that returns
   how many more times the station was visited today than yesterday --
   negative if fewer. Two count() calls and a subtraction, today's first.

   ```
   visits_change(["Harbour", "Harbour", "Stadium"], ["Harbour"], "Harbour") -> 1
   ```

   *Return: an int.*

5. **How many names start with a vowel** (P480)

   Write a function `vowel_names(names)` that returns how many of the names
   begin with a vowel, in either case; an empty string does not count. A sum
   over a generator that tests the first character lower-cased, with a guard
   for the empty string.

   ```
   vowel_names(["Aisha", "Umar", "Rosa", "Eleanor"]) -> 3
   ```

   *Return: an int.*

## 2 - Labels (5)

round() rather than int(), // and % with :02d rather than a float, words[-1]
rather than words[1], divmod into two padded parts, and the dash added before
join().

6. **A percentage, rounded, as a label** (P481)

   Write a function `percent_label(part, whole)` that returns the share as a
   whole-number percentage with a percent sign, '67%' for 2 of 3, or 'n/a'
   when the whole is 0. round() to no decimals, inside an f-string.

   ```
   percent_label(2, 3) -> "67%"
   ```

   *Return: a str.*

7. **Cents as dollars on a receipt** (P482)

   Write a function `dollars(cents)` that returns the amount as '$3.50': a
   dollar sign, the whole dollars, a point, and the cents left over always as
   two digits. // and % give the two parts; a format spec pads the second.

   ```
   dollars(350) -> "$3.50"
   ```

   *Return: a str.*

8. **A name the way the register writes it** (P483)

   Write a function `register_name(name)` that turns 'Hamid Uddin' into
   'Uddin, Hamid': the LAST word first, a comma and a space, then everything
   before it. A one-word name is returned unchanged. split(), a slice, and
   join().

   ```
   register_name("Hamid Uddin") -> "Uddin, Hamid"
   ```

   *Return: a str.*

9. **Minutes since midnight as a clock time** (P484)

   Write a function `clock(minutes)` that turns minutes since midnight into
   'HH:MM' with both parts two digits: 485 is '08:05'. divmod() by 60 gives
   hours and minutes at once; a format spec pads each.

   ```
   clock(485) -> "08:05"
   ```

   *Return: a str.*

10. **A bulleted list of names** (P485)

    Write a function `bulleted(names)` that returns the names as a bulleted
    list in one string: each name on its own line, starting with '- ', lines
    separated by newlines and no newline at the end; '' for no names. A
    comprehension to add the dash, then '\n'.join.

    ```
    bulleted(["Hamid", "Rosa"]) -> "- Hamid\n- Rosa"
    ```

    *Return: a str.*

## 3 - Checks and filters (5)

i + 1 to leave the first end out, zip with the list shifted by one, the empty
string's falsiness, strip() after split(','), and two slices that skip one
position.

11. **The stops between Harbour and Stadium** (P486)

    Write a function `between(stops, a, b)` that returns the stops strictly
    between the first a and the first b -- neither included -- and [] when
    either is missing or b comes before a. Two index() calls and one slice,
    after the checks.

    ```
    between(["Parkway", "Harbour", "Hilltop", "Riverside", "Stadium", "Parkway"], "Harbour", "Stadium") -> ["Hilltop", "Riverside"]
    ```

    *Return: a list of str.*

12. **The legs of a day, from one list** (P487)

    Write a function `legs_of(stops)` that returns one string per leg between
    consecutive stops, 'Harbour -> Stadium', from a single list of stops; one
    stop or none gives []. zip the list with itself shifted by one.

    ```
    legs_of(["Harbour", "Stadium", "Parkway"]) -> ["Harbour -> Stadium", "Stadium -> Parkway"]
    ```

    *Return: a list of str.*

13. **Blanks in the log filled in** (P488)

    Some stops were left blank -- an empty string. Write a function
    `fill_blanks(stops, default)` that returns the list with every empty
    string replaced by the default and everything else unchanged. A
    comprehension with a conditional expression, or with `or`.

    ```
    fill_blanks(["Harbour", "", "Stadium", ""], "unknown") -> ["Harbour", "unknown", "Stadium", "unknown"]
    ```

    *Return: a list of str.*

14. **Names from a comma-separated line** (P489)

    A form sends names as one line, 'Hamid, Rosa,Yusuf , Zara', with the
    spacing all over the place. Write a function `names_from(line)` that
    returns the names as a list, each stripped of spaces, empty pieces
    dropped. split on the comma, then strip, then keep the non-empty ones.

    ```
    names_from("Hamid, Rosa,Yusuf , Zara") -> ["Hamid", "Rosa", "Yusuf", "Zara"]
    ```

    *Return: a list of str.*

15. **A stop struck out** (P490)

    Write a function `without_position(stops, i)` that returns a NEW list with
    the stop at position i left out, or an unchanged copy if there is no such
    position. Two slices joined: everything before i and everything after it.

    ```
    without_position(["Harbour", "Stadium", "Parkway"], 1) -> ["Harbour", "Parkway"]
    ```

    *Return: a list of str.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,681 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
