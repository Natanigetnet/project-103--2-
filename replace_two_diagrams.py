from docx import Document
import os

# Open the document
doc = Document(r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\Gym_Management_System_Final_v2.docx")

# Only replace the first 2 images (use case and registration sequence)
diagram_files = [
    '01_use_case_diagram.png',
    '02_registration_sequence.png',
]

diagrams_folder = r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\diagrams_new"

# Collect image relationships
image_rels = []
for rel in doc.part.rels.values():
    if "image" in rel.reltype:
        image_rels.append(rel)

print(f"Found {len(image_rels)} images in document")

# Replace only the first 2 images
for i in range(min(2, len(image_rels))):
    rel = image_rels[i]
    diagram_file = os.path.join(diagrams_folder, diagram_files[i])
    
    if os.path.exists(diagram_file):
        with open(diagram_file, 'rb') as f:
            new_image_data = f.read()
        
        rel.target_part._blob = new_image_data
        print(f"Replaced image {i+1}: {diagram_files[i]}")

# Save with new name
output_path = r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\Gym_Management_System_Updated_Diagrams.docx"
doc.save(output_path)

print(f"\nDocument saved to: {output_path}")
print("Only use case and registration sequence diagrams were updated")
