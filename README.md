# 🚀 Travel Da Nang - Backend API Server

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-0.108.0+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-blue?style=for-the-badge)
![Digital Ocean](https://img.shields.io/badge/Digital_Ocean-Deployed-0080FF?style=for-the-badge&logo=digitalocean&logoColor=white)

**Backend API Server** cho ứng dụng du lịch Đà Nẵng với tính năng AI nhận diện địa điểm, tìm kiếm ngữ nghĩa (Semantic Search), RAG Chatbot, và hệ thống thanh toán PayOS.

[Tính năng](#-tính-năng-chính) • [Cài đặt](#-hướng-dẫn-cài-đặt) • [API Docs](#-api-documentation) • [Deployment](#-deployment)

</div>

---

## 📋 Tổng quan

**Travel Da Nang Backend** là API server được xây dựng trên FastAPI, cung cấp các dịch vụ:

- 🔍 **Semantic Search** - Tìm kiếm ngữ nghĩa với OpenAI Embeddings + FAISS
- 🤖 **RAG Chatbot** - Trợ lý du lịch AI với GPT-4o-mini và context từ database
- �� **AI Detection** - Nhận diện địa điểm/hiện vật qua hình ảnh (Google Lens + OpenAI Vision)
- 💰 **Payment Integration** - Tích hợp PayOS cho thanh toán/donate
- 📊 **Recommendations** - Gợi ý địa điểm cá nhân hóa dựa trên user preferences
- 🧠 **User Memory** - Lưu trữ sở thích người dùng để cá nhân hóa trải nghiệm

---

## ✨ Tính năng chính

### 🔍 Semantic Search (Tìm kiếm ngữ nghĩa)
- Sử dụng OpenAI `text-embedding-3-small` để tạo embeddings
- FAISS vector index cho tìm kiếm similarity nhanh chóng
- Hỗ trợ tìm kiếm đa entity: locations, festivals, items
- Score filtering với ngưỡng tùy chỉnh (default: 0.5)

### 🤖 RAG Chatbot
- GPT-4o-mini với context từ semantic search
- Conversation history management
- User memory integration cho personalization
- Suggested actions dựa trên context

### 📸 AI Image Detection
- Upload ảnh → Google Lens API → OpenAI Vision
- Nhận diện địa điểm du lịch và hiện vật lịch sử
- Trả về tên và mô tả chi tiết (Markdown format)
- Fallback data từ NocoDB khi có sẵn

### 💰 Payment System
- PayOS integration cho thanh toán QR
- Webhook handler cho payment confirmation
- Transaction logging vào NocoDB
- Auto-update user balance

### 📊 Personalized Recommendations
- Vector similarity-based recommendations
- User preference learning từ interactions
- Memory types: preference, interest, visited, dislike

---

## 🛠️ Công nghệ sử dụng

| Category | Technology | Version |
|----------|------------|---------|
| **Framework** | FastAPI | 0.108.0+ |
| **Server** | Uvicorn / Gunicorn | 0.25.0+ / 20.1.0+ |
| **AI/ML** | OpenAI API | 1.51.0+ |
| **Vector Search** | FAISS | Latest |
| **Database** | NocoDB (Cloud) | - |
| **Storage** | Firebase Storage | 6.5.0+ |
| **Payment** | PayOS | - |
| **Search** | SerpAPI (Google Lens) | 0.1.5+ |
| **Validation** | Pydantic | 2.0.0+ |

---

## 📋 Yêu cầu hệ thống

### Prerequisites
- **Python** >= 3.8
- **pip** >= 21.x
- **Git**
- **Virtual Environment** (venv, virtualenv, hoặc conda)

### External Services (cần đăng ký)
- **OpenAI Account** - API key cho embeddings và chat
- **NocoDB Account** - Database hosting
- **PayOS Account** - Payment gateway (optional)
- **Firebase Project** - Storage (optional)
- **SerpAPI Account** - Google Lens API (optional)

---

## 🚀 Hướng dẫn cài đặt

### Bước 1: Clone Repository

```bash
git clone <repository-url> freelance-travel-app-server
cd freelance-travel-app-server
```

### Bước 2: Tạo Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 4: Cấu hình Environment Variables

Tạo file `.env` trong thư mục root:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# NocoDB Configuration
NOCODB_BASE_URL=https://app.nocodb.com
NOCODB_API_TOKEN=your-nocodb-api-token
NOCODB_LOCATIONS_TABLE_ID=mfz84cb0t9a84jt
NOCODB_ITEMS_TABLE_ID=m0s4uwjesun4rl9
NOCODB_FESTIVALS_TABLE_ID=mktzgff8mpu2c32

# PayOS Configuration (optional)
PAYOS_CLIENT_ID=your-payos-client-id
PAYOS_API_KEY=your-payos-api-key
PAYOS_CHECKSUM_KEY=your-payos-checksum-key

# Server Configuration
PUBLIC_BASE_URL=http://localhost:8080

# Search API (optional)
SERPAPI_KEY=your-serpapi-key

# Firebase (optional)
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_STORAGE_BUCKET=your-bucket.appspot.com

# FAISS Index Directory
FAISS_INDEX_DIR=./faiss_indexes
```

### Bước 5: Chạy Server

```bash
# Development mode (auto-reload)
uvicorn app:app --reload --host 0.0.0.0 --port 8080

# Production mode
gunicorn -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 app:app
```

### Bước 6: Kiểm tra

- **Health Check**: http://localhost:8080/
- **API Docs (Swagger)**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

---

## 📂 Cấu trúc dự án

```
freelance-travel-app-server/
├── app.py                      # Main FastAPI application
├── main.py                     # Uvicorn entry point
├── service.py                  # AI detection service (Google Lens + OpenAI)
├── nocodb_service.py           # NocoDB database integration
├── payment_service.py          # PayOS payment integration
├── data.py                     # Fallback data for offline mode
├── firestore.py                # Firebase integration
├── requirements.txt            # Python dependencies
├── Procfile                    # Digital Ocean deployment config
├── .env                        # Environment variables (không commit)
├── .gitignore                  # Git ignore rules
├── privateKey.json             # Firebase credentials (không commit)
│
├── routers/                    # API route handlers
│   ├── __init__.py
│   ├── search.py               # Semantic search endpoints
│   ├── chat.py                 # RAG chatbot endpoints
│   ├── memory.py               # User memory endpoints
│   └── recommendations.py      # Recommendations endpoints
│
├── services/                   # Business logic services
│   ├── __init__.py
│   ├── embedding_service.py    # OpenAI embeddings
│   ├── faiss_service.py        # FAISS vector index
│   ├── rag_service.py          # RAG pipeline
│   └── memory_service.py       # User memory management
│
├── models/                     # Pydantic models
│   ├── __init__.py
│   ├── search.py               # Search request/response models
│   ├── chat.py                 # Chat models
│   └── memory.py               # Memory models
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   └── startup_indexer.py      # FAISS index builder on startup
│
├── scripts/                    # Utility scripts
│   ├── index_data.py           # Manual index building
│   ├── get_table_ids.py        # NocoDB table ID helper
│   └── setup_nocodb_tables.py  # Database setup
│
├── faiss_indexes/              # FAISS index files (auto-generated)
│   ├── text_index.faiss
│   ├── text_id_map.json
│   ├── image_index.faiss
│   └── image_id_map.json
│
└── .do/                        # Digital Ocean config
    └── deploy.template.yaml
```

---

## 📡 API Documentation

### Base URL
- **Local**: `http://localhost:8080`
- **Production**: `https://digital-ocean-fast-api-h9zys.ondigitalocean.app`

### Core Endpoints

#### Health Check
```http
GET /
```
**Response:**
```json
{
  "message": "Hello World",
  "version": "2.0.0",
  "features": ["semantic-search", "rag-chat", "recommendations"]
}
```

#### AI Image Detection
```http
POST /detect
Content-Type: multipart/form-data
```
**Request:** `image_file` (JPEG, PNG)

**Response:**
```json
{
  "name": "Đài thờ Trà Kiệu",
  "description": "# Đài thờ Trà Kiệu\n\nĐài thờ Trà Kiệu là một di tích..."
}
```

---

### Semantic Search API (`/api/v1/search`)

#### Semantic Search
```http
POST /api/v1/search/semantic
Content-Type: application/json
```
**Request:**
```json
{
  "query": "bãi biển đẹp ở Đà Nẵng",
  "entity_types": ["location", "festival"],
  "top_k": 10,
  "min_score": 0.5
}
```
**Response:**
```json
{
  "success": true,
  "query": "bãi biển đẹp ở Đà Nẵng",
  "results": [
    {
      "id": 5,
      "entity_type": "location",
      "title": "Bãi biển Mỹ Khê",
      "description": "Bãi biển đẹp nhất Đà Nẵng...",
      "score": 0.78,
      "metadata": { "image_url": "...", "location": "Đà Nẵng" }
    }
  ],
  "total_count": 8,
  "search_time_ms": 145.5,
  "search_type": "text"
}
```

#### Search Suggestions
```http
GET /api/v1/search/suggestions?query=bãi biển&limit=5
```

---

### RAG Chat API (`/api/v1/chat`)

#### Send Message
```http
POST /api/v1/chat/rag
Content-Type: application/json
```
**Request:**
```json
{
  "message": "Gợi ý địa điểm du lịch ở Đà Nẵng",
  "user_id": 123,
  "session_id": "session_abc123",
  "include_sources": true
}
```
**Response:**
```json
{
  "success": true,
  "message": "Đà Nẵng có nhiều địa điểm du lịch hấp dẫn...",
  "sources": [
    {
      "entity_id": 5,
      "entity_type": "location",
      "title": "Bãi biển Mỹ Khê",
      "relevance_score": 0.85
    }
  ],
  "suggested_actions": [
    {
      "action_type": "navigate",
      "label": "View Bãi biển Mỹ Khê",
      "payload": { "screen": "LocationDetail", "id": 5 }
    }
  ],
  "session_id": "session_abc123",
  "tokens_used": 450,
  "response_time_ms": 1250
}
```

#### Clear Session
```http
POST /api/v1/chat/clear-session?session_id=session_abc123
```

---

### Recommendations API (`/api/v1`)

#### Get Similar Items
```http
GET /api/v1/similar/{entity_type}/{entity_id}?limit=5
```
**Example:** `GET /api/v1/similar/location/5?limit=5`

**Response:**
```json
{
  "success": true,
  "entity_type": "location",
  "entity_id": 5,
  "similar_items": [
    {
      "entity_type": "location",
      "entity_id": 12,
      "name": "Bãi biển Non Nước",
      "similarity_score": 0.82,
      "description": "...",
      "image_url": "..."
    }
  ]
}
```

#### Get Personalized Recommendations
```http
GET /api/v1/recommendations/{user_id}?limit=10
```
**Response:**
```json
{
  "success": true,
  "user_id": 123,
  "recommendations": [
    {
      "entity_type": "location",
      "entity_id": 8,
      "name": "Bà Nà Hills",
      "reason": "Based on your preferences",
      "score": 0.85,
      "description": "...",
      "images": ["..."]
    }
  ]
}
```

---

### User Memory API (`/api/v1/memory`)

#### Store Memory
```http
POST /api/v1/memory/store
Content-Type: application/json
```
**Request:**
```json
{
  "user_id": 123,
  "memory_type": "preference",
  "content": "User prefers beach destinations",
  "confidence": 0.9
}
```
**Memory Types:** `preference`, `interest`, `visited`, `dislike`, `context`

#### Get User Memories
```http
GET /api/v1/memory/user/{user_id}?memory_type=preference&limit=10
```

#### Get Conversation History
```http
GET /api/v1/memory/conversation/{session_id}?limit=20
```

---

### Payment API

#### Create Payment Link
```http
POST /payments/create
Content-Type: application/json
```
**Request:**
```json
{
  "amount": 50000,
  "userId": 123,
  "description": "Donation from user 123"
}
```
**Response:**
```json
{
  "orderCode": 1234567890,
  "paymentLinkId": "abc123xyz",
  "qrCode": "data:image/png;base64,...",
  "checkoutUrl": "https://pay.payos.vn/web/abc123xyz"
}
```

#### Get Payment Status
```http
GET /payments/status/{order_code}
```

#### PayOS Webhook
```http
POST /webhook/payos
```
Được gọi tự động bởi PayOS khi thanh toán hoàn tất.

---

## 📜 Scripts có sẵn

| Script | Mô tả |
|--------|-------|
| `uvicorn app:app --reload` | Chạy development server |
| `gunicorn -w 2 -k uvicorn.workers.UvicornWorker app:app` | Chạy production server |
| `python scripts/index_data.py` | Build FAISS indexes thủ công |
| `python scripts/get_table_ids.py` | Lấy NocoDB table IDs |

---

## 🚢 Deployment

### Digital Ocean App Platform

#### Bước 1: Tạo App
1. Đăng nhập https://cloud.digitalocean.com/
2. Create → Apps → Deploy from GitHub
3. Chọn repository và branch `main`

#### Bước 2: Cấu hình Environment Variables
Trong App Settings → Environment Variables:
```
OPENAI_API_KEY=sk-your-key
NOCODB_BASE_URL=https://app.nocodb.com
NOCODB_API_TOKEN=your-token
NOCODB_LOCATIONS_TABLE_ID=mfz84cb0t9a84jt
PAYOS_CLIENT_ID=your-client-id
PAYOS_API_KEY=your-api-key
PAYOS_CHECKSUM_KEY=your-checksum-key
PUBLIC_BASE_URL=https://your-app.ondigitalocean.app
SERPAPI_KEY=your-serpapi-key
```

#### Bước 3: Deploy
App sẽ tự động build và deploy khi push code lên GitHub.

---

## 🔧 Troubleshooting

### Lỗi thường gặp

#### 1. FAISS Index Empty
**Triệu chứng:** Semantic search trả về 0 results
**Giải pháp:**
```bash
# Rebuild indexes
python scripts/index_data.py
```

#### 2. OpenAI API Error 401
**Triệu chứng:** "Invalid API key"
**Giải pháp:** Kiểm tra `OPENAI_API_KEY` trong `.env`

#### 3. NocoDB Connection Failed
**Triệu chứng:** "Failed to fetch data from NocoDB"
**Giải pháp:**
- Kiểm tra `NOCODB_API_TOKEN`
- Kiểm tra table IDs
- Verify NocoDB service status

#### 4. PayOS Webhook Not Working
**Triệu chứng:** Payment không update balance
**Giải pháp:**
- Kiểm tra webhook URL trong PayOS dashboard
- Verify `PUBLIC_BASE_URL` environment variable
- Check server logs cho webhook errors

---

## 📚 Tài liệu tham khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [FAISS Documentation](https://faiss.ai/)
- [NocoDB Documentation](https://docs.nocodb.com/)
- [PayOS Documentation](https://payos.vn/docs/)
- [Digital Ocean App Platform](https://docs.digitalocean.com/products/app-platform/)

---

## 📄 License

Dự án này là **private repository**. Mọi quyền được bảo lưu.

---

## 👥 Liên hệ

Nếu có câu hỏi hoặc cần hỗ trợ, vui lòng liên hệ qua:
- **Email**: [lekhanhdat03@gmail.com]
- **GitHub Issues**: Tạo issue trong repository

---

<div align="center">

**Made with ❤️ for Da Nang Tourism**

</div>
