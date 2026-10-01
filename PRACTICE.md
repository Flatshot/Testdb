# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the district hospital -- the
same data as the previous sets, with none of their questions, at the level
of the last two sets -- and **fifteen Python**, a step up again: each asks
for a function of two to five lines with a loop or an if/else inside,
graded on what it returns.

| Stage | SQL questions |
|---|---|
| 1 - Warm-up | 1-2 |
| 2 - Strings and sequences | 3-4 |
| 3 - Dates and times | 5-6 |
| 4 - Intervals and occupancy | 7-8 |
| 5 - Joins and grain | 9-10 |
| 6 - Window functions | 11-12 |
| 7 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Counting and filtering | 1-4 |
| 2 - Building a list | 5-8 |
| 3 - Choosing | 9-12 |
| 4 - Dictionaries | 13-15 |

## The schema

Eleven tables. `admissions` is the centre: a patient, an admitting ward, a
consultant, `admitted_at`, and a `discharged_at` that is NULL while the patient
is still in. Under it hang `ward_stays` (the ordered sequence of wards, with
their own start and end), `procedures` (priced by `procedure_types.tariff_pence`),
`prescriptions` (of `drugs`, with a start and an end date) and `observations`
(the big table: a reading every few hours). `staff` is a forest -- four division
heads report to nobody -- and `shifts` is their rota. Double-click a table in
the left pane to see its columns.

**Datetimes are text**, 'YYYY-MM-DD HH:MM', and dates are 'YYYY-MM-DD'. They
compare correctly as text; `julianday()` turns either into a number of days
you can subtract, and `date()` cuts a datetime to its day.

**The data ends at 2026-06-30 23:59.** Anything that would have ended after
that is open instead -- 39 admissions have no discharge, 39
ward stays no end, 71 prescriptions no end -- and every question that
measures an open interval says which end to supply.

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

**Driver statements.** Question 14 runs four inserts of its own *after*
yours -- the codes your CHECK should sort. Questions 13 and 15 are graded
on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | a `VIEW` with `GROUP BY` and `RANK() OVER` inside it, so ties share a place |
| 14 | `CHECK (code GLOB 'G[0-9][0-9][0-9][0-9][0-9]')`: a format enforced by the table |
| 15 | `INSERT ... SELECT value FROM json_each(...)`: a JSON list turned into rows |

## Things the data does on purpose

- **9 forenames are shared by 80 or more patients**, Cerys by the
  most, which is question 3's answer.
- **5 of the eight wards average a higher heart rate than the hospital**,
  by fractions of a beat, which is why question 2 asks for two decimals.
- **Theatre 3 stood empty for more than a day 11 times from June on**,
  measured from the previous procedure's end -- measured from its start,
  every gap looks longer.
- **39 ward stays are open on 2026-06-30**, so question 8's two
  instants on that day count almost nobody without COALESCE.
- **3 procedure types have never been performed anywhere**, so they
  are the zeros question 10's LEFT JOIN has to keep.
- **Two wards took 37 admissions in June 2026**, the tie that makes
  question 13's RANK differ from ROW_NUMBER.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question here needs a loop or a choice inside
the function, and its title names the pattern. (The grader also supports **program** questions, graded on what they
print; none in this set.)

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Warm-up (2)

A rate as a ratio of two sums rather than an average of ratios, and HAVING
compared against a scalar subquery.

1. **Pence per minute in theatre** (Q817)

   For each category of procedure, the tariff earned per minute of theatre
   time, to two decimals: the TOTAL tariff of the procedures with a recorded
   duration, divided by their TOTAL minutes. One ratio of two sums, not an
   average of ratios.

   *Return: category, pence_per_minute*

2. **Wards above the hospital's pulse** (Q818)

   Admitting wards whose observations average a higher heart rate than the
   hospital as a whole: ward_id, readings, and the ward's average to two
   decimals. The hospital average is a scalar subquery, and the comparison
   belongs in HAVING.

   *Return: ward_id, readings, avg_hr*

## 2 - Strings and sequences (2)

The forename cut one short of the space, and LAG turning 'higher than the
previous reading' into a column a SUM can count.

3. **The commonest forenames** (Q819)

   Forenames shared by 80 or more patients, with the count. The forename is
   everything BEFORE the single space in the name.

   *Return: forename, patients*

4. **Readings on the rise** (Q820)

   For admissions 1 to 10: how many observations each has, how many of them
   recorded a heart rate HIGHER than the previous observation of the same
   admission, and the percentage to one decimal. The first reading has no
   previous and is not a rise.

   *Return: admission_id, readings, rises, pct_rising*

## 3 - Dates and times (2)

Sunday is '0' in %w, and a julianday difference split into whole days by CAST
and hours from the fraction.

5. **Arrived at the weekend** (Q821)

   For each route of admission: how many admissions, how many arrived on a
   Saturday or a Sunday, and the percentage to one decimal. strftime('%w') is
   the weekday as text, '0' for Sunday to '6' for Saturday.

   *Return: admitted_via, admissions, weekend, pct*

