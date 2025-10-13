from app.libzbar_preload import preload_libzbar
preload_libzbar()

from app import create_app, db
import os


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=os.environ.get("FLASK_DEBUG", True))