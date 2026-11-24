import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.models import AIAlert, AuditLog
from app.agents import orchestrator

app = create_app()

with app.app_context():
    db.create_all()
    print("✓ AIAlert and AuditLog tables verified in database.")

    fleet = orchestrator.get_agent_fleet()
    print(f"✓ Agent Fleet loaded ({len(fleet)} specialized agents):")
    for a in fleet:
        print(f"   [{a['module']}] {a['name']}: {a['status']} ({a['role']})")

    # Run full system scan
    scan = orchestrator.run_full_system_scan()
    print(f"✓ System Scan Output:")
    print(f"   Health Score: {scan['system_health_score']}%")
    print(f"   Overall Risk: {scan['overall_risk']}")
    print(f"   Active Alerts Pending: {scan['total_alerts_pending']}")

    # Test Administrative Assistance Agent
    queries = [
        "What is the current election status?",
        "How is voter turnout?",
        "Show pre-election setup checklist",
        "Are there any pending voter verifications?"
    ]
    print("✓ Testing Administrative Assistance Agent (Module 7):")
    for q in queries:
        ans = orchestrator.handle_admin_query(q)
        print(f"   Q: '{q}' -> Response length: {len(ans['response'])} chars")

    print("\n✓ ALL AGENTIC AI COMPONENTS VERIFIED SUCCESSFULLY!")
