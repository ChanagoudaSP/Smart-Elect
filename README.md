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
- Python 3.8+
- MySQL
- OpenCV
- Flask
- Other dependencies (see requirements.txt)

## Setup Instructions
1. Create a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: .\env\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up MySQL database:
- Install MySQL
- Create a database named 'smart_elect'
- Run init_db.py to initialize the database schema

4. Generate security keys:
```bash
python generate_keys.py
```

5. Run the application:
```bash
python run.py
```

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