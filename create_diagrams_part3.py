import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import numpy as np

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# ============================================================
# DIAGRAM 10: Class Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')
ax.set_facecolor('#FFFFFF')

ax.text(8, 11.5, 'Figure 3.8.1 Class Diagram', ha='center', fontsize=12, fontweight='bold')

def draw_class_box(ax, x, y, width, height, class_name, attributes, methods):
    # Main box
    rect = Rectangle((x, y), width, height, facecolor='#F8F8F8', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    
    # Class name with icon
    ax.text(x + 0.3, y + height - 0.3, 'C', ha='center', va='center', fontsize=8, 
            fontweight='bold', bbox=dict(boxstyle='circle', facecolor='#D8D8E8', edgecolor='black'))
    ax.text(x + width/2 + 0.3, y + height - 0.3, class_name, ha='center', va='center',
            fontsize=10, fontweight='bold')
    
    # Separator
    ax.plot([x, x + width], [y + height - 0.5, y + height - 0.5], 'k-', linewidth=1)
    
    # Attributes
    attr_y = y + height - 0.7
    for attr in attributes:
        ax.text(x + 0.2, attr_y, attr, ha='left', va='center', fontsize=8)
        attr_y -= 0.25
    
    # Separator
    ax.plot([x, x + width], [attr_y + 0.1, attr_y + 0.1], 'k-', linewidth=1)
    
    # Methods
    method_y = attr_y - 0.1
    for method in methods:
        ax.text(x + 0.2, method_y, method, ha='left', va='center', fontsize=8)
        method_y -= 0.25

# Draw classes
draw_class_box(ax, 0.5, 7, 3, 3.5, 'User', 
               ['- userId: Integer', '+ username: String', '+ passwordHash: String', 
                '+ email: String', '+ role: Enum {GUEST, MEMBER, TRAINER, ADMIN}',
                '+ lastLogin: DateTime'],
               ['+ login(credentials): Boolean', '+ logout(): Void', 
                '+ updateProfile(data): Boolean'])

draw_class_box(ax, 4, 7, 3, 3.5, 'UserProfile',
               ['- profileId: Integer', '+ user: User (1-to-1)', '+ role: String', 
                '+ gender: String', '+ category: Category (FK)',
                '+ medicalInfo: String', '+ image: Blob'],
               ['+ isTrainer(): Boolean', '+ isRegistrar(): Boolean',
                '+ __str__(): String'])

draw_class_box(ax, 7.5, 7, 3, 3.5, 'Names',
               ['- memberId: Integer', '+ fullName: String', '+ email: String',
                '+ phoneNumber: String', '+ role: String', '+ gender: String',
                '+ trainer: User (FK)', '+ category: Category (FK)'],
               ['+ __str__(): String', '+ getTrainees(): List',
                '+ getSessions(): List'])

draw_class_box(ax, 11, 7, 3, 3.5, 'Category',
               ['- categoryId: Integer', '+ name: String', '+ description: String'],
               ['+ __str__(): String', '+ getMembers(): List',
                '+ getTrainers(): List'])

draw_class_box(ax, 0.5, 2.5, 3, 3.5, 'TrainingSession',
               ['- sessionId: Integer', '+ title: String', '+ description: String',
                '+ sessionDate: DateTime', '+ durationMinutes: Integer',
                '+ maxTrainees: Integer', '+ trainer: Names (FK)'],
               ['+ isFull(): Boolean', '+ slotsLeft(): Integer',
                '+ register(trainee): Void'])

draw_class_box(ax, 4, 2.5, 3, 3.5, 'AttendanceLog',
               ['- logId: Integer', '+ member: Names (FK)', '+ session: TrainingSession (FK)',
                '+ checkedInBy: User (FK)', '+ checkIn: DateTime',
                '+ checkOut: DateTime', '+ notes: String'],
               ['+ checkIn(): Void', '+ checkOut(): Void',
                '+ duration(): Integer'])

draw_class_box(ax, 7.5, 2.5, 3, 3.5, 'TrainingPlan',
               ['- planId: Integer', '+ trainee: Names (FK)', '+ trainer: Names (FK)',
                '+ splitType: String', '+ startDate: Date', '+ endDate: Date',
                '+ isActive: Boolean'],
               ['+ splitDays(): List', '+ getExercises(): List',
                '+ __str__(): String'])

draw_class_box(ax, 11, 2.5, 3, 3.5, 'MembershipPayment',
               ['- paymentId: Integer', '+ user: User (FK)', '+ amount: Decimal',
                '+ paymentDate: Date', '+ paymentMethod: String',
                '+ isVerified: Boolean', '+ subscriptionEnd: Date'],
               ['+ verify(): Boolean', '+ getReceipt(): String',
                '+ isActive(): Boolean'])

# Draw relationships
relationships = [
    (2, 7, 5.5, 7, '1-to-1', '0..1'),  # User - UserProfile
    (5.5, 7, 9, 7, 'FK', '0..*'),  # UserProfile - Names
    (9, 7, 12.5, 7, 'FK', '0..*'),  # Names - Category
    (2, 6, 2, 6, '', ''),  # User - TrainingSession (via trainer)
    (9, 6, 2, 6, 'FK', '0..*'),  # TrainingSession - User
    (9, 6, 5.5, 6, 'FK', '0..*'),  # AttendanceLog - Names
    (9, 6, 9, 6, 'FK', '0..*'),  # TrainingPlan - Names
    (12.5, 6, 12.5, 6, 'FK', '0..*'),  # MembershipPayment - User
]

for x1, y1, x2, y2, label1, label2 in relationships:
    if x1 != x2 or y1 != y2:
        ax.plot([x1, x2], [y1, y2], 'k-', linewidth=1)
        if label1:
            ax.text((x1 + x2)/2 - 0.3, (y1 + y2)/2 + 0.15, label1, fontsize=7, ha='center')
        if label2:
            ax.text((x1 + x2)/2 + 0.3, (y1 + y2)/2 + 0.15, label2, fontsize=7, ha='center')

plt.tight_layout()
plt.savefig('diagrams_new/10_class_diagram.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Class Diagram")

# ============================================================
# DIAGRAM 11: Component Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor('#FFFFFF')

ax.text(7, 9.5, 'Figure 4.3.2.1 Component Diagram', ha='center', fontsize=12, fontweight='bold')

def draw_component_box(ax, x, y, width, height, name, items):
    # Main box
    rect = Rectangle((x, y), width, height, facecolor='#F8F8F8', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    
    # Component icon (two small rectangles)
    icon1 = Rectangle((x + 0.2, y + height - 0.5), 0.3, 0.2, facecolor='#D8D8E8', edgecolor='black', linewidth=1)
    icon2 = Rectangle((x + 0.2, y + height - 0.8), 0.3, 0.2, facecolor='#D8D8E8', edgecolor='black', linewidth=1)
    ax.add_patch(icon1)
    ax.add_patch(icon2)
    
    # Name
    ax.text(x + width/2 + 0.3, y + height - 0.3, name, ha='center', va='center',
            fontsize=10, fontweight='bold')
    
    # Items
    item_y = y + height - 0.6
    for item in items:
        ax.text(x + 0.3, item_y, f'• {item}', ha='left', va='center', fontsize=8)
        item_y -= 0.25

# Components
components = [
    (1, 6, 3, 2.5, 'Frontend', ['HTML Templates', 'Bootstrap CSS', 'JavaScript']),
    (5, 6, 3, 2.5, 'Django Backend', ['Views', 'Models', 'Forms', 'URLs']),
    (9, 6, 3, 2.5, 'Database', ['SQLite/PostgreSQL', 'Data Storage']),
    (1, 2.5, 3, 2.5, 'External APIs', ['Gemini AI', 'Chapa Payment', 'Telegram Bot']),
    (5, 2.5, 3, 2.5, 'File Storage', ['Cloudinary', 'Media Files', 'QR Codes']),
    (9, 2.5, 3, 2.5, 'Authentication', ['Django Auth', 'Sessions', 'CSRF']),
]

for x, y, w, h, name, items in components:
    draw_component_box(ax, x, y, w, h, name, items)

# Connections (dashed arrows)
connections = [
    (4, 7.25, 5, 7.25),  # Frontend - Backend
    (8, 7.25, 9, 7.25),  # Backend - Database
    (2.5, 6, 2.5, 5),    # Frontend - External APIs
    (6.5, 6, 6.5, 5),    # Backend - File Storage
    (10.5, 6, 10.5, 5),  # Database - Authentication
]

for x1, y1, x2, y2 in connections:
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5, linestyle='dashed'))

plt.tight_layout()
plt.savefig('diagrams_new/11_component_diagram.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Component Diagram")

# ============================================================
# DIAGRAM 12: Deployment Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor('#FFFFFF')

ax.text(7, 9.5, 'Figure 4.3.3.1 Deployment Diagram', ha='center', fontsize=12, fontweight='bold')

def draw_3d_box(ax, x, y, width, height, name, items):
    # 3D effect - back face
    rect_back = Rectangle((x + 0.15, y + 0.15), width, height, 
                          facecolor='#E0E0E0', edgecolor='black', linewidth=1)
    ax.add_patch(rect_back)
    
    # Front face
    rect = Rectangle((x, y), width, height, facecolor='#F8F8F8', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    
    # Name
    ax.text(x + width/2, y + height - 0.3, name, ha='center', va='center',
            fontsize=10, fontweight='bold')
    
    # Items
    item_y = y + height - 0.6
    for item in items:
        ax.text(x + 0.2, item_y, f'• {item}', ha='left', va='center', fontsize=8)
        item_y -= 0.25

# Nodes
nodes = [
    (1, 5, 3.5, 3, 'Client Device', ['Web Browser', 'Mobile Browser', 'QR Scanner']),
    (5.5, 5, 3.5, 3, 'Application Server', ['Django App', 'Gunicorn', 'Python Runtime']),
    (10, 5, 3.5, 3, 'Database Server', ['PostgreSQL', 'Data Storage']),
]

for x, y, w, h, name, items in nodes:
    draw_3d_box(ax, x, y, w, h, name, items)

# Connections
ax.annotate('', xy=(5.5, 6.5), xytext=(4.5, 6.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5, linestyle='dashed'))
ax.text(5, 6.7, 'HTTP/HTTPS', fontsize=8, ha='center')

ax.annotate('', xy=(10, 6.5), xytext=(9, 6.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5, linestyle='dashed'))
ax.text(9.5, 6.7, 'SQL', fontsize=8, ha='center')

# External services
ax.text(7, 2, 'External Services:', ha='center', fontsize=10, fontweight='bold')
services = ['Google Gemini API', 'Chapa Payment Gateway', 'Telegram Bot API', 'Cloudinary Storage']
for i, service in enumerate(services):
    ax.text(2 + i * 3, 1.5, f'• {service}', fontsize=8)

plt.tight_layout()
plt.savefig('diagrams_new/12_deployment_diagram.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Deployment Diagram")

# ============================================================
# DIAGRAM 13: Detailed Class Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(18, 14))
ax.set_xlim(0, 18)
ax.set_ylim(0, 14)
ax.axis('off')
ax.set_facecolor('#FFFFFF')

ax.text(9, 13.5, 'Figure 4.3.4 Detailed Class Diagram', ha='center', fontsize=12, fontweight='bold')

# More detailed classes
detailed_classes = [
    (0.5, 9, 3.5, 4, 'User', [
        '- userId: Integer',
        '+ username: String',
        '+ passwordHash: String',
        '+ email: String',
        '+ firstName: String',
        '+ lastName: String',
        '+ isSuperuser: Boolean',
        '+ isStaff: Boolean',
        '+ isActive: Boolean',
        '+ dateJoined: DateTime'
    ], [
        '+ login(credentials): Boolean',
        '+ logout(): Void',
        '+ changePassword(): Void',
        '+ getFullName(): String',
        '+ checkPassword(raw): Boolean'
    ]),
    
    (4.5, 9, 3.5, 4, 'UserProfile', [
        '- profileId: Integer',
        '+ user: User (1-to-1)',
        '+ role: String',
        '+ gender: String',
        '+ category: Category (FK)',
        '+ medicalInfo: String',
        '+ image: ImageField',
        '+ createdAt: DateTime'
    ], [
        '+ isTrainer(): Boolean',
        '+ isRegistrar(): Boolean',
        '+ __str__(): String'
    ]),
    
    (8.5, 9, 3.5, 4, 'Names', [
        '- memberId: Integer',
        '+ name: String',
        '+ email: String',
        '+ phoneNumber: String',
        '+ detail: String',
        '+ date: DateTime',
        '+ image: ImageField',
        '+ role: String',
        '+ gender: String',
        '+ trainer: User (FK)',
        '+ category: Category (FK)'
    ], [
        '+ __str__(): String',
        '+ getTrainees(): List',
        '+ getSessions(): List'
    ]),
    
    (12.5, 9, 3.5, 4, 'Category', [
        '- categoryId: Integer',
        '+ name: String',
        '+ description: String'
    ], [
        '+ __str__(): String',
        '+ getMembers(): List',
        '+ getTrainers(): List'
    ]),
    
    (0.5, 4, 3.5, 4, 'TrainingSession', [
        '- sessionId: Integer',
        '+ title: String',
        '+ description: String',
        '+ sessionDate: DateTime',
        '+ durationMinutes: Integer',
        '+ space: TrainingSpace (FK)',
        '+ trainer: Names (FK)',
        '+ maxTrainees: Integer',
        '+ registeredTrainees: M2M',
        '+ createdAt: DateTime'
    ], [
        '+ isFull(): Boolean',
        '+ slotsLeft(): Integer',
        '+ endTime(): DateTime',
        '+ isPast(): Boolean',
        '+ register(trainee): Void'
    ]),
    
    (4.5, 4, 3.5, 4, 'AttendanceLog', [
        '- logId: Integer',
        '+ member: Names (FK)',
        '+ session: TrainingSession (FK)',
        '+ checkedInBy: User (FK)',
        '+ checkIn: DateTime',
        '+ checkOut: DateTime',
        '+ checkedOutBy: User (FK)',
        '+ notes: String'
    ], [
        '+ checkIn(): Void',
        '+ checkOut(): Void',
        '+ duration(): Integer',
        '+ __str__(): String'
    ]),
    
    (8.5, 4, 3.5, 4, 'TrainingPlan', [
        '- planId: Integer',
        '+ trainee: Names (FK)',
        '+ trainer: Names (FK)',
        '+ splitType: String',
        '+ startDate: Date',
        '+ endDate: Date',
        '+ notes: String',
        '+ isActive: Boolean',
        '+ createdAt: DateTime',
        '+ updatedAt: DateTime'
    ], [
        '+ splitDays(): List',
        '+ getExercises(): List',
        '+ __str__(): String'
    ]),
    
    (12.5, 4, 3.5, 4, 'MembershipPayment', [
        '- paymentId: Integer',
        '+ user: User (FK)',
        '+ amount: Decimal',
        '+ paymentDate: Date',
        '+ entryDate: DateTime',
        '+ paymentMethod: String',
        '+ receiptNumber: String',
        '+ isVerified: Boolean',
        '+ subscriptionStart: Date',
        '+ subscriptionEnd: Date',
        '+ chapaTxRef: String'
    ], [
        '+ verify(): Boolean',
        '+ getReceipt(): String',
        '+ isActive(): Boolean',
        '+ __str__(): String'
    ]),
]

for x, y, w, h, name, attrs, methods in detailed_classes:
    draw_class_box(ax, x, y, w, h, name, attrs, methods)

plt.tight_layout()
plt.savefig('diagrams_new/13_detailed_class_diagram.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Detailed Class Diagram")

print("\n✓ All 13 diagrams created successfully in exact original style!")
print("Location: diagrams_new/ folder")
