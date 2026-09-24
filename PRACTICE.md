# SQL and Python practice exercises

Forty questions in two tabs. **Twenty SQL** on the district hospital -- the
same data as the previous set, with none of its questions -- and **twenty
Python**, from a first print() to dictionaries and try/except. The Python
questions are beginner-level on purpose; the SQL ones are at the level of the
previous sets.

| Stage | SQL questions |
|---|---|
| 1 - Warm-up | 1-3 |
| 2 - Strings and sequences | 4-5 |
| 3 - Dates and times | 6-7 |
| 4 - Intervals and occupancy | 8-10 |
| 5 - Joins and grain | 11-13 |
| 6 - Window functions | 14-15 |
| 7 - Changing the data | 16-20 |

| Stage | Python questions |
|---|---|
| 1 - First steps | 1-4 |
| 2 - Strings and lists | 5-8 |
| 3 - Conditions and loops | 9-12 |
| 4 - Functions | 13-16 |
| 5 - Dicts, sets and comprehensions | 17-20 |

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
instead is constraints, triggers, views and DML driven by CTEs -- and each of
questions 16 to 20 is one of those.

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

**Driver statements.** Questions 16, 17, 19 and 20 run statements of their
own *after* yours -- inserts that your key, trigger or table should refuse or
let through. A refusal is reported in the status bar as what it is, not as an
error.

| # | Construct |
|---|---|
| 16 | a keyed summary table, against `CREATE TABLE ... AS SELECT`, which copies no key |
| 17 | a composite `FOREIGN KEY (a, b) REFERENCES parent (a, b)` |
| 18 | an index on an expression, and the plan that proves it is used |
| 19 | a `BEFORE INSERT` trigger whose WHEN clause reads another table |
| 20 | `RAISE(ROLLBACK)` against `RAISE(ABORT)`: how much of a transaction is undone |

## Things the data does on purpose

- **487 procedures have no recorded duration**, which is what question 1's
  AVG has to leave out.
- **2,135 ward stays are moves** -- a stay_seq above 1 -- and stays of one
  admission never overlap, so a procedure falls inside exactly one of them.
- **9 staff have no home ward**, the pharmacists and porters, so a
  comparison against their ward is NULL rather than false.
- **3 procedure types have never been performed**, and they are the
  whole answer to question 12.
- **2 of admissions 31 to 40 reach their peak heart rate twice**, which is
  why question 14 says which of the two it wants.
- **Admission 173 is still open and admission 1 was discharged on 2026-04-02**,
  the two that question 19's trigger has to let through.
- **The largest dose on file is 10,000 mg**, so question 20's cap of 10000
  refuses nothing already there.

## How the Python questions are graded

Two kinds, and the question says which. A **program** question: the editor
holds a whole program, Run shows what it prints, and Check compares that with
the reference program's output line for line -- trailing spaces and blank
lines at the end are ignored, nothing else is. Where the program is meant to
read input(), the question says what it will be given. A **function** question:
the editor defines a function with the name the question gives, Run calls it
once for each test input and shows every call and its result, and Check
compares each result with the reference function's. Values are compared, not
their printed form, so a dictionary in a different order is the same
dictionary -- but the type counts: a tuple is not a list, and a set is not a
sorted list.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Warm-up (3)

Three questions on aggregates: an AVG that must skip NULLs, a COUNT(column) that
does not do what it looks like, and two conditions on totals that belong in
HAVING.

1. **Procedures by category** (Q732)

   One row per category of procedure: how many have been performed, the
   revenue in POUNDS to two decimals (tariffs are in pence), and the average
   duration in minutes to one decimal -- over the procedures whose duration
   was recorded.

   *Return: category, procedures, revenue_pounds, avg_minutes*

2. **Controlled, by form** (Q733)

   One row per form of drug -- tablet, injection, infusion, inhaler: how many
   drugs come in that form, how many of them are controlled, and the
   percentage that are, to one decimal. `controlled` is 0 or 1.

   *Return: form, drugs, controlled, pct*

3. **Night owls** (Q734)

   Staff who have worked at least 300 shifts, of which at least 40 per cent
   were nights: staff_id, their shifts, their nights, and the percentage to
   one decimal.

   Both conditions are about totals, so both belong in HAVING.

   *Return: staff_id, shifts, nights, pct_night*

## 2 - Strings and sequences (2)

A name split with instr() and substr(), and consecutive ward stays paired by a
self-join on stay_seq + 1.

4. **Surname first** (Q735)

   Patients 1 to 10 with their name turned round, 'Surname, Forename' --
   'Marcus Lindqvist' becomes 'Lindqvist, Marcus'. Every name is two words
   separated by one space; instr() finds the space and substr() takes either
   side of it.

   *Return: patient_id, sorted_name*

