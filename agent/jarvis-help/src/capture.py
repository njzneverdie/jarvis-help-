import cv2


class WebcamCapture:
    def __init__(self, index: int = 0, width: int = 640, height: int = 480, flip_horizontal: bool = True):
        self.flip_horizontal = flip_horizontal
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {index}")

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        if self.flip_horizontal:
            frame = cv2.flip(frame, 1)
        return frame

    def release(self):
        self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.release()
