import os, time, cv2, mediapipe as mp

# ---- Settings ----
URL = os.getenv("IP_CAM_URL", "http://127.0.0.1:8080/video")
W, H = 640, 480
RECONNECT_DELAY = 1.0
USE_HOG = False            # set True to also try HOG people detector (slower but can help)

# ---- Camera helper ----
def open_cap():
    cap = cv2.VideoCapture(URL)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    return cap

cap = open_cap()
last = time.time()
fps = 0.0

# ---- Mediapipe Face ----
mp_face = mp.solutions.face_detection
fd = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6)

# ---- OpenCV Haar Cascades (upper body + full body) ----
casc_dir = cv2.data.haarcascades
upper_cascade = cv2.CascadeClassifier(os.path.join(casc_dir, "haarcascade_upperbody.xml"))
full_cascade  = cv2.CascadeClassifier(os.path.join(casc_dir, "haarcascade_fullbody.xml"))

# ---- Optional HOG people detector ----
if USE_HOG:
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def detect_face(frame_bgr):
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    res = fd.process(rgb)
    boxes = []
    if res.detections:
        h, w = frame_bgr.shape[:2]
        for det in res.detections:
            rb = det.location_data.relative_bounding_box
            x, y = int(rb.xmin*w), int(rb.ymin*h)
            ww, hh = int(rb.width*w), int(rb.height*h)
            boxes.append((x, y, ww, hh))
    return boxes

def detect_body_haar(frame_bgr):
    # Haar works on grayscale; scale down a bit for speed
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    # tuning: scaleFactor=1.05..1.2, minNeighbors=3..5
    upper = upper_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(60, 60))
    full  = full_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(60, 120))
    boxes = []
    for (x,y,w,h) in list(upper) + list(full):
        boxes.append((x,y,w,h))
    return boxes

def detect_body_hog(frame_bgr):
    # Downscale for speed
    scale = 0.75
    small = cv2.resize(frame_bgr, (0,0), fx=scale, fy=scale)
    rects, weights = hog.detectMultiScale(small, winStride=(8,8), padding=(8,8), scale=1.05)
    # Map back to original scale
    boxes = []
    for (x,y,w,h) in rects:
        boxes.append((int(x/scale), int(y/scale), int(w/scale), int(h/scale)))
    return boxes

while True:
    if not cap.isOpened():
        cap.release(); cap = open_cap(); time.sleep(RECONNECT_DELAY)

    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release(); cap = open_cap(); time.sleep(RECONNECT_DELAY); continue

    # --- Run detectors ---
    face_boxes = detect_face(frame)
    body_boxes = detect_body_haar(frame)
    if USE_HOG:
        body_boxes += detect_body_hog(frame)

    person_present = (len(face_boxes) > 0) or (len(body_boxes) > 0)

    # --- Draw ---
    for (x,y,w,h) in face_boxes:
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,255), 2)
    for (x,y,w,h) in body_boxes:
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,200,0), 2)

    # --- FPS/UI ---
    now = time.time()
    dt = max(1e-6, now - last); inst = 1.0/dt
    fps = 0.9*fps + 0.1*inst if fps>0 else inst
    last = now
    label = "PERSON" if person_present else "NO PERSON"
    cv2.putText(frame, f"{label} | FPS: {fps:.1f}", (10,22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0) if person_present else (0,0,255), 2, cv2.LINE_AA)

    cv2.imshow("Person detection (q=quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
