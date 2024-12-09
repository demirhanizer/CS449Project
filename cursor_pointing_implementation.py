import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import math
import time

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Start video capture
cap = cv2.VideoCapture(0)

# Initialize Tkinter GUI
root = tk.Tk()
root.title("Menu Navigation with Gestures")
root.geometry("1200x800")

# Circular menu items
menu_items = [
    "Turlar", "Rehber Bilgisi", "Sanat Eserleri",
    "Etkinlikler", "Ziyaretçi Rehberi", "Kafeterya",
    "Biletler", "Hediye Dükkanı"
]

# Submenus for each main menu item
sub_menus = {
    "Turlar": [f"Tur {i}" for i in range(1, 21)],
    "Rehber Bilgisi": [f"Rehber {i}" for i in range(1, 21)],
    "Sanat Eserleri": [f"Eser {i}" for i in range(1, 21)],
    "Etkinlikler": [f"Etkinlik {i}" for i in range(1, 21)],
    "Ziyaretçi Rehberi": [f"Rehberlik Bilgisi {i}" for i in range(1, 21)],
    "Kafeterya": [f"Menü {i}" for i in range(1, 21)],
    "Biletler": [f"Bilet Tipi {i}" for i in range(1, 21)],
    "Hediye Dükkanı": [f"Ürün {i}" for i in range(1, 21)],
}

current_menu = "main"
current_sub_menu_items = []
selected_item_index = 0

# Scrolling and highlighting in submenu
scroll_index = 0
hovered_index = 0  # tracks which item in the visible window is highlighted

# For slowing down scrolling and highlight movement
last_scroll_frame = 0
scroll_cooldown_frames = 10  # lower this for a bit faster response

menu_canvas = tk.Canvas(root, width=1200, height=800, bg="lightgray")
menu_canvas.pack()

selected_text_label = tk.Label(root, text="Selected: None", font=("Helvetica", 16), bg="lightgray", fg="black")
selected_text_label.place(x=10, y=750)

center_x, center_y = 600, 250
menu_radius = 180

def draw_circular_menu(selected_index):
    menu_canvas.delete("menu")
    angle_step = 360 / len(menu_items)
    for i, item in enumerate(menu_items):
        angle = math.radians(i * angle_step - 90)
        x = center_x + menu_radius * math.cos(angle)
        y = center_y + menu_radius * math.sin(angle)
        color = "red" if i == selected_index else "black"
        menu_canvas.create_rectangle(x - 50, y - 20, x + 50, y + 20, fill="white", outline=color, width=2, tags="menu")
        menu_canvas.create_text(x, y, text=item, fill=color, font=("Helvetica", 12, "bold"), tags="menu")

def draw_listed_menu(items, scroll_index, hovered_index=None):
    menu_canvas.delete("menu")
    visible_items = items[scroll_index:scroll_index + 10]
    for i, item in enumerate(visible_items):
        y = 100 + i * 40
        if hovered_index == i:
            fill_color = "#e0f7fa"
            outline_color = "blue"
        else:
            fill_color = "white"
            outline_color = "black"
        menu_canvas.create_rectangle(400, y, 800, y + 30, fill=fill_color, outline=outline_color, tags="menu")
        menu_canvas.create_text(600, y + 15, text=item, fill="black", font=("Helvetica", 12, "bold"), tags="menu")

def detect_thumbs_gesture(landmarks):
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    thumb_ip = landmarks[mp_hands.HandLandmark.THUMB_IP]
    thumb_mcp = landmarks[mp_hands.HandLandmark.THUMB_MCP]
    thumb_cmc = landmarks[mp_hands.HandLandmark.THUMB_CMC]
    thumb_upwards = thumb_tip.y < thumb_ip.y < thumb_mcp.y < thumb_cmc.y
    thumb_downwards = thumb_tip.y > thumb_ip.y > thumb_mcp.y > thumb_cmc.y
    if thumb_upwards:
        return "Thumbs Up"
    elif thumb_downwards:
        return "Thumbs Down"
    return "No Gesture"

def detect_peace_sign(landmarks):
    wrist_y = landmarks[mp_hands.HandLandmark.WRIST].y
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    margin_y = 0.03
    min_finger_separation = 0.04
    vertical_threshold = 0.03

    index_extended = index_tip.y < (wrist_y - margin_y)
    middle_extended = middle_tip.y < (wrist_y - margin_y)
    similar_height = abs(index_tip.y - middle_tip.y) < vertical_threshold
    v_shape = abs(index_tip.x - middle_tip.x) > min_finger_separation

    ring_folded = ring_tip.y > wrist_y
    pinky_folded = pinky_tip.y > wrist_y
    thumb_folded = thumb_tip.y > wrist_y

    return (index_extended and middle_extended and similar_height and v_shape and
            ring_folded and pinky_folded and thumb_folded)

