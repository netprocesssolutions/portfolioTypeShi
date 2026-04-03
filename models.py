"""
Database models for the Action Item Tracker.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class StrategicObjective(db.Model):
    __tablename__ = 'strategic_objectives'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    projects = db.relationship('Project', backref='objective', lazy='dynamic',
                               cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='objective', lazy='dynamic',
                               cascade='all, delete-orphan',
                               foreign_keys='Comment.objective_id')

    def action_item_count(self):
        return ActionItem.query.join(Project).filter(
            Project.objective_id == self.id
        ).count()

    def open_count(self):
        return ActionItem.query.join(Project).filter(
            Project.objective_id == self.id,
            ActionItem.status.in_(['open', 'in_progress', 'blocked'])
        ).count()

    def completed_count(self):
        return ActionItem.query.join(Project).filter(
            Project.objective_id == self.id,
            ActionItem.status == 'completed'
        ).count()


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    objective_id = db.Column(db.Integer, db.ForeignKey('strategic_objectives.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    action_items = db.relationship('ActionItem', backref='project', lazy='dynamic',
                                   cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='project', lazy='dynamic',
                               cascade='all, delete-orphan',
                               foreign_keys='Comment.project_id')


class ActionItem(db.Model):
    __tablename__ = 'action_items'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, default='')
    source = db.Column(db.String(200), default='')
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed, blocked
    due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    comments = db.relationship('Comment', backref='action_item', lazy='dynamic',
                               cascade='all, delete-orphan',
                               foreign_keys='Comment.action_item_id')


class Comment(db.Model):
    """Polymorphic comments that can attach to objectives, projects, or action items."""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(20), default='comment')  # comment, suggestion, question
    # Polymorphic parent references (only one should be set)
    objective_id = db.Column(db.Integer, db.ForeignKey('strategic_objectives.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    action_item_id = db.Column(db.Integer, db.ForeignKey('action_items.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='comments')


class WikiPage(db.Model):
    """Wiki pages for definitions, procedures, and reference material."""
    __tablename__ = 'wiki_pages'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    title = db.Column(db.String(300), nullable=False)
    body = db.Column(db.Text, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    created_by = db.relationship('User', backref='wiki_pages')
