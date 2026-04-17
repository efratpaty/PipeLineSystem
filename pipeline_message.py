from collections import namedtuple

BoundingBox = namedtuple('BoundingBox', ['x', 'y', 'w', 'h'])


class PipelineMessage:
    def __init__(self, slot_index, frame_index, detections, is_sentinel):
        self.slotIndex = slot_index
        self.frameIndex = frame_index
        self.detections = detections
        self.isSentinel = is_sentinel

    @classmethod
    def create_sentinel(cls):
        return cls(None, None, None, True)
