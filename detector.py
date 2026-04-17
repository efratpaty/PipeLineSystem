import cv2

from pipeline_message import BoundingBox, PipelineMessage
from shared_memory_pool import SharedMemoryPool

# Filters out tiny flickering pixels or camera noise that technically pass the threshold but aren't meaningful motion
MIN_CONTOUR_AREA = 500


class Detector:
    def __init__(self, input_queue, output_queue, pool_metadata):
        self._inputQueue = input_queue
        self._outputQueue = output_queue
        self._poolMetadata = pool_metadata

    def _get_detections(self, frame, prev_frame):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is None:
            return [], gray_frame
        diff = cv2.absdiff(gray_frame, prev_frame)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = [BoundingBox(*cv2.boundingRect(c)) for c in cnts if cv2.contourArea(c) >= MIN_CONTOUR_AREA]
        return detections, gray_frame

    def run(self):
        pool = SharedMemoryPool.from_metadata(self._poolMetadata)
        prev_frame = None
        try:
            while True:
                msg = self._inputQueue.get()
                if msg.isSentinel:
                    break
                frame = pool.get_frame_array(msg.slotIndex)
                detections, prev_frame = self._get_detections(frame, prev_frame)
                self._outputQueue.put(PipelineMessage(msg.slotIndex, msg.frameIndex, detections))
        finally:
            self._outputQueue.put(PipelineMessage.create_sentinel())
            pool.close()
