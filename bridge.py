#Author/s: Thanuja Athuruliya Withanage
#Date: 10/04/2026
#Version: 0.2.0
#Imports
from flask import Flask, render_template, url_for, request, redirect, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import shutil
import yaml
import os
import shutil
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
#End imports

#global variables
logged_in_admin = False
logged_in_user = False

#End of global variables


#Initialise the app
#The absolute path from the docker file for the databases
instance_path = "/Bridge/instance" 
app = Flask(__name__, instance_path=instance_path)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Bridge/instance/site.db'
app.config['SQLALCHEMY_BINDS'] = {
    'users_db': 'sqlite:////Bridge/instance/users.db',
    'drives_db': 'sqlite:////Bridge/instance/drives.db'
}
db = SQLAlchemy(app)
app.secret_key = 'super_secret_random_string' # Change this to something unique
#End app initialisation

#Initialise databases
class User(db.Model):
    """
    The user database, stores all the information relevant about a user with the appropriate data type in an SQL database
    """
    __bind_key__ = 'users_db'
    id = db.Column(db.Integer, primary_key=True)
    rank = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    
class Drive(db.Model):
    """
    The drives database, stores all the information relevant about a drive with the appropriate data type in an SQL database
    """
    __bind_key__ = 'drives_db'
    id = db.Column(db.Integer, primary_key=True)
    drive_name = db.Column(db.String(20), unique=True, nullable=False)
    drive_used = db.Column(db.Float, nullable=False)
    drive_size = db.Column(db.Float, nullable=False)
    drive_mnt = db.Column(db.String(50), unique=True, nullable=False)
    user_connection = db.Column(db.String(20))
#End databse initialisation


#App Functionaility
def get_drives():
    """
    This function gets the drives from the docker-compose file and stores the appropriate information about the drive into the Drive database
    """
    try:
        #Open the docker file
        with open("docker-compose.yaml", 'r') as f:
            services = yaml.safe_load(f).get('services', {})

        #Loop through the docker file until the program reaches the volumes section of the file(which is where the drives would be stored)
        for config in services.values():
            for v in config.get('volumes', []):
                if isinstance(v, str) and ":" in v:
                    path = v.split(':')[1]
                    #Only grab actual storage mounts
                    if path.startswith(('/mnt', '/media')):
                        #Get name and size in one-liners
                        name = path.split('/')[-1]
                        usage = shutil.disk_usage(path)
                        size_used = usage.used / (2**30)
                        size_total = usage.total / (2**30)
                        existing_drive = Drive.query.filter_by(drive_name=name).first()
                        
                        #This updates the existing drives' info when files are added etc
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
    """
    Handles all the functionality when it comes to admin's dashboard
    """
    global logged_in_admin
    #This means the user did not go through the login page
    if not logged_in_admin:
        return redirect('/login')
    
    #Grab all the users
    users = User.query.filter_by(rank="user").all()
    #Initialise all the variables in case they don't get updated later on
    drive_activity = False
    user_activity = False
    user_drive = None
    drive_size_print = None
    drive_used_print = None
    drive_free_print = None
    user_drive_connection = None
    selected_drive_name = None
    selected_user_name = None
    #print("Hello", flush=True)

    if request.method == "POST":
        #This is just to keep a selected item highlighted
        selected_user_name = request.form.get('user_name_input')
        selected_drive_name = request.form.get('drive_name_input')
        #Get the user selcted or drive selected (it can only be one or the other since the details are printed on the same box)
        drive_name = request.form.get("drive_name_input")
        user_name = request.form.get("user_name_input")
        #Handles if a drive is selected
        if drive_name:
            drive_activity = True
            #Finds the drive in the Drive database
            drive_details = Drive.query.filter_by(drive_name=drive_name).first()
            if drive_details:
                #Stores all the relevant information
                drive_size = drive_details.drive_size
                drive_size_print = round(float(drive_size), 2)
                drive_used = drive_details.drive_used
                drive_used_print = round(float(drive_used), 2)
                drive_free = float(drive_details.drive_size) - float(drive_details.drive_used)
                drive_free_print = round(drive_free, 2)
                user_drive_connection = drive_details.user_connection
                if user_drive_connection:
                    user_drive = user_drive_connection
                else:
                    user_drive = "No connections"
                #Debugging
                print(f"Admin clicked on: {drive_details.drive_name}", flush=True)
                print(f"It is mounted at: {drive_details.drive_mnt}", flush=True)
                print(f"Used space: {drive_details.drive_used}", flush=True)
                print(f"Total space: {drive_details.drive_size}", flush=True)
                print(f"Free space: {float(drive_details.drive_size) - float(drive_details.drive_used)}", flush=True)
        #Handles if a user is selected
        elif user_name:
            user_activity = True
            #Finds the user in the User database
            user_drive_connection = Drive.query.filter_by(user_connection=user_name).first()
            #Stores the connected drives
            if user_drive_connection:
                user_drive = user_drive_connection.drive_name
            else:
                user_drive = "No connections"

    get_drives()
    #This helps print the drives on the gui
    all_drives = Drive.query.all()
    return render_template("/admin_dashboard.html", drives=all_drives, drive_size=drive_size_print, drive_used=drive_used_print, drive_free=drive_free_print, users=users, drive_activity=drive_activity, user_activity=user_activity, user_drives=user_drive, selected_user_name=selected_user_name, selected_drive_name=selected_drive_name)

    
