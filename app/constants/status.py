# app/constants/status.py

class ScanLineStatus:
    CREATED = "Created"
    ALLOCATED = "Allocated"
    IN_PROGRESS = "In-Progress"
    VARIANCE_APPROVED = "Variance Approved"
    COMPLETED = "Completed"
    DISCARDED = "Discarded"
    VARIATION_COUNT_COMPLETED = "Variation: Count Completed"
    VARIATION_ADDITIONAL_REQUIRED = "Variation: Additional Count Required"

    # Helper groups for filters / UI
    ACTIVE_STATUSES = [CREATED, IN_PROGRESS, ALLOCATED]
    OTHER_STATUSES = [COMPLETED, VARIATION_COUNT_COMPLETED, VARIATION_ADDITIONAL_REQUIRED, DISCARDED]


class ScanRecordStatus:
    SUBMITTED = "Submitted"
    COMPLETED = "Completed"
    VERIFIED = "Verified"
    VERIFICATION_FAILED = "Verification Failed"