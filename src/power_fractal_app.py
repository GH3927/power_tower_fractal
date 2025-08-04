import sys
import math
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from PyQt6.QtWidgets import QFileDialog, QProgressBar
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QIntValidator

class FractalWorker(QThread):
    progress_changed = pyqtSignal(int)
    result_ready = pyqtSignal(np.ndarray)

    def __init__(self, resolution, spacing, center_x, center_y, threshold, max_iter):
        super().__init__()
        self.resolution = resolution
        self.spacing = spacing
        self.center_x = center_x
        self.center_y = center_y
        self.threshold = threshold
        self.max_iter = max_iter

    def run(self):
        x = np.linspace(self.center_x - self.resolution * self.spacing / 2,
                        self.center_x + self.resolution * self.spacing / 2,
                        self.resolution, dtype=np.float64)
        y = np.linspace(self.center_y - self.resolution * self.spacing / 2,
                        self.center_y + self.resolution * self.spacing / 2,
                        self.resolution, dtype=np.float64)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y
        Z = np.ones_like(C, dtype=np.complex128)
        fractal = np.zeros((self.resolution, self.resolution), dtype=np.uint16)

        for i in range(self.max_iter):
            Z = np.where(np.abs(Z) < self.threshold, C ** Z, Z)
            mask = (np.abs(Z) > self.threshold) & (fractal == 0)
            fractal[mask] = i + 1
            mask_nan_inf = (np.isnan(Z) | np.isinf(Z)) & (fractal == 0)
            fractal[mask_nan_inf] = i + 1
            self.progress_changed.emit(int((i + 1) / self.max_iter * 100))
        
            if np.all(fractal != 0):
                break

        self.result_ready.emit(fractal)

class FractalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Power Fractal Explorer")
        self.current_spacing = 0.005
        self.current_center_x = 0.0
        self.current_center_y = 0.0
        self.current_resolution = 200
        self.zoom_scale = 1.0
        self.is_rendering = False
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(720, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(main_layout)
        
        # Input fields
        input_layout = QHBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.resolution_input = QLineEdit("200")
        self.spacing_input = QLineEdit("0.05")
        self.center_x_input = QLineEdit("0.0")
        self.center_y_input = QLineEdit("0.0")
        self.threshold_input = QLineEdit("1e40")
        self.max_iter_input = QLineEdit("50")

        self.spacing_input.setValidator(QDoubleValidator(1e-20, 100.0, 20))
        self.resolution_input.setValidator(QIntValidator(1, 10000))
        self.center_x_input.setValidator(QDoubleValidator(-1000, 1000, 20))
        self.center_y_input.setValidator(QDoubleValidator(-1000, 1000, 20))
        self.threshold_input.setValidator(QDoubleValidator(1e-10, 1e10, 20))
        self.max_iter_input.setValidator(QIntValidator(1, 10000))

        input_layout.addWidget(QLabel("Resolution:"))
        input_layout.addWidget(self.resolution_input)
        input_layout.addWidget(QLabel("Pixel Spacing:"))
        input_layout.addWidget(self.spacing_input)
        input_layout.addWidget(QLabel("Center X:"))
        input_layout.addWidget(self.center_x_input)
        input_layout.addWidget(QLabel("Center Y:"))
        input_layout.addWidget(self.center_y_input)
        input_layout.addWidget(QLabel("Threshold:"))
        input_layout.addWidget(self.threshold_input)
        input_layout.addWidget(QLabel("Max Iter:"))
        input_layout.addWidget(self.max_iter_input)

        main_layout.addLayout(input_layout)

        # Color parameters and mode selection layout
        color_param_layout = QHBoxLayout()
        
        # Mode Selection
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Color", "Grayscale"])
        self.mode_combo.currentTextChanged.connect(self.toggle_color_inputs)
        color_param_layout.addWidget(QLabel("Mode:"))
        color_param_layout.addWidget(self.mode_combo)

        # Color specific inputs
        self.mod_amp_label = QLabel("Mod Amp:")
        self.mod_amp_input = QLineEdit("90")
        self.mod_freq_label = QLabel("Mod Freq:")
        self.mod_freq_input = QLineEdit("3")
        self.hue_offset_label = QLabel("Hue Offset:")
        self.hue_offset_input = QLineEdit("60")
        self.min_brightness_label = QLabel("Min Bright:")
        self.min_brightness_input = QLineEdit("150")

        self.mod_amp_input.setValidator(QDoubleValidator(-1000.0, 1000.0, 4))
        self.mod_freq_input.setValidator(QDoubleValidator(0.0, 100.0, 4))
        self.hue_offset_input.setValidator(QDoubleValidator(-360.0, 720.0, 4))
        self.min_brightness_input.setValidator(QIntValidator(0, 255))
        
        color_param_layout.addWidget(self.mod_amp_label)
        color_param_layout.addWidget(self.mod_amp_input)
        color_param_layout.addWidget(self.mod_freq_label)
        color_param_layout.addWidget(self.mod_freq_input)
        color_param_layout.addWidget(self.hue_offset_label)
        color_param_layout.addWidget(self.hue_offset_input)
        color_param_layout.addWidget(self.min_brightness_label)
        color_param_layout.addWidget(self.min_brightness_input)
        
        main_layout.addLayout(color_param_layout)

        # Plot button
        self.plot_button = QPushButton("Render Fractal")
        self.plot_button.clicked.connect(self.plot_fractal)
        main_layout.addWidget(self.plot_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setEnabled(False)
        main_layout.addWidget(self.progress_bar)
        
        self.coord_label = QLabel("X: 0.000, Y: 0.000")
        main_layout.addWidget(self.coord_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(700, 700)
        self.image_label.setMouseTracking(True)
    
        self.image_label.mousePressEvent = self.mouse_press_event
        self.image_label.mouseReleaseEvent = self.mouse_release_event
        self.image_label.mouseMoveEvent = self.mouse_move_event
        self.image_label.wheelEvent = self.mouse_wheel_event

        main_layout.addWidget(self.image_label)
        self.dragging = False
        self.last_mouse_pos = None
        
        self.save_button = QPushButton("Save Image")
        self.save_button.clicked.connect(self.save_image)
        main_layout.addWidget(self.save_button)
                
        self.resolution_input.editingFinished.connect(self.adjust_spacing_for_resolution)
        self.toggle_color_inputs("Color") # Initial state

    def toggle_color_inputs(self, mode):
        is_color_mode = (mode == "Color")
        self.mod_amp_label.setVisible(is_color_mode)
        self.mod_amp_input.setVisible(is_color_mode)
        self.mod_freq_label.setVisible(is_color_mode)
        self.mod_freq_input.setVisible(is_color_mode)
        self.hue_offset_label.setVisible(is_color_mode)
        self.hue_offset_input.setVisible(is_color_mode)

    def adjust_spacing_for_resolution(self):
        try:
            new_resolution = int(self.resolution_input.text())
            if new_resolution <= 0:
                raise ValueError
    
            current_view_size = self.current_spacing * self.current_resolution
            new_spacing = current_view_size / new_resolution
    
            if new_spacing < 1e-20:
                new_spacing = 1e-20
    
            self.current_resolution = new_resolution
            self.current_spacing = new_spacing
    
            self.spacing_input.setText(f"{self.current_spacing:.20e}")
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
            self.current_center_x -= delta.x() * self.current_spacing
            self.current_center_y += delta.y() * self.current_spacing
            self.last_mouse_pos = event.position()
    
            self.center_x_input.setText(str(self.current_center_x))
            self.center_y_input.setText(str(self.current_center_y))
    
            self.plot_fractal()

    def mouse_wheel_event(self, event):
        if not hasattr(self, 'scaled_pixmap') or self.scaled_pixmap.isNull(): return
    
        pos = event.position()
        pixmap_rect = self.scaled_pixmap.rect()
        pixmap_rect.moveCenter(self.image_label.rect().center())
    
        if not pixmap_rect.contains(int(pos.x()), int(pos.y())):
            rel_x, rel_y = 0.5, 0.5
        else:
            rel_x = (pos.x() - pixmap_rect.left()) / pixmap_rect.width()
            rel_y = (pos.y() - pixmap_rect.top()) / pixmap_rect.height()
    
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        new_spacing = self.current_spacing / zoom_factor
    
        if not (1e-20 < new_spacing < 100.0): return
    
        fractal_x_before = self.current_center_x + (rel_x - 0.5) * self.current_resolution * self.current_spacing
        fractal_y_before = self.current_center_y - (rel_y - 0.5) * self.current_resolution * self.current_spacing
        fractal_x_after = self.current_center_x + (rel_x - 0.5) * self.current_resolution * new_spacing
        fractal_y_after = self.current_center_y - (rel_y - 0.5) * self.current_resolution * new_spacing
    
        self.current_center_x += fractal_x_before - fractal_x_after
        self.current_center_y += fractal_y_before - fractal_y_after
        self.current_spacing = new_spacing
    
        self.center_x_input.setText(f"{self.current_center_x:.20e}")
        self.center_y_input.setText(f"{self.current_center_y:.20e}")
        self.spacing_input.setText(f"{self.current_spacing:.20e}")
        self.plot_fractal()

    def update_coordinates(self, event):
        if not hasattr(self, 'scaled_pixmap') or self.scaled_pixmap.isNull(): return
        
        pos = event.position()
        label_rect = self.image_label.rect()
        pixmap_rect = self.scaled_pixmap.rect()
        pixmap_rect.moveCenter(label_rect.center())
    
        if pixmap_rect.contains(int(pos.x()), int(pos.y())):
            rel_x = (pos.x() - pixmap_rect.left()) / pixmap_rect.width()
            rel_y = (pos.y() - pixmap_rect.top()) / pixmap_rect.height()
            fractal_x = self.current_center_x + (rel_x - 0.5) * self.current_resolution * self.current_spacing
            fractal_y = self.current_center_y - (rel_y - 0.5) * self.current_resolution * self.current_spacing
            self.coord_label.setText(f"X: {fractal_x:.6f}, Y: {fractal_y:.6f}")
        else:
            self.coord_label.setText("X: -, Y: -")

    def plot_fractal(self):
        if self.is_rendering: return
        self.is_rendering = True
        self.plot_button.setEnabled(False)
            
        try:
            self.current_spacing = float(self.spacing_input.text())
            self.current_center_x = float(self.center_x_input.text())
            self.current_center_y = float(self.center_y_input.text())
            self.current_resolution = int(self.resolution_input.text())
            threshold = float(self.threshold_input.text())
            max_iter = int(self.max_iter_input.text())
        except ValueError:
            self.image_label.setText("Invalid input values")
            self.is_rendering = False
            self.plot_button.setEnabled(True)
            return
        
        self.progress_bar.setValue(0)
        self.progress_bar.setEnabled(True)
    
        self.worker = FractalWorker(
            self.current_resolution, self.current_spacing, self.current_center_x,
            self.current_center_y, threshold, max_iter
        )
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.result_ready.connect(self.display_fractal)
        self.worker.finished.connect(self.on_render_finished)
        self.worker.start()

    def display_fractal(self, fractal):
        mode = self.mode_combo.currentText()
        try:
            min_brightness = float(self.min_brightness_input.text())
        except ValueError:
            min_brightness = 150

        max_val = np.max(fractal)
        if max_val == 0: max_val = 1 # Prevent division by zero
        height, width = fractal.shape
        image = QImage(width, height, QImage.Format.Format_RGB888)

        # Get color parameters only if in color mode
        if mode == "Color":
            try:
                mod_amp = float(self.mod_amp_input.text())
                mod_freq = float(self.mod_freq_input.text())
                hue_offset = float(self.hue_offset_input.text())
            except ValueError:
                mod_amp, mod_freq, hue_offset = 90, 3, 60
    
        for y in range(height):
            for x in range(width):
                iter_count = fractal[y, x]
                if iter_count == 0:
                    color_val = QColor(0, 0, 0).rgb()
                else:
                    norm = math.log(iter_count + 1) / math.log(max_val + 1)
                    
                    if mode == "Color":
                        base_hue = 360 * norm
                        modulation = mod_amp * math.sin(mod_freq * math.pi * norm)
                        hue = int((base_hue + modulation + hue_offset) % 360)
                        value = max(min_brightness, min(255, 255 * ((1 - norm) ** 0.5)))
                        color = QColor.fromHsv(hue, 255, int(value))
                        color_val = color.rgb()
                    else: # Grayscale
                        gray_val = max(min_brightness, min(255, 255 * ((1 - norm) ** 0.5)))
                        color_val = QColor(int(gray_val), int(gray_val), int(gray_val)).rgb()

                image.setPixel(x, y, color_val)
    
        self.current_pixmap = QPixmap.fromImage(image)
        self.scaled_pixmap = self.current_pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        self.image_label.setPixmap(self.scaled_pixmap)
    
        self.plot_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_bar.setEnabled(False)

    def on_render_finished(self):
        self.is_rendering = False
        self.plot_button.setEnabled(True)

    def save_image(self):
        if not hasattr(self, 'current_pixmap') or self.current_pixmap.isNull():
            self.coord_label.setText("No image to save.")
            return
    
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Fractal Image", "fractal_snapshot.png", "PNG Files (*.png)"
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
    sys.exit(app.exec()
