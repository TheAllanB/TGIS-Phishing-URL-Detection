-- Run this once to set up the local PostgreSQL database.
-- Usage: psql -U postgres -p 5432 -f scripts/setup_db.sql

CREATE USER phishing_user WITH PASSWORD 'secure_password';
CREATE DATABASE phishing_db OWNER phishing_user;
GRANT ALL PRIVILEGES ON DATABASE phishing_db TO phishing_user;
