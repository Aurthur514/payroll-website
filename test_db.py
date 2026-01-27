from app import app, db
print('Imports successful')
with app.app_context():
    db.create_all()
    print('Database created')