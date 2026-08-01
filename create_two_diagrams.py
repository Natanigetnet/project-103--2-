import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch
import numpy as np

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# ============================================================
# USE CASE DIAGRAM - Matching original style exactly
# ============================================================
fig, ax = plt.subplots(figsize=(12, 16))
ax.set_xlim(0, 12)
ax.set_ylim(0, 16)
ax.axis('off')
ax.set_facecolor('#FFFFFF')

# Helper functions matching original style
def draw_actor_simple(ax, x, y, label, size=0.3):
    """Simple stick figure actor matching original"""
    # Head (circle, no fill)
    circle = Circle((x, y + size*1.5), size*0.4, facecolor='none', edgecolor='black', linewidth=1.2)
    ax.add_patch(circle)
    # Body
    ax.plot([x, x], [y + size*1.1, y + size*0.3], 'k-', linewidth=1.2)
    # Arms
    ax.plot([x - size*0.4, x + size*0.4], [y + size*0.8, y + size*0.8], 'k-', linewidth=1.2)
    # Legs
    ax.plot([x, x - size*0.3], [y + size*0.3, y - size*0.1], 'k-', linewidth=1.2)
    ax.plot([x, x + size*0.3], [y + size*0.3, y - size*0.1], 'k-', linewidth=1.2)
    # Label
    ax.text(x, y - size*0.3, label, ha='center', va='top', fontsize=9)

def draw_use_case_oval(ax, x, y, width, height, label, uc_id=None):
    """Oval use case matching original style"""
    ellipse = mpatches.Ellipse((x, y), width, height, facecolor='#F0F0F0', edgecolor='black', linewidth=1)
    ax.add_patch(ellipse)
    if uc_id:
        ax.text(x, y + 0.1, label, ha='center', va='center', fontsize=8)
        ax.text(x, y - 0.15, f'({uc_id})', ha='center', va='center', fontsize=7)
    else:
        ax.text(x, y, label, ha='center', va='center', fontsize=8)

