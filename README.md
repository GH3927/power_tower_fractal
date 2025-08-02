# Power Fractal Explorer

**Power Fractal Explorer** is a graphical application for visualizing and exploring power tower fractals, using PyQt6 for the interface. It offers interactive zooming and real-time rendering for mathematical visualization enthusiasts.

---

## ✨ Features

- Interactive GUI with zoom & pan support  
- Real-time fractal rendering with progress updates  
- Save fractal images as PNG  
- Lightweight and easy to use  
- Built with PyQt6 and NumPy

---

## 📦 Requirements

If running from source:

- Python 3.11  
- PyQt6  
- NumPy  

> 📄 See `requirements.txt` for exact versions.

---

## 🚀 How to Run

### 🔧 Option 1: Run from source (Python required)

1. Set up the environment:

    ```bash
    conda create -n tetration python=3.11
    conda activate tetration
    pip install -r requirements.txt
    ```

2. Run the application:

    ```bash
    python src/power_fractal_app.py
    ```

---

### 🧊 Option 2: Run the executable (no Python required)

1. Download or locate the built executable file:

    ```
    power_fractal_app.exe
    ```

2. Double-click to launch the app — no installation required.

> ✅ This executable was created using PyInstaller and includes all necessary dependencies.

---

## 🖼 Screenshots

*(Add screenshots of the app interface here if available)*

---

## 🔧 Building the Executable (Optional)

To build your own standalone executable using PyInstaller:

```bash
pyinstaller src/power_fractal_app.py --onefile --noconsole