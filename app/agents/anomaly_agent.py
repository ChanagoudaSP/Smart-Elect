from datetime import datetime, timedelta
from collections import defaultdict
import logging
from app import db
from app.models.models import Election, Candidate, Vote, User, AIAlert

logger = logging.getLogger(__name__)

class IntegrityAnomalyAgent:
    """
    Integrity and Anomaly Analysis Agent (Module 8)
    Detects irregular voting patterns, temporal anomalies, velocity surges,
    and voter integrity issues, flagging them for human administrator review.
    """

    def __init__(self):
        self.name = "Integrity & Anomaly Analysis Agent"
        self.version = "1.0.0"

    def scan(self):
        """Analyze transaction logs and ballot patterns for anomalies."""
        now = datetime.now()
        anomalies = []
        alerts_created = []

        elections = Election.query.all()

        for election in elections:
            votes = Vote.query.filter_by(election_id=election.id).order_by(Vote.created_at.asc()).all()

            if not votes:
                continue

            # 1. Temporal Window Check: Any vote recorded before start_date or after end_date?
            invalid_time_votes = [
                v for v in votes
                if v.created_at and (v.created_at < election.start_date or v.created_at > election.end_date)
            ]
            if invalid_time_votes:
                msg = (f"Found {len(invalid_time_votes)} vote(s) in election '{election.title}' "
                       f"recorded outside active window ({election.start_date} to {election.end_date}).")
                anomalies.append({
                    'type': 'Temporal Violation',
                    'election_id': election.id,
                    'severity': 'HIGH',
                    'description': msg,
                    'recommendation': 'Audit server timestamp sync and investigate database transactions.'
                })
                alerts_created.append(self._create_alert(
                    election_id=election.id,
                    alert_type='temporal_anomaly',
                    severity='HIGH',
                    title=f'Out-of-Window Votes Detected: {election.title}',
                    message=msg
                ))

            # 2. Velocity / Rapid Burst Check:
            # Check if > 5 votes were cast within any rolling 60-second window
            time_windows = defaultdict(int)
            for v in votes:
                if v.created_at:
                    # Group by minute
                    minute_key = v.created_at.strftime('%Y-%m-%d %H:%M')
                    time_windows[minute_key] += 1

            for minute_str, count in time_windows.items():
                if count >= 8:  # Burst threshold
                    msg = (f"High velocity voting burst detected: {count} votes cast in a single minute ({minute_str}) "
                           f"in election '{election.title}'.")
                    anomalies.append({
                        'type': 'Velocity Surge',
                        'election_id': election.id,
                        'severity': 'WARNING',
                        'description': msg,
                        'recommendation': 'Verify bot protection and review client IP access logs.'
                    })
                    alerts_created.append(self._create_alert(
                        election_id=election.id,
                        alert_type='velocity_surge',
                        severity='WARNING',
                        title=f'Voting Surge Alert ({minute_str})',
                        message=msg
                    ))

            # 3. Candidate Distribution Skewness Check (if total votes >= 15)
            if len(votes) >= 15 and len(election.candidates) > 1:
                candidate_tallies = defaultdict(int)
                for v in votes:
                    candidate_tallies[v.candidate_id] += 1
                
                max_candidate_votes = max(candidate_tallies.values())
                dominance_ratio = max_candidate_votes / len(votes)
                if dominance_ratio > 0.95:
                    msg = (f"Extreme vote concentration in '{election.title}': One candidate has "
                           f"{dominance_ratio * 100:.1f}% ({max_candidate_votes}/{len(votes)}) of all cast votes.")
                    anomalies.append({
                        'type': 'Distribution Skew',
                        'election_id': election.id,
                        'severity': 'INFO',
                        'description': msg,
                        'recommendation': 'Review candidate verification and ballot distribution.'
                    })

        # 4. User Registration Integrity Checks
        unverified_users_with_votes = db.session.query(Vote).join(User, Vote.user_id == User.id)\
            .filter(User.is_verified == False).count()
        if unverified_users_with_votes > 0:
            msg = f"Critical Integrity Violation: {unverified_users_with_votes} vote(s) found from unverified accounts."
            anomalies.append({
                'type': 'Authorization Integrity',
                'severity': 'CRITICAL',
                'description': msg,
                'recommendation': 'Immediately invalidate unauthorized ballots and audit user verification gate.'
            })
            alerts_created.append(self._create_alert(
                election_id=None,
                alert_type='unverified_voter_ballot',
                severity='CRITICAL',
                title='Unauthorized Voter Ballots Detected',
                message=msg
            ))

        risk_level = 'LOW'
        if any(a['severity'] == 'CRITICAL' for a in anomalies):
            risk_level = 'CRITICAL'
        elif any(a['severity'] == 'HIGH' for a in anomalies):
            risk_level = 'HIGH'
        elif any(a['severity'] == 'WARNING' for a in anomalies):
            risk_level = 'MEDIUM'

        return {
            'agent': self.name,
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
            'risk_level': risk_level,
            'total_anomalies_flagged': len(anomalies),
            'anomalies': anomalies,
            'alerts_created_count': len([a for a in alerts_created if a is not None])
        }

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
