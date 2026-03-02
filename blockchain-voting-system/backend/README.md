# Biometric Authentication API Documentation

**Version:** 1.0.0  
**Base URL:** `http://<YOUR_LOCAL_IP>:8000`  
**Content-Type:** `multipart/form-data` (for file uploads)

---

## 1. System Overview

This API provides **Biometric Identity Verification** for a decentralized voting system. It supports:

- **1:1 Face Matching** — Verifies a live user against a registered Voter ID
- **Liveness Detection** — Challenge–response validation (Smile, Wink, Angry, Surprise)
- **Cross-Device Handoff** — Desktop Kiosk session verified via user's mobile device

---

## 2. Integration Workflow (Order of Execution)

**Scenario: Kiosk Voting Booth**

1. Kiosk calls `GET /create-session` to generate a QR code
2. Kiosk polls `GET /session-status/{session_id}` every 2 seconds
3. User scans QR code on mobile and uploads selfie via `POST /mobile-verify`
4. API verifies face + liveness and updates session status
5. Kiosk unlocks voting screen upon verification
6. After voting, Kiosk calls `POST /cleanup-session` to reset the booth

---

## 3. API Endpoints

### A. Kiosk Session Management

#### 1. Create New Session

**Method:** `GET`  
**Endpoint:** `/create-session`  
**Description:** Initializes a new voting session and returns a QR code link.

**Response (200 OK):**

```json
{
  "session_id": "550e8400-e29b-...",
  "qr_code_url": "http://192.168.1.5:8000/docs...",
  "message": "Display this QR code on the Kiosk."
}
```

---

#### 2. Check Session Status (Polling)

**Method:** `GET`  
**Endpoint:** `/session-status/{session_id}`  
**Description:** Polled by the Desktop Kiosk to determine whether the user has completed biometric verification on their mobile device.

**Path Parameter:**
- `session_id` (string) — The ID returned by `/create-session`

**Response (Pending):**

```json
{
  "status": "pending",
  "wallet": null
}
```

**Response (Verified):**

```json
{
  "status": "verified",
  "wallet": "0xABC123...",
  "voter_id": "IND-001"
}
```

---

#### 3. Mobile Verification (The "Selfie" Step)

**Method:** `POST`  
**Endpoint:** `/mobile-verify`  
**Description:** Called by the mobile device to upload a live selfie for face and liveness verification.

**Form Data (Body):**
- `session_id` (string) — The active session ID from the QR code
- `voter_id` (string) — The ID entered by the user (e.g., "IND-001")
- `challenge_type` (string) — The liveness action performed. Options: `smile`, `wink`, `angry`, `surprise`
- `file` (file) — The live image file (jpg/png)

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Verified! Check the Kiosk screen."
}
```

**Response (401 Unauthorized):**

```json
{
  "detail": "Liveness Failed: Frown Harder"
}
```

---

#### 4. Cleanup Session

**Method:** `POST`  
**Endpoint:** `/cleanup-session`  
**Description:** **CRITICAL.** Must be called immediately after a vote is cast to reset the kiosk for the next user.

**Form Data (Body):**
- `session_id` (string) — The session to delete

**Response:**

```json
{
  "status": "success",
  "message": "Session cleared. Kiosk ready."
}
```

---

### B. Admin & Setup

#### 5. Register Voter

**Method:** `POST`  
**Endpoint:** `/register`  
**Description:** Onboards a new user. Converts their face photo into a secure vector and stores it in MongoDB.

**Form Data (Body):**
- `voter_id` (string) — Unique ID (e.g., "IND-001")
- `name` (string) — Full name
- `wallet_address` (string) — Blockchain wallet address
- `file` (file) — A clear, front-facing photo

**Response:**

```json
{
  "status": "success",
  "message": "Voter John Doe registered."
}
```

---

### C. Debugging (Standalone)

#### 6. Verify User (Direct)

**Method:** `POST`  
**Endpoint:** `/verify`  
**Description:** Used for testing verification without the full Kiosk/Mobile session flow.

**Form Data:**
- `voter_id`
- `challenge_type`
- `file`

**Response:**

```json
{
  "verified": true
}
```

---

## 4. Liveness Challenge Reference

The frontend should prompt the user to perform one of these actions before taking the photo. Pass the corresponding keyword in the `challenge_type` field.

| UI Prompt | `challenge_type` | Validation Logic |
|-----------|-----------------|-----------------|
| "Please Smile!" | `smile` | Mouth width > height × 1.8 |
| "Look Angry!" | `angry` | Eyebrow distance < eye width |
| "Open Your Mouth!" | `surprise` | Mouth height > width × 0.45 |
| "Wink One Eye!" | `wink` | Difference in eye openness > 0.04 |
| (Testing Only) | `none` | Skips liveness, checks face ID only |

---

## 5. How to Run Locally

### Install Dependencies

```bash
pip install fastapi uvicorn pymongo opencv-python face-recognition numpy scipy qrcode
```

### Start Server (Network Accessible)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Find IP Address

The server terminal will print your local IP (e.g., `192.168.1.5`). Use this IP for mobile testing, **not localhost**.

---