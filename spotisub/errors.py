from flask import render_template
from spotisub import spotisub, configuration_db


@spotisub.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', title='Page Not Found'), 404


@spotisub.errorhandler(500)
def internal_error(error):
    configuration_db.session.rollback()
    return render_template('errors/500.html', title='Unexpected Error'), 500