6. **Days and hours, separately** (Q822)

   For admissions 1 to 5, the length of stay as whole days and the hours left
   over, to one decimal -- 3 days and 20.8 hours, not 3.9 days. The julianday
   difference is a number of days with a fraction; CAST it to INTEGER for the
   days and use the fraction for the hours.

   *Return: admission_id, days, hours*

## 4 - Intervals and occupancy (2)

LAG of a computed end for the gaps between procedures, and the same ward at two
instants as two conditional SUMs.

7. **Theatre 3 standing empty** (Q823)

   In theatre 3, from June 2026 on, the gaps of more than 24 hours between one
   procedure ENDING and the next BEGINNING, over procedures with a recorded
   duration: when the previous one ended, when the next began, and the gap in
   hours to one decimal. A procedure ends at datetime(performed_at, '+' ||
   duration_minutes || ' minutes').

   *Return: previous_end, next_start, gap_hours*

8. **Two in the morning and two in the afternoon** (Q824)

   For each ward, how many patients were on it at 02:00 and how many at 14:00
   on 2026-06-30, as two columns from one query: a stay covers an instant if
   it began at or before it and had not ended, and an open stay has not ended.

   *Return: ward_id, at_0200, at_1400*

## 5 - Joins and grain (2)

A self-join on person and day with an inequality on the theatre, and a LEFT JOIN
whose filter must stay in the ON.

9. **Two theatres in one day** (Q825)

   For each surgeon, on how many DAYS they operated in two or more different
   theatres. Pair each procedure with another by the same surgeon on the same
   date in a different theatre, then count the distinct dates.

   *Return: surgeon_id, split_days*

10. **Theatre 6's tally, every type** (Q826)

    Every procedure type with how many times it has been performed in theatre
    6 -- all thirty types, with 0 for the ones never done there. The theatre
    condition has to live in the join's ON clause, not the WHERE.

    *Return: code, in_theatre_6*

## 6 - Window functions (2)

LAG and LEAD side by side, and CUME_DIST within a partition.

11. **The reading before and the reading after** (Q827)

    For admission 9, every observation in time order with the heart rate, the
    heart rate of the PREVIOUS observation and of the NEXT one -- NULL where
    there is none. LAG and LEAD over the same ordering.

    *Return: taken_at, heart_rate, previous_hr, next_hr*

12. **Where a stay sits on its ward** (Q828)

    For admissions 1 to 10 that are completed: the length of stay to two
    decimals, and its CUME_DIST within the admitting ward's completed
    admissions ordered by length -- the share of that ward's stays that are
    this long or shorter, to two decimals.

    *Return: admission_id, ward_id, days, cume_dist*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A view with a window function, a CHECK
that uses GLOB, and rows made from a JSON list.

13. **A ranking you can query** (Q829)

    Create a view `june_ranking (ward_id, admissions, rank)` over admissions
    in June 2026, with RANK() by admissions, 1 for the most -- so that two
    wards with the same count share a rank. A window function works inside a
    view like anywhere else.

    *Checked: the view's rows*

14. **A code with a shape** (Q830)

    Create `gp_practices (code TEXT PRIMARY KEY, name TEXT NOT NULL)` where
    code must be a capital G followed by exactly five digits -- a CHECK using
    GLOB, whose [0-9] matches one digit and which is case-sensitive. After
    your script, the question inserts 'G12345', 'g12345', 'G1234' and
    'G123456'.

    *Checked: the codes that were accepted*

15. **Rows out of a JSON list** (Q831)

    Create `ward_tags (tag_id INTEGER PRIMARY KEY, tag TEXT NOT NULL)` and
    fill it from the JSON list '["isolation", "bariatric", "paediatric",
    "step-down"]' -- one row per element, in order -- with INSERT ... SELECT
    over json_each(), whose `value` column is each element.

    *Checked: the tags, in tag_id order, and how many there are*

# Python

## 1 - Counting and filtering (4)

A counter inside an if, a return inside a loop, a new list built by append
rather than removing from the old one, and strip() as a truth test.

1. **for + if: count the ones over a limit** (P086)

   Write a function `count_above(rates, limit)` that returns how many of the
   rates are STRICTLY greater than the limit, using a for loop with an if and
   a counter:

   ```
   count_above([72, 118, 65, 101], 100) -> 2
   ```

   *Return: the count; 0 for an empty list.*

2. **for + return: the first one over** (P087)

   Write a function `first_above(rates, limit)` that returns the FIRST rate
   greater than the limit, or None if there is none:

   ```
   first_above([72, 118, 65, 101], 100) -> 118
   ```

   *Return: the rate, or None.*