def draw_system_boundary(ax, x, y, width, height, title):
    """System boundary box matching original"""
    rect = Rectangle((x, y), width, height, facecolor='none', edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(x + width/2, y + height - 0.2, title, ha='center', va='top', fontsize=10, fontweight='bold')

# System boundaries (subsystems)
draw_system_boundary(ax, 2, 12, 3.5, 3, 'Access Control')
draw_system_boundary(ax, 2, 6, 3.5, 5.5, 'Resource & Training')
draw_system_boundary(ax, 6, 4, 3.5, 4, 'Communication & Management')
draw_system_boundary(ax, 6, 1, 3.5, 2.5, 'Payments')

# Actors
draw_actor_simple(ax, 0.5, 13.5, 'Guest', 0.4)
draw_actor_simple(ax, 0.5, 9, 'Member', 0.4)
draw_actor_simple(ax, 3.5, 5, 'Trainer', 0.4)
draw_actor_simple(ax, 7.5, 2.5, 'Admin', 0.4)
draw_actor_simple(ax, 7.5, 0.3, 'Chapa', 0.4)

# Use cases - Access Control
draw_use_case_oval(ax, 3.5, 14, 1.2, 0.5, 'Login', 'UC-02')
draw_use_case_oval(ax, 3.5, 13, 1.2, 0.5, 'Register Account', 'UC-01')
draw_use_case_oval(ax, 3.5, 12, 1.2, 0.5, 'Logout', 'UC-03')
draw_use_case_oval(ax, 3.5, 11, 1.2, 0.5, 'Update Profile', 'UC-04')

# Use cases - Resource & Training
draw_use_case_oval(ax, 3.5, 10.5, 1.2, 0.5, 'Post Resource', 'UC-07')
draw_use_case_oval(ax, 3.5, 9.5, 1.2, 0.5, 'View Resources', 'UC-05')
draw_use_case_oval(ax, 3.5, 8.5, 1.2, 0.5, 'Search Resources', 'UC-06')
draw_use_case_oval(ax, 3.5, 7.5, 1.2, 0.5, 'Request Resource', 'UC-08')
draw_use_case_oval(ax, 3.5, 6.5, 1.2, 0.5, 'Rate Resource', 'UC-09')
draw_use_case_oval(ax, 3.5, 5.5, 1.2, 0.5, 'Send Message', 'UC-10')
draw_use_case_oval(ax, 3.5, 4.5, 1.2, 0.5, 'Upload Workout', 'UC-12')
draw_use_case_oval(ax, 3.5, 3.5, 1.2, 0.5, 'Manage Clients', 'UC-13')
draw_use_case_oval(ax, 3.5, 2.5, 1.2, 0.5, 'Create Training Program', 'UC-11')
draw_use_case_oval(ax, 3.5, 1.5, 1.2, 0.5, 'Respond to Questions', 'UC-14')
draw_use_case_oval(ax, 3.5, 0.5, 1.2, 0.5, 'Update Training Program', 'UC-15')

# Use cases - Communication & Management
draw_use_case_oval(ax, 7.5, 7, 1.2, 0.5, 'Approve Submission', 'UC-16')
draw_use_case_oval(ax, 7.5, 6, 1.2, 0.5, 'Suspend User', 'UC-19')
draw_use_case_oval(ax, 7.5, 5, 1.2, 0.5, 'View System Logs', 'UC-21')
draw_use_case_oval(ax, 7.5, 4, 1.2, 0.5, 'Generate Reports', 'UC-20')
draw_use_case_oval(ax, 7.5, 3, 1.2, 0.5, 'Manage Users', 'UC-18')
draw_use_case_oval(ax, 7.5, 2, 1.2, 0.5, 'Reject Submission', 'UC-17')

# Use cases - Payments
draw_use_case_oval(ax, 7.5, 1.5, 1.2, 0.5, 'Payment Integration', 'UC-22')

# Actor connections (solid lines)
# Guest connections
ax.plot([0.8, 2.9], [13.5, 14], 'k-', linewidth=0.8)  # Guest - Login
ax.plot([0.8, 2.9], [13.5, 13], 'k-', linewidth=0.8)  # Guest - Register

# Member connections
ax.plot([0.8, 2.9], [9, 10.5], 'k-', linewidth=0.8)  # Member - Post Resource
ax.plot([0.8, 2.9], [9, 9.5], 'k-', linewidth=0.8)   # Member - View Resources
ax.plot([0.8, 2.9], [9, 8.5], 'k-', linewidth=0.8)   # Member - Search Resources
ax.plot([0.8, 2.9], [9, 7.5], 'k-', linewidth=0.8)   # Member - Request Resource
ax.plot([0.8, 2.9], [9, 6.5], 'k-', linewidth=0.8)   # Member - Rate Resource
ax.plot([0.8, 2.9], [9, 5.5], 'k-', linewidth=0.8)   # Member - Send Message

# Trainer connections
ax.plot([3.8, 2.9], [5, 4.5], 'k-', linewidth=0.8)   # Trainer - Upload Workout
ax.plot([3.8, 2.9], [5, 3.5], 'k-', linewidth=0.8)   # Trainer - Manage Clients
ax.plot([3.8, 2.9], [5, 2.5], 'k-', linewidth=0.8)   # Trainer - Create Training Program
ax.plot([3.8, 2.9], [5, 1.5], 'k-', linewidth=0.8)   # Trainer - Respond to Questions
ax.plot([3.8, 2.9], [5, 0.5], 'k-', linewidth=0.8)   # Trainer - Update Training Program

# Admin connections
ax.plot([7.8, 6.9], [2.5, 7], 'k-', linewidth=0.8)   # Admin - Approve Submission
ax.plot([7.8, 6.9], [2.5, 6], 'k-', linewidth=0.8)   # Admin - Suspend User
ax.plot([7.8, 6.9], [2.5, 5], 'k-', linewidth=0.8)   # Admin - View System Logs
ax.plot([7.8, 6.9], [2.5, 4], 'k-', linewidth=0.8)   # Admin - Generate Reports
ax.plot([7.8, 6.9], [2.5, 3], 'k-', linewidth=0.8)   # Admin - Manage Users
ax.plot([7.8, 6.9], [2.5, 2], 'k-', linewidth=0.8)   # Admin - Reject Submission
ax.plot([7.8, 6.9], [2.5, 1.5], 'k-', linewidth=0.8) # Admin - Payment Integration

# Chapa connection
ax.plot([7.8, 6.9], [0.3, 1.5], 'k-', linewidth=0.8) # Chapa - Payment Integration

# Include/Extend relationships (dashed arrows)
# Login includes Register
ax.annotate('', xy=(3.5, 13.3), xytext=(3.5, 13.7),
            arrowprops=dict(arrowstyle='->', color='black', lw=0.8, linestyle='dashed'))
ax.text(3.8, 13.5, '<<include>>', fontsize=7, rotation=90)

# Post Resource extends Approve Submission
ax.annotate('', xy=(6.9, 7), xytext=(4.1, 10.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=0.8, linestyle='dashed'))
ax.text(5.5, 8.5, '<<extend>>', fontsize=7)

# Upload Workout extends Approve Submission
ax.annotate('', xy=(6.9, 7), xytext=(4.1, 4.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=0.8, linestyle='dashed'))
ax.text(5.5, 6, '<<extend>>', fontsize=7)

# Manage Users includes Generate Reports
ax.annotate('', xy=(7.5, 4.3), xytext=(7.5, 3.3),
            arrowprops=dict(arrowstyle='->', color='black', lw=0.8, linestyle='dashed'))
ax.text(7.8, 3.8, '<<include>>', fontsize=7, rotation=90)

# Manage Users extends Reject Submission
ax.annotate('', xy=(7.5, 2.3), xytext=(7.5, 3.3),
            arrowprops=dict(arrowstyle='->', color='black', lw=0.8, linestyle='dashed'))
ax.text(7.8, 2.8, '<<extend>>', fontsize=7, rotation=90)

plt.tight_layout()
plt.savefig('diagrams_new/01_use_case_diagram.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Use Case Diagram matching original style")

# ============================================================
# REGISTRATION SEQUENCE DIAGRAM - Matching original style exactly
# ============================================================
fig, ax = plt.subplots(figsize=(12, 10))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor('#FFFFFF')

# Colors matching original
ACTOR_COLOR = '#D8D8E8'
OBJECT_COLOR = '#D8D8E8'

def draw_actor_original(ax, x, y, label, size=0.4):
    """Actor matching original - circle head with body"""
    # Head (larger circle with fill)
    circle = Circle((x, y + size*1.3), size*0.5, facecolor=ACTOR_COLOR, edgecolor='black', linewidth=1, zorder=5)
    ax.add_patch(circle)
    # Body
    ax.plot([x, x], [y + size*0.8, y - size*0.2], 'k-', linewidth=1, zorder=4)
    # Arms
    ax.plot([x - size*0.4, x + size*0.4], [y + size*0.5, y + size*0.5], 'k-', linewidth=1, zorder=4)
    # Legs
    ax.plot([x, x - size*0.3], [y - size*0.2, y - size*0.6], 'k-', linewidth=1, zorder=4)
    ax.plot([x, x + size*0.3], [y - size*0.2, y - size*0.6], 'k-', linewidth=1, zorder=4)
    # Label
    ax.text(x, y - size*0.9, label, ha='center', va='top', fontsize=9)

def draw_boundary_original(ax, x, y, label, size=0.25):
    """Boundary object - circle with T-shape line"""
    circle = Circle((x, y), size, facecolor=OBJECT_COLOR, edgecolor='black', linewidth=1, zorder=5)
    ax.add_patch(circle)
    # T-shape line (horizontal line above circle)
    ax.plot([x - size*0.6, x + size*0.6], [y + size*1.2, y + size*1.2], 'k-', linewidth=1, zorder=6)
    ax.plot([x, x], [y + size, y + size*1.2], 'k-', linewidth=1, zorder=6)
    # Label
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=9)

def draw_control_original(ax, x, y, label, size=0.25):
    """Control object - circle with curved arrow"""
    circle = Circle((x, y), size, facecolor=OBJECT_COLOR, edgecolor='black', linewidth=1, zorder=5)
    ax.add_patch(circle)
    # Curved arrow inside
    theta = np.linspace(0.5, 2.8, 20)
    arrow_x = x + size*0.6*np.cos(theta)
    arrow_y = y + size*0.6*np.sin(theta)
    ax.plot(arrow_x, arrow_y, 'k-', linewidth=1, zorder=6)
    ax.annotate('', xy=(arrow_x[-1], arrow_y[-1]), xytext=(arrow_x[-3], arrow_y[-3]),
                arrowprops=dict(arrowstyle='->', color='black', lw=1))
    # Label
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=9)

