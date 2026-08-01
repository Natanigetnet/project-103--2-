import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch
import numpy as np

# Set up style to match original diagrams exactly
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 11
plt.rcParams['font.weight'] = 'normal'

# Colors matching original
ACTOR_HEAD_COLOR = '#D8D8E8'
BOUNDARY_COLOR = '#D8D8E8'
CONTROL_COLOR = '#D8D8E8'
ENTITY_COLOR = '#D8D8E8'
BG_COLOR = '#FFFFFF'
ARROW_COLOR = '#000000'
TEXT_COLOR = '#000000'

def draw_actor_stick(ax, x, y, label, size=0.4):
    """Draw actor matching original style - circle head with body"""
    # Head
    circle = Circle((x, y + size*1.2), size*0.5, facecolor=ACTOR_HEAD_COLOR, edgecolor='black', linewidth=1.5, zorder=5)
    ax.add_patch(circle)
    # Body line
    ax.plot([x, x], [y + size*0.7, y - size*0.3], 'k-', linewidth=1.5, zorder=4)
    # Arms
    ax.plot([x - size*0.4, x + size*0.4], [y + size*0.4, y + size*0.4], 'k-', linewidth=1.5, zorder=4)
    # Legs
    ax.plot([x, x - size*0.3], [y - size*0.3, y - size*0.7], 'k-', linewidth=1.5, zorder=4)
    ax.plot([x, x + size*0.3], [y - size*0.3, y - size*0.7], 'k-', linewidth=1.5, zorder=4)
    # Label below
    ax.text(x, y - size*1.2, label, ha='center', va='top', fontsize=10, fontweight='normal')

def draw_boundary_object(ax, x, y, label, size=0.3):
    """Draw boundary object - circle with horizontal line"""
    circle = Circle((x, y), size, facecolor=BOUNDARY_COLOR, edgecolor='black', linewidth=1.5, zorder=5)
    ax.add_patch(circle)
    # Horizontal line through middle
    ax.plot([x - size*0.8, x + size*0.8], [y, y], 'k-', linewidth=1.5, zorder=6)
    # Label
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=10)

def draw_control_object(ax, x, y, label, size=0.3):
    """Draw control object - circle with arrow"""
    circle = Circle((x, y), size, facecolor=CONTROL_COLOR, edgecolor='black', linewidth=1.5, zorder=5)
    ax.add_patch(circle)
    # Arrow inside (curved)
    theta = np.linspace(0.3, 2.5, 20)
    arrow_x = x + size*0.5*np.cos(theta)
    arrow_y = y + size*0.5*np.sin(theta)
    ax.plot(arrow_x, arrow_y, 'k-', linewidth=1.5, zorder=6)
    ax.annotate('', xy=(arrow_x[-1], arrow_y[-1]), xytext=(arrow_x[-3], arrow_y[-3]),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    # Label
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=10)

def draw_entity_object(ax, x, y, label, size=0.3):
    """Draw entity object - plain circle"""
    circle = Circle((x, y), size, facecolor=ENTITY_COLOR, edgecolor='black', linewidth=1.5, zorder=5)
    ax.add_patch(circle)
    # Label
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=10)

def draw_lifeline(ax, x, y_top, y_bottom):
    """Draw dashed lifeline"""
    ax.plot([x, x], [y_top, y_bottom], 'k--', linewidth=0.8, alpha=0.6, zorder=1)

def draw_activation_bar(ax, x, y_top, y_bottom, width=0.12):
    """Draw activation bar on lifeline"""
    rect = Rectangle((x - width/2, y_bottom), width, y_top - y_bottom,
                     facecolor='white', edgecolor='black', linewidth=1, zorder=3)
    ax.add_patch(rect)

def draw_solid_arrow(ax, x1, y1, x2, y2, label, label_pos='above'):
    """Draw solid arrow for synchronous message"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.2, connectionstyle='arc3,rad=0'), zorder=4)
    # Label
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    offset = 0.15 if label_pos == 'above' else -0.15
    ax.text(mid_x, mid_y + offset, label, ha='center', va='center', fontsize=9, zorder=5)

def draw_dashed_arrow(ax, x1, y1, x2, y2, label, label_pos='above'):
    """Draw dashed arrow for return message"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.2, linestyle='dashed', connectionstyle='arc3,rad=0'), zorder=4)
    # Label
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    offset = 0.15 if label_pos == 'above' else -0.15
    ax.text(mid_x, mid_y + offset, label, ha='center', va='center', fontsize=9, zorder=5)

