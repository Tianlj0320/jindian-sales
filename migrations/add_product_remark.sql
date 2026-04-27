-- Migration: Add remark column to products table
-- Date: 2026-04-27
-- Description: Added remark field to Product model for product notes

ALTER TABLE products ADD COLUMN remark VARCHAR(500) DEFAULT '';
