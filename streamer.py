import time

import cv2

from pipeline_message import PipelineMessage

FALLBACK_FPS = 30.0


class Streamer:
    def __init__(self, video_path, output_queue):
        self._videoPath = video_path
        self._outputQueue = output_queue

    def run(self):
        cap = cv2.VideoCapture(self._videoPath)
        if not cap.isOpened():
            print(f"[ERROR] Cannot open video: {self._videoPath}")
            self._outputQueue.put(PipelineMessage.create_sentinel())
            return
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = FALLBACK_FPS
        target_interval = 1.0 / fps
        frame_index = 0
        try:
            while True:
                frame_start = time.perf_counter()
                ret, frame = cap.read()
                if not ret:
                    break
                msg = PipelineMessage(frame, frame_index, None, False)
                self._outputQueue.put(msg)
                frame_index += 1
                # Ensures frames are emitted at the video's native speed, not as fast as the CPU allows
                elapsed = time.perf_counter() - frame_start
                sleep_time = target_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
        finally:
            cap.release()
            self._outputQueue.put(PipelineMessage.create_sentinel())
