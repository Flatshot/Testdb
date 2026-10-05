# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on a NEW schema -- a public
library service, replacing the hospital -- at the level of the last hospital
sets, and **fifteen Python**, a step back down: tiny functions of one or two
lines, each about ONE tool named in the question's title.

| Stage | SQL questions |
|---|---|
| 1 - Warm-up | 1-2 |
| 2 - Strings and sequences | 3-4 |
| 3 - Dates and times | 5-6 |
| 4 - Intervals and queues | 7-8 |
| 5 - Joins and grain | 9-10 |
| 6 - Window functions | 11-12 |
| 7 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Numbers | 1-4 |
| 2 - Strings | 5-8 |
| 3 - Lists | 9-13 |
| 4 - Membership and pairs | 14-15 |

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
past due; 337 holds are still waiting; 1,380 fines are unpaid -- and
every question that measures an open interval says which end to supply.

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

**Driver statements.** Question 13 runs two inserts of its own *after* yours
-- the loans your trigger should sort. Questions 14 and 15 are graded on
what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `BEFORE INSERT ... WHEN (SELECT SUM(...)) >= 500`: a rule that spans three tables |
| 14 | an `UPDATE` whose WHERE has the condition that protects history as well as the one that selects |
| 15 | a `VIEW` holding a two-part definition the whole library can agree on |

## Things the data does on purpose

- **200 of the 1,500 members have never borrowed anything**, and 20
  of the 600 titles have no copies -- the rows a LEFT JOIN keeps and an
  inner join loses.
- **117 copies have been withdrawn**, which is the half of 'available'
  that question 15's trap forgets.
- **30 members have 150 or more loans**, the heavy readers; question 2's
  two thresholds keep seven of them.
- **Book 587 has 7 members waiting**, the longest queue, which is why
  question 4 asks about it.
- **83 per cent of loans are of a copy held away from the member's home
  branch** -- members borrow from the whole service, not their own branch.
- **Member 1149 owes the most in unpaid fines, and member 11 owes nothing**,
  the two that question 13's trigger must tell apart.

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

## 1 - Warm-up (2)

Two tables where the join decides who is counted, and two aggregate conditions
in HAVING with a NULL comparison that SUM skips on its own.

1. **Copies per title, by genre** (Q847)

   For each genre: how many books -- titles -- the catalogue lists, how many
   physical copies there are of them, and copies per title to one decimal.
   Twenty titles have no copies at all and still count as titles.

   *Return: genre, titles, copies, per_title*

2. **Heavy borrowers, often late** (Q848)

   Members with at least 200 loans, at least 40 of which came back late --
   returned after due_on: member_id, loans, late, and the late percentage to
   one decimal. A loan still out is not late by this test.

   *Return: member_id, loans, late, pct_late*

## 2 - Strings and sequences (2)

LIKE anchored at the start of a title, and a queue numbered by ROW_NUMBER once
the WHERE has said who is still in it.

3. **Titles that begin with The** (Q849)

   For each genre: how many titles, how many of them BEGIN with the word
   'The', and the percentage to one decimal. 'Beyond the Door' does not begin
   with The.

   *Return: genre, titles, the_titles, pct*

4. **The queue for book 587** (Q850)

   The members still WAITING for book 587 -- holds neither fulfilled nor
   cancelled -- in the order they placed their hold, with their position in
   the queue, 1 for the front. Order is placed_at.

   *Return: position, member_id, placed_at*

## 3 - Dates and times (2)

Late means later than the stored due date, not a recomputed one, and overdue is
two conditions, not one.

5. **Late returns by month** (Q851)

   For each month of RETURN, 'YYYY-MM': how many loans came back, how many
   came back after their due_on, and the percentage to one decimal. due_on
   already includes any renewals.

   *Return: month, returns, late, pct_late*

6. **Overdue at the end of the data** (Q852)

   As of 2026-06-30, per branch holding the copy: how many loans are still out
   AND past their due date, and the most days overdue among them, as a whole
   number. A loan is overdue when returned_on is NULL and due_on is before
   that day.

   *Return: branch_id, overdue, max_days_over*

