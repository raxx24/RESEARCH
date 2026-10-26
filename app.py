from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash
import os, csv, io, hashlib, hmac, math
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(32)
mongo_client = MongoClient(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017'), serverSelectionTimeoutMS=5000)
database = mongo_client[os.environ.get('MONGODB_DATABASE', 'fieldnote')]

SKILLS = [
    ('Programming','Python'),('Programming','Java'),('Programming','JavaScript'),('Programming','C++'),('Programming','SQL'),
    ('Web Development','HTML/CSS'),('Web Development','React'),('Web Development','Node.js'),('Web Development','Flask'),
    ('Design','UI/UX Design'),('Design','Graphic Design'),('Design','Photoshop'),('Design','AutoCAD'),
    ('Creative','Video Editing'),('Creative','Photography'),('Creative','Content Writing'),('Creative','Public Speaking'),
    ('Business','Digital Marketing'),('Business','Project Management'),('Business','Data Analytics'),
    ('Cloud','AWS'),('Cloud','Azure'),('Cloud','Google Cloud'),('Data','Machine Learning'),('Data','Data Science')
]

def db():
    return database

def next_id(collection_name):
    counter = db().counters.find_one_and_update(
        {'_id': collection_name}, {'$inc': {'sequence': 1}}, upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return counter['sequence']

def insert_document(collection_name, document):
    document['id'] = next_id(collection_name)
    db()[collection_name].insert_one(document)
    return document['id']

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, stored_password):
    if '$' in stored_password:
        return check_password_hash(stored_password, password)
    legacy_hash = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(stored_password, legacy_hash)

def init_db():
    database.users.create_index('username_key', unique=True)
    database.users.create_index('email_key', unique=True)
    database.connections.create_index([('user_id', 1), ('partner_id', 1)], unique=True)
    database.experiment_collaborators.create_index([('experiment_id', 1), ('user_id', 1)], unique=True)

    now = datetime.now().isoformat(timespec='seconds')
    if database.users.count_documents({}) == 0:
        demo = [
            ('ram','ram@example.com','CSE student interested in full-stack development and cloud technologies.','Web Development,Cloud,Design'),
            ('ananya','ananya@example.com','UI/UX designer who enjoys mentoring beginners.','Design,Creative'),
            ('arjun','arjun@example.com','Python and data enthusiast looking for project collaborators.','Programming,Data'),
            ('meena','meena@example.com','Digital marketing learner and content creator.','Business,Creative')
        ]
        users = {}
        for username, email, bio, interests in demo:
            user_id = insert_document('users', {
                'username': username, 'username_key': username.lower(), 'email': email,
                'email_key': email.lower(), 'password': hash_password('1234'), 'bio': bio,
                'interests': interests, 'created_at': now
            })
            users[username] = user_id

        skill_rows = [
            ('ram','Python','Can Teach','Advanced'),('ram','Flask','Can Teach','Intermediate'),('ram','UI/UX Design','Want to Learn','Beginner'),('ram','AWS','Want to Learn','Beginner'),
            ('ananya','UI/UX Design','Can Teach','Advanced'),('ananya','Graphic Design','Can Teach','Advanced'),('ananya','Photography','Can Teach','Intermediate'),('ananya','Python','Want to Learn','Beginner'),
            ('arjun','Python','Can Teach','Advanced'),('arjun','Machine Learning','Can Teach','Intermediate'),('arjun','SQL','Can Teach','Advanced'),('arjun','React','Want to Learn','Beginner'),
            ('meena','Digital Marketing','Can Teach','Advanced'),('meena','Content Writing','Can Teach','Advanced'),('meena','Public Speaking','Want to Learn','Intermediate')
        ]
        for username, name, skill_type, level in skill_rows:
            insert_document('skills', {'user_id': users[username], 'name': name, 'type': skill_type, 'level': level})
        for title, description, target_date, progress in [
            ('Build a portfolio website','Complete a responsive portfolio with projects and contact form','2026-10-30',45),
            ('Learn UI/UX fundamentals','Finish core UX research and wireframing modules','2026-11-15',20)
        ]:
            insert_document('goals', {'user_id': users['ram'], 'title': title, 'description': description,
                'target_date': target_date, 'progress': progress, 'status': 'Active', 'created_at': now})
        for index, title in enumerate(['Flask API practice','AWS Skill Builder','UI/UX wireframe study']):
            insert_document('activities', {'user_id': users['ram'], 'title': title, 'minutes': 45 + index * 15,
                'activity_date': date.today().isoformat(), 'notes': 'Demo activity'})

    if database.equipment.count_documents({}) == 0:
        equipment_rows = [
            ('Cryo-TEM 01','Titan Krios G4','Imaging suite A','In use',78,'2026-10-18'),
            ('Mass Spectrometer','Orbitrap Exploris 480','Analytical lab B','Available',54,'2026-10-24'),
            ('X-ray Diffractometer','Empyrean Series 3','Materials wing','Available',36,'2026-11-02'),
            ('Confocal Microscope','LSM 980','Imaging suite C','Maintenance',12,'2026-10-13')
        ]
        equipment_ids = {}
        for name, model, location, status, utilization, maintenance_date in equipment_rows:
            equipment_ids[name] = insert_document('equipment', {'name': name, 'model': model, 'location': location,
                'status': status, 'utilization': utilization, 'maintenance_date': maintenance_date})
        now_dt = datetime.now().replace(second=0, microsecond=0)
        researcher_rows = list(database.users.find({}, {'username': 1, 'id': 1}).sort('id', 1))
        people = {user['username']: user['id'] for user in researcher_rows}
        lead_ids = [people.get(name, researcher_rows[index % len(researcher_rows)]['id'])
            for index, name in enumerate(('ram', 'ananya', 'arjun'))]
        experiment_rows = [
            ('Membrane protein structure','Structural Biology',lead_ids[0],equipment_ids['Cryo-TEM 01'],now_dt + timedelta(hours=2),now_dt + timedelta(hours=5)),
            ('Cell response time series','Neurobiology',lead_ids[1],equipment_ids['Confocal Microscope'],now_dt + timedelta(days=1),now_dt + timedelta(days=1,hours=3)),
            ('Catalyst surface mapping','Materials Science',lead_ids[2],equipment_ids['X-ray Diffractometer'],now_dt + timedelta(days=2),now_dt + timedelta(days=2,hours=4))
        ]
        for title, project, lead_id, equipment_id, starts_at, ends_at in experiment_rows:
            experiment_id = insert_document('experiments', {'title': title, 'project': project, 'lead_id': lead_id,
                'equipment_id': equipment_id, 'starts_at': starts_at.isoformat(timespec='minutes'),
                'ends_at': ends_at.isoformat(timespec='minutes'), 'status': 'Scheduled', 'created_at': now_dt.isoformat(timespec='seconds')})
            if title == 'Membrane protein structure':
                insert_document('detector_runs', {'experiment_id': experiment_id, 'detector': 'Cryo-TEM',
                    'dataset': 'membrane_scan_042', 'size_gb': 128.4, 'status': 'Ready',
                    'captured_at': (now_dt - timedelta(hours=1)).isoformat(timespec='minutes')})
                collaborator_id=people.get('ananya')
                if collaborator_id and collaborator_id != lead_id:
                    insert_document('experiment_collaborators', {'experiment_id': experiment_id,
                        'user_id': collaborator_id, 'status': 'Accepted'})

init_db()

@app.context_processor
def inject():
    return {'current_user': session.get('username')}

def login_required():
    return 'user_id' in session

def current_user_id(): return session.get('user_id')

@app.route('/')
def index():
    if login_required(): return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form.get('username','').strip()
        email=request.form.get('email','').strip().lower()
        password=request.form.get('password','')

        if not username or not email:
            flash('Username and email are required.','danger'); return render_template('register.html')
        if len(username) < 3:
            flash('Username must be at least 3 characters.','danger'); return render_template('register.html')
        if len(password) < 4:
            flash('Password must contain at least 4 characters.','danger'); return render_template('register.html')

        users = db().users
        if users.find_one({'$or': [{'username_key': username.lower()}, {'email_key': email}]}):
            flash('Username or email already exists. Please choose another one.','danger')
            return render_template('register.html')

        try:
            insert_document('users', {'username': username, 'username_key': username.lower(), 'email': email,
                'email_key': email, 'password': hash_password(password), 'bio': '', 'interests': '',
                'created_at': datetime.now().isoformat(timespec='seconds')})
            flash('Account created. Please sign in.','success'); return redirect(url_for('login'))
        except DuplicateKeyError:
            flash('Username or email already exists. Please choose another one.','danger')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        ident=request.form['identifier'].strip().lower(); password=request.form['password']
        user=db().users.find_one({'$or': [{'username_key': ident}, {'email_key': ident}]}, {'_id': 0})
        if user and verify_password(password, user['password']):
            if '$' not in user['password']:
                db().users.update_one({'id': user['id']}, {'$set': {'password': hash_password(password)}})
            session['user_id']=user['id']; session['username']=user['username']; return redirect(url_for('dashboard'))
        flash('Invalid login details.','danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not login_required(): return redirect(url_for('login'))
    database=db(); uid=current_user_id()
    experiments=[]
    for experiment in database.experiments.find().sort('starts_at', 1).limit(8):
        experiment.pop('_id', None)
        lead=database.users.find_one({'id': experiment['lead_id']}, {'_id': 0, 'username': 1})
        equipment_record=database.equipment.find_one({'id': experiment.get('equipment_id')}, {'_id': 0, 'name': 1})
        experiment['lead']=lead['username'] if lead else 'Unknown'
        experiment['equipment_name']=equipment_record['name'] if equipment_record else None
        experiment['collaborator_count']=database.experiment_collaborators.count_documents({'experiment_id': experiment['id']})
        experiments.append(experiment)
    equipment=list(database.equipment.find({}, {'_id': 0}).sort('utilization', -1))
    detector_runs=[]
    for detector_run in database.detector_runs.find().sort('captured_at', -1).limit(6):
        detector_run.pop('_id', None)
        related_experiment=database.experiments.find_one({'id': detector_run['experiment_id']}, {'_id': 0, 'title': 1})
        detector_run['experiment_title']=related_experiment['title'] if related_experiment else 'Unknown'
        detector_runs.append(detector_run)
    researchers=[]
    for researcher in database.users.find({}, {'_id': 0, 'id': 1, 'username': 1}):
        led_ids=[item['id'] for item in database.experiments.find({'lead_id': researcher['id']}, {'id': 1})]
        collaborated_ids=[item['experiment_id'] for item in database.experiment_collaborators.find({'user_id': researcher['id']}, {'experiment_id': 1})]
        researcher['experiment_count']=len(set(led_ids + collaborated_ids))
        researchers.append(researcher)
    researchers.sort(key=lambda item: (-item['experiment_count'], item['username']))
    researchers=researchers[:8]
    detector_documents=list(database.detector_runs.find({}, {'size_gb': 1}))
    equipment_documents=list(database.equipment.find({}, {'utilization': 1}))
    metrics={
        'experiments':database.experiments.count_documents({'status': {'$in': ['Scheduled', 'Running']}}),
        'datasets':len(detector_documents),
        'data_gb':sum(item.get('size_gb', 0) for item in detector_documents),
        'utilization':round(sum(item.get('utilization', 0) for item in equipment_documents) / len(equipment_documents)) if equipment_documents else 0
    }
    return render_template('landing.html',experiments=experiments,equipment=equipment,detector_runs=detector_runs,researchers=researchers,metrics=metrics)

@app.route('/experiments/schedule', methods=['POST'])
def schedule_experiment():
    if not login_required(): return redirect(url_for('login'))
    title=request.form.get('title','').strip(); project=request.form.get('project','').strip()
    starts_at=request.form.get('starts_at',''); ends_at=request.form.get('ends_at','')
    try:
        starts=datetime.fromisoformat(starts_at); ends=datetime.fromisoformat(ends_at)
        if not title or not project or ends <= starts: raise ValueError
    except ValueError:
        flash('Enter an experiment, project, and a valid time range.','danger')
        return redirect(url_for('dashboard')+'#schedule')
    equipment_id=request.form.get('equipment_id') or None
    database=db()
    if equipment_id:
        try:
            equipment_id=int(equipment_id)
        except ValueError:
            flash('Choose a valid instrument.','danger')
            return redirect(url_for('dashboard')+'#schedule')
        equipment=database.equipment.find_one({'id': equipment_id}, {'status': 1})
        if not equipment or equipment['status']=='Maintenance':
            flash('That instrument is not available for booking.','danger')
            return redirect(url_for('dashboard')+'#schedule')
        conflict=database.experiments.find_one({'equipment_id': equipment_id, 'status': {'$ne': 'Cancelled'},
            'starts_at': {'$lt': ends_at}, 'ends_at': {'$gt': starts_at}}, {'_id': 1})
        if conflict:
            flash('That instrument is already booked during this time.','danger')
            return redirect(url_for('dashboard')+'#schedule')
    insert_document('experiments', {'title': title, 'project': project, 'lead_id': current_user_id(),
        'equipment_id': equipment_id, 'starts_at': starts_at, 'ends_at': ends_at, 'status': 'Scheduled',
        'created_at': datetime.now().isoformat(timespec='seconds')})
    flash('Experiment scheduled.','success')
    return redirect(url_for('dashboard')+'#experiments')

@app.route('/detector-runs', methods=['POST'])
def log_detector_run():
    if not login_required(): return redirect(url_for('login'))
    try:
        experiment_id=int(request.form['experiment_id']); size_gb=float(request.form.get('size_gb',0))
        if not math.isfinite(size_gb) or size_gb < 0: raise ValueError
    except (ValueError,KeyError):
        flash('Choose an experiment and enter a valid data size.','danger')
        return redirect(url_for('dashboard')+'#data')
    detector=request.form.get('detector','').strip(); dataset=request.form.get('dataset','').strip()
    if not detector or not dataset:
        flash('Detector and dataset name are required.','danger')
        return redirect(url_for('dashboard')+'#data')
    database=db()
    if not database.experiments.find_one({'id': experiment_id}, {'_id': 1}):
        flash('Choose an existing experiment.','danger')
        return redirect(url_for('dashboard')+'#data')
    insert_document('detector_runs', {'experiment_id': experiment_id, 'detector': detector, 'dataset': dataset,
        'size_gb': size_gb, 'status': 'Processing', 'captured_at': datetime.now().isoformat(timespec='minutes')})
    flash('Detector data record added.','success')
    return redirect(url_for('dashboard')+'#data')

@app.route('/equipment/<int:equipment_id>/status', methods=['POST'])
def update_equipment_status(equipment_id):
    if not login_required(): return redirect(url_for('login'))
    status=request.form.get('status','')
    if status not in ('Available','In use','Maintenance'):
        flash('Select a valid equipment status.','danger')
    else:
        db().equipment.update_one({'id': equipment_id}, {'$set': {'status': status}})
        flash('Equipment status updated.','success')
    return redirect(url_for('dashboard')+'#equipment')

@app.route('/experiments/<int:experiment_id>/collaborators', methods=['POST'])
def invite_collaborator(experiment_id):
    if not login_required(): return redirect(url_for('login'))
    username=request.form.get('username','').strip()
    database=db(); user=database.users.find_one({'username_key': username.lower()}, {'id': 1})
    experiment=database.experiments.find_one({'id': experiment_id}, {'id': 1})
    if not user or not experiment or user['id']==current_user_id():
        flash('Choose an existing researcher and experiment.','danger')
    else:
        try:
            insert_document('experiment_collaborators', {'experiment_id': experiment_id, 'user_id': user['id'], 'status': 'Invited'})
            flash('Researcher invited to collaborate.','success')
        except DuplicateKeyError:
            flash('That researcher is already on this experiment.','info')
    return redirect(url_for('dashboard')+'#team')

@app.route('/profile', methods=['GET','POST'])
def profile():
    if not login_required(): return redirect(url_for('login'))
    database=db(); uid=current_user_id()
    if request.method=='POST':
        database.users.update_one({'id': uid}, {'$set': {'bio': request.form.get('bio',''), 'interests': request.form.get('interests','')}})
        flash('Profile updated.','success')
    user=database.users.find_one({'id': uid}, {'_id': 0})
    skills=list(database.skills.find({'user_id': uid}, {'_id': 0}).sort([('type', 1), ('name', 1)]))
    return render_template('profile.html',user=user,skills=skills,skill_catalog=SKILLS)

@app.route('/skills', methods=['GET','POST'])
def skills():
    if not login_required(): return redirect(url_for('login'))
    database=db(); uid=current_user_id()
    if request.method=='POST':
        name=request.form['name']; typ=request.form['type']; level=request.form.get('level','Intermediate')
        if name:
            insert_document('skills', {'user_id': uid, 'name': name, 'type': typ, 'level': level})
            flash('Skill added.','success')
        return redirect(url_for('skills'))
    rows=list(database.skills.find({'user_id': uid}, {'_id': 0}).sort([('type', 1), ('name', 1)]))
    return render_template('skills.html',skills=rows,skill_catalog=SKILLS)

@app.route('/skills/delete/<int:sid>', methods=['POST'])
def skill_delete(sid):
    if not login_required(): return redirect(url_for('login'))
    db().skills.delete_one({'id': sid, 'user_id': current_user_id()})
    return redirect(url_for('skills'))

@app.route('/discover')
def discover():
    if not login_required(): return redirect(url_for('login'))
    q=request.args.get('q','').strip().lower(); category=request.args.get('category','').strip()
    database=db(); uid=current_user_id()
    users=list(database.users.find({'id': {'$ne': uid}}, {'_id': 0, 'id': 1, 'username': 1, 'bio': 1, 'interests': 1}))
    results=[]
    current_skills=list(database.skills.find({'user_id': uid}, {'_id': 0, 'name': 1, 'type': 1}))
    wanted={skill['name'] for skill in current_skills if skill['type']=='Want to Learn'}
    offered={skill['name'] for skill in current_skills if skill['type']=='Can Teach'}
    for u in users:
        skills_u=list(database.skills.find({'user_id': u['id']}, {'_id': 0, 'name': 1, 'type': 1, 'level': 1}))
        teach=[s['name'] for s in skills_u if s['type']=='Can Teach']; learn=[s['name'] for s in skills_u if s['type']=='Want to Learn']
        matches=sorted(set(teach)&wanted); mutual=sorted(set(learn)&offered)
        hay=' '.join([u['username'],u['bio'],u['interests']]+teach+learn).lower()
        if q and q not in hay: continue
        if category and not any(category.lower() in x.lower() for x in teach+learn): continue
        score=len(matches)*30+len(mutual)*20
        results.append({'id':u['id'],'username':u['username'],'bio':u['bio'],'teach':teach,'learn':learn,'matches':matches,'mutual':mutual,'score':score})
    results.sort(key=lambda x:(-x['score'],x['username']))
    return render_template('discover.html',results=results,q=q,category=category)

@app.route('/connect/<int:partner_id>', methods=['POST'])
def connect(partner_id):
    if not login_required(): return redirect(url_for('login'))
    if partner_id==current_user_id(): return redirect(url_for('discover'))
    if not db().users.find_one({'id': partner_id}, {'_id': 1}):
        flash('Choose an existing researcher.','danger')
        return redirect(request.referrer or url_for('discover'))
    try:
        insert_document('connections', {'user_id': current_user_id(), 'partner_id': partner_id,
            'status': 'Requested', 'created_at': datetime.now().isoformat(timespec='seconds')})
        flash('Learning connection requested.','success')
    except DuplicateKeyError:
        flash('Connection already exists.','info')
    return redirect(request.referrer or url_for('discover'))

@app.route('/goals', methods=['GET','POST'])
def goals():
    if not login_required(): return redirect(url_for('login'))
    database=db(); uid=current_user_id()
    if request.method=='POST':
        insert_document('goals', {'user_id': uid, 'title': request.form['title'], 'description': request.form.get('description',''),
            'target_date': request.form.get('target_date',''), 'progress': 0, 'status': 'Active',
            'created_at': datetime.now().isoformat(timespec='seconds')})
        flash('Learning goal created.','success')
        return redirect(url_for('goals'))
    rows=list(database.goals.find({'user_id': uid}, {'_id': 0}).sort('id', -1))
    return render_template('goals.html',goals=rows)

@app.route('/goals/<int:gid>/progress', methods=['POST'])
def goal_progress(gid):
    if not login_required(): return redirect(url_for('login'))
    try: p=max(0,min(100,int(request.form['progress'])))
    except: p=0
    status='Completed' if p>=100 else 'Active'
    db().goals.update_one({'id': gid, 'user_id': current_user_id()}, {'$set': {'progress': p, 'status': status}})
    return redirect(url_for('goals'))

@app.route('/activities', methods=['GET','POST'])
def activities():
    if not login_required(): return redirect(url_for('login'))
    database=db(); uid=current_user_id()
    if request.method=='POST':
        insert_document('activities', {'user_id': uid, 'title': request.form['title'],
            'minutes': int(request.form.get('minutes',30)), 'activity_date': request.form.get('activity_date') or date.today().isoformat(),
            'notes': request.form.get('notes','')})
        flash('Learning activity recorded.','success')
        return redirect(url_for('activities'))
    rows=list(database.activities.find({'user_id': uid}, {'_id': 0}).sort([('activity_date', -1), ('id', -1)]))
    return render_template('activities.html',activities=rows)

@app.route('/analytics')
def analytics():
    if not login_required(): return redirect(url_for('login'))
    database=db(); uid=current_user_id()
    activity_rows=list(database.activities.find({'user_id': uid}, {'_id': 0, 'minutes': 1, 'activity_date': 1}))
    totals={'mins': sum(row.get('minutes', 0) for row in activity_rows), 'sessions': len(activity_rows)}
    completed=database.goals.count_documents({'user_id': uid, 'status': 'Completed'})
    active=database.goals.count_documents({'user_id': uid, 'status': 'Active'})
    daily_totals={}
    for activity in activity_rows:
        activity_date=activity['activity_date']
        daily_totals[activity_date]=daily_totals.get(activity_date, 0)+activity.get('minutes', 0)
    daily=[{'activity_date': activity_date, 'mins': minutes} for activity_date, minutes in
        sorted(daily_totals.items(), reverse=True)[:14]]
    skill_counts={}
    for skill in database.skills.find({'user_id': uid}, {'type': 1}):
        skill_counts[skill['type']]=skill_counts.get(skill['type'], 0)+1
    skills=[{'type': skill_type, 'c': count} for skill_type, count in skill_counts.items()]
    return render_template('analytics.html',totals=totals,completed=completed,active=active,daily=list(reversed(daily)),skills=skills)

@app.route('/export')
def export():
    if not login_required(): return redirect(url_for('login'))
    uid=current_user_id(); out=io.StringIO(); w=csv.writer(out); w.writerow(['Learning Record','Date','Minutes','Notes'])
    for record in db().activities.find({'user_id': uid}, {'_id': 0}).sort('activity_date', -1):
        w.writerow([record['title'],record['activity_date'],record['minutes'],record['notes']])
    return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=learning_report.csv'})

@app.route('/api/summary')
def api_summary():
    if not login_required(): return jsonify({'error':'unauthorized'}),401
    activities=list(db().activities.find({'user_id': current_user_id()}, {'_id': 0, 'minutes': 1}))
    return jsonify({'sessions': len(activities), 'minutes': sum(item.get('minutes', 0) for item in activities)})

@app.route('/health')
def health(): return jsonify({'status':'ok','service':'Research Lab Operations'})

if __name__=='__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1')
    app.run(debug=False, host=host, port=port)