@app.route("/admin_setup", methods=["POST", "GET"])
def admin_setup():
    """
    Handles the admin setup
    """
    global logged_in_admin
    #Ensure the drive knows this an admin 
    rank = "admin"
    name_taken = None
    no_admin = True
    admins = User.query.filter_by(rank="admin").first()
    if admins:
        no_admin = False
        return render_template('/login.html')

    if request.method == "POST":
        #Grabs the username and password entered in the gui
        username = request.form.get("usrnme").strip()
        password = request.form.get("psswrd")
        #Encrypt the password
        encrypted_psswd = generate_password_hash(password)
        #Add the admin to the User database
        new_admin = User(rank=rank, username=username, password_hash=encrypted_psswd)
        try:
            db.session.add(new_admin)
            db.session.commit()
            logged_in_admin = True
            return redirect('/admin_dashboard')
        except:
            #If its a duplicate username then it does not add the user and informs the user through the gui
            print("duplicate name")
            logged_in_admin = False
            db.session.rollback()
            name_taken = "Error admin with that name already exists!"
            return render_template("/account_setup.html", rank=rank, duplicate_name = name_taken)
        
    return render_template('/account_setup.html', rank=rank, duplicate_name=name_taken, no_admin=no_admin)

@app.route("/user_setup", methods=["POST", "GET"])
def user_setup():
    """
    Step 1: Collect user info and store it in a session.
    No database insertion happens here.
    """
    rank = "user"
    name_taken = None

    if request.method == "POST":
        username = request.form.get("usrnme").strip()
        password = request.form.get("psswrd")

        # Check if the name exists before moving forward
        if User.query.filter_by(username=username).first():
            name_taken = "Error: User with that name already exists!"
            return render_template("/account_setup.html", rank=rank, duplicate_name=name_taken)

        #Store data in session instead of the DB
        #This keeps the hash out of the URL
        session['temp_user_data'] = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'rank': rank
        }

        return redirect(url_for('user_drive_setup'))

    return render_template('/account_setup.html', rank=rank, duplicate_name=name_taken)


@app.route("/user_drive_setup", methods=["POST", "GET"])
def user_drive_setup():
    """
    Step 2: Assign a drive and perform the final 'Atomic' database commit.
    """
    #Ensures they actually came from the setup page
    user_data = session.get('temp_user_data')
    if not user_data:
        return redirect(url_for('user_setup'))

    # Get available drives
    drives = Drive.query.filter_by(user_connection="None").all()

    if request.method == "POST":
        clicked_drive = request.form.get("selected_drive_name")
        drive_to_connect = Drive.query.filter_by(drive_name=clicked_drive).first()

        if drive_to_connect:
            try:
                #This ensures a new user is only added once they connect the user to a drive
                new_user = User(
                    rank=user_data['rank'],
                    username=user_data['username'],
                    password_hash=user_data['password_hash']
                )
                db.session.add(new_user)
                drive_to_connect.user_connection = user_data['username']


                user_dir = os.path.join(drive_to_connect.drive_mnt, user_data['username'])
                if not os.path.exists(user_dir):
                    os.makedirs(user_dir, mode=0o777)
                    os.chmod(user_dir, 0o777)


                db.session.commit()


                session.pop('temp_user_data', None)

                return redirect('/admin_dashboard')

            except Exception as e:
                db.session.rollback()
                print(f"Critical failure during user/drive creation: {e}")
                return "Internal Server Error", 500

    return render_template("/drive_setup.html", drives=drives, user=user_data['username'])

