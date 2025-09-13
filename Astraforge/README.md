# 🚀 AstraForge - Space Mission Simulator

An AI-powered, open-source space mission simulator that democratizes space mission planning through an intuitive web interface.

## ⚡ Quick Start

### Option 1: Single Command (Recommended)
```bash
npm start
```

### Option 2: Platform-specific Scripts
**Windows (Command Prompt):**
```cmd
start.bat
```

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Linux/macOS:**
```bash
./start.sh
```

## 🌐 Access Points

Once started, the application will be available at:

- **Frontend (React)**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## 📋 Prerequisites

- **Node.js** >= 18.0.0
- **Python** >= 3.11.0
- **npm** or **yarn**

## 🛠 Development Setup

### First-time Setup
```bash
# Install all dependencies (frontend + backend)
npm run install-all
```

### Available Scripts

- `npm start` - Start both frontend and backend
- `npm run dev` - Same as start (development mode)
- `npm run backend` - Start only the backend
- `npm run frontend` - Start only the frontend
- `npm run build` - Build the frontend for production
- `npm run test` - Run tests for both frontend and backend
- `npm run lint` - Lint both frontend and backend code
- `npm run clean` - Clean build artifacts and cache

## 🏗 Project Structure

```
Astraforge/
├── frontend/          # React + Vite frontend
├── backend/           # FastAPI backend
├── scripts/           # Development scripts
├── package.json       # Root package configuration
└── README.md         # This file
```

## 🔧 Configuration

### Environment Variables

**Backend** (create `backend/.env`):
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/astraforge
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Frontend** (create `frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## 🚀 Features

- ✅ AI-powered mission generation
- ✅ Physics-based simulation engine
- ✅ Interactive 3D visualization
- ✅ Mission optimization algorithms
- ✅ Authentication system
- ✅ Mission gallery and management
- ✅ Real-time mission tracking

## 🧪 Testing

```bash
# Run all tests
npm run test

# Backend tests only
cd backend && python -m pytest

# Frontend tests only
cd frontend && npm run test
```

## 📚 Documentation

- [Backend API Documentation](http://localhost:8000/docs) (when running)
- [Frontend Components](./frontend/README.md)
- [Backend Services](./backend/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `npm run test`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Happy space mission planning! 🌌**