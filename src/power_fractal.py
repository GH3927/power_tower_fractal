import numpy as np

def compute_power_fractal(resolution, spacing, center_x, center_y, threshold=100.0):
    x = np.linspace(center_x - resolution * spacing / 2, center_x + resolution * spacing / 2, resolution, dtype=np.float64)
    y = np.linspace(center_y - resolution * spacing / 2, center_y + resolution * spacing / 2, resolution, dtype=np.float64)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y
    Z = np.ones_like(C, dtype=np.complex128)  # 고정밀 복소수 사용
    fractal = np.zeros((resolution, resolution), dtype=np.float64)

    max_iter = 50

    for i in range(max_iter):
        # 거듭제곱 계산 시 안정성 확보
        Z = np.where(np.abs(Z) < threshold, C ** Z, Z)  # 발산하지 않은 경우에만 계산
        mask = (np.abs(Z) > threshold) & (fractal == 0)
        fractal[mask] = 1
        mask_nan_inf = (np.isnan(Z) | np.isinf(Z)) & (fractal == 0)
        fractal[mask_nan_inf] = 1
        if np.all(fractal != 0):  # 모든 픽셀이 처리되면 종료
            break

    return fractal