"""Python practice exercises: fifteen functions, one simple loop each.

The eighteenth Python set, and a change of shape: every question asks for
a function built around ONE for or while loop over plain numbers or
strings -- counting, summing, finding, building a list -- with no import
and no row-shaped data. The loop body is an if, an accumulator, or both.
The title names the task; the prompt says which kind of loop and what it
keeps track of.

Two kinds of question, told apart by `kind`:

  "program"   the editor holds a whole program, graded on what it prints.
              Not used in this set.
  "function"  the editor defines a function named `func`. Run calls it once
              per case in `cases` and shows each call and its result; Check
              compares each result with the reference function's. Values
              are compared, not their printed form -- a dict in another
              order is the same dict -- but the container type counts, so a
              tuple is not a list, and 0 is not False.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py).
"""

import pyrun

EXERCISES = [
    # ======================================================== 1 Counting
    dict(
        id=1, ledger="P266", concept="PY4 for count if", tier="1 - Counting",
        title="Count the vowels", kind="function",
        func="count_vowels",
        cases=[("library",), ("AEIOU",), ("rhythm",), ("",)],
        prompt=(
            "Write a function `count_vowels(s)` that returns how many"
            " characters of s are vowels, upper or lower case. A for"
            " loop over the characters, an if that tests the lower-cased"
            " character against 'aeiou', and a counter.\n\n"
            "  count_vowels(\"library\") -> 2\n\n"
            "Return: an integer."
        ),
        solution=("def count_vowels(s):\n"
                  "    n = 0\n"
                  "    for ch in s:\n"
                  "        if ch.lower() in \"aeiou\":\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_vowels(s):\n"
              "    n = 0\n"
              "    for ch in s:\n"
              "        if ch in \"aeiou\":\n"
              "            n += 1\n"
              "    return n\n"),
        note="The loop visits each character; the if decides whether to"
             " count it. Testing the character as typed misses capitals,"
             " so 'AEIOU' counts zero -- lower() it first, or test against"
             " both cases.",
    ),
    dict(
        id=2, ledger="P267", concept="PY4 for range sum", tier="1 - Counting",
        title="The sum of the squares up to n", kind="function",
        func="sum_of_squares",
        cases=[(3,), (1,), (0,), (10,)],
        prompt=(
            "Write a function `sum_of_squares(n)` that returns 1*1 + 2*2"
            " + ... + n*n, using a for loop over range(1, n + 1) and a"
            " running total. For n = 0 the answer is 0.\n\n"
            "  sum_of_squares(3) -> 14\n\n"
            "Return: an integer."
        ),
        solution=("def sum_of_squares(n):\n"
                  "    total = 0\n"
                  "    for i in range(1, n + 1):\n"
                  "        total += i * i\n"
                  "    return total\n"),
        trap=("def sum_of_squares(n):\n"
              "    total = 0\n"
              "    for i in range(n):\n"
              "        total += i * i\n"
              "    return total\n"),
        note="range(n) runs from 0 to n - 1, so it adds 0 squared and"
             " never adds n squared -- one short at the top, and"
             " 0 + 1 + 4 = 5 instead of 14. range(1, n + 1) is 1 to n"
             " inclusive.",
    ),
    dict(
        id=3, ledger="P268", concept="PY4 for pairs count", tier="1 - Counting",
        title="Neighbours that match", kind="function",
        func="count_repeats",
        cases=[([1, 1, 2, 2, 2, 3],), ([],), ([7],), (["a", "b", "a"],)],
        prompt=(
            "Write a function `count_repeats(values)` that returns how"
            " many positions hold the same value as the position before"
            " them. A for loop over range(1, len(values)), comparing"
            " values[i] with values[i - 1].\n\n"
            "  count_repeats([1, 1, 2, 2, 2, 3]) -> 3\n\n"
            "Return: an integer."
        ),
        solution=("def count_repeats(values):\n"
                  "    n = 0\n"
                  "    for i in range(1, len(values)):\n"
                  "        if values[i] == values[i - 1]:\n"
                  "            n += 1\n"
                  "    return n\n"),
        trap=("def count_repeats(values):\n"
              "    n = 0\n"
              "    for i in range(len(values)):\n"
              "        if values[i] == values[i - 1]:\n"
              "            n += 1\n"
              "    return n\n"),
        note="Starting the loop at 1 is what makes values[i - 1] a real"
             " neighbour. From 0, the first comparison is values[0]"
             " against values[-1] -- the LAST item, because negative"
             " indexes wrap -- which is a repeat that is not there.",
    ),
    dict(
        id=4, ledger="P269", concept="PY4 for seen set", tier="1 - Counting",
        title="Is anything repeated?", kind="function",
        func="has_repeat",
        cases=[([1, 2, 3, 1],), ([1, 2, 3],), ([],), (["a", "b", "a", "c"],)],
        prompt=(
            "Write a function `has_repeat(values)` that returns True when"
            " any value appears more than once, anywhere in the list. A"
            " for loop that keeps the values seen so far in a set, and"
            " returns True the moment the current value is already in it.\n\n"
            "  has_repeat([1, 2, 3, 1]) -> True\n\n"
            "Return: True or False."
        ),
        solution=("def has_repeat(values):\n"
                  "    seen = set()\n"
                  "    for v in values:\n"
                  "        if v in seen:\n"
                  "            return True\n"
                  "        seen.add(v)\n"
                  "    return False\n"),
        trap=("def has_repeat(values):\n"
              "    for i in range(1, len(values)):\n"
              "        if values[i] == values[i - 1]:\n"
              "            return True\n"
              "    return False\n"),
        note="Comparing neighbours only finds repeats that sit side by"
             " side; 1 at both ends of [1, 2, 3, 1] is missed. A set of"
             " what has been seen remembers everything, and 'in' on a set"
             " is fast. The return inside the loop stops at the first"
             " repeat; the return after it runs only if there was none.",
    ),
    # ========================================================= 2 Searching
    dict(
        id=5, ledger="P270", concept="PY4 for first match", tier="2 - Searching",
        title="The first value over the limit", kind="function",
        func="first_over",
        cases=[([3, 8, 12, 5], 7), ([1, 2], 7), ([], 7), ([7, 8], 7)],
        prompt=(
            "Write a function `first_over(values, limit)` that returns"
            " the first value STRICTLY greater than limit, or None when"
            " there is none. A for loop with an if and a return inside"
            " it, and a return of None after the loop.\n\n"
            "  first_over([3, 8, 12, 5], 7) -> 8\n\n"
            "Return: the value, or None."
        ),
        solution=("def first_over(values, limit):\n"
                  "    for v in values:\n"
                  "        if v > limit:\n"
                  "            return v\n"
                  "    return None\n"),
        trap=("def first_over(values, limit):\n"
              "    for v in values:\n"
              "        if v >= limit:\n"
              "            return v\n"
              "    return None\n"),
        note="'Over' is strictly greater, so a value equal to the limit"
             " does not count: [7, 8] with limit 7 gives 8, not 7. A"
             " return inside a loop ends the function at the first"
             " match, and the line after the loop is the no-match case.",
    ),
    dict(
        id=6, ledger="P271", concept="PY4 for track index", tier="2 - Searching",
        title="Where the smallest value is", kind="function",
        func="index_of_min",
        cases=[([5, 3, 9, 3],), ([1],), ([4, 2, 0, 7],), ([-1, -5, -5],)],
        prompt=(
            "Write a function `index_of_min(values)` that returns the"
            " POSITION of the smallest value in a non-empty list, the"
            " first such position if it appears more than once. A for"
            " loop over range(len(values)) that remembers the best"
            " position so far.\n\n"
            "  index_of_min([5, 3, 9, 3]) -> 1\n\n"
            "Return: an integer."
        ),
        solution=("def index_of_min(values):\n"
                  "    best = 0\n"
                  "    for i in range(1, len(values)):\n"
                  "        if values[i] < values[best]:\n"
                  "            best = i\n"
                  "    return best\n"),
        trap=("def index_of_min(values):\n"
              "    best = values[0]\n"
              "    for v in values:\n"
              "        if v < best:\n"
              "            best = v\n"
              "    return best\n"),
        note="The question asks for the position, so the loop has to"
             " track an index, not a value -- the trap returns the"
             " smallest value itself. The strict < keeps the FIRST"
             " position among equals, because a later equal value does"
             " not replace it.",
    ),
    dict(
        id=7, ledger="P272", concept="PY4 for break sum", tier="2 - Searching",
        title="Add up until the first negative", kind="function",
        func="total_until_negative",
        cases=[([4, 5, -1, 10],), ([1, 2, 3],), ([-3, 1],), ([],)],
        prompt=(
            "Write a function `total_until_negative(values)` that returns"
            " the sum of the values BEFORE the first negative one -- all"
            " of them if none is negative. A for loop with a running"
            " total and a break when a negative value is met.\n\n"
            "  total_until_negative([4, 5, -1, 10]) -> 9\n\n"
            "Return: the total."
        ),
        solution=("def total_until_negative(values):\n"
                  "    total = 0\n"
                  "    for v in values:\n"
                  "        if v < 0:\n"
                  "            break\n"
                  "        total += v\n"
                  "    return total\n"),
        trap=("def total_until_negative(values):\n"
              "    total = 0\n"
              "    for v in values:\n"
              "        if v >= 0:\n"
              "            total += v\n"
              "    return total\n"),
        note="break leaves the loop for good; an if that merely skips"
             " the negative value carries on and adds the 10 after it."
             " The test comes before the addition, so the negative value"
             " itself is never added.",
    ),
    dict(
        id=8, ledger="P273", concept="PY4 for running max", tier="2 - Searching",
        title="The highest so far, at every step", kind="function",
        func="running_max",
        cases=[([3, 1, 4, 1, 5],), ([],), ([2, 2, 1],), ([-3, -1, -2],)],
        prompt=(
            "Write a function `running_max(values)` that returns a list"
            " where each position holds the largest value seen up to and"
            " including that position. A for loop with a 'best so far'"
            " variable that starts as None, and a result list to append"
            " to.\n\n"
            "  running_max([3, 1, 4, 1, 5]) -> [3, 3, 4, 4, 5]\n\n"
            "Return: the new list."
        ),
        solution=("def running_max(values):\n"
                  "    out = []\n"
                  "    best = None\n"
                  "    for v in values:\n"
                  "        if best is None or v > best:\n"
                  "            best = v\n"
                  "        out.append(best)\n"
                  "    return out\n"),
        trap=("def running_max(values):\n"
              "    out = []\n"
              "    best = 0\n"
              "    for v in values:\n"
              "        if v > best:\n"
              "            best = v\n"
              "        out.append(best)\n"
              "    return out\n"),
        note="Starting the best at 0 silently assumes the values are"
             " positive, and [-3, -1, -2] comes out as [0, 0, 0]. None as"
             " the starting value, with 'best is None or' in the test,"
             " takes the first value whatever it is. The append happens"
             " every time round, not only when the best changes.",
    ),
    # ========================================================== 3 Building
    dict(
        id=9, ledger="P274", concept="PY4 while countdown", tier="3 - Building",
        title="Counting down to one", kind="function",
        func="countdown",
        cases=[(5,), (1,), (0,), (3,)],
        prompt=(
            "Write a function `countdown(n)` that returns the list n,"
            " n - 1, ..., 1 -- empty for n of 0 or less. A while loop"
            " that appends n and then reduces it, running while n is"
            " above zero.\n\n"
            "  countdown(5) -> [5, 4, 3, 2, 1]\n\n"
            "Return: the list."
        ),
        solution=("def countdown(n):\n"
                  "    out = []\n"
                  "    while n > 0:\n"
                  "        out.append(n)\n"
                  "        n -= 1\n"
                  "    return out\n"),
        trap=("def countdown(n):\n"
              "    out = []\n"
              "    while n > 1:\n"
              "        out.append(n)\n"
              "        n -= 1\n"
              "    return out\n"),
        note="The loop condition decides the last value appended: while"
             " n > 0 runs once more than while n > 1 and so includes the"
             " 1. The decrement is what makes the loop end -- forget it"
             " and the loop never stops.",
    ),
    dict(
        id=10, ledger="P275", concept="PY4 for build strings", tier="3 - Building",
        title="A staircase of stars", kind="function",
        func="staircase",
        cases=[(3,), (1,), (0,), (5,)],
        prompt=(
            "Write a function `staircase(n)` that returns a list of n"
            " strings, the first one star, the second two stars, and so"
            " on. A for loop over range(1, n + 1) appending '*' * i each"
            " time.\n\n"
            "  staircase(3) -> [\"*\", \"**\", \"***\"]\n\n"
            "Return: the list of strings."
        ),
        solution=("def staircase(n):\n"
                  "    out = []\n"
                  "    for i in range(1, n + 1):\n"
                  "        out.append(\"*\" * i)\n"
                  "    return out\n"),
        trap=("def staircase(n):\n"
              "    out = []\n"
              "    for i in range(n):\n"
              "        out.append(\"*\" * i)\n"
              "    return out\n"),
        note="range(n) starts at 0, so the first step is '' -- zero stars"
             " -- and the last has n - 1. The staircase wants 1 to n,"
             " which is range(1, n + 1). String multiplication repeats"
             " the star i times.",
    ),
    dict(
        id=11, ledger="P276", concept="PY4 for if elif", tier="3 - Building",
        title="Fizz and buzz, as a list", kind="function",
        func="fizzbuzz",
        cases=[(15,), (5,), (1,), (0,)],
        prompt=(
            "Write a function `fizzbuzz(n)` that returns a list for 1 to"
            " n where multiples of 15 become 'FizzBuzz', other multiples"
            " of 3 'Fizz', other multiples of 5 'Buzz', and everything"
            " else stays a number. A for loop with an if / elif / elif /"
            " else, testing 15 FIRST.\n\n"
            "  fizzbuzz(5) -> [1, 2, \"Fizz\", 4, \"Buzz\"]\n\n"
            "Return: the list."
        ),
        solution=("def fizzbuzz(n):\n"
                  "    out = []\n"
                  "    for i in range(1, n + 1):\n"
                  "        if i % 15 == 0:\n"
                  "            out.append(\"FizzBuzz\")\n"
                  "        elif i % 3 == 0:\n"
                  "            out.append(\"Fizz\")\n"
                  "        elif i % 5 == 0:\n"
                  "            out.append(\"Buzz\")\n"
                  "        else:\n"
                  "            out.append(i)\n"
                  "    return out\n"),
        trap=("def fizzbuzz(n):\n"
              "    out = []\n"
              "    for i in range(1, n + 1):\n"
              "        if i % 3 == 0:\n"
              "            out.append(\"Fizz\")\n"
              "        elif i % 5 == 0:\n"
              "            out.append(\"Buzz\")\n"
              "        elif i % 15 == 0:\n"
              "            out.append(\"FizzBuzz\")\n"
              "        else:\n"
              "            out.append(i)\n"
              "    return out\n"),
        note="An if / elif chain stops at the first true branch, so the"
             " most specific test -- divisible by 15 -- has to come"
             " first. With it last, 15 is caught by the 'divisible by 3'"
             " branch and 'FizzBuzz' never appears. The same rule as a"
             " SQL CASE.",
    ),
    dict(
        id=12, ledger="P277", concept="PY4 for reverse build", tier="3 - Building",
        title="The words in reverse order", kind="function",
        func="reverse_words",
        cases=[("the glass path",), ("one",), ("",), ("a b c d",)],
        prompt=(
            "Write a function `reverse_words(s)` that returns the words"
            " of s in the opposite order, joined by single spaces. A for"
            " loop over s.split() that builds a list by inserting each"
            " word at the FRONT -- insert(0, word) -- then ' '.join()"
            " of the list.\n\n"
            "  reverse_words(\"the glass path\") -> \"path glass the\"\n\n"
            "Return: the string."
        ),
        solution=("def reverse_words(s):\n"
                  "    out = []\n"
                  "    for w in s.split():\n"
                  "        out.insert(0, w)\n"
                  "    return \" \".join(out)\n"),
        trap=("def reverse_words(s):\n"
              "    out = []\n"
              "    for w in s.split():\n"
              "        out.append(w)\n"
              "    return \" \".join(out)\n"),
        note="insert(0, w) puts each new word before the ones already"
             " there, so the last word ends up first; append keeps the"
             " original order. The empty string splits to no words and"
             " joins back to ''. (s.split()[::-1] would do it without a"
             " loop -- this one is about the loop.)",
    ),
    # ======================================================== 4 Reducing
    dict(
        id=13, ledger="P278", concept="PY4 while digits", tier="4 - Reducing",
        title="The digits of a number, added up", kind="function",
        func="digit_sum",
        cases=[(1234,), (0,), (9,), (100100,)],
        prompt=(
            "Write a function `digit_sum(n)` that returns the sum of the"
            " decimal digits of a non-negative integer, using a while"
            " loop that adds n % 10 to a total and then replaces n with"
            " n // 10, running while n is above zero.\n\n"
            "  digit_sum(1234) -> 10\n\n"
            "Return: an integer."
        ),
        solution=("def digit_sum(n):\n"
                  "    total = 0\n"
                  "    while n > 0:\n"
                  "        total += n % 10\n"
                  "        n //= 10\n"
                  "    return total\n"),
        trap=("def digit_sum(n):\n"
              "    total = 0\n"
              "    for ch in str(n):\n"
              "        total += ch\n"
              "    return total\n"),
        note="n % 10 is the last digit and n // 10 drops it, so the loop"
             " eats the number from the right until nothing is left."
             " Looping over str(n) is a fair alternative, but the"
             " characters have to be converted with int() -- adding a"
             " string to a number is a TypeError.",
    ),
    dict(
        id=14, ledger="P279", concept="PY4 for sum count guard", tier="4 - Reducing",
        title="An average that copes with nothing", kind="function",
        func="average_or_zero",
        cases=[([2, 4, 6],), ([],), ([5],), ([1, 2],)],
        prompt=(
            "Write a function `average_or_zero(values)` that returns the"
            " mean of the values, or 0 for an empty list. A for loop"
            " that keeps a total and a count, then an if that returns 0"
            " when the count is zero and the division otherwise.\n\n"
            "  average_or_zero([2, 4, 6]) -> 4.0\n"
            "  average_or_zero([]) -> 0\n\n"
            "Return: the mean, or 0."
        ),
        solution=("def average_or_zero(values):\n"
                  "    total = 0\n"
                  "    count = 0\n"
                  "    for v in values:\n"
                  "        total += v\n"
                  "        count += 1\n"
                  "    if count == 0:\n"
                  "        return 0\n"
                  "    return total / count\n"),
        trap=("def average_or_zero(values):\n"
              "    total = 0\n"
              "    count = 0\n"
              "    for v in values:\n"
              "        total += v\n"
              "        count += 1\n"
              "    return total / count\n"),
        note="Dividing by a count of zero raises ZeroDivisionError, which"
             " is why the question asks for the guard. The loop is the"
             " long form of sum() and len(); the if afterwards is the"
             " part neither of those gives you.",
    ),
    dict(
        id=15, ledger="P280", concept="PY4 while steps", tier="4 - Reducing",
        title="Steps to reach one", kind="function",
        func="collatz_steps",
        cases=[(6,), (1,), (27,), (8,)],
        prompt=(
            "Write a function `collatz_steps(n)` that counts how many"
            " steps it takes to reach 1 from a positive integer when each"
            " step halves an even number and turns an odd number into 3n"
            " + 1. A while loop running while n is not 1, with an if /"
            " else for the two cases and a step counter that starts at"
            " 0.\n\n"
            "  collatz_steps(6) -> 8\n\n"
            "Return: an integer."
        ),
        solution=("def collatz_steps(n):\n"
                  "    steps = 0\n"
                  "    while n != 1:\n"
                  "        if n % 2 == 0:\n"
                  "            n = n // 2\n"
                  "        else:\n"
                  "            n = 3 * n + 1\n"
                  "        steps += 1\n"
                  "    return steps\n"),
        trap=("def collatz_steps(n):\n"
              "    steps = 1\n"
              "    while n != 1:\n"
              "        if n % 2 == 0:\n"
              "            n = n // 2\n"
              "        else:\n"
              "            n = 3 * n + 1\n"
              "        steps += 1\n"
              "    return steps\n"),
        note="A while loop whose condition is 'not there yet' is the"
             " shape for 'keep going until': the body changes n, the"
             " counter goes up once per pass. Starting the counter at 1"
             " counts a step that was never taken, and says 1 needs a"
             " step to reach 1. Use // for the halving so n stays an int.",
    ),
]

