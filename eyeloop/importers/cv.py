from pathlib import Path

import cv2

import eyeloop.config as config
from eyeloop.importers.importer import IMPORTER


class Importer(IMPORTER):

    def __init__(self) -> None:
        super().__init__()

    def first_frame(self) -> None:
        self.vid_path = Path(config.arguments.video)
        # load first frame
        if str(self.vid_path.name) == "0" or self.vid_path.is_file():  # or stream
            if str(self.vid_path.name) == "0":
                self.capture = cv2.VideoCapture(0)
            else:
                self.capture = cv2.VideoCapture(str(self.vid_path))

            self.route_frame = self.route_cam
            width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

            _, image = self.capture.read()
            if self.capture.isOpened():
                try:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                except:
                    image = image[..., 0]
            else:
                raise ValueError("Failed to initialize video stream.\nMake sure that the video path is correct, or that your webcam is plugged in and compatible with opencv.")

        elif self.vid_path.is_dir():

            config.file_manager.input_folderpath = self.vid_path

            config.file_manager.input_folderpath = self.vid_path

            image = config.file_manager.read_image(self.frame)

            try:
                height, width, _ = image.shape
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                self.route_frame = self.route_sequence_sing
            except:  # TODO fix bare except
                height, width = image.shape
                self.route_frame = self.route_sequence_flat

        else:
            raise ValueError(f"Video path at {self.vid_path} is not a file or directory!")

        self.arm(width, height, image)

    def route(self) -> None:
        self.first_frame()

        while True:
            try:
                self.route_frame()
            except ValueError:
                config.engine.release()
                print("Importer released (1).")
                break
            except TypeError:
                print("Importer released (2).")
                break


    def proceed(self, image) -> None:
        image = self.resize(image)
        image = self.rotate(image, config.engine.angle)
        config.engine.update_feed(image)
        self.save(image)
        self.frame += 1

    def route_sequence_sing(self) -> None:

        image = config.file_manager.read_image(self.frame)[..., 0]
        if image is not None:
            self.proceed(image)
        else:
            raise ValueError("No more frames.")

    def route_sequence_flat(self) -> None:

        image = config.file_manager.read_image(self.frame)
        if image is not None:
            self.proceed(image)
        else:
            raise ValueError("No more frames.")

    def route_cam(self) -> None:
        """
        Routes the capture frame to:
        1: eyeloop for online processing
        2: frame save for offline processing
        """

        _, image = self.capture.read()

        if image is not None:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            self.proceed(image)
        else:
            self.capture.release()
            raise ValueError("No more frames.")

    def release(self) -> None:
        raise TypeError()
        #self.route_frame = lambda _: None
