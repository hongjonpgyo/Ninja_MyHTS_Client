from PyQt6.QtGui import QColor

def make_color_with_intensity(base_hex, intensity, min_alpha, max_alpha):
    """
    intensity: 0~1 (수량 비율)
    """
    r = int(base_hex[1:3], 16)
    g = int(base_hex[3:5], 16)
    b = int(base_hex[5:7], 16)

    alpha = min_alpha + int((max_alpha - min_alpha) * intensity)
    return QColor(r, g, b, alpha)