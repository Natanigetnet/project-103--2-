import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import numpy as np

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# Create Activity Diagram 1 - Session Creation
fig, ax = plt.subplots(figsize=(10, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Title
ax.text(5, 11.5, 'Activity Diagram: Session Creation', ha='center', fontsize=12, fontweight='bold')

# Start node
start = Circle((5, 10.5), 0.2, facecolor='black', edgecolor='black')
ax.add_patch(start)

# Activities
activities = [
    (5, 9.5, 'Trainer logs in'),
    (5, 8.5, 'Navigate to Create Session'),
    (5, 7.5, 'Fill session details'),
    (5, 6.5, 'Select training space'),
    (5, 5.5, 'Set max trainees'),
    (5, 4.5, 'Submit session'),
]

for i, (x, y, label) in enumerate(activities):
    rect = FancyBboxPatch((x - 1, y - 0.3), 2, 0.6, boxstyle="round,pad=0.1",
                          facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x, y, label, ha='center', va='center', fontsize=9)
    
    # Connect to next
    if i < len(activities) - 1:
        ax.annotate('', xy=(x, activities[i+1][1] + 0.3), xytext=(x, y - 0.3),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Connect start to first activity
ax.annotate('', xy=(5, 9.8), xytext=(5, 10.3),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Decision node
decision = Circle((5, 3.5), 0.3, facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(decision)
ax.annotate('', xy=(5, 3.8), xytext=(5, 4.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Yes path
ax.annotate('', xy=(3, 3.5), xytext=(4.7, 3.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(3.5, 3.7, 'Yes', fontsize=8)

rect2 = FancyBboxPatch((1.5, 2.2), 3, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect2)
ax.text(3, 2.5, 'Notify trainees', ha='center', va='center', fontsize=9)

# No path
ax.annotate('', xy=(7, 3.5), xytext=(5.3, 3.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(6.5, 3.7, 'No', fontsize=8)

rect3 = FancyBboxPatch((5.5, 2.2), 3, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect3)
ax.text(7, 2.5, 'Show error', ha='center', va='center', fontsize=9)

# End node
end = Circle((5, 1), 0.2, facecolor='black', edgecolor='black', linewidth=2)
ax.add_patch(end)
end2 = Circle((5, 1), 0.15, facecolor='white', edgecolor='black', linewidth=2)
ax.add_patch(end2)

# Connect to end
ax.annotate('', xy=(3, 1.2), xytext=(3, 2.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.annotate('', xy=(5, 1.2), xytext=(7, 2.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.annotate('', xy=(5, 1.2), xytext=(3, 1.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

plt.tight_layout()
plt.savefig('diagrams/08_activity_diagram_1.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Activity Diagram 1")

# Create Activity Diagram 2 - Member Check-in
fig, ax = plt.subplots(figsize=(10, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

ax.text(5, 11.5, 'Activity Diagram: Member Check-in', ha='center', fontsize=12, fontweight='bold')

start = Circle((5, 10.5), 0.2, facecolor='black', edgecolor='black')
ax.add_patch(start)

activities = [
    (5, 9.5, 'Member arrives at gym'),
    (5, 8.5, 'Show QR code'),
    (5, 7.5, 'Registrar scans QR'),
    (5, 6.5, 'System validates member'),
]

for i, (x, y, label) in enumerate(activities):
    rect = FancyBboxPatch((x - 1, y - 0.3), 2, 0.6, boxstyle="round,pad=0.1",
                          facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x, y, label, ha='center', va='center', fontsize=9)
    
    if i < len(activities) - 1:
        ax.annotate('', xy=(x, activities[i+1][1] + 0.3), xytext=(x, y - 0.3),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

ax.annotate('', xy=(5, 9.8), xytext=(5, 10.3),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Decision - membership active?
decision = Circle((5, 5.5), 0.3, facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(decision)
ax.annotate('', xy=(5, 5.8), xytext=(5, 6.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Yes - check in
ax.annotate('', xy=(3, 5.5), xytext=(4.7, 5.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(3.5, 5.7, 'Active', fontsize=8)

rect2 = FancyBboxPatch((1.5, 4.2), 3, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect2)
ax.text(3, 4.5, 'Create attendance log', ha='center', va='center', fontsize=9)

# No - expired
ax.annotate('', xy=(7, 5.5), xytext=(5.3, 5.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(6.5, 5.7, 'Expired', fontsize=8)

rect3 = FancyBboxPatch((5.5, 4.2), 3, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect3)
ax.text(7, 4.5, 'Show renewal prompt', ha='center', va='center', fontsize=9)

# Decision - has open session?
decision2 = Circle((3, 3.2), 0.3, facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(decision2)
ax.annotate('', xy=(3, 3.5), xytext=(3, 4.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# No - check in
ax.annotate('', xy=(1.5, 3.2), xytext=(2.7, 3.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(1.8, 3.4, 'No', fontsize=8)

rect4 = FancyBboxPatch((0.3, 2), 2.4, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect4)
ax.text(1.5, 2.3, 'Check in member', ha='center', va='center', fontsize=9)

# Yes - check out
ax.annotate('', xy=(4.5, 3.2), xytext=(3.3, 3.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(4.2, 3.4, 'Yes', fontsize=8)

rect5 = FancyBboxPatch((3.3, 2), 2.4, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect5)
ax.text(4.5, 2.3, 'Check out member', ha='center', va='center', fontsize=9)

# End
end = Circle((5, 1), 0.2, facecolor='black', edgecolor='black', linewidth=2)
ax.add_patch(end)
end2 = Circle((5, 1), 0.15, facecolor='white', edgecolor='black', linewidth=2)
ax.add_patch(end2)

ax.annotate('', xy=(5, 1.2), xytext=(1.5, 2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.annotate('', xy=(5, 1.2), xytext=(7, 2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.annotate('', xy=(5, 1.2), xytext=(4.5, 2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

plt.tight_layout()
plt.savefig('diagrams/09_activity_diagram_2.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Activity Diagram 2")

# Create Class Diagram
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

ax.text(7, 9.5, 'Class Diagram', ha='center', fontsize=12, fontweight='bold')

# Helper function to draw class box
def draw_class_box(ax, x, y, width, height, class_name, attributes, methods):
    # Main box
    rect = Rectangle((x, y), width, height, facecolor='white', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    
    # Class name
    ax.text(x + width/2, y + height - 0.3, class_name, ha='center', va='center',
            fontsize=9, fontweight='bold')
    
    # Separator
    ax.plot([x, x + width], [y + height - 0.5, y + height - 0.5], 'k-', linewidth=1)
    
    # Attributes
    attr_y = y + height - 0.7
    for attr in attributes:
        ax.text(x + 0.1, attr_y, attr, ha='left', va='center', fontsize=7)
        attr_y -= 0.2
    
    # Separator
    ax.plot([x, x + width], [attr_y + 0.1, attr_y + 0.1], 'k-', linewidth=1)
    
    # Methods
    method_y = attr_y - 0.1
    for method in methods:
        ax.text(x + 0.1, method_y, method, ha='left', va='center', fontsize=7)
        method_y -= 0.2

# Draw classes
draw_class_box(ax, 0.5, 6, 2.5, 3, 'User', 
               ['- username: str', '- email: str', '- password: str', '+ is_superuser: bool'],
               ['+ login()', '+ logout()', '+ change_password()'])

draw_class_box(ax, 3.5, 6, 2.5, 3, 'UserProfile',
               ['- role: str', '- gender: str', '- medical_info: str', '+ category: Category'],
               ['+ is_trainer()', '+ is_registrar()'])

draw_class_box(ax, 6.5, 6, 2.5, 3, 'Names',
               ['- name: str', '- email: str', '- role: str', '+ trainer: User', '+ category: Category'],
               ['+ __str__()', '+ get_trainees()'])

draw_class_box(ax, 9.5, 6, 2.5, 3, 'Category',
               ['- name: str', '- description: str'],
               ['+ __str__()', '+ get_members()'])

draw_class_box(ax, 0.5, 2, 2.5, 3, 'TrainingSession',
               ['- title: str', '- session_date: datetime', '- max_trainees: int', '+ trainer: Names'],
               ['+ is_full()', '+ slots_left()', '+ register()'])

draw_class_box(ax, 3.5, 2, 2.5, 3, 'AttendanceLog',
               ['- check_in: datetime', '- check_out: datetime', '+ member: Names', '+ checked_in_by: User'],
               ['+ check_in()', '+ check_out()'])

draw_class_box(ax, 6.5, 2, 2.5, 3, 'TrainingPlan',
               ['- split_type: str', '- start_date: date', '- end_date: date', '+ is_active: bool'],
               ['+ split_days()', '+ get_exercises()'])

draw_class_box(ax, 9.5, 2, 2.5, 3, 'MembershipPayment',
               ['- amount: decimal', '- payment_date: date', '- payment_method: str', '+ is_verified: bool'],
               ['+ verify()', '+ get_receipt()'])

# Draw relationships
relationships = [
    (1.75, 6, 4.75, 6, '1-to-1'),  # User - UserProfile
    (4.75, 6, 7.75, 6, 'FK'),  # UserProfile - Names
    (7.75, 6, 10.75, 6, 'FK'),  # Names - Category
    (1.75, 5, 1.75, 5, ''),  # User - TrainingSession
    (7.75, 5, 1.75, 5, 'FK'),  # TrainingSession - User (trainer)
    (7.75, 5, 4.75, 5, 'FK'),  # AttendanceLog - Names
    (7.75, 5, 7.75, 5, 'FK'),  # TrainingPlan - Names
    (10.75, 5, 10.75, 5, 'FK'),  # MembershipPayment - User
]

for x1, y1, x2, y2, label in relationships:
    if x1 != x2 or y1 != y2:
        ax.plot([x1, x2], [y1, y2], 'k-', linewidth=1)
        if label:
            ax.text((x1 + x2)/2, (y1 + y2)/2 + 0.1, label, fontsize=7, ha='center')

plt.tight_layout()
plt.savefig('diagrams/10_class_diagram.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Class Diagram")

# Create Component Diagram
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

ax.text(6, 7.5, 'Component Diagram', ha='center', fontsize=12, fontweight='bold')

# Components
components = [
    (1, 5, 2.5, 2, 'Frontend', ['HTML Templates', 'Bootstrap CSS', 'JavaScript']),
    (4, 5, 2.5, 2, 'Django Backend', ['Views', 'Models', 'Forms']),
    (7, 5, 2.5, 2, 'Database', ['SQLite/PostgreSQL', 'Data Storage']),
    (1, 2, 2.5, 2, 'External APIs', ['Gemini AI', 'Chapa Payment', 'Telegram']),
    (4, 2, 2.5, 2, 'File Storage', ['Cloudinary', 'Media Files']),
    (7, 2, 2.5, 2, 'Authentication', ['Django Auth', 'Sessions']),
]

for x, y, w, h, name, items in components:
    rect = Rectangle((x, y), w, h, facecolor='#E8E8F0', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.3, name, ha='center', va='center', fontsize=9, fontweight='bold')
    
    item_y = y + h - 0.6
    for item in items:
        ax.text(x + 0.2, item_y, f'• {item}', ha='left', va='center', fontsize=7)
        item_y -= 0.25

# Connections
connections = [
    (3.5, 6, 4, 6),  # Frontend - Backend
    (6.5, 6, 7, 6),  # Backend - Database
    (2.25, 5, 2.25, 4),  # Frontend - External APIs
    (5.25, 5, 5.25, 4),  # Backend - File Storage
    (8.25, 5, 8.25, 4),  # Database - Authentication
]

for x1, y1, x2, y2 in connections:
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))

plt.tight_layout()
plt.savefig('diagrams/11_component_diagram.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Component Diagram")

# Create Deployment Diagram
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

ax.text(6, 7.5, 'Deployment Diagram', ha='center', fontsize=12, fontweight='bold')

# Nodes
nodes = [
    (1, 4, 3, 3, 'Client Device', ['Web Browser', 'Mobile Browser', 'QR Scanner']),
    (5, 4, 3, 3, 'Application Server', ['Django App', 'Gunicorn', 'Python Runtime']),
    (9, 4, 3, 3, 'Database Server', ['PostgreSQL', 'Data Storage']),
]

for x, y, w, h, name, items in nodes:
    # 3D box effect
    rect = Rectangle((x, y), w, h, facecolor='#E8E8F0', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    rect2 = Rectangle((x + 0.1, y + 0.1), w, h, facecolor='none', edgecolor='black', linewidth=1)
    ax.add_patch(rect2)
    
    ax.text(x + w/2, y + h - 0.3, name, ha='center', va='center', fontsize=9, fontweight='bold')
    
    item_y = y + h - 0.6
    for item in items:
        ax.text(x + 0.2, item_y, f'• {item}', ha='left', va='center', fontsize=7)
        item_y -= 0.25

# Connections
ax.annotate('', xy=(5, 5.5), xytext=(4, 5.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
ax.text(4.5, 5.7, 'HTTP/HTTPS', fontsize=8, ha='center')

ax.annotate('', xy=(9, 5.5), xytext=(8, 5.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
ax.text(8.5, 5.7, 'SQL', fontsize=8, ha='center')

# External services
ax.text(6, 1, 'External Services:', ha='center', fontsize=9, fontweight='bold')
services = ['Google Gemini API', 'Chapa Payment Gateway', 'Telegram Bot API', 'Cloudinary Storage']
for i, service in enumerate(services):
    ax.text(1.5 + i * 2.5, 0.5, f'• {service}', fontsize=7)

plt.tight_layout()
plt.savefig('diagrams/12_deployment_diagram.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Deployment Diagram")

# Create Detailed Class Diagram
fig, ax = plt.subplots(figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

ax.text(8, 11.5, 'Detailed Class Diagram', ha='center', fontsize=12, fontweight='bold')

# More detailed classes
detailed_classes = [
    (0.5, 8, 3, 3.5, 'User', [
        '- username: str',
        '- email: str',
        '- password: str',
        '- first_name: str',
        '- last_name: str',
        '- is_superuser: bool',
        '- is_staff: bool',
        '- is_active: bool',
        '- date_joined: datetime'
    ], [
        '+ login()',
        '+ logout()',
        '+ change_password()',
        '+ get_full_name()',
        '+ check_password()'
    ]),
    
    (4, 8, 3, 3.5, 'UserProfile', [
        '- user: User (1-to-1)',
        '- role: str',
        '- gender: str',
        '- category: Category (FK)',
        '- medical_info: str',
        '- image: ImageField',
        '- created_at: datetime'
    ], [
        '+ is_trainer()',
        '+ is_registrar()',
        '+ __str__()'
    ]),
    
    (7.5, 8, 3, 3.5, 'Names', [
        '- name: str',
        '- email: str',
        '- phone_number: str',
        '- detail: str',
        '- date: datetime',
        '- image: ImageField',
        '- role: str',
        '- gender: str',
        '- trainer: User (FK)',
        '- category: Category (FK)'
    ], [
        '+ __str__()',
        '+ get_trainees()',
        '+ get_sessions()'
    ]),
    
    (11, 8, 3, 3.5, 'Category', [
        '- name: str',
        '- description: str'
    ], [
        '+ __str__()',
        '+ get_members()',
        '+ get_trainers()'
    ]),
    
    (0.5, 3.5, 3, 3.5, 'TrainingSession', [
        '- title: str',
        '- description: str',
        '- session_date: datetime',
        '- duration_minutes: int',
        '- space: TrainingSpace (FK)',
        '- trainer: Names (FK)',
        '- max_trainees: int',
        '- registered_trainees: M2M',
        '- created_at: datetime'
    ], [
        '+ is_full()',
        '+ slots_left()',
        '+ end_time()',
        '+ is_past()',
        '+ register()'
    ]),
    
    (4, 3.5, 3, 3.5, 'AttendanceLog', [
        '- member: Names (FK)',
        '- session: TrainingSession (FK)',
        '- checked_in_by: User (FK)',
        '- check_in: datetime',
        '- check_out: datetime',
        '- checked_out_by: User (FK)',
        '- notes: str'
    ], [
        '+ check_in()',
        '+ check_out()',
        '+ duration()',
        '+ __str__()'
    ]),
    
    (7.5, 3.5, 3, 3.5, 'TrainingPlan', [
        '- trainee: Names (FK)',
        '- trainer: Names (FK)',
        '- split_type: str',
        '- start_date: date',
        '- end_date: date',
        '- notes: str',
        '- is_active: bool',
        '- created_at: datetime',
        '- updated_at: datetime'
    ], [
        '+ split_days()',
        '+ get_exercises()',
        '+ __str__()'
    ]),
    
    (11, 3.5, 3, 3.5, 'MembershipPayment', [
        '- user: User (FK)',
        '- amount: Decimal',
        '- payment_date: date',
        '- entry_date: datetime',
        '- payment_method: str',
        '- receipt_number: str',
        '- is_verified: bool',
        '- subscription_start: date',
        '- subscription_end: date',
        '- chapa_tx_ref: str'
    ], [
        '+ verify()',
        '+ get_receipt()',
        '+ is_active()',
        '+ __str__()'
    ]),
]

for x, y, w, h, name, attrs, methods in detailed_classes:
    draw_class_box(ax, x, y, w, h, name, attrs, methods)

plt.tight_layout()
plt.savefig('diagrams/13_detailed_class_diagram.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Detailed Class Diagram")

print("\n✓ All diagrams created successfully!")
print("Total: 13 diagrams in 'diagrams/' folder")