3. **for + append: keep the evens** (P088)

   Write a function `evens_only(nums)` that returns a NEW list holding only
   the even numbers, in their original order -- an empty list to start with,
   append() inside the if:

   ```
   evens_only([1, 2, 3, 4, 6]) -> [2, 4, 6]
   ```

   *Return: the new list.*

4. **for + if: drop the blank strings** (P089)

   Write a function `remove_blanks(strings)` that returns a new list without
   the strings that are empty or only whitespace. strip() turns a whitespace-
   only string into an empty one, and an empty string is false in an if:

   ```
   remove_blanks(["Bay A", "", "   ", "Bay B"]) -> ["Bay A", "Bay B"]
   ```

   *Return: the new list, with the kept strings unchanged.*

## 2 - Building a list (4)

A running total with the add before the append, if/elif/else as one decision, a
while loop that moves its own variable, and // with % to peel digits.

5. **for + accumulator: running totals** (P090)

   Write a function `running_total(nums)` that returns a list of the
   cumulative sums -- each item is the total so far:

   ```
   running_total([3, 1, 4, 1]) -> [3, 4, 8, 9]
   ```

   Keep a total that grows as you go, and append it after each addition.

   *Return: the list of totals.*

6. **for + if/elif: clamp every value** (P091)

   Write a function `clamp_all(values, lo, hi)` that returns a new list where
   every value below lo becomes lo, every value above hi becomes hi, and the
   rest are unchanged:

   ```
   clamp_all([35.2, 36.8, 42.5], 36.0, 41.0) -> [36.0, 36.8, 41.0]
   ```

   *Return: the new list.*

7. **while: count down to one** (P092)

   Write a function `countdown(n)` that returns the list n, n-1, ... down to
   1, using a while loop that appends and then decrements. For 0 or less,
   return an empty list:

   ```
   countdown(3) -> [3, 2, 1]
   ```

   *Return: the list.*

8. **while + // and %: add up the digits** (P093)

   Write a function `digit_sum(n)` that returns the sum of the digits of a
   non-negative integer, peeling the last digit off with % 10 and dropping it
   with // 10 in a while loop:

   ```
   digit_sum(1234) -> 10
   ```

   digit_sum(0) is 0.

   *Return: the sum.*

## 3 - Choosing (4)

Bands tested in order, set() before the second largest, test-then-add for
duplicates, and a current run beside a best run.

9. **if/elif/else: an age band** (P094)

   Write a function `band(age)` that returns 'child' for an age under 18,
   'adult' for 18 up to and including 64, and 'senior' for 65 and over:

   ```
   band(64) -> 'adult'
   band(65) -> 'senior'
   ```

   *Return: one of the three strings.*

10. **for + two variables: the second largest** (P095)

    Write a function `second_largest(nums)` that returns the second-largest
    DISTINCT value in a list of at least two distinct numbers:

    ```
    second_largest([72, 118, 65, 101]) -> 101
    second_largest([5, 5, 3]) -> 3
    ```

    *Return: the number.*

11. **for + set: is anything repeated** (P096)

    Write a function `has_duplicates(items)` that returns True if any value
    appears more than once, else False. Keep a set of what you have seen;
    return True the moment an item is already in it:

    ```
    has_duplicates([1, 2, 3, 2]) -> True
    ```

    *Return: True or False.*

12. **for + reset: the longest streak** (P097)

    Write a function `longest_run(flags)` that returns the length of the
    longest unbroken run of True values in the list:

    ```
    longest_run([True, True, False, True, True, True]) -> 3
    ```

    Keep a current run that grows on True and resets to 0 on False, and a best
    that remembers the highest the current run has reached.

    *Return: the length; 0 if there is no True.*

## 4 - Dictionaries (3)

items() with the if on one half and the append on the other, out[value] = key to
invert, and get(key, 0) + n to merge.

13. **for + items(): keys whose value passes** (P098)

    Write a function `keys_above(d, limit)` that returns a list of the keys
    whose value is greater than the limit, in the dictionary's order:

    ```
    keys_above({"Fleming": 16, "Barry": 30, "Jenner": 18}, 17) -> ["Barry", "Jenner"]
    ```

    *Return: a list of keys.*

14. **for + d[k] = v: invert a dictionary** (P099)

    Write a function `invert(d)` that returns a new dictionary with the keys
    and values swapped. The values are unique:

    ```
    invert({"Fleming": 5, "Barry": 4}) -> {5: "Fleming", 4: "Barry"}
    ```

    *Return: the new dictionary.*

15. **for + get(): add two tallies together** (P100)

    Write a function `merge_counts(a, b)` that returns a new dictionary
    holding the sum of the counts in two tallies -- a key in both is added up,
    a key in one keeps its count:

    ```
    merge_counts({"day": 3, "night": 1}, {"night": 2, "late": 1}) -> {"day": 3, "night": 3, "late": 1}
    ```

    Start from a copy of a, then loop over b with get(key, 0).

    *Return: the merged dictionary.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
901 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
