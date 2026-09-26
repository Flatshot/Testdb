# SQL and Python practice exercises

Forty questions in two tabs. **Twenty SQL** on the district hospital -- the
same data as the previous set, with none of its questions -- and **twenty
Python**, each a short program about ONE function or method, named in the
question's title. The Python questions are a step down from the last set on
purpose; the SQL ones are at the level of the previous sets.

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
| 1 - Printing | 1-4 |
| 2 - Strings | 5-9 |
| 3 - Numbers | 10-14 |
| 4 - Lists | 15-18 |
| 5 - Loops | 19-20 |

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
instead is constraints, triggers, views, DDL and DML driven by CTEs -- and
each of questions 16 to 20 is one of those.

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

**Driver statements.** Questions 16, 17 and 18 run statements of their own
*after* yours -- inserts your table should fill in or refuse, and a delete
your foreign key should follow. A refusal is reported in the status bar as
what it is, not as an error.

| # | Construct |
|---|---|
| 16 | `DEFAULT` values: what a column takes when an INSERT leaves it out |
| 17 | `UNIQUE` with `COLLATE NOCASE`: equality that ignores case |
| 18 | `ON DELETE SET NULL`, against the default refusal and against CASCADE |
| 19 | a `WITHOUT ROWID` table with a composite key, filled by a recursive CTE |
| 20 | `ALTER TABLE ... RENAME TO` and `RENAME COLUMN`, and the foreign key that follows |

## Things the data does on purpose

- **487 procedures have no recorded duration**, which question 2's AVG
  leaves out on its own.
- **3 names are shared by two staff each**, which is what question 4
  finds as colliding usernames.
- **1,855 of the 4,479 procedures were performed on a day the surgeon had
  no shift**, so question 11's LEFT JOIN has plenty of non-matches.
- **96 patients have nine or more admissions**, the population of
  question 9; two of admissions 1 to 10 overlap the admission that follows,
  which is question 7's negative gap.
- **The eight wards have 184 beds between them**, the row count question 19
  has to reach.
- **Eighteen months of data**, so a month keyed on '%m' alone merges two
  years -- question 15's trap.

## How the Python questions are graded

Every question in this set is a **program**: the editor holds a whole
program, Run shows what it prints, and Check compares that with the reference
program's output line for line -- trailing spaces and blank lines at the end
are ignored, nothing else is. Where the program is meant to read input(), the
question says what it will be given. Each question is about one function or
method, named in its title, and the prompt says what to print so that you can
tell at once whether you have it. (The grader also supports **function**
questions, where the value returned is compared instead; none in this set.)

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Warm-up (3)

A pivot by conditional aggregation, two conditions on totals that belong in
HAVING, and a per-admission MIN that has to be found before it is averaged.

1. **Priorities, side by side** (Q752)

   One row per consultant who has admitted anyone, with their admissions split
   into three columns by priority: how many were immediate, how many urgent,
   how many routine. Three counts on one row, not three rows.

   *Return: consultant_id, immediate, urgent, routine*

2. **Long operations** (Q753)

   Surgeons who have performed at least 175 procedures and whose average
   recorded duration is over 160 minutes: surgeon_id, their procedures, and
   the average to one decimal. A NULL duration is unknown and simply not
   averaged.

   *Return: surgeon_id, procedures, avg_minutes*

3. **Hours to the first procedure** (Q754)

   For each admitting ward: the average number of hours between admission and
   the FIRST procedure of the admission, to one decimal, over admissions that
   had at least one. Find each admission's earliest performed_at first, then
   average the difference.

   *Return: ward_id, avg_hours*

## 2 - Strings and sequences (2)

lower() and replace() building a username, and CAST turning the tail of a
postcode into a number.

4. **Usernames that collide** (Q755)

   A username is the staff member's name in lower case with the space replaced
   by a full stop: 'Xiu Chowdhury' becomes 'xiu.chowdhury'. Which usernames
   would belong to more than one person, and which staff_ids would share them
   -- as one comma-separated string in id order, such as '17,42'?

   *Return: username, staff_ids*

