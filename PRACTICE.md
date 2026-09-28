# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the district hospital -- the
same data as the previous sets, with none of their questions, and a step
easier than they were -- and **fifteen Python**, each a short program about
ONE function, method or keyword, named in the question's title, on tools the
last set did not cover.

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
| 1 - More strings | 1-3 |
| 2 - Lists | 4-10 |
| 3 - Numbers and types | 11-13 |
| 4 - Loops | 14-15 |

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

**No driver statements this time.** The probe reads what your script left
behind, and nothing else runs in between.

| # | Construct |
|---|---|
| 13 | an `UPDATE` with arithmetic in the SET and a `WHERE` that keeps it to one role |
| 14 | `ALTER TABLE ... DROP COLUMN`, against blanking the values |
| 15 | `DROP INDEX` and `CREATE INDEX`: an index replaced, not merely added to |

## Things the data does on purpose

- **The least prescribed drug has 263 prescriptions**, so question 2's
  threshold of 330 keeps only four.
- **315 admissions had a third stay**, which is why question 4 says
  exactly 2 and not 2 or more.
- **22 prescriptions running on 2026-06-28 have no end date**, and
  they are the ones question 7's trap drops.
- **240 patients have no recorded blood group**, the population of
  question 9.
- **Staff 1 to 4 are the division heads**, with a NULL reports_to, so
  question 10's inner join loses four of its ten rows.
- **Patient 1500 has 18 admissions**, and the ids were not dealt in time
  order -- the first admission has id 2415.
- **There are 5 porters**, so question 13's UPDATE should change five
  rows and no more.

## How the Python questions are graded

Every question in this set is a **program**: the editor holds a whole
program, Run shows what it prints, and Check compares that with the reference
program's output line for line -- trailing spaces and blank lines at the end
are ignored, nothing else is. Each question is about one function, method or
keyword, named in its title, and the prompt says what to print so that you
can tell at once whether you have it. Several traps in this set raise an
error rather than print the wrong thing; the output pane shows the traceback,
and the last line of it names the mistake. (The grader also supports
**function** questions, where the value returned is compared instead; none in
this set.)

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Warm-up (2)

Which table answers the question, and a condition on a count that has to be
HAVING.

1. **The price list** (Q772)

   One row per category in procedure_types -- the catalogue of what CAN be
   done, not the procedures performed: the cheapest, the dearest and the
   average tariff of the types listed, in POUNDS to two decimals. Tariffs are
   stored in pence.

   *Return: category, cheapest, dearest, average*

2. **The most prescribed** (Q773)

   Drugs that have been prescribed more than 330 times, with the count. The
   condition is on the count, so it cannot go in WHERE.

   *Return: drug, prescriptions*

## 2 - Strings and sequences (2)

substr() counts from 1, and stay_seq = 2 is an equality, not a range.

3. **Three-letter ward codes** (Q774)

   Every ward with a code made from the first three letters of its name in
   upper case -- 'Nightingale' gives 'NIG'. substr(text, start, length) counts
   from 1.

   *Return: ward_id, name, code*

4. **Where the second stay was** (Q775)

   For each ward, how many admissions had their SECOND stay there -- stay_seq
   exactly 2 in ward_stays. A third stay does not count.

   *Return: ward_id, second_stays*

## 3 - Dates and times (2)

strftime() returns text until you CAST it, and two datetimes have to go through
julianday() before they can be subtracted.

5. **Admissions by year** (Q776)

   How many admissions there were in each year, with the year as a NUMBER.
   strftime('%Y', ...) gives the year as text.

   *Return: year, admissions*

6. **How long admissions 1 to 5 lasted** (Q777)

   For admissions 1 to 5, the length of stay in days to one decimal:
   discharged_at minus admitted_at. They are text, so turn each into a number
   of days with julianday() before subtracting.

   *Return: admission_id, days*

## 4 - Intervals and occupancy (2)

A day inside an interval, and two intervals that touch -- both with the open end
supplied by COALESCE.

7. **Running on the last Sunday** (Q778)

   For each drug that had at least one, how many prescriptions were running on
   2026-06-28: started on or before that day and not ended before it. A
   prescription with no end date is still running.

   *Return: drug, running*

8. **Touching the last weekend** (Q779)

   For each ward, how many ward stays overlapped the weekend of 2026-06-27 and
   2026-06-28 at all -- began before the weekend ended and had not ended
   before it began. An open stay has not ended.

   *Return: ward_id, stays*

## 5 - Joins and grain (2)

IS NULL where = NULL finds nothing, and a self LEFT JOIN that keeps the people
with no manager.

9. **Blood group unknown** (Q780)

   For each admitting ward, how many admissions were of a patient whose blood
   group is not recorded -- NULL in patients.

   *Return: ward_id, admissions*

10. **Who each person reports to** (Q781)

    Staff 1 to 10 with the NAME of the person they report to. The four
    division heads report to nobody, and must still appear, with NULL for the
    manager.

    *Return: staff_id, name, manager*

## 6 - Window functions (2)

ROW_NUMBER ordered by the column that matters, and SUM() OVER () for a share of
the whole.

11. **Patient 1500's admissions, numbered** (Q782)

    Every admission of patient 1500 -- the most admitted patient -- numbered
    1, 2, 3 ... in the order they happened. Ids are not in time order, so
    number by admitted_at.

    *Return: n, admission_id, admitted_at*