def draw_alt_frame(ax, x, y, width, height, conditions):
    """Draw alt fragment frame matching original style"""
    # Main rectangle
    rect = Rectangle((x, y), width, height, facecolor='none', edgecolor='black', linewidth=1.5, zorder=2)
    ax.add_patch(rect)
    
    # "alt" label in top-left
    ax.text(x + 0.15, y + height - 0.2, 'alt', fontsize=10, fontweight='bold', zorder=5)
    
    # Condition dividers
    for i, cond in enumerate(conditions):
        if i > 0:
            cond_y = y + height - 0.5 - i * (height - 1) / len(conditions)
            ax.plot([x, x + width], [cond_y, cond_y], 'k--', linewidth=0.8, zorder=3)
        # Condition label
        cond_y = y + height - 0.5 - i * (height - 1) / len(conditions)
        ax.text(x + 0.3, cond_y + 0.1, f'[{cond}]', fontsize=9, fontweight='bold', zorder=5)

def draw_destruction_x(ax, x, y, size=0.2):
    """Draw X mark for destruction"""
    ax.plot([x - size, x + size], [y - size, y + size], 'r-', linewidth=2, zorder=5)
    ax.plot([x - size, x + size], [y + size, y - size], 'r-', linewidth=2, zorder=5)

# ============================================================
# DIAGRAM 1: Use Case Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

# System boundary box
rect = FancyBboxPatch((4, 1), 8, 10, boxstyle="round,pad=0.1", facecolor='none', edgecolor='black', linewidth=2)
ax.add_patch(rect)
ax.text(8, 11.5, 'Gym Management System', ha='center', fontsize=14, fontweight='bold')

# Actors (left side)
draw_actor_stick(ax, 1.5, 9, 'Admin', 0.5)
draw_actor_stick(ax, 1.5, 6, 'Trainer', 0.5)
draw_actor_stick(ax, 1.5, 3, 'Trainee', 0.5)

# Actors (right side)
draw_actor_stick(ax, 14.5, 9, 'Registrar', 0.5)

# Use cases (ellipses inside system boundary)
use_cases = [
    (6, 10, 'Manage Users'),
    (8, 10, 'View Reports'),
    (10, 10, 'Configure System'),
    (6, 8.5, 'Create Sessions'),
    (8, 8.5, 'Manage Trainees'),
    (10, 8.5, 'View Schedule'),
    (6, 7, 'Book Session'),
    (8, 7, 'View Training Plan'),
    (10, 7, 'Track BMI'),
    (6, 5.5, 'Scan QR Code'),
    (8, 5.5, 'Register Member'),
    (10, 5.5, 'View Attendance'),
    (6, 4, 'Chat with AI'),
    (8, 4, 'View Feed'),
    (10, 4, 'Make Payment'),
    (6, 2.5, 'Rate Trainer'),
    (8, 2.5, 'Request Trainer Change'),
    (10, 2.5, 'View ID Card'),
]

for x, y, label in use_cases:
    ellipse = mpatches.Ellipse((x, y), 1.5, 0.6, facecolor='#E8E8F0', edgecolor='black', linewidth=1.2)
    ax.add_patch(ellipse)
    ax.text(x, y, label, ha='center', va='center', fontsize=9)

# Connect actors to use cases
connections = [
    # Admin connections
    (1.9, 9, 5.2, 10), (1.9, 9, 7.2, 10), (1.9, 9, 9.2, 10),
    (1.9, 9, 5.2, 5.5), (1.9, 9, 7.2, 5.5), (1.9, 9, 9.2, 5.5),
    # Trainer connections
    (1.9, 6, 5.2, 8.5), (1.9, 6, 7.2, 8.5), (1.9, 6, 9.2, 8.5),
    (1.9, 6, 5.2, 7), (1.9, 6, 7.2, 7),
    # Trainee connections
    (1.9, 3, 5.2, 7), (1.9, 3, 7.2, 7), (1.9, 3, 9.2, 7),
    (1.9, 3, 5.2, 4), (1.9, 3, 7.2, 4), (1.9, 3, 9.2, 4),
    (1.9, 3, 5.2, 2.5), (1.9, 3, 7.2, 2.5), (1.9, 3, 9.2, 2.5),
    # Registrar connections
    (14.1, 9, 9.8, 5.5), (14.1, 9, 7.8, 5.5), (14.1, 9, 5.8, 5.5),
]

