# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the district hospital -- the
same data as the previous sets, with none of their questions, and back at
the level of the sets before the easy one -- and **fifteen Python**, each a
short program about ONE tool, named in the question's title, this time on
dictionaries, tuples, slices and string tests.

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
| 1 - Dictionaries | 1-7 |
| 2 - Tuples and slices | 8-10 |
| 3 - String tests | 11-13 |
| 4 - Two lists at once | 14-15 |

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

**Driver statements.** All three writable questions run statements of their
own *after* yours -- a rename your foreign key should follow, inserts your
CHECK should sort, and an UPDATE your trigger should redirect. A refusal is
reported in the status bar as what it is, not as an error.

| # | Construct |
|---|---|
| 13 | `ON UPDATE CASCADE`: a parent key renamed and the children following |
| 14 | `CHECK (json_valid(payload))`: a constraint that calls a function |
| 15 | `INSTEAD OF UPDATE` on a view, with OLD to say which row |

## Things the data does on purpose

- **9 surnames are shared by three or more staff**, Papadopoulos by
  eight, which is question 3's answer.
- **Consecutive stays are never on the same ward**, so 'back where they
  started' can only mean stay 3 -- 34 admissions did it.
- **The longest completed stay is 27 days**, so question 5's trap of
  'over 30 days' finds nothing at all.
- **296 pairs of same-drug prescriptions overlap**, on all forty drugs,
  the population of question 8.
- **Every one of the 30 days of June 2026 has an admission**, so
  question 11's moving average needs no calendar.
- **Patient 3 lives in LS7** until question 15's driver moves them to LS99;
  a trigger body without a WHERE moves all 2,000.

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

An average of products, which is not a product of averages, and a share that
needs the whole group in HAVING.

1. **Milligrams a day, by form** (Q787)

   For each form of drug: how many prescriptions, the average DAILY dose in mg
   to one decimal -- dose_mg times times_per_day, averaged over prescriptions
   -- and the largest daily dose.

   *Return: form, prescriptions, avg_daily_mg, max_daily_mg*

2. **Mostly emergencies** (Q788)

   Consultants for whom at least 55 per cent of admissions came in as
   emergencies: consultant_id, admissions, emergencies, and the percentage to
   one decimal.

   *Return: consultant_id, admissions, emergencies, pct*

## 2 - Strings and sequences (2)

Surnames cut one past the space, and the first and third stays of an admission
joined with both sequence numbers pinned.

3. **Surnames on the payroll** (Q789)

   Surnames shared by THREE or more staff, with how many, and their staff_ids
   as one comma-separated string in id order. The surname is everything after
   the single space in the name.

   *Return: surname, people, staff_ids*

4. **Back where they started** (Q790)

   Admissions that moved ward twice and ended up back on the ward they were
   admitted to -- stay 3 on the same ward as stay 1 -- counted per ward. Two
   rows of ward_stays for one admission, joined.

   *Return: ward_id, returned*

## 3 - Dates and times (2)

A month boundary crossed, tested by comparing 'YYYY-MM' strings, and the
difference between %W and %U.

5. **Crossing the month end** (Q791)

   For each month of admission, 'YYYY-MM': how many completed admissions began
   in it, how many of them were discharged in a LATER month than they were
   admitted, and the percentage to one decimal. Compare months, not lengths of
   stay.

   *Return: month, admissions, crossed, pct*

6. **Weeks that start on Monday** (Q792)

   Admissions per week of 2026, for weeks 1 to 10, with the week as an
   integer. A week starts on MONDAY, and week 1 is the first week with a
   Monday in it -- which is what strftime('%W') numbers. Its sibling '%U'
   starts weeks on Sunday.

   *Return: week, admissions*

## 4 - Intervals and occupancy (2)

A per-ward peak from a running sum over every event, and two prescriptions of
one drug whose date ranges overlap.

