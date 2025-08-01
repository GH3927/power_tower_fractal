import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QRect
from power_fractal import compute_power_fractal

class FractalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Power Fractal Explorer")
        self.current_spacing = 0.005
        self.current_center_x = 0.0
        self.current_center_y = 0.0
        self.current_resolution = 200
        self.zoom_scale = 1.0
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(main_layout)

        # Input fields
        input_layout = QHBoxLayout()
        
        self.resolution_input = QLineEdit("200")
        self.spacing_input = QLineEdit("0.005")
        self.center_x_input = QLineEdit("0.0")
        self.center_y_input = QLineEdit("0.0")

        input_layout.addWidget(QLabel("Resolution:"))
        input_layout.addWidget(self.resolution_input)
        input_layout.addWidget(QLabel("Pixel Spacing:"))
        input_layout.addWidget(self.spacing_input)
        input_layout.addWidget(QLabel("Center X:"))
        input_layout.addWidget(self.center_x_input)
        input_layout.addWidget(QLabel("Center Y:"))
        input_layout.addWidget(self.center_y_input)

        main_layout.addLayout(input_layout)

        # Plot button
        self.plot_button = QPushButton("Render Fractal")
        self.plot_button.clicked.connect(self.plot_fractal)
        main_layout.addWidget(self.plot_button)

        # Coordinate display
        self.coord_label = QLabel("X: 0.000, Y: 0.000")
        main_layout.addWidget(self.coord_label)

        # mouse event
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(600, 600)  # 고정 크기 추가
        self.image_label.setMouseTracking(True)
    
        # 이벤트 핸들러 연결 (update_coordinates는 mouse_move_event 내부에서 호출되므로 삭제)
        # self.image_label.mouseMoveEvent = self.update_coordinates  # 삭제
        self.image_label.mousePressEvent = self.mouse_press_event
        self.image_label.mouseReleaseEvent = self.mouse_release_event
        self.image_label.mouseMoveEvent = self.mouse_move_event
        self.image_label.wheelEvent = self.mouse_wheel_event

        main_layout.addWidget(self.image_label)
        self.dragging = False
        self.last_mouse_pos = None
        
        # 이미지 저장 버튼 추가
        self.save_button = QPushButton("Save Image")
        self.save_button.clicked.connect(self.save_image)
        main_layout.addWidget(self.save_button)
                
        self.resolution_input.editingFinished.connect(self.adjust_spacing_for_resolution)
        
    def adjust_spacing_for_resolution(self):
        try:
            new_resolution = int(self.resolution_input.text())
            if new_resolution <= 0:
                raise ValueError
    
            # 현재 시야 크기 유지: old_spacing * old_resolution = new_spacing * new_resolution
            current_view_size = self.current_spacing * self.current_resolution
            new_spacing = current_view_size / new_resolution
    
            self.current_resolution = new_resolution
            self.current_spacing = new_spacing
    
            # 입력창 업데이트
            self.spacing_input.setText(f"{self.current_spacing:.8f}")
    
            # 이미지 다시 렌더링
            self.plot_fractal()
    
        except ValueError:
            self.coord_label.setText("Invalid resolution.")

    def mouse_press_event(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_mouse_pos = event.position()

    def mouse_release_event(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.last_mouse_pos = None

    def mouse_move_event(self, event):
        self.update_coordinates(event)
        if self.dragging and self.last_mouse_pos is not None:
            delta = event.position() - self.last_mouse_pos
            dx = delta.x()
            dy = delta.y()
    
            self.current_center_x -= dx * self.current_spacing
            self.current_center_y += dy * self.current_spacing
            self.last_mouse_pos = event.position()
    
            self.center_x_input.setText(str(self.current_center_x))
            self.center_y_input.setText(str(self.current_center_y))
    
            self.plot_fractal()  # 드래그 중 실시간 렌더링

    def mouse_wheel_event(self, event):
        if not hasattr(self, 'scaled_pixmap') or self.scaled_pixmap.isNull():
            return
    
        pos = event.position()
        x, y = pos.x(), pos.y()
    
        pixmap_rect = self.scaled_pixmap.rect()
        pixmap_rect.moveCenter(self.image_label.rect().center())
    
        if not pixmap_rect.contains(int(x), int(y)):
            rel_x, rel_y = 0.5, 0.5
        else:
            rel_x = (x - pixmap_rect.left()) / pixmap_rect.width()
            rel_y = (y - pixmap_rect.top()) / pixmap_rect.height()
    
        angle = event.angleDelta().y()
        zoom_factor = 1.1 if angle > 0 else 0.9
    
        new_spacing = self.current_spacing / zoom_factor
    
        min_spacing = 1e-7
        max_spacing = 100.0
        if new_spacing < min_spacing or new_spacing > max_spacing:
            return
    
        fractal_x_before = self.current_center_x + (rel_x - 0.5) * self.current_resolution * self.current_spacing
        fractal_y_before = self.current_center_y - (rel_y - 0.5) * self.current_resolution * self.current_spacing
    
        fractal_x_after = self.current_center_x + (rel_x - 0.5) * self.current_resolution * new_spacing
        fractal_y_after = self.current_center_y - (rel_y - 0.5) * self.current_resolution * new_spacing
    
        self.current_center_x += fractal_x_before - fractal_x_after
        self.current_center_y += fractal_y_before - fractal_y_after
    
        self.current_spacing = new_spacing
    
        self.center_x_input.setText(f"{self.current_center_x:.8f}")
        self.center_y_input.setText(f"{self.current_center_y:.8f}")
        self.spacing_input.setText(f"{self.current_spacing:.8f}")
    
        self.plot_fractal()

    def update_coordinates(self, event):
        if not hasattr(self, 'scaled_pixmap') or self.scaled_pixmap.isNull():
            return
    
        pos = event.position()
        x, y = pos.x(), pos.y()
    
        label_rect = self.image_label.rect()
        pixmap_rect = self.scaled_pixmap.rect()
        pixmap_rect.moveCenter(label_rect.center())
    
        if pixmap_rect.contains(int(x), int(y)):
            rel_x = (x - pixmap_rect.left()) / pixmap_rect.width()
            rel_y = (y - pixmap_rect.top()) / pixmap_rect.height()
    
            fractal_x = self.current_center_x + (rel_x - 0.5) * self.current_resolution * self.current_spacing
            fractal_y = self.current_center_y - (rel_y - 0.5) * self.current_resolution * self.current_spacing
    
            self.coord_label.setText(f"X: {fractal_x:.6f}, Y: {fractal_y:.6f}")
        else:
            self.coord_label.setText("X: -, Y: -")

    def plot_fractal(self):
        try:
            self.current_spacing = float(self.spacing_input.text())
            self.current_center_x = float(self.center_x_input.text())
            self.current_center_y = float(self.center_y_input.text())
            self.current_resolution = int(self.resolution_input.text())
        except ValueError:
            self.image_label.setText("Invalid input values")
            return
    
        fractal = compute_power_fractal(
            self.current_resolution,
            self.current_spacing,
            self.current_center_x,
            self.current_center_y
        )
    
        height, width = fractal.shape
        image = QImage(width, height, QImage.Format.Format_Grayscale8)
        for y in range(height):
            for x in range(width):
                value = int(fractal[y, x] * 255)
                image.setPixel(x, y, value * 0x10101)
    
        self.current_pixmap = QPixmap.fromImage(image)
    
        # 여기서 scaled_pixmap을 별도로 저장
        self.scaled_pixmap = self.current_pixmap.scaled(
            self.image_label.width(), self.image_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
    
        self.image_label.setPixmap(self.scaled_pixmap)

    def save_image(self):
        if not hasattr(self, 'current_pixmap') or self.current_pixmap.isNull():
            self.coord_label.setText("No image to save.")
            return
    
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Fractal Image",
            "fractal_snapshot.png",
            "PNG Files (*.png)"
        )
    
        if filename:
            if not filename.lower().endswith('.png'):
                filename += '.png'
    
            if self.current_pixmap.save(filename, "PNG"):
                self.coord_label.setText(f"Saved: {filename}")
            else:
                self.coord_label.setText("Failed to save image.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FractalWindow()
    window.show()
    sys.exit(app.exec())