def detect_open_hand(landmarks):
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    return (index_tip.y < wrist.y and
            middle_tip.y < wrist.y and
            ring_tip.y < wrist.y and
            pinky_tip.y < wrist.y and
            thumb_tip.y < wrist.y)

def recognize_gesture(landmarks):
    # Open hand gesture in main menu opens submenu
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    if all([index_tip.y < wrist.y,
            middle_tip.y < wrist.y,
            thumb_tip.y < wrist.y,
            pinky_tip.y < wrist.y,
            ring_tip.y < wrist.y]):
        if current_menu == "main":
            selected_item = menu_items[selected_item_index]
            set_submenu(sub_menus[selected_item])
        return "Open Hand Gesture"
    return "Unknown Gesture"

def set_submenu(items):
    global current_menu, current_sub_menu_items, scroll_index, hovered_index
    current_sub_menu_items = items
    current_menu = "submenu"
    scroll_index = 0
    hovered_index = 0  # Start highlighting the first visible item

def move_highlight(direction):
    # direction: 'up' or 'down'
    # Attempt to move hovered_index and scroll_index accordingly
    global hovered_index, scroll_index, last_scroll_frame
    current_frame_id = int(time.time() * 30)
    if (current_frame_id - last_scroll_frame) <= scroll_cooldown_frames:
        return

    visible_count = len(current_sub_menu_items[scroll_index:scroll_index+10])
    if visible_count == 0:
        return

    if direction == 'up':
        if hovered_index > 0:
            hovered_index -= 1
        else:
            # hovered at top visible item, try scrolling up if possible
            if scroll_index > 0:
                scroll_index -= 1
                # Keep hovered_index at the same position after scroll
            # else no movement
    elif direction == 'down':
        if hovered_index < visible_count - 1:
            hovered_index += 1
        else:
            # hovered at bottom visible item, try scrolling down if possible
            if scroll_index + 10 < len(current_sub_menu_items):
                scroll_index += 1
                # hovered_index stays at bottom (since we scrolled)
            # else no movement

    last_scroll_frame = current_frame_id

def update_video():
    global selected_item_index, scroll_index, current_menu, current_sub_menu_items, hovered_index
    ret, frame = cap.read()
    if not ret:
        root.after(10, update_video)
        return

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    menu_canvas.delete("camera")

    selected_item = None
    thumb_gesture_detected = "No Gesture"

    hand_landmarks_list = []

    if results.multi_hand_landmarks:
        for hl in results.multi_hand_landmarks:
            hand_landmarks_list.append(hl.landmark)

        # Detect thumbs gesture if any hand shows it
        for hand_landmarks in hand_landmarks_list:
            tg = detect_thumbs_gesture(hand_landmarks)
            if tg in ("Thumbs Up", "Thumbs Down"):
                thumb_gesture_detected = tg
                break

        # Process each hand gesture recognition (for open hand in main menu)
        for hand_landmarks in hand_landmarks_list:
            gesture = recognize_gesture(hand_landmarks)
            # main menu displayed
            if current_menu == "main":
                draw_circular_menu(selected_item_index)

    if current_menu == "submenu":
        # Check if any hand is open (all fingers extended)
        any_hand_open = False
        for hl in hand_landmarks_list:
            if detect_open_hand(hl):
                any_hand_open = True
                break

        # In submenu, we use thumbs up/down to move highlight,
        # but only if no hand is fully open.
        if not any_hand_open:
            if thumb_gesture_detected == "Thumbs Up":
                move_highlight('up')
            elif thumb_gesture_detected == "Thumbs Down":
                move_highlight('down')

        draw_listed_menu(current_sub_menu_items, scroll_index, hovered_index=hovered_index)

        # Check peace sign to return to main menu
        if hand_landmarks_list:
            for hl in hand_landmarks_list:
                if detect_peace_sign(hl):
                    current_menu = "main"
                    break

        # If hovered item and thumbs gesture, check if both hands open for selection
        if hovered_index is not None and hovered_index >= 0 and hovered_index < len(current_sub_menu_items[scroll_index:scroll_index+10]):
            if thumb_gesture_detected in ("Thumbs Up", "Thumbs Down"):
                open_count = 0
                for hl in hand_landmarks_list:
                    if detect_open_hand(hl):
                        open_count += 1
                if open_count >= 2:
                    absolute_index = scroll_index + hovered_index
                    selected_item = current_sub_menu_items[absolute_index]


    if selected_item is not None:
        selected_text_label.configure(text=f"Selected: {selected_item}")

    resized_frame = cv2.resize(frame_rgb, (450, 325))
    frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))
    menu_canvas.create_image(400, 480, anchor=tk.NW, image=frame_image, tags="camera")
    menu_canvas.image = frame_image
    menu_canvas.tag_lower("camera")

    root.after(10, update_video)

draw_circular_menu(selected_item_index)
update_video()
root.mainloop()
cap.release()
cv2.destroyAllWindows()
