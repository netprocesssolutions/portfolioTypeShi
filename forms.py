"""
Flask-WTF forms for the Action Item Tracker.
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, TextAreaField, SelectField,
                     DateField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class ActionItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=300)])
    description = TextAreaField('Description', validators=[Optional()])
    project_id = SelectField('Project', coerce=int, validators=[DataRequired()])
    source = StringField('Source', validators=[Optional(), Length(max=200)])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium')
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked')
    ], default='open')
    due_date = DateField('Due Date', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save')


class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    objective_id = SelectField('Strategic Objective', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')


class CommentForm(FlaskForm):
    body = TextAreaField('Comment', validators=[DataRequired(), Length(max=2000)])
    comment_type = SelectField('Type', choices=[
        ('comment', 'Comment'),
        ('suggestion', 'Suggestion'),
        ('question', 'Question')
    ], default='comment')
    submit = SubmitField('Post')


class WikiPageForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=300)])
    body = TextAreaField('Content', validators=[Optional()])
    submit = SubmitField('Save')
