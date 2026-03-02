# services/face_logic.py
import face_recognition
import numpy as np
import cv2
from scipy.spatial import distance as dist

def encode_face(image_nparray):
    rgb_img = cv2.cvtColor(image_nparray, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_img)
    if len(encodings) > 0:
        return encodings[0].tolist()
    return None

# --- GEOMETRIC HELPERS ---
def get_ear(eye_points):
    """Eye Aspect Ratio (How open the eye is)"""
    # Vertical distances
    A = dist.euclidean(eye_points[1], eye_points[5])
    B = dist.euclidean(eye_points[2], eye_points[4])
    # Horizontal distance
    C = dist.euclidean(eye_points[0], eye_points[3])
    return (A + B) / (2.0 * C)

def get_mar(mouth_points):
    """Mouth Aspect Ratio (Vertical Openness)"""
    # Vertical distance (Lip Height) - points 14 (top) to 18 (bottom) inside mouth usually
    # But face_recognition gives 12 outer lip points (0-11) and 8 inner (12-19)
    # Let's use outer lip points for robustness: Top(3) to Bottom(9)
    A = dist.euclidean(mouth_points[3], mouth_points[9]) 
    # Horizontal distance (Mouth Width) - Left(0) to Right(6)
    B = dist.euclidean(mouth_points[0], mouth_points[6])
    return A / B  # Height / Width

# --- CHALLENGE LOGIC ---
def check_expression(landmarks, challenge_type):
    # Extract features
    left_eye = landmarks['left_eye']
    right_eye = landmarks['right_eye']
    top_lip = landmarks['top_lip']
    bottom_lip = landmarks['bottom_lip']
    left_eyebrow = landmarks['left_eyebrow']
    right_eyebrow = landmarks['right_eyebrow']

    # Get Ratios
    left_ear = get_ear(left_eye)
    right_ear = get_ear(right_eye)
    
    # Calculate Mouth metrics
    # Combine top and bottom lip lists to make one full loop
    full_lip_points = top_lip + bottom_lip
    
    # 1. SMILE (Wide Mouth, Corners Up)
    if challenge_type == "smile":
        # Metric: Horizontal Width vs Vertical Height
        mouth_width = dist.euclidean(top_lip[0], top_lip[6])
        mouth_height = dist.euclidean(top_lip[3], bottom_lip[3])
        
        # Smile Ratio: Width should be much larger than height
        # Normal mouth is ~1.5x wider than tall. Smile is > 2.5x.
        if mouth_width > (mouth_height * 2.0): 
            return True, "Smile Detected"
        return False, "Smile Wider (Show Teeth)"

    # 2. ANGER (Frown)
    elif challenge_type == "angry":
        # Metric: Eyebrows move closer together and down
        # 1. Distance between inner brow points
        brow_dist = dist.euclidean(left_eyebrow[-1], right_eyebrow[0])
        # 2. Reference: Width of an eye
        eye_width = dist.euclidean(left_eye[0], left_eye[3])
        
        # If brows are pinched (distance < eye_width), it's a frown
        if brow_dist < eye_width:
            return True, "Anger Detected"
        return False, "Frown Harder (Pinch Eyebrows)"

    # 3. SURPRISE / MOUTH OPEN (Replaces Hand on Lips)
    elif challenge_type == "surprise":
        # Metric: Vertical mouth opening
        mouth_height = dist.euclidean(top_lip[3], bottom_lip[3])
        mouth_width = dist.euclidean(top_lip[0], top_lip[6])
        
        # If height is close to width (making a circle/O-shape)
        if mouth_height > (mouth_width * 0.5): 
            return True, "Surprise/Open Mouth Detected"
        return False, "Open Mouth Wider (Say 'O')"

    # 4. WINK
    elif challenge_type == "wink":
        # Strategy: Check the DIFFERENCE. 
        # If one eye is 0.04 smaller than the other, it's a wink.
        diff = abs(left_ear - right_ear)
        
        # Debugging: Print this to your terminal to see your actual values
        print(f"Left Eye: {left_ear:.3f}, Right Eye: {right_ear:.3f}, Diff: {diff:.3f}")
        
        if diff > 0.04: 
            return True, "Wink Detected"
        return False, "Wink Harder (Close one eye tight)"

    return True, "Challenge Passed"

def verify_face_match_with_challenge(known_encoding, live_image_nparray, challenge_type="smile"):
    # 1. Encoding & Detection
    rgb_img = cv2.cvtColor(live_image_nparray, cv2.COLOR_BGR2RGB)
    landmarks_list = face_recognition.face_landmarks(rgb_img)
    
    if not landmarks_list:
        return False, "No face detected. (Ensure face is not covered)"
    
    # 2. CHECK LIVENESS
    if challenge_type != "none":
        is_live, live_msg = check_expression(landmarks_list[0], challenge_type)
        if not is_live:
            return False, f"Liveness Failed: {live_msg}"
    
    # 3. CHECK IDENTITY
    live_encoding = encode_face(live_image_nparray)
    if live_encoding is None:
        return False, "Face encoding failed."

    results = face_recognition.compare_faces([np.array(known_encoding)], np.array(live_encoding), tolerance=0.5)
    
    if results[0] == True:
        return True, "Verified Successfully"
    else:
        return False, "Face ID does not match registered user."