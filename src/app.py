from pathlib import Path
from threading import Thread

import cv2
import numpy as np
from PyQt6 import QtCore
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
    QWidget,
    QLabel
)

from mask import FaceMask
from predictor import PredictorModel


class ImageDisplay(QLabel):
    def __init__(self, width: int, height: int) -> None:
        super().__init__()

        self.setStyleSheet("border: 1px solid gray; background-color: black")
        self.setFixedSize(width, height)


    def _scale_img(self, img: cv2.UMat) -> cv2.UMat:
        label_width = self.size().width()
        label_height = self.size().height()

        img_h, img_w = img.shape[:2]

        if (img_w-label_width) > (img_h-label_height):
            factor = label_width / img_w
        else:
            factor = label_height / img_h

        img_w = min(label_width, round(img_w * factor))
        img_h = min(label_height, round(img_h * factor))

        resized = cv2.resize(img, (img_w, img_h))

        padded = np.zeros((label_height, label_width, 3), np.uint8)

        offset_x = 0
        offset_y = 0

        if (label_height - img_h) > (label_width - img_w):
            offset_y = int((label_height - img_h) / 2)
        else:
            offset_x = int((label_width - img_w) / 2)

        padded[offset_y:offset_y+img_h, offset_x:offset_x+img_w] = resized

        return padded

    
    def set_image(self, img: cv2.UMat) -> None:
        img = self._scale_img(img)

        h, w = img.shape[:2]

        q_img = QImage(img.data, w, h, QImage.Format.Format_RGB888)
        pix_map = QPixmap.fromImage(q_img.rgbSwapped())

        self.setPixmap(pix_map)


class AppWindow(QMainWindow):
    def __init__(self, working_dir: Path) -> None:
        super().__init__()

        predictor_path = Path(working_dir, "assets", "shape_predictor_68_face_landmarks.dat")
        PredictorModel.init(predictor_path)

        self._active_generating = False
        self._face_file = None
        self._face_mask = None
        self._input_file = None

        self.setFixedSize(850, 500)
        self.setWindowTitle("Deepfake")

        root_layout = QHBoxLayout()
        root_layout.setSpacing(20)

        self._panel = self._create_control_panel()
        self._result_img = ImageDisplay(560, 480)

        root_layout.addLayout(self._panel)
        root_layout.addWidget(self._result_img)

        widget = QWidget()
        widget.setLayout(root_layout)
        self.setCentralWidget(widget)
        self.show()
    

    def _create_control_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()        

        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self._face_preview = ImageDisplay(200, 200)
        layout.addWidget(self._face_preview)
        
        controlLabel = QLabel("━━━━━━━━━━━━━━━━━━━━━")
        controlLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(controlLabel)
        
        self._openFaceBtn = QPushButton("Open face image")
        self._openFaceBtn.setFixedSize(200, 60)
        self._openFaceBtn.clicked.connect(self._open_face_img)
        layout.addWidget(self._openFaceBtn)

        self._openInputBtn = QPushButton("Open input file")
        self._openInputBtn.setFixedSize(200, 60)
        self._openInputBtn.clicked.connect(self._open_input_file)
        layout.addWidget(self._openInputBtn)

        self._generateBtn = QPushButton()
        self._generateBtn.setText("Generate")
        self._generateBtn.setFixedSize(200, 60)
        self._generateBtn.clicked.connect(self._generate_deepfake)
        layout.addWidget(self._generateBtn)

        return layout
    

    def _open_face_img(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open file',
            None,
            "Image files (*.jpg *.png *.jpeg)"
        )
        
        if not file_path:
            return
        
        img = cv2.imread(file_path)
        faces = PredictorModel.detect_faces(img)

        if len(faces) == 0:
            QMessageBox.critical(
                None,
                "Error",
                "Unable to locate faces in image"
            )
            return
        elif len(faces) > 1:
            QMessageBox.critical(
                None,
                "Error",
                "Too many faces located in image"
            )
            return

        self._face_mask = FaceMask(img, faces[0])
        self._face_preview.set_image(img)

    
    def _open_input_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open file',
            None,
            "Media files (*.jpg *.png *.jpeg)"
        )

        if not file_path:
            return
        
        self._input_file = cv2.imread(file_path)
        self._result_img.set_image(self._input_file)


    def _deepfake_daemon(self) -> None:
        if self._input_file is None or self._face_mask is None:
            self._active_generating = False
            QMessageBox.critical(None, "Error", "Make sure to add input file and face image")
            return

        faces = PredictorModel.detect_faces(self._input_file)

        if len(faces) == 0:
            self._active_generating = False
            QMessageBox.critical(None, "Error", "Unable to locate faces in input file")
            return

        result = self._face_mask.apply_mask(self._input_file, faces)
        self._result_img.set_image(result)

        self._active_generating = False


    def _generate_deepfake(self) -> None:
        if self._active_generating:
            return
        
        self._active_generating = True
        
        t = Thread(
            target=self._deepfake_daemon,
            daemon=True
        )
        t.start()