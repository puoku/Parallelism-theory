import argparse
import queue
import threading
import time
import cv2
from ultralytics import YOLO

MODEL_NAME = "yolov8s-pose.pt"


class Video:
    def __init__(self, path):
        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open video '{path}'")

    def read(self):
        return self._cap.read()

    def fps(self):
        return self._cap.get(cv2.CAP_PROP_FPS) or 30.0

    def size(self):
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (w, h)

    def __del__(self):
        if getattr(self, "_cap", None) is not None:
            self._cap.release()


class VideoWriter:
    def __init__(self, path, fps, size):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(path, fourcc, fps, size)
        if not self._writer.isOpened():
            raise RuntimeError(f"Cannot open writer for '{path}'")

    def write(self, frame):
        self._writer.write(frame)

    def __del__(self):
        if getattr(self, "_writer", None) is not None:
            self._writer.release()


def process_single(input_path, output_path):
    model = YOLO(MODEL_NAME)
    video = Video(input_path)
    writer = VideoWriter(output_path, video.fps(), video.size())

    count = 0
    while True:
        ok, frame = video.read()
        if not ok:
            break
        result = model.predict(frame, verbose=False)[0]
        writer.write(result.plot())
        count += 1
    return count


def process_multi(input_path, output_path, num_workers):
    video = Video(input_path)
    writer = VideoWriter(output_path, video.fps(), video.size())

    in_q = queue.Queue(maxsize=num_workers * 2)
    out_q = queue.Queue(maxsize=num_workers * 4)
    total = [None]

    def reader():
        idx = 0
        while True:
            ok, frame = video.read()
            if not ok:
                break
            in_q.put((idx, frame))
            idx += 1
        total[0] = idx
        for _ in range(num_workers):
            in_q.put(None)

    def worker():
        model = YOLO(MODEL_NAME)
        while True:
            item = in_q.get()
            if item is None:
                return
            idx, frame = item
            result = model.predict(frame, verbose=False)[0]
            out_q.put((idx, result.plot()))

    threads = [threading.Thread(target=worker, daemon=True)
               for _ in range(num_workers)]
    reader_t = threading.Thread(target=reader, daemon=True)
    for t in threads:
        t.start()
    reader_t.start()

    buffer = {}
    next_idx = 0
    while total[0] is None or next_idx < total[0]:
        idx, frame = out_q.get()
        buffer[idx] = frame
        while next_idx in buffer:
            writer.write(buffer.pop(next_idx))
            next_idx += 1

    reader_t.join()
    for t in threads:
        t.join()
    return next_idx


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, help="path to input video (640x480)")
    p.add_argument("--mode", choices=["single", "multi"], default="single")
    p.add_argument("--output", required=True, help="path to output video")
    p.add_argument("--workers", type=int, default=4,
                   help="number of workers for --mode multi")
    args = p.parse_args()

    t0 = time.time()
    if args.mode == "single":
        n = process_single(args.video, args.output)
    else:
        n = process_multi(args.video, args.output, args.workers)
    dt = time.time() - t0

    print(f"Mode={args.mode} workers={args.workers if args.mode == 'multi' else 1}")
    print(f"Frames={n}")
    print(f"Time={dt:.2f} s")
    print(f"Avg FPS={n / dt:.2f}")


if __name__ == "__main__":
    main()
