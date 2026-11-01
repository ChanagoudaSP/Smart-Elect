import os
import sys
from dotenv import load_dotenv
import mysql.connector
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

def create_database(cursor, db_name):
    """Create database if it doesn't exist"""
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        return True
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        return False

def setup_database():
    # Database configuration
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root1'),
        'database': os.getenv('DB_NAME', 'evoting_db')
    }
    
    try:
        # Connect to MySQL server
        print("Connecting to MySQL server...")
        conn = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        
        # Create and use database
        if not create_database(cursor, config['database']):
            return 1
        
        # Create tables
        tables = {
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    national_id VARCHAR(20) UNIQUE NOT NULL,
                    face_encoding TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'elections': """
                CREATE TABLE IF NOT EXISTS elections (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    start_date DATETIME NOT NULL,
                    end_date DATETIME NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'candidates': """
                CREATE TABLE IF NOT EXISTS candidates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    election_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    party VARCHAR(100),
                    bio TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (election_id) REFERENCES elections(id)
                )
            """,
            'votes': """
                CREATE TABLE IF NOT EXISTS votes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    election_id INT NOT NULL,
                    candidate_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (election_id) REFERENCES elections(id),
                    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
                    UNIQUE KEY unique_vote (user_id, election_id)
                )
            """
        }
        
        # Create each table
        for table_name, query in tables.items():
            print(f"Creating {table_name} table...")
            cursor.execute(query)
          # Create indexes
        indexes = [
            "CREATE INDEX idx_user_email ON users(email)",
            "CREATE INDEX idx_election_dates ON elections(start_date, end_date)",
            "CREATE INDEX idx_vote_election ON votes(election_id)"
        ]
        
        for index in indexes:
            try:
                cursor.execute(index)
            except mysql.connector.Error as err:
                # Skip if index already exists
                if err.errno == 1061:  # Error code for duplicate key name
                    continue
                else:
                    raise
        
        # Commit changes
        conn.commit()
        print("✓ Database setup completed successfully")
        return 0
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return 1
        
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    sys.exit(setup_database())