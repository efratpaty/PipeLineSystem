from datetime import datetime

import cv2

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_THICKNESS = 2
BOX_COLOR = (0, 255, 0)
BOX_THICKNESS = 2
TEXT_COLOR = (255, 255, 255)
TEXT_POSITION = (10, 30)


class Displayer:
    def __init__(self, input_queue):
        self._inputQueue = input_queue

    @staticmethod
    def _draw(display_frame, detections):
        for (x, y, w, h) in detections:
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), BOX_COLOR, BOX_THICKNESS)
        current_time = datetime.now().strftime("%H:%M:%S")
        cv2.putText(display_frame, current_time, TEXT_POSITION, FONT, FONT_SCALE, TEXT_COLOR, FONT_THICKNESS)

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
