import os, random, string, smtplib, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from flask import current_app, url_for
from .extensions import db
from .models import SiteSettings

logger = logging.getLogger(__name__)

def allowed_file_magic(file, allowed_mime_set):
    try:
        import magic
        file.stream.seek(0)
        mime = magic.from_buffer(file.stream.read(2048), mime=True)
        file.stream.seek(0)
        return mime in allowed_mime_set
    except:
        return False

def save_file(file, user_id, prefix=''):
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f"{prefix}{user_id}_{int(datetime.utcnow().timestamp())}.{ext}")
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return url_for('static', filename=f'uploads/{filename}')

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(to_email, otp_code):
    # هەمان کۆدی پێشوو
    pass

def get_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return settings

def is_vip_active(user):
    return user.plan == 'vip' and user.plan_expires and user.plan_expires > datetime.utcnow()

def count_monthly_uploads(user_id, media_type):
    from datetime import datetime
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    from .models import Part
    return Part.query.filter(
        Part.seller_id == user_id,
        Part.media_type == media_type,
        Part.created_at >= start_of_month
    ).count()