5. **Leeds districts as numbers** (Q756)

   Patients whose postcode area starts with LS, counted by the district NUMBER
   that follows the letters -- 'LS16' is district 16. Return the district as
   an integer, not text, so that it sorts as a number.

   *Return: district, patients*

## 3 - Dates and times (2)

date() for 'the same calendar day', and LEAD with the row filter kept outside
the window.

6. **In and out the same day** (Q757)

   For each ward, by admitting ward: how many completed admissions it has had,
   how many of them were discharged on the same CALENDAR DAY they were
   admitted, and the percentage to one decimal.

   *Return: ward_id, completed, same_day, pct*

7. **The next admission** (Q758)

   For admissions 1 to 10: when the same patient was NEXT admitted, and the
   days from this admission's discharge to that, to one decimal. NULL in both
   if there was no next admission; negative if the next one began before this
   one ended. LEAD is LAG's mirror.

   *Return: admission_id, next_admitted_at, days_between*

## 4 - Intervals and occupancy (3)

Who was already on the ward at the instant of admission, the longest gap from a
discharge to the next admission, and prescription-days with the open ends
supplied.

8. **Already on the ward** (Q759)

   For admissions 1 to 10: how many OTHER patients were on the admitting ward
   at the moment of admission -- ward_stays on that ward whose interval covers
   admitted_at, not counting this admission's own stay. A stay with no end is
   still running.

   *Return: admission_id, ward_id, already_there*

9. **The longest time away** (Q760)

   For patients with at least NINE admissions: the longest gap, in days to one
   decimal, between being discharged and next being admitted. Measure from the
   previous DISCHARGE, in admission order.

   *Return: patient_id, longest_gap_days*

10. **Days on a drug** (Q761)

    For each drug, the total number of prescription-days as of 2026-06-30:
    each prescription contributes ended_on minus started_on in days, and a
    prescription with no end runs to 2026-06-30. Dates, not datetimes, so the
    answer is a whole number.

    *Return: drug, days*

## 5 - Joins and grain (3)

A LEFT JOIN on a date whose non-matches are the answer, all-or-none by SUM of a
comparison, and COUNT(DISTINCT) against COUNT.

11. **Operating off the rota** (Q762)

    For each surgeon: how many procedures they have performed, and how many of
    those were on a day the surgeon had NO shift in the rota. shifts has one
    row per person per day, so match on staff and on date(performed_at).

    *Return: surgeon_id, procedures, off_rota*

12. **Always routine** (Q763)

    Patients with at least four admissions, EVERY one of which was routine
    priority, with their number of admissions.

    *Return: patient_id, admissions*

13. **How many hands on each ward** (Q764)

    For each ward: how many shifts have been worked there, how many DIFFERENT
    staff have worked them, and shifts per person to one decimal.

    *Return: ward_id, shifts, staff, per_person*

## 6 - Window functions (2)

NTILE quarters ordered by the thing being quartered, and top-1 per group keyed
on a month that includes its year.

14. **Length of stay in quarters** (Q765)

    Split the completed admissions into four equal groups by length of stay --
    NTILE(4) ordered by the stay -- and for each group give the count and the
    shortest, longest and average stay in days, to two decimals.

    *Return: quarter, admissions, shortest, longest, avg_days*

15. **Each ward's busiest month** (Q766)

    For each ward, the month -- 'YYYY-MM' of admitted_at -- in which it took
    the most admissions, with the count. If two months tie, the EARLIER one.

    *Return: ward_id, month, admissions*

## 7 - Changing the data (5)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. DEFAULT values, UNIQUE COLLATE NOCASE,
ON DELETE SET NULL, a WITHOUT ROWID table, and ALTER TABLE RENAME.

16. **Fill in what was left out** (Q767)

    Create `ward_rounds (round_id INTEGER PRIMARY KEY, ward_id INTEGER NOT
    NULL referencing wards, held_on TEXT NOT NULL, start_time TEXT NOT NULL,
    attendees INTEGER NOT NULL)` so that an insert giving only a ward_id
    succeeds, with held_on '2026-07-01', start_time '08:00' and attendees 0
    filled in by the table. After your script, the question inserts a round
    for ward 3 giving nothing else, and one for ward 5 giving a start_time of
    '14:00'.

    *Checked: the four value columns of each round*

