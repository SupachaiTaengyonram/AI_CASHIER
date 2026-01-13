# AI CASHIER

A comprehensive AI-powered point-of-sale (POS) and cashier management system built with Django, featuring intelligent product recommendations, voice command support, and seamless payment processing.

**Project Owner:** Mr. Supachai Taengyonram  
**Project Type:** Senior Project  
**Status:** Active Development

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Docker Deployment](#docker-deployment)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🎯 Overview

**AI CASHIER** is an intelligent point-of-sale system that leverages artificial intelligence to enhance the cashier experience and business operations. The system integrates modern AI technologies including Google Generative AI (Gemini), Retrieval-Augmented Generation (RAG), and voice recognition to provide:

- Intelligent product recommendations powered by AI
- Natural language product search and queries
- Voice command support for hands-free operations
- Automated customer management
- Advanced analytics and reporting
- Seamless payment processing with Stripe integration
- Multilingual support with advanced NLP capabilities

The system is designed for retail businesses seeking to modernize their POS infrastructure with AI-driven insights and improved operational efficiency.

---

## ✨ Key Features

### 🤖 AI & Intelligent Features
- **AI-Powered Product Recommendations**: Provides intelligent suggestions based on customer history and preferences using LangChain
- **Natural Language Processing**: Query products using conversational language instead of traditional searches
- **RAG (Retrieval-Augmented Generation)**: Advanced document retrieval with LangGraph for complex reasoning chains
- **Multi-Model AI Support**: Supports both Google Gemini API and local LLM fallbacks
- **Voice Commands**: Full voice command support for hands-free cashier operations with multilingual support
- **Intelligent Analytics**: AI-driven sales analytics and customer behavior insights with ML algorithms
- **Multilingual Support**: Built-in support for Thai, English and multiple languages using sentence-transformers
- **Graph-Based AI Chains**: LangGraph integration for complex multi-step AI workflows
- **LLM Monitoring & Tracing**: LangSmith integration for debugging and optimizing AI chains

### 💳 Payment & Transactions
- **Stripe Integration**: Secure payment processing with Stripe payment gateway
- **Webhook Support**: Real-time payment notifications and verification
- **Multiple Payment Methods**: Support for credit cards, digital wallets, and more
- **Order Management**: Complete order tracking and management system
- **Order History**: Comprehensive order logging and retrieval
- **Transaction Security**: PCI-compliant payment handling

### 👥 Customer Management
- **Customer Profiles**: Detailed customer information and purchase history
- **Loyalty Tracking**: Monitor customer spending and loyalty metrics
- **Role-Based Access Control**: Staff and customer role differentiation with granular permissions
- **Customer Analytics**: Track customer behavior and preferences using ML
- **Customer Segmentation**: Automatic customer grouping based on behavior

### 📦 Inventory & Products
- **Product Management**: Add, update, and delete products with rich data
- **Category Organization**: Organize products by hierarchical categories
- **QR Code Generation**: Generate QR codes (segno + qrcode) for quick product identification
- **Stock Tracking**: Real-time inventory management
- **Product Recommendations**: AI-powered product discovery

### 🎁 Promotions & Offers
- **Promotion Management**: Create and manage promotional campaigns
- **Discount Application**: Automated discount calculation and application
- **Seasonal Offers**: Time-based promotion scheduling
- **Dynamic Pricing**: AI-suggested pricing strategies

### 📊 Dashboard & Analytics
- **Sales Analytics**: Real-time sales metrics and trends with advanced visualization
- **Customer Analytics**: Customer count, average transaction value, and behavior trends
- **Performance Reporting**: Comprehensive business performance dashboards
- **Export Functionality**: Export data to multiple formats
- **Data Visualization**: Rich charts and graphs using advanced libraries

### 📡 Advanced Features
- **Async Processing**: Uvicorn + Uvloop for high-performance async request handling
- **Real-time Updates**: WebSocket support for live data updates
- **Distributed Tracing**: OpenTelemetry integration for observability
- **Analytics & Monitoring**: PostHog integration for user behavior analytics
- **Kubernetes Ready**: Full container orchestration support
- **Deep Learning**: PyTorch and ONNX Runtime for ML inference
- **Scientific Computing**: NumPy, SciPy, Scikit-learn for data analysis

### ⚙️ System Configuration
- **AI Settings**: Configure AI model parameters and behavior
- **Voice Command Configuration**: Customize voice command recognition and language
- **System Preferences**: Manage system-wide settings
- **Performance Tuning**: Configurable batch processing and caching

---

## 🛠 Technology Stack

### Backend
- **Framework**: Django 5.2.6
- **Database**: MySQL 2.2.7 (mysqlclient)
- **Authentication**: Django Auth with Custom User Model
- **Web Server**: ASGI/WSGI with Uvicorn 0.35.0
- **HTTP Client**: httpx 0.28.1, requests 2.32.5

### AI & LLM
- **Primary LLM**: Google Generative AI (gemini) 0.8.5
- **Alternative LLM**: Google AI SDK (google-genai) 1.56.0
- **RAG Engine**: LangChain 1.0.7
  - langchain-community 0.4.1
  - langchain-google-genai 3.1.0
  - langchain-chroma 1.0.0
  - langgraph 1.0.3 (Advanced graph-based chains)
  - langsmith 0.4.43 (LangChain monitoring)
- **Vector Database**: ChromaDB 1.0.20
- **Embedding Models**: 
  - sentence-transformers 3.2.1 (paraphrase-multilingual-MiniLM-L12-v2)
  - langchain-huggingface 1.1.0
- **Transformers**: transformers 4.46.3, torch 2.9.1

### Machine Learning & NLP
- **Deep Learning**: PyTorch 2.9.1
- **Scientific Computing**: numpy 2.3.3, scipy 1.16.3, scikit-learn 1.7.2
- **Tensor Processing**: ONNX Runtime 1.22.1
- **Text Processing**: 
  - langchain-text-splitters 1.0.0
  - tokenizers 0.20.3
  - regex 2025.11.3
- **ML Utilities**: joblib 1.5.2, tqdm 4.67.1

### Speech & Audio
- **Text-to-Speech**: Google Cloud Text-to-Speech API
- **Speech Recognition**: Google Cloud Speech API
- **Audio Libraries**: pyzmq 27.1.0, websockets 15.0.1

### Frontend
- **CSS Framework**: Tailwind CSS 4.4.2
- **Template Engine**: Django Templates
- **LiveReload**: django-browser-reload 1.19.0
- **Image Processing**: Pillow 12.0.0
- **Code Highlighting**: Pygments 2.19.2

### Payments & E-commerce
- **Payment Gateway**: Stripe 14.0.1
- **QR Code Generation**: segno 1.6.6
- **Additional QR**: qrcode 8.2

### Data & Serialization
- **JSON**: orjson 3.11.3, ormsgpack 1.12.0
- **Data Validation**: pydantic 2.11.7, pydantic-settings 2.12.0
- **JSON Schema**: jsonschema 4.25.1, dataclasses-json 0.6.7
- **ORM/Query**: SQLAlchemy 2.0.44, PyPika 0.48.9
- **Networking**: networkx 3.6
- **File Detection**: filetype 1.2.0

### Development & Debugging
- **Code Quality**: pylint 4.0.4, isort 7.0.0
- **Type Checking**: mypy_extensions 1.1.0
- **Interactive Shell**: IPython 8.12.3, jupyter_client 8.8.0
- **Linting**: beautifulsoup4 4.14.3
- **Project Templates**: cookiecutter 2.6.0

### DevOps & Deployment
- **Containerization**: Docker & Docker Compose
- **Environment Management**: python-dotenv 1.1.1
- **Monitoring**: 
  - OpenTelemetry 1.37.0 (opentelemetry-api, opentelemetry-sdk)
  - OpenTelemetry OTLP exporter (gRPC + Protobuf)
  - PostHog 5.4.0 (Analytics)
- **Kubernetes Support**: kubernetes 33.1.0

### Cloud & APIs
- **Google Cloud**: 
  - google-api-core 2.28.1
  - google-api-python-client 2.187.0
  - google-auth 2.45.0
  - googleapis-common-protos 1.70.0
- **Protocol Buffers**: protobuf 5.29.5
- **gRPC**: grpcio 1.74.0, grpcio-status 1.71.2

### Async & Networking
- **Async HTTP**: aiohttp 3.13.2, httpx 0.28.1
- **Async Utilities**: aiosignal 1.4.0, anyio 4.10.0
- **Event Loop**: uvloop 0.21.0
- **WebSocket**: websockets 15.0.1, websocket-client 1.8.0
- **HTTP Utilities**: httptools 0.6.4, httplib2 0.31.0, httpcore 1.0.9

### Utilities & Helpers
- **Date/Time**: python-dateutil 2.9.0.post0, arrow 1.3.0, durationpy 0.10
- **Text Processing**: python-slugify 8.0.4
- **Encoding**: chardet 5.2.0, charset-normalizer 3.4.3
- **XML/HTML**: defusedxml 0.7.1, bleach 6.3.0
- **File Operations**: filelock 3.19.1, fsspec 2025.9.0
- **Compression**: zstandard 0.25.0
- **Math**: sympy 1.14.0, mpmath 1.3.0
- **Caching**: cachetools 5.5.2
- **Serialization**: six 1.17.0, orjson 3.11.3
- **Terminal**: rich 14.1.0, click 8.2.1, typer 0.17.4

### Security & Auth
- **Authentication**: bcrypt 4.3.0
- **OAuth**: oauthlib 3.3.1, requests-oauthlib 2.0.0
- **Certificates**: certifi 2025.8.3
- **Cryptography**: rsa 4.9.1, pyasn1 0.6.1, pyasn1_modules 0.4.2

### Additional Libraries
- **Retry Logic**: backoff 2.2.1, tenacity 9.1.2
- **Type Annotations**: annotated-types 0.7.0, typing-extensions 4.15.0
- **Logging**: coloredlogs 15.0.1, humanfriendly 10.0
- **System Utilities**: distro 1.9.0, platformdirs 4.5.1, shellingham 1.5.4
- **Serialization Formats**: PyYAML 6.0.2
- **Build Tools**: build 1.3.0, setuptools 80.9.0, pyproject_hooks 1.2.0

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: 3.10 or higher
- **MySQL**: 8.0 or higher
- **Docker**: Latest stable version (for containerized deployment)
- **Docker Compose**: Latest stable version
- **Node.js**: 14.0 or higher (for frontend asset compilation)
- **pip**: Latest version
- **Git**: For version control
- **CUDA/GPU** (Optional): For accelerated ML inference with PyTorch
- **Kubernetes** (Optional): For container orchestration

### API Keys & Credentials Required
- **Google Cloud**:
  - Google Generative AI API key (Gemini access)
  - Text-to-Speech API credentials
  - Speech-to-Text API credentials
  - Service account JSON for authentication
- **Stripe**: Secret key and publishable key for payment processing
- **OpenTelemetry** (Optional): OTLP endpoint for monitoring

### System Requirements
- **RAM**: Minimum 4GB (8GB+ recommended for ML models)
- **Disk Space**: 5GB+ (for dependencies and AI models)
- **OS**: macOS, Linux, or Windows (WSL2 recommended for Windows)
- **Network**: Stable internet connection for API calls

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Project01
```

### Step 2: Create a Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Install all requirements (205+ dependencies)
pip install -r requirements.txt

# Verify critical packages
python -c "import django; import torch; import langchain; print('All core dependencies installed successfully')"
```

### Step 4: Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration (see [Configuration](#configuration) section). At minimum, you need:
- Google API credentials
- Stripe API keys
- Database credentials

### Step 5: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
# Follow prompts to create admin account
```

Or use the provided script:

```bash
bash create_superuser.sh
```

### Step 6: Initialize AI Services

```bash
# Initialize RAG service (download embeddings models)
python manage.py init_rag

# Sync AI models
python manage.py sync_ai
```

### Step 7: Frontend Setup (if needed)

```bash
cd theme/static_src
npm install
npm run build
cd ../..
```

### Step 8: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 9: Run the Development Server

```bash
python manage.py runserver
```

Or use the provided script:

```bash
bash run_server.sh
```

Access the application at `http://localhost:8000`

### Troubleshooting Installation

**PyTorch Installation Issues:**
```bash
# For CPU-only
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# For GPU (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**MySQL Connection Issues:**
```bash
# macOS
brew install mysql-client

# Linux (Ubuntu/Debian)
sudo apt-get install python3-dev libmysqlclient-dev

# macOS with Apple Silicon
pip install mysqlclient --only-binary :all:
```

**ChromaDB Issues:**
```bash
# Reset ChromaDB
rm -rf data/chroma/
python manage.py init_rag
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=ai_cashier_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Google Cloud Configuration
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Stripe Configuration
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# AI Model Configuration
AI_MODEL_NAME=gemini-pro
AI_TEMPERATURE=0.7
RAG_ENABLED=True
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
VOICE_COMMANDS_ENABLED=True
VOICE_LANGUAGE=th-TH
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# ChromaDB Configuration
CHROMA_DB_PATH=./data/chroma
CHROMA_HOST=localhost
CHROMA_PORT=8000

# OpenTelemetry Configuration (Optional)
OTEL_ENABLED=False
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=ai-cashier

# PostHog Analytics (Optional)
POSTHOG_API_KEY=your-posthog-key
POSTHOG_ENABLED=False

# Application Settings
LANGUAGE_CODE=th
TIME_ZONE=Asia/Bangkok
USE_I18N=True
USE_TZ=True
STATIC_URL=/static/
MEDIA_URL=/media/
```

### Database Configuration

The project uses MySQL as the default database. For Docker deployment, ensure the `docker-compose.yml` is properly configured with your database credentials.

### Google Cloud Setup

1. Create a Google Cloud project
2. Enable the following APIs:
   - Google Generative AI API
   - Google Cloud Text-to-Speech API
   - Google Cloud Speech-to-Text API
3. Create a service account and download credentials JSON
4. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

### Stripe Configuration

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe Dashboard
3. Set `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` in `.env`

---

## 🚀 Usage

### Starting the Application

#### Development Mode

```bash
python manage.py runserver
```

#### Production Mode with Uvicorn

```bash
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop
```

#### Production Mode (Docker)

```bash
docker-compose up -d
```

#### With Monitoring (OpenTelemetry)

```bash
# Start Jaeger for distributed tracing (requires Docker)
docker run -d -p 6831:6831/udp -p 16686:16686 jaegertracing/all-in-one

# Start application with telemetry
OTEL_ENABLED=True uvicorn config.asgi:application
```

### Accessing the Application

- **Main Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Login**: http://localhost:8000/login
- **Jaeger Tracing** (if enabled): http://localhost:16686

### Key Operations

#### Managing Products

1. Navigate to Admin Panel (`/admin/`)
2. Add/Edit/Delete products with descriptions
3. Assign categories and pricing
4. Generate QR codes automatically
5. Set up promotions and discounts

#### Processing Transactions

1. Login as cashier (`/login/`)
2. Search and add products to cart
3. Apply promotions if available
4. Review order details
5. Process payment via Stripe
6. Complete transaction and print receipt

#### Using Voice Commands

1. Enable voice commands in AI Settings
2. Ensure Google Cloud Speech-to-Text is configured
3. Speak commands like:
   - "Search for [product name]"
   - "Add [product] to cart"
   - "Show recommendations"
   - "Process payment"
   - "Print receipt"

#### Accessing Analytics

1. Go to Dashboard (`/dashboard/`)
2. View real-time sales metrics
3. Analyze customer behavior patterns
4. Export reports to CSV/JSON
5. Compare trends over time periods

#### Managing AI Configuration

1. Admin Panel → AI Settings
2. Configure model parameters:
   - Temperature (0.0-1.0)
   - Max tokens
   - Language preference
3. Enable/disable features:
   - Voice commands
   - RAG system
   - Recommendations
   - Analytics

### Management Commands

```bash
# Initialize RAG service with embeddings
python manage.py init_rag

# Sync AI models and caches
python manage.py sync_ai

# Backup all data
python manage.py dumpdata > backup_data.json

# Restore data from backup
python manage.py loaddata backup_data.json

# Clear stale sessions
python manage.py clearsessions

# Create demo data
python manage.py seed_demo_data  # if available

# Run tests
python manage.py test

# Check system status
python manage.py check
```

### Performance Optimization

#### Enable Async Task Processing

```python
# Configure in settings.py
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
```

#### Optimize Database

```bash
# Analyze slow queries
python manage.py dbshell
> ANALYZE TABLE aicashier_order;
> ANALYZE TABLE aicashier_product;
```

#### Cache Configuration

```python
# Redis caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Monitoring & Observability

#### Enable OpenTelemetry Monitoring

```bash
# Set environment variables
export OTEL_ENABLED=True
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=ai-cashier
```

#### View Logs

```bash
# Docker logs
docker-compose logs -f web

# Application logs
tail -f logs/app.log

# Error logs
tail -f logs/error.log
```

---

## 📁 Project Structure

```
Project01/
├── aicashier/                          # Main Django application
│   ├── models.py                       # Database models
│   ├── views.py                        # View functions and classes
│   ├── urls.py                         # URL routing
│   ├── forms.py                        # Django forms
│   ├── admin.py                        # Admin configuration
│   ├── gemini_service.py               # Google Gemini AI integration
│   ├── rag_service.py                  # RAG (Retrieval-Augmented Generation)
│   ├── stripe_service.py               # Stripe payment integration
│   ├── middleware.py                   # Custom middleware
│   ├── signals.py                      # Django signals
│   ├── management/
│   │   └── commands/
│   │       ├── init_rag.py             # RAG initialization
│   │       └── sync_ai.py              # AI model synchronization
│   ├── migrations/                     # Database migrations
│   ├── models/                         # AI models (Sentence Transformers)
│   ├── templates/aicashier/            # HTML templates
│   └── static/                         # Static files (CSS, JS, images)
├── config/                             # Django configuration
│   ├── settings.py                     # Main settings
│   ├── urls.py                         # Root URL configuration
│   ├── wsgi.py                         # WSGI application
│   └── asgi.py                         # ASGI application
├── theme/                              # Theme/UI components
│   ├── static_src/                     # Frontend source files
│   └── templates/base.html             # Base template
├── data/                               # Data storage
│   ├── chroma/                         # ChromaDB vector database
│   └── mysql/                          # MySQL data (Docker)
├── media/                              # User-uploaded media
├── manage.py                           # Django management script
├── requirements.txt                    # Python dependencies
├── docker-compose.yml                  # Docker Compose configuration
├── .env                                # Environment variables
└── README.md                           # This file
```

---

## 🔌 API Endpoints

### Authentication & User Management
- `POST /login/` - User login
- `POST /logout/` - User logout  
- `POST /register/` - User registration
- `POST /api/auth/refresh-token/` - Refresh authentication token
- `GET /api/user/profile/` - Get current user profile
- `PUT /api/user/profile/` - Update user profile
- `POST /api/user/change-password/` - Change password

### Products & Inventory
- `GET /api/products/` - List all products (paginated)
- `GET /api/products/<id>/` - Get product details
- `GET /api/products/search/?q=<query>` - Search products
- `POST /api/products/` - Create product (Admin only)
- `PUT /api/products/<id>/` - Update product (Admin only)
- `DELETE /api/products/<id>/` - Delete product (Admin only)
- `GET /api/categories/` - List all categories
- `POST /api/categories/` - Create category (Admin only)
- `GET /api/products/<id>/qrcode/` - Generate QR code

### Orders & Transactions
- `GET /api/orders/` - List user orders
- `GET /api/orders/<id>/` - Get order details
- `POST /api/orders/` - Create new order
- `PUT /api/orders/<id>/` - Update order
- `DELETE /api/orders/<id>/` - Cancel order
- `POST /api/orders/<id>/payment/` - Process payment
- `GET /api/orders/<id>/invoice/` - Generate invoice
- `POST /api/orders/<id>/items/` - Add items to order
- `DELETE /api/orders/<id>/items/<item_id>/` - Remove item from order

### Customers & Profiles
- `GET /api/customers/` - List customers (Admin only, paginated)
- `GET /api/customers/<id>/` - Get customer details
- `POST /api/customers/` - Create customer (Admin only)
- `PUT /api/customers/<id>/` - Update customer
- `DELETE /api/customers/<id>/` - Delete customer (Admin only)
- `GET /api/customers/<id>/orders/` - Get customer order history
- `GET /api/customers/<id>/analytics/` - Get customer analytics

### Payments
- `POST /api/payments/` - Create payment
- `GET /api/payments/<id>/` - Get payment details
- `POST /api/payments/<id>/confirm/` - Confirm payment
- `POST /api/payments/<id>/refund/` - Process refund
- `GET /api/payments/?status=<status>` - List payments by status
- `POST /api/payments/webhook/` - Stripe webhook (internal)

### Promotions & Discounts
- `GET /api/promotions/` - List active promotions
- `GET /api/promotions/<id>/` - Get promotion details
- `POST /api/promotions/` - Create promotion (Admin only)
- `PUT /api/promotions/<id>/` - Update promotion (Admin only)
- `DELETE /api/promotions/<id>/` - Delete promotion (Admin only)
- `POST /api/promotions/<id>/apply/` - Apply promotion to order
- `GET /api/promotions/validate/?code=<code>` - Validate promo code

### AI Features
- `POST /api/ai/search/` - AI-powered product search
- `GET /api/ai/search/history/` - Get search history
- `POST /api/ai/recommendations/` - Get product recommendations
- `POST /api/ai/recommendations/<user_id>/` - Get personalized recommendations
- `POST /api/ai/voice-command/` - Process voice commands (audio upload)
- `POST /api/ai/chat/` - Chat with AI assistant
- `POST /api/ai/rag/query/` - Query RAG system
- `GET /api/ai/model-info/` - Get current AI model info

### Analytics & Reports
- `GET /api/analytics/dashboard/` - Dashboard overview
- `GET /api/analytics/sales/` - Sales report (daily/weekly/monthly)
- `GET /api/analytics/customers/` - Customer analytics
- `GET /api/analytics/products/` - Product performance analytics
- `GET /api/analytics/revenue/` - Revenue trends
- `GET /api/analytics/export/?format=csv` - Export analytics
- `GET /api/analytics/compare/?period1=<date1>&period2=<date2>` - Compare periods

### System & Settings
- `GET /api/system/health/` - System health check
- `GET /api/system/status/` - System status
- `GET /api/ai/settings/` - Get AI settings
- `PUT /api/ai/settings/` - Update AI settings (Admin only)
- `POST /api/cache/clear/` - Clear cache (Admin only)
- `GET /api/system/logs/` - System logs (Admin only)

### Batch Operations
- `POST /api/batch/products/import/` - Bulk import products
- `POST /api/batch/orders/process/` - Process batch orders
- `POST /api/batch/refund/` - Process batch refunds

### WebSocket Endpoints (Real-time)
- `ws://localhost:8000/ws/orders/` - Real-time order updates
- `ws://localhost:8000/ws/analytics/` - Real-time analytics
- `ws://localhost:8000/ws/chat/` - Real-time chat

### Response Format

All API endpoints return JSON with standard format:

```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation successful",
  "timestamp": "2025-01-13T10:30:00Z",
  "request_id": "uuid-string"
}
```

### Error Responses

```json
{
  "success": false,
  "error": "Error code",
  "message": "Human readable error message",
  "details": { /* error details */ },
  "status_code": 400
}
```

---

## 🗄️ Database Schema

### Key Models

**Customer** (Custom User Model)
- username, email, password
- first_name, last_name
- phone_number, address
- role (staff/customer/admin)
- created_at, updated_at

**Product**
- name, description, price
- category (Foreign Key)
- quantity, sku
- qr_code
- created_at, updated_at

**Order**
- customer (Foreign Key)
- order_number, order_type
- total_amount, tax_amount
- status, payment_status
- order_date, completed_date

**OrderItem**
- order (Foreign Key)
- product (Foreign Key)
- quantity, price
- subtotal

**Payment**
- order (Foreign Key)
- amount, payment_method
- transaction_id, status
- stripe_payment_intent
- created_at

**Promotion**
- title, description
- discount_percentage/amount
- valid_from, valid_to
- active

**AISettings**
- model_name, temperature
- voice_commands_enabled
- language_preference

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild services
docker-compose up -d --build
```

### Services Included
- **web**: Django application
- **db**: MySQL database
- **chroma**: ChromaDB vector database (optional)

---

## 🔒 Security Best Practices

### Authentication & Authorization
- **JWT Tokens**: Use JWT for API authentication in production
- **CSRF Protection**: Enabled by default for form submissions
- **HTTPS**: Always use HTTPS in production
- **API Keys**: Store in environment variables, never commit to git

### Database Security
```python
# settings.py - Enable SSL for MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'ssl': {'ca': '/path/to/ca.pem'},
        }
    }
}
```

### Payment Security
- **PCI Compliance**: Stripe handles sensitive payment data
- **Webhook Verification**: Always verify Stripe webhooks
- **Token Storage**: Never store raw payment tokens
- **Rate Limiting**: Implement rate limiting on payment endpoints

### API Security
```python
# Add to settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'
```

### AI Model Security
- **Input Validation**: Sanitize all user inputs before sending to AI
- **Output Filtering**: Filter AI responses for harmful content
- **API Rate Limits**: Implement rate limiting on AI endpoints
- **Model Isolation**: Run AI services in isolated containers

### Data Protection
- **Encryption at Rest**: Enable database encryption
- **Encryption in Transit**: Use TLS/SSL
- **Data Backup**: Regular encrypted backups
- **Data Retention**: Implement data retention policies

---

## 📚 Best Practices

### Code Quality
```bash
# Run linting
pylint aicashier/

