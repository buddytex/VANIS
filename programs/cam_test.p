import os, time, cv2

URL = os.getenv("IP_CAM_URL", "http://127.0.0.1:8080/video")
W, H = 640, 480
RECONNECT_DELAY = 1.0
fps, last = 0.0, time.time()

def open_cap():
    cap = cv2.VideoCapture(URL)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    return cap

cap = open_cap()

while True:
    if not cap.isOpened():
        cap.release()
        cap = open_cap()
        time.sleep(RECONNECT_DELAY)

    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        cap = open_cap()
        time.sleep(RECONNECT_DELAY)
        continue

    # FPS
    now = time.time()
    dt = max(1e-6, now - last)
    inst = 1.0 / dt
    fps = 0.9*fps + 0.1*inst if fps > 0 else inst
    last = now

    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.LINE_AA)
    cv2.imshow("IP Cam Test (q=quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
