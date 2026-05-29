import os
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'civicfix_secure_key_2026'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('civicfix.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE username = ? AND password = ? AND role = ?', 
                            (username, password, role)).fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            session['role'] = role
            if role == 'admin':
                return redirect('/admin')
            elif role == 'worker':
                return redirect(f'/worker/{username}')
        else:
            return render_template('login.html', error="Invalid username or password.")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/citizen')
def citizen_interface():
    conn = get_db_connection()
    reports = conn.execute("SELECT * FROM Reports ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('index.html', reports=reports)

@app.route('/submit_report', methods=['POST'])
def submit_report():
    user_comment = request.form.get('user_comment', '').strip()
    if not user_comment or 'user_image' not in request.files:
        return jsonify({"message": "Error: Photo and comment required."}), 400

    user_file = request.files['user_image']
    
    # Server-Side Image Validation
    if not user_file.mimetype.startswith('image/'):
        return jsonify({"message": "Please change the attached file to a valid image."}), 400

    try:
        lat, lon = float(request.form.get('lat')), float(request.form.get('lon'))
    except (TypeError, ValueError):
        lat, lon = 33.6844, 73.0479 

    filename = secure_filename(f"user_issue_{user_file.filename}")
    user_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO Reports (user_comment, user_image, lat, lon, status, assigned_worker)
        VALUES (?, ?, ?, ?, 'Pending', 'Unassigned')
    ''', (user_comment, filename, lat, lon))
    conn.commit()
    conn.close()
    return jsonify({"message": "Incident reported successfully."})

@app.route('/user_verify', methods=['POST'])
def user_verify():
    conn = get_db_connection()
    conn.execute("UPDATE Reports SET status = 'Verified' WHERE id = ?", (request.form['report_id'],))
    conn.commit()
    conn.close()
    return jsonify({"message": "Task verified and archived."})

@app.route('/delete_report', methods=['POST'])
def delete_report():
    conn = get_db_connection()
    conn.execute("DELETE FROM Reports WHERE id = ?", (request.form['report_id'],))
    conn.commit()
    conn.close()
    return jsonify({"message": "Record permanently removed."})

@app.route('/clear_all_history', methods=['POST'])
def clear_all_history():
    conn = get_db_connection()
    conn.execute("DELETE FROM Reports WHERE status = 'Verified'")
    conn.commit()
    conn.close()
    return jsonify({"message": "All verified history has been cleared."})

@app.route('/admin')
def admin_interface():
    if session.get('role') != 'admin':
        return redirect('/')
    conn = get_db_connection()
    reports = conn.execute("SELECT * FROM Reports ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin.html', reports=reports)

@app.route('/assign_task', methods=['POST'])
def assign_task():
    conn = get_db_connection()
    conn.execute("UPDATE Reports SET status = 'Assigned', assigned_worker = ? WHERE id = ?", 
                 (request.form['worker_name'], request.form['report_id']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Department Dispatched."})

@app.route('/admin_message_user', methods=['POST'])
def admin_message_user():
    conn = get_db_connection()
    conn.execute("UPDATE Reports SET admin_message = ? WHERE id = ?", 
                 (request.form['admin_message'], request.form['report_id']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Verification request sent."})

@app.route('/worker/<worker_id>')
def worker_interface(worker_id):
    if session.get('role') != 'worker' or session.get('username') != worker_id:
        return redirect('/')
    conn = get_db_connection()
    active_tasks = conn.execute("SELECT * FROM Reports WHERE assigned_worker = ? AND status = 'Assigned' ORDER BY id DESC", (worker_id,)).fetchall()
    history_tasks = conn.execute("SELECT * FROM Reports WHERE assigned_worker = ? AND status IN ('Completed', 'Verified') ORDER BY id DESC", (worker_id,)).fetchall()
    conn.close()
    return render_template('worker.html', active_tasks=active_tasks, history_tasks=history_tasks, worker_name=worker_id)

@app.route('/upload_proof', methods=['POST'])
def upload_proof():
    worker_comment = request.form.get('worker_comment', '').strip()
    if 'worker_image' not in request.files:
        return jsonify({"message": "Proof photo required."}), 400
        
    worker_file = request.files['worker_image']
    
    # Server-Side Image Validation
    if not worker_file.mimetype.startswith('image/'):
        return jsonify({"message": "Please change the attached file to a valid image."}), 400

    filename = secure_filename(f"worker_proof_{request.form['report_id']}.jpg")
    worker_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE Reports 
        SET worker_image = ?, worker_comment = ?, status = 'Completed'
        WHERE id = ?
    ''', (filename, worker_comment, request.form['report_id']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Proof uploaded successfully."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)