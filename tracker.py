"""
Tracker Blueprint - Action Item Tracker routes.
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import re
from markupsafe import Markup, escape
from models import db, User, StrategicObjective, Project, ActionItem, Comment, WikiPage
from forms import LoginForm, ActionItemForm, ProjectForm, CommentForm, WikiPageForm

tracker_bp = Blueprint('tracker', __name__, template_folder='templates/tracker')


def wiki_link_filter(text):
    """Convert [[Page Name]] syntax to clickable wiki links."""
    if not text:
        return ''
    escaped = str(escape(text))

    def replace_link(match):
        page_name = match.group(1).strip()
        slug = re.sub(r'[^a-z0-9]+', '-', page_name.lower()).strip('-')
        return f'<a href="/tracker/wiki/{slug}" class="wiki-link">{page_name}</a>'

    result = re.sub(r'\[\[(.+?)\]\]', replace_link, escaped)
    return Markup(result)


@tracker_bp.app_template_filter('wikilinks')
def wikilinks_filter(text):
    return wiki_link_filter(text)


# ---- Auth Routes ----

@tracker_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tracker.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('tracker.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html', form=form)


@tracker_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('tracker.login'))


# ---- Dashboard ----

@tracker_bp.route('/')
@login_required
def dashboard():
    objectives = StrategicObjective.query.order_by(StrategicObjective.number).all()
    # Get overall stats
    total_items = ActionItem.query.count()
    open_items = ActionItem.query.filter(ActionItem.status.in_(['open', 'in_progress', 'blocked'])).count()
    completed_items = ActionItem.query.filter_by(status='completed').count()
    critical_items = ActionItem.query.filter(
        ActionItem.priority == 'critical',
        ActionItem.status != 'completed'
    ).count()
    return render_template('dashboard.html',
                         objectives=objectives,
                         total_items=total_items,
                         open_items=open_items,
                         completed_items=completed_items,
                         critical_items=critical_items)


# ---- Objective Detail ----

@tracker_bp.route('/objective/<int:obj_id>')
@login_required
def objective_detail(obj_id):
    objective = StrategicObjective.query.get_or_404(obj_id)
    projects = Project.query.filter_by(objective_id=obj_id).all()
    # Get all action items for this objective
    action_items = ActionItem.query.join(Project).filter(
        Project.objective_id == obj_id
    ).order_by(ActionItem.created_at.desc()).all()
    return render_template('objective_detail.html',
                         objective=objective,
                         projects=projects,
                         action_items=action_items)


# ---- Action Items CRUD ----

@tracker_bp.route('/action-items/new', methods=['GET', 'POST'])
@login_required
def new_action_item():
    form = ActionItemForm()
    # Populate project choices grouped by objective
    projects = Project.query.join(StrategicObjective).order_by(
        StrategicObjective.number, Project.name
    ).all()
    form.project_id.choices = [
        (p.id, f"{p.objective.number}. {p.objective.name} — {p.name}") for p in projects
    ]

    # Pre-select project if passed via query param
    if request.method == 'GET' and request.args.get('project_id'):
        form.project_id.data = int(request.args.get('project_id'))

    if form.validate_on_submit():
        item = ActionItem(
            title=form.title.data,
            description=form.description.data,
            project_id=form.project_id.data,
            source=form.source.data,
            priority=form.priority.data,
            status=form.status.data,
            due_date=form.due_date.data,
            notes=form.notes.data
        )
        db.session.add(item)
        db.session.commit()
        flash('Action item created.', 'success')
        # Redirect to the objective detail page
        project = Project.query.get(form.project_id.data)
        return redirect(url_for('tracker.objective_detail', obj_id=project.objective_id))

    return render_template('action_item_form.html', form=form, editing=False)


@tracker_bp.route('/action-items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_action_item(item_id):
    item = ActionItem.query.get_or_404(item_id)
    form = ActionItemForm(obj=item)

    projects = Project.query.join(StrategicObjective).order_by(
        StrategicObjective.number, Project.name
    ).all()
    form.project_id.choices = [
        (p.id, f"{p.objective.number}. {p.objective.name} — {p.name}") for p in projects
    ]

    if request.method == 'GET':
        form.title.data = item.title
        form.description.data = item.description
        form.project_id.data = item.project_id
        form.source.data = item.source
        form.priority.data = item.priority
        form.status.data = item.status
        form.due_date.data = item.due_date
        form.notes.data = item.notes

    if form.validate_on_submit():
        item.title = form.title.data
        item.description = form.description.data
        item.project_id = form.project_id.data
        item.source = form.source.data
        item.priority = form.priority.data
        item.status = form.status.data
        item.due_date = form.due_date.data
        item.notes = form.notes.data
        if item.status == 'completed' and not item.completed_at:
            item.completed_at = datetime.now(timezone.utc)
        elif item.status != 'completed':
            item.completed_at = None
        db.session.commit()
        flash('Action item updated.', 'success')
        project = Project.query.get(form.project_id.data)
        return redirect(url_for('tracker.objective_detail', obj_id=project.objective_id))

    return render_template('action_item_form.html', form=form, editing=True, item=item)


@tracker_bp.route('/action-items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_action_item(item_id):
    item = ActionItem.query.get_or_404(item_id)
    obj_id = item.project.objective_id
    db.session.delete(item)
    db.session.commit()
    flash('Action item deleted.', 'success')
    return redirect(url_for('tracker.objective_detail', obj_id=obj_id))


@tracker_bp.route('/action-items/<int:item_id>/status', methods=['POST'])
@login_required
def toggle_status(item_id):
    """AJAX status toggle - CSRF token sent via X-CSRFToken header."""
    item = ActionItem.query.get_or_404(item_id)
    data = request.get_json()
    if data and 'status' in data:
        item.status = data['status']
        if item.status == 'completed':
            item.completed_at = datetime.now(timezone.utc)
        else:
            item.completed_at = None
        db.session.commit()
        return jsonify({'status': item.status, 'id': item.id})
    return jsonify({'error': 'Invalid request'}), 400


# ---- Projects CRUD ----

@tracker_bp.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    form = ProjectForm()
    objectives = StrategicObjective.query.order_by(StrategicObjective.number).all()
    form.objective_id.choices = [
        (o.id, f"{o.number}. {o.name}") for o in objectives
    ]

    if request.method == 'GET' and request.args.get('objective_id'):
        form.objective_id.data = int(request.args.get('objective_id'))

    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data,
            objective_id=form.objective_id.data
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created.', 'success')
        return redirect(url_for('tracker.objective_detail', obj_id=form.objective_id.data))

    return render_template('project_form.html', form=form, editing=False)


@tracker_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)

    objectives = StrategicObjective.query.order_by(StrategicObjective.number).all()
    form.objective_id.choices = [
        (o.id, f"{o.number}. {o.name}") for o in objectives
    ]

    if request.method == 'GET':
        form.name.data = project.name
        form.description.data = project.description
        form.objective_id.data = project.objective_id

    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.objective_id = form.objective_id.data
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('tracker.objective_detail', obj_id=form.objective_id.data))

    return render_template('project_form.html', form=form, editing=True, project=project)


@tracker_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    obj_id = project.objective_id
    db.session.delete(project)
    db.session.commit()
    flash('Project and all its action items deleted.', 'success')
    return redirect(url_for('tracker.objective_detail', obj_id=obj_id))


# ---- Comments ----

@tracker_bp.route('/comments/add', methods=['POST'])
@login_required
def add_comment():
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            user_id=current_user.id,
            body=form.body.data,
            comment_type=form.comment_type.data
        )
        # Determine parent from hidden fields
        parent_type = request.form.get('parent_type')
        parent_id = int(request.form.get('parent_id'))
        if parent_type == 'objective':
            comment.objective_id = parent_id
            redirect_url = url_for('tracker.objective_detail', obj_id=parent_id)
        elif parent_type == 'project':
            comment.project_id = parent_id
            project = Project.query.get_or_404(parent_id)
            redirect_url = url_for('tracker.objective_detail', obj_id=project.objective_id)
        elif parent_type == 'action_item':
            comment.action_item_id = parent_id
            item = ActionItem.query.get_or_404(parent_id)
            redirect_url = url_for('tracker.objective_detail', obj_id=item.project.objective_id)
        else:
            flash('Invalid comment target.', 'error')
            return redirect(url_for('tracker.dashboard'))
        db.session.add(comment)
        db.session.commit()
        flash('Comment posted.', 'success')
        return redirect(redirect_url)
    flash('Comment cannot be empty.', 'error')
    return redirect(url_for('tracker.dashboard'))


@tracker_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    # Determine redirect before deleting
    if comment.objective_id:
        redirect_url = url_for('tracker.objective_detail', obj_id=comment.objective_id)
    elif comment.project_id:
        redirect_url = url_for('tracker.objective_detail', obj_id=comment.project.objective_id)
    elif comment.action_item_id:
        redirect_url = url_for('tracker.objective_detail', obj_id=comment.action_item.project.objective_id)
    else:
        redirect_url = url_for('tracker.dashboard')
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'success')
    return redirect(redirect_url)


# ---- Activity Feed ----

@tracker_bp.route('/feed')
@login_required
def activity_feed():
    comments = Comment.query.order_by(Comment.created_at.desc()).limit(50).all()
    recent_items = ActionItem.query.order_by(ActionItem.updated_at.desc()).limit(20).all()
    return render_template('feed.html', comments=comments, recent_items=recent_items)


# ---- Wiki ----

@tracker_bp.route('/wiki')
@login_required
def wiki_index():
    pages = WikiPage.query.order_by(WikiPage.title).all()
    return render_template('wiki_index.html', pages=pages)


@tracker_bp.route('/wiki/<slug>')
@login_required
def wiki_page(slug):
    page = WikiPage.query.filter_by(slug=slug).first()
    if not page:
        # Offer to create the page
        return render_template('wiki_page.html', page=None, slug=slug,
                             title=slug.replace('-', ' ').title())
    return render_template('wiki_page.html', page=page)


@tracker_bp.route('/wiki/new', methods=['GET', 'POST'])
@login_required
def new_wiki_page():
    form = WikiPageForm()
    if request.method == 'GET' and request.args.get('title'):
        form.title.data = request.args.get('title')

    if form.validate_on_submit():
        slug = re.sub(r'[^a-z0-9]+', '-', form.title.data.lower()).strip('-')
        existing = WikiPage.query.filter_by(slug=slug).first()
        if existing:
            flash('A page with that title already exists.', 'error')
            return redirect(url_for('tracker.wiki_page', slug=slug))
        page = WikiPage(
            slug=slug,
            title=form.title.data,
            body=form.body.data,
            created_by_id=current_user.id
        )
        db.session.add(page)
        db.session.commit()
        flash('Wiki page created.', 'success')
        return redirect(url_for('tracker.wiki_page', slug=slug))
    return render_template('wiki_form.html', form=form, editing=False)


@tracker_bp.route('/wiki/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_wiki_page(slug):
    page = WikiPage.query.filter_by(slug=slug).first_or_404()
    form = WikiPageForm(obj=page)

    if request.method == 'GET':
        form.title.data = page.title
        form.body.data = page.body

    if form.validate_on_submit():
        page.title = form.title.data
        page.slug = re.sub(r'[^a-z0-9]+', '-', form.title.data.lower()).strip('-')
        page.body = form.body.data
        db.session.commit()
        flash('Wiki page updated.', 'success')
        return redirect(url_for('tracker.wiki_page', slug=page.slug))
    return render_template('wiki_form.html', form=form, editing=True, page=page)


# ---- API ----

@tracker_bp.route('/api/stats')
@login_required
def api_stats():
    objectives = StrategicObjective.query.order_by(StrategicObjective.number).all()
    data = []
    for obj in objectives:
        data.append({
            'id': obj.id,
            'number': obj.number,
            'name': obj.name,
            'total': obj.action_item_count(),
            'open': obj.open_count(),
            'completed': obj.completed_count()
        })
    return jsonify(data)
