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
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            # Some video files are broken or don't store FPS metadata. If fps came back as 0 or negative (invalid), we substitute the fallback value so the rest of the code still works safely
            fps = FALLBACK_FPS
        c_target_interval = 1.0 / fps
        frame_index = 0
        while True:
            frame_start = time.perf_counter()
            ret, frame = cap.read()
            if (not ret) or frame is None:
                break
            msg = PipelineMessage(frame, frame_index, None, False)
            self._outputQueue.put(msg)
            frame_index += 1
            # Ensures frames are emitted at the video's native speed, not as fast as the CPU allows
            elapsed = time.perf_counter() - frame_start
            c_sleep_time = c_target_interval - elapsed
            if c_sleep_time > 0:
                time.sleep(c_sleep_time)
        cap.release()
        self._outputQueue.put(PipelineMessage.create_sentinel())
