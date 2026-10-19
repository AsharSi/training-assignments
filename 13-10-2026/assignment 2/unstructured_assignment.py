with open('airport_operations_report.txt', 'r') as f:
    text = f.read()

lines = text.splitlines()

total_words = len(text.split())
total_lines = len(lines)
total_chars = len(text)

print(total_words)
print(total_lines)
print(total_chars)

print(text.lower().count('flight'))
print(text.lower().count('runway'))
print(text.lower().count('operations'))
print(text.lower().count('reported'))

for line in lines:
    if 'runway' in line.lower():
        print(line)

for line in lines:
    if any(word in line.lower() for word in ['delay', 'delayed', 'delays']):
        print(line)

for line in lines:
    if 'reported' in line.lower():
        print(line)

for word in ['emergency', 'inspection', 'weather', 'passengers', 'maintenance']:
    print(word, word in text.lower())

word_dict = {
    "flight": text.lower().count('flight'),
    "runway": text.lower().count('runway'),
    "operations": text.lower().count('operations')
}
print(word_dict)

print(max(lines, key=len))

filtered_lines = [line for line in lines if any(w in line.lower() for w in ['delay', 'delayed', 'delays', 'weather'])]
with open('filtered_airport_report.txt', 'w') as f:
    f.write('\n'.join(filtered_lines))