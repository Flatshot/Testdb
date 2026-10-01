# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the district hospital -- the
same data as the previous sets, with none of their questions, at the level
of the last set -- and **fifteen Python**, a small step up: each asks for a
tiny FUNCTION that returns a value, graded on the return, still built
around one tool named in the question's title.

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
| 1 - Numbers | 1-3 |
| 2 - Strings | 4-8 |
| 3 - Lists | 9-13 |
| 4 - Dictionaries | 14-15 |

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

**Driver statements.** Question 15 runs one statement of its own *after*
yours -- the discharge your trigger should act on. Questions 13 and 14 are
graded on what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `PRAGMA foreign_keys = OFF` for a load, `ON` again, and `pragma_foreign_key_check` to find what slipped in |
| 14 | `ALTER TABLE ADD COLUMN` and an `UPDATE` with a correlated `json_group_array(... ORDER BY ...)` |
| 15 | `AFTER UPDATE OF column ... WHEN`, with a body that updates a second table |

## Things the data does on purpose

- **26 staff prescribe**, and one of them sits at 19.96 per cent
  controlled -- which rounds to 20.0 and is not 20, so question 2 says
  'before rounding'.
- **315 admissions had exactly three stays**, the population of question
  4, and the first stay is the longest of the three more often than not.
- **487 procedures have no recorded duration**, so question 7 has to
  leave them out before computing an end.
- **39 patients have spent more than 40 days in hospital in all**, five
  of them with an admission still open -- the five question 8's trap loses.
- **353 admissions had neither a procedure nor a prescription**; with
  OR instead of AND the count is six times that.
- **Admission 173 is still open and moved ward on 2026-06-28**, so question
  15's trigger has one open stay to close and one closed stay to leave
  alone.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question is still about one tool, named in its
title. (The grader also supports **program** questions, graded on what they
print; none in this set.)

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Warm-up (2)

A pivot by two conditional SUMs with a real division, and two aggregate
conditions in one HAVING with the flag summed rather than filtered.

1. **Days and nights, side by side** (Q802)

   One row per ward: how many day shifts and how many night shifts have been
   worked there, as two columns, and the percentage of shifts that were nights
   to one decimal.

   *Return: ward_id, day_shifts, night_shifts, pct_night*

2. **Heavy on the controlled drugs** (Q803)

   Prescribers who have written at least 460 prescriptions, of which at least
   20 per cent were for controlled drugs -- tested on the exact share, before
   rounding: staff_id, prescriptions, controlled, and the percentage to one
   decimal. `controlled` is on drugs.

   *Return: staff_id, prescriptions, controlled, pct*

## 2 - Strings and sequences (2)

printf() to pad a number, and top-1 per admission followed by a count of which
position won.

3. **Reference numbers, zero-padded** (Q804)

   For patients 1 to 5, build a reference code: the letter P followed by the
   patient_id written as FIVE digits, with zeros in front to make up the
   width. Patient 1 becomes 'P00001'; patient 23 would become 'P00023'.

   The padding is what printf() does: printf('%05d', 7) gives '00007' -- d
   means a whole number, 05 means at least five characters wide, filled with
   zeros. Put the P in front with ||, or inside the format string.

   *Return: patient_id, reference*

4. **Which of three stays was the longest** (Q805)

   For admissions that had exactly three ward stays: how often the LONGEST of
   the three was stay 1, stay 2 and stay 3. Three rows. An open stay runs to
   2026-06-30 23:59; find each admission's longest stay first, then count by
   its stay_seq.

   *Return: stay_seq, admissions*

## 3 - Dates and times (2)

date() modifiers applied left to right for the end of a month, and %H cast to an
integer.

5. **First and last day of the month** (Q806)

   For admissions 1 to 5: the first and the last day of the month they were
   admitted in, as dates. date() takes modifiers: 'start of month', '+1
   month', '-1 day'.

   *Return: admission_id, month_start, month_end*

6. **Readings round the clock** (Q807)

   Observations by the hour of day they were taken, 0 to 23 as an integer: how
   many, and the average heart rate to one decimal. strftime('%H') gives the
   hour, as text.

   *Return: hour, readings, avg_hr*

## 4 - Intervals and occupancy (2)

