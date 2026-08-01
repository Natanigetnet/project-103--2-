import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import numpy as np

# Set up the style to match the original diagrams
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# Color scheme matching the original
ACTOR_COLOR = '#E8E8F0'
BOUNDARY_COLOR = '#E8E8F0'
CONTROL_COLOR = '#E8E8F0'
ENTITY_COLOR = '#E8E8F0'
ARROW_COLOR = '#000000'
BG_COLOR = '#FFFFFF'

def draw_actor(ax, x, y, label, size=0.3):
    """Draw a stick figure actor"""
    # Head
    circle = Circle((x, y + size*1.5), size*0.5, facecolor=ACTOR_COLOR, edgecolor='black', linewidth=1.5)
    ax.add_patch(circle)
    # Body
    ax.plot([x, x], [y + size, y], 'k-', linewidth=1.5)
    # Arms
    ax.plot([x - size*0.5, x + size*0.5], [y + size*0.7, y + size*0.7], 'k-', linewidth=1.5)
    # Legs
    ax.plot([x, x - size*0.4], [y, y - size*0.6], 'k-', linewidth=1.5)
    ax.plot([x, x + size*0.4], [y, y - size*0.6], 'k-', linewidth=1.5)
    # Label
    ax.text(x, y - size, label, ha='center', va='top', fontsize=9, fontweight='bold')

def draw_boundary(ax, x, y, label, size=0.25):
    """Draw a boundary object (circle with line)"""
    circle = Circle((x, y), size, facecolor=BOUNDARY_COLOR, edgecolor='black', linewidth=1.5)
    ax.add_patch(circle)
    ax.plot([x - size*0.7, x + size*0.7], [y, y], 'k-', linewidth=1.5)
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=9)

def draw_control(ax, x, y, label, size=0.25):
    """Draw a control object (circle with arrow)"""
    circle = Circle((x, y), size, facecolor=CONTROL_COLOR, edgecolor='black', linewidth=1.5)
    ax.add_patch(circle)
    # Arrow inside
    ax.annotate('', xy=(x + size*0.5, y + size*0.3), xytext=(x - size*0.3, y - size*0.3),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=9)

def draw_entity(ax, x, y, label, size=0.25):
    """Draw an entity object (circle)"""
    circle = Circle((x, y), size, facecolor=ENTITY_COLOR, edgecolor='black', linewidth=1.5)
    ax.add_patch(circle)
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=9)

def draw_lifeline(ax, x, y_top, y_bottom):
    """Draw a dashed lifeline"""
    ax.plot([x, x], [y_top, y_bottom], 'k--', linewidth=0.8, alpha=0.5)

def draw_message(ax, x1, y1, x2, y2, label, solid=True):
    """Draw a message arrow"""
    if solid:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
    else:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.2, linestyle='dashed'))
    # Label
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    ax.text(mid_x, mid_y + 0.1, label, ha='center', va='bottom', fontsize=8)

def draw_activation(ax, x, y_top, y_bottom, width=0.15):
    """Draw an activation box"""
    rect = Rectangle((x - width/2, y_bottom), width, y_top - y_bottom,
                     facecolor='white', edgecolor='black', linewidth=1)
    ax.add_patch(rect)

