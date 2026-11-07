# Axoora Backend (Django & Django REST Framework)

High-performance, secure backend API powering the **Axoora** sovereign fintech platform and street-level banking website.

Built with **Python 3.12**, **Django 5.1**, **Django REST Framework (DRF)**, **CORS Headers**, and **WhiteNoise**.

---

## 🚀 Quick Start

### 1. Activate the Virtual Environment
A virtual environment has already been created in `.venv`:

```bash
cd backend
source .venv/bin/activate
```

### 2. Verify / Set Environment Variables
The local `.env` is pre-configured with:
```ini
SECRET_KEY=django-insecure-axoora-local-dev-key-9284209384920384
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,https://axoora.ai
```

### 3. Run Migrations & Seed Data
Database migrations and initial seed data are already executed, but you can re-run them anytime:

```bash
# Run database migrations
python manage.py migrate

# Seed CMS, FAQs, articles, products, and sample waitlist leads
python manage.py seed_axoora_data

# Ensure default admin exists (admin / admin123456)
python manage.py create_default_admin
```

### 4. Start the Development Server
```bash
python manage.py runserver 8000
```

The API will be live at `http://127.0.0.1:8000/`.

---

## 🔐 Django Admin Portal
Access the Django Admin at **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)**

- **Username:** `admin`
- **Password:** `admin123456`

From the Django Admin you can:
- Review and filter priority waitlist submissions by interest, status, and location.
- Perform bulk actions: *Mark as Contacted*, *Mark as Approved*, *Dispatch POS Terminal*.
- Edit the announcement ticker and live hero headlines.
- Publish or draft journal articles and FAQ items.
- View and resolve inbound contact and partnership inquiries.

---

## 📡 API Endpoints Reference

### Root & System
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API status and interactive endpoints directory |
| `GET` | `/health/` | Health check endpoint |
| `GET/POST` | `/admin/` | Django Administration Dashboard |

### Waitlist & Leads (`/api/v1/waitlist/`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/waitlist/submit/` | Public waitlist submission (captures phone, interest, city, consent, IP, user-agent) |
| `GET` | `/api/v1/waitlist/leads/` | List leads (filterable by `status`, `interest`, `city`; searchable by name, phone, email) |
| `GET/PUT/PATCH` | `/api/v1/waitlist/leads/<id>/` | View or update lead status and notes |

### Content & CMS (`/api/v1/content/`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/content/hero/` | Active hero headlines and announcement ticker |
| `PUT` | `/api/v1/content/hero/` | Update hero configuration |
| `GET` | `/api/v1/content/articles/` | List published journal articles (filterable by category) |
| `GET` | `/api/v1/content/articles/<slug>/` | Retrieve specific article by slug |
| `GET` | `/api/v1/content/faqs/` | List active resolution desk FAQs |
| `GET` | `/api/v1/content/stories/` | List customer & merchant testimonials |
| `GET` | `/api/v1/content/products/` | Product catalog, pricing, and fee structure |

### Contact & Support (`/api/v1/contact/`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/contact/submit/` | Public support message and partnership pitch submission |
| `GET` | `/api/v1/contact/inquiries/` | List inquiries (filterable by category and status) |
| `GET/PATCH` | `/api/v1/contact/inquiries/<id>/` | Update inquiry status (`new`, `in_review`, `resolved`) |

### Customer Chat, AI Concierge & RAG (`/api/v1/chat/`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat/message/` | Interactive chat message (RAG hybrid retrieval, AI answering & human escalation detection) |
| `POST` | `/api/v1/chat/escalate/` | Explicit customer human escalation (generates ticket and WhatsApp desk link) |
| `GET` | `/api/v1/chat/history/<session_id>/` | Retrieve full chat transcript |
| `POST` | `/api/v1/chat/agent-reply/` | Human agent reply endpoint |
| `GET` | `/api/v1/chat/sessions/` | Staff/Admin list of active customer chats with status filters |
| `POST` | `/api/v1/chat/rag/query/` | Direct RAG Explorer endpoint (returns retrieved chunks, similarity scores & sources) |

---

## 🧠 Retrieval-Augmented Generation (RAG) Architecture

Axoora uses a production **Hybrid RAG Pipeline** designed for financial accuracy and strict grounding:

1. **Knowledge Ingestion**:
   - `KnowledgeDocument`: Full authoritative policy whitepapers, terminal manuals, and terms authored in Markdown.
   - `KnowledgeChunk`: Segmented passages indexed with lexical keywords and vector embeddings.
   - Auto-syncs all FAQs, Journal articles, and Products into the chunk index via:
     ```bash
     python manage.py sync_rag_knowledge
     ```
2. **Hybrid Retrieval**:
   - **Semantic Search**: Vector similarity via `text-embedding-004` (Google Gemini) or `text-embedding-3-small` (OpenAI).
   - **Lexical Index**: BM25/keyword density scoring matching exact domain terminology (e.g., *NIBSS*, *Mudarabah*, *0.4%*, *dual-SIM*).
   - **Combined Score**: `(0.6 * Semantic) + (0.4 * Lexical)`.