An interval whose end is computed with datetime() and a modifier built from a
column, and a sum of intervals with open ends tested in HAVING.

7. **Two on the table at once** (Q808)

   For each theatre, how many PAIRS of procedures overlapped in time -- a
   procedure runs from performed_at for duration_minutes, and
   datetime(performed_at, '+' || duration_minutes || ' minutes') is when it
   ended. Only procedures with a recorded duration; each pair once.

   *Return: theatre, overlapping_pairs*

8. **Forty days in hospital** (Q809)

   Patients who have spent more than 40 days in hospital altogether, adding up
   every admission as of 2026-06-30 23:59 -- an open admission counts up to
   then. With their number of admissions and the total to one decimal.

   *Return: patient_id, admissions, total_days*

## 5 - Joins and grain (2)

A pair of columns from two tables as the grain, and two NOT EXISTS joined by the
right connective.

9. **Consultant and surgeon, a regular pair** (Q810)

   Pairs of consultant and surgeon who have worked on the same admissions at
   least 25 times -- the consultant is on the admission, the surgeon on the
   procedure -- with the number of procedures and of distinct admissions.

   *Return: consultant_id, surgeon_id, procedures, admissions*

10. **Neither cut nor dosed** (Q811)

    For each admitting ward, how many admissions had NO procedure AND NO
    prescription -- nothing done at all. Two NOT EXISTS, and mind the
    connective.

    *Return: ward_id, admissions*

## 6 - Window functions (2)

DENSE_RANK beside FIRST_VALUE for a gap to the leader, and a running SUM over a
total SUM for a cumulative share.

11. **Behind the leader** (Q812)

    Wards by admissions in June 2026: each ward's count, its DENSE_RANK with 1
    for the most, and how many admissions behind the leading ward it is -- 0
    for the leader. FIRST_VALUE over the same ordering gives the leader's
    count on every row.

    *Return: ward_id, admissions, rank, behind*

12. **Running share of admissions** (Q813)

    Wards ordered from most admissions to fewest, each with its count and the
    CUMULATIVE share of all admissions up to and including it, to one decimal
    -- the last row reaches 100. Ties by the lower ward_id. Two window SUMs:
    one ordered, one not.

    *Return: ward_id, admissions, cumulative_pct*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A load with foreign keys off and a
check afterwards, a JSON column built by UPDATE, and a trigger that keeps two
tables consistent.

13. **Load first, check afterwards** (Q814)

    Create `referrals (referral_id INTEGER PRIMARY KEY, patient_id INTEGER NOT
    NULL referencing patients, referred_on TEXT NOT NULL)`. Then, with foreign
    keys switched OFF by PRAGMA, insert referrals for patients 1, 2 and 9999
    -- the last does not exist -- switch them back ON, and use PRAGMA
    foreign_key_check (or the pragma_foreign_key_check table) to find and
    DELETE the offending row.

    *Checked: the referrals left, and how many foreign-key violations remain*

14. **A route stored as JSON** (Q815)

    Add a column `route` (TEXT) to admissions and fill it, for EVERY
    admission, with a JSON array of the ward_ids of its stays in stay_seq
    order -- '[1,5,2]' for admission 12. json_group_array(... ORDER BY ...)
    builds the array; an UPDATE with a correlated subquery fills the column.

    *Checked: admission 12's route, how many routes are valid JSON arrays, and how many have three wards*

15. **Discharge closes the stay** (Q816)

    Write a trigger so that when an admission's discharged_at is set -- an
    UPDATE OF that column from NULL to a value -- the admission's OPEN ward
    stay gets that value as its to_at. After your script, the question
    discharges admission 173 at '2026-07-01 09:00'.

    *Checked: admission 173's stays with their to_at, and how many open stays it has left*

# Python

## 1 - Numbers (3)

return against print, a comparison returned as a boolean, and / against // in an
average.

1. **return: sum() handed back** (P071)

   Write a function `total(nums)` that RETURNS the sum of the numbers in the
   list, using sum():

   ```
   total([16, 30, 18]) -> 64
   ```

   Return the value; do not print it. An empty list totals 0.

   *Return: the total.*

