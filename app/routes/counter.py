from flask import request, current_app, Blueprint, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.constants.status import ScanLineStatus
import time
from werkzeug.utils import secure_filename
from app.models import ScanLine, ScanRecord, BarcodeEntry
from app.utils.s3_helper import upload_to_s3, delete_from_s3, generate_presigned_url
from app import db

import os
from app.barcode_processor import process_barcode_image

bp = Blueprint("counter", __name__, url_prefix="/counter")


@bp.route("/dashboard")
@login_required
def dashboard():
    active_jobs = ScanLine.query.filter(
        ((ScanLine.counter_1_id == current_user.id) | (ScanLine.counter_2_id == current_user.id)) &
        (ScanLine.status.in_(ScanLineStatus.ACTIVE_STATUSES))
    ).all()

    other_jobs = ScanLine.query.filter(
        ((ScanLine.counter_1_id == current_user.id) | (ScanLine.counter_2_id == current_user.id)) &
        (ScanLine.status.in_(ScanLineStatus.OTHER_STATUSES))
    ).all()

    return render_template('counter_dashboard.html', active_jobs=active_jobs, other_jobs=other_jobs)


@bp.route('/view/<int:id>')
@login_required
def view_scan_line(id):
    """View details of a scan line for the counter."""
    line = ScanLine.query.get_or_404(id)

    # Only allow assigned counters to access
    if current_user.id not in [line.counter_1_id, line.counter_2_id]:
        flash("You are not assigned to this scan line.", "danger")
        return redirect(url_for('counter.dashboard'))

    # Fetch scan records linked to this line
    records = ScanRecord.query.filter_by(scan_line_id=line.id).all()
    # Generate presigned URLs for each record image
    for record in records:
        if record.image_path:
            record.image_url = generate_presigned_url(record.image_path)
        else:
            record.image_url = None
    return render_template('counter_view_scan_line.html', line=line, records=records)


@bp.route('/count/<int:line_id>')
@login_required
def count_page(line_id):
    """Render the counting interface for the counter."""
    line = ScanLine.query.get_or_404(line_id)

    # Restrict access to assigned counters only
    if current_user.id not in [line.counter_1_id, line.counter_2_id]:
        flash("You are not assigned to this scan line.", "danger")
        return redirect(url_for('counter.dashboard'))

    scanned_count = ScanRecord.query.filter_by(scan_line_id=line.id).count()
    remaining = (line.target_count or 0) - scanned_count
    return render_template(
        "counter_count_page.html",
        line=line,
        scanned_count=scanned_count,
        remaining=remaining
    )


@bp.route('/process_barcode', methods=['POST'])
@login_required
def process_barcode():
    """Process image only — detect barcodes but do NOT save ScanRecord."""
    try:
        file = request.files.get("image")
        if not file:
            return jsonify({"error": "No image uploaded"}), 400

        # Read bytes
        file.stream.seek(0)
        raw_bytes = file.read()

        # Process via barcode_processor
        result = process_barcode_image(raw_bytes)
        codes = result.get("codes", []) if isinstance(result, dict) else []
        codes = (codes + ["", "", ""])[:3]

        return jsonify({
            "success": True,
            "barcodes": codes,
            "message": result.get("message", "Processed")
        })

    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500
    

