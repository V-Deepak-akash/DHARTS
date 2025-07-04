from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import base64
import os
from werkzeug.utils import secure_filename
import jwt
import datetime
from functools import wraps
from flask import send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
CORS(app)  # enable CORS for all domains - adjust for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///arts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # CHANGE THIS TO SOMETHING SECURE

db = SQLAlchemy(app)

# --- Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    security_question = db.Column(db.String(255), nullable=False)
    security_answer_hash = db.Column(db.String(128), nullable=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    image_data = db.Column(db.Text, nullable=False)  # base64 string
    likes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', cascade="all, delete-orphan")

# Modify Comment model (already has id)
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)


# --- Utility Functions ---

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(username=data['username']).first()
            if not current_user:
                raise Exception('User not found')
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# --- Routes ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    
    token = jwt.encode({
        'username': user.username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({'token': token})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if not check_password_hash(user.security_answer_hash, data.get('answer', '')):
        return jsonify({'message': 'Security answer incorrect'}), 403

    new_password = generate_password_hash(data.get('new_password'))
    user.password_hash = new_password
    db.session.commit()

    return jsonify({'message': 'Password reset successful'})

@app.route('/api/security-question')
def get_security_question():
    username = request.args.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'question': user.security_question})

@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    result = []
    for p in posts:
        result.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'category': p.category,
            'image_url': f"data:image/*;base64,{p.image_data}",
            'likes': p.likes,
            'comments': [{'id': c.id, 'text': c.text} for c in p.comments]
        })
    return jsonify({'posts': result})

@app.route('/api/posts/<int:post_id>/comment/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, post_id, comment_id):
    comment = Comment.query.filter_by(id=comment_id, post_id=post_id).first()
    if not comment:
        return jsonify({'message': 'Comment not found'}), 404
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Comment deleted'})


@app.route('/api/posts', methods=['POST'])
@token_required
def create_post(current_user):
    if 'imageFile' not in request.files:
        return jsonify({'message': 'Image file required'}), 400
    image = request.files['imageFile']
    if image.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')

    if not title or not description or not category:
        return jsonify({'message': 'Title, description, and category are required'}), 400

    # Convert image to base64 string
    image_data = base64.b64encode(image.read()).decode('utf-8')

    new_post = Post(
        title=title,
        description=description,
        category=category.lower(),
        image_data=image_data,
        likes=0
    )
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'message': 'Post created', 'id': new_post.id})

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    return jsonify({'message': 'Liked', 'likes': post.likes})

@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    comment_text = data.get('comment')
    if not comment_text:
        return jsonify({'message': 'Comment text required'}), 400
    comment = Comment(post_id=post.id, text=comment_text)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Comment added'})

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted'})

# --- Initialize ---

def init_db():
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                security_question="What is your favorite color?",
                security_answer_hash=generate_password_hash("purple")
            )
            db.session.add(admin_user)
            db.session.commit()

@app.route('/')
def serve_login():
    return send_from_directory('../frontend', 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route('/home')
def serve_home():
    return send_from_directory('../frontend', 'index.html')

if __name__ == '__main__':
    if not os.path.exists('arts.db'):
        init_db()
    app.run(debug=True)
