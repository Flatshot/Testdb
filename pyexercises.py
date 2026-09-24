"""Python practice exercises: twenty questions from a first print() to
dictionaries and comprehensions.

Two kinds of question, told apart by `kind`:

  "program"   the editor holds a whole program. Run executes it and shows
              what it printed; Check compares that, line for line, with what
              the reference program prints. `stdin`, where present, is the
              text the program can read with input().
  "function"  the editor defines a function named `func`. Run calls it once
              per case in `cases` and shows each call and its result; Check
              compares each result with the reference function's. Values
              are compared, not their printed form -- a dict in another
              order is the same dict -- but the container type counts, so a
              tuple is not a list.

Every question carries a `trap`: a wrong answer a beginner is likely to
write, which check_questions.py proves the grader rejects. The `note` is
shown when the answer is right, and says what the trap would have got wrong.

The code runs in a separate interpreter with a time limit (see pyrun.py),
so an infinite loop or a print in a loop is stopped, not fatal.
"""

import pyrun

EXERCISES = [
    # ======================================================== 1 First steps
    dict(
        id=1, ledger="P001", concept="PY0 print", tier="1 - First steps",
        title="Say hello", kind="program",
        prompt=(
            "Write a program that prints exactly this line:\n\n"
            "  Hello, hospital!\n\n"
            "Print: the line above, punctuation included."
        ),
        solution='print("Hello, hospital!")\n',
        trap='print("Hello hospital!")\n',
        note="print() writes its argument and then a newline. The text"
             " inside the quotes is printed exactly as written -- the"
             " comma and the exclamation mark are part of the answer, and"
             " the grader compares character by character.",
    ),
    dict(
        id=2, ledger="P002", concept="PY0 arithmetic", tier="1 - First steps",
        title="Three sums", kind="program",
        prompt=(
            "Print three numbers, one per line, each worked out by Python"
            " rather than typed in:\n\n"
            "  the hours in a 365-day year\n"
            "  the minutes in a week\n"
            "  2 to the power of 10\n\n"
            "Print: three lines, the numbers only."
        ),
        solution="print(365 * 24)\nprint(7 * 24 * 60)\nprint(2 ** 10)\n",
        trap="print(365 * 24)\nprint(7 * 24 * 60)\nprint(2 ^ 10)\n",
        note="Power is **, not ^. In Python ^ is bitwise exclusive-or, so"
             " 2 ^ 10 is 8 -- it runs without complaint and is simply the"
             " wrong number. The other arithmetic operators are + - * and /,"
             " with // for whole-number division and % for the remainder.",
    ),
    dict(
        id=3, ledger="P003", concept="PY0 f-strings", tier="1 - First steps",
        title="Variables in a sentence", kind="program",
        prompt=(
            "Put the ward name 'Fleming', its 16 beds and its 11 patients in"
            " three variables, then print two lines built from them:\n\n"
            "  Fleming has 16 beds and 11 patients\n"
            "  Occupancy: 68.8%\n\n"
            "The percentage is patients divided by beds times 100, shown"
            " to ONE decimal place -- use an f-string with a format spec"
            " such as {x:.1f}.\n\n"
            "Print: the two lines."
        ),
        solution=('ward = "Fleming"\nbeds = 16\npatients = 11\n'
                  'print(f"{ward} has {beds} beds and {patients} patients")\n'
                  'print(f"Occupancy: {patients / beds * 100:.1f}%")\n'),
        trap=('ward = "Fleming"\nbeds = 16\npatients = 11\n'
              'print(ward + " has " + str(beds) + " beds and " + str(patients)'
              ' + " patients")\n'
              'print("Occupancy: " + str(patients / beds * 100) + "%")\n'),
        note="An f-string puts any expression inside {braces} and can"
             " format it on the way: {value:.1f} means one decimal place."
             " Building the line with + and str() works for the first"
             " line, but the second prints 68.75 -- str() has no opinion"
             " about decimals.",
    ),
    dict(
        id=4, ledger="P004", concept="PY0 input", tier="1 - First steps",
        title="Reading a line", kind="program",
        stdin="Ada\n",
        prompt=(
            "Read one line from the keyboard with input() -- it will be a"
            " name -- and greet it:\n\n"
            "  Good morning, Ada.\n\n"
            "When you press Run the program is given the line 'Ada' as its"
            " input, so you cannot type it yourself.\n\n"
            "Print: the greeting, with the name that was read."
        ),
        solution='name = input()\nprint(f"Good morning, {name}.")\n',
        trap='name = input("Name? ")\nprint(f"Good morning, {name}.")\n',
        note="input() returns the line typed, without its newline. An"
             " argument to input() is a prompt, and a prompt is PRINTED --"
             " so input(\"Name? \") puts 'Name? ' on the output before the"
             " greeting, and the output no longer matches. Prompts are for"
             " people at a keyboard; a program that is fed its input has"
             " no one to read them.",
    ),
    # ================================================= 2 Strings and lists
    dict(
        id=5, ledger="P005", concept="PY1 strings", tier="2 - Strings and lists",
        title="Initials", kind="function",
        func="initials",
        cases=[("Florence Nightingale",), ("Mary Seacole",),
               ("Jean Paul Gaultier",), ("Ada",)],
        prompt=(
            "Write a function `initials(name)` that returns the first letter"
            " of each word in the name, each followed by a full stop:\n\n"
            "  initials(\"Florence Nightingale\") -> \"F.N.\"\n\n"
            "A name can have one word or several. str.split() breaks a"
            " string into a list of words.\n\n"
            "Return: the initials as one string."
        ),
        solution=('def initials(name):\n'
                  '    return "".join(word[0] + "." for word in name.split())\n'),
        trap=('def initials(name):\n'
              '    words = name.split()\n'
              '    return words[0][0] + "." + words[1][0] + "."\n'),
        note="Indexing words[1] assumes exactly two words: a third is"
             " ignored and a single word raises IndexError. A loop over"
             " name.split() -- or a join over it -- handles any number."
             " word[0] is the first character of a string; strings are"
             " sequences, indexed from 0 like lists.",
    ),
    dict(
        id=6, ledger="P006", concept="PY1 strings", tier="2 - Strings and lists",
        title="Counting vowels", kind="function",
        func="count_vowels",
        cases=[("Observation",), ("RHYTHM",), ("Aeiou Sky",), ("",)],
        prompt=(
            "Write a function `count_vowels(text)` that returns how many"
            " vowels -- a, e, i, o, u -- the text contains, in either"
            " case:\n\n"
            "  count_vowels(\"Observation\") -> 5\n\n"
            "Return: the count as an integer."
        ),
        solution=('def count_vowels(text):\n'
                  '    count = 0\n'
                  '    for ch in text.lower():\n'
                  '        if ch in "aeiou":\n'
                  '            count += 1\n'
                  '    return count\n'),
        trap=('def count_vowels(text):\n'
              '    count = 0\n'
              '    for ch in text:\n'
              '        if ch in "aeiou":\n'
              '            count += 1\n'
              '    return count\n'),
        note="The capital O in Observation is a vowel too. Lower-casing the"
             " text once, with text.lower(), is simpler than listing both"
             " cases -- and `ch in \"aeiou\"` asks whether a one-character"
             " string appears inside another, which is the same `in` that"
             " tests list membership.",
    ),
    dict(
        id=7, ledger="P007", concept="PY1 slicing", tier="2 - Strings and lists",
        title="Every other one", kind="function",
        func="every_other",
        cases=[([1, 2, 3, 4, 5],), (["a", "b"],), ([],), ([7],)],
        prompt=(
            "Write a function `every_other(items)` that returns a new list"
            " holding the first item, the third, the fifth and so on --"
            " the ones at even positions counting from 0:\n\n"
            "  every_other([1, 2, 3, 4, 5]) -> [1, 3, 5]\n\n"
            "A slice can do it in one expression: items[start:stop:step].\n\n"
            "Return: the new list; an empty list stays empty."
        ),
        solution="def every_other(items):\n    return items[::2]\n",
        trap="def every_other(items):\n    return items[1::2]\n",
        note="items[::2] starts at index 0 and takes every second item;"
             " items[1::2] starts at index 1 and returns the OTHER half."
             " Slicing never raises on an empty list or a short one -- it"
             " just returns what is there, which is why no special case is"
             " needed.",
    ),
    dict(
        id=8, ledger="P008", concept="PY1 lists", tier="2 - Strings and lists",
        title="The longest word", kind="function",
        func="longest_word",
        cases=[("the ward round starts at nine",), ("a bb cc",),
               ("single",), ("",)],
        prompt=(
            "Write a function `longest_word(sentence)` that returns the"
            " longest word in the sentence. If several tie, return the one"
            " that comes FIRST. An empty sentence returns an empty"
            " string.\n\n"
            "  longest_word(\"a bb cc\") -> \"bb\"\n\n"
            "Return: the word."
        ),
        solution=('def longest_word(sentence):\n'
                  '    best = ""\n'
                  '    for word in sentence.split():\n'
                  '        if len(word) > len(best):\n'
                  '            best = word\n'
                  '    return best\n'),
        trap=('def longest_word(sentence):\n'
              '    words = sentence.split()\n'
              '    if not words:\n'
              '        return ""\n'
              '    return sorted(words, key=len)[-1]\n'),
        note="Sorting by length and taking the last item returns the LAST"
             " of the tied words, because a sort keeps ties in their"
             " original order. A loop that only replaces the best on a"
             " strictly greater length keeps the first; so does"
             " max(words, key=len), which returns the first maximum it meets.",
    ),
    # ============================================== 3 Conditions and loops
    dict(
        id=9, ledger="P009", concept="PY2 if/elif", tier="3 - Conditions and loops",
        title="Triage by heart rate", kind="function",
        func="triage",
        cases=[(100,), (101,), (60,), (59,), (75,)],
        prompt=(
            "Write a function `triage(heart_rate)` that returns 'high' for"
            " a rate over 100, 'low' for a rate under 60, and 'normal'"
            " otherwise. 100 and 60 are both normal.\n\n"
            "  triage(101) -> 'high'\n\n"
            "Return: one of the three strings."
        ),
        solution=('def triage(heart_rate):\n'
                  '    if heart_rate > 100:\n'
                  '        return "high"\n'
                  '    elif heart_rate < 60:\n'
                  '        return "low"\n'
                  '    else:\n'
                  '        return "normal"\n'),
        trap=('def triage(heart_rate):\n'
              '    if heart_rate >= 100:\n'
              '        return "high"\n'
              '    elif heart_rate <= 60:\n'
              '        return "low"\n'
              '    else:\n'
              '        return "normal"\n'),
        note="'Over 100' is > 100, not >= 100: the boundary belongs to"
             " normal. Off-by-one at a boundary is the commonest bug in an"
             " if; test the boundary values themselves, as the cases here"
             " do. Once a return runs the function is over, so the elif"
             " and else only see rates the first test let through.",
    ),
    dict(
        id=10, ledger="P010", concept="PY2 for/range", tier="3 - Conditions and loops",
        title="The seven times table", kind="program",
        prompt=(
            "Print the seven times table from 1 to 10, one line each, in"
            " this form:\n\n"
            "  7 x 1 = 7\n"
            "  7 x 2 = 14\n"
            "  ...\n"
            "  7 x 10 = 70\n\n"
            "Use a for loop over range(), not ten print statements.\n\n"
            "Print: ten lines."
        ),
        solution='for n in range(1, 11):\n    print(f"7 x {n} = {7 * n}")\n',
        trap='for n in range(1, 10):\n    print(f"7 x {n} = {7 * n}")\n',
        note="range(1, 10) stops BEFORE 10, so the table ends at 9. The"
             " stop value is never included, which is what makes range(len"
             "(items)) produce exactly the valid indexes -- and what makes"
             " an inclusive table need range(1, 11).",
    ),
    dict(
        id=11, ledger="P011", concept="PY2 while", tier="3 - Conditions and loops",
        title="Steps to one", kind="function",
        func="collatz_steps",
        cases=[(1,), (2,), (6,), (27,)],
        prompt=(
            "Write a function `collatz_steps(n)` that counts how many steps"
            " it takes to reach 1 from n, where a step halves an even"
            " number and turns an odd number into 3n + 1:\n\n"
            "  6 -> 3 -> 10 -> 5 -> 16 -> 8 -> 4 -> 2 -> 1, so"
            " collatz_steps(6) -> 8\n\n"
            "collatz_steps(1) is 0. You do not know in advance how many"
            " steps there are, so this is a while loop.\n\n"
            "Return: the number of steps."
        ),
        solution=('def collatz_steps(n):\n'
                  '    steps = 0\n'
                  '    while n != 1:\n'
                  '        if n % 2 == 0:\n'
                  '            n = n // 2\n'
                  '        else:\n'
                  '            n = 3 * n + 1\n'
                  '        steps += 1\n'
                  '    return steps\n'),
        trap=('def collatz_steps(n):\n'
              '    steps = 1\n'
              '    while n != 1:\n'
              '        if n % 2 == 0:\n'
              '            n = n // 2\n'
              '        else:\n'
              '            n = 3 * n + 1\n'
              '        steps += 1\n'
              '    return steps\n'),
        note="A while loop runs until its condition is false, and the"
             " counter counts the times the body ran -- so it starts at 0,"
             " and n = 1 leaves it there. Starting at 1 counts the number"
             " itself as a step. n // 2 keeps the result an integer; n / 2"
             " would turn it into 3.0, and then 3.0 % 2 keeps working but"
             " the final answer arrives as a float.",
    ),
    dict(
        id=12, ledger="P012", concept="PY2 enumerate/break",
        tier="3 - Conditions and loops",
        title="The first negative", kind="function",
        func="first_negative_index",
        cases=[([3, 1, -4, 1, -5],), ([1, 2],), ([-1],), ([],)],
        prompt=(
            "Write a function `first_negative_index(nums)` that returns the"
            " index of the first negative number in the list, or -1 if"
            " there is none:\n\n"
            "  first_negative_index([3, 1, -4, 1, -5]) -> 2\n\n"
            "enumerate(nums) gives you each index with its value; return"
            " as soon as you find one.\n\n"
            "Return: an index, or -1."
        ),
        solution=('def first_negative_index(nums):\n'
                  '    for i, n in enumerate(nums):\n'
                  '        if n < 0:\n'
                  '            return i\n'
                  '    return -1\n'),
        trap=('def first_negative_index(nums):\n'
              '    found = -1\n'
              '    for i, n in enumerate(nums):\n'
              '        if n < 0:\n'
              '            found = i\n'
              '    return found\n'),
        note="Without a return or a break the loop keeps going, and the"
             " variable ends up holding the LAST negative's index, not the"
             " first. A return inside the loop leaves both the loop and the"
             " function at once; the return after the loop only runs when"
             " nothing was found.",
    ),
    # ============================================================ 4 Functions
    dict(
        id=13, ledger="P013", concept="PY3 functions", tier="4 - Functions",
        title="Body mass index", kind="function",
        func="bmi",
        cases=[(70, 1.75), (90, 1.8), (50, 1.6)],
        prompt=(
            "Write a function `bmi(weight_kg, height_m)` that returns the"
            " body mass index -- weight divided by the SQUARE of height --"
            " rounded to one decimal place:\n\n"
            "  bmi(70, 1.75) -> 22.9\n\n"
            "Return: a number with one decimal place."
        ),
        solution=('def bmi(weight_kg, height_m):\n'
                  '    return round(weight_kg / height_m ** 2, 1)\n'),
        trap=('def bmi(weight_kg, height_m):\n'
              '    return round(weight_kg / height_m, 1)\n'),
        note="round(x, 1) rounds to one decimal place; round(x) alone gives"
             " an integer. ** binds tighter than /, so weight / height ** 2"
             " squares the height first -- no brackets needed, though"
             " (height_m ** 2) does no harm and reads more clearly.",
    ),
    dict(
        id=14, ledger="P014", concept="PY3 default arguments", tier="4 - Functions",
        title="Arguments you can leave out", kind="function",
        func="course_total_mg",
        cases=[(500,), (500, 3), (250, 4, 5)],
        prompt=(
            "Write a function `course_total_mg(dose_mg, times_per_day, days)`"
            " that returns the total milligrams over a course: dose times"
            " doses per day times days. The last two arguments are"
            " optional -- times_per_day defaults to 2 and days to 7 -- so"
            " all three of these calls work:\n\n"
            "  course_total_mg(500) -> 7000\n"
            "  course_total_mg(500, 3) -> 10500\n"
            "  course_total_mg(250, 4, 5) -> 5000\n\n"
            "Return: the total as an integer."
        ),
        solution=('def course_total_mg(dose_mg, times_per_day=2, days=7):\n'
                  '    return dose_mg * times_per_day * days\n'),
        trap=('def course_total_mg(dose_mg, times_per_day, days):\n'
              '    return dose_mg * times_per_day * days\n'),
        note="A parameter with a default -- days=7 -- may be left out of"
             " the call. Without defaults, course_total_mg(500) raises"
             " TypeError: missing 2 required positional arguments. Defaults"
             " must come after the parameters that have none, and the"
             " arguments are matched left to right, so the second call"
             " sets times_per_day and leaves days at 7.",
    ),
    dict(
        id=15, ledger="P015", concept="PY3 tuples", tier="4 - Functions",
        title="Three answers at once", kind="function",
        func="min_max_mean",
        cases=[([1, 2, 3, 4],), ([10],), ([2, 9, 4],)],
        prompt=(
            "Write a function `min_max_mean(nums)` that returns the"
            " smallest value, the largest, and the mean rounded to two"
            " decimal places -- as a TUPLE of three:\n\n"
            "  min_max_mean([1, 2, 3, 4]) -> (1, 4, 2.5)\n\n"
            "min(), max(), sum() and len() do the arithmetic. The list is"
            " never empty.\n\n"
            "Return: a tuple (smallest, largest, mean)."
        ),
        solution=('def min_max_mean(nums):\n'
                  '    return min(nums), max(nums), round(sum(nums) / len(nums), 2)\n'),
        trap=('def min_max_mean(nums):\n'
              '    return [min(nums), max(nums), round(sum(nums) / len(nums), 2)]\n'),
        note="A function returns one value; a tuple is how it returns"
             " several. `return a, b, c` makes one -- the brackets are"
             " optional -- and the caller can unpack it: lo, hi, avg ="
             " min_max_mean(nums). A list holds the same numbers but is a"
             " different type, and the grader compares types too, because"
             " a caller expecting a tuple may rely on it being immutable.",
    ),
    dict(
        id=16, ledger="P016", concept="PY3 booleans", tier="4 - Functions",
        title="Reads the same backwards", kind="function",
        func="is_palindrome",
        cases=[("Never odd or even",), ("Ward",), ("",), ("A Toyota",)],
        prompt=(
            "Write a function `is_palindrome(text)` that returns True when"
            " the text reads the same backwards as forwards, ignoring case"
            " and spaces:\n\n"
            "  is_palindrome(\"Never odd or even\") -> True\n\n"
            "text[::-1] is the text reversed. An empty string counts as a"
            " palindrome.\n\n"
            "Return: True or False."
        ),
        solution=('def is_palindrome(text):\n'
                  '    cleaned = text.lower().replace(" ", "")\n'
                  '    return cleaned == cleaned[::-1]\n'),
        trap=('def is_palindrome(text):\n'
              '    cleaned = text.lower()\n'
              '    return cleaned == cleaned[::-1]\n'),
        note="A comparison is already a boolean, so `return cleaned =="
             " cleaned[::-1]` needs no if/else around it. The spaces have"
             " to go before comparing: 'never odd or even' reversed is"
             " 'neve ro ddo reven', which is not the same string.",
    ),
    # ============================================ 5 Dicts, sets and comprehensions
    dict(
        id=17, ledger="P017", concept="PY4 dicts",
        tier="5 - Dicts, sets and comprehensions",
        title="Counting words", kind="function",
        func="word_counts",
        cases=[("the ward the bed",), ("A a A",), ("",)],
        prompt=(
            "Write a function `word_counts(text)` that returns a dictionary"
            " from each word, lower-cased, to how many times it appears:\n\n"
            "  word_counts(\"the ward the bed\") -> {'the': 2, 'ward': 1,"
            " 'bed': 1}\n\n"
            "dict.get(key, 0) reads a count that may not exist yet.\n\n"
            "Return: the dictionary; empty text gives an empty one."
        ),
        solution=('def word_counts(text):\n'
                  '    counts = {}\n'
                  '    for word in text.lower().split():\n'
                  '        counts[word] = counts.get(word, 0) + 1\n'
                  '    return counts\n'),
        trap=('def word_counts(text):\n'
              '    counts = {}\n'
              '    for word in text.split():\n'
              '        counts[word] = counts.get(word, 0) + 1\n'
              '    return counts\n'),
        note="counts[word] on a word not yet seen raises KeyError;"
             " counts.get(word, 0) returns 0 instead, so the first sighting"
             " and the fifth are the same line of code. Without .lower(),"
             " 'A' and 'a' are two different keys. The standard library's"
             " collections.Counter does exactly this, once you have written"
             " it by hand once.",
    ),
    dict(
        id=18, ledger="P018", concept="PY4 dicts",
        tier="5 - Dicts, sets and comprehensions",
        title="The most common item", kind="function",
        func="most_common",
        cases=[(["b", "a", "b", "a"],), ([3, 1, 3, 1, 1],), (["x"],)],
        prompt=(
            "Write a function `most_common(items)` that returns the item"
            " appearing most often. If several tie, return the one that"
            " appears FIRST in the list. The list is never empty.\n\n"
            "  most_common([\"b\", \"a\", \"b\", \"a\"]) -> \"b\"\n\n"
            "Count into a dictionary first, then look for the largest"
            " count; a dictionary remembers the order keys were added.\n\n"
            "Return: the item."
        ),
        solution=('def most_common(items):\n'
                  '    counts = {}\n'
                  '    for item in items:\n'
                  '        counts[item] = counts.get(item, 0) + 1\n'
                  '    best = None\n'
                  '    for item, count in counts.items():\n'
                  '        if best is None or count > counts[best]:\n'
                  '            best = item\n'
                  '    return best\n'),
        trap=('def most_common(items):\n'
              '    return max(sorted(set(items)), key=items.count)\n'),
        note="A dict keeps insertion order, so walking counts.items() visits"
             " items in the order they were first seen, and replacing the"
             " best only on a strictly greater count keeps the first of a"
             " tie. Going through a set -- or a sorted one -- throws that"
             " order away, and max() then breaks the tie by whatever order"
             " it was given.",
    ),
    dict(
        id=19, ledger="P019", concept="PY4 sets",
        tier="5 - Dicts, sets and comprehensions",
        title="Prescribed on both wards", kind="function",
        func="shared_drugs",
        cases=[(["Morphine", "Codeine", "Codeine"],
                ["Codeine", "Aspirin", "Morphine"]),
               ([], ["Codeine"]),
               (["Insulin"], ["Insulin"])],
        prompt=(
            "Write a function `shared_drugs(ward_a, ward_b)` that takes two"
            " lists of drug names, possibly with repeats, and returns the"
            " names that appear in BOTH -- each once, sorted:\n\n"
            "  shared_drugs([\"Morphine\", \"Codeine\", \"Codeine\"],"
            " [\"Codeine\", \"Aspirin\", \"Morphine\"]) -> [\"Codeine\","
            " \"Morphine\"]\n\n"
            "A set drops the repeats and & finds what two sets share.\n\n"
            "Return: a sorted LIST of names."
        ),
        solution=('def shared_drugs(ward_a, ward_b):\n'
                  '    return sorted(set(ward_a) & set(ward_b))\n'),
        trap=('def shared_drugs(ward_a, ward_b):\n'
              '    return set(ward_a) & set(ward_b)\n'),
        note="set(a) & set(b) is the intersection, and a set has no order"
             " -- which is exactly why the question asks for a sorted list:"
             " sorted() takes any collection and returns a list. Returning"
             " the set itself is a different type, and one whose printed"
             " order is not something a caller can rely on.",
    ),
    dict(
        id=20, ledger="P020", concept="PY4 try/except",
        tier="5 - Dicts, sets and comprehensions",
        title="Readings that are not numbers", kind="function",
        func="parse_readings",
        cases=[(["72", "x", "-5", " 80 ", "3.5"],), ([],), (["1", "2"],)],
        prompt=(
            "Write a function `parse_readings(strings)` that turns a list of"
            " strings into a list of integers, SKIPPING any string that is"
            " not a whole number:\n\n"
            "  parse_readings([\"72\", \"x\", \"-5\", \" 80 \", \"3.5\"])"
            " -> [72, -5, 80]\n\n"
            "int(s) converts a string and raises ValueError when it cannot;"
            " catch that with try/except rather than inspecting the"
            " characters yourself.\n\n"
            "Return: the list of integers, in the original order."
        ),
        solution=('def parse_readings(strings):\n'
                  '    readings = []\n'
                  '    for s in strings:\n'
                  '        try:\n'
                  '            readings.append(int(s))\n'
                  '        except ValueError:\n'
                  '            pass\n'
                  '    return readings\n'),
        trap=('def parse_readings(strings):\n'
              '    return [int(s) for s in strings if s.strip().isdigit()]\n'),
        note="isdigit() is false for '-5', so a negative reading is thrown"
             " away, and it would also be false for '+3'. Asking int() and"
             " catching the ValueError accepts exactly what int() accepts --"
             " including the spaces around ' 80 ' -- and nothing else."
             " This is the Python habit: try the operation, handle the"
             " failure, rather than predicting it.",
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