@app.route("/download/<username>/<path:filename>")
def download_file(username, filename):
    """
    Handles downloading files withing the user dashboard
    Inputs:
    - username: Need to know what drive the file is stored in so the username will find the drive/s that it will exist in
    - filename: the file the user is trying to download
    """
    #Finds the drive by finding the user's connection
    drive = Drive.query.filter_by(user_connection=username).first()
    
    if drive:
        #Download the file if it exists
        user_folder_path = os.path.join(drive.drive_mnt, username)
        try:
            return send_from_directory(directory=user_folder_path, path=filename, as_attachment=True)
        except FileNotFoundError:
            return "File not found.", 404
            
    return "Drive connection not found.", 404


@app.route("/view/<username>/<path:filename>")
def view_file(username, filename):
    """
    Handles the file preview within the user dashboard
    - username: Need to know what drive the file is stored in so the username will find the drive/s that it will exist in
    - filename: the file the user is trying to view
    """
    #Find the drive/s it will be stored in
    drive = Drive.query.filter_by(user_connection=username).first()
    
    if drive:
        #The extensions that can be previewed
        previewable_extensions = {'.pdf', '.txt', '.png', '.jpg', '.jpeg', '.gif', '.mp3', '.mp4'}
        #Split the filename between its name and the type of file
        _, ext = os.path.splitext(filename)
        
        #If its not a previewable extension
        if ext.lower() not in previewable_extensions:
            return f"""
            <div style="display: flex; height: 100vh; align-items: center; justify-content: center; flex-direction: column; color: gray; font-family: sans-serif; text-align: center;">
                <h3>No Preview Available</h3>
                <p>The file <b>{filename}</b> cannot be viewed in the browser.</p>
                <p>Please use the Download button to access it.</p>
            </div>
            """
        #Find the directory which the file is located in 
        user_folder_path = os.path.join(drive.drive_mnt, username)
        #Grab the file to preview
        try:
            return send_from_directory(directory=user_folder_path, path=filename)
        except FileNotFoundError:
            return "File not found.", 404
            
    return "Drive connection not found.", 404

@app.route("/delete/<username>/<path:filename>", methods=["POST"])
def delete_item(username, filename):
    """
    Handles deleting the file from the drive
    - username: Need to know what drive the file is stored in so the username will find the drive/s that it will exist in
    - filename: the file the user is trying to delete
    """
    #Verifies that there is a drive that this user is connected to
    drive = Drive.query.filter_by(user_connection=username).first()
    if not drive:
        return "Drive connection not found.", 404

    #Find the directory where the file is stored
    user_root = os.path.join(drive.drive_mnt, username)
    target_path = os.path.normpath(os.path.join(user_root, filename))

    # Security check
    if not target_path.startswith(os.path.abspath(user_root)):
        return "Unauthorized action.", 403

    try:
        #Deletes the file
        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)
            
            # Update the drive usage stats in the DB
            get_drives()
            
            #Figures out where to redirect after deleting
            parent_dir = os.path.dirname(filename)
            
            # Explicitly return to the dashboard
            return redirect(url_for('user_dashboard', subpath=parent_dir))
        else:
            print(f"File not found at: {target_path}")
            return "File not found.", 404
    except Exception as e:
        print(f"Delete failed with error: {e}")
        return f"Error deleting item: {e}", 500
    
