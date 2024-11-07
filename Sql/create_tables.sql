-- Drop existing tables if they exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS games;

-- Create the users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);