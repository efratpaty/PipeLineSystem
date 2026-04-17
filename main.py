import argparse
import multiprocessing
import sys

import cv2

from detector import Detector
from displayer import Displayer
from shared_memory_pool import SharedMemoryPool
from streamer import Streamer

QUEUE_MAX_SIZE = 10
POOL_SIZE = QUEUE_MAX_SIZE * 2 + 3
FALLBACK_FPS = 30.0


def _read_video_metadata(video_path):
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    if not ret:
        print("ERROR: cannot open video or read first frame")
        sys.exit(1)
    if fps <= 0:
        fps = FALLBACK_FPS
    return frame.shape, fps


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motion detection pipeline")
    parser.add_argument("video_path", help="Path to the input video file")
    args = parser.parse_args()

    frame_shape, fps = _read_video_metadata(args.video_path)
    pool = SharedMemoryPool(POOL_SIZE, frame_shape)
    pool_metadata = pool.get_metadata()

    free_slots = multiprocessing.Queue(maxsize=POOL_SIZE)
    for i in range(POOL_SIZE):
        free_slots.put(i)

    streamer_to_detector = multiprocessing.Queue(maxsize=QUEUE_MAX_SIZE)
    detector_to_displayer = multiprocessing.Queue(maxsize=QUEUE_MAX_SIZE)

    streamer = Streamer(args.video_path, streamer_to_detector, pool_metadata, free_slots)
    detector = Detector(streamer_to_detector, detector_to_displayer, pool_metadata)
    displayer = Displayer(detector_to_displayer, pool_metadata, free_slots, fps)

    streamer_process = multiprocessing.Process(target=streamer.run)
    detector_process = multiprocessing.Process(target=detector.run)
    displayer_process = multiprocessing.Process(target=displayer.run)

    try:
        streamer_process.start()
        detector_process.start()
        displayer_process.start()

        displayer_process.join()
        detector_process.join(timeout=5)
        streamer_process.join(timeout=5)

        for process in [detector_process, streamer_process]:
            if process.is_alive():
                process.terminate()
            elif process.exitcode not in (0, None):
                print(f"[WARNING] Process {process.name} exited with code {process.exitcode}")
    finally:
        pool.close()
        pool.unlink()