# Format code
isort aicashier/
black aicashier/

# Type checking
mypy aicashier/

# Tests
python manage.py test --verbosity=2 --failfast
```

### Performance Optimization
- **Database Indexing**: Add indexes on frequently queried fields
- **Query Optimization**: Use `select_related()` and `prefetch_related()`
- **Caching Strategy**: Cache AI model responses
- **Async Operations**: Use async for long-running tasks
- **Connection Pooling**: Configure MySQL connection pooling

### Testing Strategy
```bash
# Unit tests
python manage.py test aicashier.tests.unit

# Integration tests
python manage.py test aicashier.tests.integration

# E2E tests (requires Selenium)
python manage.py test aicashier.tests.e2e

# Coverage report
coverage run --source='aicashier' manage.py test
coverage report
coverage html
```

### Deployment Checklist
- [ ] Set `DEBUG = False`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS/SSL
- [ ] Set up database backups
- [ ] Configure environment variables
- [ ] Run `collectstatic`
- [ ] Run `migrate`
- [ ] Set up monitoring/logging
- [ ] Test payment processing
- [ ] Verify AI services
- [ ] Load test endpoints

---

## 🐛 Troubleshooting

### Database Connection Issues

**Problem**: `Can't connect to MySQL server`

```bash
# Check MySQL is running
mysql -u root -p

# Verify credentials in .env
# Check database exists
mysql -u root -p -e "SHOW DATABASES;"

# Create if missing
mysql -u root -p -e "CREATE DATABASE ai_cashier_db;"
```

