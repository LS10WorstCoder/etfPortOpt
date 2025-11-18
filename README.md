# Portfolio Analyzer & Optimizer

**Educational portfolio analysis and optimization recommendations platform**

⚠️ **DISCLAIMER**: This tool is for educational purposes only. It does not provide personalized investment advice and cannot execute trades. Always consult with a qualified financial advisor before making investment decisions.

## Overview

Portfolio Analyzer is a read-only web application that helps investors analyze their existing portfolios and receive optimization recommendations. Users manually input their holdings, and the system provides:

- Deep analytics and risk assessment
- Portfolio optimization suggestions
- Performance visualization
- Correlation analysis

**Key Features:**
- ✅ Manual portfolio entry
- ✅ Risk metrics calculation
- ✅ Optimization recommendations
- ✅ Educational focus
- ❌ No trading capabilities
- ❌ No brokerage connections
- ❌ No payment processing

## Tech Stack

### Backend
- **FastAPI** - Python web framework
- **PostgreSQL** - Database
- **Redis** - Caching
- **yfinance** - Market data
- **scipy** - Optimization algorithms

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Shadcn/UI** - UI components
- **Recharts** - Data visualization

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd etfPortOpt
```

2. Create environment file:
```bash
cp backend/.env.example backend/.env
# Edit .env and set SECRET_KEY
```

3. Start services:
```bash
docker-compose up -d
```

4. Access the application:
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend: (coming soon)

### Local Development

#### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run the application:
```bash
python main.py
```

#### Frontend Setup
(Coming soon in Phase 2)

## Project Structure

```
etfPortOpt/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Backend container
│   └── .env.example        # Environment template
├── frontend/               # Next.js application (coming soon)
├── docker-compose.yml      # Multi-container setup
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Development Roadmap

- [x] Project setup and infrastructure
- [ ] Database schema and models
- [ ] Authentication system
- [ ] Portfolio CRUD API
- [ ] Market data integration
- [ ] Analysis engine
- [ ] Optimization algorithms
- [ ] Frontend setup
- [ ] UI components
- [ ] Testing suite
- [ ] Deployment

## Security

This application is designed with security in mind:
- No brokerage API connections
- No storage of account credentials
- JWT-based authentication
- Rate limiting
- Input validation and sanitization
- HTTPS enforcement

## Legal

**Important Disclaimers:**
- This tool provides educational information only
- Not personalized investment advice
- Cannot execute trades or access brokerage accounts
- No guarantee of accuracy or results
- Users are solely responsible for investment decisions

See Terms of Service and Privacy Policy for full details.

## License

[License details to be added]

## Contributing

[Contribution guidelines to be added]

## Support

For questions or issues, please [open an issue](repository-issues-url).
