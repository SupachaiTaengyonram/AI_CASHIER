

#  AI CASHIER

An AI-powered Point-of-Sale (POS) web application that combines
traditional product management with **LLM, RAG, Semantic Search, and Voice Commands**.

This project was developed as a senior project with a focus on
full-stack web application development and practical AI integration.

---

## ✨ Features

- 🛒 Product and shopping cart management
- 🎤 Voice-based product commands
- 🤖 LLM-powered conversational interaction
- 🔎 Semantic Search for product discovery
- 🧠 Retrieval-Augmented Generation (RAG)
- 📚 Vector search using ChromaDB
- 🗄️ Relational data management using MySQL
- 💳 Payment integration
- 📊 Sales and inventory management
- 👤 User and staff management
- 🧾 Order and transaction tracking
- 📦 Real-time inventory validation
- 📊 Sales analytics and reporting
- ⚙️ Admin-configurable voice commands
- 🔄 Automatic voice-command configuration reload without server restart

---

#  System Architecture

The application consists of a Django backend, MySQL for structured
application data, and ChromaDB for vector-based semantic search.

```text
                         User
                           │
                           ▼
                    Django Web App
                           │
                 ┌─────────┴─────────┐
                 │                   │
                 ▼                   ▼
              MySQL             RAG Service
                 │                   │
        Structured Data       ┌───────┼────────┐
                              │       │        │
                              ▼       ▼        ▼
                         Embedding  ChromaDB  Gemini
                           Model       │       LLM
                              │        │        │
                              └───────►│        │
                                       │        │
                                       ▼        │
                                  Semantic     │
                                    Search     │
                                       │        │
                                       └───┬────┘
                                           ▼
                                        Context
                                           │
                                           ▼
                                          LLM
                                           │
                                           ▼
                                       Response
````

---

# 🧠 AI Architecture

The AI component is based on a combination of:

-  Large Language Model (LLM) 
-  Retrieval-Augmented Generation (RAG) 
-  Semantic Search 
-  Embeddings 
-  Vector Database 
-  LangChain 

The main AI flow is:

```
```

```
User Query
    │
    ▼
Embedding Model
    │
    ▼
Vector Representation
    │
    ▼
ChromaDB
    │
    ▼
Similarity Search
    │
    ▼
Relevant Product Information
    │
    ▼
RAG Context
    │
    ▼
Gemini LLM
    │
    ▼
Generated Response
```

---

# 🔎 Semantic Search

Traditional keyword search depends heavily on exact words.

For example:

```
```

```
Query:
"เครื่องดื่มหวานน้อย"
```

A keyword-based search may only find products containing the exact

keywords.

This project uses **Semantic Search**, which attempts to understand

the meaning of the query.

```
```

```
User Query
     │
     ▼
Embedding
     │
     ▼
Vector
     │
     ▼
ChromaDB
     │
     ▼
Similarity Search
     │
     ▼
Semantically Similar Products
```

The project uses:

```
```

```
Sentence Transformers
paraphrase-multilingual-MiniLM-L12-v2
```

to generate multilingual text embeddings.

---

# 📚 ChromaDB

ChromaDB is used as the project's **vector database**.

It stores vector embeddings and metadata used for similarity search.

Example:

```
```

```
Product
   │
   ▼
Text Representation
   │
   ▼
Embedding Model
   │
   ▼
Vector
   │
   ▼
ChromaDB
```

ChromaDB is not used as a replacement for MySQL.

The two databases have different responsibilities.

### MySQL

Stores structured application data:

```
```

```
Products
Orders
Users
Inventory
Prices
Categories
```

### ChromaDB

Stores information used for semantic retrieval:

```
```

```
Embeddings
Product metadata
Vector representations
```

The databases are connected through the **Django application layer**,

rather than directly connecting MySQL to ChromaDB.

---

# 🔗 MySQL + ChromaDB Data Flow

The application uses MySQL as the primary source of structured

application data.

Product information can be transformed into embeddings and stored

in ChromaDB for semantic retrieval.

```
```

```
                 MySQL
                   │
                   │ Product Data
                   ▼
              RAG Service
                   │
                   │ Generate Embedding
                   ▼
               ChromaDB
                   │
                   │ Similarity Search
                   ▼
             Relevant Product
                   │
                   │ product_id / metadata
                   ▼
                 MySQL
                   │
                   ▼
          Actual Product Data