12. **Each ward's share of the beds** (Q783)

    Every ward with its beds and what percentage of ALL the hospital's beds
    that is, to one decimal. A window SUM with an empty OVER () gives the
    total on every row.

    *Return: ward_id, beds, pct_of_beds*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. An UPDATE that must have a WHERE, DROP
COLUMN, and replacing an index.

13. **A rise for the porters** (Q784)

    Give every porter a 5 per cent rise, rounded to the nearest whole pound,
    and nobody else anything. One UPDATE.

    *Checked: the total salary of each role*

14. **A column nobody needs** (Q785)

    Remove the `floor` column from wards -- the column itself, not its values
    -- leaving the other four columns and all eight rows as they are.

    *Checked: the columns of wards, in order, and its row count*

15. **Swap one index for another** (Q786)

    observations has an index `idx_obs_taken` on taken_at alone. Replace it:
    drop that index, and create `idx_obs_by` on (taken_by, taken_at), so that
    a lookup by the nurse and then by time can use it. The other index on the
    table stays.

    *Checked: the names of the table's indexes, and the columns of idx_obs_by in order*

# Python

## 1 - More strings (3)

title() against capitalize(), startswith() against ==, and find() against
index() on a miss.

1. **title(): a capital on every word** (P041)

   Put 'florence nightingale' in a variable and use the title() method to
   print it with a capital letter on each word:

   ```
   Florence Nightingale
   ```

   *Print: that one line.*

2. **startswith(): does it begin with** (P042)

   Put the procedure code 'SRG-04' in a variable. Use the startswith() method
   to print whether it begins with 'SRG', then whether it begins with 'DIA':

   ```
   True
   False
   ```

   *Print: the two lines.*

3. **find(): where a character is** (P043)

   Put 'SRG-04' in a variable. Use the find() method to print the position of
   the hyphen, then the result of looking for a letter that is not there, 'X':

   ```
   3
   -1
   ```

   Positions count from 0.

   *Print: the two lines.*

## 2 - Lists (7)

The in test, index(), pop(), insert(), remove(), sorted() with reverse=True, and
len() on a list -- with the errors each one raises when it is used like its
neighbour.

4. **in: is it in the list** (P044)

   Put the list ['Morphine', 'Codeine', 'Diazepam'] in a variable. Use the in
   test to print whether 'Codeine' is in it, then whether 'Aspirin' is:

   ```
   True
   False
   ```

   *Print: the two lines.*

5. **index(): where in the list** (P045)

   Put ['Morphine', 'Codeine', 'Diazepam'] in a variable and use the index()
   method to print the position of 'Codeine':

   ```
   1
   ```

   *Print: the number.*

6. **pop(): take the last one off** (P046)

   Put [72, 118, 65] in a variable. Use the pop() method to remove the LAST
   item, print the item that was removed, then print the list:

   ```
   65
   [72, 118]
   ```

   *Print: the two lines.*

7. **insert(): put it at a position** (P047)

   Put ['Barry', 'Cavell'] in a variable. Use the insert() method to put
   'Bevan' at position 1 -- between the two -- then print the list:

   ```
   ['Barry', 'Bevan', 'Cavell']
   ```

   *Print: the list.*

8. **remove(): take out by value** (P048)

   Put ['Barry', 'Bevan', 'Cavell'] in a variable. Use the remove() method to
   take out 'Bevan' -- by its value, not its position -- then print the list:

   ```
   ['Barry', 'Cavell']
   ```

   *Print: the list.*

9. **sorted(reverse=True): largest first** (P049)

   Put [72, 118, 65, 90] in a variable and use sorted() with its reverse=
   option to print the list from largest to smallest:

   ```
   [118, 90, 72, 65]
   ```

   *Print: the sorted list.*

10. **len(): how many in the list** (P050)

    Put ['Barry', 'Bevan', 'Cavell', 'Fleming'] in a variable and use len() to
    print how many wards the list holds:

    ```
    4
    ```

    *Print: the number.*

## 3 - Numbers and types (3)

A .2f format spec where round() does not help, divmod() unpacked into two names,
and type() on three values that look alike.

11. **f'{x:.2f}': two decimal places** (P051)

    A dose costs 180 pence. Put that in a variable, divide by 100 to get
    pounds, and use an f-string with the format spec .2f to print it with two
    decimal places and a pound sign:

    ```
    £1.80
    ```

    *Print: that one line.*

12. **divmod(): quotient and remainder at once** (P052)

    A shift lasted 155 minutes. Use divmod() to get the whole hours and the
    minutes left over in ONE call, unpack the pair into two variables, and
    print:

    ```
    2 h 35 min
    ```

    *Print: that one line.*

13. **type(): what kind of value** (P053)

    Use type() to print the type of 3, of 3.0 and of '3', one per line,
    exactly as Python shows them:

    ```
    <class 'int'>
    <class 'float'>
    <class 'str'>
    ```

    *Print: the three lines.*

## 4 - Loops (2)

enumerate() with a start value, and a while loop that has to change its own
variable.

14. **enumerate(): numbering as you loop** (P054)

    Put ['Fleming', 'Jenner', 'Lister'] in a variable and use a for loop with
    enumerate() to print each ward with its number, counting from 1:

    ```
    1. Fleming
    2. Jenner
    3. Lister
    ```

    enumerate() takes a second argument for where to start.

    *Print: the three lines.*

15. **while: repeat until a condition fails** (P055)

    Start a variable at 3 and use a while loop to count down, printing the
    number each time, until it reaches 0; then print Go:

    ```
    3
    2
    1
    Go
    ```

    Something inside the loop has to change the variable, or the loop never
    ends.

    *Print: the four lines.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
811 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
