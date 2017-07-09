from flask import Blueprint, render_template, current_app, request
from ..call.views import create
from ..call.decorators import crossdomain
from ..extensions import csrf

site = Blueprint('site', __name__, )
csrf.exempt(site)

@site.route('/')
def index():
    INSTALLED_ORG = current_app.config.get('INSTALLED_ORG', '<YOUR ORG NAME>')
    return render_template('site/index.html', INSTALLED_ORG=INSTALLED_ORG)


# legacy route to be compatible with call-congress
@site.route('/create', methods = ['GET', 'POST'])
@crossdomain(origin='*')
def legacy_call_redirect():
	# don't redirect, just return desired function
	return create()
