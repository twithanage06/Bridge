#Author/s: Thanuja Athuruliya Withanage
#Date: 10/04/2026
#Version: 0.0.8

from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import numpy as np
import subprocess as sp
import yaml
import os
import shutil
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Use the absolute path inside the container
instance_path = "/Bridge/instance" 

app = Flask(__name__, instance_path=instance_path)

# Ensure the DBs are explicitly inside that absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Bridge/instance/site.db'
app.config['SQLALCHEMY_BINDS'] = {
    'users_db': 'sqlite:////Bridge/instance/users.db',
    'drives_db': 'sqlite:////Bridge/instance/drives.db'
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
    drive_used = db.Column(db.String(20), nullable=False)
    drive_size = db.Column(db.Float, nullable=False)
    drive_mnt = db.Column(db.String(50), unique=True, nullable=False)
    user_connection = db.Column(db.String(20))


def get_drives():
    try:
        with open("docker-compose.yaml", 'r') as f:
            services = yaml.safe_load(f).get('services', {})



        for config in services.values():
            for v in config.get('volumes', []):
                if isinstance(v, str) and ":" in v:
                    path = v.split(':')[1]
                    # Only grab actual storage mounts
                    if path.startswith(('/mnt', '/media')):
                        # Get name and size in one-liners
                        name = path.split('/')[-1]
                        usage = shutil.disk_usage(path)
                        size_used = usage.used / (2**30)
                        size_total = usage.total / (2**30)
                        existing_drive = Drive.query.filter_by(drive_name=name).first()
                        
                        if existing_drive:

                            existing_drive.drive_used = size_used
                            existing_drive.drive_size = size_total
                        else:
                            
                            db.session.add(Drive(drive_name=name, drive_used=size_used, drive_size=size_total, drive_mnt=path, user_connection="None"))


        db.session.commit()
    except Exception as e:
        print(f"Sync failed: {e}")
        db.session.rollback()
                


@app.route("/admin_dashboard", methods=["POST","GET"])
def admin_dashboard():
    users = User.query.filter_by(rank="user").all()
    drive_activity = False
    user_activity = False
    user_drive = None
    drive_size_print = None
    drive_used_print = None
    drive_free_print = None
    user_drive_connection = None
    print("Hello", flush=True)
    if request.method == "POST":
        drive_name = request.form.get("drive_name_input")
        user_name = request.form.get("user_name_input")
        if drive_name:
            drive_activity = True
            drive_details = Drive.query.filter_by(drive_name=drive_name).first()
            if drive_details:
                drive_size = drive_details.drive_size
                drive_size_print = round(float(drive_size), 2)
                drive_used = drive_details.drive_used
                drive_used_print = round(float(drive_used), 2)
                drive_free = float(drive_details.drive_size) - float(drive_details.drive_used)
                drive_free_print = round(drive_free, 2)
                print(f"Admin clicked on: {drive_details.drive_name}", flush=True)
                print(f"It is mounted at: {drive_details.drive_mnt}", flush=True)
                print(f"Used space: {drive_details.drive_used}", flush=True)
                print(f"Total space: {drive_details.drive_size}", flush=True)
                print(f"Free space: {float(drive_details.drive_size) - float(drive_details.drive_used)}", flush=True)
        elif user_name:
            user_activity = True
            user_drive_connection = Drive.query.filter_by(user_connection=user_name).first()
            if user_drive_connection:
                user_drive = user_drive_connection.drive_name
            else:
                user_drive = "No connections"

    get_drives()
    all_drives = Drive.query.all()
    return render_template("/admin_dashboard.html", drives=all_drives, drive_size=drive_size_print, drive_used=drive_used_print, drive_free=drive_free_print, users=users, drive_activity=drive_activity, user_activity=user_activity, user_drives=user_drive)

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
            with open("initial_setup.txt", "w") as f:
                f.write("1")
            return redirect('/admin_dashboard')
        except:
            print("duplicate name")
            db.session.rollback()
            name_taken = "Error admin with that name already exists!"
            return render_template("/account_setup.html", rank=rank, duplicate_name = name_taken)
        
    return render_template('/account_setup.html', rank=rank, duplicate_name=name_taken)

@app.route("/user_setup", methods=["POST", "GET"])
def user_setup():
    rank = "user"
    name_taken = None
    if request.method == "POST":
        username = request.form.get("usrnme").strip()
        password = request.form.get("psswrd")
        encrypted_psswd = generate_password_hash(password)

        new_user = User(rank=rank, username=username, password_hash=encrypted_psswd)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('user_drive_setup', username=username))
        except:
            print("duplicate name")
            db.session.rollback()
            name_taken = "Error user with that name already exists!"
            return render_template("/account_setup.html", rank=rank, duplicate_name = name_taken)
    return render_template('/account_setup.html', rank=rank, duplicate_name=name_taken)

