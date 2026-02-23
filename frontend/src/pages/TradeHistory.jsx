import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  History,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  Download,
} from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TradeHistory = ({ trades: initialTrades, onRefresh }) => {
  const [trades, setTrades] = useState(initialTrades || []);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    asset: "all",
    status: "all",
    search: "",
  });

  useEffect(() => {
    setTrades(initialTrades || []);
  }, [initialTrades]);

  const fetchTrades = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.asset !== "all") params.append("asset", filters.asset);
      if (filters.status !== "all") params.append("status", filters.status);
      params.append("limit", "100");

      const response = await axios.get(`${API}/trades?${params.toString()}`);
      setTrades(response.data);
    } catch (error) {
      console.error("Error fetching trades:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  useEffect(() => {
    fetchTrades();
  }, [filters.asset, filters.status]);

  const formatPnl = (value) => {
    if (value === null || value === undefined) return "-";
    if (value >= 0) return `+$${value.toFixed(2)}`;
    return `-$${Math.abs(value).toFixed(2)}`;
  };

  const filteredTrades = trades.filter((trade) => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        trade.asset.toLowerCase().includes(searchLower) ||
        trade.id.toLowerCase().includes(searchLower) ||
        trade.market_id?.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  const exportToCsv = () => {
    const headers = ["ID", "Asset", "Direction", "Amount", "Entry", "Exit", "P&L", "Status", "Time"];
    const rows = filteredTrades.map((trade) => [
      trade.id,
      trade.asset,
      trade.direction,
      trade.amount_usdc,
      trade.entry_price,
      trade.exit_price || "",
      trade.pnl || "",
      trade.status,
      trade.timestamp,
    ]);

    const csvContent = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `activebot-trades-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Calculate stats from filtered trades
  const stats = {
    total: filteredTrades.length,
    wins: filteredTrades.filter((t) => t.status === "WON").length,
    losses: filteredTrades.filter((t) => t.status === "LOST").length,
    totalPnl: filteredTrades.reduce((sum, t) => sum + (t.pnl || 0), 0),
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight uppercase font-mono">
            Trade History
          </h2>
          <p className="text-muted-foreground text-sm">
            Complete record of all trades
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={exportToCsv}
            data-testid="export-csv-btn"
            className="font-mono uppercase tracking-wider"
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTrades}
            disabled={loading}
            data-testid="refresh-trades-btn"
            className="font-mono uppercase tracking-wider"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border rounded-sm shadow-none">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">
              Total Trades
            </p>
            <p className="text-2xl font-mono font-bold tracking-tighter">{stats.total}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border rounded-sm shadow-none">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">
              Wins
            </p>
            <p className="text-2xl font-mono font-bold tracking-tighter text-primary">{stats.wins}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border rounded-sm shadow-none">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">
              Losses
            </p>
            <p className="text-2xl font-mono font-bold tracking-tighter text-destructive">{stats.losses}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border rounded-sm shadow-none">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">
              Total P&L
            </p>
            <p className={`text-2xl font-mono font-bold tracking-tighter ${stats.totalPnl >= 0 ? "number-positive" : "number-negative"}`}>
              {formatPnl(stats.totalPnl)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-card border-border rounded-sm shadow-none">
        <CardHeader className="border-b border-border p-4">
          <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
            <Filter className="w-5 h-5 text-primary" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2 block">
                Search
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search by ID, asset..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange("search", e.target.value)}
                  className="pl-10 font-mono bg-muted border-input"
                  data-testid="search-input"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2 block">
                Asset
              </label>
              <Select value={filters.asset} onValueChange={(value) => handleFilterChange("asset", value)}>
                <SelectTrigger className="font-mono bg-muted border-input" data-testid="asset-filter">
                  <SelectValue placeholder="All Assets" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Assets</SelectItem>
                  <SelectItem value="BTC">BTC</SelectItem>
                  <SelectItem value="ETH">ETH</SelectItem>
                  <SelectItem value="SOL">SOL</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2 block">
                Status
              </label>
              <Select value={filters.status} onValueChange={(value) => handleFilterChange("status", value)}>
                <SelectTrigger className="font-mono bg-muted border-input" data-testid="status-filter">
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="WON">Won</SelectItem>
                  <SelectItem value="LOST">Lost</SelectItem>
                  <SelectItem value="OPEN">Open</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trade Table */}
      <Card className="bg-card border-border rounded-sm shadow-none">
        <CardHeader className="border-b border-border p-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
              <History className="w-5 h-5 text-primary" />
              All Trades
            </CardTitle>
            <span className="text-xs text-muted-foreground font-mono">
              {filteredTrades.length} trades
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full data-table">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-4">ID</th>
                  <th className="text-left p-4">Asset</th>
                  <th className="text-left p-4">Direction</th>
                  <th className="text-left p-4">Amount</th>
                  <th className="text-left p-4">CFGI</th>
                  <th className="text-left p-4">Entry</th>
                  <th className="text-left p-4">Exit</th>
                  <th className="text-left p-4">P&L</th>
                  <th className="text-left p-4">Status</th>
                  <th className="text-left p-4">Time</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrades.length === 0 ? (
                  <tr>
                    <td colSpan="10" className="text-center p-8 text-muted-foreground font-mono">
                      No trades found matching your filters.
                    </td>
                  </tr>
                ) : (
                  filteredTrades.map((trade) => (
                    <tr
                      key={trade.id}
                      className="border-b border-border/50 hover:bg-muted/50 transition-colors"
                      data-testid={`history-trade-${trade.id}`}
                    >
                      <td className="p-4 font-mono text-xs text-muted-foreground">
                        {trade.id.substring(0, 8)}...
                      </td>
                      <td className="p-4 font-mono font-medium">{trade.asset}</td>
                      <td className="p-4">
                        <span className={`flex items-center gap-1 ${trade.direction === "UP" ? "text-primary" : "text-destructive"}`}>
                          {trade.direction === "UP" ? (
                            <TrendingUp className="w-4 h-4" />
                          ) : (
                            <TrendingDown className="w-4 h-4" />
                          )}
                          {trade.direction}
                        </span>
                      </td>
                      <td className="p-4 font-mono">${trade.amount_usdc}</td>
                      <td className="p-4 font-mono">{trade.cfgi_score}</td>
                      <td className="p-4 font-mono">{trade.entry_price?.toFixed(4)}</td>
                      <td className="p-4 font-mono">{trade.exit_price?.toFixed(4) || "-"}</td>
                      <td className={`p-4 font-mono font-medium ${trade.pnl >= 0 ? "number-positive" : "number-negative"}`}>
                        {formatPnl(trade.pnl)}
                      </td>
                      <td className="p-4">
                        <Badge
                          className={`rounded-none px-2 py-0.5 text-xs font-mono uppercase tracking-widest ${
                            trade.status === "WON"
                              ? "badge-success"
                              : trade.status === "LOST"
                              ? "badge-error"
                              : trade.status === "OPEN"
                              ? "bg-accent/20 text-accent border border-accent/50"
                              : "badge-neutral"
                          }`}
                        >
                          {trade.status}
                        </Badge>
                      </td>
                      <td className="p-4 text-muted-foreground text-xs whitespace-nowrap">
                        {new Date(trade.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TradeHistory;