def draw_entity_original(ax, x, y, label, size=0.25):
    """Entity object - plain circle"""
    circle = Circle((x, y), size, facecolor=OBJECT_COLOR, edgecolor='black', linewidth=1, zorder=5)
    ax.add_patch(circle)
    # Label
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=9)

def draw_lifeline_original(ax, x, y_top, y_bottom):
    """Dashed lifeline"""
    ax.plot([x, x], [y_top, y_bottom], 'k--', linewidth=0.8, alpha=0.5, zorder=1)

def draw_activation_original(ax, x, y_top, y_bottom, width=0.1):
    """Activation bar"""
    rect = Rectangle((x - width/2, y_bottom), width, y_top - y_bottom,
                     facecolor='white', edgecolor='black', linewidth=0.8, zorder=3)
    ax.add_patch(rect)

def draw_message_solid(ax, x1, y1, x2, y2, label):
    """Solid arrow message"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', lw=1), zorder=4)
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    ax.text(mid_x, mid_y + 0.1, label, ha='center', va='bottom', fontsize=8, zorder=5)

def draw_message_dashed(ax, x1, y1, x2, y2, label):
    """Dashed arrow message"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', lw=1, linestyle='dashed'), zorder=4)
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    ax.text(mid_x, mid_y + 0.1, label, ha='center', va='bottom', fontsize=8, zorder=5)