# --- Directory to store uploaded barcode images ---
UPLOAD_FOLDER = "app/static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@bp.route("/save_scan_record", methods=["POST"])
@login_required
def save_scan_record():
    line_id = request.form.get("line_id")
    barcode1 = (request.form.get("barcode_1") or "").strip()
    barcode2 = (request.form.get("barcode_2") or "").strip()
    barcode3 = (request.form.get("barcode_3") or "").strip()
    image = request.files.get("image")

    barcodes = [b for b in [barcode1, barcode2, barcode3] if b]

    # ✅ Step 1: Validate at least one barcode
    if not barcodes:
        return jsonify({"success": False, "error": "At least one barcode is required."}), 400

    # ✅ Step 2: Check if any barcode already exists in BarcodeEntry
    existing = BarcodeEntry.query.filter(BarcodeEntry.barcode.in_(barcodes)).first()
    if existing:
        return jsonify({
            "success": False,
            "error": "One or more of these barcodes already exist in the system."
        }), 400

    # ✅ Step 3: Proceed with image saving
    scan_line = ScanLine.query.get(line_id)
    if not scan_line:
        return jsonify({"success": False, "error": "Invalid scan line."}), 404

    filename = None
    s3_key=""
    if image:
        timestamp = str(time.time()).replace(".", "")
        filename = f"{timestamp}_{secure_filename(image.filename)}"
        s3_key = f"uploads/{filename}" 
        upload_to_s3(image, s3_key)

    # ✅ Step 4: Create ScanRecord
    record = ScanRecord(
        scan_line_id=scan_line.id,
        location_id=scan_line.location_id,
        warehouse_id=scan_line.warehouse_id,
        counter_user_id=current_user.id,
        barcode_1=barcode1 or None,
        barcode_2=barcode2 or None,
        barcode_3=barcode3 or None,
        image_path=s3_key,
    )

    db.session.add(record)
    db.session.flush()  # ✅ ensures record.id is available

    # ✅ Step 5: Create BarcodeEntry for each barcode
    for code in barcodes:
        db.session.add(BarcodeEntry(scan_record_id=record.id, barcode=code))

    # ✅ Step 6: Update ScanLine count and status
    scan_line.current_count = (scan_line.current_count or 0) + 1
    if scan_line.status == "Created":
        scan_line.status = "In-Progress"

    db.session.commit()

    # ✅ Step 7: Return JSON response for UI update
    return jsonify({
        "success": True,
        "record": {
            "barcode_1": record.barcode_1,
            "barcode_2": record.barcode_2,
            "barcode_3": record.barcode_3,
            "created_on": record.created_on.strftime("%Y-%m-%d %H:%M:%S"),
            "image_url": url_for("static", filename=record.image_path, _external=False),
        },
        "scanned_count": scan_line.current_count,
        "remaining": scan_line.target_count - scan_line.current_count
    })    


@bp.route("/raise_variation", methods=["POST"])
@login_required
def raise_variation():
    """
    Counter submits a variation request:
      - Type can be 'Count Completed' or 'Additional Count Required'
      - Locks the scan line
      - Updates status and remarks
    """
    try:
        line_id = request.form.get("line_id", type=int)
        variation_type = request.form.get("variation_type")  # 'count_completed' or 'additional_required'
        remarks = request.form.get("remarks", "")

        line = ScanLine.query.get_or_404(line_id)

        # Verify counter access
        if current_user.id not in [line.counter_1_id, line.counter_2_id]:
            return jsonify({"error": "Unauthorized"}), 403

        # Lock the job
        line.is_locked = True
        line.remarks = remarks

        if variation_type == "count_completed":
            line.status = "Variation: Count Completed"
        elif variation_type == "additional_required":
            line.status = "Variation: Additional Count Required"
        else:
            return jsonify({"error": "Invalid variation type"}), 400

        db.session.commit()

        return jsonify({
            "success": True,
            "status": line.status,
            "message": "Variation submitted successfully. Job locked until TL review."
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@bp.route("/delete_scan_record", methods=["POST"])
@login_required
def delete_scan_record():
    record_id = request.form.get("record_id")
    record = ScanRecord.query.get(record_id)

    if not record:
        return jsonify({"success": False, "error": "Record not found"}), 404

    # Only the counter who created it can delete
    if record.counter_user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized action"}), 403

    try:
        # ✅ Delete associated image file (if exists)
        if record.image_path:
            delete_from_s3(record.image_path)

        # ✅ Get related ScanLine before deleting
        scan_line = record.scan_line

        # ✅ Delete the record (BarcodeEntry cascade handles automatically)
        db.session.delete(record)
        db.session.commit()  # commit early to ensure the deletion is flushed

        # ✅ Recalculate the actual count from remaining ScanRecords
        if scan_line:
            new_count = ScanRecord.query.filter_by(scan_line_id=scan_line.id).count()
            scan_line.current_count = new_count
            db.session.commit()

        return jsonify({
            "success": True,
            "new_count": scan_line.current_count if scan_line else 0
        })

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to delete record: {e}")
        return jsonify({"success": False, "error": "Internal error during deletion"}), 50