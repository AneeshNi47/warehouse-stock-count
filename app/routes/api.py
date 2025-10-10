from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func
from app.models import db, User, ScanLine, ScanRecord


bp = Blueprint("api", __name__, url_prefix="/api/insights")


@bp.route("/dashboard")
@login_required
def dashboard_insights():
    location_id = request.args.get("location")
    warehouse_id = request.args.get("warehouse")
    tl_id = request.args.get("tl")

    query = ScanLine.query

    if location_id:
        query = query.filter(ScanLine.location_id == location_id)
    if warehouse_id:
        query = query.filter(ScanLine.warehouse_id == warehouse_id)
    if tl_id:
        query = query.filter(ScanLine.team_leader_user_id == tl_id)
        
    lines = query.all()

    total_lines = len(lines)
    total_scans = sum(len(line.scan_records) for line in lines)
    active_jobs = sum(1 for line in lines if line.status in ["Allocated", "In-Progress"])
    completed_jobs = sum(1 for line in lines if line.status == "Completed")

    location_data = {}
    warehouse_data = {}

    for line in lines:
        location_data[line.location.name] = location_data.get(line.location.name, 0) + len(line.scan_records)
        warehouse_data[line.warehouse.warehouse_name] = warehouse_data.get(line.warehouse.warehouse_name, 0) + len(line.scan_records)

    top_counters = (
        db.session.query(User.username, func.count(ScanRecord.id))
        .join(ScanRecord, ScanRecord.counter_user_id == User.id)
        .group_by(User.id)
        .order_by(func.count(ScanRecord.id).desc())
        .limit(5)
        .all()
    )
    return jsonify({
        "success": True,
        "totalLines": total_lines,
        "activeJobs": active_jobs,
        "completedJobs": completed_jobs,
        "totalScans": total_scans,
        "locations": list(location_data.keys()),
        "locationScans": list(location_data.values()),
        "warehouses": list(warehouse_data.keys()),
        "warehouseJobs": list(warehouse_data.values()),
        "topCounters": [{"name": name, "scans": count} for name, count in top_counters],
    })
