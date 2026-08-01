import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch
import numpy as np

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 11

ACTOR_HEAD_COLOR = '#D8D8E8'
BOUNDARY_COLOR = '#D8D8E8'
CONTROL_COLOR = '#D8D8E8'
ENTITY_COLOR = '#D8D8E8'
BG_COLOR = '#FFFFFF'

def draw_actor_stick(ax, x, y, label, size=0.4):
    circle = Circle((x, y + size*1.2), size*0.5, facecolor=ACTOR_HEAD_COLOR, edgecolor='black', linewidth=1.5, zorder=5)
    ax.add_patch(circle)
    ax.plot([x, x], [y + size*0.7, y - size*0.3], 'k-', linewidth=1.5, zorder=4)
    ax.plot([x - size*0.4, x + size*0.4], [y + size*0.4, y + size*0.4], 'k-', linewidth=1.5, zorder=4)
    ax.plot([x, x - size*0.3], [y - size*0.3, y - size*0.7], 'k-', linewidth=1.5, zorder=4)
    ax.plot([x, x + size*0.3], [y - size*0.3, y - size*0.7], 'k-', linewidth=1.5, zorder=4)
    ax.text(x, y - size*1.2, label, ha='center', va='top', fontsize=10)

def draw_boundary_object(ax, x, y, label, size=0.3):
    circle = Circle((x, y), size, facecolor=BOUNDARY_COLOR, edgecolor='black', linewidth=1.5, zorder=5)
    ax.add_patch(circle)
    ax.plot([x - size*0.8, x + size*0.8], [y, y], 'k-', linewidth=1.5, zorder=6)
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=10)

def draw_control_object(ax, x, y, label, size=0.3):
    circle = Circle((x, y), size, facecolor=CONTROL_COLOR, edgecolor='black', linewidth=1.5, zorder=5)
    ax.add_patch(circle)
    theta = np.linspace(0.3, 2.5, 20)
    arrow_x = x + size*0.5*np.cos(theta)
    arrow_y = y + size*0.5*np.sin(theta)
    ax.plot(arrow_x, arrow_y, 'k-', linewidth=1.5, zorder=6)
    ax.annotate('', xy=(arrow_x[-1], arrow_y[-1]), xytext=(arrow_x[-3], arrow_y[-3]),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=10)

def draw_entity_object(ax, x, y, label, size=0.3):
    circle = Circle((x, y), size, facecolor=ENTITY_COLOR, edgecolor='black', linewidth=1.5, zorder=5)
    ax.add_patch(circle)
    ax.text(x, y - size*1.5, label, ha='center', va='top', fontsize=10)

def draw_lifeline(ax, x, y_top, y_bottom):
    ax.plot([x, x], [y_top, y_bottom], 'k--', linewidth=0.8, alpha=0.6, zorder=1)

def draw_activation_bar(ax, x, y_top, y_bottom, width=0.12):
    rect = Rectangle((x - width/2, y_bottom), width, y_top - y_bottom,
                     facecolor='white', edgecolor='black', linewidth=1, zorder=3)
    ax.add_patch(rect)

def draw_solid_arrow(ax, x1, y1, x2, y2, label, label_pos='above'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.2, connectionstyle='arc3,rad=0'), zorder=4)
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    offset = 0.15 if label_pos == 'above' else -0.15
    ax.text(mid_x, mid_y + offset, label, ha='center', va='center', fontsize=9, zorder=5)

def draw_dashed_arrow(ax, x1, y1, x2, y2, label, label_pos='above'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.2, linestyle='dashed', connectionstyle='arc3,rad=0'), zorder=4)
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    offset = 0.15 if label_pos == 'above' else -0.15
    ax.text(mid_x, mid_y + offset, label, ha='center', va='center', fontsize=9, zorder=5)

def draw_alt_frame(ax, x, y, width, height, conditions):
    rect = Rectangle((x, y), width, height, facecolor='none', edgecolor='black', linewidth=1.5, zorder=2)
    ax.add_patch(rect)
    ax.text(x + 0.15, y + height - 0.2, 'alt', fontsize=10, fontweight='bold', zorder=5)
    for i, cond in enumerate(conditions):
        if i > 0:
            cond_y = y + height - 0.5 - i * (height - 1) / len(conditions)
            ax.plot([x, x + width], [cond_y, cond_y], 'k--', linewidth=0.8, zorder=3)
        cond_y = y + height - 0.5 - i * (height - 1) / len(conditions)
        ax.text(x + 0.3, cond_y + 0.1, f'[{cond}]', fontsize=9, fontweight='bold', zorder=5)

def draw_destruction_x(ax, x, y, size=0.2):
    ax.plot([x - size, x + size], [y - size, y + size], 'r-', linewidth=2, zorder=5)
    ax.plot([x - size, x + size], [y + size, y - size], 'r-', linewidth=2, zorder=5)

