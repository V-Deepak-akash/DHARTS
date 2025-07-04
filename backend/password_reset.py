from app import app, db, User  # Make sure app, db, and User are imported from your app.py
from werkzeug.security import generate_password_hash

new_username = 'dharshini'
new_password = 'dharshini'

with app.app_context():
    user = User.query.filter_by(username='admin').first()  # or current username

    if user:
        user.username = new_username
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print(f"✅ Admin credentials updated: {new_username} / {new_password}")
    else:
        print("❌ Admin user not found.")