### AI Model Issues

**Problem**: `Google API authentication failed`

```bash
# Verify credentials file
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
python -c "from google.oauth2 import service_account; print('OK')"

# Check API is enabled
gcloud services list --enabled | grep generativeai
```

**Problem**: `Sentence Transformers model download fails`

```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Or set cache directory
export SENTENCE_TRANSFORMERS_HOME=/path/to/cache
```

### Stripe Payment Issues

**Problem**: `Stripe API key invalid`

```bash
# Verify key
python -c "import stripe; stripe.api_key='your-key'; stripe.Account.retrieve()"

# Check webhook endpoint
stripe listen --forward-to localhost:8000/webhook/stripe/
```

### Voice Command Issues

**Problem**: `Speech recognition not working`

```bash
# Check Google Cloud credentials
gcloud auth application-default login

# Verify Cloud Speech API is enabled
gcloud services enable speech.googleapis.com
```

### Performance Issues

**Problem**: `Slow AI queries`

```bash
# Check model performance
time python manage.py init_rag

# Monitor database queries
from django.db import connection
from django.test.utils import override_settings
@override_settings(DEBUG=True)
def slow_query():
    # Your query here
    print(connection.queries)
```

### Memory Issues

**Problem**: `Out of memory during model loading`

```bash
# Check available memory
free -h

# Reduce batch size in settings
RAG_BATCH_SIZE=4

# Use CPU instead of GPU
export CUDA_VISIBLE_DEVICES=""
```

