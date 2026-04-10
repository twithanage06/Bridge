#Author/s: Thanuja Athuruliya Withanage
#Date: 10/04/2026
#Version: 0.0.0

from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import numpy as np
import subprocess as sp
import yaml
import os
import shutil
from werkzeug.security import generate_password_hash, check_password_hash

#Initialises the app and databses
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' 
app.config['SQLALCHEMY_BINDS'] = {
    'users_db': 'sqlite:///users.db',
    'drives_db': 'sqlite:///drives.db'
}
db = SQLAlchemy(app)

class User(db.Model):
    __bind_key__ = 'users_db'
    id = db.Column(db.Integer, primary_key=True)
    rank = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"User('{self.username}')"
    
class Drive(db.Model):
    __bind_key__ = 'drives_db'
    id = db.Column(db.Integer, primary_key=True)
    drive_name = db.Column(db.String(20), unique=True, nullable=False)
    drive_size = db.Column(db.String(20), nullable=False)
    drive_mnt = db.Column(db.String(50), unique=True, nullable=False)
    user_connection = db.Column(db.String(20))


def get_drives():
    try:
        with open("docker-compose.yaml", 'r') as f:
            services = yaml.safe_load(f).get('services', {})

        Drive.query.delete()

        for config in services.values():
            for v in config.get('volumes', []):
                if isinstance(v, str) and ":" in v:
                    path = v.split(':')[1]
                    # Only grab actual storage mounts
                    if path.startswith(('/mnt', '/media')):
                        # Get name and size in one-liners
                        name = path.split('/')[-1]
                        usage = shutil.disk_usage(path)
                        size_info = f"{usage.used // (2**30)}GB / {usage.total // (2**30)}GB"
                        
                        db.session.add(Drive(drive_name=name, drive_size=size_info, drive_mnt=path, user_connection="None"))

        db.session.commit()
    except Exception as e:
        print(f"Sync failed: {e}")
        db.session.rollback()
                


@app.route("/admin_dashboard", methods=["POST","GET"])
def admin_dashboard():
    
    return render_template("/admin_dashboard.html")

@app.route("/admin_setup", methods=["POST", "GET"])
def admin_setup():
    rank = "admin"
    name_taken = None
    if request.method == "POST":
        username = request.form.get("usrnme").strip()
        password = request.form.get("psswrd")
        encrypted_psswd = generate_password_hash(password)

        new_admin = User(rank=rank, username=username, password_hash=encrypted_psswd)
        try:
            db.session.add(new_admin)
            db.session.commit()
            return redirect('/admin_dashboard')
        except:
            print("duplicate name")
            db.session.rollback()
            name_taken = "Error admin with that name already exists!"
            return render_template("/account_setup.html", rank=rank, duplicate_name = name_taken)
        
    return render_template('/account_setup.html', rank=rank, duplicate_name=name_taken)

@app.route('/nuke')
def nuke_everything():
    """
    Resets the file storing chosen user back to defualt

    Inputs: username
    Outputs: None
    """
    default = "0,NULL,NULL"
    with open("initial_setup.txt", "w") as f:
        f.write(default)
    with app.app_context():
        db.drop_all()   # Deletes the tables
        db.create_all() # Recreates them fresh
    return "Database wiped. Try the setup again!"

@app.route("/")
def root():
    get_drives()
    with app.app_context():
        db.create_all()
        print("Database created!")

    with open("setup_done.txt", "r") as f:
        setup_done = f.readline().strip()
    if str(setup_done) == "0":
        return redirect("/admin_setup")
    

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port='5000')