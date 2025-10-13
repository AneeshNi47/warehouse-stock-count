import os
import ctypes
import logging


def preload_libzbar():
    """
    Loads libzbar manually via ctypes on Heroku (before pyzbar import)
    """
    heroku_lib_path = "/app/.apt/usr/lib/x86_64-linux-gnu/libzbar.so.0"
    if os.path.exists(heroku_lib_path):
        try:
            os.environ["LD_LIBRARY_PATH"] = "/app/.apt/usr/lib/x86_64-linux-gnu:/app/.apt/usr/lib"
            ctypes.cdll.LoadLibrary(heroku_lib_path)
            logging.info("✅ Preloaded libzbar.so.0 from Heroku apt path")
        except Exception as e:
            logging.error(f"❌ Failed to preload libzbar: {e}")
    else:
        logging.info("libzbar not found in Heroku path — assuming local environment")