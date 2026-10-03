# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the district hospital,
RE-SEEDED (SEED 846) so every number you remember from earlier sets is now
wrong, at the level of the last three sets -- and **fifteen Python** over
rows shaped like the database's: admissions as dicts, stays as tuples, a
patients dict, and the SQL operations done by hand in Python.

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
| 1 - One list of rows | 1-5 |
| 2 - Grouping and ranking | 6-9 |
| 3 - Two tables | 10-12 |
| 4 - Checks and windows | 13-15 |

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
that is open instead -- 32 admissions have no discharge, 32
ward stays no end, 50 prescriptions no end -- and every question that
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

**Driver statements.** Questions 13 and 15 run inserts of their own *after*
yours -- the dates your CHECK should sort, and the drug names your index
should sort. Question 14 is graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `CHECK (date(x) IS x)`: a real date, and IS rather than = because a NULL CHECK passes |
| 14 | `INSERT ... SELECT ... WHERE NOT EXISTS`: the rows that are missing, and only those |
| 15 | `CREATE UNIQUE INDEX ... ON drugs (lower(name))`: uniqueness of an expression |

## Things the data does on purpose

- **The data is re-seeded.** Same schema, same shape, new numbers: 36
  admissions for patient 86, the most of anyone, where it used to be
  patient 1500.
- **6,093 observations have no temperature**, the gap between question
  1's two counts.
- **43 patients have a name of ten characters or fewer**, several of
  them sharing the same name, which is why question 3 returns the id.
- **1,561 admissions had exactly two stays**, the population of
  question 4 once the three-stay ones are ruled out.
- **26 patients with three or more admissions never left one ward**,
  by ward_stays; by admitting ward alone the count is five times that.
- **There are 40 drugs, one of them Morphine**, so question 15's
  'morphine' is the case clash the index has to refuse.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question here works on rows shaped like the
database's -- a list of dicts, a list of tuples, a dict -- and names the SQL
it mirrors, so the two tabs can be read side by side. (The grader also supports **program** questions, graded on what they
print; none in this set.)

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Warm-up (2)

COUNT(column) against COUNT(*) where a NULL changes a count, and two conditions
on one group in HAVING with the flag summed, not filtered.

1. **Temperatures taken** (Q832)

   For each admitting ward: how many observations its admissions have, how
   many of those recorded a temperature, and the lowest and highest
   temperature seen. temp_c is NULL where it was not taken.

   *Return: ward_id, readings, with_temp, lowest, highest*

2. **Well-typed postcodes** (Q833)

   Postcode areas with at least 125 patients, of whom fewer than 10 per cent
   have no recorded blood group: the area, its patients, how many have no
   blood group, and that percentage to one decimal.

   *Return: postcode_area, patients, untyped, pct_untyped*

## 2 - Strings and sequences (2)

length() of the string as stored, and stays 1 and 2 side by side with a NOT
EXISTS to rule out a third.

3. **Short names** (Q834)

   Patients whose full name -- space included -- is ten characters or fewer,
   with the name and its length().

   *Return: patient_id, name, chars*

4. **Longer the second time** (Q835)

   For admissions with EXACTLY two ward stays, per admitting ward: how many
   there are, how many had a second stay longer than the first, and the
   percentage to one decimal. An open second stay runs to 2026-06-30 23:59.

   *Return: ward_id, two_stay_admissions, second_longer, pct*

## 3 - Dates and times (2)

A quarter from the month by integer division, and a birthday as a '%m-%d' string
that ignores the year.

5. **Admissions by quarter** (Q836)

   Admissions per calendar quarter: the year as an integer, the quarter 1 to
   4, and the count. The quarter comes from the month by integer arithmetic --
   months 1 to 3 are quarter 1, 4 to 6 quarter 2 -- and (month + 2) / 3 does
   it in whole numbers.

   *Return: year, quarter, admissions*

6. **Birthdays in the first week of July** (Q837)

   How many patients have a birthday on each day from 1 to 7 July, whatever
   year they were born: the month-and-day as 'MM-DD' and the count.
   strftime('%m-%d', born_on) gives a string that ignores the year.

   *Return: month_day, patients*

## 4 - Intervals and occupancy (2)

Midnights crossed as a difference of dates, and the running occupancy pattern on
dates where the end day is inclusive.

7. **Nights in hospital** (Q838)

   For admissions 1 to 10 that are completed: the number of NIGHTS spent in --
   the midnights between admission and discharge, which is the difference
   between the two DATES, not the rounded length of stay. A patient in from
   23:00 to 02:00 spent one night and three hours.

   *Return: admission_id, nights*

8. **Peak demand for each drug** (Q839)

   For each drug, the most prescriptions of it that were running on any one
   day: a prescription runs from started_on to ended_on inclusive, open ones
   to 2026-06-30. Turn each into a +1 on its start day and a -1 on the day
   AFTER its end, run a total per drug in date order, and take the maximum.
   Count a -1 before a +1 on the same day.

   *Return: drug, peak*

