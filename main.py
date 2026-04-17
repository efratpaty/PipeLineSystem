import multiprocessing

from detector import Detector
from displayer import Displayer
from streamer import Streamer

QUEUE_MAX_SIZE = 10


if __name__ == "__main__":
    video_path = r"C:\Users\Efrat\Documents\PrivateFolder\NewProject\People - 6387.mp4"
    streamer_to_detector = multiprocessing.Queue(maxsize=QUEUE_MAX_SIZE)
    detector_to_displayer = multiprocessing.Queue(maxsize=QUEUE_MAX_SIZE)

    streamer = Streamer(video_path, streamer_to_detector)
    detector = Detector(streamer_to_detector, detector_to_displayer)
    displayer = Displayer(detector_to_displayer)

    streamer_process = multiprocessing.Process(target=streamer.run)
    detector_process = multiprocessing.Process(target=detector.run)
    displayer_process = multiprocessing.Process(target=displayer.run)

    streamer_process.start()
    detector_process.start()
    displayer_process.start()

    displayer_process.join()
    detector_process.join(timeout=5)
    streamer_process.join(timeout=5)

    for process in [detector_process, streamer_process]:
        if process.is_alive():
            process.terminate()
