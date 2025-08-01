from pathlib import Path
from typing import List

import cv2
import dlib

from face import FaceModel


class PredictorModel:
    @classmethod
    def init(cls, predictor_path: Path):
        if not predictor_path.is_file():
                raise FileNotFoundError(f"Unable to locate predictor file: {predictor_path}")

        cls.face_detector = dlib.get_frontal_face_detector()
        cls.shape_predictor = dlib.shape_predictor(str(predictor_path))
    

    @classmethod
    def detect_faces(cls, img: cv2.UMat) -> List[FaceModel]:
        faces = []

        for rect in cls.face_detector(img):
            shape = cls.shape_predictor(img, rect)
        
            landmarks = []
            for n in range(shape.num_parts):
                x = shape.part(n).x
                y = shape.part(n).y
                landmarks.append((x, y))
            
            face = FaceModel(rect, landmarks)
            faces.append(face)

        return faces