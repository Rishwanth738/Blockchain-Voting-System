# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.face_logic import encode_face, verify_face_match_with_challenge
from database import save_voter, get_voter
import cv2
import numpy as np
import uuid
import socket

app = FastAPI()

# --- 1. ENABLE CORS (Required for Kiosk/Mobile access) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. SESSION STORE (In-Memory) ---
# Format: { "session_uuid": { "status": "pending", "wallet": None, "voter_id": None } }
session_store = {}

# --- 3. HELPER: GET LOCAL IP ---
def get_local_ip():
    """Auto-detects your laptop's Wi-Fi IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ================= KIOSK & SESSION ROUTES =================

@app.get("/create-session")
def create_session():
    """
    KIOSK START: Generates a unique QR code link for the current voter.
    """
    session_id = str(uuid.uuid4())
    local_ip = get_local_ip()
    
    # Initialize session
    session_store[session_id] = {"status": "pending", "wallet": None}
    
    # This is the URL your phone should open (points to Frontend or Docs)
    # For now, pointing to API Docs for testing
    mobile_link = f"http://{local_ip}:8000/docs" 
    
    return {
        "session_id": session_id,
        "qr_code_url": mobile_link,
        "raw_ip_link": f"http://{local_ip}:8000",
        "message": "Display this QR code on the Kiosk."
    }

@app.get("/session-status/{session_id}")
def check_session(session_id: str):
    """
    KIOSK POLLING: Frontend checks this every 2 seconds.
    """
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
    
    return session_store[session_id]

@app.post("/cleanup-session")
def cleanup_session(session_id: str = Form(...)):
    """
    KIOSK CLEANUP: Call this immediately after the vote is cast.
    """
    if session_id in session_store:
        del session_store[session_id]
        return {"status": "success", "message": "Session cleared. Kiosk ready."}
    return {"status": "success", "message": "Session already gone."}

# ================= VERIFICATION ROUTES =================

@app.post("/mobile-verify")
async def mobile_verify(
    session_id: str = Form(...),
    voter_id: str = Form(...),
    challenge_type: str = Form(...),
    file: UploadFile = File(...)
):
    """
    PHONE ACTION: User uploads selfie from phone to verify session.
    """
    # 1. Validate Session
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Invalid or Expired Session")

    # 2. Get User Data
    user_data = get_voter(voter_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="Invalid Voter ID")
    
    if user_data.get("has_voted"):
        raise HTTPException(status_code=403, detail="User has already voted.")

    # 3. Process Image
    image_data = await file.read()
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 4. Biometric & Liveness Check
    stored_encoding = user_data["face_encoding"]
    is_match, message = verify_face_match_with_challenge(stored_encoding, img, challenge_type)

    if is_match:
        # SUCCESS: Update the session so the Kiosk knows!
        session_store[session_id]["status"] = "verified"
        session_store[session_id]["wallet"] = user_data["wallet_address"]
        session_store[session_id]["voter_id"] = voter_id
        
        return {"status": "success", "message": "Verified! Check the Kiosk screen."}
    else:
        raise HTTPException(status_code=401, detail=message)

# ================= STANDARD ROUTES (Admin/Debug) =================

@app.get("/")
def home():
    return {"message": "Voting System API Online", "ip": get_local_ip()}

@app.post("/register")
async def register_user(
    voter_id: str = Form(...),
    name: str = Form(...),
    wallet_address: str = Form(...),
    file: UploadFile = File(...)
):
    if get_voter(voter_id):
        raise HTTPException(status_code=400, detail="Voter ID already registered")

    image_data = await file.read()
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    encoding = encode_face(img)
    if not encoding:
        raise HTTPException(status_code=400, detail="No face detected.")

    if save_voter(voter_id, name, wallet_address, encoding):
        return {"status": "success", "message": f"Voter {name} registered."}
    else:
        raise HTTPException(status_code=500, detail="Database Error")

# Standalone verify (if not using Kiosk flow)
@app.post("/verify")
async def verify_user(
    voter_id: str = Form(...),
    challenge_type: str = Form(...), 
    file: UploadFile = File(...)
):
    user_data = get_voter(voter_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="Invalid Voter ID")
    
    if user_data.get("has_voted"):
        raise HTTPException(status_code=403, detail="User has already voted.")

    image_data = await file.read()
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    stored_encoding = user_data["face_encoding"]
    is_match, message = verify_face_match_with_challenge(stored_encoding, img, challenge_type)

    if is_match:
        return {
            "status": "success", 
            "verified": True, 
            "wallet_address": user_data["wallet_address"],
            "message": message
        }
    else:
        raise HTTPException(status_code=401, detail=message)