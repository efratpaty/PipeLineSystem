from datetime import datetime

import cv2

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_THICKNESS = 2
BOX_COLOR = (0, 255, 0)
BOX_THICKNESS = 2
TEXT_COLOR = (255, 255, 255)
TEXT_POSITION = (10, 30)
BLUR_KERNEL_SIZE = (51, 51)


class Displayer:
    def __init__(self, input_queue):
        self._inputQueue = input_queue

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
        while True:
            msg = self._inputQueue.get()
            if msg.isSentinel:
                break
            # copy to avoid mutating shared data
            display_frame = msg.frame.copy()
            self._draw(display_frame, msg.detections)
            cv2.imshow("Pipeline", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
