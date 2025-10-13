# app/barcode_loader.py

import os
import ctypes
import logging

HEROKU_ZBAR_PATH = "/app/.apt/usr/lib/x86_64-linux-gnu/libzbar.so.0"

def get_decoder():
    try:
        if os.path.exists(HEROKU_ZBAR_PATH):
            os.environ["LD_LIBRARY_PATH"] = "/app/.apt/usr/lib/x86_64-linux-gnu:/app/.apt/usr/lib"
            ctypes.cdll.LoadLibrary(HEROKU_ZBAR_PATH)
            logging.info("✅ Heroku: Loaded libzbar using ctypes.")
        else:
            logging.info("✅ Local: Assuming libzbar is available on system.")
    except Exception as e:
        logging.warning(f"⚠️ Failed to preload libzbar: {e}")

    # Only import after lib is loaded
    from pyzbar.pyzbar import decode
    return decode