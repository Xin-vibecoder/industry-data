-- 申万行业成分股表
CREATE TABLE sw_industry_constituents (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100) NOT NULL,
    industry_level1 VARCHAR(50),  -- 申万一级行业
    industry_level2 VARCHAR(50),  -- 申万二级行业
    industry_level3 VARCHAR(50),  -- 申万三级行业
    inclusion_date DATE,          -- 纳入时间
    price DECIMAL(10, 2),         -- 价格
    pe_ratio DECIMAL(10, 2),      -- 市盈率
    pe_ttm DECIMAL(10, 2),        -- 市盈率TTM
    pb_ratio DECIMAL(10, 2),      -- 市净率
    dividend_yield DECIMAL(10, 4), -- 股息率
    market_cap DECIMAL(20, 2),    -- 市值
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(stock_code, industry_level3)
);

-- 创建索引
CREATE INDEX idx_constituents_stock ON sw_industry_constituents(stock_code);
CREATE INDEX idx_constituents_industry1 ON sw_industry_constituents(industry_level1);
CREATE INDEX idx_constituents_industry3 ON sw_industry_constituents(industry_level3);

-- 配置 RLS
ALTER TABLE sw_industry_constituents ENABLE ROW LEVEL SECURITY;

-- 允许匿名读取
CREATE POLICY "Allow anonymous read" ON sw_industry_constituents FOR SELECT USING (true);
