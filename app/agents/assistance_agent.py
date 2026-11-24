from datetime import datetime
import os
import re
from app.models.models import Election, Candidate, Vote, User, AIAlert

class AdministrativeAssistanceAgent:
    """
    Administrative Assistance Agent (Module 7)
    Acts as an intelligent copilot for election administrators, providing
    status summaries, natural language question answering, and administrative checklists.
    """

    def __init__(self):
        self.name = "Administrative Assistance Agent"
        self.version = "1.0.0"

    def process_query(self, query: str, admin_user=None) -> dict:
        """Parse natural language query and formulate an actionable response."""
        q = (query or "").strip().lower()

        # 1. Checklist request
        if "checklist" in q or "prepare" in q or "steps" in q:
            return self._generate_checklist(q)

        # 2. Turnout / participation query
        if "turnout" in q or "participation" in q or "how many voted" in q:
            return self._get_turnout_response()

        # 3. Voter verification query
        if "verify" in q or "voter" in q or "pending" in q or "unverified" in q or "users" in q:
            return self._get_voter_status_response()

        # 4. Election status / list query
        if "election" in q or "status" in q or "active" in q or "running" in q:
            return self._get_elections_summary_response()

        # 5. Anomalies / Alerts query
        if "alert" in q or "anomaly" in q or "issue" in q or "threat" in q or "risk" in q:
            return self._get_alerts_summary_response()

        # 6. Default / Help response
        return self._get_help_response(query)

    def _get_elections_summary_response(self) -> dict:
        now = datetime.now()
        elections = Election.query.all()
        if not elections:
            return {
                'response': "Currently, there are **no elections** configured in the system. Use the **Create Election** button to set one up.",
                'suggestions': ["How to create an election?", "Show pre-election checklist", "Voter verification status"]
            }

        lines = [f"### 🗳️ Election Status Summary ({len(elections)} Total)\n"]
        for e in elections:
            votes = len(e.votes)
            candidates = len(e.candidates)
            if e.is_active and e.start_date <= now <= e.end_date:
                status_badge = "🟢 **ACTIVE**"
            elif e.start_date > now:
                status_badge = "🟡 **UPCOMING**"
            else:
                status_badge = "⚪ **ENDED**"

            lines.append(
                f"- **{e.title}** (ID: {e.id}) — {status_badge}\n"
                f"  - **Dates**: {e.start_date.strftime('%b %d, %Y %H:%M')} to {e.end_date.strftime('%b %d, %Y %H:%M')}\n"
                f"  - **Candidates**: {candidates} | **Votes Cast**: {votes}"
            )

        return {
            'response': "\n".join(lines),
            'suggestions': ["Show turnout details", "Run anomaly audit", "Generate polling day checklist"]
        }

    def _get_turnout_response(self) -> dict:
        total_voters = User.query.filter_by(is_verified=True).count()
        elections = Election.query.all()

        lines = [f"### 📊 Voter Participation & Turnout\n- **Total Verified Voters**: `{total_voters}`\n"]
        for e in elections:
            votes_count = len(e.votes)
            turnout_pct = (votes_count / total_voters * 100) if total_voters > 0 else 0
            lines.append(f"- **{e.title}**: **{votes_count}** votes cast (`{turnout_pct:.1f}%` turnout)")

        return {
            'response': "\n".join(lines),
            'suggestions': ["Check election anomalies", "View pending voter verifications", "Export results to Excel"]
        }

    def _get_voter_status_response(self) -> dict:
        total_users = User.query.count()
        verified = User.query.filter_by(is_verified=True).count()
        unverified = total_users - verified

        text = (
            f"### 👥 Voter Registration & Verification Overview\n\n"
            f"- **Total Registered Accounts**: `{total_users}`\n"
            f"- **Verified (Eligible to Vote)**: `{verified}`\n"
            f"- **Pending Approval**: `{unverified}`\n\n"
        )
        if unverified > 0:
            text += f"⚠️ **Action Required**: There are **{unverified}** pending voters waiting for verification. Go to **Manage Users** to review and approve their face and identity credentials."
        else:
            text += "✅ All registered voters are currently verified."

        return {
            'response': text,
            'suggestions': ["Go to Manage Users", "Check active elections", "Run monitoring scan"]
        }

    def _get_alerts_summary_response(self) -> dict:
        pending_alerts = AIAlert.query.filter_by(status='PENDING_REVIEW').all()
        if not pending_alerts:
            return {
                'response': "✅ **No Unresolved Alerts**: System integrity is clean. No pending anomalies or monitoring warnings have been flagged.",
                'suggestions': ["Run a fresh anomaly scan", "Check election status", "View audit trail"]
            }

        lines = [f"### ⚠️ Unresolved AI Alerts ({len(pending_alerts)} Total)\n"]
        for a in pending_alerts:
            lines.append(f"- `[{a.severity}]` **{a.title}** ({a.agent_name})\n  {a.message}")

        return {
            'response': "\n".join(lines),
            'suggestions': ["Review alerts in AI Center", "Run anomaly audit", "Election status"]
        }

    def _generate_checklist(self, q: str) -> dict:
        if "pre" in q or "setup" in q or "create" in q:
            title = "📋 Pre-Election Setup Checklist"
            items = [
                "[ ] Configure election title, description, and strict start/end timestamps.",
                "[ ] Add at least 2 vetted candidates with high-resolution photos and bios.",
                "[ ] Verify all candidate cryptographic IDs and election links.",
                "[ ] Process pending voter registrations and verify face encodings.",
                "[ ] Run pre-flight AI Monitoring scan to confirm system health = 100%."
            ]
        elif "post" in q or "result" in q or "close" in q:
            title = "📋 Post-Election Audit & Closure Checklist"
            items = [
                "[ ] Confirm election status has transitioned to ENDED.",
                "[ ] Run Integrity & Anomaly Analysis Agent to verify zero temporal or burst violations.",
                "[ ] Generate official Executive Election Summary report.",
                "[ ] Export certified ballot tally to Excel spreadsheet.",
                "[ ] Archive audit trail records and notify registered voters."
            ]
        else:
            title = "📋 Polling Day Operations Checklist"
            items = [
                "[ ] Verify Flask server and database connectivity.",
                "[ ] Monitor real-time voting velocity for unexpected bursts.",
                "[ ] Check pending voter support queries and approval requests.",
                "[ ] Review AI Alert Center for any high-severity integrity notifications.",
                "[ ] Ensure election closing countdown alerts are observed."
            ]

        body = f"### {title}\n" + "\n".join(items)
        return {
            'response': body,
            'suggestions': ["Check election status", "Run monitoring scan", "Show turnout"]
        }

    def _get_help_response(self, original_query: str) -> dict:
        return {
            'response': (
                f"I am your **Smart-Elect AI Administrative Assistant**. I can help you monitor and manage election operations.\n\n"
                f"**Here are things you can ask me:**\n"
                f"- `What is the current election status?`\n"
                f"- `How is voter turnout across active elections?`\n"
                f"- `Are there any pending voter approvals?`\n"
                f"- `Give me the pre-election setup checklist`\n"
                f"- `Show polling day checklist`\n"
                f"- `What alerts require my attention?`"
            ),
            'suggestions': ["Election status", "Voter turnout", "Checklists", "Pending alerts"]
        }
