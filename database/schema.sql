-- ===================================================
-- AI-Based Fake News Detection System
-- Database Schema for MySQL (XAMPP)
-- RV College of Engineering, MCA Department
-- ===================================================

CREATE DATABASE IF NOT EXISTS fake_news_detector
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE fake_news_detector;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    is_admin TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_is_admin (is_admin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- News History Table
CREATE TABLE IF NOT EXISTS news_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    news_text TEXT NOT NULL,
    prediction VARCHAR(10) NOT NULL,
    confidence FLOAT NOT NULL,
    explanation TEXT,
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    keywords TEXT,
    suspicious_phrases TEXT,
    source_url VARCHAR(500),
    processing_time FLOAT,
    method VARCHAR(50) DEFAULT 'phi3',
    source_type VARCHAR(20) DEFAULT 'text',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_prediction (prediction),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE news_history ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) DEFAULT 'text';

-- Prediction Logs Table
CREATE TABLE IF NOT EXISTS prediction_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    news_text VARCHAR(500) NOT NULL,
    prediction VARCHAR(10) NOT NULL,
    confidence FLOAT NOT NULL,
    method VARCHAR(50) DEFAULT 'phi3',
    processing_time FLOAT,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_prediction (prediction),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Admin Logs Table
CREATE TABLE IF NOT EXISTS admin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_admin_id (admin_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Datasets Table
CREATE TABLE IF NOT EXISTS datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    total_samples INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, is_admin, is_active)
VALUES (
    'admin',
    'admin@rvce.edu.in',
    '$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1Qlq5GzGm3qZzY5Kf0VxG7y8W9Ku',
    'Admin RVCE',
    1,
    1
) ON DUPLICATE KEY UPDATE username=username;

-- Insert demo user (password: demo123)
INSERT INTO users (username, email, password_hash, full_name, is_admin, is_active)
VALUES (
    'demo',
    'demo@rvce.edu.in',
    '$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1Qlq5GzGm3qZzY5Kf0VxG7y8W9Ku',
    'Demo User',
    0,
    1
) ON DUPLICATE KEY UPDATE username=username;
