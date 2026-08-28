SNIPPETS = {
    "Hello World": (
        '# Your first program\n'
        'print("Hello, World!")\n'
        'name = input("What is your name? ")\n'
        'print("Nice to meet you,", name)\n'
    ),
    "Variables & Data Types": (
        '# Different types of data\n'
        'age = 17                 # integer\n'
        'marks = 92.5             # float\n'
        'name = "Ayush"           # string\n'
        'is_student = True        # boolean\n\n'
        'print(type(age), age)\n'
        'print(type(marks), marks)\n'
        'print(type(name), name)\n'
        'print(type(is_student), is_student)\n'
    ),
    "If-Else (Grade Checker)": (
        '# Grade checker using if-elif-else\n'
        'marks = int(input("Enter your marks (0-100): "))\n\n'
        'if marks >= 90:\n'
        '    print("Grade: A+")\n'
        'elif marks >= 75:\n'
        '    print("Grade: A")\n'
        'elif marks >= 60:\n'
        '    print("Grade: B")\n'
        'elif marks >= 33:\n'
        '    print("Grade: Pass")\n'
        'else:\n'
        '    print("Grade: Fail")\n'
    ),
    "For Loop (Table)": (
        '# Print multiplication table\n'
        'num = int(input("Enter a number: "))\n\n'
        'for i in range(1, 11):\n'
        '    print(num, "x", i, "=", num * i)\n'
    ),
    "While Loop (Sum)": (
        '# Sum of numbers until user enters 0\n'
        'total = 0\n'
        'while True:\n'
        '    n = int(input("Enter a number (0 to stop): "))\n'
        '    if n == 0:\n'
        '        break\n'
        '    total += n\n'
        'print("Total sum =", total)\n'
    ),
    "Lists": (
        '# Working with lists\n'
        'fruits = ["apple", "banana", "mango"]\n\n'
        'fruits.append("orange")      # add\n'
        'print("All fruits:", fruits)\n'
        'print("First fruit:", fruits[0])\n'
        'print("Total fruits:", len(fruits))\n\n'
        'for fruit in fruits:\n'
        '    print("-", fruit)\n'
    ),
    "Dictionary": (
        '# Student record using dictionary\n'
        'student = {\n'
        '    "name": "Ayush",\n'
        '    "class": 12,\n'
        '    "marks": 92\n'
        '}\n\n'
        'print("Name:", student["name"])\n'
        'print("Marks:", student["marks"])\n\n'
        'for key, value in student.items():\n'
        '    print(key, "->", value)\n'
    ),
    "Function": (
        '# Defining and calling a function\n'
        'def area_of_rectangle(length, width):\n'
        '    return length * width\n\n'
        'l = float(input("Length: "))\n'
        'w = float(input("Width: "))\n'
        'print("Area =", area_of_rectangle(l, w))\n'
    ),
    "File Read/Write": (
        '# Write to a file, then read it back\n'
        'with open("notes.txt", "w") as f:\n'
        '    f.write("Python is fun!\\n")\n'
        '    f.write("I am learning files.\\n")\n\n'
        'print("File written. Now reading:")\n'
        'with open("notes.txt", "r") as f:\n'
        '    print(f.read())\n'
    ),
    "Loop with Error (try AI)": (
        '# This code has a bug on purpose!\n'
        '# Run it, see the red line, then click AI Analyze\n'
        'numbers = [1, 2, 3]\n'
        'for i in range(5):\n'
        '    print(numbers[i])   # IndexError will happen\n'
    ),
}