def draw_alt_frame_original(ax, x, y, width, height, conditions):
    """Alt frame matching original"""
    rect = Rectangle((x, y), width, height, facecolor='none', edgecolor='black', linewidth=1.2, zorder=2)
    ax.add_patch(rect)
    # "alt" label in small box
    alt_box = Rectangle((x, y + height - 0.4), 0.5, 0.3, facecolor='white', edgecolor='black', linewidth=1, zorder=3)
    ax.add_patch(alt_box)
    ax.text(x + 0.25, y + height - 0.25, 'alt', ha='center', va='center', fontsize=8, fontweight='bold', zorder=4)
    # Conditions
    for i, cond in enumerate(conditions):
        if i > 0:
            cond_y = y + height - 0.5 - i * (height - 0.8) / len(conditions)
            ax.plot([x, x + width], [cond_y, cond_y], 'k--', linewidth=0.8, zorder=3)
        cond_y = y + height - 0.5 - i * (height - 0.8) / len(conditions)
        ax.text(x + 0.6, cond_y + 0.1, f'[{cond}]', fontsize=8, fontweight='bold', zorder=5)

def draw_destruction_original(ax, x, y, size=0.15):
    """Red X destruction mark"""
    ax.plot([x - size, x + size], [y - size, y + size], 'r-', linewidth=1.5, zorder=5)
    ax.plot([x - size, x + size], [y + size, y - size], 'r-', linewidth=1.5, zorder=5)

# Participants at top
participants = [
    (1.5, 'Guest', 'actor'),
    (4, 'Registration Page', 'boundary'),
    (7, 'Registration Controller', 'control'),
    (10, 'User Table', 'entity'),
]

for x, label, ptype in participants:
    if ptype == 'actor':
        draw_actor_original(ax, x, 8.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_original(ax, x, 8.5, label, 0.25)
    elif ptype == 'control':
        draw_control_original(ax, x, 8.5, label, 0.25)
    else:
        draw_entity_original(ax, x, 8.5, label, 0.25)

# Lifelines
for x, label, ptype in participants:
    draw_lifeline_original(ax, x, 8, 1)

# Messages
draw_message_solid(ax, 1.5, 7.5, 4, 7.5, '1. Open registration page')
draw_message_dashed(ax, 4, 7.2, 1.5, 7.2, '1.1 Displays Form')
draw_message_solid(ax, 1.5, 6.9, 4, 6.9, '2. Enter details')
draw_message_solid(ax, 4, 6.6, 7, 6.6, '2.1 Pass data for validation')

# Alt frame
draw_alt_frame_original(ax, 0.3, 2, 11.4, 4.3, ['validation successful', 'validation errors or duplicate'])

# Messages inside alt frame
draw_message_solid(ax, 7, 5.8, 10, 5.8, '3. Check duplicates & Store')
draw_message_dashed(ax, 10, 5.5, 7, 5.5, '3.1 Data saved')
draw_message_dashed(ax, 7, 5.2, 4, 5.2, '4. Registration success')
draw_message_dashed(ax, 4, 4.9, 1.5, 4.9, '4.1 Show confirmation')

draw_message_dashed(ax, 7, 3.5, 4, 3.5, '4. Return validation error')
draw_message_dashed(ax, 4, 3.2, 1.5, 3.2, '4.1 Show error message')

# Activation bars
draw_activation_original(ax, 4, 7.5, 3.2, 0.1)
draw_activation_original(ax, 7, 6.6, 3.5, 0.1)
draw_activation_original(ax, 10, 5.8, 5.5, 0.1)

# Destruction marks
for x, label, ptype in participants[1:]:
    draw_destruction_original(ax, x, 1.2, 0.15)

# Participants at bottom (same as top)
for x, label, ptype in participants:
    if ptype == 'actor':
        draw_actor_original(ax, x, 0.5, label, 0.4)
    elif ptype == 'boundary':
        draw_boundary_original(ax, x, 0.5, label, 0.25)
    elif ptype == 'control':
        draw_control_original(ax, x, 0.5, label, 0.25)
    else:
        draw_entity_original(ax, x, 0.5, label, 0.25)

plt.tight_layout()
plt.savefig('diagrams_new/02_registration_sequence.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Registration Sequence Diagram matching original style")

print("\nBoth diagrams created matching original design exactly!")
