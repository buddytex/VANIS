import os, time, cv2, mediapipe as mp

URL = os.getenv("IP_CAM_URL", "http://127.0.0.1:8080/video")
W, H = 640, 480
RECONNECT_DELAY = 1.0

def open_cap():
    cap = cv2.VideoCapture(URL)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    return cap

cap = open_cap()
last = time.time()
fps = 0.0

mp_face = mp.solutions.face_detection
fd = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6)

while True:
    if not cap.isOpened():
        cap.release(); cap = open_cap(); time.sleep(RECONNECT_DELAY)

    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release(); cap = open_cap(); time.sleep(RECONNECT_DELAY); continue

    # Convert to RGB for Mediapipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = fd.process(rgb)

    face_found = False
    if res.detections:
        h, w = frame.shape[:2]
        for det in res.detections:
            bbox = det.location_data.relative_bounding_box
            x, y = int(bbox.xmin * w), int(bbox.ymin * h)
            ww, hh = int(bbox.width * w), int(bbox.height * h)
            cv2.rectangle(frame, (x, y), (x + ww, y + hh), (0, 255, 255), 2)
        face_found = True

    # FPS
    now = time.time()
    dt = max(1e-6, now - last)
    inst = 1.0 / dt
    fps = 0.9 * fps + 0.1 * inst if fps > 0 else inst
    last = now

    txt = "FACE" if face_found else "NO FACE"
    cv2.putText(frame, f"{txt} | FPS: {fps:.1f}", (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.LINE_AA)

    cv2.imshow("Face Detection Test (q=quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
