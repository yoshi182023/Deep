# Email RAG - 数据库配置指南

## 📋 概述

本项目使用 **Neon PostgreSQL** + **pgvector** 扩展来存储邮件和向量嵌入。

## 🚀 快速开始

### 1. 获取 Neon 连接字符串

#### 第一步：创建 Neon 账户
- 访问 [https://console.neon.tech/](https://console.neon.tech/)
- 使用 GitHub/Google 账号注册（免费）
- 创建新项目

#### 第二步：获取连接字符串
1. 在 Neon 控制台中，点击你的项目
2. 在 "Connection strings" 部分
3. 选择 **PostgreSQL** 选项卡
4. 复制完整的连接字符串，格式如下：
```
postgresql://neondb_owner:your_password@ep-your-project.us-east-1.neon.tech/neondb?sslmode=require
```

### 2. 配置本地 .env 文件

创建 `/workspaces/Deep/.env`：

```bash
NEON_PG_CONNECTION_URL=postgresql://neondb_owner:your_password@ep-your-project.us-east-1.neon.tech/neondb?sslmode=require
```

**⚠️ 重要：** 
- 不要提交 `.env` 文件到 Git（已在 .gitignore 中）
- 请妥善保管你的密码

### 3. 在 Notebook 中执行

打开 `email_parser.ipynb`，依次执行单元格：

1. **第一部分**：邮件解析（已完成）
2. **第二部分**：向量嵌入（已完成）
3. **第三部分**：数据库存储
   - 单元格：设置数据库连接
   - 单元格：创建 pgvector 扩展和表
   - 单元格：插入数据
   - 单元格：验证数据

### 4. 验证连接

运行以下命令测试连接：

```bash
cd /workspaces/Deep
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('NEON_PG_CONNECTION_URL'))"
```

## 📊 数据库结构

表名：`emails_rag`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| email_id | TEXT | 唯一 ID（email_0, email_1 等） |
| sender | TEXT | 发件人地址 |
| email_date | VARCHAR(10) | 日期 (MM-DD 格式) |
| subject | TEXT | 邮件主题 |
| body | TEXT | 邮件正文 |
| signature | TEXT | 署名块 |
| person_name | TEXT | 联系人姓名 |
| company | TEXT | 公司名称 |
| job_title | TEXT | 职位 |
| contact_info | TEXT | 联系方式 |
| embedding | VECTOR(384) | pgvector 向量嵌入 |

## 🔍 测试查询

连接到数据库后，可以运行以下 SQL 查询：

```sql
-- 查看表统计
SELECT COUNT(*) FROM emails_rag;

-- 查看样本数据
SELECT email_id, subject, company, person_name 
FROM emails_rag LIMIT 5;

-- 查询特定公司的邮件
SELECT * FROM emails_rag 
WHERE company ILIKE '%Amazon%' 
LIMIT 10;
```

## 📝 费用

Neon 提供免费层级：
- **存储**: 3 GB
- **计算**: 0.5 vCPU（共享）
- **连接**: 无限制

对于 172 封邮件 + 嵌入向量，完全在免费层范围内。

## 🛠️ 故障排除

### 连接失败

**错误**: `Cannot connect to Neon PostgreSQL`

**解决方案**:
1. 确保 `.env` 文件存在且包含正确的连接字符串
2. 确认连接字符串未过期（有时 Neon 会重置）
3. 检查网络连接
4. 验证密码中没有特殊字符需要 URL 编码

### pgvector 扩展错误

**错误**: `extension "vector" does not exist`

**解决方案**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 表已存在

**错误**: `relation "emails_rag" already exists`

**解决方案**: 
- Notebook 会自动 DROP 表并重建
- 或手动运行: `DROP TABLE IF EXISTS emails_rag;`

## 📚 相关文档

- Neon 官方文档: [https://neon.tech/docs](https://neon.tech/docs)
- pgvector GitHub: [https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
- PostgreSQL 文档: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)

## ✅ 完成检查清单

- [ ] 创建 Neon 账户
- [ ] 获取连接字符串
- [ ] 配置 `.env` 文件
- [ ] 运行 Notebook（第一、二、三部分）
- [ ] 验证数据已插入
- [ ] 测试 SQL 查询
