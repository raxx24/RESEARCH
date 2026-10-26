# Fieldnote — Research Lab Operations

A full-stack Flask application for coordinating institutional research workflows: experiment scheduling, detector data tracking, researcher collaboration, and shared equipment utilization.

## Features
- Researcher registration and session-based sign-in
- Responsive operations dashboard with experiment, dataset, and utilization metrics
- Instrument-aware experiment booking with overlapping reservation checks
- Detector dataset records attached to experiments
- Equipment availability, maintenance status, and utilization monitoring
- Researcher invitations to shared experiments
- MongoDB persistence with demo records seeded on first launch
- Health endpoint at `/health`

## Demo access
- Username: `ram`
- Password: `1234`
- Other demo users: `ananya`, `arjun`, and `meena` (password `1234`)

## Run locally on Windows
1. Install Python 3.10 or later.
2. Make sure MongoDB is running locally, or create a MongoDB Atlas cluster.
3. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
4. Install the dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Configure the MongoDB connection and database name if needed:
   ```powershell
   $env:MONGODB_URI = 'mongodb://localhost:27017'
   $env:MONGODB_DATABASE = 'fieldnote'
   ```
   `MONGODB_URI` defaults to `mongodb://localhost:27017`; `MONGODB_DATABASE` defaults to `fieldnote`.
6. Start the Flask application:
   ```powershell
   python app.py
   ```
7. Open `http://127.0.0.1:5000`.

MongoDB collections and indexes are initialized on startup. Demo records are added when the database has no users. Existing `fieldnote.db` SQLite data is not imported automatically.

## Deploy to Render
1. Push this project to GitHub.
2. Create a new Web Service on Render.
3. Connect the repository.
4. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add environment variables:
   - `SECRET_KEY` = a strong random value
   - `MONGODB_URI` = your MongoDB Atlas connection string
   - `MONGODB_DATABASE` = `fieldnote` (or your chosen database name)
   - `PORT` = `10000` (Render usually sets this automatically)

Allow the Render service to connect to your Atlas cluster using its network access settings. Keep the Atlas credentials in environment variables, not in source control.

## Suggested presentation flow
1. Open the landing page and introduce the lab coordination problem.
2. Sign in with the demo account and review the overview metrics.
3. Schedule an experiment and demonstrate the instrument conflict check.
4. Log a detector dataset and show the experiment linkage.
5. Change an equipment status and review utilization and service dates.
6. Invite another researcher to an experiment.

## Production considerations
- Replace the demo credentials and use a strong environment-provided `SECRET_KEY`.
- Use MongoDB Atlas or another managed MongoDB service for production deployments.
- Add role-based authorization, CSRF protection, audit history, and file/object storage for detector payloads before handling real research data.
