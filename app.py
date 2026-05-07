from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Part
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gellek-qursi-key'  # لە بەرهەمهێناندا بگۆڕە
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# دروستکردنی خشتەکان لە یەکەم جاردا
with app.app_context():
    db.create_all()

# ----------------- ڕووپەڕەکان -----------------
@app.route('/')
def index():
    search_query = request.args.get('q', '')
    if search_query:
        parts = Part.query.filter(
            (Part.name.contains(search_query)) |
            (Part.description.contains(search_query)) |
            (Part.car_model.contains(search_query))
        ).order_by(Part.created_at.desc()).all()
    else:
        parts = Part.query.order_by(Part.created_at.desc()).all()
    return render_template('index.html', parts=parts, search_query=search_query)

@app.route('/part/<int:part_id>')
def part_detail(part_id):
    part = Part.query.get_or_404(part_id)
    return render_template('part_detail.html', part=part)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']   # 'seller' or 'buyer'
        if User.query.filter_by(username=username).first():
            flash('ئەم ناوە پێشتر تۆمار کراوە!', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, password=password, user_type=user_type)
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
            flash('بەخێربێیتەوە!', 'success')
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
    my_parts = Part.query.filter_by(seller_id=current_user.id).order_by(Part.created_at.desc()).all()
    return render_template('dashboard.html', parts=my_parts)

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
        price = float(request.form['price'])
        image_url = request.form['image_url']
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

# ----------------- API بۆ ئەپی داهاتوو -----------------
@app.route('/api/parts')
def api_parts():
    parts = Part.query.all()
    return {'parts': [{'id': p.id, 'name': p.name, 'price': p.price} for p in parts]}

if __name__ == '__main__':
    app.run(debug=True)
