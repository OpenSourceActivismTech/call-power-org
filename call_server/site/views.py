from flask import Blueprint, render_template, current_app, redirect, url_for, request
from ..call.decorators import crossdomain
from ..extensions import csrf

site = Blueprint('site', __name__, )
csrf.exempt(site)

@site.route('/')
def index():
    INSTALLED_ORG = current_app.config.get('INSTALLED_ORG', '<YOUR ORG NAME>')
    return render_template('site/index.html', INSTALLED_ORG=INSTALLED_ORG)


@site.route('/create')
@crossdomain(origin='*')
def legacy_call_redirect():
	return redirect(url_for('call.create', **request.args), 302)
