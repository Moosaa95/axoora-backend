"""
Axoora Team Email & Credential Dispatch Service.
Dispatches invitations, auto-generated credentials, and password reset notifications.
"""

from __future__ import annotations

import string
import secrets
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_secure_password(length: int = 12) -> str:
    """
    Generates a cryptographically strong, human-readable temporary password.
    Guarantees at least 1 uppercase, 1 lowercase, 1 digit, and 1 special symbol.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in "!@#$%^&*" for c in pwd)
        ):
            return pwd


def get_login_url(request=None) -> str:
    """Resolve the canonical frontend admin login URL."""
    base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    if request:
        origin = request.headers.get('origin') or request.headers.get('referer')
        if origin and ('localhost' in origin or 'vercel.app' in origin or 'axoora.ai' in origin):
            base_url = origin.split('/admin')[0].rstrip('/')
    return f"{base_url}/admin/login"


def send_team_invite_email(member, temporary_password: str, request=None) -> bool:
    """
    Sends an invitation email with auto-generated credentials to a new or invited team member.
    """
    login_url = get_login_url(request)
    recipient_email = member.user.email
    full_name = member.full_name
    username = member.user.username
    role_name = member.role.name if member.role else 'Staff Member'
    department = member.get_department_display() if hasattr(member, 'get_department_display') else member.department

    subject = f"Welcome to Axoora Admin Portal — Your Access Credentials"
    
    plain_message = f"""Hello {full_name},

You have been invited to join the Axoora Platform Team as {role_name} ({department}).

Your administrative account has been provisioned with the following initial credentials:

  • Portal Login URL: {login_url}
  • Username: {username}
  • Email: {recipient_email}
  • Temporary Password: {temporary_password}

For security compliance under Central Bank of Nigeria (CBN) and NDIC operating guidelines, please sign in and update your password immediately upon your first login.

If you have any questions or did not expect this invitation, please contact the Security Desk at security@axoora.ai.

Warm regards,
Axoora Security & Platform Operations
Suite 08 Block C, Cappador Mall, 85 Aguiyi Ironsi Street Maitama, Abuja
"""

    html_message = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #020B1D; color: #F2F5F9; margin: 0; padding: 24px; }}
    .container {{ max-width: 560px; margin: 0 auto; background-color: #08152F; border: 1px solid #14294F; border-radius: 16px; overflow: hidden; }}
    .header {{ background: linear-gradient(135deg, #0D95FE 0%, #00DF8F 100%); padding: 28px 24px; text-align: center; color: #ffffff; }}
    .content {{ padding: 28px 24px; }}
    .badge {{ display: inline-block; background-color: rgba(13, 149, 254, 0.15); border: 1px solid rgba(13, 149, 254, 0.4); color: #0D95FE; font-size: 11px; font-weight: bold; padding: 4px 10px; border-radius: 999px; text-transform: uppercase; margin-bottom: 12px; }}
    .cred-box {{ background-color: #030E26; border: 1px solid #14294F; border-radius: 12px; padding: 16px; margin: 20px 0; }}
    .cred-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #0F2244; font-size: 13px; }}
    .cred-row:last-child {{ border-bottom: none; }}
    .cred-label {{ color: #7B9CD2; font-weight: 600; }}
    .cred-value {{ color: #00DF8F; font-family: monospace; font-weight: bold; }}
    .btn {{ display: block; width: fit-content; margin: 24px auto 8px auto; background-color: #00DF8F; color: #003825; font-weight: 800; font-size: 14px; padding: 12px 28px; border-radius: 10px; text-decoration: none; text-align: center; }}
    .footer {{ font-size: 11px; color: #53719C; text-align: center; padding: 16px 24px; border-top: 1px solid #14294F; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 style="margin: 0; font-size: 24px; font-weight: 900; letter-spacing: -0.5px;">Axoora</h1>
      <p style="margin: 6px 0 0 0; font-size: 13px; opacity: 0.9;">Platform Administration & Operations Portal</p>
    </div>
    <div class="content">
      <div class="badge">Official Invitation</div>
      <h2 style="margin: 0 0 12px 0; font-size: 18px; color: #FFFFFF;">Hello {full_name},</h2>
      <p style="font-size: 13px; line-height: 1.6; color: #A8BBD6; margin: 0 0 16px 0;">
        You have been provisioned with staff access to the Axoora Admin Portal as <strong>{role_name}</strong> within the <strong>{department}</strong> team.
      </p>

      <div class="cred-box">
        <div class="cred-row"><span class="cred-label">Portal URL:</span><span class="cred-value">{login_url}</span></div>
        <div class="cred-row"><span class="cred-label">Username:</span><span class="cred-value">{username}</span></div>
        <div class="cred-row"><span class="cred-label">Email:</span><span class="cred-value">{recipient_email}</span></div>
        <div class="cred-row"><span class="cred-label">Temporary Password:</span><span class="cred-value">{temporary_password}</span></div>
      </div>

      <a href="{login_url}" class="btn">Log In to Axoora Portal &rarr;</a>

      <p style="font-size: 11px; color: #7B9CD2; text-align: center; margin-top: 16px;">
        🔒 Security Policy: Please update your password immediately upon your first sign in.
      </p>
    </div>
    <div class="footer">
      Central Bank of Nigeria (CBN) Supervised · NDIC Insured<br>
      Axoora Financial Technologies Limited · Suite 08 Block C, Cappador Mall, 85 Aguiyi Ironsi Street Maitama, Abuja
    </div>
  </div>
</body>
</html>
"""

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'Axoora Platform <no-reply@axoora.ai>'),
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Invitation email successfully sent to {recipient_email}")
        return True
    except Exception as e:
        logger.warning(f"Failed to send invitation email to {recipient_email}: {e}")
        return False


