from flask import Blueprint, render_template
from flask_login import login_required, current_user
from . import db
from .models import Possession, User

main = Blueprint('main', __name__, static_folder='static')

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
def profile():
    data = db.session.query(Possession, Possession.material, Possession.quantity
    ).join(User, User.get_id(current_user) == Possession.id)
    return render_template('profile.html', name=current_user.name, data = data)

