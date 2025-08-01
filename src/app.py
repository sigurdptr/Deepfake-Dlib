import cv2
import numpy as np

from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLabel
)

from PyQt6.QtGui import QPixmap, QImage
from PyQt6 import QtCore


class ImageDisplay(QLabel):
    def __init__(self, width: int, height: int) -> None:
        super().__init__()

        self.setStyleSheet("border: 1px solid gray; background-color: black")
        self.setFixedSize(width, height)


    def _scale_img(self, img: cv2.UMat) -> None:
        label_width = self.size().width()
        label_height = self.size().height()

        img_h, img_w = img.shape[:2]

        if (img_w-label_width) > (img_h-label_height):
            factor = label_width / img_w
        else:
            factor = label_height / img_h

        img_w = min(label_width, int(img_w *factor))
        img_h = min(label_height, int(img_h *factor))

        resized = cv2.resize(img, (img_w, img_h))

        padded = np.zeros((label_height, label_width, 3), np.uint8)

        offset_x = 0
        offset_y = 0

        if (label_height - img_h) > (label_width - img_w):
            offset_y = int((label_height - img_h) / 2)
        else:
            offset_x = int((label_width - img_w) / 2)

        print(offset_x, img_w)
        print(offset_y, img_h)

        padded[offset_y:offset_y+img_h, offset_x:offset_x+img_w] = resized

        return padded

    
    def setImage(self, img: cv2.UMat) -> None:
        img = self._scale_img(img)

        h, w = img.shape[:2]

        q_img = QImage(img.data, w, h, QImage.Format.Format_RGB888)
        pix_map = QPixmap.fromImage(q_img.rgbSwapped())

        self.setPixmap(pix_map)


class AppWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setFixedSize(850, 500)
        self.setWindowTitle("Deepfake")

        rootLayout = QHBoxLayout()
        rootLayout.setSpacing(20)

        panel = self._createControlPanel()
        result = ImageDisplay(560, 480)

        rootLayout.addLayout(panel)
        rootLayout.addWidget(result)

        widget = QWidget()
        widget.setLayout(rootLayout)
        self.setCentralWidget(widget)
        self.show()
    

    def _createControlPanel(self) -> QVBoxLayout:
        layout = QVBoxLayout()        

        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        preview = ImageDisplay(200, 200)
        layout.addWidget(preview)
        
        controlLabel = QLabel("━━━━━━━━━━━━━━━━━━━━━")
        controlLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(controlLabel)
        
        openFaceBtn = QPushButton("Open face image")
        openFaceBtn.setFixedSize(200, 60)
        openFaceBtn.clicked.connect(self._openFaceImg)
        layout.addWidget(openFaceBtn)

        openInputBtn = QPushButton("Open input file")
        openInputBtn.setFixedSize(200, 60)
        openInputBtn.clicked.connect(self._openInputFile)
        layout.addWidget(openInputBtn)

        generateBtn = QPushButton()
        generateBtn.setText("Generate")
        generateBtn.setFixedSize(200, 60)
        generateBtn.clicked.connect(self._generateDeepfake)
        layout.addWidget(generateBtn)

        return layout
    

    def _openFaceImg(self) -> None:
        print("face")

    
    def _openInputFile(self) -> None:
        print("input")


    def _generateDeepfake(self) -> None:
        print("generate")