for x1, y1, x2, y2 in connections:
    ax.plot([x1, x2], [y1, y2], 'k-', linewidth=0.8, zorder=1)

plt.tight_layout()
plt.savefig('diagrams_new/01_use_case_diagram.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Use Case Diagram")

# ============================================================
# DIAGRAM 2: Registration Sequence Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

# Title
ax.text(7, 9.5, 'Figure 3.5.1 Registration Sequence Diagram', ha='center', fontsize=12, fontweight='bold')

# Participants at top
participants_top = [
    (2, 'Guest', 'actor'),
    (5, 'Signup Page', 'boundary'),
    (8, 'Auth Controller', 'control'),
    (11, 'User Model', 'entity'),
    (13, 'Email Service', 'entity'),
]

for x, label, ptype in participants_top:
    if ptype == 'actor':
        draw_actor_stick(ax, x, 8.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_object(ax, x, 8.5, label, 0.3)
    elif ptype == 'control':
        draw_control_object(ax, x, 8.5, label, 0.3)
    else:
        draw_entity_object(ax, x, 8.5, label, 0.3)

# Draw lifelines
lifeline_y_top = 8
lifeline_y_bottom = 1
for x, label, ptype in participants_top:
    draw_lifeline(ax, x, lifeline_y_top, lifeline_y_bottom)

# Messages
messages = [
    # Solid arrows (synchronous)
    (2, 7.5, 5, 7.5, '1. Select Register', 'solid'),
    (5, 7.2, 8, 7.2, '1.1 Submit form', 'solid'),
    (8, 6.9, 11, 6.9, '2. Create user', 'solid'),
    (8, 6.3, 13, 6.3, '3. Send welcome email', 'solid'),
    # Dashed arrows (return)
    (11, 6.6, 8, 6.6, '2.1 User created', 'dashed'),
    (13, 6.0, 8, 6.0, '3.1 Email sent', 'dashed'),
    (8, 5.7, 5, 5.7, '4. Show success', 'dashed'),
    (5, 5.4, 2, 5.4, '4.1 Redirect to home', 'dashed'),
]

for x1, y1, x2, y2, label, arrow_type in messages:
    if arrow_type == 'solid':
        draw_solid_arrow(ax, x1, y1, x2, y2, label)
    else:
        draw_dashed_arrow(ax, x1, y1, x2, y2, label)

# Activation bars
draw_activation_bar(ax, 5, 7.5, 5.4, 0.12)
draw_activation_bar(ax, 8, 7.2, 5.7, 0.12)
draw_activation_bar(ax, 11, 6.9, 6.6, 0.12)
draw_activation_bar(ax, 13, 6.3, 6.0, 0.12)

# Destruction marks at bottom
for x, label, ptype in participants_top[1:]:  # Skip actor
    draw_destruction_x(ax, x, 1.2, 0.2)

# Participants at bottom (same as top)
for x, label, ptype in participants_top:
    if ptype == 'actor':
        draw_actor_stick(ax, x, 0.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_object(ax, x, 0.5, label, 0.3)
    elif ptype == 'control':
        draw_control_object(ax, x, 0.5, label, 0.3)
    else:
        draw_entity_object(ax, x, 0.5, label, 0.3)

plt.tight_layout()
plt.savefig('diagrams_new/02_registration_sequence.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Registration Sequence Diagram")

# ============================================================
# DIAGRAM 3: Login Sequence Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

ax.text(7, 9.5, 'Figure 3.5.2 Login Sequence Diagram', ha='center', fontsize=12, fontweight='bold')

participants_top = [
    (2, 'User', 'actor'),
    (5, 'Login Page', 'boundary'),
    (8, 'Auth Controller', 'control'),
    (11, 'User Model', 'entity'),
]

for x, label, ptype in participants_top:
    if ptype == 'actor':
        draw_actor_stick(ax, x, 8.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_object(ax, x, 8.5, label, 0.3)
    elif ptype == 'control':
        draw_control_object(ax, x, 8.5, label, 0.3)
    else:
        draw_entity_object(ax, x, 8.5, label, 0.3)

for x, label, ptype in participants_top:
    draw_lifeline(ax, x, 8, 1)

messages = [
    (2, 7.5, 5, 7.5, '1. Enter credentials', 'solid'),
    (5, 7.2, 8, 7.2, '1.1 Submit login', 'solid'),
    (8, 6.9, 11, 6.9, '2. Validate credentials', 'solid'),
    (11, 6.6, 8, 6.6, '2.1 User found', 'dashed'),
    (8, 6.3, 11, 6.3, '3. Check password', 'solid'),
    (11, 6.0, 8, 6.0, '3.1 Password valid', 'dashed'),
    (8, 5.7, 5, 5.7, '4. Create session', 'dashed'),
    (5, 5.4, 2, 5.4, '4.1 Redirect to dashboard', 'dashed'),
]

for x1, y1, x2, y2, label, arrow_type in messages:
    if arrow_type == 'solid':
        draw_solid_arrow(ax, x1, y1, x2, y2, label)
    else:
        draw_dashed_arrow(ax, x1, y1, x2, y2, label)

draw_activation_bar(ax, 5, 7.5, 5.4, 0.12)
draw_activation_bar(ax, 8, 7.2, 5.7, 0.12)
draw_activation_bar(ax, 11, 6.9, 6.0, 0.12)

for x, label, ptype in participants_top[1:]:
    draw_destruction_x(ax, x, 1.2, 0.2)

for x, label, ptype in participants_top:
    if ptype == 'actor':
        draw_actor_stick(ax, x, 0.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_object(ax, x, 0.5, label, 0.3)
    elif ptype == 'control':
        draw_control_object(ax, x, 0.5, label, 0.3)
    else:
        draw_entity_object(ax, x, 0.5, label, 0.3)

plt.tight_layout()
plt.savefig('diagrams_new/03_login_sequence.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Login Sequence Diagram")

# ============================================================
# DIAGRAM 4: Session Booking Sequence Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

ax.text(7, 9.5, 'Figure 3.5.3 Session Booking Sequence Diagram', ha='center', fontsize=12, fontweight='bold')

participants_top = [
    (2, 'Trainee', 'actor'),
    (5, 'Session List', 'boundary'),
    (8, 'Booking Controller', 'control'),
    (11, 'TrainingSession', 'entity'),
]

for x, label, ptype in participants_top:
    if ptype == 'actor':
        draw_actor_stick(ax, x, 8.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_object(ax, x, 8.5, label, 0.3)
    elif ptype == 'control':
        draw_control_object(ax, x, 8.5, label, 0.3)
    else:
        draw_entity_object(ax, x, 8.5, label, 0.3)

for x, label, ptype in participants_top:
    draw_lifeline(ax, x, 8, 1)

messages = [
    (2, 7.5, 5, 7.5, '1. View available sessions', 'solid'),
    (5, 7.2, 8, 7.2, '1.1 Get sessions', 'solid'),
    (8, 6.9, 11, 6.9, '2. Query sessions', 'solid'),
    (11, 6.6, 8, 6.6, '2.1 Return list', 'dashed'),
    (8, 6.3, 5, 6.3, '3. Display sessions', 'dashed'),
    (5, 6.0, 2, 6.0, '3.1 Show to trainee', 'dashed'),
    (2, 5.7, 5, 5.7, '4. Select session', 'solid'),
    (5, 5.4, 8, 5.4, '4.1 Register request', 'solid'),
    (8, 5.1, 11, 5.1, '5. Check availability', 'solid'),
    (11, 4.8, 8, 4.8, '5.1 Slots available', 'dashed'),
    (8, 4.5, 11, 4.5, '6. Add trainee', 'solid'),
    (11, 4.2, 8, 4.2, '6.1 Registration saved', 'dashed'),
    (8, 3.9, 5, 3.9, '7. Confirm booking', 'dashed'),
    (5, 3.6, 2, 3.6, '7.1 Show confirmation', 'dashed'),
]

for x1, y1, x2, y2, label, arrow_type in messages:
    if arrow_type == 'solid':
        draw_solid_arrow(ax, x1, y1, x2, y2, label)
    else:
        draw_dashed_arrow(ax, x1, y1, x2, y2, label)

draw_activation_bar(ax, 5, 7.5, 3.6, 0.12)
draw_activation_bar(ax, 8, 7.2, 3.9, 0.12)
draw_activation_bar(ax, 11, 6.9, 4.2, 0.12)

for x, label, ptype in participants_top[1:]:
    draw_destruction_x(ax, x, 1.2, 0.2)

for x, label, ptype in participants_top:
    if ptype == 'actor':
        draw_actor_stick(ax, x, 0.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_object(ax, x, 0.5, label, 0.3)
    elif ptype == 'control':
        draw_control_object(ax, x, 0.5, label, 0.3)
    else:
        draw_entity_object(ax, x, 0.5, label, 0.3)

plt.tight_layout()
plt.savefig('diagrams_new/04_session_booking_sequence.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Session Booking Sequence Diagram")

# ============================================================
# DIAGRAM 5: QR Attendance Sequence Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

ax.text(7, 9.5, 'Figure 3.5.4 QR Attendance Sequence Diagram', ha='center', fontsize=12, fontweight='bold')

participants_top = [
    (2, 'Trainee', 'actor'),
    (5, 'QR Scanner', 'boundary'),
    (8, 'Attendance Controller', 'control'),
    (11, 'AttendanceLog', 'entity'),
]

for x, label, ptype in participants_top:
    if ptype == 'actor':
        draw_actor_stick(ax, x, 8.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_object(ax, x, 8.5, label, 0.3)
    elif ptype == 'control':
        draw_control_object(ax, x, 8.5, label, 0.3)
    else:
        draw_entity_object(ax, x, 8.5, label, 0.3)

for x, label, ptype in participants_top:
    draw_lifeline(ax, x, 8, 1)

# Alt frame
draw_alt_frame(ax, 0.5, 2, 13, 4, ['membership active', 'membership expired'])

messages = [
    (2, 7.5, 5, 7.5, '1. Show QR code', 'solid'),
    (5, 7.2, 8, 7.2, '1.1 Scan QR', 'solid'),
    (8, 6.9, 11, 6.9, '2. Lookup member', 'solid'),
    (11, 6.6, 8, 6.6, '2.1 Member found', 'dashed'),
    (8, 6.3, 11, 6.3, '3. Check membership', 'solid'),
    (11, 6.0, 8, 6.0, '3.1 Membership active', 'dashed'),
    # Inside alt frame - membership active
    (8, 5.5, 11, 5.5, '4. Create attendance log', 'solid'),
    (11, 5.2, 8, 5.2, '4.1 Log created', 'dashed'),
    (8, 4.9, 5, 4.9, '5. Show success', 'dashed'),
    (5, 4.6, 2, 4.6, '5.1 Check-in confirmed', 'dashed'),
    # Inside alt frame - membership expired
    (8, 3.5, 5, 3.5, '4. Return notification', 'dashed'),
    (5, 3.2, 2, 3.2, '4.1 Prompt for renewal', 'dashed'),
]

for x1, y1, x2, y2, label, arrow_type in messages:
    if arrow_type == 'solid':
        draw_solid_arrow(ax, x1, y1, x2, y2, label)
    else:
        draw_dashed_arrow(ax, x1, y1, x2, y2, label)

draw_activation_bar(ax, 5, 7.5, 3.2, 0.12)
draw_activation_bar(ax, 8, 7.2, 3.5, 0.12)
draw_activation_bar(ax, 11, 6.9, 5.2, 0.12)

for x, label, ptype in participants_top[1:]:
    draw_destruction_x(ax, x, 1.2, 0.2)

for x, label, ptype in participants_top:
    if ptype == 'actor':
        draw_actor_stick(ax, x, 0.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_object(ax, x, 0.5, label, 0.3)
    elif ptype == 'control':
        draw_control_object(ax, x, 0.5, label, 0.3)
    else:
        draw_entity_object(ax, x, 0.5, label, 0.3)

plt.tight_layout()
plt.savefig('diagrams_new/05_qr_attendance_sequence.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created QR Attendance Sequence Diagram")

print("\nCreated first 5 diagrams matching original style")
print("Continuing with remaining diagrams...")
