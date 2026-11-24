from datetime import datetime, timedelta
import json
import logging
from app import db
from app.models.models import Election, Candidate, Vote, User, AIAlert

logger = logging.getLogger(__name__)

class ElectionMonitoringAgent:
    """
    Election Monitoring Agent (Module 6)
    Continuously monitors election status, voter verification backlog,
    turnout pace, and configuration issues.
    """

    def __init__(self):
        self.name = "Election Monitoring Agent"
        self.version = "1.0.0"

    def scan(self):
        """Perform a full monitoring scan and generate alerts."""
        now = datetime.now()
        findings = []
        alerts_created = []

        total_users = User.query.count()
        verified_users = User.query.filter_by(is_verified=True).count()
        unverified_users = total_users - verified_users

        # Check unverified user backlog
        if unverified_users > 0:
            msg = f"{unverified_users} registered voter(s) are awaiting admin verification."
            findings.append({
                'category': 'Voter Verification',
                'severity': 'WARNING' if unverified_users > 5 else 'INFO',
                'message': msg
            })
            if unverified_users > 3:
                alerts_created.append(self._create_alert(
                    election_id=None,
                    alert_type='voter_verification',
                    severity='WARNING',
                    title='Voter Verification Backlog',
                    message=msg
                ))

        elections = Election.query.all()
        active_count = 0
        upcoming_count = 0
        ended_count = 0

        for election in elections:
            candidate_count = len(election.candidates)
            vote_count = len(election.votes)
            turnout_pct = (vote_count / verified_users * 100) if verified_users > 0 else 0

            # 1. Configuration check: Active or Upcoming election with < 2 candidates
            if election.is_active and candidate_count < 2:
                msg = f"Election '{election.title}' has only {candidate_count} candidate(s). Contested elections require at least 2 candidates."
                findings.append({
                    'category': 'Election Configuration',
                    'election_id': election.id,
                    'severity': 'HIGH',
                    'message': msg
                })
                alerts_created.append(self._create_alert(
                    election_id=election.id,
                    alert_type='configuration',
                    severity='HIGH',
                    title=f'Insufficient Candidates: {election.title}',
                    message=msg
                ))

            # 2. Status categorization
            if election.start_date <= now <= election.end_date and election.is_active:
                active_count += 1
                time_left = election.end_date - now
                hours_left = time_left.total_seconds() / 3600

                # Impending close alert
                if hours_left <= 2:
                    msg = f"Election '{election.title}' will close in {int(time_left.total_seconds() // 60)} minutes."
                    findings.append({
                        'category': 'Deadline',
                        'election_id': election.id,
                        'severity': 'WARNING',
                        'message': msg
                    })
                    alerts_created.append(self._create_alert(
                        election_id=election.id,
                        alert_type='deadline',
                        severity='WARNING',
                        title=f'Closing Soon: {election.title}',
                        message=msg
                    ))

                # Low turnout alert
                if hours_left < 6 and turnout_pct < 10 and verified_users > 5:
                    msg = f"Low turnout warning for '{election.title}': Current turnout is {turnout_pct:.1f}% ({vote_count}/{verified_users} votes)."
                    findings.append({
                        'category': 'Turnout',
                        'election_id': election.id,
                        'severity': 'WARNING',
                        'message': msg
                    })

            elif election.start_date > now:
                upcoming_count += 1
            else:
                ended_count += 1

        # Calculate overall system health score (0 - 100)
        deductions = 0
        for f in findings:
            if f['severity'] == 'HIGH':
                deductions += 20
            elif f['severity'] == 'WARNING':
                deductions += 10
            elif f['severity'] == 'INFO':
                deductions += 2
        health_score = max(0, 100 - deductions)

        summary = {
            'agent': self.name,
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
            'health_score': health_score,
            'status': 'Optimal' if health_score >= 85 else ('Attention Required' if health_score >= 60 else 'Critical'),
            'metrics': {
                'total_elections': len(elections),
                'active_elections': active_count,
                'upcoming_elections': upcoming_count,
                'ended_elections': ended_count,
                'verified_voters': verified_users,
                'unverified_voters': unverified_users,
            },
            'findings': findings,
            'alerts_created_count': len([a for a in alerts_created if a is not None])
        }

        return summary

    def _create_alert(self, election_id, alert_type, severity, title, message):
        """Deduplicate and insert alert into DB if not existing in PENDING_REVIEW state."""
        try:
            existing = AIAlert.query.filter_by(
                election_id=election_id,
                alert_type=alert_type,
                title=title,
                status='PENDING_REVIEW'
            ).first()

            if not existing:
                alert = AIAlert(
                    election_id=election_id,
                    agent_name=self.name,
                    alert_type=alert_type,
                    severity=severity,
                    title=title,
                    message=message,
                    status='PENDING_REVIEW'
                )
                db.session.add(alert)
                db.session.commit()
                return alert
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating AI alert: {e}")
        return None