5. **Where transfers go** (Q736)

   Every move between wards: for each pair of wards, how many times a patient
   went straight from the first to the second. A move is two CONSECUTIVE stays
   of one admission -- stay_seq and stay_seq + 1.

   *Return: from_ward, to_ward, transfers*

## 3 - Dates and times (2)

strftime('%w') for the weekday, and an age from a julianday difference rather
than a subtraction of years.

6. **Admissions by weekday** (Q737)

   How many admissions arrived on each day of the week, with the percentage of
   all admissions to one decimal. strftime('%w') gives the weekday as a digit,
   0 for Sunday through 6 for Saturday; return the digit as an integer and the
   English name.

   *Return: day_num, day_name, admissions, pct*

7. **Age at admission** (Q738)

   Admissions by the patient's age on the day they were admitted: 'under 18',
   '18-64' and '65 and over', with the count and the percentage of all
   admissions to one decimal. Age in years is the difference in julianday()
   divided by 365.25, rounded down.

   *Return: band, admissions, pct*

## 4 - Intervals and occupancy (3)

Clipping stays to a month for a share of bed-days, placing a point inside an
interval, and asking the same interval question on every day of a recursive
calendar.

8. **Beds in use, March 2026** (Q739)

   For each ward, the percentage of its bed-days used in March 2026, to one
   decimal: the days of ward_stays that fell INSIDE the month, added up, over
   beds times 31. A stay that began in February or ran into April counts only
   for its March part -- clip each stay to the month with MAX() and MIN()
   before subtracting. An open stay runs to 2026-06-30 23:59.

   *Return: ward_id, beds, pct_used*

9. **Where the patient was** (Q740)

   How many procedures were performed while the patient was on each ward --
   not the ward they were admitted to, but the ward_stay whose interval
   contains performed_at. A stay with no end is still running.

   *Return: ward_id, procedures*

10. **Fleming at eight, all week** (Q741)

    For each day from 2026-06-24 to 2026-06-30, how many patients were on ward
    5 at 08:00 that morning. Build the seven days with a recursive CTE, then
    join ward_stays on the interval containing that instant -- the day plus '
    08:00'. Stays with no end are still running.

    *Return: day, patients*

## 5 - Joins and grain (3)

COUNT(DISTINCT) over two hops, an anti-join that `<>` cannot express, and a
comparison that goes NULL when one side is missing.

11. **Well travelled** (Q742)

    Patients who have been on SIX or more different wards over all their
    admissions, with the number of wards. A patient who was on a ward twice
    has been on it once.

    *Return: patient_id, wards*

12. **Never in theatre six** (Q743)

    Procedure types that have never been performed in theatre 6, with their
    name. A type never performed anywhere qualifies too.

    *Return: code, name*

13. **Away from home** (Q744)

    For each role that HAS a home ward -- consultants, doctors, nurses;
    pharmacists and porters have NULL -- how many shifts its staff have
    worked, how many were on a ward other than their own, and the percentage
    to one decimal.

    *Return: role, shifts, away, pct_away*

## 6 - Window functions (2)

Top-1 per group with a tiebreak that is part of the question, and LAG that must
be partitioned.

14. **The peak reading** (Q745)

    For admissions 31 to 40: the highest heart rate recorded, and how many
    hours after admission it was taken, to one decimal. If the peak was
    reached more than once, the EARLIEST time.

    *Return: admission_id, peak_hr, hours_in*

15. **Gaps in the readings** (Q746)

    For admissions 1 to 10: the longest gap between two consecutive
    observations, in hours to one decimal. LAG brings the previous reading's
    time onto each row; the partition matters.

    *Return: admission_id, longest_gap_hours*

## 7 - Changing the data (5)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A keyed summary table against CTAS, a
composite foreign key, an expression index, a trigger that reads another table,
and RAISE(ROLLBACK).

16. **A summary with a key** (Q747)

    Build `ward_load (ward_id INTEGER PRIMARY KEY, admissions INTEGER NOT
    NULL)` holding each ward's number of admissions as the admitting ward --
    eight rows -- so that the table has a real PRIMARY KEY. CREATE TABLE ...
    AS SELECT will not give you one. After your script, the question tries to
    insert a second row for ward 1.

    *Checked: how many columns are the key, the row count, and the sum of admissions*