7. **Each ward's peak in June** (Q793)

   The most patients each ward held at any one instant during June 2026. Turn
   every ward stay into a +1 event at from_at and a -1 at to_at, run a total
   per ward in time order over ALL events, and take the highest value reached
   at an event inside June. At the same instant, count the departure before
   the arrival.

   *Return: ward_id, peak*

8. **Twice at once** (Q794)

   For each drug, how many admissions had two prescriptions of it RUNNING AT
   THE SAME TIME -- two rows of prescriptions for the same admission and drug
   whose date ranges overlap. Count each admission once. An open prescription
   runs to 2026-06-30.

   *Return: drug, admissions*

## 5 - Joins and grain (2)

A correlated subquery for the ward's own average, and three one-to-many children
counted without multiplying each other.

9. **Longer than the ward's usual** (Q795)

   For completed admissions that began in June 2026, per admitting ward: how
   many there were, and how many lasted longer than THAT WARD's average
   completed length of stay over all time. The comparison is against the
   ward's own average, so it is a correlated subquery.

   *Return: ward_id, admissions, above_average*

10. **Three children of one admission** (Q796)

    For admissions 1 to 10: how many ward stays, procedures and prescriptions
    each has. Three tables hang off admissions, and joining all three at once
    multiplies each count by the other two.

    *Return: admission_id, stays, procedures, prescriptions*

## 6 - Window functions (2)

A ROWS frame for a moving average, and rn = 2 for second place per group.

11. **A week's worth, smoothed** (Q797)

    For each day of June 2026: the admissions that day, and the seven-day
    moving average -- that day and the six before it, to two decimals. Days
    early in the month average over what there is. Every day of June has
    admissions, so a calendar is not needed.

    *Return: day, admissions, avg7*

12. **Second-longest stay on each ward** (Q798)

    For each admitting ward, the SECOND-longest completed admission: its id
    and its length in days to two decimals. Ties by the lower admission_id.

    *Return: ward_id, admission_id, days*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. ON UPDATE CASCADE, a CHECK that calls
json_valid(), and INSTEAD OF UPDATE on a view.

13. **Rename the key and the children follow** (Q799)

    Create `ward_codes (code TEXT PRIMARY KEY, ward_id INTEGER NOT NULL
    referencing wards)` and `ward_sections (section_id INTEGER PRIMARY KEY,
    code TEXT NOT NULL referencing ward_codes, label TEXT NOT NULL)`, such
    that changing a code in ward_codes changes it in every section that uses
    it. Insert codes 'NIG' for ward 1 and 'SEA' for ward 2, and sections 'bay
    A' and 'bay B' under NIG and 'bay A' under SEA. After your script, the
    question renames NIG to 'NGT'.

    *Checked: each section's code, in section order*

14. **A column that must hold JSON** (Q800)

    Create `device_readings (reading_id INTEGER PRIMARY KEY, admission_id
    INTEGER NOT NULL referencing admissions, payload TEXT NOT NULL)` where
    payload must be VALID JSON -- a CHECK constraint can call json_valid().
    After your script, the question inserts three payloads for admission 1:
    '{"spo2": 97}', 'spo2=97' and '[97, 98]'.

    *Checked: the payloads that were accepted, in insertion order*

15. **Editing through a view** (Q801)

    Create a view `patient_contact (patient_id, name, postcode_area)` over
    patients, and make an UPDATE of postcode_area on the VIEW change the
    patient underneath -- an INSTEAD OF UPDATE trigger. After your script, the
    question runs UPDATE patient_contact SET postcode_area = 'LS99' WHERE
    patient_id = 3.

    *Checked: patient 3's postcode in the table, and how many patients have postcode LS99*

# Python

## 1 - Dictionaries (7)

Square brackets against get(), assigning a new key, keys() and values() as
views, items() unpacked in a loop, and len().

1. **dict: a value by its key** (P056)

   Make a dictionary from ward names to beds: 'Fleming' 16, 'Barry' 30,
   'Jenner' 18. Look up Fleming with square brackets and print its beds:

   ```
   16
   ```

   *Print: the number.*

