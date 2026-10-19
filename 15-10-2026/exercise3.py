import pymupdf
import pytesseract
from PIL import Image

doc = pymupdf.open("EY_Scanned_PDF_OCR_Practice.pdf")

cnt = 1
for page in doc:
    pix = page.get_pixmap()

    pix.save(f"page{cnt}.png")
    cnt += 1

image = Image.open("page1.png")

text = pytesseract.image_to_string(image)

print(text)

if "Forklift FL-17" in text:
    print("Detected Forklift FL-17")
else:
    print("Not Detected Forklift FL-17")

if 'injuries' in text:
    print("Detected Injuries")
else:
    print("Not Detected Injuries")

lines = text.split("\n")

for line in lines:
    if "inspection" in line:
        print(line)

with open('ocr_result.txt', 'w') as f:
    f.write(text)

print("Count of inspection: ", text.lower().count("inspection"))

for line in lines:
    if "Loading Bay" in line:
        print(line)