17. **A note on one stay** (Q748)

    Create `stay_notes (note_id INTEGER PRIMARY KEY, admission_id INTEGER NOT
    NULL, stay_seq INTEGER NOT NULL, note TEXT NOT NULL)` where the PAIR
    (admission_id, stay_seq) must match a row of ward_stays -- a foreign key
    on two columns at once. After your script, the question inserts a note for
    stay (1, 1), one for (1, 9), and one for (999999, 1).

    *Checked: which (admission_id, stay_seq) pairs the notes hold*

18. **An index on an expression** (Q749)

    The query `SELECT COUNT(*) FROM admissions WHERE date(admitted_at) =
    '2026-03-01'` scans the whole table: the index on admitted_at cannot serve
    a condition on date(admitted_at). Create an index named `idx_adm_day` that
    CAN -- an index on the expression itself.

    *Checked: the query plan of that SELECT*

19. **No prescribing after discharge** (Q750)

    Write a BEFORE INSERT trigger on prescriptions that refuses a prescription
    whose started_on is after the day its admission was discharged --
    RAISE(ABORT, ...) -- and lets any other through, including one for an
    admission still open. The check needs to read admissions. After your
    script, the question inserts one for admission 2 starting 2026-03-01, one
    for admission 173 starting 2026-06-20, and one for admission 1 starting
    2026-04-01.

    *Checked: the admission and start date of each new prescription*

20. **Undo everything, not just this row** (Q751)

    Write a BEFORE INSERT trigger on prescriptions that refuses a dose over
    10000 mg with RAISE(ROLLBACK, ...) -- not ABORT. After your script, the
    question runs, as separate statements: BEGIN; an insert of 100 mg with id
    20001; an insert of 20000 mg with id 20002; an insert of 100 mg with id
    20003; COMMIT.

    *Checked: which of the three ids exist afterwards*

# Python

## 1 - First steps (4)

Programs, graded on what they print: print(), arithmetic, variables in an
f-string, and a line read with input().

1. **Say hello** (P001)

   Write a program that prints exactly this line:

   ```
   Hello, hospital!
   ```

   *Print: the line above, punctuation included.*

2. **Three sums** (P002)

   Print three numbers, one per line, each worked out by Python rather than
   typed in:

   ```
   the hours in a 365-day year
   the minutes in a week
   2 to the power of 10
   ```

   *Print: three lines, the numbers only.*

3. **Variables in a sentence** (P003)

   Put the ward name 'Fleming', its 16 beds and its 11 patients in three
   variables, then print two lines built from them:

   ```
   Fleming has 16 beds and 11 patients
   Occupancy: 68.8%
   ```

   The percentage is patients divided by beds times 100, shown to ONE decimal
   place -- use an f-string with a format spec such as {x:.1f}.

   *Print: the two lines.*

4. **Reading a line** (P004)

   Read one line from the keyboard with input() -- it will be a name -- and
   greet it:

   ```
   Good morning, Ada.
   ```

   When you press Run the program is given the line 'Ada' as its input, so you
   cannot type it yourself.

   *Print: the greeting, with the name that was read.*

## 2 - Strings and lists (4)

Functions, graded on what they return: split and index a string, count with a
loop, slice a list, keep the first of a tie.

5. **Initials** (P005)

   Write a function `initials(name)` that returns the first letter of each
   word in the name, each followed by a full stop:

   ```
   initials("Florence Nightingale") -> "F.N."
   ```

   A name can have one word or several. str.split() breaks a string into a
   list of words.

   *Return: the initials as one string.*

6. **Counting vowels** (P006)

   Write a function `count_vowels(text)` that returns how many vowels -- a, e,
   i, o, u -- the text contains, in either case:

   ```
   count_vowels("Observation") -> 5
   ```

   *Return: the count as an integer.*

7. **Every other one** (P007)

   Write a function `every_other(items)` that returns a new list holding the
   first item, the third, the fifth and so on -- the ones at even positions
   counting from 0:

   ```
   every_other([1, 2, 3, 4, 5]) -> [1, 3, 5]
   ```

   A slice can do it in one expression: items[start:stop:step].

   *Return: the new list; an empty list stays empty.*

8. **The longest word** (P008)

   Write a function `longest_word(sentence)` that returns the longest word in
   the sentence. If several tie, return the one that comes FIRST. An empty
   sentence returns an empty string.

   ```
   longest_word("a bb cc") -> "bb"
   ```

   *Return: the word.*

## 3 - Conditions and loops (4)

if/elif with a boundary, for over range(), a while loop that counts, and a
return from inside a loop.

9. **Triage by heart rate** (P009)

   Write a function `triage(heart_rate)` that returns 'high' for a rate over
   100, 'low' for a rate under 60, and 'normal' otherwise. 100 and 60 are both
   normal.

   ```
   triage(101) -> 'high'
   ```

   *Return: one of the three strings.*

