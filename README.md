# Smart-Elect: E-Voting System with Face Recognition

A secure electronic voting system with face recognition authentication built using Flask, OpenCV, and MySQL.

## Features
- Face Recognition Authentication
- Secure Vote Encryption
- Real-time Election Results
- Admin Dashboard
- User Registration and Management
- Multiple Election Support

## Requirements
- Python 3.10+ (tested with Python 3.13 on Windows)
- MySQL 8
- A webcam (optional, only for face enrollment)
- Other dependencies (see requirements.txt)

## Setup Instructions (Windows)
1. Create and activate a virtual environment:
```powershell
python -m venv env
.\env\Scripts\activate
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Create the MySQL database (the app creates the tables automatically):
```sql
CREATE DATABASE IF NOT EXISTS evoting_db;
```

4. Create a `.env` file in the project root:
```ini
SECRET_KEY=<random-secret>
ENCRYPTION_KEY=<fernet-key>
SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/evoting_db
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=YOUR_PASSWORD
DB_NAME=evoting_db
FLASK_APP=run.py
```

5. Create an admin account:
```powershell
python -m flask --app run.py create-admin admin@example.com "Admin@12345" Admin User ADMIN001
```

6. Run the application from the project root:
```powershell
python run.py
```

Open http://127.0.0.1:5000.

Notes:
- `generate_keys.py` can create the `SECRET_KEY` and `ENCRYPTION_KEY` values, but it does not write `SQLALCHEMY_DATABASE_URI`; add that line manually.
- Announcement emails are suppressed by default on a dev machine (`MAIL_SUPPRESS_SEND`). Configure `MAIL_USERNAME`/`MAIL_PASSWORD` and set `MAIL_SUPPRESS_SEND=false` to send them.
- Registration tries to capture a face from the machine's webcam; if no camera is available, registration still completes.
- `setup_database.py` is a legacy script and is not required by the app.

## Project Structure
```
smart-elect/
├── app/
│   ├── models/
│   ├── routes/
│   ├── static/
│   ├── templates/
│   └── utils/
├── requirements.txt
├── run.py
└── README.md
```

## Security Features
- Face recognition for voter verification
- End-to-end vote encryption
- Secure session management
- Protection against common web vulnerabilities

## License
MIT License 