import os
import re
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Part
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --------- Logging ڕێکخستنی ---------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gellek-qursi-key-default')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///marketplace.db')
app.config['WTF_CSRF_ENABLED'] = True
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# FIX #5: پشکنینی image_url بە Regex
ALLOWED_URL_PATTERN = re.compile(
    r'^https?://'                      # http یان https
    r'[\w\-]+(\.[\w\-]+)+'             # domain
    r'(/[\w\-._~:/?#\[\]@!$&\'()*+,;=%]*)?$',  # path
    re.IGNORECASE
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_image_url(url):
    """پشکنینی ئەوەی image_url ئادرەسێکی درووستی http/https ە"""
    return bool(ALLOWED_URL_PATTERN.match(url))


def save_uploaded_image(file, user_id):
    """وێنەی بارکراو پاشەکەوت بکە و ئادرەسەکەی برگەردێنەوە"""
    filename = secure_filename(f"{user_id}_{int(datetime.utcnow().timestamp())}_{file.filename}")
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return url_for('static', filename=f'uploads/{filename}')


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# FIX #2 (گەورە): create_tables بە شێوەی درووست — کار دەکات هەم بە gunicorn هەم ڕاستەوخۆ
def create_tables():
    with app.app_context():
        db.create_all()
        logger.info("جەدوەلەکان دروست کران / پشکنران.")


# --------- ڕێڕەوەکان ---------

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    per_page = 9

    if search_query:
        parts_query = Part.query.filter(
            (Part.name.ilike(f'%{search_query}%')) |
            (Part.description.ilike(f'%{search_query}%')) |
            (Part.car_model.ilike(f'%{search_query}%'))
        ).order_by(Part.created_at.desc())
    else:
        parts_query = Part.query.order_by(Part.created_at.desc())

    parts_paginated = parts_query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('index.html', parts=parts_paginated.items,
                           pagination=parts_paginated, search_query=search_query)


@app.route('/part/<int:part_id>')
def part_detail(part_id):
    part = db.session.get(Part, part_id)
    if part is None:
        return render_template('404.html'), 404
    return render_template('part_detail.html', part=part)


@app.route('/seller/<int:user_id>')
def seller_profile(user_id):
    seller = db.session.get(User, user_id)
    if seller is None:
        return render_template('404.html'), 404
    if seller.user_type != 'seller':
        flash('ئەم بەکارهێنەرە فرۆشیار نییە.', 'info')
        return redirect(url_for('index'))
    parts = Part.query.filter_by(seller_id=seller.id).order_by(Part.created_at.desc()).all()
    return render_template('seller_profile.html', seller=seller, parts=parts)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']
        phone = request.form.get('phone', '')

        if User.query.filter_by(username=username).first():
            flash('ئەم ناوە پێشتر تۆمار کراوە!', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, password=password, user_type=user_type, phone=phone)
        db.session.add(user)
        db.session.commit()
        flash('بە سەرکەوتوویی تۆمار بوویت! ئێستا بچۆ ژوورەوە.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash(f'بەخێربێیتەوە {user.username}!', 'success')
            return redirect(url_for('dashboard' if user.user_type == 'seller' else 'index'))
        flash('ناوی بەکارهێنەر یان وشەی نهێنی هەڵەیە!', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != 'seller':
        flash('تەنها فرۆشیار دەتوانێت بچێتە داشبۆرد!', 'warning')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    per_page = 6
    parts_paginated = Part.query.filter_by(seller_id=current_user.id) \
        .order_by(Part.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('dashboard.html', parts=parts_paginated.items, pagination=parts_paginated)


@app.route('/add_part', methods=['GET', 'POST'])
@login_required
def add_part():
    if current_user.user_type != 'seller':
        flash('تەنها فرۆشیار دەتوانێت پارچە زیاد بکات!', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        car_model = request.form['car_model']
        description = request.form['description']

        try:
            price = float(request.form['price'])
            if price < 0:
                raise ValueError("نرخ نابێت نەرێنی بێت")
        except ValueError:
            flash('تکایە نرخێکی درووست و ئەرێنی بنووسە!', 'danger')
            return redirect(request.url)

        image_url = None
        if 'image_file' in request.files and request.files['image_file'].filename != '':
            file = request.files['image_file']
            if allowed_file(file.filename):
                image_url = save_uploaded_image(file, current_user.id)
            else:
                flash('جۆری فایلی وێنە ڕێگەپێدراو نییە. تکایە PNG, JPG, JPEG, GIF بەکاربهێنە.', 'danger')
                return redirect(request.url)
        elif request.form.get('image_url'):
            # FIX #5: پشکنینی image_url پێش پاشەکەوتکردن
            raw_url = request.form['image_url']
            if not allowed_image_url(raw_url):
                flash('ئادرەسی وێنەکە درووست نییە. تکایە ئادرەسێکی http/https بنووسە.', 'danger')
                return redirect(request.url)
            image_url = raw_url

        part = Part(
            name=name,
            car_model=car_model,
            description=description,
            price=price,
            image_url=image_url,
            seller_id=current_user.id
        )
        db.session.add(part)
        db.session.commit()
        flash('پارچەکەت بە سەرکەوتوویی زیاد کرا!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_part.html')
@app.route('/edit_part/<int:part_id>', methods=['GET', 'POST'])
@login_required
def edit_part(part_id):
    part = db.session.get(Part, part_id)
    if part is None:
        return render_template('404.html'), 404
    if part.seller_id != current_user.id:
        flash('تۆ ناتوانیت ئەم پارچەیە دەستکاری بکەیت!', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        part.name = request.form['name']
        part.car_model = request.form['car_model']
        part.description = request.form['description']

        try:
            part.price = float(request.form['price'])
            if part.price < 0:
                raise ValueError("نرخ نابێت نەرێنی بێت")
        except ValueError:
            flash('تکایە نرخێکی درووست و ئەرێنی بنووسە!', 'danger')
            return redirect(request.url)

        if 'image_file' in request.files and request.files['image_file'].filename != '':
            file = request.files['image_file']
            if allowed_file(file.filename):
                part.image_url = save_uploaded_image(file, current_user.id)
            else:
                flash('جۆری فایلی وێنە ڕێگەپێدراو نییە.', 'danger')
                return redirect(request.url)
        elif request.form.get('image_url'):
            # FIX #5: پشکنینی image_url پێش پاشەکەوتکردن
            raw_url = request.form['image_url']
            if not allowed_image_url(raw_url):
                flash('ئادرەسی وێنەکە درووست نییە. تکایە ئادرەسێکی http/https بنووسە.', 'danger')
                return redirect(request.url)
            part.image_url = raw_url

        db.session.commit()
        flash('پارچەکەت بە سەرکەوتوویی نوێ کرایەوە!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_part.html', part=part)


@app.route('/delete_part/<int:part_id>', methods=['POST'])
@login_required
def delete_part(part_id):
    part = db.session.get(Part, part_id)
    if part is None:
        return render_template('404.html'), 404
    if part.seller_id != current_user.id:
        flash('تۆ ناتوانیت ئەم پارچەیە بسڕیتەوە!', 'danger')
        return redirect(url_for('dashboard'))
    db.session.delete(part)
    db.session.commit()
    flash('پارچەکەت سڕایەوە.', 'info')
    return redirect(url_for('dashboard'))


# FIX #4: API بە login_required ساخکراوە
@app.route('/api/parts')
@login_required
def api_parts():
    parts = Part.query.all()
    return {'parts': [{'id': p.id, 'name': p.name, 'price': p.price} for p in parts]}


# --------- هەڵەکان ---------

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# FIX #6: هەڵەی 500 — Logging زیادکرا
@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    logger.error(f"هەڵەی سێرڤەر: {e}", exc_info=True)
    return render_template('500.html'), 500


if __name__ == '__main__':
    create_tables()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


# --------- بۆ Gunicorn: create_tables() لێرەوە کرێتەوە ---------
# ئەگەر gunicorn بەکاردەهێنیت، ئەم هێڵانە لە wsgi.py یان فایلی دیکەدا زیاد بکە:
#
#   from app import app, create_tables
#   create_tables()
#