10. **The seven times table** (P010)

    Print the seven times table from 1 to 10, one line each, in this form:

    ```
    7 x 1 = 7
    7 x 2 = 14
    ...
    7 x 10 = 70
    ```

    Use a for loop over range(), not ten print statements.

    *Print: ten lines.*

11. **Steps to one** (P011)

    Write a function `collatz_steps(n)` that counts how many steps it takes to
    reach 1 from n, where a step halves an even number and turns an odd number
    into 3n + 1:

    ```
    6 -> 3 -> 10 -> 5 -> 16 -> 8 -> 4 -> 2 -> 1, so collatz_steps(6) -> 8
    ```

    collatz_steps(1) is 0. You do not know in advance how many steps there
    are, so this is a while loop.

    *Return: the number of steps.*

12. **The first negative** (P012)

    Write a function `first_negative_index(nums)` that returns the index of
    the first negative number in the list, or -1 if there is none:

    ```
    first_negative_index([3, 1, -4, 1, -5]) -> 2
    ```

    enumerate(nums) gives you each index with its value; return as soon as you
    find one.

    *Return: an index, or -1.*

## 4 - Functions (4)

Operator precedence, default arguments, a tuple as three answers, and a
comparison returned directly as a boolean.

13. **Body mass index** (P013)

    Write a function `bmi(weight_kg, height_m)` that returns the body mass
    index -- weight divided by the SQUARE of height -- rounded to one decimal
    place:

    ```
    bmi(70, 1.75) -> 22.9
    ```

    *Return: a number with one decimal place.*

14. **Arguments you can leave out** (P014)

    Write a function `course_total_mg(dose_mg, times_per_day, days)` that
    returns the total milligrams over a course: dose times doses per day times
    days. The last two arguments are optional -- times_per_day defaults to 2
    and days to 7 -- so all three of these calls work:

    ```
    course_total_mg(500) -> 7000
    course_total_mg(500, 3) -> 10500
    course_total_mg(250, 4, 5) -> 5000
    ```

    *Return: the total as an integer.*

15. **Three answers at once** (P015)

    Write a function `min_max_mean(nums)` that returns the smallest value, the
    largest, and the mean rounded to two decimal places -- as a TUPLE of
    three:

    ```
    min_max_mean([1, 2, 3, 4]) -> (1, 4, 2.5)
    ```

    min(), max(), sum() and len() do the arithmetic. The list is never empty.

    *Return: a tuple (smallest, largest, mean).*

16. **Reads the same backwards** (P016)

    Write a function `is_palindrome(text)` that returns True when the text
    reads the same backwards as forwards, ignoring case and spaces:

    ```
    is_palindrome("Never odd or even") -> True
    ```

    text[::-1] is the text reversed. An empty string counts as a palindrome.

    *Return: True or False.*

## 5 - Dicts, sets and comprehensions (4)

Counting into a dict with .get(), insertion order as a tiebreak, a set
intersection returned as a sorted list, and try/except around int().

17. **Counting words** (P017)

    Write a function `word_counts(text)` that returns a dictionary from each
    word, lower-cased, to how many times it appears:

    ```
    word_counts("the ward the bed") -> {'the': 2, 'ward': 1, 'bed': 1}
    ```

    dict.get(key, 0) reads a count that may not exist yet.

    *Return: the dictionary; empty text gives an empty one.*

18. **The most common item** (P018)

    Write a function `most_common(items)` that returns the item appearing most
    often. If several tie, return the one that appears FIRST in the list. The
    list is never empty.

    ```
    most_common(["b", "a", "b", "a"]) -> "b"
    ```

    Count into a dictionary first, then look for the largest count; a
    dictionary remembers the order keys were added.

    *Return: the item.*

19. **Prescribed on both wards** (P019)

    Write a function `shared_drugs(ward_a, ward_b)` that takes two lists of
    drug names, possibly with repeats, and returns the names that appear in
    BOTH -- each once, sorted:

    ```
    shared_drugs(["Morphine", "Codeine", "Codeine"], ["Codeine", "Aspirin", "Morphine"]) -> ["Codeine", "Morphine"]
    ```

    A set drops the repeats and & finds what two sets share.

    *Return: a sorted LIST of names.*

20. **Readings that are not numbers** (P020)

    Write a function `parse_readings(strings)` that turns a list of strings
    into a list of integers, SKIPPING any string that is not a whole number:

    ```
    parse_readings(["72", "x", "-5", " 80 ", "3.5"]) -> [72, -5, 80]
    ```

    int(s) converts a string and raises ValueError when it cannot; catch that
    with try/except rather than inspecting the characters yourself.

    *Return: the list of integers, in the original order.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
731 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