17. **Unique whatever the case** (Q768)

    Create `ward_tags (tag_id INTEGER PRIMARY KEY, tag TEXT NOT NULL)` where a
    tag must be unique REGARDLESS OF CASE -- 'Isolation' and 'isolation' are
    the same tag. A collation does it. After your script, the question inserts
    'Isolation', 'isolation', 'ISOLATION' and 'Bariatric', in that order.

    *Checked: the tags that survive, in insertion order*

18. **The booking outlives the theatre** (Q769)

    Create `theatres (theatre_no INTEGER PRIMARY KEY, name TEXT NOT NULL)`
    with rows 1, 2 and 3 (any names), and `theatre_bookings (booking_id
    INTEGER PRIMARY KEY, theatre_no INTEGER referencing theatres, booked_for
    TEXT NOT NULL)` with bookings 1 to 4 for theatres 1, 2, 2 and 3 (any
    text). Deleting a theatre must KEEP its bookings and blank their
    theatre_no. After your script, the question deletes theatre 2.

    *Checked: each booking's theatre_no*

19. **One row per bed, no rowid** (Q770)

    Create `bed_state (ward_id INTEGER NOT NULL referencing wards, bed_no
    INTEGER NOT NULL, admission_id INTEGER referencing admissions, PRIMARY KEY
    (ward_id, bed_no))` as a WITHOUT ROWID table, and fill it with one row per
    bed of every ward -- bed_no 1 up to the ward's beds -- with admission_id
    NULL. A recursive CTE can count to each ward's beds.

    *Checked: whether the table is WITHOUT ROWID, the row count, the highest bed number on ward 5, and how many beds are taken*

20. **Renamed, and still referenced** (Q771)

    Rename the table `procedure_types` to `procedure_catalogue`, and its
    column `tariff_pence` to `price_pence`, with ALTER TABLE -- so that the
    rows, the primary key and the foreign key from procedures all carry over.
    Do not rebuild the table.

    *Checked: whether price_pence exists, how many procedures still join to the catalogue by code, and whether the old name is gone*

# Python

## 1 - Printing (4)

print() with several arguments and with sep=, str() to put a number inside text,
and input() read as a number with int().

1. **print(): two things in one call** (P021)

   Use print() with TWO arguments, separated by a comma, to print the word
   Ward and the number 5 on one line:

   ```
   Ward 5
   ```

   print() puts a space between its arguments for you.

   *Print: that one line.*

2. **print(): choosing the separator** (P022)

   Use print() with three arguments -- the numbers 2026, 6 and 30 -- and its
   sep= option to print them joined by hyphens:

   ```
   2026-6-30
   ```

   *Print: that one line.*

3. **str(): a number inside text** (P023)

   Put the number 16 in a variable called beds. Then use + to join three
   pieces into one string -- 'Fleming has ', the number, and ' beds' -- and
   print it:

   ```
   Fleming has 16 beds
   ```

   + only joins strings, so use str() to turn the number into one first.

   *Print: that one line.*

4. **input(): reading a number** (P024)

   Use input() to read one line -- it will be the number 24 -- turn it into a
   number with int(), add 1 to it, and print the result:

   ```
   25
   ```

   When you press Run the program is given the line '24', so you cannot type
   it yourself.

   *Print: the number one higher than the line read.*

## 2 - Strings (5)

len(), upper() and lower(), replace(), strip() and count() -- and the two
mistakes that go with methods: leaving off the parentheses, and forgetting that
a string method returns a new string.

5. **len(): how long a string is** (P025)

   Put 'Nightingale' in a variable and use len() to print how many characters
   it has:

   ```
   11
   ```

   *Print: the number.*

6. **upper() and lower(): changing case** (P026)

   Put 'Seacole Ward' in a variable. Use the upper() method to print it in
   capitals, then the lower() method to print it in small letters:

   ```
   SEACOLE WARD
   seacole ward
   ```

   *Print: the two lines.*