2. **%: is it even** (P072)

   Write a function `is_even(n)` that returns True when n is even and False
   otherwise, using the remainder operator %:

   ```
   is_even(4) -> True
   is_even(7) -> False
   ```

   *Return: True or False, not a number.*

3. **/: an average to two decimals** (P073)

   Write a function `average(nums)` that returns the mean of a non-empty list,
   rounded to two decimal places, using / for the division:

   ```
   average([1, 2, 3, 4]) -> 2.5
   ```

   *Return: the mean, rounded.*

## 2 - Strings (5)

upper() called, strip() against replace(), split() against list(), join() on the
separator, and a slice of three.

4. **upper(): shouting** (P074)

   Write a function `shout(text)` that returns the text in capitals with an
   exclamation mark on the end, using upper():

   ```
   shout("code blue") -> "CODE BLUE!"
   ```

   *Return: the new string.*

5. **strip(): tidy input** (P075)

   Write a function `clean(text)` that returns the text with whitespace
   removed from both ends, using strip(). Spaces inside the text stay:

   ```
   clean("  Bay 3  ") -> "Bay 3"
   ```

   *Return: the stripped string.*

6. **split(): text into words** (P076)

   Write a function `words(text)` that returns the words of the text as a
   list, using split():

   ```
   words("Morphine Codeine Diazepam") -> ["Morphine", "Codeine", "Diazepam"]
   ```

   *Return: a list of strings; empty text gives an empty list.*

7. **join(): words into text** (P077)

   Write a function `joined(names)` that returns the names as one string
   separated by ', ', using join():

   ```
   joined(["Barry", "Bevan"]) -> "Barry, Bevan"
   ```

   *Return: one string; an empty list gives an empty string.*

8. **[start:stop]: the first three** (P078)

   Write a function `first_three(text)` that returns the first three
   characters of the text, using a slice. Shorter text returns what there is:

   ```
   first_three("Nightingale") -> "Nig"
   ```

   *Return: the slice.*

## 3 - Lists (5)

max(key=len), count() against len(), [-1], a list comprehension against list
repetition, and set() turned back into a sorted list.

9. **max(key=len): the longest** (P079)

   Write a function `longest(words)` that returns the longest word in a non-
   empty list, using max() with key=len. On a tie the first of the longest is
   returned:

   ```
   longest(["Barry", "Nightingale", "Bevan"]) -> "Nightingale"
   ```

   *Return: the word.*

10. **count(): how many of one value** (P080)

    Write a function `count_of(items, value)` that returns how many times the
    value appears in the list, using the list's count() method:

    ```
    count_of(["day", "night", "day"], "day") -> 2
    ```

    *Return: the count, 0 when it never appears.*

11. **[-1]: the last item** (P081)

    Write a function `last(items)` that returns the last item of a non-empty
    list, using a negative index:

    ```
    last([72, 118, 65]) -> 65
    ```

    *Return: the item.*

12. **[... for ...]: a list from a list** (P082)

    Write a function `doubled(nums)` that returns a NEW list with every number
    doubled, using a list comprehension:

    ```
    doubled([1, 2, 3]) -> [2, 4, 6]
    ```

    *Return: the new list; an empty list stays empty.*

13. **set(): the distinct values, sorted** (P083)

    Write a function `distinct_sorted(items)` that returns the distinct values
    of the list, sorted, as a LIST -- set() to drop the repeats, sorted() to
    order them:

    ```
    distinct_sorted(["day", "night", "day"]) -> ["day", "night"]
    ```

    *Return: a sorted list.*

## 4 - Dictionaries (2)

get() with a fallback, and max(key=d.get) to return the key rather than the
value.

14. **get(): a lookup with a fallback** (P084)

    Write a function `beds_for(ward, beds)` that returns the beds for the ward
    from the dictionary, or 0 when the ward is not in it, using get():

    ```
    beds_for("Bevan", {"Fleming": 16}) -> 0
    ```

    *Return: a number.*

15. **max(key=d.get): the key with the biggest value** (P085)

    Write a function `fullest(beds)` that returns the KEY with the largest
    value in a non-empty dictionary, using max() with key=beds.get:

    ```
    fullest({"Fleming": 16, "Barry": 30}) -> "Barry"
    ```

    *Return: the key.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
871 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