2. **get(): a lookup that may miss** (P057)

   With the same dictionary -- 'Fleming' 16, 'Barry' 30, 'Jenner' 18 -- use
   the get() method to print the beds for 'Bevan', which is not there, with 0
   as the fallback; then get() 'Barry' the same way:

   ```
   0
   30
   ```

   *Print: the two lines.*

3. **dict[key] = value: adding an entry** (P058)

   Start with the dictionary 'Fleming' 16, 'Barry' 30. Add 'Jenner' with 18 by
   assigning to a new key, then print the dictionary:

   ```
   {'Fleming': 16, 'Barry': 30, 'Jenner': 18}
   ```

   *Print: the dictionary, as print() shows one.*

4. **keys(): the keys as a list** (P059)

   With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18, use the keys()
   method inside list() to print the ward names as a list:

   ```
   ['Fleming', 'Barry', 'Jenner']
   ```

   *Print: the list.*

5. **values(): adding them up** (P060)

   With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18, use sum() over
   the values() method to print the total beds:

   ```
   64
   ```

   *Print: the number.*

6. **items(): key and value together** (P061)

   With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18, loop over the
   items() method to print one line per ward:

   ```
   Fleming: 16
   Barry: 30
   Jenner: 18
   ```

   *Print: the three lines.*

7. **len(): how many entries** (P062)

   With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18, use len() to
   print how many wards it holds:

   ```
   3
   ```

   *Print: the number.*

## 2 - Tuples and slices (3)

A tuple unpacked into two names, [start:stop] on a string, and a string
multiplied.

8. **tuple: a pair that cannot change** (P063)

   Put the blood pressure reading 120 over 80 in a tuple called bp. Unpack it
   into two names, systolic and diastolic, and print them as:

   ```
   120/80
   ```

   *Print: that one line.*

9. **[start:stop]: a piece of a string** (P064)

   Put the procedure code 'SRG-04' in a variable. Use slicing to print the
   first three characters, then the last two:

   ```
   SRG
   04
   ```

   *Print: the two lines.*

10. **'-' * n: repeating a string** (P065)

    Print a line of 20 hyphens, then the word Ward, then another line of 20
    hyphens, using multiplication to make the lines:

    ```
    --------------------
    Ward
    --------------------
    ```

    *Print: the three lines.*

## 3 - String tests (3)

endswith() against in, isdigit() against type(), and if/else so that only one
line prints.

11. **endswith(): the end of a string** (P066)

    Two file names: 'report.pdf' and 'pdf_notes.txt'. Use the endswith()
    method to print whether each ends with '.pdf':

    ```
    True
    False
    ```

    *Print: the two lines.*

12. **isdigit(): is it all digits** (P067)

    Two strings read from a form: '0420' and '42a'. Use the isdigit() method
    to print whether each is made of digits only:

    ```
    True
    False
    ```

    *Print: the two lines.*

13. **if/else: one of two lines** (P068)

    Put 'Codeine' in a variable and the list ['Morphine', 'Codeine',
    'Fentanyl'] in another. Use if/else with the in test to print 'controlled'
    when the drug is in the list and 'not controlled' otherwise:

    ```
    controlled
    ```

    *Print: the one line that applies.*

## 4 - Two lists at once (2)

zip() to walk two lists in step, and max() with key= to pick by a rule.

14. **zip(): walking two lists together** (P069)

    Two lists in step: wards ['Fleming', 'Barry', 'Jenner'] and beds [16, 30,
    18]. Use zip() in a for loop to print each ward with its beds:

    ```
    Fleming 16
    Barry 30
    Jenner 18
    ```

    *Print: the three lines.*

15. **max(key=): the biggest by a rule** (P070)

    With the dictionary 'Fleming' 16, 'Barry' 30, 'Jenner' 18, use max() with
    key=beds.get to print the name of the ward with the most beds:

    ```
    Barry
    ```

    *Print: the name.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
841 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