## 5 - Joins and grain (2)

Two foreign keys compared with each other, and COUNT(DISTINCT) = 1 as a third
spelling of all-or-none.

9. **Prescribed by their own consultant** (Q840)

   For each admitting ward: how many prescriptions its admissions have, and
   how many were written by the admission's OWN consultant -- prescribed_by
   equal to the admission's consultant_id -- with the percentage to one
   decimal.

   *Return: ward_id, prescriptions, by_own_consultant, pct*

10. **Only ever one ward** (Q841)

    Patients with three or more admissions whose every ward stay, across all
    of them, was on the SAME ward: patient_id, their admissions, and that
    ward. COUNT(DISTINCT) of the stays' ward being 1 is the test.

    *Return: patient_id, admissions, ward_id*

## 6 - Window functions (2)

RANK restarted per ward by PARTITION BY, and LAG of a column that is not a
number.

11. **Each ward's busiest consultants** (Q842)

    For every ward and consultant who has admitted to it: the admissions, and
    the consultant's RANK within THAT ward, 1 for the most, ties sharing a
    rank.

    *Return: ward_id, consultant_id, admissions, rank_in_ward*

12. **Patient 86, ward by ward** (Q843)

    Patient 86 has the most admissions. For each of them in time order: when
    admitted, the admitting ward, the ward of the PREVIOUS admission -- NULL
    for the first -- and whether it is the same ward, as 1 or 0 (0 for the
    first).

    *Return: admitted_at, ward_id, previous_ward, same_ward*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A CHECK that a value is a real date,
INSERT ... SELECT for only the missing rows, and a UNIQUE index on an
expression.

13. **A column that must be a real date** (Q844)

    Create `clinic_bookings (booking_id INTEGER PRIMARY KEY, patient_id
    INTEGER NOT NULL referencing patients, booked_for TEXT NOT NULL)` where
    booked_for must be a valid date in 'YYYY-MM-DD' form. date(x) returns NULL
    for anything it cannot read, and returns x unchanged when x is already a
    well-formed date -- a CHECK can use both facts, but mind that a CHECK
    which comes out NULL counts as PASSED, so compare with IS rather than =.
    After your script, the question inserts '2026-07-14', '2026-02-30',
    '14/07/2026' and 'tomorrow' for patient 1.

    *Checked: the bookings that were accepted*

14. **Add only what is missing** (Q845)

    Create `ward_notes (ward_id INTEGER PRIMARY KEY referencing wards, note
    TEXT NOT NULL)` and insert notes for wards 1, 3 and 5 (any text). Then, in
    ONE statement, give every ward that has no note yet the note 'none
    recorded' -- without touching the three that exist. INSERT ... SELECT with
    a NOT EXISTS is the shape.

    *Checked: how many wards have a note, and how many of those notes read 'none recorded'*

15. **Unique regardless of case** (Q846)

    drugs.name is already UNIQUE, but 'Morphine' and 'morphine' are different
    strings to a plain UNIQUE. Create a unique index named `idx_drugs_name_ci`
    so that no two drugs can have names that differ only in case -- an index
    on an EXPRESSION of the column. After your script, the question inserts a
    drug called 'morphine' and one called 'Linezolid'.

    *Checked: how many drugs there are, and whether 'morphine' is among them*

# Python

## 1 - One list of rows (5)

A dict of counts keyed on the grouping column, `is None` for NULL, a filtered
sum that skips None itself, a best-so-far row, and an average whose denominator
is the values, not the rows.

1. **Admissions per ward** (P101)

   Each admission is a dict with keys id, patient, ward, days and priority;
   days is None while the patient is still in. Write
   `count_by_ward(admissions)` returning a dict from ward name to how many
   admissions it has -- GROUP BY ward, COUNT(*):

   ```
   count_by_ward(ADM) -> {'Fleming': 2, 'Barry': 2, 'Jenner': 1}
   ```

   *Return: the dict; an empty list gives an empty dict.*

2. **Still in: the open admissions** (P102)

   Write `open_admissions(admissions)` returning a list of the ids of
   admissions whose days is None -- the patient has not been discharged -- in
   the order given. WHERE discharged_at IS NULL:

   ```
   open_admissions(ADM) -> [2]
   ```

   *Return: a list of ids.*

3. **Total days on one ward** (P103)

   Write `total_days(admissions, ward)` returning the sum of days for
   completed admissions to that ward, skipping the open ones (days None).
   SUM(days) WHERE ward = ? AND days IS NOT NULL:

   ```
   total_days(ADM, 'Fleming') -> 4.5
   ```

   *Return: the total; 0 for a ward with none.*

4. **The longest completed stay** (P104)

   Write `longest_stay(admissions)` returning the id of the completed
   admission with the most days, or None if there is no completed admission.
   Open ones (days None) do not count:

   ```
   longest_stay(ADM) -> 4
   ```

   *Return: an id, or None.*

