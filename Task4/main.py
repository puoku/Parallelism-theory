import argparse
import logging
import os
import queue
import sys
import threading
import time
import cv2


class Sensor:
    def get(self):
        raise NotImplementedError("Subclasses must implement method get()")


class SensorX(Sensor):
    def __init__(self, delay):
        self._delay = delay
        self._data = 0

    def get(self):
        time.sleep(self._delay)
        self._data += 1
        return self._data


class SensorCam(Sensor):
    _MAX_RETRIES = 3

    def __init__(self, name, resolution):
        self._cam_name = name
        src = int(name) if name.isdigit() else name
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            logging.error("Cannot open camera '%s'", name)
            raise RuntimeError(f"Camera '{name}' not available")
        w, h = resolution
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

    def get(self):
        if not self._cap.isOpened():
            logging.error("Camera '%s' is no longer opened (disconnected?)",
                          self._cam_name)
            return None
        for attempt in range(self._MAX_RETRIES):
            try:
                ok, frame = self._cap.read()
            except cv2.error as e:
                logging.error("cv2 error while reading camera: %s", e)
                return None
            if ok and frame is not None:
                return frame
            logging.warning("Empty frame from camera (attempt %d/%d)",
                            attempt + 1, self._MAX_RETRIES)
            time.sleep(0.05)
        logging.error("Camera '%s' failed %d reads in a row — giving up",
                      self._cam_name, self._MAX_RETRIES)
        return None

    def __del__(self):
        if getattr(self, "_cap", None) is not None:
            self._cap.release()


class WindowImage:
    def __init__(self, freq):
        self._delay_ms = max(1, int(1000 / freq)) #задержка между кадрами в мс 
        self._created = False
        try:
            cv2.namedWindow("Sensors")
            self._created = True
        except cv2.error as e:
            logging.error("Cannot create window: %s", e)
            raise

    def show(self, img):
        try:
            cv2.imshow("Sensors", img)
            key = cv2.waitKey(self._delay_ms) & 0xFF
        except cv2.error as e:
            logging.error("Window show failed: %s", e)
            return False
        return key != ord('q')

    def __del__(self):
        if not getattr(self, "_created", False):
            return
        try:
            cv2.destroyWindow("Sensors")
        except cv2.error as e:
            logging.error("destroyWindow failed: %s", e)


def sensor_loop(sensor, q, stop):
    while not stop.is_set():
        value = sensor.get()
        if value is None:
            stop.set()
            return
        try:
            q.get_nowait()
        except queue.Empty:
            pass
        q.put(value)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--camera", default="0")
    p.add_argument("--resolution", default="1280x720")
    p.add_argument("--freq", type=float, default=30.0)
    args = p.parse_args()

    w, h = (int(x) for x in args.resolution.lower().split("x"))

    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "app.log"),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        cam = SensorCam(args.camera, (w, h))
    except Exception as e:
        logging.error("Init failed: %s", e)
        return

    try:
        window = WindowImage(args.freq)
    except Exception as e:
        logging.error("Window init failed: %s", e)
        del cam
        return

    sensors = [SensorX(0.01), SensorX(0.1), SensorX(1.0)]
    qs = [queue.Queue(maxsize=1) for _ in sensors]
    cam_q = queue.Queue(maxsize=1)
    stop = threading.Event()

    threads = [
        threading.Thread(target=sensor_loop, args=(s, q, stop), daemon=True)
        for s, q in zip(sensors, qs)
    ]
    threads.append(threading.Thread(target=sensor_loop, args=(cam, cam_q, stop), daemon=True))
    for t in threads:
        t.start()

    values = [0, 0, 0]
    frame = None

    while not stop.is_set():
        for i, q in enumerate(qs):
            try:
                values[i] = q.get_nowait()
            except queue.Empty:
                pass
        try:
            frame = cam_q.get_nowait()
        except queue.Empty:
            pass

        if frame is None:
            if (cv2.waitKey(int(1000 / args.freq)) & 0xFF) == ord('q'):
                break
            continue

        img = frame.copy()
        for i, v in enumerate(values):
            cv2.putText(img, f"Sensor{i}: {v}",
                        (img.shape[1] - 200, img.shape[0] - 60 + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)

        if not window.show(img):
            break

    if stop.is_set():
        print("Camera error — see log/app.log for details", file=sys.stderr)
    stop.set()
    for t in threads:
        t.join(timeout=2)
    del window
    del cam


if __name__ == "__main__":
    main()