```

This allows the application to combine:

-  Structured relational queries 
-  Semantic vector search 

---

# 🔥 Retrieval-Augmented Generation (RAG)

RAG is used to provide the LLM with relevant information retrieved

from the application's own data.

The process is:

```
```

```
User Question
      │
      ▼
Semantic Search
      │
      ▼
ChromaDB
      │
      ▼
Relevant Information
      │
      ▼
Context
      │
      ▼
Gemini LLM
      │
      ▼
Generated Answer
```

Instead of relying only on the LLM's general knowledge, the system

retrieves relevant information and provides it as context.

This helps the LLM generate responses based on the application's

product and business data.

---

# 🦜 LangChain

LangChain is used as an **orchestration layer** for the AI pipeline.

It helps connect different components such as:

```
```

```
LangChain
   │
   ├── Embedding Model
   │
   ├── ChromaDB
   │
   ├── Retriever
   │
   ├── Prompt
   │
   └── Gemini LLM
```

The main purpose is to organize the flow between retrieval,

context construction, and LLM generation.

LangChain does not replace the LLM.

Instead, it helps orchestrate the components around the LLM.

---

# 🤖 Large Language Model

The project uses:

```
```

```
Google Gemini 2.5 Flash
```

The LLM is responsible for understanding the retrieved context and

generating natural-language responses.

Example flow:

```
```

```
User
 │
 │ "ช่วยแนะนำเครื่องดื่มให้หน่อย"
 ▼
Semantic Search
 │
 ▼
ChromaDB
 │
 ▼
Relevant Products
 │
 ▼
RAG Context
 │
 ▼
Gemini 2.5 Flash
 │
 ▼
Natural Language Response
```

---

# 🎤 Voice Command

The system also supports voice-based interaction.

A voice command can be processed and converted into an action such as:

```
```

```
ADD
DECREASE
DELETE
SEARCH
```

Example:

```
```

```
User:
"เพิ่ม Coke 2 ขวด"

        │
        ▼

Voice / Language Processing

        │
        ▼

Identify Intent

        │
        ▼

Find Product

        │
        ▼

Update Shopping Cart
```

---

# 🐳 Docker Compose

Docker is used for **infrastructure services**, not for the Django

application.

The Django application runs directly in the Python environment.

Docker Compose is used to run:

```
```

```
Docker Compose
      │
      ├── MySQL
      │
      └── ChromaDB
```

The services are isolated and can be started together using Docker

Compose.

```
```

```
docker compose up -d
```

Check running services:

```
```

```
docker compose ps
```

View logs:

```
```

```
docker compose logs
```

Stop services:

```
```

```
docker compose down
```

---

# 🗄️ Database Architecture

```
```

```
                 Django
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
      MySQL                ChromaDB
        │                     │
        ▼                     ▼
 Structured Data        Vector Data
        │                     │
        │                Semantic Search
        │                     │
        └──────────┬──────────┘
                   ▼
                RAG
```

### MySQL

Used for transactional and structured data.

### ChromaDB

Used for vector embeddings and semantic similarity search.

---

# 🛠️ Technology Stack

## Backend

-  Python 
-  Django 

## AI / Machine Learning

-  Google Gemini 
-  LangChain 
-  Sentence Transformers 
-  RAG 
-  Semantic Search 
-  Embeddings 

## Databases

-  MySQL 
-  ChromaDB 

## Infrastructure

-  Docker 
-  Docker Compose 

## Payment

-  Stripe 

---

# 📁 Project Structure

```
```

```
AI_CASHIER/
│
├── aicashier/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── rag_service.py
│   └── ...
│
├── templates/
│
├── static/
│
├── docker-compose.yml
│
├── requirements.txt
│
├── manage.py
│
└── README.md
```

---

# ⚙️ Requirements

Before running the project, install:

-  Python 3.x 
-  Docker 
-  Docker Compose 
-  Git 

---

# 🚀 Installation

## 1. Clone the repository

```
```

```
git clone https://github.com/SupachaiTaengyonram/AI_CASHIER.git

cd AI_CASHIER
```

---

## 2. Start infrastructure services

Start MySQL and ChromaDB:

```
```

```
docker compose up -d
```

Check:

```
```

```
docker compose ps
```

---

## 3. Create Python virtual environment

```
```

```
python -m venv venv
```

Activate it.

### macOS / Linux

```
```

```
source venv/bin/activate
```

### Windows

```
```

```
venv\Scripts\activate
```

---

## 4. Install dependencies

```
```

```
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file for local configuration.

Example:

```
```

