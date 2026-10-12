# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
sixth set on this schema, on six tiers none of the library sets have used:
JSON, LIKE and GLOB, date modifiers, query plans, aggregates over windows,
and three writable statements new to the library. **Fifteen Python**: tiny
functions of one or two lines, each about ONE tool named in the question's
title, none of them used by an earlier set.

| Stage | SQL questions |
|---|---|
| 1 - JSON | 1-3 |
| 2 - LIKE and GLOB | 4-5 |
| 3 - Date modifiers | 6-8 |
| 4 - Query plans | 9-10 |
| 5 - Aggregates over windows | 11-12 |
| 6 - Changing the data | 13-15 |

| Stage | Python questions |
|---|---|
| 1 - Strings | 1-4 |
| 2 - Numbers and None | 5-9 |
| 3 - Lists | 10-12 |
| 4 - Sets and dictionaries | 13-15 |

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

None of the three runs statements of its own afterwards; each is graded on
what your script leaves behind.

| # | Construct |
|---|---|
| 13 | `UPDATE loans SET ... FROM copies WHERE copies.copy_id = loans.copy_id AND ... AND loans.returned_on IS NULL` |
| 14 | `DELETE ... WHERE hold_id IN (SELECT hold_id FROM (... ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) ...) WHERE rn > 1)` |
| 15 | `ALTER TABLE books ADD COLUMN size TEXT GENERATED ALWAYS AS (CASE ...) VIRTUAL` |

## The query-plan stage

Questions 9 and 10 cannot be graded on their rows alone, because the slow
query and the fast one return exactly the same rows. Each opens with the
slow query already in the editor -- correct, and the thing to improve --
and **Check answer** also runs `EXPLAIN QUERY PLAN` on yours: 9 must mention
`idx_loans_member`, 10 must say SEARCH and not SCAN. **Explain plan** (the
button, or F6) shows you the plan of whatever is in the editor.

## Things the data does on purpose

- **133 titles begin with a capital vowel, and none with a lower-case
  one** -- GLOB '[aeiou]*' finds nothing, because GLOB is case-sensitive.
- **589 members live in an LS1x district and 95 in LS1 itself**; LIKE
  'LS1%' lumps them together, LIKE 'LS1_' does not.
- **716 fines were issued in the ninety days to 2026-06-30, and
  736 in the three months** -- two days apart, and a few fines
  with them.
- **762 members have a birthday still to come in 2026** on
  30 June, and a difference of years makes every one of them a year too
  old.
- **Member 1149 has 214 loans**, one of the heaviest readers, which
  is why question 9 looks them up by the index.
- **8 members hold the same book twice**, the pairs question 14
  thins to one.
- **Old Town's copies have 102 loans out and 3,617
  returned**; question 13's UPDATE must move only the first group.

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

## 1 - JSON (3)

json_group_array with the ORDER BY inside the call, json_each as a table in
FROM, and json_object against json_array.

1. **Each branch's staff, as a JSON list** (Q922)

   For each branch, its staff names as ONE JSON array, in alphabetical order
   of name: json_group_array with an ORDER BY inside its parentheses.

   *Return: branch_id, names*

2. **A list of books, from JSON to rows** (Q923)

   Given the JSON list '[587, 12, 40, 275]' of book ids, how many members are
   WAITING on each -- an open hold, neither fulfilled nor cancelled --
   including 0 for a book nobody is waiting for. json_each() turns the list
   into rows with a `value` column.

   *Return: book_id, waiting*

3. **A card for each manager** (Q924)

   For each manager, a JSON object with the keys id, name and branch holding
   their staff_id, name and branch_id -- built with json_object(key, value,
   key, value, ...).

   *Return: staff_id, card*

## 2 - LIKE and GLOB (2)

A character class that only GLOB has, and is case-sensitive, and the underscore
that LIKE treats as exactly one character.

4. **Titles that begin with a vowel** (Q925)

   How many titles begin with each capital vowel -- A, E, I, O or U -- one row
   per letter that occurs. GLOB has a character class, [AEIOU], that LIKE does
   not, and GLOB is case-sensitive.

   *Return: letter, titles*

5. **The LS1x districts** (Q926)

   How many members live in each postcode area of exactly four characters
   beginning 'LS1' -- LS10 to LS19 -- but NOT in 'LS1' itself. In LIKE, _
   matches exactly one character.

   *Return: postcode_area, members*

## 3 - Date modifiers (3)

'-90 days' is not '-3 months', 'weekday 0' moves forward to a Sunday, and an age
in whole years needs the birthday test.

