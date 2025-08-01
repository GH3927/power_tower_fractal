import numpy as np

def compute_power_fractal(resolution, spacing, center_x, center_y):
    """
    Compute tetration fractal where z_n+1 = c^z_n.
    Returns array where 0 = converges, 1 = diverges.
    """
    x = np.linspace(center_x - resolution * spacing / 2, center_x + resolution * spacing / 2, resolution)
    y = np.linspace(center_y - resolution * spacing / 2, center_y + resolution * spacing / 2, resolution)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y
    Z = np.ones_like(C)  # Initial z = 1
    fractal = np.zeros((resolution, resolution))

    max_iter = 50
    threshold = 100.0  # Divergence threshold

    for i in range(max_iter):
        Z = C ** Z  # Tetration: z_n+1 = c^z_n
        mask = (np.abs(Z) > threshold) & (fractal == 0)
        fractal[mask] = 1
        # Handle NaN or inf values as divergent
        mask_nan_inf = (np.isnan(Z) | np.isinf(Z)) & (fractal == 0)
        fractal[mask_nan_inf] = 1
        if np.all(fractal == 1):
            break

    return fractal