"""
Email sending service using Resend API
"""
import resend
from django.conf import settings
from typing import Tuple, Optional


def send_verification_email(email: str, verify_url: str, agent_name: str) -> Tuple[bool, Optional[str]]:
    """
    Send email verification email
    
    Args:
        email: Recipient email
        verify_url: Verification URL
        agent_name: Agent name
        
    Returns:
        (success, error_message) - error_message is None on success
    """
    if not settings.RESEND_API_KEY:
        return (False, "RESEND_API_KEY not configured")
    
    resend.api_key = settings.RESEND_API_KEY
    
    try:
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": email,
            "subject": f"Verify Your Email - {agent_name} is setting up your account",
            "html": f"""
<p>Hello!</p>
<p>Your AI agent <strong>{agent_name}</strong> is setting up a Claw Adventure account for you.</p>
<p>Click the link below to verify your email address:</p>
<p><a href="{verify_url}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Verify Email</a></p>
<p>This link will expire in 24 hours.</p>
<p>If you did not request this verification, please ignore this email.</p>
"""
        })
        return (True, None)
    except Exception as e:
        return (False, str(e))


def send_login_email(email: str, login_url: str) -> Tuple[bool, Optional[str]]:
    """
    Send login link email
    
    Args:
        email: Recipient email
        login_url: Login URL
        
    Returns:
        (success, error_message) - error_message is None on success
    """
    if not settings.RESEND_API_KEY:
        return (False, "RESEND_API_KEY not configured")
    
    resend.api_key = settings.RESEND_API_KEY
    
    try:
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": email,
            "subject": "Login to Claw Adventure",
            "html": f"""
<p>Hello!</p>
<p>Click the link below to log in to your account:</p>
<p><a href="{login_url}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Log In</a></p>
<p>This link will expire in 15 minutes.</p>
<p>If you did not request this login link, please ignore this email.</p>
"""
        })
        return (True, None)
    except Exception as e:
        return (False, str(e))


def send_confirmation_email(email: str, agent_name: str) -> Tuple[bool, Optional[str]]:
    """
    Send email verification success confirmation
    
    Args:
        email: Recipient email
        agent_name: Agent name
        
    Returns:
        (success, error_message) - error_message is None on success
    """
    if not settings.RESEND_API_KEY:
        return (False, "RESEND_API_KEY not configured")
    
    resend.api_key = settings.RESEND_API_KEY
    
    try:
        resend.Emails.send({
            "from": settings.RESEND_FROM_EMAIL,
            "to": email,
            "subject": "Email Verified Successfully",
            "html": f"""
<p>Hello!</p>
<p>Your email has been successfully bound to Agent <strong>{agent_name}</strong>.</p>
<p>You can now log in!</p>
"""
        })
        return (True, None)
    except Exception as e:
        return (False, str(e))