def draw_alt_frame(ax, x, y, width, height, conditions):
    """Draw an alt fragment frame"""
    rect = Rectangle((x, y), width, height, facecolor='none', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    # Label
    ax.text(x + 0.1, y + height - 0.2, 'alt', fontsize=9, fontweight='bold')
    # Conditions
    for i, cond in enumerate(conditions):
        cond_y = y + height - 0.5 - i * 0.8
        ax.plot([x, x + width], [cond_y, cond_y], 'k--', linewidth=0.8)
        ax.text(x + 0.2, cond_y + 0.1, f'[{cond}]', fontsize=8, fontweight='bold')

# Create Use Case Diagram
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# System boundary
rect = FancyBboxPatch((3, 1), 8, 8, boxstyle="round,pad=0.1", facecolor='none', edgecolor='black', linewidth=2)
ax.add_patch(rect)
ax.text(7, 9.5, 'Gym Management System', ha='center', fontsize=12, fontweight='bold')

# Actors
draw_actor(ax, 1, 7, 'Admin', 0.4)
draw_actor(ax, 1, 4, 'Trainer', 0.4)
draw_actor(ax, 1, 1, 'Trainee', 0.4)
draw_actor(ax, 13, 7, 'Registrar', 0.4)

# Use cases (ellipses)
use_cases = [
    (5, 8, 'Manage Users'),
    (7, 8, 'View Reports'),
    (9, 8, 'Configure System'),
    (5, 6.5, 'Create Sessions'),
    (7, 6.5, 'Manage Trainees'),
    (9, 6.5, 'View Schedule'),
    (5, 5, 'Book Session'),
    (7, 5, 'View Training Plan'),
    (9, 5, 'Track BMI'),
    (5, 3.5, 'Scan QR Code'),
    (7, 3.5, 'Register Member'),
    (9, 3.5, 'View Attendance'),
    (5, 2, 'Chat with AI'),
    (7, 2, 'View Feed'),
    (9, 2, 'Make Payment'),
]

for x, y, label in use_cases:
    ellipse = mpatches.Ellipse((x, y), 1.2, 0.5, facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
    ax.add_patch(ellipse)
    ax.text(x, y, label, ha='center', va='center', fontsize=8)

# Connect actors to use cases
connections = [
    (1, 7, 5, 8), (1, 7, 7, 8), (1, 7, 9, 8),
    (1, 4, 5, 6.5), (1, 4, 7, 6.5), (1, 4, 9, 6.5),
    (1, 1, 5, 5), (1, 1, 7, 5), (1, 1, 9, 5),
    (1, 1, 5, 2), (1, 1, 7, 2), (1, 1, 9, 2),
    (13, 7, 5, 3.5), (13, 7, 7, 3.5), (13, 7, 9, 3.5),
]

for x1, y1, x2, y2 in connections:
    ax.plot([x1 + 0.4, x2 - 0.6], [y1, y2], 'k-', linewidth=0.8)

plt.tight_layout()
plt.savefig('diagrams/01_use_case_diagram.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Use Case Diagram")

# Create Registration Sequence Diagram
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

# Participants
participants = [
    (1.5, 'Guest', 'actor'),
    (4, 'Signup Page', 'boundary'),
    (6.5, 'Auth Controller', 'control'),
    (9, 'User Model', 'entity'),
    (11, 'Email Service', 'entity'),
]

for x, label, ptype in participants:
    if ptype == 'actor':
        draw_actor(ax, x, 7.5, label, 0.3)
    elif ptype == 'boundary':
        draw_boundary(ax, x, 7.5, label, 0.25)
    elif ptype == 'control':
        draw_control(ax, x, 7.5, label, 0.25)
    else:
        draw_entity(ax, x, 7.5, label, 0.25)
    draw_lifeline(ax, x, 7, 0.5)

# Messages
messages = [
    (1.5, 6.8, 4, 6.8, '1. Select Register', True),
    (4, 6.5, 6.5, 6.5, '1.1 Submit form', True),
    (6.5, 6.2, 9, 6.2, '2. Create user', True),
    (9, 5.9, 6.5, 5.9, '2.1 User created', False),
    (6.5, 5.6, 11, 5.6, '3. Send welcome email', True),
    (11, 5.3, 6.5, 5.3, '3.1 Email sent', False),
    (6.5, 5.0, 4, 5.0, '4. Show success', False),
    (4, 4.7, 1.5, 4.7, '4.1 Redirect to home', False),
]

for x1, y1, x2, y2, label, solid in messages:
    draw_message(ax, x1, y1, x2, y2, label, solid)

plt.tight_layout()
plt.savefig('diagrams/02_registration_sequence.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Registration Sequence Diagram")

# Create Login Sequence Diagram
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

participants = [
    (1.5, 'User', 'actor'),
    (4, 'Login Page', 'boundary'),
    (6.5, 'Auth Controller', 'control'),
    (9, 'User Model', 'entity'),
]

for x, label, ptype in participants:
    if ptype == 'actor':
        draw_actor(ax, x, 7.5, label, 0.3)
    elif ptype == 'boundary':
        draw_boundary(ax, x, 7.5, label, 0.25)
    elif ptype == 'control':
        draw_control(ax, x, 7.5, label, 0.25)
    else:
        draw_entity(ax, x, 7.5, label, 0.25)
    draw_lifeline(ax, x, 7, 0.5)

messages = [
    (1.5, 6.8, 4, 6.8, '1. Enter credentials', True),
    (4, 6.5, 6.5, 6.5, '1.1 Submit login', True),
    (6.5, 6.2, 9, 6.2, '2. Validate credentials', True),
    (9, 5.9, 6.5, 5.9, '2.1 User found', False),
    (6.5, 5.6, 9, 5.6, '3. Check password', True),
    (9, 5.3, 6.5, 5.3, '3.1 Password valid', False),
    (6.5, 5.0, 4, 5.0, '4. Create session', False),
    (4, 4.7, 1.5, 4.7, '4.1 Redirect to dashboard', False),
]

for x1, y1, x2, y2, label, solid in messages:
    draw_message(ax, x1, y1, x2, y2, label, solid)

plt.tight_layout()
plt.savefig('diagrams/03_login_sequence.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Login Sequence Diagram")

# Create Session Booking Sequence Diagram
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

participants = [
    (1.5, 'Trainee', 'actor'),
    (4, 'Session List', 'boundary'),
    (6.5, 'Booking Controller', 'control'),
    (9, 'TrainingSession', 'entity'),
]

for x, label, ptype in participants:
    if ptype == 'actor':
        draw_actor(ax, x, 7.5, label, 0.3)
    elif ptype == 'boundary':
        draw_boundary(ax, x, 7.5, label, 0.25)
    elif ptype == 'control':
        draw_control(ax, x, 7.5, label, 0.25)
    else:
        draw_entity(ax, x, 7.5, label, 0.25)
    draw_lifeline(ax, x, 7, 0.5)

messages = [
    (1.5, 6.8, 4, 6.8, '1. View available sessions', True),
    (4, 6.5, 6.5, 6.5, '1.1 Get sessions', True),
    (6.5, 6.2, 9, 6.2, '2. Query sessions', True),
    (9, 5.9, 6.5, 5.9, '2.1 Return list', False),
    (6.5, 5.6, 4, 5.6, '3. Display sessions', False),
    (4, 5.3, 1.5, 5.3, '3.1 Show to trainee', False),
    (1.5, 5.0, 4, 5.0, '4. Select session', True),
    (4, 4.7, 6.5, 4.7, '4.1 Register request', True),
    (6.5, 4.4, 9, 4.4, '5. Check availability', True),
    (9, 4.1, 6.5, 4.1, '5.1 Slots available', False),
    (6.5, 3.8, 9, 3.8, '6. Add trainee', True),
    (9, 3.5, 6.5, 3.5, '6.1 Registration saved', False),
    (6.5, 3.2, 4, 3.2, '7. Confirm booking', False),
    (4, 2.9, 1.5, 2.9, '7.1 Show confirmation', False),
]

for x1, y1, x2, y2, label, solid in messages:
    draw_message(ax, x1, y1, x2, y2, label, solid)

plt.tight_layout()
plt.savefig('diagrams/04_session_booking_sequence.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Session Booking Sequence Diagram")

# Create QR Attendance Sequence Diagram
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

participants = [
    (1.5, 'Trainee', 'actor'),
    (4, 'QR Scanner', 'boundary'),
    (6.5, 'Attendance Controller', 'control'),
    (9, 'AttendanceLog', 'entity'),
]

for x, label, ptype in participants:
    if ptype == 'actor':
        draw_actor(ax, x, 7.5, label, 0.3)
    elif ptype == 'boundary':
        draw_boundary(ax, x, 7.5, label, 0.25)
    elif ptype == 'control':
        draw_control(ax, x, 7.5, label, 0.25)
    else:
        draw_entity(ax, x, 7.5, label, 0.25)
    draw_lifeline(ax, x, 7, 0.5)

messages = [
    (1.5, 6.8, 4, 6.8, '1. Show QR code', True),
    (4, 6.5, 6.5, 6.5, '1.1 Scan QR', True),
    (6.5, 6.2, 9, 6.2, '2. Lookup member', True),
    (9, 5.9, 6.5, 5.9, '2.1 Member found', False),
    (6.5, 5.6, 9, 5.6, '3. Check membership', True),
    (9, 5.3, 6.5, 5.3, '3.1 Membership active', False),
    (6.5, 5.0, 9, 5.0, '4. Create attendance log', True),
    (9, 4.7, 6.5, 4.7, '4.1 Log created', False),
    (6.5, 4.4, 4, 4.4, '5. Show success', False),
    (4, 4.1, 1.5, 4.1, '5.1 Check-in confirmed', False),
]

for x1, y1, x2, y2, label, solid in messages:
    draw_message(ax, x1, y1, x2, y2, label, solid)

plt.tight_layout()
plt.savefig('diagrams/05_qr_attendance_sequence.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created QR Attendance Sequence Diagram")

# Create AI Chat Sequence Diagram
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

participants = [
    (1.5, 'User', 'actor'),
    (4, 'Chat Page', 'boundary'),
    (6.5, 'Chat Controller', 'control'),
    (9, 'Gemini API', 'entity'),
]

for x, label, ptype in participants:
    if ptype == 'actor':
        draw_actor(ax, x, 7.5, label, 0.3)
    elif ptype == 'boundary':
        draw_boundary(ax, x, 7.5, label, 0.25)
    elif ptype == 'control':
        draw_control(ax, x, 7.5, label, 0.25)
    else:
        draw_entity(ax, x, 7.5, label, 0.25)
    draw_lifeline(ax, x, 7, 0.5)

messages = [
    (1.5, 6.8, 4, 6.8, '1. Type question', True),
    (4, 6.5, 6.5, 6.5, '1.1 Send message', True),
    (6.5, 6.2, 9, 6.2, '2. Build context', True),
    (9, 5.9, 6.5, 5.9, '2.1 Context ready', False),
    (6.5, 5.6, 9, 5.6, '3. Call Gemini API', True),
    (9, 5.3, 6.5, 5.3, '3.1 AI response', False),
    (6.5, 5.0, 4, 5.0, '4. Return answer', False),
    (4, 4.7, 1.5, 4.7, '4.1 Display response', False),
]

for x1, y1, x2, y2, label, solid in messages:
    draw_message(ax, x1, y1, x2, y2, label, solid)

plt.tight_layout()
plt.savefig('diagrams/06_ai_chat_sequence.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created AI Chat Sequence Diagram")

# Create Member Management Sequence Diagram
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

participants = [
    (1.5, 'Admin', 'actor'),
    (4, 'Member List', 'boundary'),
    (6.5, 'Member Controller', 'control'),
    (9, 'Names Model', 'entity'),
]

for x, label, ptype in participants:
    if ptype == 'actor':
        draw_actor(ax, x, 7.5, label, 0.3)
    elif ptype == 'boundary':
        draw_boundary(ax, x, 7.5, label, 0.25)
    elif ptype == 'control':
        draw_control(ax, x, 7.5, label, 0.25)
    else:
        draw_entity(ax, x, 7.5, label, 0.25)
    draw_lifeline(ax, x, 7, 0.5)

messages = [
    (1.5, 6.8, 4, 6.8, '1. View members', True),
    (4, 6.5, 6.5, 6.5, '1.1 Get member list', True),
    (6.5, 6.2, 9, 6.2, '2. Query members', True),
    (9, 5.9, 6.5, 5.9, '2.1 Return members', False),
    (6.5, 5.6, 4, 5.6, '3. Display list', False),
    (4, 5.3, 1.5, 5.3, '3.1 Show members', False),
    (1.5, 5.0, 4, 5.0, '4. Select member', True),
    (4, 4.7, 6.5, 4.7, '4.1 Edit request', True),
    (6.5, 4.4, 9, 4.4, '5. Update member', True),
    (9, 4.1, 6.5, 4.1, '5.1 Member updated', False),
    (6.5, 3.8, 4, 3.8, '6. Refresh list', False),
    (4, 3.5, 1.5, 3.5, '6.1 Show updated', False),
]

for x1, y1, x2, y2, label, solid in messages:
    draw_message(ax, x1, y1, x2, y2, label, solid)

plt.tight_layout()
plt.savefig('diagrams/07_member_management_sequence.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Member Management Sequence Diagram")

print("\nAll sequence diagrams created successfully!")
print("Next: Creating activity diagrams, class diagrams, component diagram, and deployment diagram...")