5. **Average stay, rounded** (P105)

   Write `average_days(admissions)` returning the mean days of the completed
   admissions rounded to one decimal, or None if there are none to average --
   AVG(days):

   ```
   average_days(ADM) -> 3.7
   ```

   *Return: the mean, or None.*

## 2 - Grouping and ranking (4)

Count then filter the counts, a dict of lists with setdefault,
max(key=counts.get) for the key, and filter-sort-slice for top-N.

6. **Patients admitted more than n times** (P106)

   Write `frequent_patients(admissions, n)` returning a SORTED list of the
   patient ids with more than n admissions -- GROUP BY patient HAVING COUNT(*)
   > n:

   ```
   frequent_patients(ADM, 1) -> [7, 9]
   ```

   *Return: a sorted list of patient ids.*

7. **Ids grouped by priority** (P107)

   Write `by_priority(admissions)` returning a dict from each priority to the
   LIST of admission ids with it, in the order given:

   ```
   by_priority(ADM) -> {'urgent': [1, 5], 'routine': [2, 4], 'immediate': [3]}
   ```

   setdefault(key, []) gives you the list to append to, creating it the first
   time.

   *Return: the dict of lists.*

8. **The busiest ward** (P108)

   Write `busiest_ward(admissions)` returning the ward with the most
   admissions; on a tie, the one that appears FIRST in the list. The list is
   never empty:

   ```
   busiest_ward(ADM) -> 'Fleming'
   ```

   *Return: the ward name.*

9. **The n longest stays** (P109)

   Write `top_n(admissions, n)` returning the ids of the n completed
   admissions with the most days, longest first -- ORDER BY days DESC LIMIT n.
   Open admissions are excluded, and fewer than n are returned if fewer exist:

   ```
   top_n(ADM, 2) -> [4, 1]
   ```

   *Return: a list of ids.*

## 3 - Two tables (3)

Sort before you trust the order, a dict as the join index with get() for the
LEFT JOIN, and the interval test with None spelled out.

10. **The route through the wards** (P110)

    Ward stays are tuples (admission_id, stay_seq, ward), not necessarily in
    order. Write `route(stays, admission_id)` returning the wards of that
    admission in stay_seq order:

    ```
    route([(1, 2, 'Fleming'), (1, 1, 'Barry'), (2, 1, 'Jenner')], 1) -> ['Barry', 'Fleming']
    ```

    *Return: a list of ward names; empty if the admission has none.*

11. **Admissions with the patient's name** (P111)

    Patients are a dict from patient id to name. Write `with_names(admissions,
    patients)` returning a list of (admission id, patient name) tuples, one
    per admission in order, with None for a patient not in the dict -- a LEFT
    JOIN:

    ```
    with_names(ADM[:2], {7: 'Ada Byron'}) -> [(1, 'Ada Byron'), (2, None)]
    ```

    *Return: a list of tuples.*

12. **Who was on the ward on day d** (P112)

    Stays on one ward are tuples (admission_id, from_day, to_day), with to_day
    None while the stay is open. Write `occupancy_on(stays, day)` returning
    how many stays cover that day: began on or before it, and either open or
    ending AFTER it:

    ```
    occupancy_on([(1, 3, 7), (2, 5, None), (3, 8, 9)], 5) -> 2
    ```

    *Return: the count.*

## 4 - Checks and windows (3)

A dict remembering the last discharge as LAG, a column name as a variable, and a
CHECK constraint written as a list of messages.

13. **Readmitted within a window** (P113)

    Admissions are tuples (patient, admitted_day, discharged_day) in admission
    order. Write `readmitted_within(admissions, window)` returning the sorted
    list of patients who were admitted again within `window` days of a
    previous discharge -- admitted_day minus the earlier discharged_day at
    most window:

    ```
    readmitted_within([(7, 1, 4), (9, 2, 6), (7, 20, 22), (9, 30, 31)], 14) -> []
    readmitted_within([(7, 1, 4), (7, 10, 12)], 14) -> [7]
    ```

    *Return: a sorted list of patient ids, each once.*

14. **WHERE column = value, for any column** (P114)

    Write `where_equal(rows, key, value)` returning the rows -- the dicts
    themselves -- whose field `key` equals `value`, in order. The column name
    arrives as a string, so it indexes the dict:

    ```
    where_equal(ADM, 'priority', 'immediate') -> [{'id': 3, ...}]
    ```

    *Return: a list of dicts.*

15. **Problems with a row** (P115)

    Write `problems(row)` returning a list of the things wrong with one
    admission dict, in this order and with these exact strings: 'no patient'
    if the key patient is missing, 'no ward' if ward is missing or empty,
    'negative days' if days is a number below 0 (None is fine), 'bad priority'
    if priority is not one of immediate, urgent, routine:

    ```
    problems({'id': 2, 'ward': '', 'days': -1, 'priority': 'high'}) -> ['no patient', 'no ward', 'negative days', 'bad priority']
    ```

    *Return: the list; empty for a good row.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
931 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
