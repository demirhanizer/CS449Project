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
    "Turlar": ["Klasik Tur", "Modern Sanat Turu", "Mimari Tur", 
               "Tarih Tur", "Aile Turu", "Gece Turu", "Kısa Tur"],
    "Rehber Bilgisi": ["Sesli Rehber", "Yazılı Rehber", "Sanal Rehber", 
                       "Çocuk Rehberi", "Erişilebilirlik Rehberi", "Video Rehber", "Dil Seçenekleri"],
    "Sanat Eserleri": ["Resimler", "Heykeller", "Çağdaş Sanat", 
                       "Klasik Sanat", "Yerel Sanat", "Geçici Sergiler", "Koleksiyonlar"],
    "Etkinlikler": ["Atölyeler", "Konserler", "Konferanslar", 
                    "Sergi Açılışları", "Tiyatro", "Film Gösterimi", "Özel Etkinlikler"],
    "Ziyaretçi Rehberi": ["Haritalar", "Giriş Saatleri", "Kurallar", 
                          "Güvenlik Bilgisi", "Ulaşım Bilgisi", "Wi-Fi Kullanımı", "Engelliler İçin Bilgi"],
    "Kafeterya": ["Kahve Çeşitleri", "Tatlılar", "Sandviçler", 
                  "Vejetaryen Seçenekler", "Glütensiz Seçenekler", "İçecekler", "Menüler"],
    "Biletler": ["Yetişkin Bilet", "Öğrenci Bilet", "Aile Bilet", 
                 "Grup Bilet", "Sezonluk Bilet", "Ücretsiz Giriş Günleri", "Özel Biletler"],
    "Hediye Dükkanı": ["Posterler", "Kitaplar", "Kupa Bardaklar", 
                       "Tişörtler", "Anahtarlıklar", "Sanat Replikaları", "Oyuncaklar"]
}

current_menu = "main"
current_sub_menu_items = []
selected_item_index = 0
scroll_index = 0

# For slowing down scrolling
last_scroll_frame = 0
scroll_cooldown_frames = 40  # Adjust to slow down scrolling. Higher = slower.

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

