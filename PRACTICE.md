# SQL practice exercises

Thirty questions on a NEW schema: a district hospital, replacing the railway.
Its shape is intervals -- admissions with a start and an end, ward stays,
prescriptions, and a time series of observations -- so alongside the familiar
tiers there is one on **intervals and occupancy** that no earlier schema could
ask. **The last eight are writable**, on constructs none of the five earlier
writable stages used.

| Stage | Questions |
|---|---|
| 1 - Warm-up | 1-3 |
| 2 - Sequences and strings | 4-7 |
| 3 - Dates and times | 8-10 |
| 4 - Intervals and occupancy | 11-14 |
| 5 - Joins and grain | 15-18 |
| 6 - Window functions | 19-22 |
| 7 - Changing the data | 23-30 |

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
that is open instead -- 39 admissions have no discharge, 71
prescriptions have no end -- and every question that measures an open interval
says which end to supply.

## The writable stage

SQLite has no stored procedures, variables, loops or TRY/CATCH. What it has
instead is constraints, triggers, views and DML driven by CTEs -- and each of
questions 23 to 30 is one of those.

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

**Driver statements.** Questions 24, 25, 27, 28 and 29 run statements of their
own *after* yours -- inserts and deletes that your table, trigger, view or
index should refuse, cascade, soften or let through. A refusal is reported in
the status bar as what it is, not as an error.

| # | Construct |
|---|---|
| 23 | `WITH RECURSIVE ... UPDATE`: a tree walk feeding one statement |
| 24 | `AUTOINCREMENT`, and why a plain INTEGER PRIMARY KEY reuses ids |
| 25 | `ON DELETE CASCADE` declared in the table, against the default refusal |
| 26 | a `DEFERRABLE INITIALLY DEFERRED` foreign key, checked at COMMIT |
| 27 | `RAISE(FAIL)` against `RAISE(ABORT)`: how much of a statement is undone |
| 28 | `INSTEAD OF DELETE` on a view -- a soft delete |
| 29 | a partial `UNIQUE` index: a rule that applies only to open rows |
| 30 | `CREATE TEMP TABLE`, the `temp` schema and `sqlite_temp_master` |

## Things the data does on purpose

- **463 of the 2,000 patients have never been admitted**, and patient 6
  is one of them -- which is why question 25 can delete them.
- **39 admissions are still open**, and patient 1500 holds one; they
  have 18 admissions altogether, the most of anyone.
- **176 pairs of admissions of the same patient overlap in time.** The
  ids were not assigned in time order, which is what question 12's trap trips
  on.
- **18 of the 56 staff below the heads report to someone with a HIGHER id**
  than their own, so a one-level UPDATE cannot fill the tree by luck.
- **Three staff have never worked a shift**, one of them a porter.
- **6,488 observations have no temperature and 487 procedures no
  duration**, and three procedure types have never been performed.
- **Ward 1 was empty on 2025-01-01**, as every ward was: the data starts that
  day, so a running occupancy needs no opening balance.

## 1 - Warm-up (3)

Three questions to meet the tables: a per-bed ratio that must not truncate, a
share of all admissions, and two conditions on a consultant's caseload that
belong in HAVING.

1. **Beds and admissions per ward** (Q702)

   One row per ward: its name, how many beds it has, how many admissions it
   has taken (as the admitting ward), and admissions per bed to one decimal.

   *Return: ward, beds, admissions, per_bed*

2. **How patients arrive** (Q703)

   One row per route of admission -- emergency, referral, transfer -- with how
   many admissions came that way and what percentage of all admissions that
   is, to two decimals.

   *Return: admitted_via, admissions, pct*

3. **Busy consultants with long stays** (Q704)

   Consultants with at least 600 completed admissions whose patients' average
   length of stay is over 3.2 days, with both figures -- the average to two
   decimals.

   Length of stay is discharged_at minus admitted_at; julianday() of each
   gives days. Only discharged admissions count.

   *Return: consultant_id, admissions, avg_days*

## 2 - Sequences and strings (4)

`ward_stays` is keyed on (admission_id, stay_seq), like stops were on a service.
LAG along it, initials from a name, a set difference over a patient's history,
and FIRST_VALUE/LAST_VALUE over a time series.

4. **One admission's moves** (Q705)

   Admission 12 moved ward twice. For each of its stays: the ward, how many
   hours it lasted to one decimal, and the ward the patient came FROM -- NULL
   for the first stay.

   ward_stays is keyed on (admission_id, stay_seq).

   *Return: stay_seq, ward_id, hours, from_ward*

