#!/bin/bash
# Dreamwell Assessment - WSL Linux Setup Script

set -e  # Exit on error

echo "🚀 Dreamwell Assessment - WSL Setup"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "mcp_server.py" ] || [ ! -f "backend_main.py" ]; then
    echo "❌ Error: Please run this script from the dreamwell_assessment directory"
    exit 1
fi

# Step 1: Python Setup
echo "📦 Step 1: Setting up Python virtual environment..."
if [ -d "venv" ]; then
    echo "   ℹ️  Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
fi

# Activate venv and install dependencies
echo "   📥 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "   ✅ Python dependencies installed"

# Step 2: Create .env file if it doesn't exist
echo ""
echo "🔑 Step 2: Configuring environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# API Keys
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
EOF
    echo "   ✅ .env file created (edit with your API keys)"
else
    echo "   ℹ️  .env file already exists"
fi

# Step 3: Node.js and Frontend Setup
echo ""
echo "🎨 Step 3: Setting up Frontend..."

# Check Node version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    echo "   Node.js version: $(node -v)"
    
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo "   ⚠️  Warning: Node.js 18+ recommended (you have $NODE_VERSION)"
    fi
else
    echo "   ❌ Node.js not found. Please install Node.js 20 LTS:"
    echo "      curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "      sudo apt-get install -y nodejs"
    exit 1
fi

# Install frontend dependencies
cd frontend
echo "   📥 Installing frontend dependencies (this may take a minute)..."
npm install
echo "   ✅ Frontend dependencies installed"
cd ..

# Step 4: Verify data files
echo ""
echo "📁 Step 4: Verifying data files..."
for file in "data/email_fixtures.json" "data/youtube_profiles.json" "data/brand_profiles.json"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
    fi
done

# Step 5: Create helper scripts
echo ""
echo "🛠️  Step 5: Creating helper scripts..."

# Start backend script
cat > start_backend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "🚀 Starting FastAPI backend on http://localhost:8000"
python backend_main.py
EOF
chmod +x start_backend.sh
echo "   ✅ Created start_backend.sh"

# Start frontend script
cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
echo "🎨 Starting React frontend on http://localhost:5173"
npm run dev
EOF
chmod +x start_frontend.sh
echo "   ✅ Created start_frontend.sh"

# Start both script
cat > start_all.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup INT TERM

# Start backend
echo "🚀 Starting backend..."
./start_backend.sh > logs/backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

# Check if backend started
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check logs/backend.log"
    exit 1
fi
echo "✅ Backend running (PID: $BACKEND_PID)"

# Start frontend
echo "🎨 Starting frontend..."
./start_frontend.sh > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 3

# Check if frontend started
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start. Check logs/frontend.log"
    kill $BACKEND_PID
    exit 1
fi
echo "✅ Frontend running (PID: $FRONTEND_PID)"

echo ""
echo "✅ All services running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
wait
EOF
chmod +x start_all.sh
echo "   ✅ Created start_all.sh"

# Test API script
cat > test_api.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing API endpoints..."
echo ""

# Test health check
echo "1. Testing health check..."
HEALTH=$(curl -s http://localhost:8000/)
if echo "$HEALTH" | grep -q "ok"; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed"
    echo "   Make sure backend is running: ./start_backend.sh"
    exit 1
fi

# Test emails endpoint
echo "2. Testing emails endpoint..."
EMAILS=$(curl -s http://localhost:8000/api/emails)
if echo "$EMAILS" | grep -q "success"; then
    COUNT=$(echo "$EMAILS" | grep -o '"thread_id"' | wc -l)
    echo "   ✅ Emails endpoint working (found $COUNT emails)"
else
    echo "   ❌ Emails endpoint failed"
    exit 1
fi

# Test specific email
echo "3. Testing specific email thread..."
THREAD=$(curl -s http://localhost:8000/api/emails/thread_001)
if echo "$THREAD" | grep -q "success"; then
    echo "   ✅ Email thread endpoint working"
else
    echo "   ❌ Email thread endpoint failed"
    exit 1
fi

echo ""
echo "✅ All tests passed!"
EOF
chmod +x test_api.sh
echo "   ✅ Created test_api.sh"

# Create logs directory
mkdir -p logs
echo "   ✅ Created logs directory"

# Step 6: Final summary
echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Edit .env file with your API keys (optional for Day 1):"
echo "   nano .env"
echo ""
echo "2. Start the application:"
echo "   ./start_all.sh          # Start both backend and frontend"
echo "   # OR start separately:"
echo "   ./start_backend.sh      # Just backend"
echo "   ./start_frontend.sh     # Just frontend"
echo ""
echo "3. Test the API:"
echo "   ./test_api.sh"
echo ""
echo "4. Access the application:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "📚 Documentation:"
echo "   - README.md              - Full project documentation"
echo "   - IMPLEMENTATION_PLAN.md - 4-day implementation plan"
echo "   - CLAUDE.md              - Architecture rules"
echo ""
echo "🎯 Current Status: Day 1 Complete (Backend 100%, Frontend 100%)"
echo ""

