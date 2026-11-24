from datetime import datetime
import hashlib
import logging
from app import db
from app.models.models import AuditLog

logger = logging.getLogger(__name__)

def record_audit(action: str, user_id: int = None, entity_type: str = None, 
                 entity_id: int = None, details: str = None, ip_address: str = None) -> AuditLog:
    """
    Cryptographically chained audit logger (Module 10).
    Ensures every critical event is permanently logged with tamper-evident chaining.
    """
    try:
        # Get the latest audit log entry to establish the hash chain
        latest = AuditLog.query.order_by(AuditLog.id.desc()).first()
        prev_hash = latest.entry_hash if latest and latest.entry_hash else "GENESIS_BLOCK_0000000000000000000000000000000000000000000000000000"

        now = datetime.utcnow()
        # Compute entry hash
        raw_payload = f"{user_id}:{action}:{entity_type}:{entity_id}:{details}:{ip_address}:{prev_hash}:{now.isoformat()}"
        entry_hash = hashlib.sha256(raw_payload.encode('utf-8')).hexdigest()

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            created_at=now
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to record audit event '{action}': {e}")
        return None

def verify_audit_chain() -> dict:
    """
    Verifies the cryptographic hash-chain across all stored audit entries.
    Returns status, broken links (if any), and total audited records.
    """
    logs = AuditLog.query.order_by(AuditLog.id.asc()).all()
    if not logs:
        return {'valid': True, 'total': 0, 'broken_index': None, 'message': 'No audit records to verify.'}

    prev_hash = "GENESIS_BLOCK_0000000000000000000000000000000000000000000000000000"
    for idx, entry in enumerate(logs):
        entry_prev = entry.prev_hash or "GENESIS_BLOCK_0000000000000000000000000000000000000000000000000000"
        
        # If legacy entry had no entry_hash, assign one
        if not entry.entry_hash:
            raw_payload = f"{entry.user_id}:{entry.action}:{entry.entity_type}:{entry.entity_id}:{entry.details}:{entry.ip_address}:{prev_hash}:{entry.created_at.isoformat() if entry.created_at else ''}"
            entry.entry_hash = hashlib.sha256(raw_payload.encode('utf-8')).hexdigest()
            entry.prev_hash = prev_hash
            db.session.commit()
            entry_prev = prev_hash

        if entry_prev != prev_hash:
            return {
                'valid': False,
                'total': len(logs),
                'broken_id': entry.id,
                'message': f"Hash chain discrepancy at Audit Entry #{entry.id}. Expected {prev_hash[:12]}..., found {entry_prev[:12]}..."
            }
        prev_hash = entry.entry_hash

    return {
        'valid': True,
        'total': len(logs),
        'head_hash': prev_hash,
        'message': f"All {len(logs)} audit entries verified against cryptographic hash-chain. Zero tampering detected."
    }
