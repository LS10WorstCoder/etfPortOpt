# Portfolio Analyzer & Optimizer

**Educational portfolio analysis and optimization platform using Modern Portfolio Theory**

⚠️ **DISCLAIMER**: This tool is for educational purposes only. It does not provide personalized investment advice. Always consult with a qualified financial advisor before making investment decisions.

---

## 📊 Overview

A full-stack web application that analyzes investment portfolios and provides data-driven optimization recommendations. Users manually input their holdings, and the system provides:

- **6 Risk Metrics**: Total value, annual return, volatility, Sharpe ratio, max drawdown, VaR 95%
- **Portfolio Optimization**: 3 strategies (max Sharpe, min volatility, equal weight) with optional weight constraints
- **Market Data Integration**: Real-time prices and historical data via yfinance
- **CSV Import/Export**: Bulk upload and download holdings
- **Smart Caching**: 1-hour cache with automatic invalidation

**Key Features:**
- ✅ Manual portfolio entry with fractional shares support
- ✅ Deep analytics with 6 risk metrics + correlation matrix
- ✅ scipy-based optimization (SLSQP algorithm)
- ✅ CSV import/export for bulk operations
- ✅ PostgreSQL caching for performance
- ✅ Supabase authentication & database
- ❌ No trading capabilities
- ❌ No brokerage connections
- ❌ No payment processing

---

## 🛠 Tech Stack

### Backend (Complete ✅)
- **FastAPI** - Modern Python web framework with auto-docs
- **Supabase** - PostgreSQL database + authentication
- **SQLAlchemy** - ORM with UUID primary keys
- **yfinance** - Yahoo Finance API wrapper for market data
- **scipy** - Portfolio optimization (SLSQP algorithm)
- **numpy/pandas** - Financial calculations and time series analysis

### Frontend (Planned)
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Shadcn/UI** - Accessible component library
- **Supabase Client** - Auth helpers

---

## 🚀 API Endpoints (23 Total)

### **Authentication (2)**
- `POST /api/register` - Create account via Supabase
- `POST /api/login` - Login via Supabase

### **Portfolios (5)**
- `POST /api/portfolios/` - Create portfolio
- `GET /api/portfolios/` - List user's portfolios
- `GET /api/portfolios/{id}` - Get portfolio details
- `PUT /api/portfolios/{id}` - Update portfolio
- `DELETE /api/portfolios/{id}` - Delete portfolio

### **Holdings (5)**
- `POST /api/portfolios/{id}/holdings/` - Add holding (max 100)
- `GET /api/portfolios/{id}/holdings/` - List holdings
- `GET /api/portfolios/{id}/holdings/{holding_id}` - Get holding
- `PUT /api/portfolios/{id}/holdings/{holding_id}` - Update holding
- `DELETE /api/portfolios/{id}/holdings/{holding_id}` - Delete holding

### **Market Data (4)**
- `GET /api/market/validate/{ticker}` - Validate ticker exists
- `GET /api/market/price/{ticker}` - Get current price
- `GET /api/market/info/{ticker}` - Get company info
- `GET /api/market/historical/{ticker}` - Get price history

### **Analytics (2)**
- `POST /api/portfolios/{id}/analyze` - Calculate 6 risk metrics (cached 1 hour)
- `GET /api/portfolios/{id}/analytics/history` - Get historical analyses

### **Optimization (2)**
- `POST /api/portfolios/{id}/optimize` - Optimize allocation (3 strategies)
- `GET /api/portfolios/{id}/optimizations/history` - Get past optimizations

### **CSV Import/Export (2)**
- `POST /api/portfolios/{id}/import` - Bulk import from CSV
- `GET /api/portfolios/{id}/export` - Download as CSV

**Interactive Docs:** http://localhost:8000/docs

---

## 📈 Risk Metrics Explained

### **1. Annual Return**
- Expected yearly return based on historical performance
- Formula: `(mean daily return) × 252 trading days`

### **2. Volatility**
- Annualized standard deviation (risk measure)
- Formula: `(daily std dev) × √252`

### **3. Sharpe Ratio**
- Risk-adjusted return (return per unit of risk)
- Formula: `(return - 4% risk-free rate) / volatility`

