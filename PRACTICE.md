# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
fourth set on this schema and a revision set: five tiers that pair up
concepts the earlier library sets introduced, every question new, plus the
writable tier. **Fifteen Python** in three shapes: five one-tool functions,
five with a loop or an if, five over library-shaped rows.

| Stage | SQL questions |
|---|---|
| 1 - Dates and set operations | 1-2 |
| 2 - Grain and CASE | 3-4 |
| 3 - Windows and recursion | 5-7 |
| 4 - EXISTS and text | 8-10 |
| 5 - Intervals and NULLs | 11-12 |
| 6 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - One tool | 1-5 |
| 2 - A loop or an if | 6-10 |
| 3 - Library rows | 11-15 |

## The schema

Nine tables. `books` are titles; `copies` are the physical things, each at a
`branch`, in some condition, perhaps withdrawn. `loans` is the centre: a copy,
a member, `loaned_on`, a `due_on` that already includes any renewals, and a
`returned_on` that is NULL while the book is still out. `holds` is a queue --
members waiting for a book, ordered by `placed_at`, each ending in a
fulfilment, a cancellation, or neither yet. `fines` hang off loans: a late
return costs 20p a day, capped, paid or not. `members` have a home branch and
`copies` have a branch, two foreign keys to the same table. `staff` work at a
branch; `authors` wrote the books. Double-click a table in the left pane to
see its columns.

**Dates are text**, 'YYYY-MM-DD', and `holds.placed_at` is a datetime,
'YYYY-MM-DD HH:MM'. They compare correctly as text; `julianday()` turns
either into a number of days you can subtract, and `date()` cuts a datetime
to its day.

**The data ends at 2026-06-30.** Anything that would have ended after that is
open instead -- 685 loans have no return date, 118 of them already
past due; 337 holds are still waiting; 1,380 fines are unpaid.

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

**Driver statements.** Question 13 runs two updates of its own *after* your
script -- a late return and an on-time one, which your trigger should price
and ignore respectively. Questions 14 and 15 are graded on what your script
leaves behind.

| # | Construct |
|---|---|
| 13 | `AFTER UPDATE OF returned_on ... WHEN OLD.returned_on IS NULL AND NEW.returned_on > NEW.due_on` |
| 14 | an `UPDATE` whose WHERE holds `(SELECT COUNT(*) FROM loans l WHERE l.copy_id = copies.copy_id)` |
| 15 | a `VIEW` of a grouped query, with the WHERE before the GROUP BY |

## Things the data does on purpose

- **810 members have both a fine and a hold** -- question 2's
  INTERSECT; the UNION is four hundred larger.
- **140 fines sit exactly at the 1,000-pence cap**, question 4's own
  band, which a CASE in the wrong order never reaches.
- **7 books have a copy at every branch, but 135 have six
  or more copies** -- six copies is not six branches, which is question 8.
- **1,238 members have had two loans out at once, 1,230 if the
  open loans are ignored** -- question 11's COALESCE is worth the
  difference.
- **No copy has been loaned more than 18 times**, and 62
  good copies have reached 15 -- the rows question 14's UPDATE touches.
- **719 members owe something**, question 15's view; member 1149 owes
  6,480 pence, the most.
- **Loan 4107 is out and was due 2026-06-20; loan 6876 is out too** -- the
  two returns question 13's trigger must tell apart.

## How the Python questions are graded

Every question in this set is a **function**: the editor defines a function
with the name the question gives, Run calls it once for each test input and
shows every call and its result in the output pane, and Check compares each
result with the reference function's. Values are compared, not their printed
form, so a dictionary in a different order is the same dictionary -- but the
type counts: a tuple is not a list, a set is not a list, and 0 is not False.
A function that prints its answer instead of returning it returns None, and
None matches nothing. Each question here is one or two lines about one tool,
named in its title.