def send_password_reset_email(member, new_password: str, request=None) -> bool:
    """
    Sends an administrative password reset notification email with newly generated credentials.
    """
    login_url = get_login_url(request)
    recipient_email = member.user.email
    full_name = member.full_name
    username = member.user.username

    subject = f"Your Axoora Admin Password Has Been Reset"
    
    plain_message = f"""Hello {full_name},

An administrator has reset your password for the Axoora Admin Portal.

Your updated login credentials are:

  • Portal Login URL: {login_url}
  • Username: {username}
  • New Temporary Password: {new_password}

Please sign in and change your password to a private phrase of your choice.

If you did not request or expect this reset, contact the Security Desk at security@axoora.ai immediately.

Warm regards,
Axoora Security & Platform Operations
"""

    html_message = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #020B1D; color: #F2F5F9; margin: 0; padding: 24px; }}
    .container {{ max-width: 560px; margin: 0 auto; background-color: #08152F; border: 1px solid #14294F; border-radius: 16px; overflow: hidden; }}
    .header {{ background: #0D95FE; padding: 24px; text-align: center; color: #ffffff; }}
    .content {{ padding: 28px 24px; }}
    .cred-box {{ background-color: #030E26; border: 1px solid #14294F; border-radius: 12px; padding: 16px; margin: 20px 0; }}
    .cred-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #0F2244; font-size: 13px; }}
    .cred-row:last-child {{ border-bottom: none; }}
    .cred-label {{ color: #7B9CD2; font-weight: 600; }}
    .cred-value {{ color: #00DF8F; font-family: monospace; font-weight: bold; }}
    .btn {{ display: block; width: fit-content; margin: 24px auto 8px auto; background-color: #00DF8F; color: #003825; font-weight: 800; font-size: 14px; padding: 12px 28px; border-radius: 10px; text-decoration: none; text-align: center; }}
    .footer {{ font-size: 11px; color: #53719C; text-align: center; padding: 16px 24px; border-top: 1px solid #14294F; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 style="margin: 0; font-size: 22px; font-weight: 900;">Axoora Security Notice</h1>
    </div>
    <div class="content">
      <h2 style="margin: 0 0 12px 0; font-size: 18px; color: #FFFFFF;">Password Reset Notification</h2>
      <p style="font-size: 13px; line-height: 1.6; color: #A8BBD6; margin: 0 0 16px 0;">
        Hello <strong>{full_name}</strong>, an administrator has reset your password for the Axoora Admin Portal.
      </p>

      <div class="cred-box">
        <div class="cred-row"><span class="cred-label">Portal URL:</span><span class="cred-value">{login_url}</span></div>
        <div class="cred-row"><span class="cred-label">Username:</span><span class="cred-value">{username}</span></div>
        <div class="cred-row"><span class="cred-label">New Password:</span><span class="cred-value">{new_password}</span></div>
      </div>

      <a href="{login_url}" class="btn">Log In to Axoora Portal &rarr;</a>

      <p style="font-size: 11px; color: #7B9CD2; text-align: center; margin-top: 16px;">
        🔒 Security Policy: Please update your password immediately after logging in.
      </p>
    </div>
    <div class="footer">
      Axoora Financial Technologies Limited · Suite 08 Block C, Cappador Mall, Maitama, Abuja
    </div>
  </div>
</body>
</html>
"""

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'Axoora Platform <no-reply@axoora.ai>'),
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email successfully sent to {recipient_email}")
        return True
    except Exception as e:
        logger.warning(f"Failed to send password reset email to {recipient_email}: {e}")
        return False
