import cv2, time
import mediapipe as mp
from collections import deque

# ==== CONFIG ====
IP_CAM_URL = "http://192.168.43.205:8080/video"
DETECT_W = 640

# ==== Helpers ====
def iou(a, b):
    ax1, ay1, aw, ah = a; ax2, ay2 = ax1+aw, ay1+ah
    bx1, by1, bw, bh = b; bx2, by2 = bx1+bw, by1+bh
    inter = max(0, min(ax2,bx2)-max(ax1,bx1)) * max(0, min(ay2,by2)-max(ay1,by1))
    ua = aw*ah + bw*bh - inter
    return inter/ua if ua>0 else 0.0

def nms(boxes, iou_thresh=0.4):
    if not boxes: return []
    boxes = sorted(boxes, key=lambda b: b[2]*b[3], reverse=True)
    keep=[]
    while boxes:
        b = boxes.pop(0)
        keep.append(b)
        boxes = [x for x in boxes if iou(b,x) < iou_thresh]
    return keep

# ==== Init detectors ====
mp_face = mp.solutions.face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.6)
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
upper = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_upperbody.xml")
fullb = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_fullbody.xml")
body_history = deque(maxlen=6)

def detect_faces(frame):
    faces_out = []
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = mp_face.process(rgb)
    if res.detections:
        for det in res.detections:
            bbox = det.location_data.relative_bounding_box
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            ww = int(bbox.width * w)
            hh = int(bbox.height * h)
            faces_out.append((x,y,ww,hh))
    return faces_out

def detect_bodies(frame_bgr):
    h, w = frame_bgr.shape[:2]
    scale = DETECT_W / float(w)
    small = cv2.resize(frame_bgr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

    gray_s = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    haar_upper = upper.detectMultiScale(gray_s, scaleFactor=1.12, minNeighbors=5,
                                        minSize=(int(50*scale), int(70*scale)))
    haar_full  = fullb.detectMultiScale(gray_s, scaleFactor=1.08, minNeighbors=5,
                                        minSize=(int(50*scale), int(110*scale)))
    haar = list(haar_upper) + list(haar_full)
    haar = [(int(x/scale), int(y/scale), int(W/scale), int(H/scale)) for (x,y,W,H) in haar]

    hog_scale = 0.6
    small2 = cv2.resize(frame_bgr, (int(w*hog_scale), int(h*hog_scale)), interpolation=cv2.INTER_AREA)
    rects, _ = hog.detectMultiScale(small2, winStride=(8,8), padding=(8,8), scale=1.05)
    hog_boxes = [(int(x/hog_scale), int(y/hog_scale), int(W/hog_scale), int(H/hog_scale)) for (x,y,W,H) in rects]

    def good_geom(b):
        x,y,W,H = b
        area = W*H
        ar = W/float(H+1e-6)
        if area < 0.01*w*h: return False
        if not (0.25 <= ar <= 0.8): return False
        if y < 0.05*h: return False
        return True

    haar = [b for b in haar if good_geom(b)]
    hog_boxes = [b for b in hog_boxes if good_geom(b)]

    agreed = []
    for b in haar:
        for c in hog_boxes:
            if iou(b, c) >= 0.3:
                agreed.append(b if (b[2]*b[3] >= c[2]*c[3]) else c)
                break

    merged = agreed if agreed else nms(haar + hog_boxes, iou_thresh=0.4)
    body_history.append(merged)
    persistent = []
    for b in merged:
        count = sum(1 for past in body_history for pb in past if iou(b, pb) >= 0.4)
        if count >= 2:
            persistent.append(b)
    return nms(persistent, iou_thresh=0.5)

# ==== Main ====
cap = cv2.VideoCapture(IP_CAM_URL)
last = time.time()
fps = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera disconnected")
        break

    faces = detect_faces(frame)
    bodies = detect_bodies(frame)

    # Draw
    for (x,y,w,h) in faces:
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,255), 2)
    for (x,y,w,h) in bodies:
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

    # FPS
    now = time.time()
    dt = max(1e-6, now-last)
    fps = 0.9*fps + 0.1*(1.0/dt)
    last = now

    txt = "PERSON !" if (faces or bodies) else "NO PERSON"
    cv2.putText(frame, f"{txt} | FPS: {fps:.1f}", (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0) if faces or bodies else (0,0,255), 2)

    cv2.imshow("Face + Body Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