@app.route("/user_drive_setup", methods=["POST", "GET"])
def user_drive_setup():
    drives = Drive.query.filter_by(user_connection="None").all()
    passed_user = request.args.get('username')
    if request.method == "POST":
        clicked_drive = request.form.get("selected_drive_name")
        passed_user = request.form.get("hidden_username")
        print(f"User clicked on drive: {clicked_drive}", flush=True)
        drive_to_connect = Drive.query.filter_by(drive_name=clicked_drive).first()
        if drive_to_connect:
            drive_to_connect.user_connection = passed_user
            user_dir = os.path.join(drive_to_connect.drive_mnt, passed_user)
            try:
                if not os.path.exists(user_dir):
                    os.makedirs(user_dir, mode=0o777)
                    os.chmod(user_dir, 0o777)
                db.session.commit()
                return redirect('/admin_dashboard')
            except OSError as e:
                db.session.rollback()
                print(f"Directory creation failed: {e}")
    return render_template("/drive_setup.html", drives=drives, user=passed_user)

@app.route("/user_dashboard", methods=["POST", "GET"])
def user_dashboard():
    passed_user = request.args.get('username')
    drive = Drive.query.filter_by(user_connection=passed_user).first()
    
    file_details = []
    
    if drive:
        user_folder_path = os.path.join(drive.drive_mnt, passed_user)
        try:
            if os.path.exists(user_folder_path):
                with os.scandir(user_folder_path) as entries:
                    for entry in entries:
                        if entry.is_file():
                            stats = entry.stat()
                            raw_bytes = stats.st_size
                            if raw_bytes > 1024**3:
                                size_readable = f"{round(raw_bytes / (1024), 2)} GB"
                            elif raw_bytes > 1024**2:
                                size_readable = f"{round(stats.st_size / (1024), 2)} MB"
                            elif raw_bytes > 1024:
                                size_readable = f"{round(stats.st_size / (1024), 2)} KB"
                            else:
                                size_readable = f"{raw_bytes} B"
                            file_details.append({
                                "name": entry.name,
                                "size": size_readable,
                                "modified": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                            })
        except Exception as e:
            print(f"Error accessing drive: {e}")
            
    return render_template('user_dashboard.html', files=file_details, username=passed_user)

@app.route("/login", methods=["POST", "GET"])
def login():
    incorrect_user = False
    incorrect_password = False
    if request.method == "POST":
        username = request.form.get("usrnme").strip()
        password = request.form.get("psswrd")

        find_user = User.query.filter_by(username=username).first()
        if find_user:
            if check_password_hash(find_user.password_hash, password):
                if find_user.rank == "admin":
                    return redirect("/admin_dashboard")
                else:
                    return redirect(url_for("user_dashboard", username=username))
            else:
                incorrect_password = True
        else:
            incorrect_user = True

        

    return render_template("/login.html", user_login = incorrect_user, user_pass = incorrect_password)

@app.route('/nuke')
def nuke_everything():
    """
    Resets the file storing chosen user back to defualt

    Inputs: username
    Outputs: None
    """
    default = "0"
    with open("initial_setup.txt", "w") as f:
        f.write(default)
    with app.app_context():
        db.drop_all()   
        db.create_all() 
    return "Database wiped. Try the setup again!"

@app.route("/")
def root():
    
    with app.app_context():
        db.create_all()
        print("Database created!")

    admin = User.query.filter_by(rank="admin").first()
    if admin:
        return redirect("/login")
    else:
        return redirect("/admin_setup") 
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host = '0.0.0.0', port='5000', debug="True")
    