3. **Context Grounding & LLM Synthesis**:
   - Synthesizes answers based **strictly** on retrieved Axoora documentation (prevents AI hallucination).
   - Automatically falls back to deterministic RAG synthesis if no external API key is provided, so it runs **100% offline out-of-the-box**.
   - Optional: Add `GEMINI_API_KEY=your_key` or `OPENAI_API_KEY=your_key` in `.env` to unlock live LLM text generation.

---

## 🧪 Running Automated Tests
Run the built-in test suite:

```bash
python manage.py test
```

All 6 test suites cover API status, validation, waitlist creation, content serialization, and contact workflows.

---

---

## 🏛️ Engineering Patterns (DRY & Domain Driven)

1. **Common Module & Mixins (`apps.common.models`)**:
   - `TimestampedModel`: Abstract mixin providing `created_at` and `updated_at` indexing across all models.
   - `ActiveModelMixin`: Abstract mixin providing `is_active` boolean toggle.
   - `UUIDReferenceModel`: Abstract mixin providing immutable UUID reference IDs.
2. **Explicit Enums (`enums.py` per app)**:
   - Uses `models.TextChoices` for clean type-safety, admin choices, and serializer validation (`WaitlistInterest`, `WaitlistStatus`, `ArticleCategory`, `ChatStatus`, etc.).
3. **Explicit Serializers (`serializers.Serializer`)**:
   - Uses `serializers.Serializer` rather than `ModelSerializer` for full control, decoupling representation from storage and preventing hidden side-effects.
4. **Class-based `APIView` Endpoints**:
   - All HTTP handlers inherit directly from DRF's `APIView` with clean `get()`, `post()`, `patch()`, and `delete()` methods.
5. **Model Query Classmethods (Domain Query Pattern)**:
   - Endpoints do NOT write raw ORM queries like `.objects.filter()`.
   - All queries are encapsulated as model `@classmethod` methods (e.g. `WaitlistLead.create_lead()`, `JournalArticle.get_published()`, `ChatSession.get_or_create_session()`), ensuring 100% DRY, reusable, and unit-testable database operations.

---

## 📁 Project Architecture

```
backend/
├── .env                       # Local environment variables
├── .env.example               # Template environment variables
├── .gitignore                 # Python, venv, and SQLite exclusions
├── .venv/                     # Python 3.12 virtual environment
├── README.md                  # Backend documentation
├── manage.py                  # Django management script
├── requirements.txt           # Python package dependencies
├── db.sqlite3                 # SQLite database pre-seeded with Axoora data
├── staticfiles/               # Collected static files for WhiteNoise
├── config/                    # Main Django project configuration
│   ├── settings.py            # DRF, CORS, WhiteNoise, and app settings
│   ├── urls.py                # Root router & endpoint registry
│   ├── asgi.py
│   └── wsgi.py
└── apps/                      # Modular domain applications
    ├── common/                # Shared mixins, pagination & utilities
    │   ├── models.py          # TimestampedModel, ActiveModelMixin, UUIDReferenceModel
    │   └── pagination.py      # Standard pagination for APIViews
    ├── waitlist/              # Waitlist submissions & CRM lead tracking
    │   ├── enums.py           # WaitlistInterest, WaitlistStatus (TextChoices)
    │   ├── models.py          # Uses mixins + @classmethod query helpers
    │   ├── serializers.py    # Explicit serializers.Serializer
    │   ├── views.py          # Class-based APIView endpoints
    │   ├── urls.py
    │   ├── admin.py
    │   └── tests.py
    ├── content/               # CMS, hero config, articles, FAQs, stories
    │   ├── enums.py           # ArticleCategory, FaqCategory, ProductCategory, ProductStatus
    │   ├── models.py          # Uses mixins + @classmethod query helpers
    │   ├── serializers.py    # Explicit serializers.Serializer
    │   ├── views.py          # Class-based APIView endpoints
    │   ├── urls.py
    │   ├── admin.py
    │   ├── tests.py
    │   └── management/commands/
    │       ├── seed_axoora_data.py
    │       └── create_default_admin.py
    ├── contact/               # Customer contact inquiries & partnerships
    │   ├── enums.py           # InquiryCategory, InquiryStatus
    │   ├── models.py          # Uses mixins + @classmethod query helpers
    │   ├── serializers.py    # Explicit serializers.Serializer
    │   ├── views.py          # Class-based APIView endpoints
    │   ├── urls.py
    │   ├── admin.py
    │   └── tests.py
    └── chat/                  # AI Support, RAG & Human Escalation
        ├── enums.py           # ChatStatus, MessageSender, KnowledgeCategory
        ├── models.py          # Uses mixins + @classmethod query helpers
        ├── rag.py             # Hybrid Vector & Lexical RAG Engine
        ├── services.py        # Intent detection & AI responses
        ├── serializers.py    # Explicit serializers.Serializer
        ├── views.py          # Class-based APIView endpoints
        ├── urls.py
        ├── admin.py
        ├── tests.py
        └── management/commands/
            └── sync_rag_knowledge.py
```