### **4. Max Drawdown**
- Worst peak-to-trough decline in portfolio value
- Example: -25% means portfolio lost 25% from peak

### **5. VaR 95%**
- Daily loss threshold not exceeded 95% of days
- Example: -2.5% means 95% of days lose less than 2.5%

### **6. Correlation Matrix**
- Shows how assets move together (-1 to +1)
- Lower correlation = better diversification

---

## ⚙️ Optimization Strategies

### **Max Sharpe Ratio**
Finds allocation with best risk-adjusted return using scipy's SLSQP algorithm.

**Math:**
```
Maximize: (Portfolio Return - 4%) / Portfolio Volatility
Subject to: Σ weights = 1, 0 ≤ weight ≤ 1
```

### **Min Volatility**
Finds lowest-risk allocation (conservative strategy).

**Math:**
```
Minimize: √(w^T × Σ × w)
Subject to: Σ weights = 1, 0 ≤ weight ≤ 1
```

### **Equal Weight**
Naive diversification baseline (1/N allocation).

**Optional Weight Constraints:**
```json
{
  "constraints": {
    "AAPL": {"min": 0.2, "max": 0.4},
    "MSFT": {"min": 0.1, "max": 0.3}
  }
}
```

---

## 🗄 Database Schema

**5 PostgreSQL Tables:**

1. **users** - User accounts (syncs with Supabase auth)
2. **portfolios** - Portfolio containers (name, description)
3. **holdings** - Individual asset positions (ticker, quantity, cost)
4. **portfolio_analytics** - Cached analysis results (1-hour TTL)
5. **optimization_results** - Historical optimization records

**Key Features:**
- UUID primary keys (non-sequential, secure)
- Foreign key constraints with CASCADE DELETE
- Unique constraints (portfolio/ticker, portfolio/date)
- Timestamp tracking (created_at, updated_at)
- NUMERIC precision for financial data

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Supabase account
- Node.js 18+ (for frontend, coming soon)

### Backend Setup

1. **Clone repository:**
```bash
git clone https://github.com/LS10WorstCoder/etfPortOpt.git
cd etfPortOpt/backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
```

Edit `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.your-project.supabase.co:5432/postgres
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

5. **Run application:**
```bash
python main.py
```

Backend runs at: http://localhost:8000  
API docs: http://localhost:8000/docs

### Frontend Setup
(Coming in Phase 2 - Next.js 14 with TypeScript)

---

## 📁 Project Structure

```
etfPortOpt/
├── backend/                    # FastAPI backend (1,938 lines)
│   ├── api/                   # API route handlers (882 lines)
│   │   ├── auth.py           # Authentication (2 endpoints)
│   │   ├── portfolios.py     # Portfolio CRUD (5 endpoints)
│   │   ├── holdings.py       # Holdings CRUD (5 endpoints)
│   │   ├── market.py         # Market data (4 endpoints)
│   │   ├── analytics.py      # Analysis (2 endpoints)
│   │   ├── optimization.py   # Optimization (2 endpoints)
│   │   └── csv_import.py     # CSV I/O (2 endpoints)
│   ├── models/               # SQLAlchemy models (120 lines)
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   ├── holding.py
│   │   ├── analytics.py
│   │   └── optimization.py
│   ├── schemas/              # Pydantic schemas (100 lines)
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   ├── holding.py
│   │   └── csv.py
│   ├── services/             # Business logic (661 lines)
│   │   ├── market_data.py           # yfinance wrapper
│   │   ├── portfolio_analyzer.py   # Risk metrics
│   │   └── portfolio_optimizer.py  # scipy optimization
│   ├── utils/                # Shared utilities (46 lines)
│   │   ├── financial.py             # Constants & formulas
│   │   └── portfolio_utils.py       # Reusable helpers
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Pydantic settings
│   ├── database.py           # SQLAlchemy setup
│   └── requirements.txt      # 15 dependencies
│
├── frontend/                 # Next.js 14 (coming soon)
├── .gitignore
└── README.md
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | Public anon key | `eyJhbGc...` |
| `SUPABASE_SERVICE_KEY` | Admin service key | `eyJhbGc...` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://...` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `http://localhost:3000` |
| `ENVIRONMENT` | Environment mode | `development` or `production` |

### Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `TRADING_DAYS_PER_YEAR` | 252 | Annualization factor |
| `RISK_FREE_RATE` | 0.04 (4%) | Sharpe ratio baseline |
| `MAX_HOLDINGS` | 100 | Holdings per portfolio limit |
| `CACHE_TTL` | 1 hour | Analytics cache duration |

---

## 🧪 Testing

**Manual Testing via Swagger UI:**
1. Start backend: `python main.py`
2. Open: http://localhost:8000/docs
3. Register user → Login → Create portfolio → Add holdings → Analyze

**Example cURL:**
```bash
# Register
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'

# Analyze portfolio
curl -X POST http://localhost:8000/api/portfolios/123/analyze?period=1y \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔒 Security

- ✅ Supabase authentication (JWT tokens)
- ✅ User ownership validation on all endpoints
- ✅ Input validation via Pydantic schemas
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ CORS configuration
- ✅ No brokerage API connections
- ✅ No storage of sensitive credentials
- ✅ UUID primary keys (non-guessable)

---

## 📊 Performance Optimizations

### **Caching Strategy**
- **Analytics caching:** 1-hour TTL using PostgreSQL
- **Event-based invalidation:** Auto-clear cache when holdings change
- **600x speedup:** 4-6s → 10ms for cached requests

### **Data Reuse**
- Optimizer reuses Analyzer's `calculate_returns()`
- Shared financial utilities eliminate duplicate code
- Lazy analyzer initialization in optimizer

### **Database Optimizations**
- Indexed foreign keys
- Unique constraints prevent duplicates
- CASCADE DELETE reduces orphaned records

---

## 🗺 Development Roadmap

### Phase 1: Backend (✅ Complete)
- [x] Supabase integration
- [x] Portfolio CRUD API
- [x] Holdings CRUD API
- [x] Market data integration (yfinance)
- [x] Analysis engine (6 metrics)
- [x] Optimization engine (3 strategies)
- [x] CSV import/export
- [x] Smart caching system

### Phase 2: Frontend (🔄 In Progress)
- [ ] Next.js 14 setup
- [ ] Supabase auth integration
- [ ] Portfolio management UI
- [ ] Holdings input forms
- [ ] Analytics dashboard
- [ ] Optimization results display
- [ ] CSV upload/download
- [ ] Responsive design

### Phase 3: Polish (📋 Planned)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Error monitoring
- [ ] Performance profiling
- [ ] Documentation
- [ ] Deployment (Vercel + Supabase)

---

## 📖 API Documentation

**Interactive Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

**Example Requests:**

```python
import requests

# Login
response = requests.post("http://localhost:8000/api/login", json={
    "email": "user@example.com",
    "password": "password123"
})
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Create portfolio
portfolio = requests.post(
    "http://localhost:8000/api/portfolios/",
    headers=headers,
    json={"name": "My Portfolio", "description": "Tech stocks"}
).json()

# Add holdings
requests.post(
    f"http://localhost:8000/api/portfolios/{portfolio['id']}/holdings/",
    headers=headers,
    json={"ticker": "AAPL", "quantity": 10, "average_cost": 150.50}
)

# Analyze
analysis = requests.post(
    f"http://localhost:8000/api/portfolios/{portfolio['id']}/analyze?period=1y",
    headers=headers
).json()

print(f"Sharpe Ratio: {analysis['sharpe_ratio']}")
print(f"Volatility: {analysis['volatility']:.2%}")
```

---

## ⚠️ Legal Disclaimers

**Important:**
- This tool provides **educational information only**
- **Not personalized investment advice**
- Cannot execute trades or access brokerage accounts
- No guarantee of accuracy or results
- Users are **solely responsible** for investment decisions
- Past performance does not guarantee future results
- Consult a qualified financial advisor before investing

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📧 Support

- **Issues:** [GitHub Issues](https://github.com/LS10WorstCoder/etfPortOpt/issues)
- **Discussions:** [GitHub Discussions](https://github.com/LS10WorstCoder/etfPortOpt/discussions)

---

**Built with ❤️ using Modern Portfolio Theory**
