import pymupdf

doc = pymupdf.open("EY_Digital_PDF_Practice.pdf")

print("Total Pages ", doc.page_count)

cnt = 1

text = ""

for page in doc:

    print ("\n\nPage ", cnt)
    cnt += 1

    text += page.get_text()
    print(page.get_text())

words = text.split()

print(words)

if "Maintenance" in words:
    print("Maintenance exists")
else:
    print("Maintenance does not exist")

print("V303 count is: ", words.count("V303"))

print(doc[1].get_text())

with open("digital_pdf_text.txt", "w") as f:
    f.write(text)