5. **Initials** (Q706)

   Patients 1 to 10 with their initials as 'A.B.' -- first letter of each
   name, each followed by a full stop. Every name is two words.

   *Return: patient_id, initials*

6. **Only ever an emergency** (Q707)

   Patients who have been admitted as an emergency and have NEVER been
   admitted any other way.

   *Return: patient_id*

7. **First and last readings** (Q708)

   For admissions 1 to 5, the heart rate at the first observation and at the
   last -- one row per admission, no NULLs.

   FIRST_VALUE and LAST_VALUE; mind the frame on the second.

   *Return: admission_id, first_hr, last_hr*

## 3 - Dates and times (3)

Datetimes are 'YYYY-MM-DD HH:MM' text. A month key across a year boundary, a
time range that wraps midnight, and the first open interval: a stay with no end
yet.

8. **Admissions by month** (Q709)

   For each month, by date of admission: how many admissions, and the average
   completed length of stay in days to one decimal. Eighteen months -- January
   2025 and January 2026 are different months. Still-open admissions count as
   admissions but not in the average.

   *Return: month, admissions, avg_days*

9. **Admitted in the night** (Q710)

   For each route of admission: how many admissions, how many of them arrived
   between 22:00 and 06:00, and the percentage to one decimal.

   The time is the tail of admitted_at, from character 12. The night wraps
   past midnight.

   *Return: admitted_via, admissions, at_night, pct*

10. **Length of stay so far** (Q711)

    For admissions in June 2026, per ward: how many, how many are still in,
    and the average length of stay in days to two decimals AS OF the end of
    the data, 2026-06-30 23:59 -- so a patient still in has been in from
    admission until then.

    Open intervals: an end that is NULL means 'not yet'.

    *Return: ward_id, admissions, still_in, avg_days*

## 4 - Intervals and occupancy (4)

New ground. Who was on a ward at an instant, two intervals that overlap, a
readmission within thirty days of a discharge, and a running occupancy built
from +1 and -1 events.

11. **Who was where at eight o'clock** (Q712)

    How many patients were on each ward at 2026-06-30 08:00, from ward_stays:
    a stay covers that instant if it began at or before it and had not ended
    -- and a stay with no end had not ended.

    *Return: ward_id, patients*

12. **Admitted twice at once** (Q713)

    Pairs of admissions of the SAME patient whose intervals overlap -- a data-
    quality check. Each pair once, the lower admission_id first. An open
    admission runs to the snapshot, 2026-06-30 23:59.

    Two intervals overlap when each starts before the other ends.

    *Return: admission_a, admission_b, patient_id*

13. **Back within thirty days** (Q714)

    For each route of admission: how many admissions, how many of them were
    READMISSIONS -- the same patient had been discharged within the previous
    30 days -- and the percentage to one decimal.

    Measure from the previous DISCHARGE, not the previous admission.

    *Return: admitted_via, admissions, readmissions, pct*

14. **Nightingale, day by day** (Q715)

    For each day in January 2025 on which someone arrived on or left ward 1:
    the net change that day -- arrivals minus departures, by ward_stays -- and
    how many patients were on the ward at the end of it. The ward was empty on
    2025-01-01.

    Turn every stay into a +1 event and a -1 event, then run a total over the
    days.

    *Return: day, net, occupancy*

## 5 - Joins and grain (4)

Two children of one parent, an anti-join that must test the key, a NOT EXISTS
against the right table, and a join on two intervals overlapping instead of two
keys matching.

15. **Procedures and prescriptions, per ward** (Q716)

    For each ward, by admitting ward: how many procedures and how many
    prescriptions its admissions have had.

    Both hang off `admissions`. Joining both at once multiplies each by the
    other.

    *Return: ward_id, procedures, prescriptions*

16. **Never admitted** (Q717)

    Patients who have never been admitted. Write it as an outer join that
    keeps the non-matches.

    *Return: patient_id, name*

17. **Never on the rota** (Q718)

    Staff who have never worked a shift, with their role.

    *Return: staff_id, name, role*

18. **Controlled drugs on Fleming** (Q719)

    For each controlled drug, how many prescriptions of it were running while
    the patient was on ward 5 -- Fleming -- at any point, whether or not they
    were admitted there.

    A prescription runs from started_on to ended_on (dates); a stay from
    from_at to to_at (datetimes, date() them). NULL ends run to 2026-06-30.

    *Return: drug, prescriptions*

## 6 - Window functions (4)

A running total per partition, DENSE_RANK over an aggregate, a share of a
partition, and top-N per group.

19. **Admissions accumulating, per ward** (Q720)

    Admissions by ward and month of admission, with a running total that
    restarts for each ward.

    *Return: ward_id, month, admissions, running_total*

