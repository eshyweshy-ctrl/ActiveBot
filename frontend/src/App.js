import { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";
import TradeHistory from "./pages/TradeHistory";
import Navigation from "./components/Navigation";
import Login from "./pages/Login";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API,
  timeout: 30000,
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [botStatus, setBotStatus] = useState({
    is_running: false,
    config: {
      trade_size_usdc: 10,
      assets_enabled: ["BTC", "ETH", "SOL"],
      dry_run_mode: true,
      telegram_enabled: false,
    },
  });
  const [stats, setStats] = useState({
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    open_trades: 0,
    total_pnl: 0,
    win_rate: 0,
    best_trade: 0,
    worst_trade: 0,
  });
  const [sentiment, setSentiment] = useState({
    BTC: { score: 50, signal: "HOLD" },
    ETH: { score: 50, signal: "HOLD" },
    SOL: { score: 50, signal: "HOLD" },
  });
  const [trades, setTrades] = useState([]);
  const [pnlHistory, setPnlHistory] = useState([]);
  const [systemStatus, setSystemStatus] = useState({
    cfgi_api: "unknown",
    polymarket_api: "unknown",
    mongodb: "unknown",
    telegram: "unknown",
  });
  const [walletInfo, setWalletInfo] = useState({
    address: null,
    address_short: null,
    usdc_balance: 0,
    matic_balance: 0,
    positions_value: 0,
    total_value: 0,
  });
  const [loading, setLoading] = useState(true);

  // Check if already logged in
  useEffect(() => {
    const savedAuth = localStorage.getItem("activebot_auth");
    if (savedAuth === "true") {
      setIsAuthenticated(true);
    }
    setCheckingAuth(false);
  }, []);

  const handleLogin = async (password) => {
    try {
      const response = await api.post("/auth/login", { password });
      if (response.data.authenticated) {
        setIsAuthenticated(true);
        localStorage.setItem("activebot_auth", "true");
        return true;
      }
    } catch (error) {
      return false;
    }
    return false;
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem("activebot_auth");
  };

  const fetchData = useCallback(async () => {
    if (!isAuthenticated) return;
    
    try {
      const [statusRes, statsRes, sentimentRes, tradesRes, pnlRes, sysStatusRes, walletRes] = await Promise.all([
        api.get("/bot/status"),
        api.get("/stats"),
        api.get("/sentiment/current"),
        api.get("/trades?limit=20"),
        api.get("/stats/pnl-history"),
        api.get("/system/status"),
        api.get("/wallet/info"),
      ]);

      setBotStatus(statusRes.data);
      setStats(statsRes.data);
      setSentiment(sentimentRes.data);
      setTrades(tradesRes.data);
      setPnlHistory(pnlRes.data);
      setSystemStatus(sysStatusRes.data);
      setWalletInfo(walletRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
      const interval = setInterval(fetchData, 10000);
      return () => clearInterval(interval);
    }
  }, [fetchData, isAuthenticated]);

  const startBot = async () => {
    try {
      await api.post("/bot/start");
      toast.success("Bot started successfully");
      fetchData();
    } catch (error) {
      toast.error("Failed to start bot");
    }
  };

  const stopBot = async () => {
    try {
      await api.post("/bot/stop");
      toast.success("Bot stopped");
      fetchData();
    } catch (error) {
      toast.error("Failed to stop bot");
    }
  };

  const updateConfig = async (config) => {
    try {
      await api.put("/config", config);
      toast.success("Configuration updated");
      fetchData();
    } catch (error) {
      toast.error("Failed to update configuration");
    }
  };

  const testTelegram = async (chatId) => {
    try {
      await api.post("/telegram/test", { chat_id: chatId });
      toast.success("Test message sent!");
      return true;
    } catch (error) {
      toast.error("Failed to send test message");
      return false;
    }
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        <Login onLogin={handleLogin} />
        <Toaster position="top-right" richColors />
      </>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground font-mono uppercase tracking-wider text-sm">Loading ACTIVEBOT...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background grid-bg">
      <BrowserRouter>
        <Navigation isRunning={botStatus.is_running} onLogout={handleLogout} />
        <main className="max-w-[1600px] mx-auto p-4 md:p-6">
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  botStatus={botStatus}
                  stats={stats}
                  sentiment={sentiment}
                  trades={trades}
                  pnlHistory={pnlHistory}
                  systemStatus={systemStatus}
                  onStart={startBot}
                  onStop={stopBot}
                  onRefresh={fetchData}
                />
              }
            />
            <Route
              path="/history"
              element={<TradeHistory trades={trades} onRefresh={fetchData} />}
            />
            <Route
              path="/settings"
              element={
                <Settings
                  config={botStatus.config}
                  onUpdateConfig={updateConfig}
                  onTestTelegram={testTelegram}
                />
              }
            />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
