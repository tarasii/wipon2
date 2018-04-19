from flask import Flask, session, request, render_template, redirect, flash, url_for, g, jsonify
import os
import utill

from sqlite3 import dbapi2 as sqlite3


app = Flask(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'main'),
    DEBUG=True,
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/'
))

# def create_app(config=None):
#     app = Flask(__name__)
#
#     app.config.update(dict(
#         DATABASE=os.path.join(app.root_path, 'flaskr.db'),
#         DEBUG=True,
#         SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/',
#         USERNAME='admin',
#         PASSWORD='default'
#     ))
#     app.config.update(config or {})
#     app.config.from_envvar('FLASKR_SETTINGS', silent=True)
#
#
#     return app

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


# def init_db():
#     """Initializes the database."""
#     db = get_db()
#     with current_app.open_resource('schema.sql', mode='r') as f:
#         db.cursor().executescript(f.read())
#     db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.route("/")
def index():
    return redirect(url_for('go'))

@app.route("/go", methods=['GET', 'POST'])
def go():
    db = get_db()
    settings_db = utill.get_raw_settings(db)
    settings_form = utill.get_settings(settings_db)

    if request.method == 'POST':
        session['logged_in'] = False
        utill.save_settings(db, request.form, settings_form, settings_db)

    id, count_all, count, barcode, status = utill.get_statistics(db)

    settings_form['count'] = "{}/{}".format(count, count_all)
    settings_form['last_id'] = id
    settings_form['status'] = status

    settings_form['categories_all'] = utill.default_categories
    settings_form['colors_all'] = utill.default_colors
    settings_form['templates_all'] = utill.default_templates
    settings_form['products_all'] = utill.default_products


    settings_form['barcode_right'] = utill.make_barcode(settings_form['enterprise'], settings_form['line_right'], id+1)
    settings_form['barcode_left'] = utill.make_barcode(settings_form['enterprise'], settings_form['line_left'], id+1)
    settings_form['barcode_last'] = barcode

    return render_template('index.html', **settings_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    #session['logged_in'] = False
    error = None
    if request.method == 'POST':
        error = utill.check_authorization(app, request.form['username'], request.form['password'])
        if not error:
            session['logged_in'] = True
            session['username'] = request.form['username']
            flash('You were logged in')
            return redirect(url_for('go'))

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session['logged_in'] = False
    #session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('go'))


@app.route('/get_settings')
def get_settings():
    db = get_db()
    settings_db = utill.get_settings(db)
    settings_form = {x: settings_db.get(x, utill.default_settings[x]) for x in utill.default_settings.keys()}
    return jsonify(settings_form)

@app.route('/get_errors')
def get_errors():
    db = get_db()
    cur = db.execute('SELECT datetime, barcode, value FROM error_log ORDER BY id DESC LIMIT 20')
    error_entries = cur.fetchall()

    return render_template('get_errors.html', errors=error_entries)


if __name__=='__main__':
    app.run()