from docx import Document
from docx.shared import Inches
import os

# Open the updated document
doc = Document(r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\Gym_Management_System_Updated.docx")

# Map of diagram files to their positions in the document
# Based on the figure numbers in the original document
diagram_files = [
    '01_use_case_diagram.png',           # Figure 3.4.8
    '02_registration_sequence.png',      # Figure 3.5.1
    '03_login_sequence.png',             # Figure 3.5.2
    '04_session_booking_sequence.png',   # Figure 3.5.3
    '05_qr_attendance_sequence.png',     # Figure 3.5.4
    '06_ai_chat_sequence.png',           # Figure 3.5.5
    '07_member_management_sequence.png', # Figure 3.5.6
    '08_activity_diagram_1.png',         # Figure 3.7.1
    '09_activity_diagram_2.png',         # Figure 3.7.2
    '10_class_diagram.png',              # Figure 3.8.1
    '11_component_diagram.png',          # Figure 4.3.2.1
    '12_deployment_diagram.png',         # Figure 4.3.3.1
    '13_detailed_class_diagram.png',     # Figure 4.3.4
]

diagrams_folder = r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\diagrams"

# Find and replace images in the document
# We need to find the image placeholders and replace them
image_count = 0

for rel in doc.part.rels.values():
    if "image" in rel.reltype:
        image_count += 1
        if image_count <= len(diagram_files):
            # Get the new diagram file
            diagram_file = os.path.join(diagrams_folder, diagram_files[image_count - 1])
            
            if os.path.exists(diagram_file):
                # Replace the image data
                with open(diagram_file, 'rb') as f:
                    new_image_data = f.read()
                
                # Update the image part
                rel.target_part.blob = new_image_data
                print(f"Replaced image {image_count} with {diagram_files[image_count - 1]}")

# Save the document
output_path = r"C:\Users\natan\OneDrive\Nati's documents\project 103 (2)\Gym_Management_System_Final.docx"
doc.save(output_path)

print(f"\nDocument saved to: {output_path}")
print(f"Replaced {min(image_count, len(diagram_files))} diagrams")
