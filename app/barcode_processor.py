"""
Barcode processor module
Processes uploaded images and extracts up to 3 real barcodes
"""

import io
import base64
from PIL import Image
import cv2
import numpy as np
from pyzbar.pyzbar import decode  # Safe now, libzbar is preloaded

def process_barcode_image(image_data):
    """
    Process an uploaded image and extract barcode data

    Args:
        image_data: Can be a file path, file object, or base64 string

    Returns:
        dict: {success: bool, codes: list, message: str}
    """
    try:
        # Decode input image
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
            pil_img = Image.open(io.BytesIO(image_bytes))
        else:
            pil_img = Image.open(io.BytesIO(image_data))

        # Convert PIL → OpenCV
        image = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

        # Enhance + grayscale
        def enhance(img):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=0)
            return cv2.GaussianBlur(gray, (3, 3), 0)

        def rotate(img, angle):
            (h, w) = img.shape[:2]
            M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            return cv2.warpAffine(img, M, (w, h))

        gray = enhance(image)
        all_decoded = []

        for angle in [0, 90, 180, 270]:
            rotated = rotate(gray, angle)
            for scale in [1.0, 1.25, 1.5]:
                resized = cv2.resize(rotated, (0, 0), fx=scale, fy=scale)
                decoded = decode(resized)
                all_decoded.extend(decoded)

        if not all_decoded:
            return {'success': False, 'codes': [], 'message': 'No barcodes detected'}

        # Deduplicate
        seen = set()
        unique = []
        for obj in all_decoded:
            data = obj.data.decode('utf-8')
            if data not in seen:
                seen.add(data)
                unique.append(obj)

        # Sort top → bottom and return top 3
        unique = sorted(unique, key=lambda o: o.rect.top)
        codes = [obj.data.decode('utf-8') for obj in unique[:3]]

        return {'success': True, 'codes': codes, 'message': f'{len(codes)} barcode(s) detected successfully'}

    except Exception as e:
        return {'success': False, 'codes': [], 'message': f'Error processing image: {str(e)}'}