# ============================================================
# DIAGRAM 6: AI Chat Sequence Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

ax.text(7, 9.5, 'Figure 3.5.5 AI Chat Sequence Diagram', ha='center', fontsize=12, fontweight='bold')

participants_top = [
    (2, 'User', 'actor'),
    (5, 'Chat Page', 'boundary'),
    (8, 'Chat Controller', 'control'),
    (11, 'Gemini API', 'entity'),
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
    (2, 7.5, 5, 7.5, '1. Type question', 'solid'),
    (5, 7.2, 8, 7.2, '1.1 Send message', 'solid'),
    (8, 6.9, 11, 6.9, '2. Build context', 'solid'),
    (11, 6.6, 8, 6.6, '2.1 Context ready', 'dashed'),
    (8, 6.3, 11, 6.3, '3. Call Gemini API', 'solid'),
    (11, 6.0, 8, 6.0, '3.1 AI response', 'dashed'),
    (8, 5.7, 5, 5.7, '4. Return answer', 'dashed'),
    (5, 5.4, 2, 5.4, '4.1 Display response', 'dashed'),
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
plt.savefig('diagrams_new/06_ai_chat_sequence.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created AI Chat Sequence Diagram")

# ============================================================
# DIAGRAM 7: Member Management Sequence Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

ax.text(7, 9.5, 'Figure 3.5.6 Member Management Sequence Diagram', ha='center', fontsize=12, fontweight='bold')

participants_top = [
    (2, 'Admin', 'actor'),
    (5, 'Member List', 'boundary'),
    (8, 'Member Controller', 'control'),
    (11, 'Names Model', 'entity'),
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
    (2, 7.5, 5, 7.5, '1. View members', 'solid'),
    (5, 7.2, 8, 7.2, '1.1 Get member list', 'solid'),
    (8, 6.9, 11, 6.9, '2. Query members', 'solid'),
    (11, 6.6, 8, 6.6, '2.1 Return members', 'dashed'),
    (8, 6.3, 5, 6.3, '3. Display list', 'dashed'),
    (5, 6.0, 2, 6.0, '3.1 Show members', 'dashed'),
    (2, 5.7, 5, 5.7, '4. Select member', 'solid'),
    (5, 5.4, 8, 5.4, '4.1 Edit request', 'solid'),
    (8, 5.1, 11, 5.1, '5. Update member', 'solid'),
    (11, 4.8, 8, 4.8, '5.1 Member updated', 'dashed'),
    (8, 4.5, 5, 4.5, '6. Refresh list', 'dashed'),
    (5, 4.2, 2, 4.2, '6.1 Show updated', 'dashed'),
]

for x1, y1, x2, y2, label, arrow_type in messages:
    if arrow_type == 'solid':
        draw_solid_arrow(ax, x1, y1, x2, y2, label)
    else:
        draw_dashed_arrow(ax, x1, y1, x2, y2, label)

draw_activation_bar(ax, 5, 7.5, 4.2, 0.12)
draw_activation_bar(ax, 8, 7.2, 4.5, 0.12)
draw_activation_bar(ax, 11, 6.9, 4.8, 0.12)

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
plt.savefig('diagrams_new/07_member_management_sequence.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Member Management Sequence Diagram")

# ============================================================
# DIAGRAM 8: Activity Diagram 1 - Session Creation
# ============================================================
fig, ax = plt.subplots(figsize=(10, 14))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

ax.text(5, 13.5, 'Figure 3.7.1 Session Creation Activity Diagram', ha='center', fontsize=12, fontweight='bold')

# Start node
start = Circle((5, 12.5), 0.2, facecolor='black', edgecolor='black')
ax.add_patch(start)

# Activities
activities = [
    (5, 11.5, 'Trainer logs in'),
    (5, 10.5, 'Navigate to Create Session'),
    (5, 9.5, 'Fill session details'),
    (5, 8.5, 'Select training space'),
    (5, 7.5, 'Set max trainees'),
    (5, 6.5, 'Submit session'),
]

for i, (x, y, label) in enumerate(activities):
    rect = FancyBboxPatch((x - 1.2, y - 0.3), 2.4, 0.6, boxstyle="round,pad=0.1",
                          facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x, y, label, ha='center', va='center', fontsize=9)
    
    if i < len(activities) - 1:
        ax.annotate('', xy=(x, activities[i+1][1] + 0.3), xytext=(x, y - 0.3),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

ax.annotate('', xy=(5, 11.8), xytext=(5, 12.3),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Decision node
decision = Circle((5, 5.5), 0.3, facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(decision)
ax.annotate('', xy=(5, 5.8), xytext=(5, 6.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Yes path
ax.annotate('', xy=(3, 5.5), xytext=(4.7, 5.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(3.5, 5.7, 'Yes', fontsize=8)

rect2 = FancyBboxPatch((1.5, 4.2), 3, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect2)
ax.text(3, 4.5, 'Notify trainees', ha='center', va='center', fontsize=9)

# No path
ax.annotate('', xy=(7, 5.5), xytext=(5.3, 5.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(6.5, 5.7, 'No', fontsize=8)

rect3 = FancyBboxPatch((5.5, 4.2), 3, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect3)
ax.text(7, 4.5, 'Show error', ha='center', va='center', fontsize=9)

# End node
end = Circle((5, 3), 0.2, facecolor='black', edgecolor='black', linewidth=2)
ax.add_patch(end)
end2 = Circle((5, 3), 0.15, facecolor='white', edgecolor='black', linewidth=2)
ax.add_patch(end2)

ax.annotate('', xy=(3, 3.2), xytext=(3, 4.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.annotate('', xy=(5, 3.2), xytext=(7, 4.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.annotate('', xy=(5, 3.2), xytext=(3, 3.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

plt.tight_layout()
plt.savefig('diagrams_new/08_activity_diagram_1.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Activity Diagram 1")

# ============================================================
# DIAGRAM 9: Activity Diagram 2 - Member Check-in
# ============================================================
fig, ax = plt.subplots(figsize=(10, 14))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')
ax.set_facecolor(BG_COLOR)

ax.text(5, 13.5, 'Figure 3.7.2 Member Check-in Activity Diagram', ha='center', fontsize=12, fontweight='bold')

start = Circle((5, 12.5), 0.2, facecolor='black', edgecolor='black')
ax.add_patch(start)

activities = [
    (5, 11.5, 'Member arrives at gym'),
    (5, 10.5, 'Show QR code'),
    (5, 9.5, 'Registrar scans QR'),
    (5, 8.5, 'System validates member'),
]

for i, (x, y, label) in enumerate(activities):
    rect = FancyBboxPatch((x - 1.2, y - 0.3), 2.4, 0.6, boxstyle="round,pad=0.1",
                          facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x, y, label, ha='center', va='center', fontsize=9)
    
    if i < len(activities) - 1:
        ax.annotate('', xy=(x, activities[i+1][1] + 0.3), xytext=(x, y - 0.3),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

ax.annotate('', xy=(5, 11.8), xytext=(5, 12.3),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Decision - membership active?
decision = Circle((5, 7.5), 0.3, facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(decision)
ax.annotate('', xy=(5, 7.8), xytext=(5, 8.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# Yes - check in
ax.annotate('', xy=(3, 7.5), xytext=(4.7, 7.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(3.5, 7.7, 'Active', fontsize=8)

rect2 = FancyBboxPatch((1.5, 6.2), 3, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect2)
ax.text(3, 6.5, 'Create attendance log', ha='center', va='center', fontsize=9)

# No - expired
ax.annotate('', xy=(7, 7.5), xytext=(5.3, 7.5),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(6.5, 7.7, 'Expired', fontsize=8)

rect3 = FancyBboxPatch((5.5, 6.2), 3, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect3)
ax.text(7, 6.5, 'Show renewal prompt', ha='center', va='center', fontsize=9)

# Decision - has open session?
decision2 = Circle((3, 5.2), 0.3, facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(decision2)
ax.annotate('', xy=(3, 5.5), xytext=(3, 6.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

# No - check in
ax.annotate('', xy=(1.5, 5.2), xytext=(2.7, 5.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(1.8, 5.4, 'No', fontsize=8)

rect4 = FancyBboxPatch((0.3, 4), 2.4, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect4)
ax.text(1.5, 4.3, 'Check in member', ha='center', va='center', fontsize=9)

# Yes - check out
ax.annotate('', xy=(4.5, 5.2), xytext=(3.3, 5.2),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.text(4.2, 5.4, 'Yes', fontsize=8)

rect5 = FancyBboxPatch((3.3, 4), 2.4, 0.6, boxstyle="round,pad=0.1",
                       facecolor='#F0F0F0', edgecolor='black', linewidth=1.2)
ax.add_patch(rect5)
ax.text(4.5, 4.3, 'Check out member', ha='center', va='center', fontsize=9)

# End
end = Circle((5, 3), 0.2, facecolor='black', edgecolor='black', linewidth=2)
ax.add_patch(end)
end2 = Circle((5, 3), 0.15, facecolor='white', edgecolor='black', linewidth=2)
ax.add_patch(end2)

ax.annotate('', xy=(5, 3.2), xytext=(1.5, 4),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.annotate('', xy=(5, 3.2), xytext=(7, 4),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
ax.annotate('', xy=(5, 3.2), xytext=(4.5, 4),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.2))

plt.tight_layout()
plt.savefig('diagrams_new/09_activity_diagram_2.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print("Created Activity Diagram 2")

print("\nCreated diagrams 6-9")
print("Continuing with class diagrams...")