def draw_listed_menu(items, scroll_index, hovered_index=None):
    """
    Draw the listed menu with scroll functionality.
    The hovered_index (if not None) highlights the hovered item.
    """
    menu_canvas.delete("menu")
    visible_items = items[scroll_index:scroll_index + 10]
    for i, item in enumerate(visible_items):
        y = 100 + i * 60
        # If this item is hovered, highlight it differently
        if hovered_index == i:
            fill_color = "#e0f7fa"  # a light highlight color
            outline_color = "blue"
        else:
            fill_color = "white"
            outline_color = "black"
        menu_canvas.create_rectangle(400, y, 800, y + 30, fill=fill_color, outline=outline_color, tags="menu")
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
    Detects a 'peace sign' gesture with stricter conditions.
    """
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

    if index_extended and middle_extended and similar_height and v_shape and ring_folded and pinky_folded and thumb_folded:
        return True
    return False

def detect_open_hand(landmarks):
    """
    Detect open hand gesture (all fingers extended).
    """
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
    global selected_item_index, current_menu, current_sub_menu_items, scroll_index

    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    wrist = landmarks[mp_hands.HandLandmark.WRIST]
    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
    pinky_tip = landmarks[mp_hands.HandLandmark.PINKY_TIP]
    ring_tip = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP]

    # Check for Pointing Gesture in main menu
    if index_tip.y < middle_tip.y:
        x = index_tip.x
        y = index_tip.y
        angle = math.degrees(math.atan2(y - 0.5, x - 0.5)) + 90
        angle = (angle + 360) % 360  # Normalize angle
        selected_item_index = int(len(menu_items) * angle / 360) % len(menu_items)
        return "Pointing Gesture"

    # Check for Open Hand Gesture (all fingers extended) to open submenu from main menu
    elif all([index_tip.y < wrist.y,
              middle_tip.y < wrist.y,
              thumb_tip.y < wrist.y,
              pinky_tip.y < wrist.y,
              ring_tip.y < wrist.y]):
        if current_menu == "main":
            selected_item = menu_items[selected_item_index]
            current_sub_menu_items = sub_menus[selected_item]
            current_menu = "submenu"
            scroll_index = 0
        return "Open Hand Gesture"

    return "Unknown Gesture"

def update_video():
    global selected_item_index, scroll_index, current_menu, current_sub_menu_items, last_scroll_frame, selection_made
    ret, frame = cap.read()
    if not ret:
        return

    # Flip the frame for a mirror effect
    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    menu_canvas.delete("camera")
    menu_canvas.delete("cursor")

    hovered_index = None
    selected_item = None

    # Track gestures from all hands
    # We'll need to know if there's another open hand besides the hovering hand for selection
    hand_landmarks_list = []

    if results.multi_hand_landmarks:
        # Collect all hands
        for hl in results.multi_hand_landmarks:
            hand_landmarks_list.append(hl.landmark)
        
            # El işaretlerini çerçeveye çiziyoruz
            mp_drawing.draw_landmarks(
                frame, hl, mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),  # Nokta stilleri
                mp_drawing.DrawingSpec(color=(250, 44, 250), thickness=2)  # Bağlantı stilleri
            )

        # Process gestures after collecting all
        for i, hand_landmarks in enumerate(hand_landmarks_list):
            gesture = recognize_gesture(hand_landmarks)
            thumb_gesture = detect_thumbs_gesture(hand_landmarks)

            if current_menu == "main":
                draw_circular_menu(selected_item_index)
                if gesture == "Pointing Gesture":
                    angle = (360 / len(menu_items)) * selected_item_index - 90
                    cursor_angle = math.radians(angle)
                    cursor_x = center_x + menu_radius * 0.7 * math.cos(cursor_angle)
                    cursor_y = center_y + menu_radius * 0.7 * math.sin(cursor_angle)
                    menu_canvas.create_oval(
                        cursor_x - 10, cursor_y - 10, cursor_x + 10, cursor_y + 10,
                        fill="blue", outline="black", tags="cursor"
                    )

            elif current_menu == "submenu":
                # Hover logic: use index finger of this hand
                index_tip = hand_landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                canvas_x = index_tip.x * 1200
                canvas_y = index_tip.y * 800
                visible_items = current_sub_menu_items[scroll_index:scroll_index + 10]

                # Determine hover
                temp_hover = None
                for j, item in enumerate(visible_items):
                    y = 100 + j * 40
                    if 400 <= canvas_x <= 800 and y <= canvas_y <= y + 30:
                        temp_hover = j
                        break

                # Only set hovered_index if we find an item hover;
                # If multiple hands could hover, let's say the last one we detect sets it.
                if temp_hover is not None:
                    hovered_index = temp_hover

                # Scroll only if enough frames have passed since last scroll
                # and only if thumbs up/down is detected
                current_frame_id = int(time.time() * 30)  # rough frame count using time
                # For smoother logic, you could use another global incrementer, but this suffices.
                if (current_frame_id - last_scroll_frame) > scroll_cooldown_frames:
                    if thumb_gesture == "Thumbs Up" and scroll_index > 0:
                        scroll_index -= 1
                        last_scroll_frame = current_frame_id
                    elif thumb_gesture == "Thumbs Down" and scroll_index < len(current_sub_menu_items) - 10:
                        scroll_index += 1
                        last_scroll_frame = current_frame_id

                # We'll decide on selection after checking all hands
        # After processing all hands, check selection condition
        selection_made = False
        if current_menu == "submenu":
            # Redraw with hovered item
            draw_listed_menu(current_sub_menu_items, scroll_index, hovered_index=hovered_index)

            # Check peace sign for going back
            for hl in hand_landmarks_list:
                if detect_peace_sign(hl):
                    current_menu = "main"
                    break

            # Seçim koşulu: hovered_index belirli ve açık el jesti var mı?

            if hovered_index is not None:  # Eğer bir öğe hover ediliyorsa
                # hovered_index ile eşleşen imlecin (index parmağının) hover yaptığı öğe
                absolute_index = scroll_index + hovered_index

                for hl in hand_landmarks_list:
                    index_tip = hl[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    canvas_x = index_tip.x * 1200
                    canvas_y = index_tip.y * 800

                    # İmlecin (cursor) hover yaptığı öğenin bölgesinde mi?
                    y = 100 + hovered_index * 60  # Her bir öğenin yüksekliğini kontrol et (40'tan 60'a çıkarıldı)
                    if 400 <= canvas_x <= 800 and y <= canvas_y <= y + 30:  # İmleç hover edilen öğenin bölgesinde mi?
                        if detect_open_hand(hl) and not selection_made:  # Eğer bu el açık el jesti yapıyorsa ve seçim yapılmamışsa
                            selected_item = current_sub_menu_items[absolute_index]  # Bu öğe seçilir
                            print(f"Seçilen öğe: {selected_item}")  # Konsola seçilen öğeyi yazdır
                            selected_text_label.configure(text=f"Selected: {selected_item}")  # Ekranda seçilen öğeyi göster
                            selection_made = True  # Artık seçim yapıldı, bu yüzden seçim işlemini durdur
                            break  # Seçim yapıldıktan sonra döngüden çık
                    else:
                        # El hover edilen bölgeden çıkarsa seçim tekrar aktif olur
                        selection_made = False  # Seçim tekrar aktif olur



    if selected_item is not None:
        selected_text_label.configure(text=f"Selected: {selected_item}")

    resized_frame = cv2.resize(frame, (450, 325))  # Burada frame_rgb yerine frame kullanıyoruz
    frame_image = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)))
    menu_canvas.create_image(400, 480, anchor=tk.NW, image=frame_image, tags="camera")
    menu_canvas.image = frame_image


    menu_canvas.tag_lower("camera")

    root.after(10, update_video)

# Initial menu drawing
draw_circular_menu(selected_item_index)
update_video()
root.mainloop()
cap.release()
cv2.destroyAllWindows()
