from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import url_for, current_app

# Generate a token for email confirmation
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="email-confirm-salt")

# Confirm token (returns email if valid, False if invalid/expired)
def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=expiration)
    except:
        return False
    return email

# Send confirmation email
def send_confirmation_email(user_email):
    # Compose confirmation link that points to the routes.confirm_email handler
    token = generate_confirmation_token(user_email)
    confirm_url = url_for("routes.confirm_email", token=token, _external=True)
    html = f"""
        <p>Welcome to MealMind! Thanks for signing up.</p>
        <p>To complete registration, please confirm your email by clicking the link below:</p>
        <p><a href="{confirm_url}">Confirm Email</a></p>
        <p>This link expires in 1 hour.</p>
        <p> Best regards,<br/>The MealMind Team</p>
    """
    msg = Message("Confirm Your Email", recipients=[user_email], html=html)

    try:
        from app import mail
        mail.send(msg)
    except Exception as e:
        # Mail not configured or send failed — fallback to logging the URL
        try:
            current_app.logger.warning(f"Could not send confirmation email: {e}")
            current_app.logger.warning(f"Confirmation URL: {confirm_url}")
        except Exception:
            # Last resort: print to stdout
            print("Could not send confirmation email:", e)
            print("Confirmation URL:", confirm_url)


# --- Password reset helpers 
def generate_password_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="password-reset-salt")


def confirm_password_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=expiration)
    except Exception:
        return False
    return email


def send_password_reset_email(user_email):
    token = generate_password_reset_token(user_email)
    reset_url = url_for('routes.reset_with_token', token=token, _external=True)
    html = f"""
        <p>We received a request to reset your MealMind password.</p>
        <p>Click the link below to choose a new password (this link expires in 1 hour):</p>
        <p><a href="{reset_url}">Reset your password</a></p>
        <p>If you did not request a password reset, you can safely ignore this email.</p>
        <p>Best regards,<br/>The MealMind Team</p>
    """
    msg = Message("MealMind Password Reset", recipients=[user_email], html=html)
    try:
        from app import mail
        mail.send(msg)
    except Exception as e:
        try:
            current_app.logger.warning(f"Could not send password reset email: {e}")
            current_app.logger.warning(f"Password reset URL: {reset_url}")
        except Exception:
            print("Could not send password reset email:", e)
            print("Password reset URL:", reset_url)
