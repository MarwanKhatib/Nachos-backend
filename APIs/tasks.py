import yagmail
from decouple import config
import logging

logger = logging.getLogger(__name__)

def send_verification_email(email, auth_key):
    """Send verification email asynchronously"""
    try:
        logger.info(f"Starting verification email process for {email}")
        
        # Get email configuration
        email_user = config("EMAIL_HOST_USER", default=None)
        email_password = config("EMAIL_HOST_PASSWORD", default=None)
        
        if not email_user or not email_password:
            logger.error("Email configuration is missing")
            logger.error(f"EMAIL_HOST_USER: {'Set' if email_user else 'Not set'}")
            logger.error(f"EMAIL_HOST_PASSWORD: {'Set' if email_password else 'Not set'}")
            return False
        
        logger.info(f"Using email host user: {email_user}")
        
        try:
            # Configure yagmail with explicit settings
            yag = yagmail.SMTP(
                user=email_user,
                password=email_password,
                host='smtp.gmail.com',
                port=465,
                smtp_ssl=True,
                smtp_starttls=False,
                smtp_skip_login=False,
                timeout=30
            )
            
            logger.info("SMTP connection established")
            
            # Define contents here as HTML
            contents = f"<p>Welcome to Nachos!</p><p>Your verification code is: <strong>{auth_key}</strong></p><p>Please use this code to verify your email address.</p><p>If you didn't request this, please ignore this email.</p>"

            # Log the contents being sent
            logger.info(f"Email contents being sent: {contents}")
            
            # Send email with more detailed content
            yag.send(
                to=email,
                subject="Verify Your Email - Nachos",
                contents=contents,
                # Specify that the content is HTML
                prettify_html=True
            )
            
            logger.info(f"Email sent successfully to {email}")
            return True
            
        except Exception as smtp_error:
            logger.error(f"SMTP Error: {str(smtp_error)}")
            logger.error(f"SMTP Error type: {type(smtp_error)}")
            logger.error(f"SMTP Error details: {smtp_error.__dict__ if hasattr(smtp_error, '__dict__') else 'No details available'}")
            
            # Try alternative SMTP configuration
            try:
                logger.info("Attempting alternative SMTP configuration...")
                yag = yagmail.SMTP(
                    user=email_user,
                    password=email_password,
                    host='smtp.gmail.com',
                    port=587,
                    smtp_ssl=False,
                    smtp_starttls=True,
                    smtp_skip_login=False,
                    timeout=30
                )
                
                logger.info("Alternative SMTP connection established")
                
                # Define contents for alternative here as HTML
                contents_alt = f"<p>Welcome to Nachos!</p><p>Your verification code is: <strong>{auth_key}</strong></p><p>Please use this code to verify your email address.</p><p>If you didn't request this, please ignore this email.</p>"
                
                # Log the contents being sent in alternative
                logger.info(f"Email contents being sent (alternative): {contents_alt}")

                yag.send(
                    to=email,
                    subject="Verify Your Email - Nachos",
                    contents=contents_alt,
                    # Specify that the content is HTML
                    prettify_html=True
                )
                
                logger.info(f"Email sent successfully using alternative configuration to {email}")
                return True
                
            except Exception as alt_smtp_error:
                logger.error(f"Alternative SMTP Error: {str(alt_smtp_error)}")
                logger.error(f"Alternative SMTP Error type: {type(alt_smtp_error)}")
                raise alt_smtp_error
                
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
        return False

def create_user_suggestions(user_id):
    """Create initial movie suggestions asynchronously"""
    try:
        # Import here to avoid circular imports
        from APIs.models.user_model import User
        from APIs.utils.suggestion_helpers import create_initial_movie_suggestions
        
        user = User.objects.get(id=user_id)
        create_initial_movie_suggestions(user)
        return True
    except Exception as e:
        print(f"Error creating movie suggestions: {str(e)}")
        return False


def send_password_reset_code_email(email, code):
    """Send password reset code email asynchronously"""
    try:
        logger.info(f"Starting password reset code email process for {email}")
        
        email_user = config("EMAIL_HOST_USER", default=None)
        email_password = config("EMAIL_HOST_PASSWORD", default=None)
        
        if not email_user or not email_password:
            logger.error("Email configuration is missing for password reset")
            return False
        
        yag = yagmail.SMTP(
            user=email_user,
            password=email_password,
            host='smtp.gmail.com',
            port=465,
            smtp_ssl=True,
            smtp_starttls=False,
            smtp_skip_login=False,
            timeout=30
        )
        
        contents = f"""
        <p>Hello,</p>
        <p>You are receiving this email because you requested a password reset for your account.</p>
        <p>Your password reset code is: <strong>{code}</strong></p>
        <p>Please use this code to reset your password.</p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>Thank you,</p>
        <p>The Nachos Team</p>
        """

        yag.send(
            to=email,
            subject="Password Reset Request for Nachos",
            contents=contents,
            prettify_html=True
        )
        
        logger.info(f"Password reset code email sent successfully to {email}")
        return True
            
    except Exception as e:
        logger.error(f"Error sending password reset code email to {email}: {str(e)}", exc_info=True)
        return False
