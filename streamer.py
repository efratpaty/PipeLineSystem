import queue

import cv2
import numpy

from pipeline_message import PipelineMessage
from shared_memory_pool import SharedMemoryPool


class Streamer:
    def __init__(self, video_path, output_queue, pool_metadata, free_slots):
        self._videoPath = video_path
        self._outputQueue = output_queue
        self._poolMetadata = pool_metadata
        self._freeSlots = free_slots

    def run(self):
        pool = SharedMemoryPool.from_metadata(self._poolMetadata)
        cap = cv2.VideoCapture(self._videoPath)
        if not cap.isOpened():
            print(f"[ERROR] Cannot open video: {self._videoPath}")
            self._outputQueue.put(PipelineMessage.create_sentinel())
            pool.close()
            return
        frame_index = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                slot_index = self._freeSlots.get()
                numpy.copyto(pool.get_frame_array(slot_index), frame)
                self._outputQueue.put(PipelineMessage(slot_index, frame_index, None, False))
                frame_index += 1
        finally:
            cap.release()
            self._outputQueue.put(PipelineMessage.create_sentinel())
            pool.close()
