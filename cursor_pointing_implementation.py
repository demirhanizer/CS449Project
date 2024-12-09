import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import math

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Start video capture
cap = cv2.VideoCapture(1)

# Initialize Tkinter GUI
root = tk.Tk()
root.title("Circular Menu with Gesture Control")
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
scroll_index = 0

# Canvas for the circular menu and camera feed
menu_canvas = tk.Canvas(root, width=1200, height=800, bg="lightgray")
menu_canvas.pack()

# Text to display the selected option
selected_text_label = tk.Label(root, text="Selected: None", font=("Helvetica", 16), bg="lightgray", fg="black")
selected_text_label.place(x=10, y=750)

# Menu center and radius
center_x, center_y = 600, 250
menu_radius = 180


def draw_circular_menu(selected_index):
    """
    Draw the circular menu on the canvas with the highlighted item.
    """
    menu_canvas.delete("menu")
    angle_step = 360 / len(menu_items)
    for i, item in enumerate(menu_items):
        angle = math.radians(i * angle_step - 90)
        x = center_x + menu_radius * math.cos(angle)
        y = center_y + menu_radius * math.sin(angle)
        color = "red" if i == selected_index else "black"
        box_x1, box_y1 = x - 50, y - 20
        box_x2, box_y2 = x + 50, y + 20
        menu_canvas.create_rectangle(box_x1, box_y1, box_x2, box_y2, fill="white", outline=color, width=2, tags="menu")
        menu_canvas.create_text(x, y, text=item, fill=color, font=("Helvetica", 12, "bold"), tags="menu")


def draw_listed_menu(items, scroll_index):
    """
    Draw the listed menu with scroll functionality.
    """
    menu_canvas.delete("menu")
    visible_items = items[scroll_index:scroll_index + 10]
    for i, item in enumerate(visible_items):
        y = 100 + i * 40
        menu_canvas.create_rectangle(400, y, 800, y + 30, fill="white", outline="black", tags="menu")
        menu_canvas.create_text(600, y + 15, text=item, fill="black", font=("Helvetica", 12, "bold"), tags="menu")


def detect_thumbs_gesture(landmarks):
    """
    Detect thumbs up or thumbs down gestures for scrolling.
    """
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    thumb_ip = landmarks[mp_hands.HandLandmark.THUMB_IP]
    thumb_mcp = landmarks[mp_hands.HandLandmark.THUMB_MCP]
    thumb_cmc = landmarks[mp_hands.HandLandmark.THUMB_CMC]
    thumb_upwards = thumb_tip.y < thumb_ip.y < thumb_mcp.y < thumb_cmc.y
    thumb_downwards = thumb_tip.y > thumb_ip.y > thumb_mcp.y > thumb_cmc.y
    if thumb_upwards:
        return "Thumbs Up"
    if thumb_downwards:
        return "Thumbs Down"
    return "No Gesture"

def detect_peace_sign(landmarks):
    """
    Detects a 'peace sign' gesture with stricter conditions to avoid mixing it up
    with a pointing gesture.

    Conditions:
    - Index and middle fingertips both clearly above the wrist line.
    - Index and middle fingertips at roughly the same vertical height 
      (so both are equally extended, not one much higher than the other).
    - A sufficient horizontal separation between index and middle fingertips 
      to form a distinct "V".
    - Ring, pinky, and thumb below the wrist line, folded in.
    """
    wrist_y = landmarks[mp_hands.HandLandmark.WRIST].y

    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]

    # Margins and thresholds - adjust as needed
    margin_y = 0.03  # How far above wrist index/middle must be
    min_finger_separation = 0.04  # Horizontal gap needed between index and middle
    vertical_threshold = 0.03  # Max vertical difference allowed between index and middle tips

    # Check that index and middle are well above the wrist
    index_extended = index_tip.y < (wrist_y - margin_y)
    middle_extended = middle_tip.y < (wrist_y - margin_y)

    # Check vertical alignment - they should be at similar height
    similar_height = abs(index_tip.y - middle_tip.y) < vertical_threshold

    # Check horizontal separation
    v_shape = abs(index_tip.x - middle_tip.x) > min_finger_separation

    # Other fingers folded (below wrist or not extended significantly)
    ring_folded = ring_tip.y > wrist_y
    pinky_folded = pinky_tip.y > wrist_y
    thumb_folded = thumb_tip.y > wrist_y

    # All conditions must be met
    if index_extended and middle_extended and similar_height and v_shape and ring_folded and pinky_folded and thumb_folded:
        return True

    return False




