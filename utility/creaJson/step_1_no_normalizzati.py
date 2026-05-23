import cv2
import mediapipe as mp
import json
from pathlib import Path
import os

os.system('cls')

# ============================================================
# CONFIG
# ============================================================

VIDEO_PATH = "video/sconfitta.mp4"     # tuo video
OUTPUT_JSON = "json_no_normalizzati/sconfitta.json"    # output JSON

# ============================================================
# LANDMARK MAPS
# ============================================================

POSE_NAMES = {
    11: "left_shoulder", 12: "right_shoulder",
    13: "left_elbow",    14: "right_elbow",
    15: "left_wrist",    16: "right_wrist",
    23: "left_hip",      24: "right_hip",
    0: "nose"
}

HAND_NAMES = {
    0: "wrist",
    1: "thumb_cmc", 2: "thumb_mcp", 3: "thumb_ip", 4: "thumb_tip",
    5: "index_mcp", 6: "index_pip", 7: "index_dip", 8: "index_tip",
    9: "middle_mcp", 10: "middle_pip", 11: "middle_dip", 12: "middle_tip",
    13: "ring_mcp", 14: "ring_pip", 15: "ring_dip", 16: "ring_tip",
    17: "pinky_mcp", 18: "pinky_pip", 19: "pinky_dip", 20: "pinky_tip"
}

FACE_GROUPS = {
    "lips": [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 185, 40, 39, 37, 0, 267, 269, 270, 409],
    "left_eye": [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398],
    "right_eye": [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246],
    "left_eyebrow": [336, 285, 295, 282, 283],
    "right_eyebrow": [70, 63, 105, 66, 107],
    "nose_bridge": [1, 2, 98, 327]
}

# ============================================================
# UTILS
# ============================================================

def lm_to_xyz(lm):
    return [float(lm.x), float(lm.y), float(lm.z)]

# ============================================================
# INITIALIZATION
# ============================================================

mp_holistic = mp.solutions.holistic
mp_hands = mp.solutions.hands

holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=2,
    refine_face_landmarks=True
)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS)
frames_data = []
frame_idx = 0

# ============================================================
# MAIN LOOP
# ============================================================

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results_holistic = holistic.process(rgb)
    results_hands = hands.process(rgb)

    frame_json = {
        "f": frame_idx,
        "pose": {},
        "hands": {"left": {}, "right": {}},
        "face": {}
    }

    # ---------------- POSE ----------------
    if results_holistic.pose_landmarks:
        pose_raw = {}
        for idx, name in POSE_NAMES.items():
            lm = results_holistic.pose_landmarks.landmark[idx]
            pose_raw[name] = lm_to_xyz(lm)
        frame_json["pose"] = pose_raw

    # ---------------- HANDS ----------------
    if results_hands.multi_hand_landmarks and results_hands.multi_handedness:
        for hand_lm, handedness in zip(results_hands.multi_hand_landmarks,
                                       results_hands.multi_handedness):

            label = handedness.classification[0].label.lower()  # "left" / "right"
            hand_dict = {}

            for i, lm in enumerate(hand_lm.landmark):
                hand_dict[HAND_NAMES[i]] = lm_to_xyz(lm)

            frame_json["hands"][label] = hand_dict

    # ---------------- FACE ----------------
    '''
    if results_holistic.face_landmarks:
        all_face = results_holistic.face_landmarks.landmark
        for group_name, indices in FACE_GROUPS.items():
            frame_json["face"][group_name] = {
                f"v_{idx}": lm_to_xyz(all_face[idx])
                for idx in indices
            }
    '''
    frames_data.append(frame_json)
    frame_idx += 1

    if frame_idx % 30 == 0:
        print(f"Elaborazione frame: {frame_idx}")

cap.release()

# ============================================================
# EXPORT JSON
# ============================================================

output = {
    "meta": {
        "video": Path(VIDEO_PATH).name,
        "fps": fps,
        "total_frames": frame_idx,
        "model": "Holistic + Hands (no normalization)"
    },
    "frames": frames_data
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"\n✅ JSON generato correttamente!")
print(f"File salvato: {OUTPUT_JSON}")


