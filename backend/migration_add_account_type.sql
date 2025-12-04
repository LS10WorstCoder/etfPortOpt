-- Migration: Add account_type column to portfolios table
-- This allows tracking whether a portfolio is a taxable account or retirement account
-- Retirement accounts (Roth IRA, Traditional IRA, 401k) require whole-share optimization

-- Add account_type column with default 'taxable'
ALTER TABLE portfolios 
ADD COLUMN IF NOT EXISTS account_type VARCHAR(20) NOT NULL DEFAULT 'taxable';

-- Add check constraint to ensure valid account types
ALTER TABLE portfolios 
ADD CONSTRAINT portfolios_account_type_check 
CHECK (account_type IN ('taxable', 'roth_ira', 'traditional_ira', '401k'));

-- Create index for filtering by account type
CREATE INDEX IF NOT EXISTS idx_portfolios_account_type ON portfolios(account_type);

-- Update existing portfolios to have 'taxable' account type (already default, but explicit)
UPDATE portfolios SET account_type = 'taxable' WHERE account_type IS NULL;