BY_ID = {e["id"]: e for e in EXERCISES}
TIERS = list(dict.fromkeys(e["tier"] for e in EXERCISES))


def is_program(exercise):
    return exercise["kind"] == "program"


def run(exercise, code):
    """Run the learner's code the way the question needs, and return the
    raw pyrun result."""
    if is_program(exercise):
        return pyrun.run_program(code, exercise.get("stdin", ""))
    return pyrun.run_function(code, exercise["func"], exercise["cases"])


def render(exercise, result):
    """The text for the output pane after a Run."""
    if is_program(exercise):
        text = result["stdout"]
        if result["stderr"]:
            text += ("\n" if text and not text.endswith("\n") else "") + result["stderr"]
        return text or "(nothing printed)"
    parts = []
    if result.get("stdout", "").strip():
        parts.append(result["stdout"].rstrip() + "\n")
    if result["define_error"]:
        parts.append(result["define_error"])
        return "\n".join(parts)
    parts.append("Test calls:")
    for r in result["results"]:
        if "error" in r:
            parts.append(f"  {r['call']}\n    raised: {r['error'].splitlines()[-1]}")
        else:
            parts.append(f"  {r['call']} -> {r['repr']}")
    return "\n".join(parts)


def _lines(text):
    """Output as a list of lines, trailing spaces and blank lines dropped."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def _short(s, n=60):
    return s if len(s) <= n else s[:n - 3] + "..."


def grade(exercise, code):
    """(passed, message, output_text): run the learner's code and the
    reference the same way, and compare."""
    got = run(exercise, code)
    text = render(exercise, got)
    if got.get("timed_out"):
        return False, (got.get("stderr") or got.get("define_error")), text

    if is_program(exercise):
        if got["stderr"]:
            return False, "Your program raised an error -- see the output pane.", text
        want = pyrun.run_program(exercise["solution"], exercise.get("stdin", ""))
        g, w = _lines(got["stdout"]), _lines(want["stdout"])
        if g == w:
            return True, f"Correct - {len(w)} line(s) matched.", text
        if not g:
            return False, f"Your program printed nothing; expected {len(w)} line(s).", text
        if len(g) != len(w):
            return False, (f"Wrong number of lines: you printed {len(g)},"
                           f" expected {len(w)}."), text
        for i, (a, b) in enumerate(zip(g, w), 1):
            if a != b:
                return False, (f"Line {i} differs.\n  Expected: {_short(b)!r}"
                               f"\n  Printed:  {_short(a)!r}"), text
        return False, "Output differs.", text

    if got["define_error"]:
        return False, got["define_error"].splitlines()[-1], text
    want = pyrun.run_function(exercise["solution"], exercise["func"], exercise["cases"])
    if want["define_error"]:
        return False, f"reference solution failed: {want['define_error']}", text
    failed = 0
    first = None
    for g, w in zip(got["results"], want["results"]):
        if "error" in g:
            failed += 1
            first = first or (f"{g['call']} raised {g['error'].splitlines()[-1]};"
                              f" expected {w['repr']}")
        elif g["canon"] != w["canon"]:
            failed += 1
            first = first or (f"{g['call']} returned {_short(g['repr'])},"
                              f" expected {_short(w['repr'])}")
    if not failed:
        return True, f"Correct - all {len(want['results'])} test call(s) matched.", text
    return False, (f"{failed} of {len(want['results'])} test call(s) wrong."
                   f"\n  {first}"), text