@app.route("/user_dashboard", methods=["POST", "GET"])
def user_dashboard():
    """
    Handles the user dahboard functionality
    """
    global logged_in_user
    file_selected = False
    selected_file = None
    #Checks whether the user went through the login page
    if not logged_in_user:
        return redirect('/login')
    #Get the username from the login page
    stored_user = session.get('username_data')
    passed_user = stored_user["username"]

    #This gets the nested paths for nested folders
    subpath = request.args.get('subpath', '') 

    #Gets the drive information
    drive = Drive.query.filter_by(user_connection=passed_user).first()
    if not drive:
        return "Drive not found", 404
    used_space = drive.drive_used
    total_space = drive.drive_size
    space_left_kb = (total_space-used_space)*(2**20)
    used_percentage = round((used_space / total_space) * 100, 2)

    #Gets the base directory and stores it
    user_root_path = os.path.abspath(os.path.join(drive.drive_mnt, passed_user))

    #Gets the directory the user wnats to go in
    target_path = os.path.abspath(os.path.join(user_root_path, subpath))

    #If the target path doesn't start with the base directory then the user must be in the base directory
    if not target_path.startswith(user_root_path):
        target_path = user_root_path
        subpath = '' 

    if request.method == "POST":
        #Handles the upload feature
        selected_file = request.form.get("selected_file")
        if selected_file:
            file_selected = True
        #Checks whether the file picker in the html sent the data
        if 'file_to_upload' in request.files:
            #Get the bytes of the file
            file = request.files['file_to_upload']
            #Validation to see whether there is a file
            if file and file.filename != '':
                #Checks if the file directory exists
                os.makedirs(target_path, exist_ok=True)
                #Remove any complications from the file name
                safe_name = secure_filename(file.filename)
                #Saves the file in the drive
                file.save(os.path.join(target_path, safe_name))
                #Updates the drive info
                get_drives()
                return redirect(url_for('user_dashboard', subpath=subpath))

        #Handles the new folder feature
        folder_name = request.form.get("folder_name")
        if folder_name:
            #Removes any complications in folder name
            safe_folder_name = secure_filename(folder_name)
            #Creates a directory for the folder
            full_new_folder_path = os.path.join(target_path, safe_folder_name)
            #Actually makes the folder
            try:
                os.makedirs(full_new_folder_path, exist_ok=True)
                return redirect(url_for('user_dashboard', subpath=subpath))
            except Exception as e:
                print(f"Error creating folder: {e}")

    #Handles printing the files within the drive as well as any relevant information
    file_details = []
    try:
        #Get the files in an existing path
        if os.path.exists(target_path):
            with os.scandir(target_path) as entries:
                #loop through each file in the directory
                for entry in entries:
                    #Get the relevant information about the file and update the path
                    stats = entry.stat()
                    modified_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                    rel_path = os.path.relpath(entry.path, user_root_path).replace('\\', '/')
                    #If its a file
                    if entry.is_file():
                        #Get the size in a cleaner more readable format
                        raw_bytes = stats.st_size
                        if raw_bytes > 1024**3:
                            size_readable = f"{round(raw_bytes / (1024**3), 2)} GB"
                        elif raw_bytes > 1024**2:
                            size_readable = f"{round(raw_bytes / (1024**2), 2)} MB"
                        elif raw_bytes > 1024:
                            size_readable = f"{round(raw_bytes / (1024), 2)} KB"
                        else:
                            size_readable = f"{raw_bytes} B"
                        #Add the file information to a list through a dictionary to grab later
                        file_details.append({
                            "name": entry.name,
                            "size": size_readable,
                            "type": "File",
                            "modified": modified_time,
                            "rel_path": rel_path 
                        })
                    #If its a folder
                    elif entry.is_dir():
                        #Essentially the same but no data for the folder to be grabbed or shown
                        file_details.append({
                            "name": entry.name,
                            "size": "--",
                            "type": "Folder",
                            "modified": modified_time,
                            "rel_path": rel_path 
                        })
    except Exception as e:
        print(f"Error accessing drive: {e}")

    #Handles nested folders
    parent_subpath = None
    if subpath != '':
        parent_subpath = os.path.dirname(subpath)
        if parent_subpath in ['.', '/'] or parent_subpath == subpath:
            parent_subpath = ''

    return render_template('user_dashboard.html', files=file_details, username=passed_user,drive_size = space_left_kb, used_percentage=used_percentage,current_subpath=subpath,parent_subpath=parent_subpath,file_selected=file_selected,selected_file=selected_file)

@app.route("/login", methods=["POST", "GET"])
def login():
    """
    Handles the login functionality
    """

    #Initialise variables
    global logged_in_admin
    global logged_in_user
    logged_in_admin = False
    logged_in_user = False
    incorrect_user = False
    incorrect_password = False

    if request.method == "POST":
        #Get the attempt from the user
        username = request.form.get("usrnme").strip()
        password = request.form.get("psswrd")
        #First check if the user even exists
        find_user = User.query.filter_by(username=username).first()
        if find_user:
            #Next compare the encrypted version of both the attempted password and the real password
            if check_password_hash(find_user.password_hash, password):
                #Finally check the rank of the user and send them to the appropriate location
                if find_user.rank == "admin":
                    logged_in_admin = True
                    return redirect("/admin_dashboard")
                else:
                    logged_in_user = True
                    session['username_data'] = {
                        'username': username,
                    }
                    return redirect("/user_dashboard")
                    
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
    """
    Handles the user direction at the launch of the app
    """
    #Create the databases if they dont exist
    with app.app_context():
        db.create_all()
        print("Database created!")

    #Check if there is an admin already 
    admin = User.query.filter_by(rank="admin").first()
    if admin:
        return redirect("/login")
    else:
        return redirect("/admin_setup") 
#End app functionality

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host = '0.0.0.0', port='5000', debug="True")
    