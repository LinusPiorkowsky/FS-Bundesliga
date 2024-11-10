-- Drop the users table if it exists
DROP TABLE IF EXISTS users;

-- Create the users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);
