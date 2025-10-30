import io
import base64
from PIL import Image
import cv2
import numpy as np
from pyzbar.pyzbar import decode

def process_barcode_image(image_data):
    """
    Optimized, sorted (top→bottom), and version-safe barcode processor
    """
    try:
        # Decode input image once
        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
            pil_img = Image.open(io.BytesIO(image_bytes))
        else:
            pil_img = Image.open(io.BytesIO(image_data))

        # Convert PIL → OpenCV
        image = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

        # ✅ Resize if too large (max dimension = 1280 px)
        h, w = image.shape[:2]
        if max(h, w) > 1280:
            scale = 1280 / max(h, w)
            image = cv2.resize(image, (int(w * scale), int(h * scale)))

        # ✅ Preprocess once
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        # ✅ Try OpenCV barcode detector (handles both signatures)
        detector = cv2.barcode_BarcodeDetector()
        try:
            retval, decoded_info, decoded_type, corners = detector.detectAndDecode(gray)
        except ValueError:
            retval, decoded_info, decoded_type = detector.detectAndDecode(gray)
            corners = None

        results = []

        # Add OpenCV results (with coordinates)
        if retval and decoded_info:
            for text, pts in zip(decoded_info, corners or []):
                if text:
                    y_avg = np.mean(pts[:, 1]) if pts is not None else 0
                    results.append({'code': text, 'y': y_avg})

        # ✅ Fallback to pyzbar (and also record coordinates)
        if not results:
            decoded_objects = decode(gray)
            for obj in decoded_objects:
                (x, y, w, h) = obj.rect
                results.append({'code': obj.data.decode('utf-8'), 'y': y + h/2})

            # Try one rotation if nothing found
            if not results:
                rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
                decoded_objects = decode(rotated)
                for obj in decoded_objects:
                    (x, y, w, h) = obj.rect
                    results.append({'code': obj.data.decode('utf-8'), 'y': y + h/2})

        if not results:
            return {'success': False, 'codes': [], 'message': 'No barcodes detected'}

        # ✅ Sort top → bottom (ascending y)
        results.sort(key=lambda r: r['y'])

        # ✅ Extract only top 3 unique codes
        seen = set()
        codes = []
        for r in results:
            if r['code'] not in seen:
                seen.add(r['code'])
                codes.append(r['code'])
            if len(codes) >= 3:
                break

        return {'success': True, 'codes': codes, 'message': f'{len(codes)} barcode(s) detected successfully'}

    except Exception as e:
        print(e)
        return {'success': False, 'codes': [], 'message': f'Error processing image: {str(e)}'}