Your code runs in a separate interpreter with a five-second limit, so a loop
that never ends is stopped and reported, not fatal. It cannot see the
database, the app, or any file. Tab inserts four spaces and Return keeps the
indentation of the line above.

# SQL

## 1 - Dates and set operations (2)

strftime's %w against its %W, and INTERSECT against UNION with the fine reaching
its member through loans.

1. **Loans by day of the week** (Q892)

   How many loans started on each day of the week, with the day as strftime's
   %w gives it: '0' for Sunday through '6' for Saturday.

   *Return: weekday, loans*

2. **Fined and waiting** (Q893)

   Members who have had a fine -- any fine, paid or not -- AND have placed a
   hold -- any hold. Use INTERSECT between a query over fines, joined to loans
   for the member, and a query over holds.

   *Return: member_id*

## 2 - Grain and CASE (2)

Two children of one parent counted without multiplying them together, and bands
whose WHENs have to be tested narrowest first.

3. **Staff and copies, per branch** (Q894)

   For each branch: how many staff work there and how many copies it holds.
   Staff and copies are two separate children of a branch, and joining both to
   branches in one FROM multiplies them together.

   *Return: branch_id, staff, copies*

4. **Fines in bands** (Q895)

   Put every fine in a band by amount_pence and count and total each band:
   'small' up to 100, 'medium' up to 500, 'capped' when exactly 1000 -- the
   cap -- and 'large' for the rest. The order of the WHENs is part of the
   answer.

   *Return: band, fines, pence*

## 3 - Windows and recursion (3)

ROW_NUMBER with a tie-break against RANK for position 2, LAG over the previous
RETURN rather than the previous start, and a recursive calendar of weeks with a
half-open boundary.

5. **The runner-up in each genre** (Q896)

   For each genre, the SECOND most borrowed book: its book_id and loan count.
   Order books within a genre by loans descending, ties broken by the lower
   book_id, and take the one in position 2 -- ROW_NUMBER, not RANK.

   *Return: genre, book_id, loans*

6. **How long copy 1 sat on the shelf** (Q897)

   For each loan of copy 1, in order of loaned_on: loan_id, loaned_on, and the
   number of days between the PREVIOUS loan's return and this loan's start --
   NULL for the first. LAG over returned_on, then julianday arithmetic.

   *Return: loan_id, loaned_on, shelf_days*

