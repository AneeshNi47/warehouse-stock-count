from flask import Blueprint, jsonify

bp = Blueprint("api", __name__, url_prefix="/api/insights")

@bp.route("/dashboard")
def dashboard_data():
    data = {
        "totalLines": 42,
        "activeJobs": 8,
        "completedJobs": 30,
        "totalScans": 12340,
        "locations": ["KIZAD", "JEBEL_ALI"],
        "locationScans": [6000, 6340],
        "warehouses": ["W1", "W2", "W3"],
        "warehouseJobs": [10, 20, 12],
        "topCounters": [{"name": "Ali", "scans": 3200}, {"name": "Omar", "scans": 2700}],
    }
    return jsonify(data)