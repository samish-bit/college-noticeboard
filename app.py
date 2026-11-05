from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Post, Upvote

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-change-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///noticeboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------- Auth ----------

@app.route('/')
def index():
    return redirect(url_for('board'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))
        user = User(
            name=request.form['name'],
            email=email,
            password=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('board'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if not user or not check_password_hash(user.password, request.form['password']):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('board'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ---------- Main page ----------

@app.route('/board')
@login_required
def board():
    return render_template('board.html')


# ---------- REST API routes ----------

@app.route('/api/posts')
@login_required
def get_posts():
    category = request.args.get('category', 'all')
    query = Post.query
    if category != 'all':
        query = query.filter_by(category=category)
    posts = query.order_by(Post.created_at.desc()).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'body': p.body,
        'category': p.category,
        'author': p.author.name,
        'created_at': p.created_at.strftime('%b %d, %Y'),
        'upvotes': len(p.upvotes),
        'upvoted_by_me': any(u.user_id == current_user.id for u in p.upvotes),'is_mine': p.user_id == current_user.id
    } for p in posts])

@app.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('body'):
        return jsonify({'error': 'Title and body required'}), 400
    post = Post(
        title=data['title'],
        body=data['body'],
        category=data.get('category', 'General'),
        user_id=current_user.id
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created', 'id': post.id}), 201

@app.route('/api/posts/<int:id>', methods=['DELETE'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

@app.route('/api/posts/<int:id>/upvote', methods=['POST'])
@login_required
def upvote_post(id):
    post = Post.query.get_or_404(id)
    existing = Upvote.query.filter_by(user_id=current_user.id, post_id=id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'message': 'upvote removed', 'upvotes': len(post.upvotes)})
    upvote = Upvote(user_id=current_user.id, post_id=id)
    db.session.add(upvote)
    db.session.commit()
    return jsonify({'message': 'upvoted', 'upvotes': len(post.upvotes)})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)