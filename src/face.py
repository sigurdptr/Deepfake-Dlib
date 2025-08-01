from typing import List

import numpy as np


class FaceModel:
    def __init__(self,
            rect: object,
            landmarks: List[object]
        ) -> None:
        
        self.rect = rect
        self.landmarks = landmarks
        self.points = np.array(landmarks, np.int32)