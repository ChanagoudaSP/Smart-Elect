from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from app import db
from app.models.models import Election, Candidate, Vote, User, AIAlert, AuditLog
from app.agents import orchestrator

bp = Blueprint('ai_agent', __name__, url_prefix='/admin/ai')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Administrator privileges required to access the AI Agent Center.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Main Agentic AI Center dashboard."""
    fleet = orchestrator.get_agent_fleet()
    pending_alerts = AIAlert.query.filter_by(status='PENDING_REVIEW').order_by(AIAlert.created_at.desc()).all()
    resolved_alerts = AIAlert.query.filter(AIAlert.status != 'PENDING_REVIEW').order_by(AIAlert.created_at.desc()).limit(10).all()
    elections = Election.query.order_by(Election.created_at.desc()).all()

    # Get latest scan if available or perform quick status count
    total_users = User.query.count()
    verified_users = User.query.filter_by(is_verified=True).count()
    active_elections = Election.query.filter_by(is_active=True).count()

    return render_template(
        'admin/ai_center.html',
        fleet=fleet,
        pending_alerts=pending_alerts,
        resolved_alerts=resolved_alerts,
        elections=elections,
        last_scan=orchestrator.last_scan_results,
        total_users=total_users,
        verified_users=verified_users,
        active_elections=active_elections
    )

@bp.route('/scan', methods=['POST'])
@login_required
@admin_required
def run_scan():
    """Trigger a full system monitoring and anomaly scan."""
    try:
        results = orchestrator.run_full_system_scan()
        
        # Log to audit trail
        audit = AuditLog(
            user_id=current_user.id,
            action='AI_FULL_SCAN_EXECUTED',
            details=f"Scan completed with health score {results.get('system_health_score')} and risk {results.get('overall_risk')}",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'AI Agent Fleet scan completed successfully.',
            'data': results
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/chat', methods=['POST'])
@login_required
@admin_required
def chat():
    """Administrative Assistant conversational copilot endpoint."""
    data = request.get_json() or {}
    user_query = data.get('message', '').strip()

    if not user_query:
        return jsonify({'success': False, 'error': 'Query message cannot be empty.'}), 400

    try:
        reply = orchestrator.handle_admin_query(user_query, current_user)
        return jsonify({
            'success': True,
            'data': reply
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/alert/<int:alert_id>/action', methods=['POST'])
@login_required
@admin_required
def alert_action(alert_id):
    """Human-in-the-loop review of AI alerts (Resolve or Dismiss)."""
    data = request.get_json() or {}
    action = data.get('action', '').lower()

    alert = AIAlert.query.get_or_404(alert_id)

    if action == 'resolve':
        alert.status = 'RESOLVED'
        alert.resolved_at = datetime.utcnow()
    elif action == 'dismiss':
        alert.status = 'DISMISSED'
        alert.resolved_at = datetime.utcnow()
    else:
        return jsonify({'success': False, 'error': 'Invalid action. Choose resolve or dismiss.'}), 400

    # Audit record
    audit = AuditLog(
        user_id=current_user.id,
        action=f'AI_ALERT_{action.upper()}',
        entity_type='AIAlert',
        entity_id=alert.id,
        details=f"Admin {current_user.email} marked alert '{alert.title}' as {alert.status}",
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f"Alert '{alert.title}' marked as {alert.status}."
    })

@bp.route('/report/<int:election_id>', methods=['GET'])
@login_required
@admin_required
def get_report(election_id):
    """Retrieve an autonomous executive election report."""
    try:
        report = orchestrator.generate_election_report(election_id)
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
