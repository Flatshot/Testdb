# SQL and Python practice exercises

Thirty questions in two tabs. **Fifteen SQL** on the public library, the
fifth set on this schema and a second revision set: five tiers that pair up
the library's concepts differently from last time, every question new, plus
four writable questions. **Fifteen Python**: tiny functions of one or two
lines, each about ONE tool named in the question's title, none of them used
by an earlier set.

| Stage | SQL questions |
|---|---|
| 1 - Windows and text | 1-2 |
| 2 - Intervals and CASE | 3-4 |
| 3 - Recursion and set operations | 5-6 |
| 4 - Subqueries and dates | 7-9 |
| 5 - EXISTS and grain | 10-11 |
| 6 - Changing the data | 12-15 |

| Stage | Python questions |
|---|---|
| 1 - Strings | 1-5 |
| 2 - Numbers | 6-9 |
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
questions 12 to 15 is one of those.

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

**Driver statements.** Question 12 runs two inserts of its own *after* your
script -- the holds your trigger should refuse and allow. Questions 13 to 15
are graded on what your script leaves behind.

| # | Construct |
|---|---|
| 12 | `BEFORE INSERT ... WHEN (SELECT COUNT(*) ... open holds ...) >= 3` |
| 13 | `UPDATE ... SET salary = CASE role WHEN ... ELSE salary END` |
| 14 | `CREATE TABLE ... AS SELECT ... WHERE closed`, then `DELETE ... WHERE closed` |
| 15 | a `VIEW` with `ROW_NUMBER() OVER (PARTITION BY book_id ORDER BY placed_at)` over the open holds |

## Things the data does on purpose

- **The top three borrowers of each branch are 19 members, not eighteen**
  -- one branch has a tie, which is why question 1 asks for DENSE_RANK.
- **Titles begin with 35 different first words**, five of them from
  the title frames (The, A, Beyond, Poems, Notes).
- **156 of 863 fulfilled holds were met within a week**;
  subtracting the date strings instead of their julianday() says all of
  them were.
- **149 books are at Central but not Old Town, and
  131 the other way round** -- question 6's EXCEPT reversed is
  a different answer.
- **Only 24 members took their first loan in or after June
  2025**; a WHERE on the date instead of a HAVING on MIN makes it almost
  everyone.
- **316 of the 337 waiting holds are for a book with a copy on
  a shelf somewhere** -- the queue is at the wrong branch, which is
  question 10.
- **Members 930 and 1454 each have three open holds**, the limit question
  12's trigger enforces; the second driven member's holds are all closed.
- **1,163 holds are closed and 337 open**, the split question 14's
  archive and question 15's queue both depend on; 140 books have
  someone waiting.

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

## 1 - Windows and text (2)

DENSE_RANK against ROW_NUMBER and RANK when members tie, and SUBSTR whose length
has to be one less than where INSTR found the space.

1. **Each branch's three keenest borrowers** (Q907)

   For each home branch, the members with the three highest loan counts -- ALL
   of them when members tie, so a branch may show more than three rows.
   DENSE_RANK within the branch, by loans descending.

   *Return: home_branch_id, member_id, loans, place*

2. **Titles by their first word** (Q908)

   How many titles begin with each first word -- the text before the first
   space, without the space. Every title has at least two words. SUBSTR(text,
   start, length) with INSTR finding the space.

   *Return: first_word, titles*

## 2 - Intervals and CASE (2)

julianday arithmetic inside a conditional SUM, where subtracting two date
strings gives 0, and a simple CASE on renewals whose WHENs cannot overlap.

3. **Holds fulfilled within the week** (Q909)

   For each branch the hold was placed at: how many holds were fulfilled, how
   many of those within 7 days of being placed, and how many took longer. The
   wait is julianday arithmetic -- placed_at carries a time, which julianday
   handles -- and the split is a conditional SUM.

   *Return: branch_id, fulfilled, within_week, longer*

4. **Renewed once, twice, or not at all** (Q910)

   Loans by how often they were renewed -- labelled 'none', 'once', 'twice'
   from the renewals column -- with the count and the percentage returned
   late, to one decimal. A loan still out is not late.

   *Return: renewed, loans, pct_late*

## 3 - Recursion and set operations (2)

Twelve decades manufactured by recursion so the empty ones keep a 0, and EXCEPT
with the branch that must have the book on the left.

5. **Branches opened, decade by decade** (Q911)

   For every decade from 1900 to 2010 -- 1900, 1910, ..., 2010 -- how many
   branches opened in it, 0 for the decades with none. Build the decades with
   a recursive CTE and count the branches whose opened_on falls in each.

   *Return: decade, branches*

