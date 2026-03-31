from models import db, User

def seed_admin():
    """Create default admin if not exists."""
    admin = User.query.filter_by(email='admin@dept.edu').first()
    if not admin:
        admin = User(
            name='Department Admin',
            email='admin@dept.edu',
            role='admin',
            department='Computer Science'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Default coordinator
        coord = User.query.filter_by(email='coordinator@dept.edu').first()
        if not coord:
            coord = User(
                name='Department Coordinator',
                email='coordinator@dept.edu',
                role='coordinator',
                department='Computer Science',
                phone='9000000002'
            )
            coord.set_password('coord123')
            db.session.add(coord)

        db.session.commit()
        print("✅ Default admin and coordinator seeded.")
