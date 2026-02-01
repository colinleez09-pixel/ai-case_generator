# Flask后端API服务

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

## 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## API接口文档

### 1. 获取案例库选项
- **URL**: `/api/case-library-options`
- **方法**: GET
- **返回**:
```json
{
  "success": true,
  "data": [
    {"value": "all", "label": "全量历史用例案例库"},
    {"value": "archived", "label": "已归档精品案例库"}
  ]
}
```

### 2. 搜索历史用例
- **URL**: `/api/search-history-cases`
- **方法**: POST
- **请求体**:
```json
{
  "caseLibrary": "all",
  "searchMethod": "keyword",
  "searchText": "账单"
}
```
- **返回**:
```json
{
  "success": true,
  "data": [...],
  "filters": {
    "caseLibrary": "all",
    "searchMethod": "keyword",
    "searchText": "账单"
  }
}
```

### 3. 获取预置数据
- **URL**: `/api/preset-data`
- **方法**: GET
- **返回**:
```json
{
  "success": true,
  "data": {
    "steps": [...],
    "components": [...]
  }
}
```

## 测试接口

### 使用curl测试

```bash
# 测试健康检查
curl http://localhost:5000/health

# 获取案例库选项
curl http://localhost:5000/api/case-library-options

# 搜索历史用例
curl -X POST http://localhost:5000/api/search-history-cases \
  -H "Content-Type: application/json" \
  -d '{"caseLibrary":"all","searchMethod":"keyword","searchText":"账单"}'

# 获取预置数据
curl http://localhost:5000/api/preset-data
```