## 4 - Intervals and queues (2)

A day inside a loan per copy with the open end supplied, and the wait of a hold
measured only for the ones that were fulfilled.

7. **On the shelf in mid-June** (Q853)

   For each branch on 2026-06-15: how many of its copies were on the books --
   not withdrawn by then -- how many of those were out on loan that day, and
   how many were available. A copy is out on a day if a loan of it started on
   or before the day and had not been returned before it; NULL returned_on
   means not yet returned.

   *Return: branch_id, copies, on_loan, available*

8. **How long a hold waits** (Q854)

   For each pickup branch: how many holds have been FULFILLED, and the average
   wait in days from the day the hold was placed to the day it was fulfilled,
   to one decimal. placed_at is a datetime; cut it to its date first.

   *Return: branch_id, fulfilled, avg_wait_days*

## 5 - Joins and grain (2)

Copies and holds as two children of one book, and the copy's branch against the
member's home branch -- two keys to one table.

9. **Copies and holds, per genre** (Q855)

   For each genre: how many copies its books have, and how many holds have
   ever been placed on them. Both hang off books. Joining both at once
   multiplies each by the other.

   *Return: genre, copies, holds*

10. **Borrowed away from home** (Q856)

    For each HOME branch of the members: how many loans its members have
    taken, how many of those were of a copy held at a DIFFERENT branch, and
    the percentage to one decimal. The copy's branch and the member's home
    branch are two foreign keys to the same table.

    *Return: home_branch_id, loans, away, pct_away*

## 6 - Window functions (2)

Top-1 per genre through two joins with a tie-break, and a share of the branch by
PARTITION BY.

11. **The most borrowed title in each genre** (Q857)

    For each genre, the title whose copies have been loaned the most times,
    with that count; ties by title alphabetically. Loans attach to copies,
    copies to books.

    *Return: genre, title, loans*

12. **Each branch's genre mix** (Q858)

    For every branch (of the copy) and genre: how many loans, and what
    percentage of THAT BRANCH's loans they are, to one decimal. Each branch's
    eight shares add to 100.

    *Return: branch_id, genre, loans, pct_of_branch*

## 7 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger that sums unpaid fines, an
UPDATE whose WHERE protects paid dates, and a view of what is available.

13. **No new loans while fines are owed** (Q859)

    Write a BEFORE INSERT trigger on loans that refuses a loan -- RAISE(ABORT,
    ...) -- when the member's UNPAID fines add up to 500 pence or more. Fines
    hang off loans, so the sum joins fines to loans by member. After your
    script, the question inserts a loan of copy 1 for member 1149, who owes a
    lot, and a loan of copy 2 for member 11, whose fines are all paid.

    *Checked: which of the two loans exist*

14. **Write off the small change** (Q860)

    Mark every UNPAID fine of 100 pence or less as paid on '2026-07-01' -- an
    amnesty on small debts -- and nothing else. Fines already paid keep their
    own paid_on.

    *Checked: how many fines are still unpaid, what they add up to, and how many fines carry the amnesty date*

15. **What is actually on the shelf** (Q861)

    Create a view `available_copies (copy_id, book_id, branch_id)` of the
    copies that can be borrowed right now: not withdrawn, and not out on a
    loan that has no returned_on.

    *Checked: how many copies the view holds, and how many of them are withdrawn or out*

# Python

## 1 - Numbers (4)

round() with and without a second argument, abs(), / against // in a percentage,
and min() over max() for a clamp.

1. **round(): to the nearest whole number** (P116)

   Write a function `nearest_whole(x)` that returns x rounded to the nearest
   whole number, as an integer, using round():

   ```
   nearest_whole(3.7) -> 4
   ```

   *Return: an integer.*

2. **abs(): how far apart** (P117)

   Write a function `distance(a, b)` that returns how far apart two numbers
   are, always as a positive number, using abs():

   ```
   distance(10, 3) -> 7
   distance(3, 10) -> 7
   ```

   *Return: the distance.*

