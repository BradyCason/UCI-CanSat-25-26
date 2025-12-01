import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt


class MapWidget(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)  # Fixed mini-map size
        self.setStyleSheet("border: 2px solid black; background: #ddd;")

        # Load and scale the image (make it bigger than the minimap)
        self.image = QPixmap(image_path).scaled(
            800, 800, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )

        # Position of the top-left corner of the image within the label
        self.offset_x = 0
        self.offset_y = 0
        self.step = 20  # Movement speed

        self.setFocusPolicy(Qt.StrongFocus)

        # Load the sniper scope icon (small image)
        scope_path = os.path.join(os.path.dirname(__file__), "gui", "scope.png")
        self.scope_icon = QPixmap(scope_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def keyPressEvent(self, event):
        # Move image, but prevent it from moving too far (keep some image visible)
        if event.key() == Qt.Key_Left:
            self.offset_x = min(self.offset_x + self.step, 0)
        elif event.key() == Qt.Key_Right:
            self.offset_x = max(self.offset_x - self.step, self.width() - self.image.width())
        elif event.key() == Qt.Key_Up:
            self.offset_y = min(self.offset_y + self.step, 0)
        elif event.key() == Qt.Key_Down:
            self.offset_y = max(self.offset_y - self.step, self.height() - self.image.height())

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setClipRect(0, 0, self.width(), self.height())  # Clip to label bounds
        painter.drawPixmap(self.offset_x, self.offset_y, self.image)

        # Draw the scope icon centered
        scope_x = (self.width() - self.scope_icon.width()) // 2
        scope_y = (self.height() - self.scope_icon.height()) // 2
        painter.drawPixmap(scope_x, scope_y, self.scope_icon)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Inside Clipped Label")
        self.setGeometry(100, 100, 600, 400)

        # Load image from gui/logo.png
        image_path = os.path.join(os.path.dirname(__file__), "gui", "launch_site.png")

        # Add the custom map widget (label that handles movement and drawing)
        self.map_widget = MapWidget(image_path, self)
        self.map_widget.move(50, 50)  # Place it somewhere in the window

        self.map_widget.setFocus()  # So it receives key events


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