6. **At Central but not at Old Town** (Q912)

   Books with a copy at Central (branch 1) but no copy at Old Town (branch 6),
   using EXCEPT between two queries over copies. Each book once.

   *Return: book_id*

## 4 - Subqueries and dates (3)

HAVING on MIN rather than WHERE on the date, quarters from the month by (m + 2)
/ 3, and a correlated subquery that is the role average only because it refers
to the outer row.

7. **Late starters** (Q913)

   Members whose FIRST loan was on or after 2025-06-01: their member_id and
   the date of that first loan. A member with loans before that date is
   excluded even if they also borrowed after it.

   *Return: member_id, first_loan*

8. **Loans by quarter** (Q914)

   How many loans started in each quarter of each year: the year as a number,
   the quarter as 1 to 4. There is no strftime code for the quarter; derive it
   from the month number with integer arithmetic.

   *Return: year, quarter, loans*

9. **Paid against the role's average** (Q915)

   Each staff member's salary, the average salary of their ROLE rounded to
   whole pounds, and how far above or below it they are. The role average is a
   correlated subquery that refers to the outer row's role.

   *Return: staff_id, salary, role_avg, diff*

## 5 - EXISTS and grain (2)

EXISTS inside EXISTS for 'a copy on a shelf somewhere', with the withdrawn test
that is easy to drop, and author, book and copy counted at three grains.

10. **Waiting while a copy sits on a shelf** (Q916)

    Open holds -- fulfilled_on and cancelled_on both NULL -- whose book has a
    copy available RIGHT NOW somewhere in the service: a copy not withdrawn
    and with no open loan. Return the hold and its book.

    *Return: hold_id, book_id*

11. **Books and copies, per author** (Q917)

    For each author who has at least one book: how many books, and how many
    copies of them in all. Books with no copies still count as books. Author,
    book and copy are three grains, and the join to copies multiplies the book
    rows.

    *Return: author_id, books, copies*

## 6 - Changing the data (4)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. A trigger that counts open holds, an
UPDATE with a CASE whose ELSE keeps the managers, CREATE TABLE AS SELECT with a
matching DELETE, and a view with a window function over a filtered table.

12. **Three open holds at most** (Q918)

    Write a BEFORE INSERT trigger on holds that refuses a new hold --
    RAISE(ABORT, ...) -- when the member already has three or more OPEN holds,
    fulfilled_on and cancelled_on both NULL. The question then inserts a hold
    for member 930, who has three waiting, and one for member 1, who has none.

    *Checked: which of the two holds exist*

13. **A pay rise by role** (Q919)

    Give every assistant a 5 per cent rise and every librarian 3 per cent,
    rounded to whole pounds with ROUND; managers' salaries do not change. One
    UPDATE with a CASE in its SET.

    *Checked: the total salary of each role*

14. **Archive the closed holds** (Q920)

    Move the CLOSED holds -- fulfilled or cancelled -- out of holds into a new
    table `holds_archive` with the same columns: CREATE TABLE ... AS SELECT to
    copy them, then DELETE them from holds with the same condition. Open holds
    stay where they are.

    *Checked: how many rows holds and holds_archive each have, and how many open holds are left in holds*

15. **The queue, as a view** (Q921)

    Create a view `hold_queue (hold_id, book_id, member_id, position)` of the
    OPEN holds, numbered within each book by placed_at from 1 -- the queue
    position. Closed holds are not in the view and do not take a number.

    *Checked: the view's size, how many holds are at position 1 -- one per book with a queue -- and the longest queue*

# Python

## 1 - Strings (5)

strip(chars) against replace(), istitle() against the first letter, replace()
with a count, removesuffix() against a slice, and isspace() against strip() ==
''.

1. **strip(chars): quotes off both ends** (P176)

   Write a function `unquote(s)` that returns s with any double quote
   characters removed from its two ENDS -- and nothing removed from the middle
   -- using strip() with the quote as its argument:

   ```
   unquote('"Leeds"') -> 'Leeds'
   ```

   *Return: the new string.*

2. **istitle(): is every word capitalised?** (P177)

   Write a function `is_title_case(s)` that returns True when every word in s
   starts with a capital and continues in lower case, using istitle():

   ```
   is_title_case("The glass path") -> False
   ```

   *Return: True or False.*

