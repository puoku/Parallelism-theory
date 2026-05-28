import argparse
import queue
import threading
import time
import cv2
from ultralytics import YOLO

MODEL_NAME = "yolov8s-pose.pt"


class Camera:
    def __init__(self, src):
        print(f"Opening camera {src}...", flush=True)
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera '{src}'")
        for attempt in range(20):
            ok, _ = self._cap.read()
            if ok:
                print(f"Camera ready after {attempt + 1} attempts", flush=True)
                return
            time.sleep(0.2)
        raise RuntimeError(f"Camera '{src}' opened but cannot read frames")

    def read(self):
        return self._cap.read()

    def __del__(self):
        if getattr(self, "_cap", None) is not None:
            self._cap.release()


def draw_fps(frame, fps):
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)


def realtime_single(src):
    model = YOLO(MODEL_NAME)
    cam = Camera(src)
    cv2.namedWindow("YOLO Pose")

    t0 = time.time()
    frames = 0
    try:
        while True:
            ok, frame = cam.read()
            if not ok:
                break
            result = model.predict(frame, verbose=False)[0]
            img = result.plot()
            frames += 1
            draw_fps(img, frames / (time.time() - t0))
            cv2.imshow("YOLO Pose", img)
            if (cv2.waitKey(1) & 0xFF) == ord("q"):
                break
    finally:
        cv2.destroyWindow("YOLO Pose")
        del cam

    dt = time.time() - t0
    print(f"Single: {frames} frames in {dt:.2f} s -> {frames / dt:.2f} FPS")


def realtime_multi(src, num_workers):
    cam = Camera(src)
    stop = threading.Event()
    in_q = queue.Queue(maxsize=1)
    out_q = queue.Queue(maxsize=1)

    def latest_put(q, item):
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        q.put(item)

    def reader():
        misses = 0
        while not stop.is_set():
            ok, frame = cam.read()
            if not ok:
                misses += 1
                if misses > 30:
                    print("Camera disconnected", flush=True)
                    stop.set()
                    return
                time.sleep(0.05)
                continue
            misses = 0
            latest_put(in_q, frame)

    def worker():
        model = YOLO(MODEL_NAME)
        print("Worker model loaded", flush=True)
        while not stop.is_set():
            try:
                frame = in_q.get(timeout=0.5) #чтобы поток не висел бесконечно в ожидании
            except queue.Empty:
                continue
            result = model.predict(frame, verbose=False)[0]
            latest_put(out_q, result.plot())

    reader_t = threading.Thread(target=reader, daemon=True)
    workers = [threading.Thread(target=worker, daemon=True)
               for _ in range(num_workers)]
    reader_t.start()
    for t in workers:
        t.start()

    cv2.namedWindow("YOLO Pose")
    t0 = time.time()
    frames = 0
    last_img = None

    try:
        while not stop.is_set():
            try:
                last_img = out_q.get(timeout=0.1)
                frames += 1
            except queue.Empty:
                pass
            if last_img is None:
                if (cv2.waitKey(10) & 0xFF) == ord("q"):
                    break
                continue
            display = last_img.copy()
            draw_fps(display, frames / (time.time() - t0))
            cv2.imshow("YOLO Pose", display)
            if (cv2.waitKey(1) & 0xFF) == ord("q"):
                break
    finally:
        stop.set()
        cv2.destroyWindow("YOLO Pose")
        del cam

    dt = time.time() - t0
    print(f"Multi ({num_workers}): {frames} frames in {dt:.2f} s -> {frames / dt:.2f} FPS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--camera", default="0", help="camera index or path")
    p.add_argument("--mode", choices=["single", "multi"], default="multi")
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()

    src = int(args.camera) if args.camera.isdigit() else args.camera

    if args.mode == "single":
        realtime_single(src)
    else:
        realtime_multi(src, args.workers)


if __name__ == "__main__":
    main()
