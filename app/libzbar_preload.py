# app/libzbar_preload.py

import os
import ctypes
import logging

HEROKU_ZBAR_PATH = "/app/.apt/usr/lib/x86_64-linux-gnu/libzbar.so.0"


def preload_zbar_for_heroku():
    if os.path.exists(HEROKU_ZBAR_PATH):
        try:
            os.environ["LD_LIBRARY_PATH"] = "/app/.apt/usr/lib/x86_64-linux-gnu:/app/.apt/usr/lib"
            ctypes.cdll.LoadLibrary(HEROKU_ZBAR_PATH)
            import pyzbar
            from pyzbar import zbar_library
            zbar_library.load = lambda: (ctypes.cdll.LoadLibrary(HEROKU_ZBAR_PATH), [])

            logging.info("✅ libzbar manually loaded and pyzbar loader overridden (Heroku)")
        except Exception as e:
            logging.warning(f"Failed to load libzbar on Heroku: {e}")
    else:
        logging.info("Not Heroku – using default pyzbar loader")