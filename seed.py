"""
Seed script - Creates admin user and strategic objectives.
Run with: python seed.py
"""

import os
import sys

# Set a default secret key for seeding
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'seed-temp-key'

from app import app
from models import db, User, StrategicObjective

OBJECTIVES = [
    (1, 'Latex ATS', 'Latex adhesive technology and system improvements'),
    (2, 'FPM ATS', 'FPM adhesive technology and system improvements'),
    (3, 'Reduce MSM', 'Reduce MSM-related issues and waste'),
    (4, 'Reduce Stops', 'Reduce unplanned stops and improve uptime'),
    (5, 'Loose Edges', 'Eliminate loose edge defects'),
    (6, 'Off-Quality Reduction', 'Reduce off-quality production'),
    (7, 'Waste / Industrial', 'Reduce waste and improve industrial metrics'),
    (8, 'Ignition Dashboards', 'Other - Ignition dashboard development'),
    (9, 'Other Tier / Other', 'Other tier objectives and miscellaneous'),
    (99, 'Stretch', 'Stretch goals and aspirational targets'),
]


def seed():
    with app.app_context():
        db.create_all()

        # Create admin user
        admin_password = os.environ.get('ADMIN_PASSWORD', 'changeme123')
        admin = User.query.filter_by(username='jordan').first()
        if not admin:
            admin = User(username='jordan')
            admin.set_password(admin_password)
            db.session.add(admin)
            print(f'Created admin user: jordan (password: {admin_password})')
        else:
            admin.set_password(admin_password)
            print('Updated admin user password')

        # Create strategic objectives
        for number, name, description in OBJECTIVES:
            existing = StrategicObjective.query.filter_by(number=number).first()
            if not existing:
                obj = StrategicObjective(number=number, name=name, description=description)
                db.session.add(obj)
                print(f'Created objective: {number}. {name}')
            else:
                print(f'Objective already exists: {number}. {name}')

        db.session.commit()
        print('\nSeed complete!')


if __name__ == '__main__':
    seed()