3. **replace(old, new, 1): only the first one** (P178)

   Write a function `replace_first(s, old, new)` that returns s with only the
   FIRST occurrence of old replaced by new, using replace() with its count
   argument:

   ```
   replace_first("a-b-c", "-", "+") -> "a+b-c"
   ```

   *Return: the new string.*

4. **removesuffix(): the extension off the end** (P179)

   Write a function `drop_txt(filename)` that returns the name without a
   trailing '.txt' -- and unchanged when it does not end in that -- using
   removesuffix():

   ```
   drop_txt("notes.txt") -> "notes"
   drop_txt("notes.csv") -> "notes.csv"
   ```

   *Return: the new string.*

5. **isspace(): nothing but whitespace** (P180)

   Write a function `is_blank(s)` that returns True when s is made only of
   whitespace -- spaces, tabs, newlines -- and has at least one character,
   using isspace():

   ```
   is_blank("   ") -> True
   is_blank("") -> False
   ```

   *Return: True or False.*

## 2 - Numbers (4)

int(s, 2) against int(s), format(n, 'b') against bin(), math.gcd() against
min(), and the .1% spec against .1f with a % typed after it.

6. **int(s, 2): a binary string to a number** (P181)

   Write a function `from_binary(s)` that returns the integer a string of 0s
   and 1s stands for in base two, using int() with a base:

   ```
   from_binary("101") -> 5
   ```

   *Return: an integer.*

7. **format(n, 'b'): a number as binary digits** (P182)

   Write a function `to_binary(n)` that returns the binary digits of a non-
   negative integer as a string, with no prefix, using format() with the 'b'
   spec:

   ```
   to_binary(5) -> "101"
   ```

   *Return: the string.*

8. **math.gcd(): the greatest common divisor** (P183)

   Write a function `common_factor(a, b)` that returns the largest whole
   number that divides both a and b, using math.gcd(). Remember the import.

   ```
   common_factor(12, 18) -> 6
   ```

   *Return: an integer.*

9. **f'{x:.1%}': a fraction as a percentage** (P184)

   Write a function `as_percent(x)` that returns the fraction x as a
   percentage string with one decimal and a % sign, using the .1% format spec
   in an f-string:

   ```
   as_percent(0.258) -> "25.8%"
   ```

   *Return: the string.*

## 3 - Lists (3)

sorted(key=str.lower) against sorted(), count() against in, and range() with a
step whose stop is one past the end.

10. **sorted(key=str.lower): alphabetical, not ASCII** (P185)

    Write a function `alphabetical(words)` that returns the words sorted
    alphabetically IGNORING case, using sorted() with key=str.lower:

    ```
    alphabetical(["banana", "Apple", "cherry"]) -> ["Apple", "banana", "cherry"]
    ```

    *Return: the new list.*

11. **list.count(): how many times** (P186)

    Write a function `times(values, x)` that returns how many times x appears
    in the list, as an integer, using the list's count() method:

    ```
    times(["LS1", "BD3", "LS1"], "LS1") -> 2
    ```

    *Return: an integer.*

12. **range(start, stop, step): the even numbers** (P187)

    Write a function `evens_up_to(n)` that returns the list of even numbers
    from 0 up to and INCLUDING n when n is even, using list() over range()
    with a step of 2:

    ```
    evens_up_to(10) -> [0, 2, 4, 6, 8, 10]
    ```

    *Return: the list.*

## 4 - Sets and dictionaries (3)

<= on sets the right way round, setdefault() against assigning a fresh list, and
in on a dict against in on its values.

13. **<= on sets: is everything wanted available?** (P188)

    Write a function `all_available(wanted, stock)` that returns True when
    every wanted item is in stock, using set() on each and the <= operator --
    subset:

    ```
    all_available(["pen", "ink"], ["ink", "pen", "paper"]) -> True
    ```

    *Return: True or False.*

14. **setdefault(): a list for each key, made on demand** (P189)

    Write a function `add_to_group(groups, key, item)` that appends item to
    the list stored under key in the dict, creating an empty list there first
    if the key is new, and returns the dict -- using setdefault():

    ```
    add_to_group({"fiction": ["A"]}, "fiction", "B") -> {"fiction": ["A", "B"]}
    ```

    *Return: the dictionary.*

15. **in on a dict: is the key there?** (P190)

    Write a function `has_area(counts, area)` that returns True when area is a
    KEY of the dict, whatever its value, using the in test on the dict itself:

    ```
    has_area({"LS1": 95}, "LS1") -> True
    ```

    *Return: True or False.*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
1,081 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
