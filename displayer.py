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
    def _blur_detections(display_frame, detections):
        for (x, y, w, h) in detections:
            display_frame[y:y + h, x:x + w] = cv2.GaussianBlur(
                display_frame[y:y + h, x:x + w],
                BLUR_KERNEL_SIZE,
                0
            )

    @staticmethod
    def _draw_boxes(display_frame, detections):
        for (x, y, w, h) in detections:
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), BOX_COLOR, BOX_THICKNESS)

    @staticmethod
    def _draw_timestamp(display_frame):
        current_time = datetime.now().strftime("%H:%M:%S")
        cv2.putText(display_frame, current_time, TEXT_POSITION, FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)

    @staticmethod
    def _draw(display_frame, detections):
        Displayer._blur_detections(display_frame, detections)
        Displayer._draw_boxes(display_frame, detections)
        Displayer._draw_timestamp(display_frame)
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
                # allow the user to quit early
                break
        cv2.destroyAllWindows()
