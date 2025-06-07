-- Create charts table
CREATE TABLE charts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL, -- Supabase user ID from payload
    title VARCHAR(255),
    type VARCHAR(50), -- e.g. "line", "bar"
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_history table
CREATE TABLE chat_history (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL, -- Supabase user ID from payload
    message TEXT,
    response TEXT,
    has_chart BOOLEAN DEFAULT FALSE,
    chart_id UUID REFERENCES charts(id) ON DELETE SET NULL, -- Optional: Chart returned in this message
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create transactions table
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL, -- Supabase user ID from payload
    symbol VARCHAR(20),
    date_time TIMESTAMP,
    quantity FLOAT,
    trade_price FLOAT,
    close_price FLOAT,
    proceeds FLOAT,
    commission_fee FLOAT,
    basis FLOAT,
    realized_p_l FLOAT,
    mtm_p_l FLOAT,
    code VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX idx_chat_history_created_at ON chat_history(created_at);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);
CREATE INDEX idx_transactions_date_time ON transactions(date_time);
CREATE INDEX idx_charts_user_id ON charts(user_id);
