import logging
import threading
from flask import current_app, render_template
from flask_mail import Message
from app import db, mail
from app.models.models import User
from app.models.notification import Notification

logger = logging.getLogger(__name__)

def _send_async_email_thread(app, messages):
    """Worker function executed in background thread to dispatch emails."""
    with app.app_context():
        sent_count = 0
        error_count = 0
        for msg in messages:
            try:
                mail.send(msg)
                sent_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to send email to {msg.recipients}: {str(e)}")
        logger.info(f"Email batch completed: {sent_count} sent successfully, {error_count} failed.")

def notify_new_election(election):
    """
    Broadcasts announcement notifications for newly created elections:
    1. Creates in-app Notification records for all registered & verified voters.
    2. Compiles and dispatches personalized HTML notification emails in the background.
    """
    app = current_app._get_current_object()
    
    sender = (
        app.config.get('MAIL_DEFAULT_SENDER')
        or app.config.get('MAIL_USERNAME')
        or 'noreply@smart-elect.org'
    )
    
    messages = []
    
    try:
        # Retrieve all verified voters
        verified_voters = User.query.filter_by(is_verified=True).all()
        
        # 1. Create in-app notification records in database
        for user in verified_voters:
            in_app_notif = Notification(
                user_id=user.id,
                title=f"New Election: {election.title}",
                message=(
                    f"A new election has been scheduled from "
                    f"{election.start_date.strftime('%b %d, %Y %I:%M %p')} to "
                    f"{election.end_date.strftime('%b %d, %Y %I:%M %p')}. "
                    f"Please log in to review candidates and cast your ballot."
                ),
                type="info"
            )
            db.session.add(in_app_notif)
            
            # 2. Build personalized email message
            try:
                html_body = render_template(
                    'email/new_election.html',
                    user=user,
                    election=election
                )
                msg = Message(
                    subject=f"New Election Announced: {election.title} | Smart-Elect",
                    recipients=[user.email],
                    sender=sender,
                    html=html_body
                )
                messages.append(msg)
            except Exception as render_err:
                logger.error(f"Error rendering email for user {user.email}: {str(render_err)}")

        # Commit all in-app notifications
        db.session.commit()
        logger.info(f"Created in-app notifications for {len(verified_voters)} voters.")

        # 3. Add admin announcement confirmation email
        admin_email = app.config.get('MAIL_USERNAME') or sender
        try:
            admin_msg = Message(
                subject=f"[Admin Copy] Election Created: {election.title}",
                recipients=[admin_email],
                sender=sender,
                html=render_template(
                    'email/new_election.html',
                    user=None,
                    election=election,
                    is_admin_copy=True,
                    voter_count=len(verified_voters)
                )
            )
            messages.append(admin_msg)
        except Exception as admin_render_err:
            logger.error(f"Error rendering admin email: {str(admin_render_err)}")

        # 4. Dispatch emails in background thread (asynchronous, non-blocking)
        if messages:
            thread = threading.Thread(
                target=_send_async_email_thread,
                args=(app, messages),
                daemon=True
            )
            thread.start()
            logger.info(f"Dispatched background thread to email {len(messages)} recipients.")

    except Exception as e:
        logger.error(f"Error orchestrating election notification broadcast: {str(e)}")
        db.session.rollback()