```
SECRET_KEY=your-secret-key

DEBUG=True

DB_NAME=your_database
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306

GOOGLE_API_KEY=your-google-api-key

STRIPE_SECRET_KEY=your-stripe-secret-key
```

Never commit real API keys or credentials to Git.

---

# 🗃️ Database Migration

Run Django migrations:

```
```

```
python manage.py migrate
```

Create an administrator if required:

```
```

```
python manage.py createsuperuser
```

---

# ▶️ Run the Application

Start the Django development server:

```
```

```
python manage.py runserver
```

The Django application will then be available locally.

---

# 🧪 Testing

Run Django tests:

```
```

```
python manage.py test
```

---

# 🔍 Example AI Search Flow

Example query:

```
```

```
"มีเครื่องดื่มอะไรที่เหมาะกับอากาศร้อนบ้าง"
```

Processing:

```
```

```
User Query
     │
     ▼
Embedding Model
     │
     ▼
Vector Representation
     │
     ▼
ChromaDB
     │
     ▼
Similarity Search
     │
     ▼
Relevant Products
     │
     ▼
RAG Context
     │
     ▼
Gemini
     │
     ▼
AI Response
```

---

# 💻 API Endpoints

The application exposes API endpoints for cart operations, product search,
payments, and AI interaction.

### Cart & Voice Commands

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/voice-order/` | Process voice commands |
| `POST` | `/api/voice-cart/` | Manage the cart through natural language |
| `GET` | `/api/cart/` | Get the current cart |

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products/` | List products |
| `GET` | `/api/products/search/?q=<query>` | Search products |
| `POST` | `/api/products/` | Create a product |

### Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/payments/` | Create a payment |
| `GET` | `/api/payments/<id>/` | Get payment status |

### AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/` | Interact with the AI assistant |

---

# 🎤 Voice Command Configuration

Voice commands can be configured from the Django admin panel.

Supported actions include:

- `ADD` — add a product to the cart
- `DECREASE` — decrease a product quantity
- `DELETE` — remove a product from the cart
- `SEARCH` — search for products

Commands can be stored and managed through the application's AI settings,
allowing command vocabulary to be changed without modifying the application
code.

For example, Thai command vocabulary can include:

```text
เพิ่ม|add|ใส่|ซื้อ
ลด|decrease|ดาว
ลบ|delete|ถอด
```

After configuration changes are saved, the voice-command configuration is
reloaded so that the updated commands can be used without restarting the
Django development server.

---

# 🎯 Project Objectives

The main objectives of this project are:

1.  Develop a functional POS web application. 
2.  Integrate AI into the shopping experience. 
3.  Implement semantic product search. 
4.  Implement Retrieval-Augmented Generation. 
5.  Explore vector databases using ChromaDB. 
6.  Integrate an LLM into a real-world application. 
7.  Combine relational and vector databases in a single system. 
8.  Support natural-language and voice-based interaction. 

---

# 📌 Project Scope

This project was primarily developed as a **Full-Stack Web Application**
**
with AI integration**.

DevOps practices such as production CI/CD, Kubernetes orchestration,

and production infrastructure automation were not the primary scope

of the original project.

Docker Compose was used primarily to manage the MySQL and ChromaDB

infrastructure services during development.

---

# 🐛 Troubleshooting

## MySQL Connection Error

Check that the infrastructure containers are running:

```bash
docker compose ps
docker compose logs mysql
```

Verify the database settings in `.env`.

## ChromaDB Issues

Check the ChromaDB container:

```bash
docker compose ps
docker compose logs chromadb
```

If the vector store needs to be rebuilt, re-run the project's RAG initialization
process if the corresponding management command is available.

## Google Gemini API Key Error

Verify that `GOOGLE_API_KEY` is present in `.env` and that the key is valid.

## Voice Commands Not Working

Check the configured voice-command settings in the Django admin panel and
verify that the command vocabulary contains the expected Thai or English
keywords.

---

# 🔮 Future Improvements

Potential improvements include:

-  Containerizing the Django application 
-  Implementing CI/CD with GitHub Actions 
-  Automated testing in CI 
-  Security and dependency scanning 
-  Production monitoring 
-  Centralized logging 
-  Database backup and recovery 
-  Cloud deployment 
-  Container orchestration when required

---

# 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Google AI Documentation](https://ai.google.dev/)
- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Stripe API Documentation](https://stripe.com/docs/api)

---

# 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

# 👤 Author

**Mr. Supachai Taengyonram**

Senior Project — AI CASHIER
