from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import random
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, ARRAY, DateTime, func, select
import os

# Database config - use environment variables for production
import os

# Get database URL from environment variable (Railway will provide this)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres123@localhost:5432/lotto')

# If Railway provides DATABASE_URL, we need to modify it for asyncpg
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://', 1)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
Base = declarative_base()
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class GeneratedNumbers(Base):
    __tablename__ = 'generated_numbers'
    id = Column(Integer, primary_key=True, index=True)
    numbers = Column(ARRAY(Integer), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # Create tables if they don't exist (optional, for dev)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>Lotto Number Generator</title>
            <style>
                body {
                    background: linear-gradient(135deg, #f8ffae 0%, #43c6ac 100%);
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }
                .container {
                    display: flex;
                    gap: 30px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .leaderboard {
                    flex: 0 0 300px;
                    background: rgba(255,255,255,0.9);
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    max-height: 80vh;
                    overflow-y: auto;
                }
                .main-content {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 80vh;
                }
                h1 {
                    color: #333;
                    margin-bottom: 10px;
                    text-shadow: 1px 1px 2px #fff;
                }
                .leaderboard h2 {
                    color: #333;
                    margin-bottom: 15px;
                    text-align: center;
                    font-size: 1.3rem;
                }
                .leaderboard-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    margin: 4px 0;
                    background: rgba(67,198,172,0.1);
                    border-radius: 8px;
                    font-size: 0.9rem;
                }
                .leaderboard-number {
                    font-weight: bold;
                    color: #43c6ac;
                    min-width: 30px;
                }
                .leaderboard-count {
                    color: #666;
                }
                #dates {
                    margin-bottom: 20px;
                    color: #222;
                    font-size: 1.1rem;
                    background: rgba(255,255,255,0.7);
                    padding: 10px 20px;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }
                #numbers {
                    margin-top: 30px;
                    font-size: 2.5rem;
                    letter-spacing: 0.5rem;
                    color: #fff;
                    text-shadow: 2px 2px 8px #43c6ac;
                }
                #last {
                    margin-top: 18px;
                    font-size: 1.1rem;
                    color: #191654;
                    background: rgba(255,255,255,0.7);
                    padding: 8px 18px;
                    border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }
                button {
                    background: #43c6ac;
                    color: #fff;
                    border: none;
                    padding: 15px 40px;
                    border-radius: 30px;
                    font-size: 1.2rem;
                    cursor: pointer;
                    box-shadow: 0 4px 14px rgba(67,198,172,0.2);
                    transition: background 0.3s, transform 0.2s;
                }
                button:hover {
                    background: #191654;
                    transform: scale(1.05);
                }
                .ball {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    background: #fff;
                    color: #43c6ac;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    font-size: 1.5rem;
                    margin: 0 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="leaderboard">
                    <h2>Number Frequency</h2>
                    <div id="leaderboard-content"></div>
                </div>
                <div class="main-content">
                    <h1>Lotto Number Generator</h1>
                    <div id="dates">
                        <span id="today"></span><br/>
                        <span id="next-draw"></span>
                    </div>
                    <button onclick="generateNumbers()">Generate Numbers</button>
                    <div id="numbers"></div>
                    <div id="history"></div>
                </div>
            </div>
            <script>
                // Load and display leaderboard
                async function loadLeaderboard() {
                    try {
                        const response = await fetch('/leaderboard');
                        const data = await response.json();
                        const leaderboardDiv = document.getElementById('leaderboard-content');
                        leaderboardDiv.innerHTML = data.leaderboard.map(([num, count]) => 
                            `<div class="leaderboard-item">
                                <span class="leaderboard-number">${num}</span>
                                <span class="leaderboard-count">${count} times</span>
                            </div>`
                        ).join('');
                    } catch (error) {
                        console.error('Error loading leaderboard:', error);
                        document.getElementById('leaderboard-content').innerHTML = '<p>Error loading leaderboard</p>';
                    }
                }

                // Display today's date
                const today = new Date();
                document.getElementById('today').innerText = `Today: ${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;

                // Calculate next Saturday (Lotto draw day)
                function getNextSaturday(date) {
                    const result = new Date(date);
                    result.setDate(date.getDate() + ((6 - date.getDay() + 7) % 7 || 7));
                    return result;
                }
                const nextDraw = getNextSaturday(today);
                document.getElementById('next-draw').innerText = `Next Lotto Draw: ${nextDraw.getFullYear()}-${String(nextDraw.getMonth()+1).padStart(2,'0')}-${String(nextDraw.getDate()).padStart(2,'0')}`;

                // Show all generated numbers from localStorage (history)
                function showHistory() {
                    const history = JSON.parse(localStorage.getItem('lottoHistory') || '[]');
                    const historyDiv = document.getElementById('history');
                    if (history.length > 0) {
                        historyDiv.innerHTML = '<b>History:</b><br>' + history.map((nums, idx) => {
                            return `<div style="margin:6px 0;"><span style="font-size:0.95em;color:#888;">#${history.length-idx}</span> ` + nums.map(num => `<span class="ball">${num}</span>`).join('') + '</div>';
                        }).join('');
                    } else {
                        historyDiv.innerHTML = '';
                    }
                }
                showHistory();
                loadLeaderboard();

                async function generateNumbers() {
                    const response = await fetch('/numbers');
                    const data = await response.json();
                    const numbersDiv = document.getElementById('numbers');
                    numbersDiv.innerHTML = '';
                    data.numbers.forEach(num => {
                        const ball = document.createElement('span');
                        ball.className = 'ball';
                        ball.textContent = num;
                        numbersDiv.appendChild(ball);
                    });
                    // Save to localStorage (history)
                    let history = JSON.parse(localStorage.getItem('lottoHistory') || '[]');
                    history.unshift(data.numbers); // add to front (most recent first)
                    localStorage.setItem('lottoHistory', JSON.stringify(history));
                    showHistory();
                    // Refresh leaderboard after generating new numbers
                    loadLeaderboard();
                }
            </script>
        </body>
    </html>
    """

@app.get("/numbers")
async def get_numbers():
    numbers = random.sample(range(1, 46), 6)
    numbers.sort()
    # Save to DB
    async with async_session() as session:
        new_entry = GeneratedNumbers(numbers=numbers)
        session.add(new_entry)
        await session.commit()
    return {"numbers": numbers}

@app.get("/leaderboard")
async def leaderboard():
    # Count frequency of each number 1-45
    async with async_session() as session:
        result = await session.execute(select(GeneratedNumbers.numbers))
        all_numbers = []
        for row in result.scalars():
            all_numbers.extend(row)
        freq = {i: 0 for i in range(1, 46)}
        for num in all_numbers:
            freq[num] += 1
        # Sort by frequency, then by number
        leaderboard = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
        return JSONResponse({"leaderboard": leaderboard})