7. **replace(): swapping part of a string** (P027)

   Put 'Bed 3, Bay 3' in a variable and use the replace() method to change
   every 3 to a 4, then print the result:

   ```
   Bed 4, Bay 4
   ```

   *Print: that one line.*

8. **strip(): trimming spaces** (P028)

   Put ' Bay 3 ' -- three spaces either side -- in a variable. Use the strip()
   method to remove the outer spaces, then print the result between square
   brackets:

   ```
   [Bay 3]
   ```

   *Print: that one line.*

9. **count(): occurrences of a letter** (P029)

   Put 'observation' in a variable and use the count() method to print how
   many times the letter o appears:

   ```
   2
   ```

   *Print: the number.*

## 3 - Numbers (5)

round() with and without a second argument, abs(), max() and min() with several
arguments, int() against float(), and // with %.

10. **round(): a set number of decimals** (P030)

    Use round() to print 37.66666 rounded to one decimal place, and on the
    next line rounded to a whole number:

    ```
    37.7
    38
    ```

    *Print: the two lines.*

11. **abs(): distance from zero** (P031)

    A patient's temperature is 36.2 and the normal figure is 37.0. Put both in
    variables and use abs() to print how far apart they are, as a positive
    number, rounded to one decimal:

    ```
    0.8
    ```

    *Print: the number.*

12. **max() and min(): the largest of several** (P032)

    Three heart-rate readings are 72, 118 and 65. Use max() to print the
    highest and min() to print the lowest, passing the three numbers as three
    arguments:

    ```
    118
    65
    ```

    *Print: the two lines.*

13. **int() and float(): text into numbers** (P033)

    The strings '250' and '2.5' hold a dose and a multiplier. Use int() on the
    first and float() on the second, multiply them, and print the result:

    ```
    625.0
    ```

    *Print: the number.*

14. **// and %: whole hours and the minutes left** (P034)

    A shift lasted 155 minutes. Use // to get the whole hours and % to get the
    minutes left over, and print them as:

    ```
    2 h 35 min
    ```

    *Print: that one line.*

## 4 - Lists (4)

append() returns None, sorted() against sort(), an average from sum() and len(),
and split() with join() the right way round.

15. **append(): adding to a list** (P035)

    Start with the list ['Barry', 'Bevan'] in a variable. Use the append()
    method to add 'Cavell' to the end, then print the list:

    ```
    ['Barry', 'Bevan', 'Cavell']
    ```

    *Print: the list, as print() shows a list.*

16. **sorted(): a list in order** (P036)

    Put the list [118, 72, 65, 90] in a variable and use sorted() to print it
    from smallest to largest:

    ```
    [65, 72, 90, 118]
    ```

    *Print: the sorted list.*

17. **sum() and len(): an average** (P037)

    Put the list [36.8, 37.2, 38.1, 36.9] in a variable. Use sum() and len()
    to work out the average and print it rounded to one decimal:

    ```
    37.2
    ```

    *Print: the number.*

18. **split() and join(): text to list and back** (P038)

    Put 'Morphine Codeine Diazepam' in a variable. Use the split() method to
    break it into a list and print the list, then use the join() method with
    ', ' to put it back together and print that:

    ```
    ['Morphine', 'Codeine', 'Diazepam']
    Morphine, Codeine, Diazepam
    ```

    *Print: the two lines.*

## 5 - Loops (2)

range() and where it stops, and a first for loop with the print inside it.

19. **range(): the numbers 1 to 5** (P039)

    Use range() inside list() to build the list of numbers from 1 to 5 and
    print it:

    ```
    [1, 2, 3, 4, 5]
    ```

    range() itself prints as range(1, 6); list() turns it into a real list.

    *Print: the list.*

20. **for: one line per item** (P040)

    Put the list ['Fleming', 'Jenner', 'Lister'] in a variable and use a for
    loop to print each ward on its own line, followed by ' ward':

    ```
    Fleming ward
    Jenner ward
    Lister ward
    ```

    *Print: the three lines.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
771 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
