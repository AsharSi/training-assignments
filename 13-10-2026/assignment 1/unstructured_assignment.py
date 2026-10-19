

with open('unstructured_data.txt') as file:
    data = file.read()

# print(data)

words = data.split()
lines = data.split('\n')

# print(len(words))

# print(len(lines))

# if 'maintenance' in words:
#     print("Yes, maintenance is in the word list")
# else:
#     print("No, maintenance is not in the word list")
#
# print(words.count('conveyor'))

# for line in lines:
#     if "team" in line:
#         print(line)

# for line in lines:
#     if "incident" in line:
#         print(line)

# for line in lines:
#     if "damage" in line:
#         print(line)

# with open('lowercase_report.txt', 'w') as file:
#     file.write(data.lower())

def find_wd(word):
    if word in words:
        print(word, "found")
    else:
        print(word, "not found")

find_wd("maintenance")
find_wd("injuries")
find_wd("inspection")
find_wd("replacement")
find_wd("operations")