from docx import Document
import os

doc = Document('Gym_Management_System_123.docx')
os.makedirs('extracted_images', exist_ok=True)

count = 0
for rel in doc.part.rels.values():
    if 'image' in rel.reltype:
        count += 1
        with open(f'extracted_images/image{count}.png', 'wb') as f:
            f.write(rel.target_part.blob)

print(f'Extracted {count} images to extracted_images folder')