3. **round(x, 1): a percentage to one decimal** (P118)

   Write a function `percent(part, whole)` that returns part as a percentage
   of whole, rounded to one decimal place. whole is never 0:

   ```
   percent(1, 3) -> 33.3
   ```

   *Return: the percentage.*

4. **min() and max(): keep a value in range** (P119)

   Write a function `clamp(x, lo, hi)` that returns x if it is between lo and
   hi, lo if it is below, and hi if it is above, using min() and max() rather
   than an if:

   ```
   clamp(42, 0, 10) -> 10
   ```

   *Return: the clamped value.*

## 2 - Strings (4)

startswith() against in, title() against capitalize(), count() against find(),
and split()[-1] against [-1].

5. **startswith(): does it begin with** (P120)

   Write a function `has_prefix(text, prefix)` that returns True if text
   begins with prefix and False otherwise, using startswith():

   ```
   has_prefix("SRG-04", "SRG") -> True
   ```

   *Return: True or False.*

6. **title(): a capital on each word** (P121)

   Write a function `tidy_name(name)` that returns the name with the first
   letter of each word in capitals and the rest in lower case, using title():

   ```
   tidy_name("MARY SEACOLE") -> "Mary Seacole"
   ```

   *Return: the tidied string.*

7. **count(): how many of one letter** (P122)

   Write a function `letters(text, ch)` that returns how many times the
   character ch appears in text, case-sensitive, using the string's count()
   method:

   ```
   letters("observation", "o") -> 2
   ```

   *Return: the count, 0 when absent.*

8. **split()[-1]: the last word** (P123)

   Write a function `last_word(text)` that returns the last word of a non-
   empty sentence, using split() and a negative index:

   ```
   last_word("the ward round starts at nine") -> "nine"
   ```

   *Return: the word.*

## 3 - Lists (5)

min() and sorted() with key=len, index() from 0, a comprehension that filters,
and [::-1] against reverse().

9. **min(key=len): the shortest** (P124)

   Write a function `shortest(words)` that returns the shortest word in a non-
   empty list, the first of them on a tie, using min() with key=len:

   ```
   shortest(["Nightingale", "Barry", "Bevan"]) -> "Barry"
   ```

   *Return: the word.*

10. **sorted(key=len): shortest to longest** (P125)

    Write a function `by_length(words)` that returns a new list of the words
    ordered from shortest to longest, using sorted() with key=len:

    ```
    by_length(["Nightingale", "Barry", "Jenner"]) -> ["Barry", "Jenner", "Nightingale"]
    ```

    *Return: the sorted list.*

11. **index(): where in the list** (P126)

    Write a function `position(items, value)` that returns the index of the
    first occurrence of value in the list, which is always present, using the
    list's index() method:

    ```
    position(["Barry", "Bevan", "Cavell"], "Bevan") -> 1
    ```

    *Return: an index, counting from 0.*

12. **[x for x in ... if ...]: everything but one value** (P127)

    Write a function `without(items, value)` that returns a new list with
    every occurrence of value removed, in one comprehension:

    ```
    without(["day", "night", "day"], "day") -> ["night"]
    ```

    *Return: the new list.*

13. **[::-1]: back to front** (P128)

    Write a function `backwards(items)` that returns a NEW list with the items
    in reverse order, using a slice with a step of -1:

    ```
    backwards([1, 2, 3]) -> [3, 2, 1]
    ```

    *Return: the reversed list.*

## 4 - Membership and pairs (2)

The in test returned as a boolean, and dict(zip()) for two parallel lists.

14. **in: is it there** (P129)

    Write a function `contains(items, value)` that returns True if value is in
    the list and False otherwise, using the in operator:

    ```
    contains(["Morphine", "Codeine"], "Codeine") -> True
    ```

    *Return: True or False.*

15. **dict(zip()): two lists into a dictionary** (P130)

    Write a function `pair_up(keys, values)` that returns a dictionary mapping
    each key to the value at the same position, using dict() over zip():

    ```
    pair_up(["Fleming", "Barry"], [16, 30]) -> {"Fleming": 16, "Barry": 30}
    ```

    *Return: the dictionary.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
961 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
