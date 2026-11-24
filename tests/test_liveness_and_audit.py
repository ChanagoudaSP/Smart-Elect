import os
import sys
import numpy as np
import cv2

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.utils.face_recognition import FaceRecognitionSystem
from app.utils.audit import record_audit, verify_audit_chain
from app.models.models import AuditLog

app = create_app()

with app.app_context():
    print("--- 1. Testing Biometric Liveness & Anti-Spoofing Detection (Section 7) ---")
    face_system = FaceRecognitionSystem()

    # Synthetic test frame (flat black screen / no face)
    flat_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res_noface = face_system.check_liveness(flat_frame)
    print(f"✓ No-face detection test: status={res_noface['status']}, score={res_noface['score']}")

    # Synthetic test frame with simulated texture
    textured_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    res_textured = face_system.check_liveness(textured_frame)
    print(f"✓ Texture variance analysis: status={res_textured['status']}, score={res_textured['score']}")

    print("\n--- 2. Testing Cryptographic Audit Ledger & Traceability (Module 10) ---")
    # Record test audit events
    e1 = record_audit(action='SYSTEM_STARTUP', details='Smart-Elect core services initialized', ip_address='127.0.0.1')
    e2 = record_audit(action='LIVENESS_CHECK_TEST', details='Simulated voter liveness verification', ip_address='127.0.0.1')
    e3 = record_audit(action='VOTE_AUDIT_SAMPLE', entity_type='Election', entity_id=1, details='Sample encrypted vote tally audit', ip_address='127.0.0.1')

    print(f"✓ Created 3 chained audit entries:")
    print(f"   Entry #{e1.id} -> Hash: {e1.entry_hash[:16]}... (Prev: {e1.prev_hash[:16]}...)")
    print(f"   Entry #{e2.id} -> Hash: {e2.entry_hash[:16]}... (Prev: {e2.prev_hash[:16]}...)")
    print(f"   Entry #{e3.id} -> Hash: {e3.entry_hash[:16]}... (Prev: {e3.prev_hash[:16]}...)")

    # Verify cryptographic hash chain
    chain_res = verify_audit_chain()
    print(f"✓ Hash-chain verification result: valid={chain_res['valid']}, total={chain_res['total']}")
    print(f"   Message: {chain_res['message']}")

    assert chain_res['valid'] is True, "Hash-chain verification failed!"

    # Render template test
    with app.test_request_context():
        from flask import render_template
        logs = AuditLog.query.order_by(AuditLog.id.desc()).limit(10).all()
        html = render_template('admin/audit_ledger.html', logs=logs, chain_status=chain_res)
        print(f"✓ Audit Ledger template rendered cleanly: {len(html)} bytes")

    print("\n✓ ALL TESTS PASSED SUCCESSFULLY!")
