from docx import Document
import os

# Step 1: Extract original images 1 and 2 from the original document
original_doc = Document(r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\Gym_Management_System_123.docx")

original_images = []
for rel in original_doc.part.rels.values():
    if "image" in rel.reltype:
        original_images.append(rel.target_part.blob)

print(f"Extracted {len(original_images)} original images")

# Save the first 2 original images
os.makedirs('original_images_backup', exist_ok=True)
with open('original_images_backup/image1_original.png', 'wb') as f:
    f.write(original_images[0])
with open('original_images_backup/image2_original.png', 'wb') as f:
    f.write(original_images[1])

print("Saved original images 1 and 2")

# Step 2: Open the current document and replace only images 1 and 2 with originals
current_doc = Document(r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\Gym_Management_System_Updated_Diagrams.docx")

image_rels = []
for rel in current_doc.part.rels.values():
    if "image" in rel.reltype:
        image_rels.append(rel)

print(f"Found {len(image_rels)} images in current document")

# Replace only the first 2 images with originals
for i in range(2):
    rel = image_rels[i]
    rel.target_part._blob = original_images[i]
    print(f"Replaced image {i+1} with original")

# Save
output_path = r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\Gym_Management_System_Final_v3.docx"
current_doc.save(output_path)

print(f"\nDocument saved to: {output_path}")
print("Images 1-2: Original diagrams from your document")
print("Images 3-14: New diagrams created for current system")
