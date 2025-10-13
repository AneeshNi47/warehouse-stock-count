import os
import logging
from pyzbar import zbar_library

# Try to manually load zbar shared lib if on Heroku
HEROKU_ZBAR_PATH = "/app/.apt/usr/lib/x86_64-linux-gnu/libzbar.so.0"

try:
    if os.path.exists(HEROKU_ZBAR_PATH):
        # Set env variable (just in case pyzbar or subprocesses need it)
        os.environ["LD_LIBRARY_PATH"] = "/app/.apt/usr/lib/x86_64-linux-gnu:/app/.apt/usr/lib"
        # Force pyzbar to load explicitly
        zbar_library.load(HEROKU_ZBAR_PATH)
        logging.info("✅ Loaded libzbar explicitly from Heroku apt path.")
    else:
        # Let pyzbar try to auto-load from system (brew install zbar)
        zbar_library.load()
        logging.info("✅ Loaded system libzbar")
except Exception as e:
    logging.warning(f"⚠️ Failed to load zbar shared library: {e}")


def process_barcode_image(image_data):
    """
    Process an uploaded image and extract barcode data

    Args:
        image_data: Can be a file path, file object, or base64 string

    Returns:
        dict: {
            success: bool,
            codes: list of strings,
            message: string
        }
    """
    try:
        import cv2
        import numpy as np
        from pyzbar.pyzbar import decode
        from PIL import Image
        import io, base64

        # Decode image input
        if isinstance(image_data, str):
            # Base64 input
            image_bytes = base64.b64decode(image_data)
            pil_img = Image.open(io.BytesIO(image_bytes))
        else:
            # Raw file bytes
            pil_img = Image.open(io.BytesIO(image_data))

        # Convert PIL → OpenCV
        image = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

        def enhance_image(img):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.convertScaleAbs(gray, alpha=1.6, beta=0)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            return gray

        def rotate_image(img, angle):
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            cos, sin = abs(M[0, 0]), abs(M[0, 1])
            nW = int((h * sin) + (w * cos))
            nH = int((h * cos) + (w * sin))
            M[0, 2] += (nW / 2) - center[0]
            M[1, 2] += (nH / 2) - center[1]
            return cv2.warpAffine(img, M, (nW, nH))

        gray = enhance_image(image)
        all_decoded = []

        # Multi-angle, multi-scale scanning
        for angle in [0, 90, 180, 270]:
            rotated = rotate_image(gray, angle)
            for scale in [1.0, 1.25, 1.5]:
                resized = cv2.resize(rotated, (0, 0), fx=scale, fy=scale)
                decoded = decode(resized)
                all_decoded.extend(decoded)

        if not all_decoded:
            return {
                'success': False,
                'codes': [],
                'message': 'No barcodes detected'
            }

        # Deduplicate and sort top → bottom
        seen = set()
        unique = []
        for obj in all_decoded:
            data = obj.data.decode('utf-8')
            if data not in seen:
                seen.add(data)
                unique.append(obj)
        unique = sorted(unique, key=lambda o: o.rect.top)

        # Extract up to 3 barcodes
        codes = [obj.data.decode('utf-8') for obj in unique[:3]]

        return {
            'success': True,
            'codes': codes,
            'message': f'{len(codes)} barcode(s) detected successfully'
        }

    except Exception as e:
        return {
            'success': False,
            'codes': [],
            'message': f'Error processing image: {str(e)}'
        }