20. **Consultants by caseload** (Q721)

    Every consultant who has admitted anyone, with their number of admissions
    and their rank -- 1 for the most. Two consultants tie; they share a rank,
    and no rank is skipped after them.

    *Return: consultant_id, admissions, rank*

21. **Each route's share of the ward** (Q722)

    For every ward and route of admission: how many admissions, and what
    percentage of THAT WARD's admissions came by that route, to two decimals.
    Each ward's three shares add to 100.

    *Return: ward_id, admitted_via, admissions, pct_of_ward*

22. **The three highest earners per category** (Q723)

    For each category of procedure -- surgical, diagnostic, therapeutic -- the
    three surgeons whose procedures of that category carry the highest total
    tariff, with the total in pence. Nine rows; ties by the lower surgeon_id.

    *Return: category, surgeon_id, tariff_pence*

## 7 - Changing the data (8)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A recursive UPDATE, AUTOINCREMENT, ON
DELETE CASCADE, a deferred foreign key, RAISE(FAIL), a soft delete through a
view, a partial UNIQUE index and a TEMP table.

23. **Fill the division down the tree** (Q724)

    Only the four division heads carry a division; the 56 people under them
    have NULL. Fill every NULL with the division of the head at the top of
    that person's chain, in ONE UPDATE fed by a recursive CTE.

    Managers do not always have lower ids than their reports, so copying from
    the direct manager will not cascade.

    *Checked: staff per division*

24. **An id that is never reused** (Q725)

    Create `incident_log (log_id INTEGER PRIMARY KEY, note TEXT NOT NULL)` so
    that an id, once used, is never handed out again -- even after the row
    that had it is deleted.

    After your script, the question inserts two notes, deletes the second, and
    inserts a third. The third must get id 3, not 2.

    *Checked: SELECT * FROM incident_log*

25. **Notes that go with the patient** (Q726)

    Create `patient_notes (note_id INTEGER PRIMARY KEY, patient_id INTEGER NOT
    NULL referencing patients, note TEXT NOT NULL)` such that deleting a
    patient deletes their notes with them.

    After your script, the question adds two notes for patient 6 -- who has
    never been admitted -- and then deletes patient 6. Both the patient and
    the notes should be gone.

    *Checked: whether patient 6 exists, and how many notes there are*

26. **The child before the parent** (Q727)

    Create `referrals (referral_id INTEGER PRIMARY KEY, patient_id INTEGER NOT
    NULL referencing patients, referred_on TEXT NOT NULL)`, then in one
    transaction insert a referral for patient 2001 -- who does not exist yet
    -- and THEN insert patient 2001 (any name and details), and commit.

    The foreign key has to be DEFERRABLE INITIALLY DEFERRED, or the first
    insert fails.

    *Checked: how many referrals, and whether patient 2001 exists*

27. **Fail the row, keep what came before** (Q728)

    Write a trigger that refuses any observation with a heart rate over 200 --
    but using RAISE(FAIL, ...) rather than ABORT, so that rows already written
    by the same statement stay written.

    After your script, the question inserts three observations for admission 1
    in ONE statement; the third is the bad one. The first two should land.

    *Checked: time and heart rate of admission 1's observations on or after 2026-07-01*

28. **Stop, do not delete** (Q729)

    Create a view `open_prescriptions (prescription_id, admission_id, drug_id,
    started_on)` over the prescriptions with no end date, and make DELETE on
    the view END the prescription -- set ended_on to '2026-07-01' -- rather
    than remove it.

    After your script, the question runs DELETE FROM open_prescriptions WHERE
    prescription_id = 367.

    *Checked: the prescription count, 367's ended_on, and how many are still open*

29. **One open admission per patient** (Q730)

    A patient cannot be admitted twice at once. Enforce it with a UNIQUE index
    on `admissions` that applies only to rows with no discharge -- a partial
    index -- so past admissions do not count.

    After your script, the question inserts two admissions for patient 1500,
    who is currently in: one still open, one already discharged. Only the open
    one should be refused.

    *Checked: how many partial unique indexes admissions has, and patient 1500's admission count*

30. **Scratch space that leaves no trace** (Q731)

    Find the admissions that have run more than 20 days as of 2026-06-30 23:59
    -- open ones included -- and put their ids in a TEMPORARY table
    `long_stays`. Then raise every 'routine' admission in that list to
    'urgent', reading the list from the temp table.

    A temp table lives in the `temp` schema and vanishes with the connection;
    nothing permanent should be left behind.

    *Checked: how many admissions are urgent, whether long_stays exists in the main schema, and whether it exists in temp*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
701 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