### Docker Issues

**Problem**: `Docker container won't start`

```bash
# Check logs
docker-compose logs web

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up

# Clear volumes (WARNING: deletes data)
docker-compose down -v
```

### Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping

# Start Redis (if not running)
redis-server

# Docker Redis
docker run -d -p 6379:6379 redis:latest
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Commit your changes**: `git commit -m 'Add your feature'`
4. **Push to the branch**: `git push origin feature/your-feature`
5. **Submit a Pull Request**

### Development Setup

1. Follow the installation steps
2. Create a new branch for your feature: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write/update tests: `python manage.py test`
5. Run linting: `pylint aicashier/`
6. Commit with clear messages
7. Submit PR with description

### Pull Request Guidelines
- Include description of changes
- Reference related issues (#issue-number)
- Add tests for new features
- Update documentation
- Follow PEP 8 style guide
- Ensure CI/CD passes

---

## 📞 Support & Issues

### Getting Help
1. Check [Troubleshooting](#troubleshooting) section
2. Review [GitHub Issues](https://github.com/your-repo/issues)
3. Check [Documentation](#-additional-resources)
4. Contact project owner

### Reporting Issues
- Include error messages and logs
- Provide steps to reproduce
- Mention Python, Django, and OS versions
- Include relevant configuration

---

## 🙏 Acknowledgments

- **Google Cloud** for AI and cloud services
- **Stripe** for payment processing infrastructure
- **Django Community** for excellent framework and ecosystem
- **LangChain** for RAG and LLM orchestration
- **PyTorch** for deep learning capabilities
- All contributors and testers

---

## � License

This project is licensed under the LICENSE file included in the repository.

---

## 👤 Author

**Mr. Supachai Taengyonram**

**Senior Project**: AI CASHIER System  
**Institution**: [Your Institution]  
**Year**: 2025-2026  
**Status**: Active Development 🚀

---

## 📞 Contact & Support

For questions, issues, or suggestions regarding this project:

- **Email**: [your-email@example.com]
- **GitHub Issues**: Please use the [GitHub Issues tracker](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions) (if enabled)
- **Documentation**: [Full Documentation](https://docs.example.com)

### Security Issues
For security vulnerabilities, please email [security@example.com] instead of using public issues.

---

## 📚 Additional Resources

### Official Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Google Generative AI API](https://ai.google.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [Stripe Developer Docs](https://stripe.com/docs)

### AI & ML Resources
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text/docs)
- [LangGraph for AI Workflows](https://langchain-ai.github.io/langgraph/)

### DevOps & Deployment
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [OpenTelemetry](https://opentelemetry.io/)
- [Jaeger Tracing](https://www.jaegertracing.io/)

### Related Projects
- [Django Multilingual Support](https://django-modeltranslation.readthedocs.io/)
- [Celery Task Queue](https://docs.celeryproject.io/)
- [Redis Documentation](https://redis.io/documentation)

---

## 📊 Project Statistics

- **Total Dependencies**: 205+
- **Python Packages**: 150+
- **ML/AI Libraries**: 25+
- **Total Lines of Code**: [Calculate your project]
- **Test Coverage**: [Add your coverage]
- **Documentation**: Complete

---

## 🗺️ Roadmap

### Version 1.1 (Q2 2025)
- [ ] Advanced customer segmentation using ML
- [ ] Predictive inventory management
- [ ] Multi-language UI optimization
- [ ] Mobile app companion

### Version 1.2 (Q3 2025)
- [ ] Advanced fraud detection
- [ ] Real-time inventory sync
- [ ] Enhanced analytics dashboard
- [ ] API rate limiting improvements

### Version 2.0 (Q4 2025)
- [ ] Blockchain payment verification
- [ ] AR product visualization
- [ ] Advanced supply chain integration
- [ ] IoT device support

---

## 📈 Performance Metrics

### Benchmarks (Hardware Dependent)
- **Page Load Time**: < 500ms
- **API Response Time**: < 200ms
- **AI Query Time**: < 2s (with caching)
- **Voice Command Processing**: < 3s
- **Database Query Time**: < 100ms

### Scalability
- **Concurrent Users**: 1000+
- **Orders/Hour**: 10,000+
- **API Requests/Second**: 100+
- **Data Storage**: 500GB+

---

## 🎓 Learning Resources

For developers new to this project:

1. **Django Basics**: Complete [Django for Beginners](https://djangoforbeginners.com/)
2. **AI/ML Fundamentals**: Start with [LangChain tutorials](https://python.langchain.com/docs/get_started/introduction)
3. **Google Cloud Setup**: Follow [Google Cloud documentation](https://cloud.google.com/docs)
4. **Stripe Integration**: Read [Stripe Developer Docs](https://stripe.com/docs)
5. **Docker & Deployment**: Take [Docker fundamentals course](https://docs.docker.com/guides/docker-overview/)

---

## 📝 Version History

### Version 1.0.0 - January 2026
- ✅ Initial release
- ✅ Core POS functionality
- ✅ AI-powered features
- ✅ Payment processing
- ✅ Customer management
- ✅ Analytics dashboard
- ✅ Voice commands
- ✅ Docker deployment

---

## 📄 Documentation Index

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview and setup (this file) |
| [INSTALLATION.md](docs/INSTALLATION.md) | Detailed installation guide |
| [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) | API reference |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment guide |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [LICENSE](LICENSE) | Project license |

---

**Last Updated**: January 13, 2026

**Version**: 1.0.0

**Status**: Active Development 🚀

**Made with ❤️ by Mr. Supachai Taengyonram**