7. **Twelve weeks of loans** (Q898)

   For each of the twelve weeks starting Monday 2026-01-05: the week's first
   day and how many loans started in it -- from that Monday up to but NOT
   including the next. Build the Mondays with a recursive CTE, date(start, '+7
   days').

   *Return: week_start, loans*

## 4 - EXISTS and text (3)

A double NOT EXISTS for 'at every branch', where six copies is not six branches;
words by LENGTH and REPLACE plus one; initials by || with the +1 past the space.

8. **Stocked at every branch** (Q899)

   Books that have at least one copy at EVERY branch -- all six. 'Every' is a
   double negative: no branch exists at which no copy of the book exists.

   *Return: book_id, title*

9. **Words per title** (Q900)

   How many titles have two words, three, four and five. Count the spaces --
   LENGTH of the title minus LENGTH with the spaces removed -- and remember
   that words are one more than spaces.

   *Return: words, titles*

10. **Staff initials** (Q901)

    Each staff member's initials: the first letter of the name and the first
    letter after the space, joined with ||. SUBSTR takes (text, start, length)
    and INSTR finds the space.

    *Return: staff_id, initials*

## 5 - Intervals and NULLs (2)

Two loans of one member overlapping, with the open end supplied by COALESCE, and
holds counted three ways by COUNT(column) and SUM of a boolean.

11. **Two books out at once** (Q902)

    For each home branch, how many of its members have at some point had two
    loans out at the same time: two loans of theirs whose intervals overlap, a
    loan still out running to the end of the data. Pair each loan with a later
    loan_id of the same member, and supply the open end with COALESCE.

    *Return: home_branch_id, members*

12. **Holds, three ways, per branch** (Q903)

    For each branch the hold was placed at: holds placed, how many were
    fulfilled, how many cancelled, and how many are still waiting -- neither.
    COUNT(column) counts the non-NULL values, and waiting is not 'placed minus
    fulfilled'.

    *Return: branch_id, placed, fulfilled, cancelled, waiting*

## 6 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. An AFTER UPDATE trigger with OLD and
NEW in its WHEN, an UPDATE whose WHERE counts another table, and a view with the
WHERE that makes it a view of debts.

13. **A fine the moment a book comes back late** (Q904)

    Write an AFTER UPDATE trigger on loans that fires when returned_on changes
    from NULL to a date AFTER due_on, and inserts a fine for that loan: 20
    pence a day late, capped at 1000, issued_on the return date. A return on
    or before due_on raises nothing. The question then returns loan 4107 (due
    2026-06-20) on 2026-07-10, and loan 6876 on its due date.

    *Checked: how many new fines there are, the amount of loan 4107's, and whether loan 6876 is marked returned*

14. **Well-thumbed copies** (Q905)

    Mark as 'worn' every copy in 'good' condition that has been loaned 15
    times or more. Copies already worn or damaged are left as they are,
    whatever their loan count. The count is a correlated subquery in the
    WHERE.

    *Checked: how many copies are in each condition*

15. **What each member owes** (Q906)

    Create a view `member_debts (member_id, owed_pence)` with one row per
    member who has at least one UNPAID fine, and the total of their unpaid
    fines. Members with no unpaid fines are not in the view, nor are paid
    fines in the total.

    *Checked: how many members the view holds, what they owe in all, and member 1149's row*

# Python

## 1 - One tool (5)

endswith() with a tuple against 'or', round(n, -2), split(maxsplit=1),
enumerate(start=1), and ljust() against rjust().

1. **endswith(tuple): is it an image file?** (P161)

   Write a function `is_image(filename)` that returns True when the name ends
   in '.jpg', '.png' or '.gif' -- exactly those, lower case -- using
   endswith() with a TUPLE of endings:

   ```
   is_image("cover.jpg") -> True
   is_image("cover.PNG") -> False
   ```

   *Return: True or False.*

2. **round(n, -2): to the nearest hundred** (P162)

   Write a function `nearest_hundred(n)` that returns n rounded to the nearest
   hundred, using round() with a NEGATIVE second argument:

   ```
   nearest_hundred(1234) -> 1200
   ```

   *Return: an integer.*

3. **split(maxsplit=1): the first word and the rest** (P163)

   Write a function `first_and_rest(title)` that returns a list of at most two
   strings: the first word, and everything after it as ONE string, using
   split() with maxsplit=1:

   ```
   first_and_rest("The Glass Path") -> ["The", "Glass Path"]
   ```

   A one-word title gives a one-item list; '' gives [].

   *Return: the list.*

4. **enumerate(start=1): numbering from one** (P164)

   Write a function `numbered(names)` that returns a list of (position, name)
   tuples with positions starting at 1, using list() over enumerate() with
   start=1:

   ```
   numbered(["Aisha", "Kwame"]) -> [(1, "Aisha"), (2, "Kwame")]
   ```

   *Return: the list of tuples.*

5. **ljust(width, '.'): a dotted leader** (P165)

   Write a function `leader(label, width)` that returns label padded on the
   RIGHT with dots to the given width -- like a line in a contents page --
   using ljust() with '.' as the fill character:

   ```
   leader("Travel", 12) -> "Travel......"
   ```

   A label already wider than width is returned unchanged.

   *Return: the string.*

## 2 - A loop or an if (5)

A best-so-far loop comparing lengths, an early return and a cap, a counter with
a strict comparison, a return from inside a loop, and a while loop whose
condition is the question.

6. **The longest word, by a loop** (P166)

   Write a function `longest(words)` that returns the longest word in a non-
   empty list, the FIRST one when several share the length, using a for loop
   that keeps the best so far. Do not use max() for this one.

   ```
   longest(["pen", "paper", "ink"]) -> "paper"
   ```

   *Return: the word.*

7. **A late fee with a cap** (P167)

   Write a function `late_fee(days_late)` that returns the fee in pence: 20 a
   day, but never more than 1000, and 0 when days_late is zero or negative. An
   if for the no-fee case, then the cap.

   ```
   late_fee(3) -> 60
   late_fee(80) -> 1000
   ```

   *Return: an integer.*

8. **Overdue dates, counted** (P168)

   Write a function `count_overdue(due_dates, today)` that returns how many of
   the 'YYYY-MM-DD' strings are BEFORE today -- a loan due today is not yet
   overdue. A loop with an if and a counter; the strings compare correctly as
   they are.

   ```
   count_overdue(["2026-06-01", "2026-06-30", "2026-07-02"], "2026-06-30") -> 1
   ```

   *Return: an integer.*

9. **Where the first negative is** (P169)

   Write a function `first_negative(values)` that returns the POSITION of the
   first value below zero, or -1 if there is none, using a loop over
   enumerate() that returns as soon as it finds one:

   ```
   first_negative([3, 1, -4, 1, -5]) -> 2
   ```

   *Return: an integer.*

10. **Squares below a limit** (P170)

    Write a function `squares_below(limit)` that returns the list of square
    numbers 1, 4, 9, ... that are strictly LESS than limit, using a while loop
    that stops as soon as the next square is too big:

    ```
    squares_below(30) -> [1, 4, 9, 16, 25]
    ```

    *Return: the list.*

## 3 - Library rows (5)

The same questions the SQL side asks, over lists of dicts: a filter that
collects ids, a total per key, an argmax over counts, a count that tests None
first, and HAVING as a filter over a counting dict.

11. **Loans still out** (P171)

    Each loan is a dict with keys loan_id, member, due and returned, where
    returned is None while the book is out. Write a function
    `open_loans(loans)` that returns a list of the loan_ids of the loans still
    out, in the order given:

    ```
    open_loans(LOANS) -> [2, 5]
    ```

    *Return: a list of integers.*

12. **Unpaid fines, per member** (P172)

    Each fine is a dict with keys fine_id, member, pence and paid, where paid
    is None while the fine is unpaid. Write a function `owed_by_member(fines)`
    that returns a dict mapping each member to the total pence of their UNPAID
    fines -- members with nothing unpaid are left out:

    ```
    owed_by_member(FINES) -> {9: 240, 7: 60}
    ```

    *Return: the dictionary.*

13. **The branch with the most copies** (P173)

    Each copy is a dict with keys copy_id and branch. Write a function
    `busiest_branch(copies)` that returns the NAME of the branch holding the
    most copies in a non-empty list -- count per branch first, then pick the
    largest, the first such branch if two tie:

    ```
    busiest_branch(COPIES) -> "Central"
    ```

    *Return: the branch name.*

14. **Late returns, counted** (P174)

    Using the same loan dicts (loan_id, member, due, returned, with returned
    None while out), write a function `late_returns(loans)` that returns how
    many loans came back AFTER their due date. A loan still out is not late --
    and None cannot be compared with a string, so test it first:

    ```
    late_returns(LOANS) -> 1
    ```

    *Return: an integer.*

15. **Members with enough holds** (P175)

    Each hold is a dict with keys hold_id, member and book. Write a function
    `members_with_holds(holds, at_least)` that returns a sorted list of the
    members who have placed at_least holds OR MORE -- count per member, then
    keep the ones that reach the threshold:

    ```
    members_with_holds(HOLDS, 2) -> [7, 9]
    ```

    *Return: a sorted list of member ids.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,051 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
