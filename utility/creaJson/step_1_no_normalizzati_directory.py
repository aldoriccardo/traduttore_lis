import cv2
import mediapipe as mp
import json
from pathlib import Path
import os
import numpy as np

os.system('cls')

# ============================================================
# CONFIG
# ============================================================

VIDEO_DIR = "video"
OUTPUT_DIR = "json_output"
SMOOTH_ALPHA = 0.6          # smoothing EMA
ANTI_JITTER_ALPHA = 0.4     # più forte su gomito/polso

os.makedirs(OUTPUT_DIR, exist_ok=True)

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

def lm_to_np(lm):
    return np.array([lm.x, lm.y, lm.z], dtype=np.float32)

def ema(prev, new, alpha):
    if prev is None:
        return new
    return alpha * new + (1 - alpha) * prev

# ============================================================
# MEDIAPIPE INIT
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

# ============================================================
# PROCESSA TUTTI I VIDEO NELLA DIRECTORY
# ============================================================

videos = list(Path(VIDEO_DIR).glob("*.mp4"))

for video_path in videos:
    print(f"\n🎥 Elaboro: {video_path.name}")

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames_data = []
    frame_idx = 0

    # buffer smoothing
    smooth_pose = {}
    smooth_hands = {"left": {}, "right": {}}
    smooth_face = {g: {} for g in FACE_GROUPS}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results_hol = holistic.process(rgb)
        results_h = hands.process(rgb)

        frame_json = {
            "f": frame_idx,
            "pose": {},
            "hands": {"left": {}, "right": {}},
            "face": {}
        }

        # ---------------- POSE ----------------
        if results_hol.pose_landmarks:
            for idx, name in POSE_NAMES.items():
                lm = lm_to_np(results_hol.pose_landmarks.landmark[idx])

                alpha = ANTI_JITTER_ALPHA if ("wrist" in name or "elbow" in name) else SMOOTH_ALPHA
                smooth_pose[name] = ema(smooth_pose.get(name), lm, alpha)

                frame_json["pose"][name] = smooth_pose[name].tolist()

        # ---------------- HANDS ----------------
        if results_h.multi_hand_landmarks and results_h.multi_handedness:
            for hand_lm, handedness in zip(results_h.multi_hand_landmarks,
                                           results_h.multi_handedness):

                label = handedness.classification[0].label.lower()

                for i, lm in enumerate(hand_lm.landmark):
                    name = HAND_NAMES[i]
                    lm_np = lm_to_np(lm)

                    smooth_hands[label][name] = ema(
                        smooth_hands[label].get(name),
                        lm_np,
                        SMOOTH_ALPHA
                    )

                frame_json["hands"][label] = {
                    k: v.tolist() for k, v in smooth_hands[label].items()
                }

        # ---------------- FACE ----------------
        if results_hol.face_landmarks:
            all_face = results_hol.face_landmarks.landmark

            for group_name, indices in FACE_GROUPS.items():
                group_dict = {}

                for idx in indices:
                    lm = lm_to_np(all_face[idx])

                    smooth_face[group_name][idx] = ema(
                        smooth_face[group_name].get(idx),
                        lm,
                        SMOOTH_ALPHA
                    )

                    group_dict[f"v_{idx}"] = smooth_face[group_name][idx].tolist()

                frame_json["face"][group_name] = group_dict

        frames_data.append(frame_json)
        frame_idx += 1

    cap.release()

    # ============================================================
    # CALIBRAZIONE SCALA CORPO
    # ============================================================

    print("📏 Calibrazione scala...")

    distances = []
    for f in frames_data:
        pose = f["pose"]
        if "left_shoulder" in pose and "left_hip" in pose:
            d = np.linalg.norm(np.array(pose["left_shoulder"]) - np.array(pose["left_hip"]))
            distances.append(d)

    if distances:
        scale = float(np.mean(distances))

        for f in frames_data:
            for k in f["pose"]:
                f["pose"][k] = (np.array(f["pose"][k]) / scale).tolist()

            for side in ["left", "right"]:
                for k in f["hands"][side]:
                    f["hands"][side][k] = (np.array(f["hands"][side][k]) / scale).tolist()

            for group in f["face"]:
                for k in f["face"][group]:
                    f["face"][group][k] = (np.array(f["face"][group][k]) / scale).tolist()

    # ============================================================
    # SALVA JSON
    # ============================================================

    output_json = Path(OUTPUT_DIR) / f"{video_path.stem}.json"

    output = {
        "meta": {
            "video": video_path.name,
            "fps": fps,
            "total_frames": frame_idx,
            "model": "Holistic + Hands + Face (smoothed, scaled)"
        },
        "frames": frames_data
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Salvato: {output_json}")

