from pypdf import PdfReader

reader = PdfReader("EY_Digital_PDF_Practice.pdf")
print("Pages:", len(reader.pages))

cnt = 1

text = ""

for page in reader.pages:
    print("\n\nPage ", cnt)
    cnt += 1
    text += page.extract_text()
    print(page.extract_text())

if "NorthStar Maintenance" in text:
    print("NorthStar Maintenance is in PDF")
else:
    print("NorthStar Maintenance is not in PDF")

words = text.split()

print("Count of vendor: ", text.lower().count("vendor"))

with open('pypdf_output.txt', 'w') as f:
    f.write(text)