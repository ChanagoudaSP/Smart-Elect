-- Enter your password (root1)

CREATE DATABASE IF NOT EXISTS evoting_db;
-- Create a new user (more secure than using root)
CREATE USER 'smart_elect'@'localhost' IDENTIFIED BY 'vote';

-- Grant privileges to the new user
GRANT ALL PRIVILEGES ON smart_elect.* TO 'smart_elect'@'localhost';
FLUSH PRIVILEGES;

use evoting_db;

select * from user;

update user set is_verified = 1 where id = 18;
DELETE FROM user WHERE email = 'chanagoudaspatil374@gmail.com' ;

select * from candidate;
delete from election where id = 4 ;
select * from election;

ALTER TABLE vote ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE candidate ADD COLUMN photo VARCHAR(255) DEFAULT NULL;
ALTER TABLE candidate DROP COLUMN photo_url;
select * from vote;

SELECT id, email, first_name, last_name, national_id, is_admin, is_verified, created_at 
FROM user;

ALTER TABLE candidate ADD COLUMN verified BOOLEAN DEFAULT FALSE;

SELECT * FROM user WHERE is_admin = TRUE;

SELECT * FROM user WHERE is_verified = TRUE;

SELECT COUNT(*) as total_users FROM user;

-- Get all elections
SELECT id, title, description, start_date, end_date, is_active, created_at 
FROM election;

-- Get active elections
SELECT * FROM election 
WHERE is_active = TRUE 
AND start_date <= CURRENT_TIMESTAMP 
AND end_date >= CURRENT_TIMESTAMP;

-- Get upcoming elections
SELECT * FROM election 
WHERE start_date > CURRENT_TIMESTAMP;

-- Get completed elections
SELECT * FROM election 
WHERE end_date < CURRENT_TIMESTAMP;

-- Get all candidates with their election details
SELECT c.id, c.name, c.party, c.bio, e.title as election_title
FROM candidate c
JOIN election e ON c.election_id = e.id;

-- Get candidates for a specific election (replace election_id with actual ID)
SELECT * FROM candidate 
WHERE election_id = 1;

-- Get candidates with their vote counts
SELECT c.name, c.party, e.title as election_title, COUNT(v.id) as vote_count
FROM candidate c
LEFT JOIN vote v ON c.id = v.candidate_id
JOIN election e ON c.election_id = e.id
GROUP BY c.id, c.name, c.party, e.title;

-- Get all votes with related information
SELECT v.id, 
       u.email as voter_email,
       e.title as election_title,
       c.name as candidate_name,
       v.timestamp
FROM vote v
JOIN user u ON v.user_id = u.id
JOIN election e ON v.election_id = e.id
JOIN candidate c ON v.candidate_id = c.id;

-- Get vote count per election
SELECT e.title, COUNT(v.id) as total_votes
FROM election e
LEFT JOIN vote v ON e.id = v.election_id
GROUP BY e.id, e.title;

-- Check if a specific user has voted in an election
SELECT * FROM vote 
WHERE user_id = 1 AND election_id = 1;

-- Get voting statistics
SELECT 
    e.title as election_title,
    COUNT(DISTINCT v.user_id) as total_voters,
    COUNT(v.id) as total_votes
FROM election e
LEFT JOIN vote v ON e.id = v.election_id
GROUP BY e.id, e.title;

-- Get election results with percentage
SELECT 
    e.title as election_title,
    c.name as candidate_name,
    c.party,
    COUNT(v.id) as votes,
    ROUND(COUNT(v.id) * 100.0 / NULLIF(SUM(COUNT(v.id)) OVER (PARTITION BY e.id), 0), 2) as vote_percentage
FROM election e
JOIN candidate c ON e.id = c.election_id
LEFT JOIN vote v ON c.id = v.candidate_id
GROUP BY e.id, e.title, c.id, c.name, c.party;

-- Get user participation statistics
SELECT 
    e.title,
    COUNT(DISTINCT u.id) as registered_users,
    COUNT(DISTINCT v.user_id) as voters,
    ROUND(COUNT(DISTINCT v.user_id) * 100.0 / COUNT(DISTINCT u.id), 2) as participation_percentage
FROM election e
CROSS JOIN user u
LEFT JOIN vote v ON e.id = v.election_id AND u.id = v.user_id
GROUP BY e.id, e.title;

-- Get hourly voting pattern
SELECT 
    e.title,
    DATE_FORMAT(v.timestamp, '%Y-%m-%d %H:00:00') as hour,
    COUNT(*) as votes_in_hour
FROM vote v
JOIN election e ON v.election_id = e.id
GROUP BY e.id, e.title, DATE_FORMAT(v.timestamp, '%Y-%m-%d %H:00:00')
ORDER BY e.id, hour;

-- Check for multiple votes (shouldn't exist due to constraints)
SELECT user_id, election_id, COUNT(*) as vote_count
FROM vote
GROUP BY user_id, election_id
HAVING COUNT(*) > 1;

-- Check unverified users who voted
SELECT u.email, u.national_id, e.title
FROM vote v
JOIN user u ON v.user_id = u.id
JOIN election e ON v.election_id = e.id
WHERE u.is_verified = FALSE;

-- Check voting times outside election period
SELECT v.id, u.email, e.title, v.timestamp
FROM vote v
JOIN user u ON v.user_id = u.id
JOIN election e ON v.election_id = e.id
WHERE v.timestamp < e.start_date 
   OR v.timestamp > e.end_date;
   
   -- Check database size
SELECT 
    table_name,
    table_rows,
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'smart_elect'
ORDER BY size_mb DESC;

-- Check table status
SHOW TABLE STATUS FROM smart_elect;

-- Check indexes
SHOW INDEXES FROM user;
SHOW INDEXES FROM election;
SHOW INDEXES FROM candidate;
SHOW INDEXES FROM vote;