def recognize_gesture(landmarks):
    global selected_item_index, current_menu, current_sub_menu_items, scroll_index

    # Extract necessary landmarks
    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]

    # Check for Pointing Gesture
    if index_tip.y < middle_tip.y:  # Index finger is raised more than middle
        x = index_tip.x
        y = index_tip.y
        angle = math.degrees(math.atan2(y - 0.5, x - 0.5)) + 90
        angle = (angle + 360) % 360  # Normalize angle
        selected_item_index = int(len(menu_items) * angle / 360) % len(menu_items)
        return "Pointing Gesture"

    # Check for Open Hand Gesture (all fingers extended)
    elif all([index_tip.y < wrist.y,
              middle_tip.y < wrist.y,
              thumb_tip.y < wrist.y,
              pinky_tip.y < wrist.y,
              ring_tip.y < wrist.y]):
        if current_menu == "main":
            # Open sub-menu
            selected_item = menu_items[selected_item_index]
            current_sub_menu_items = sub_menus[selected_item]
            current_menu = "submenu"
            scroll_index = 0
        return "Open Hand Gesture"

    return "Unknown Gesture"


def update_video():
    global selected_item_index, scroll_index, current_menu
    ret, frame = cap.read()
    if not ret:
        return

    # Flip the frame for a mirror effect
    frame = cv2.flip(frame, 1)

    # Convert the frame to RGB for Mediapipe processing
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    # Clear previous camera frame and cursor
    menu_canvas.delete("camera")
    menu_canvas.delete("cursor")

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            gesture = recognize_gesture(hand_landmarks.landmark)
            thumb_gesture = detect_thumbs_gesture(hand_landmarks.landmark)

            # If in main menu
            if current_menu == "main":
                draw_circular_menu(selected_item_index)
                if gesture == "Pointing Gesture":
                    # Draw cursor in main menu
                    angle = (360 / len(menu_items)) * selected_item_index - 90
                    cursor_angle = math.radians(angle)
                    cursor_x = center_x + menu_radius * 0.7 * math.cos(cursor_angle)
                    cursor_y = center_y + menu_radius * 0.7 * math.sin(cursor_angle)
                    menu_canvas.create_oval(
                        cursor_x - 10, cursor_y - 10, cursor_x + 10, cursor_y + 10,
                        fill="blue", outline="black", tags="cursor"
                    )

            # If in submenu
            elif current_menu == "submenu":
                # Scroll with thumbs
                if thumb_gesture == "Thumbs Up" and scroll_index > 0:
                    scroll_index -= 1
                elif thumb_gesture == "Thumbs Down" and scroll_index < len(current_sub_menu_items) - 10:
                    scroll_index += 1

                draw_listed_menu(current_sub_menu_items, scroll_index)

                # Detect peace sign to go back to main menu
                if detect_peace_sign(hand_landmarks.landmark):
                    current_menu = "main"

                # Pointing gesture in submenu shows cursor but no back button now
                if gesture == "Pointing Gesture":
                    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    canvas_x = index_tip.x * 1200
                    canvas_y = index_tip.y * 800
                    menu_canvas.create_oval(
                        canvas_x - 10, canvas_y - 10, canvas_x + 10, canvas_y + 10,
                        fill="blue", outline="black", tags="cursor"
                    )

    resized_frame = cv2.resize(frame_rgb, (450, 325))
    frame_image = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))
    menu_canvas.create_image(400, 480, anchor=tk.NW, image=frame_image, tags="camera")
    menu_canvas.image = frame_image

    # Kamera görüntüsünü arkaya al
    menu_canvas.tag_lower("camera")

    root.after(10, update_video)


# Initial menu drawing
draw_circular_menu(selected_item_index)
update_video()
root.mainloop()
cap.release()
cv2.destroyAllWindows()
