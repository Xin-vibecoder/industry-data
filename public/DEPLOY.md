# 部署说明

## 一、下载项目文件

- **完整项目（含数据库）**: [industry-data-full.tar.gz](/industry-data-full.tar.gz) (~9MB)
- **仅项目代码**: [industry-data-project.tar.gz](/industry-data-project.tar.gz) (~226KB)
- **数据库导出**: [db_export.tar.gz](/db_export.tar.gz) (~4.3MB)

## 二、在扣子编程中创建新项目

1. 登录扣子编程平台
2. 点击「新建项目」
3. 选择「Next.js」模板
4. 等待项目初始化完成

## 三、上传项目文件

### 方法一：逐个文件上传（推荐）

1. 解压下载的 `industry-data-project.tar.gz` 文件
2. 在扣子编程的文件管理器中，按照原有目录结构上传文件：
   - 覆盖根目录下的 `package.json`、`next.config.ts` 等配置文件
   - 上传 `src/` 目录下的所有源码文件
   - 上传 `server/` 目录下的 Python 脚本
   - 上传 `.github/` 目录下的 GitHub Actions 配置

### 方法二：压缩包上传（如果支持）

如果扣子编程支持压缩包上传，直接上传解压即可。

## 四、配置环境变量

在扣子编程的「环境变量」设置中添加：

```
SUPABASE_URL=你的Supabase项目URL
SUPABASE_ANON_KEY=你的Supabase匿名密钥
```

### 获取 Supabase 凭证

1. 登录 [Supabase Dashboard](https://supabase.com/dashboard)
2. 选择你的项目
3. 进入 Settings > API
4. 复制 `URL` 和 `anon public` 密钥

## 五、创建数据库表

在 Supabase 的 SQL Editor 中执行以下 SQL：

```sql
-- 行业板块表
CREATE TABLE industry_sectors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 行业每日数据表
CREATE TABLE industry_daily_data (
    id SERIAL PRIMARY KEY,
    sector_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(10, 3),
    high_price DECIMAL(10, 3),
    low_price DECIMAL(10, 3),
    close_price DECIMAL(10, 3),
    volume BIGINT,
    amount DECIMAL(20, 2),
    change_pct DECIMAL(10, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(sector_code, trade_date)
);

-- 行业排名表
CREATE TABLE industry_rankings (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    sector_code VARCHAR(20) NOT NULL,
    sector_name VARCHAR(100) NOT NULL,
    close_price DECIMAL(10, 3),
    change_pct DECIMAL(10, 4),
    volume BIGINT,
    amount DECIMAL(20, 2),
    rank_today INT,
    rank_change INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(trade_date, sector_code)
);

-- 创建索引
CREATE INDEX idx_daily_data_date ON industry_daily_data(trade_date);
CREATE INDEX idx_daily_data_sector ON industry_daily_data(sector_code);
CREATE INDEX idx_rankings_date ON industry_rankings(trade_date);
```

## 六、安装依赖并运行

1. 在扣子编程的终端中执行：
   ```bash
   pnpm install
   ```

2. 点击「运行」按钮启动项目

## 七、导入数据（推荐）

如果你使用导出的数据库文件，可以直接导入：

1. 解压 `db_export.tar.gz` 到 `public/` 目录
2. 在终端中执行：
   ```bash
   python3 public/import_data.py
   ```

这将导入：
- 90 个行业板块
- 48,240 条每日数据（从 2024年1月 至今）
- 48,240 条排名数据

## 八、初始化数据（备选）

如果需要从零开始获取数据：

1. 在终端中执行：
   ```bash
   python3 server/fetch_industry_data.py
   ```

2. 等待数据获取完成（约需 5-10 分钟）

3. 计算排名：
   ```bash
   python3 server/calculate_rankings.py
   ```

## 九、配置自动更新（可选）

如果要使用 GitHub Actions 自动更新：

1. 将项目推送到 GitHub 仓库
2. 在仓库的 Settings > Secrets 中添加：
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
3. 启用 GitHub Actions

## 项目结构

```
├── src/                    # 前端源码
│   ├── app/               # Next.js App Router
│   ├── components/        # React 组件
│   └── lib/               # 工具函数
├── server/                # Python 后端脚本
│   ├── fetch_industry_data.py      # 获取历史数据
│   ├── calculate_rankings.py       # 计算排名
│   └── auto_update_data.py         # 自动更新
├── .github/               # GitHub Actions 配置
└── public/                # 静态资源
```

## 常见问题

### Q: 数据获取失败怎么办？
A: 检查网络连接，AKShare 需要访问东方财富网站。

### Q: Supabase 连接失败？
A: 确认环境变量配置正确，检查 Supabase 项目是否正常运行。

### Q: 页面显示空白？
A: 检查数据库中是否有数据，如果没有请先执行数据初始化。
