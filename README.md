# AI CASHIER

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2.6-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](#status)

**An intelligent AI-powered Point of Sale (POS) system with voice command support and RAG-based product search**

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Voice Commands](#-voice-command-system) • [Contributing](#-contributing)

</div>

---

## 📋 Overview

**AI CASHIER** is a modern Point-of-Sale system combining Django backend with AI technology. Designed specifically for Thai retail businesses with natural language voice command support, intelligent product recommendations, and seamless payment processing.

**Key Highlights:**
- 🎤 Thai voice commands for hands-free cart management
- 🤖 RAG-powered semantic product search
- 💳 Stripe payment integration
- 📦 Real-time inventory tracking
- 📊 Sales analytics and reporting
- 👥 Multi-role staff management

---

## ✨ Key Features

### 🎤 Voice Command System (ระบบคำสั่งเสียง)
- **Natural Thai Language**: Process voice commands in Thai language
- **Dynamic Management**: Add/edit voice commands from admin panel without server restart
- **Three Action Types**:
  - `add` (เพิ่ม) - Add items to cart with quantity
  - `decrease` (ลด) - Reduce item quantity  
  - `delete` (ลบ) - Remove items from cart
- **Smart Parsing**: Automatically extract product names and quantities
- **Real-time Feedback**: Cart summary with prices and totals

**Example Voice Commands:**
```
"เอมะม่วง 5"       → Add 5 mangoes to cart
"ดาวมะม่วง 2"      → Decrease mangoes by 2
"ถอดส้มโอ"         → Remove pomelos from cart
```

### 🔍 Intelligent Product Search
- **RAG System**: ChromaDB vector database with semantic search
- **Embeddings**: Sentence Transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Multi-language**: Thai and English support
- **Fast Retrieval**: Sub-second product matching

### 💳 Payment Processing
- **Stripe Integration**: Secure payment gateway
- **Payment Links**: Generate QR codes for mobile payments
- **Webhook Support**: Real-time payment verification
- **Order Tracking**: Complete transaction history

### 📦 Cart Management
- **Session-based**: Persistent shopping cart
- **Dynamic Pricing**: Real-time totals and promotions
- **Stock Validation**: Automatic inventory checking
- **Detailed Summary**: Items, quantities, prices, and grand total

### 📊 Admin Dashboard
- **Sales Analytics**: Daily/weekly/monthly trends
- **Product Performance**: Top sellers and inventory status
- **Customer Management**: User profiles and order history
- **Report Export**: Download data in multiple formats

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-cashier.git
cd ai-cashier
```

### 2. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env and add:
# - GOOGLE_API_KEY (for Gemini AI)
# - STRIPE_SECRET_KEY (for payments)
# - Database credentials
```

### 5. Initialize Database
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py init_rag
```

### 6. Run Server
```bash
python manage.py runserver
```

Access at: `http://localhost:8000`  
Admin at: `http://localhost:8000/admin`

---

## 📦 Installation

### Step-by-Step Setup

#### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

#### 2. Install Requirements
```bash
pip install --upgrade pip setuptools
pip install -r requirements.txt
```

#### 3. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required .env variables:**
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
GOOGLE_API_KEY=your-google-api-key
STRIPE_SECRET_KEY=your-stripe-secret-key
DB_ENGINE=django.db.backends.mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ai_cashier_db
DB_USER=root
DB_PASSWORD=your_password
```

#### 4. Database Setup
```bash
# Apply migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
# Follow prompts to create username and password

# Initialize RAG system (download embeddings)
python manage.py init_rag
```

#### 5. Run Development Server
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Docker Setup

```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web
```

---

## 🎤 Voice Command Configuration

### Managing Voice Commands

1. **Login to Admin Panel**: `http://localhost:8000/admin/`
2. **Go to AI Settings**: Find "AI Settings" in admin menu
3. **Configure Commands**:
   - **Voice Commands (Add)**: Words for adding items (e.g., `เพิ่ม|add|ใส่`)
   - **Voice Commands (Decrease)**: Words for reducing quantity (e.g., `ลด|decrease|ดาว`)
   - **Voice Commands (Delete)**: Words for removing items (e.g., `ลบ|delete|ถอด`)
4. **Click Save**: Commands are automatically reloaded via Django signals

**No server restart needed!** Changes take effect immediately.

### Adding New Commands

Example: Add "ซื้อ" (buy) as an add command
```
In Admin → AI Settings:

Voice Commands (Add): เพิ่ม|add|ใส่|ซื้อ

Click Save → ✅ Ready to use!
```

---

## 💻 API Endpoints

### Cart & Voice Commands
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/voice-order/` | Process voice commands |
| `POST` | `/api/voice-cart/` | Manage cart via chat |
| `GET`  | `/api/cart/` | Get current cart |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/products/` | List all products |
| `GET`  | `/api/products/search/?q=<query>` | Search products |
| `POST` | `/api/products/` | Create product (admin) |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/payments/` | Create payment |
| `GET`  | `/api/payments/<id>/` | Get payment status |

### Chat & AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/` | Chat with AI |

---

## 🗂️ Project Structure

```
ai-cashier/
├── aicashier/                    # Main Django app
│   ├── models.py                 # Database models
│   ├── views.py                  # API views & endpoints
│   ├── urls.py                   # URL routing
│   ├── rag_service.py           # RAG & voice command logic
│   ├── gemini_service.py        # Google Gemini integration
│   ├── stripe_service.py        # Stripe payment integration
│   ├── signals.py               # Signal handlers (auto-reload)
│   ├── forms.py                 # Django forms
│   ├── admin.py                 # Admin configuration
│   ├── middleware.py            # Custom middleware
│   ├── management/commands/     # Management commands
│   ├── migrations/              # Database migrations
│   ├── models/                  # AI models (embeddings)
│   ├── templates/               # HTML templates
│   └── static/                  # CSS, JS, images
├── config/                       # Django configuration
│   ├── settings.py              # Main settings
│   ├── urls.py                  # Root URLs
│   ├── wsgi.py                  # WSGI entry
│   └── asgi.py                  # ASGI entry
├── data/
│   ├── chroma/                  # ChromaDB vector store
│   └── mysql/                   # MySQL data (Docker)
├── manage.py                     # Django CLI
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker configuration
├── .env.example                 # Example environment
└── README.md                    # This file
```

---

## 💡 Usage Examples

### Example 1: Add Items to Cart
```
Customer: "เอมะม่วง 5"
System Response:
─────────────────────────────────────
เพิ่ม มะม่วง 5

📦 ตะกร้าของคุณ:
• มะม่วง 5 ชิ้น @ ฿20.00 = ฿100.00

💰 รวมเป็นเงินทั้งสิ้น: ฿100.00 ครับ
─────────────────────────────────────
```

### Example 2: Reduce Quantity
```
Customer: "ดาวมะม่วง 2"
System Response:
─────────────────────────────────────
ลด มะม่วง เป็น 3

📦 ตะกร้าของคุณ:
• มะม่วง 3 ชิ้น @ ฿20.00 = ฿60.00
• ส้มโอ 6 ชิ้น @ ฿25.00 = ฿150.00

💰 รวมเป็นเงินทั้งสิ้น: ฿210.00 ครับ
─────────────────────────────────────
```

### Example 3: Remove Item
```
Customer: "ถอดส้มโอ"
System Response:
─────────────────────────────────────
ลบ ส้มโอ ออกจากตะกร้า

📦 ตะกร้าของคุณ:
• มะม่วง 3 ชิ้น @ ฿20.00 = ฿60.00

💰 รวมเป็นเงินทั้งสิ้น: ฿60.00 ครับ
─────────────────────────────────────
```

---

## 🔧 Development

### Running Tests
```bash
python manage.py test
python manage.py test aicashier --verbosity=2
```

### Database Migrations
```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Code Quality
```bash
# Linting
pylint aicashier/

# Code formatting
isort aicashier/
black aicashier/

# Type checking
mypy aicashier/
```

---

## 🐛 Troubleshooting

### MySQL Connection Error
```bash
# Check MySQL is running
mysql -u root -p

# Create database if missing
mysql -u root -p -e "CREATE DATABASE ai_cashier_db;"
```

### Google API Key Error
```bash
# Verify key works
export GOOGLE_API_KEY="your-key-here"
python -c "import google.generativeai; print('OK')"
```

### Stripe Webhook Issues
```bash
# Test webhook locally
stripe listen --forward-to localhost:8000/webhook/stripe/
```

### ChromaDB Issues
```bash
# Reset ChromaDB
rm -rf data/chroma/
python manage.py init_rag
```

### Voice Commands Not Working
```bash
# Check AISettings in database
python manage.py shell
>>> from aicashier.models import AISettings
>>> s = AISettings.get_settings()
>>> print(s.voice_commands_add)
>>> print(s.voice_commands_decrease)
>>> print(s.voice_commands_delete)

# If empty, add commands in admin panel
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────┐
│         User (Voice/Chat Input)                 │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│    API Endpoints (voice_order, voice_cart)      │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│     RAG Service                                 │
│  - parse_cart_command_with_cart_context()       │
│  - voice_manage_cart()                          │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  Voice Command Manager                          │
│  - Load commands from AISettings DB             │
│  - Detect action (add/decrease/delete)          │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│    Cart Processing                              │
│  - Find products in database                    │
│  - Update quantities                            │
│  - Calculate totals                             │
└──────────────┬──────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│  Generate Response with Cart Summary            │
│  - Display items, prices, totals                │
└─────────────────────────────────────────────────┘
```

### Auto-Reload Signal Flow
```
Admin saves AISettings
         ↓
Django post_save signal
         ↓
reload_voice_commands_on_settings_change()
         ↓
VoiceCommandManager.get_voice_commands()
         ↓
rag_service.voice_commands updated in memory
         ↓
✅ Ready for next voice command!
```

---

## 📋 Requirements

**Core Dependencies:**
- **Django 5.2.6** - Web framework
- **MySQL 2.2.7** - Database driver
- **Google Generative AI 0.8.5** - Gemini API
- **LangChain 1.0.7** - RAG orchestration
- **ChromaDB 1.0.20** - Vector database
- **Sentence Transformers 3.2.1** - Embeddings
- **Stripe 14.0.1** - Payment gateway
- **PyTorch 2.9.1** - ML framework

**Total: 205+ dependencies** (see `requirements.txt`)

---

## 🚀 Deployment

### Development
```bash
python manage.py runserver
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Production (Docker)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Update `SECRET_KEY` to random value
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS/SSL
- [ ] Set strong database password
- [ ] Run `python manage.py collectstatic`
- [ ] Setup database backups
- [ ] Configure monitoring/logging

---

## 🔒 Security

### Best Practices
```python
# settings.py for production
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### API Security
- ✅ All voice commands validated server-side
- ✅ Input sanitization before AI processing
- ✅ CSRF protection enabled
- ✅ Rate limiting on sensitive endpoints
- ✅ Stripe PCI compliance

---

## 📞 Support & Issues

### Report Issues
1. Check [Troubleshooting](#-troubleshooting) section
2. Create GitHub issue with:
   - Error message and full traceback
   - Steps to reproduce
   - Python and Django versions
   - Operating system
   - .env configuration (without secrets)

### Security Vulnerabilities
Please email security details privately instead of GitHub issues.

---

## 🤝 Contributing

We welcome contributions! Please:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Guidelines
- Follow [PEP 8](https://pep8.org/) style guide
- Write tests for new features
- Update documentation
- Ensure tests pass: `python manage.py test`
- Add docstrings to functions/classes

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Mr. Supachai Taengyonram**

- **Senior Project**: AI CASHIER System
- **Year**: 2025-2026
- **Status**: ✅ Active Development

---

## 🙏 Acknowledgments

- **Google Cloud**: Generative AI & Cloud services
- **Stripe**: Payment infrastructure
- **LangChain**: RAG and LLM orchestration
- **Django**: Web framework
- **PyTorch**: Machine learning framework
- All contributors and testers

---

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Google Generative AI](https://ai.google.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Guide](https://docs.trychroma.com/)
- [Stripe API Reference](https://stripe.com/docs/api)

---

<div align="center">

**Made with ❤️ by Mr. Supachai Taengyonram**

[⬆ Back to top](#ai-cashier)

</div>
