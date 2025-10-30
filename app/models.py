from . import db
from flask_login import UserMixin
from datetime import datetime
from app.constants.status import ScanLineStatus


# ============================
# USER MODEL
# ============================
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# ============================
# LOCATION MODEL
# ============================
class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_by = db.Column(db.String(100))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    warehouses = db.relationship("Warehouse", backref="location", lazy=True)
    scan_lines = db.relationship("ScanLine", backref="location", lazy=True)
    scan_records = db.relationship("ScanRecord", backref="location", lazy=True)

    def __repr__(self):
        return f"<Location {self.name}>"


# ============================
# WAREHOUSE MODEL
# ============================
class Warehouse(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    warehouse_name = db.Column(db.String(100), unique=True, nullable=False)

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.id", name="fk_warehouse_location_id"),
        nullable=False,
    )

    created_by = db.Column(db.String(100))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    scan_lines = db.relationship("ScanLine", backref="warehouse", lazy=True)
    scan_records = db.relationship("ScanRecord", backref="warehouse", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "warehouse_name": self.warehouse_name,
            "location_id": self.location_id,
        }

    def __repr__(self):
        return f"<Warehouse {self.warehouse_name}>"


# ============================
# SCAN LINE MODEL
# ============================
class ScanLine(db.Model):
    __tablename__ = "scan_lines"

    id = db.Column(db.Integer, primary_key=True)
    line_code = db.Column(db.String(100), unique=True, index=True, nullable=False)
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.id", name="fk_scanline_location_id"),
    )
    warehouse_id = db.Column(
        db.Integer,
        db.ForeignKey("warehouses.id", name="fk_scanline_warehouse_id"),
    )

    target_count = db.Column(db.Integer)
    current_count = db.Column(db.Integer, nullable=True, default=0)
    is_locked = db.Column(db.Boolean, default=False)   # 🔒 NEW
    remarks = db.Column(db.Text, nullable=True)   


    # Assigned Users
    counter_1_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_scanline_counter1_id"),
    )
    counter_2_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_scanline_counter2_id"),
    )
    team_leader_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_scanline_teamleader_id"),
    )

    # Status Lifecycle
    status = db.Column(db.String(50), default=ScanLineStatus.CREATED)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    scan_records = db.relationship("ScanRecord", backref="scan_line", lazy=True)

    counter_1 = db.relationship("User", foreign_keys=[counter_1_id], lazy=True)
    counter_2 = db.relationship("User", foreign_keys=[counter_2_id], lazy=True)
    team_leader = db.relationship("User", foreign_keys=[team_leader_user_id], lazy=True)

    def __repr__(self):
        return (
            f"<ScanLine ID={self.id} Status={self.status} Target={self.target_count}>"
        )


# ============================
# SCAN RECORD MODEL
# ============================
class ScanRecord(db.Model):
    __tablename__ = "scan_records"

    id = db.Column(db.Integer, primary_key=True)

    scan_line_id = db.Column(
        db.Integer,
        db.ForeignKey("scan_lines.id", name="fk_scanrecord_scanline_id"),
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.id", name="fk_scanrecord_location_id"),
    )
    warehouse_id = db.Column(
        db.Integer,
        db.ForeignKey("warehouses.id", name="fk_scanrecord_warehouse_id"),
    )
    counter_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_scanrecord_counter_id"),
    )
    quantity = db.Column(db.Integer, default=1, nullable=True)

    barcode_1 = db.Column(db.String(100))
    barcode_2 = db.Column(db.String(100))
    barcode_3 = db.Column(db.String(100))
    image_path = db.Column(db.String(255))

    # Status fields
    status = db.Column(db.String(50), default="Scanned")  # Scanned / Completed
    verification_status = db.Column(
        db.String(50), default="Pending"
    )  # Verified / Error / Pending

    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    counter_user = db.relationship("User", foreign_keys=[counter_user_id], lazy=True)

    def __repr__(self):
        return (
            f"<ScanRecord ID={self.id} Status={self.status} Verification={self.verification_status}>"
        )
    

class BarcodeEntry(db.Model):
    __tablename__ = 'barcode_entry'

    id = db.Column(db.Integer, primary_key=True)
    scan_record_id = db.Column(db.Integer, db.ForeignKey('scan_records.id', ondelete='CASCADE'))
    barcode = db.Column(db.String(255), nullable=False)
    __table_args__ = (
            db.Index('idx_barcode_unique', 'barcode', unique=True),
        )

    scan_record = db.relationship('ScanRecord', backref=db.backref('barcodes', cascade="all, delete-orphan"))