import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

function App() {
    const [imageUrl, setImageUrl] = useState('');
    const [guess, setGuess] = useState('');
    const [history, setHistory] = useState([]);
    const [message, setMessage] = useState({ text: '', type: 'info' });
    const [gameWon, setGameWon] = useState(false);
    const [guessCount, setGuessCount] = useState(0);
    const [totalWords, setTotalWords] = useState(0);
    const [guessedWords, setGuessedWords] = useState(new Set());
    const [leaderboard, setLeaderboard] = useState([]);
    const [showUsernameModal, setShowUsernameModal] = useState(false);
    const [username, setUsername] = useState('');
    const [finalRank, setFinalRank] = useState(null);
    const [lastGameSessionId, setLastGameSessionId] = useState(null);
    const [copyButtonText, setCopyButtonText] = useState('Share');
    const [loading, setLoading] = useState(true);
    const [loadingMessage, setLoadingMessage] = useState('Loading game...');
    const inputRef = useRef(null);

    const isInputDisabled = gameWon;

    const [showStatsModal, setShowStatsModal] = useState(false);
    const [stats, setStats] = useState({ played: 0, streak: 0, distribution: {} });
    const [nextGameTime, setNextGameTime] = useState(null);
    const [timeRemaining, setTimeRemaining] = useState('');


    useEffect(() => {
        // Load stats from local storage
        const savedStats = JSON.parse(localStorage.getItem('pixeloStats')) || { played: 0, streak: 0, distribution: {} };
        setStats(savedStats);

        const loadInitialData = async () => {
            const timeoutId = setTimeout(() => {
                setLoadingMessage('Waking up the server... this might take a minute (free tier hosting 😅)');
            }, 3000);

            try {
                // Fetch game data and leaderboard concurrently
                const [gameResponse, leaderboardResponse] = await Promise.all([
                    fetch(`${API_BASE_URL}/api/game/today`),
                    fetch(`${API_BASE_URL}/api/leaderboard/today`)
                ]);

                clearTimeout(timeoutId);

                if (!gameResponse.ok) {
                    const errorData = await gameResponse.json();
                    throw new Error(errorData.detail || "Could not load today's game.");
                }
                const gameData = await gameResponse.json();
                setImageUrl(`${API_BASE_URL}${gameData.imageUrl}`);
                setTotalWords(gameData.totalWords);

                // Check if already played today
                const lastCompleted = localStorage.getItem('pixelo_last_completed');
                const todayStr = new Date().toDateString();

                if (lastCompleted === todayStr) {
                    setGameWon(true);
                    setMessage({ text: 'You have already completed today\'s Pixelo!', type: 'info' });
                    setCopyButtonText('Share Result');
                }

                if (leaderboardResponse.ok) {
                    const leaderboardData = await leaderboardResponse.json();
                    setLeaderboard(leaderboardData);
                }
            } catch (error) {
                clearTimeout(timeoutId);
                setMessage({ text: `Error: ${error.message}`, type: 'error' });
            } finally {
                setLoading(false);
            }
        };
        loadInitialData();

        const savedUsername = localStorage.getItem('pixeloUsername');
        if (savedUsername) setUsername(savedUsername);

        // Setup countdown to midnight
        const now = new Date();
        const tomorrow = new Date(now);
        tomorrow.setHours(24, 0, 0, 0);
        setNextGameTime(tomorrow);

        const timer = setInterval(() => {
            const now = new Date();
            const tomorrow = new Date(now);
            tomorrow.setHours(24, 0, 0, 0);
            const diff = tomorrow - now;

            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            setTimeRemaining(`${hours}h ${minutes}m ${seconds}s`);
        }, 1000);

        return () => clearInterval(timer);
    }, []);

    const handleGuessSubmit = async (e) => {
        e.preventDefault();
        if (isInputDisabled || !guess.trim()) return;

        const wordToGuess = guess.trim().toLowerCase();

        if (guessedWords.has(wordToGuess)) {
            setMessage({ text: 'You already guessed that word!', type: 'error' });
            setGuess('');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/game/guess`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ word: wordToGuess }),
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Server error occurred.');
            }

            if (result.status === 'not_in_list') {
                setMessage({ text: result.message, type: 'error' });
            } else if (result.status === 'found') {
                const newGuessCount = guessCount + 1;
                setGuessCount(newGuessCount);
                setGuessedWords(new Set(guessedWords).add(wordToGuess));

                const newHistory = [{ word: wordToGuess, rank: result.rank }, ...history];
                newHistory.sort((a, b) => a.rank - b.rank);
                setHistory(newHistory);

                setMessage({ text: '', type: 'info' });

                if (result.isCorrect) {
                    const newSessionId = crypto.randomUUID();
                    setLastGameSessionId(newSessionId);

                    // Calculate potential rank based on the current leaderboard
                    const potentialRank = leaderboard.filter(e => e.score <= newGuessCount).length + 1;
                    setFinalRank(potentialRank);

                    setGameWon(true);
                    setMessage({ text: `Congratulations! You guessed it in ${newGuessCount} tries!`, type: 'win' });
                    setShowUsernameModal(true);

                    // Update Stats & Daily Limit
                    const todayStr = new Date().toDateString();
                    localStorage.setItem('pixelo_last_completed', todayStr);

                    const newStats = { ...stats };
                    newStats.played += 1;
                    newStats.streak += 1; // Simple streak logic
                    localStorage.setItem('pixeloStats', JSON.stringify(newStats));
                    setStats(newStats);
                }
            }
        } catch (error) {
            setMessage({ text: `Error: ${error.message}`, type: 'error' });
        } finally {
            setGuess('');
            inputRef.current.focus();
        }
    };

    const handleShare = () => {
        const shareText = `I completed today's Pixelo in ${guessCount} guesses. ✏️\nWin Streak: ${stats.streak}\nPlay now: ${window.location.origin}`;
        navigator.clipboard.writeText(shareText).then(() => {
            setCopyButtonText('Copied!');
            setTimeout(() => setCopyButtonText('Share'), 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            alert('Could not copy score to clipboard.');
        });
    };

    const handleUsernameSubmit = async (e) => {
        e.preventDefault();
        const finalUsername = username.trim();
        if (!finalUsername) return;

        try {
            const response = await fetch(`${API_BASE_URL}/api/leaderboard/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: finalUsername, score: guessCount, sessionId: lastGameSessionId }),
            });
            const updatedLeaderboard = await response.json();
            if (response.ok) {
                localStorage.setItem('pixeloUsername', finalUsername);
                setLeaderboard(updatedLeaderboard);
                setShowUsernameModal(false);
            } else {
                throw new Error('Failed to submit score.');
            }
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    };

    const getRankColor = useCallback((rank) => {
        if (rank === 0) return 'var(--rank-win)';
        if (!totalWords) return 'var(--rank-bad)';

        const percentile = rank / totalWords;

        if (percentile <= 0.1) return 'var(--rank-good)';
        if (percentile <= 0.5) return 'var(--rank-medium)';
        return 'var(--rank-bad)';
    }, [totalWords]);

    const currentUserRank = lastGameSessionId ? leaderboard.findIndex(entry => entry.sessionId === lastGameSessionId) : -1;
    const top10Leaderboard = leaderboard.slice(0, 10);

    return (
        <>
            {showUsernameModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2>You won!</h2>
                        {finalRank && (
                            <p>Your rank today is <strong className="font-numeric highlight-rank">{finalRank}</strong>!</p>
                        )}
                        <p>Add your name to the leaderboard.</p>
                        <form onSubmit={handleUsernameSubmit}>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Enter your name"
                                maxLength="20"
                                required
                                autoFocus
                            />
                            <div className="modal-button-group">
                                <button type="submit">Submit Score</button>
                                <button type="button" className="share-button" onClick={handleShare}>
                                    {copyButtonText}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
            <div className="app-layout">
                {/* Left Column: Leaderboard */}
                <div className="side-column leaderboard-column">
                    <h2>Leaderboard</h2>
                    {leaderboard.length > 0 ? (
                        <ol className="leaderboard-list">
                            {top10Leaderboard.map((entry, index) => (
                                <li key={entry.sessionId || `${entry.username}-${index}`} className={currentUserRank === index ? 'current-user' : ''}>
                                    <span className="leaderboard-rank font-numeric">{index + 1}.</span>
                                    <span className="leaderboard-name">{entry.username}{index === 0 && ' 🏆'}</span>
                                    <span className="leaderboard-score font-numeric">{entry.score}</span>
                                </li>
                            ))}
                        </ol>
                    ) : (
                        <p className="no-scores">No scores yet today.</p>
                    )}
                </div>

                {/* Middle Column: Game */}
                <div className="main-column">
                    <div className="container">
                        <header>
                            <h1>Pixelo</h1>
                        </header>
                        <main>
                            {loading ? (
                                <div className="loading-container">
                                    <p>{loadingMessage}</p>
                                </div>
                            ) : (
                                <>
                                    <div className="image-container">
                                        {imageUrl ? <img id="doodle-image" src={imageUrl} alt="A.I. generated doodle" /> : <p>Loading image...</p>}
                                    </div>
                                    <div className="game-interface">
                                        {gameWon ? (
                                            <div className="game-won-container">
                                                <div className="next-game-timer">
                                                    <p>Next Pixelo in:</p>
                                                    <div className="timer-display font-numeric">{timeRemaining}</div>
                                                </div>
                                                <button type="button" className="share-button-main" onClick={handleShare}>
                                                    {copyButtonText}
                                                </button>
                                            </div>
                                        ) : (
                                            <form id="guess-form" onSubmit={handleGuessSubmit}>
                                                <input type="text" id="guess-input" ref={inputRef} value={guess} onChange={(e) => setGuess(e.target.value)} placeholder="Type your guess..." autoComplete="off" required disabled={isInputDisabled} />
                                                <button type="submit" disabled={isInputDisabled}>Guess</button>
                                            </form>
                                        )}
                                        <div id="message-area" className={`message-${message.type}`}>{message.text}</div>
                                    </div>
                                    <div className="guess-counter" style={{ visibility: (guessCount > 0 && !gameWon) ? 'visible' : 'hidden' }}>
                                        Guesses: <span className="font-numeric">{guessCount}</span>
                                    </div>
                                </>
                            )}
                        </main>
                    </div>
                </div>

                {/* Right Column: History */}
                <div className="side-column history-column">
                    <div className="history-container">
                        <h2>History</h2>
                        <div className="history-header" style={{ visibility: history.length > 0 ? 'visible' : 'hidden' }}>
                            <span className="col-word">Word</span>
                            <span className="col-rank">Rank</span>
                        </div>
                        <ul id="history-list">
                            {history.map((item) => (
                                <li key={item.word}><span className="history-item-word"><span className="rank-color-indicator" style={{ backgroundColor: getRankColor(item.rank) }}></span>{item.word}</span><span className="history-item-rank font-numeric" style={{ color: getRankColor(item.rank) }}>{item.rank === 0 ? 'Correct!' : item.rank}</span></li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </>
    );
}

export default App;
