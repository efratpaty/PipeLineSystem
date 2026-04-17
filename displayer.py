import time
from datetime import datetime

import cv2

from shared_memory_pool import SharedMemoryPool

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_THICKNESS = 2
BOX_COLOR = (0, 255, 0)
BOX_THICKNESS = 2
TEXT_COLOR = (255, 255, 255)
TEXT_POSITION = (10, 30)
BLUR_KERNEL_SIZE = (51, 51)
MIN_WAIT_MS = 1


class Displayer:
    def __init__(self, input_queue, pool_metadata, free_slots, fps):
        self._inputQueue = input_queue
        self._poolMetadata = pool_metadata
        self._freeSlots = free_slots
        self._fps = fps

    @staticmethod
    def _blur_detection(display_frame, bbox):
        roi = display_frame[bbox.y:bbox.y + bbox.h, bbox.x:bbox.x + bbox.w]
        roi[:] = cv2.GaussianBlur(roi, BLUR_KERNEL_SIZE, 0)

    @staticmethod
    def _draw_box(display_frame, bbox):
        cv2.rectangle(display_frame, (bbox.x, bbox.y), (bbox.x + bbox.w, bbox.y + bbox.h), BOX_COLOR, BOX_THICKNESS)

    @staticmethod
    def _draw_timestamp(display_frame):
        current_time = datetime.now().strftime("%H:%M:%S")
        cv2.putText(display_frame, current_time, TEXT_POSITION, FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)

    @classmethod
    def _draw(cls, display_frame, detections):
        for bbox in detections:
            cls._blur_detection(display_frame, bbox)
            cls._draw_box(display_frame, bbox)
        cls._draw_timestamp(display_frame)

    def run(self):
        pool = SharedMemoryPool.from_metadata(self._poolMetadata)
        target_interval = 1.0 / self._fps
        start_time = None
        frame_count = 0
        try:
            while True:
                msg = self._inputQueue.get()
                if msg.isSentinel:
                    break
                # copy out of shared memory before releasing the slot
                display_frame = pool.get_frame_array(msg.slotIndex).copy()
                self._freeSlots.put(msg.slotIndex)
                self._draw(display_frame, msg.detections)
                cv2.imshow("Pipeline", display_frame)
                if start_time is None:
                    start_time = time.perf_counter()
                frame_count += 1
                target_time = start_time + frame_count * target_interval
                wait_ms = max(MIN_WAIT_MS, int((target_time - time.perf_counter()) * 1000))
                if cv2.waitKey(wait_ms) & 0xFF == ord('q'):
                    break
        finally:
            cv2.destroyAllWindows()
            pool.close()