6. **Fines from the last ninety days** (Q927)

   Fines issued in the ninety days ending 2026-06-30 -- strictly after
   date('2026-06-30', '-90 days') -- split into unpaid and paid: a 0/1 flag
   for paid, the count, and the pence.

   *Return: paid, fines, pence*

7. **Weeks ending on a Sunday** (Q928)

   For the loans started from 2026-01-01 to 2026-03-31: how many started in
   each week, labelled by the SUNDAY that ends it -- date(loaned_on, 'weekday
   0') gives the next Sunday on or after a date. Fourteen weeks, the first and
   last of them partial.

   *Return: week_ending, loans*

8. **Members by decade of age** (Q929)

   How many members fall in each decade of age on 2026-06-30: 0 for under ten,
   10 for ten to nineteen, and so on. An age in whole years is the difference
   in years MINUS ONE when the birthday has not yet come round -- compare the
   '%m-%d' parts.

   *Return: decade, members*

## 4 - Query plans (2)

Two questions graded on EXPLAIN QUERY PLAN: the slow query is already in the
editor and returns the right rows. An index is lost to arithmetic on the column,
and a NOCASE index is found by asking for its collation.

9. **Let the index find the member** (Q930)

   Member 1149's loans: loan_id and loaned_on. The query in the editor is
   correct and reads every one of the 24,000 loans. There is an index on
   loans(member_id); write the WHERE so that SQLite can use it. Your plan must
   mention idx_loans_member.

   *Return: loan_id, loaned_on*

10. **A title lookup that ignores case, through the index** (Q931)

    The book whose title is 'the glass path' in any mix of case: book_id and
    title. The query in the editor lower-cases every title to compare, which
    scans the table. The index idx_books_title is declared COLLATE NOCASE, so
    a comparison that asks for that collation can SEARCH it: your plan must
    say SEARCH, not SCAN.

    *Return: book_id, title*

## 5 - Aggregates over windows (2)

A window over the grouped rows, where PARTITION BY the group itself makes every
group its own average, and a share of the branch that needs PARTITION BY the
branch.

11. **Genres busier than the average genre** (Q932)

    Genres whose loan count is above the AVERAGE genre's loan count -- the
    average of the eight per-genre totals. Group first, then a window AVG over
    the grouped counts, then filter in an outer query.

    *Return: genre, loans*

12. **A genre that is a fifth of its branch** (Q933)

    For each branch and genre: the genre's share of that BRANCH's loans as a
    percentage to one decimal, keeping only the pairs above 20 per cent. The
    branch total is a window SUM over the grouped counts, partitioned by
    branch.

    *Return: branch_id, genre, pct*

## 6 - Changing the data (3)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. UPDATE ... FROM with the condition that
keeps history, a DELETE of duplicates numbered by ROW_NUMBER in a subquery, and
a VIRTUAL generated column added by ALTER TABLE.

13. **A week's grace at Old Town** (Q934)

    Old Town (branch 6) is closing for a week. Give every loan that is still
    OUT on one of its copies seven more days: due_on = date(due_on, '+7
    days'). Use UPDATE ... FROM to bring copies into the WHERE. Returned loans
    and other branches' loans are untouched.

    *Checked: the total loan length in days of Old Town's open loans, of its returned loans, and of open loans elsewhere*

14. **One hold per member per book, the earliest kept** (Q935)

    Eight members hold the same book twice. Delete the LATER hold of each such
    pair -- by placed_at -- keeping the earliest, with ROW_NUMBER over
    (member_id, book_id) in a subquery that picks the hold_ids to delete.

    *Checked: how many holds remain, the sum of their hold_ids, and how many (member, book) pairs still repeat*

15. **A column that computes itself** (Q936)

    Add a VIRTUAL generated column `size` to books: 'short' under 200 pages,
    'medium' under 500, 'long' otherwise -- ALTER TABLE books ADD COLUMN size
    TEXT GENERATED ALWAYS AS (...) VIRTUAL. Nothing is stored; the value is
    computed from pages whenever it is read.

    *Checked: how many books of each size*

# Python

## 1 - Strings (4)

center() against ljust(), isupper() against == upper(), the format() method
against + with an int, and ord() against int().

1. **center(width, '*'): a label in the middle** (P191)

   Write a function `banner(label, width)` that returns the label centred in a
   field of the given width, padded on both sides with '*', using center()
   with a fill character:

   ```
   banner("Hi", 8) -> "***Hi***"
   ```

   A label wider than width is returned unchanged.

   *Return: the string.*

2. **isupper(): is it all capitals?** (P192)

   Write a function `is_shouting(s)` that returns True when every letter in s
   is upper case and there is at least one letter, using isupper():

   ```
   is_shouting("LS15") -> True
   is_shouting("123") -> False
   ```

   *Return: True or False.*

3. **format(): slots filled in order** (P193)

   Write a function `loan_line(name, n)` that returns the sentence '<name> has
   <n> loans' using the string format() method with {} slots:

   ```
   loan_line("Aisha", 3) -> "Aisha has 3 loans"
   ```

   *Return: the string.*

4. **ord(): a character's code** (P194)

   Write a function `code_point(ch)` that returns the Unicode code of a single
   character as an integer, using ord():

   ```
   code_point("A") -> 65
   ```

   *Return: an integer.*

## 2 - Numbers and None (5)

is None against not x, math.isclose() against ==, is_integer() against
isinstance, math.prod() against sum(), and min(key=abs) against min().

5. **is None: missing, not merely empty** (P195)

   Write a function `is_missing(x)` that returns True only when x is None --
   not when it is 0, an empty string or an empty list -- using the is None
   test:

   ```
   is_missing(None) -> True
   is_missing(0) -> False
   ```

   *Return: True or False.*

6. **math.isclose(): equal enough** (P196)

   Write a function `about_equal(a, b)` that returns True when two floats are
   equal within floating-point noise -- 0.1 + 0.2 against 0.3 -- using
   math.isclose() with its default tolerance. Remember the import.

   ```
   about_equal(0.1 + 0.2, 0.3) -> True
   ```

   *Return: True or False.*

7. **is_integer(): a float with nothing after the point** (P197)

   Write a function `is_whole(x)` that returns True when the float x has no
   fractional part, using the float method is_integer():

   ```
   is_whole(4.0) -> True
   is_whole(4.5) -> False
   ```

   *Return: True or False.*

8. **math.prod(): multiply them all** (P198)

   Write a function `product(values)` that returns all the numbers multiplied
   together, 1 for an empty list, using math.prod(). Remember the import.

   ```
   product([2, 3, 4]) -> 24
   ```

   *Return: the product.*

9. **min(key=abs): nearest to zero** (P199)

   Write a function `closest_to_zero(values)` that returns the value in a non-
   empty list nearest to zero -- the FIRST such value when two are equally
   near -- using min() with key=abs:

   ```
   closest_to_zero([3, -1, 2]) -> -1
   ```

   *Return: the value.*

## 3 - Lists (3)

sort() returns None, extend() against append(), and list(map()) against str() of
the whole list.

10. **sort(): in place, returning None** (P200)

    Write a function `sort_in_place(values)` that sorts the list itself with
    its sort() method and then returns that same list:

    ```
    sort_in_place([3, 1, 2]) -> [1, 2, 3]
    ```

    *Return: the list.*

11. **extend(): one list onto the end of another** (P201)

    Write a function `joined(a, b)` that returns a NEW list holding a's items
    followed by b's, using extend() on a copy of a:

    ```
    joined([1, 2], [3, 4]) -> [1, 2, 3, 4]
    ```

    *Return: the new list.*

12. **map(): the same function over every item** (P202)

    Write a function `as_strings(values)` that returns a list of the items
    each converted to a string, using list() over map() with str:

    ```
    as_strings([1, 2, 3]) -> ["1", "2", "3"]
    ```

    *Return: the new list.*

## 4 - Sets and dictionaries (3)

discard() against remove(), ^ against |, and | on dicts against a + that does
not exist.

13. **discard(): remove if present** (P203)

    Write a function `without(items, x)` that returns a SET of the items with
    x removed -- and simply the set of items when x was never there -- using
    set() and discard():

    ```
    without([1, 2, 3], 2) -> {1, 3}
    without([1, 2], 9) -> {1, 2}
    ```

    *Return: the set.*

14. **^ on sets: in one but not both** (P204)

    Write a function `either_not_both(a, b)` that returns a SET of the values
    in exactly one of the two lists -- in a or in b but not in both -- using
    set() on each and the ^ operator:

    ```
    either_not_both(["LS1", "BD3"], ["BD3", "WF1"]) -> {"LS1", "WF1"}
    ```

    *Return: the set.*

15. **| on dicts: merged, the right one winning** (P205)

    Write a function `combined(a, b)` that returns a NEW dict with everything
    from a and everything from b, b winning where a key is in both, using the
    | operator on dicts:

    ```
    combined({"x": 1, "y": 2}, {"y": 3}) -> {"x": 1, "y": 3}
    ```

    *Return: the new dictionary.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,111 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
