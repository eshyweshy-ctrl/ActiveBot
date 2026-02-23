import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Play,
  Square,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  Zap,
  Wifi,
  WifiOff,
  Database,
  Send,
  Globe,
  Wallet,
  Clock,
  Copy,
  ExternalLink,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { toast } from "sonner";

const Dashboard = ({
  botStatus,
  stats,
  sentiment,
  trades,
  pnlHistory,
  systemStatus,
  walletInfo,
  onStart,
  onStop,
  onRefresh,
}) => {
  const formatPnl = (value) => {
    if (value >= 0) return `+$${value.toFixed(2)}`;
    return `-$${Math.abs(value).toFixed(2)}`;
  };

  const getSignalColor = (signal) => {
    if (signal === "BUY_YES") return "text-primary";
    if (signal === "BUY_NO") return "text-destructive";
    return "text-muted-foreground";
  };

  const getSignalBadge = (signal) => {
    if (signal === "BUY_YES") return "badge-success";
    if (signal === "BUY_NO") return "badge-error";
    return "badge-neutral";
  };

  const getSentimentLabel = (score) => {
    if (score <= 19) return "EXTREME FEAR";
    if (score <= 39) return "FEAR";
    if (score <= 59) return "NEUTRAL";
    if (score <= 79) return "GREED";
    return "EXTREME GREED";
  };

  const getStatusIcon = (status) => {
    if (status === "online") return <Wifi className="w-4 h-4 text-primary" />;
    if (status === "offline" || status === "error") return <WifiOff className="w-4 h-4 text-destructive" />;
    return <Wifi className="w-4 h-4 text-muted-foreground" />;
  };

  const getStatusBadge = (status) => {
    if (status === "online") return "badge-success";
    if (status === "offline" || status === "error") return "badge-error";
    return "badge-neutral";
  };

  return (
    <div className="space-y-6">
      {/* Header Row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight uppercase font-mono">
            Dashboard
          </h2>
          <p className="text-muted-foreground text-sm">
            Real-time trading bot monitoring
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            data-testid="refresh-btn"
            className="font-mono uppercase tracking-wider"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          {botStatus.is_running ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={onStop}
              data-testid="stop-bot-btn"
              className="font-mono uppercase tracking-wider"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop Bot
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={onStart}
              data-testid="start-bot-btn"
              className="font-mono uppercase tracking-wider bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Play className="w-4 h-4 mr-2" />
              Start Bot
            </Button>
          )}
        </div>
      </div>

      {/* System Status Bar */}
      <Card className="bg-card border-border rounded-sm shadow-none">
        <CardHeader className="border-b border-border p-4">
          <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            System Status
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="flex items-center justify-between p-3 bg-muted rounded-sm border border-border">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-muted-foreground" />
                <span className="font-mono text-sm">CFGI.io</span>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(systemStatus.cfgi_api)}
                <Badge className={`${getStatusBadge(systemStatus.cfgi_api)} rounded-none px-2 py-0.5 text-xs font-mono uppercase`}>
                  {systemStatus.cfgi_api}
                </Badge>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted rounded-sm border border-border">
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-muted-foreground" />
                <span className="font-mono text-sm">Polymarket</span>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(systemStatus.polymarket_api)}
                <Badge className={`${getStatusBadge(systemStatus.polymarket_api)} rounded-none px-2 py-0.5 text-xs font-mono uppercase`}>
                  {systemStatus.polymarket_api}
                </Badge>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted rounded-sm border border-border">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-muted-foreground" />
                <span className="font-mono text-sm">MongoDB</span>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(systemStatus.mongodb)}
                <Badge className={`${getStatusBadge(systemStatus.mongodb)} rounded-none px-2 py-0.5 text-xs font-mono uppercase`}>
                  {systemStatus.mongodb}
                </Badge>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted rounded-sm border border-border">
              <div className="flex items-center gap-2">
                <Send className="w-4 h-4 text-muted-foreground" />
                <span className="font-mono text-sm">Telegram</span>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(systemStatus.telegram)}
                <Badge className={`${getStatusBadge(systemStatus.telegram)} rounded-none px-2 py-0.5 text-xs font-mono uppercase`}>
                  {systemStatus.telegram}
                </Badge>
              </div>
            </div>
            {/* Wallet Status */}
            <div className="flex items-center justify-between p-3 bg-muted rounded-sm border border-border">
              <div className="flex items-center gap-2">
                <Wallet className="w-4 h-4 text-muted-foreground" />
                <span className="font-mono text-sm">Wallet</span>
              </div>
              <div className="flex items-center gap-2">
                {walletInfo?.address ? (
                  <Wifi className="w-4 h-4 text-primary" />
                ) : (
                  <WifiOff className="w-4 h-4 text-destructive" />
                )}
                <Badge className={`${walletInfo?.address ? "badge-success" : "badge-error"} rounded-none px-2 py-0.5 text-xs font-mono uppercase`}>
                  {walletInfo?.address ? "CONNECTED" : "NOT SET"}
                </Badge>
              </div>
            </div>
          </div>
          
          {/* Wallet Details Row */}
          {walletInfo?.address && (
            <div className="mt-4 p-3 bg-muted/50 rounded-sm border border-border">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <Wallet className="w-5 h-5 text-primary" />
                  <div>
                    <p className="text-xs text-muted-foreground font-mono uppercase">Connected Wallet</p>
                    <div className="flex items-center gap-2">
                      <code className="font-mono text-sm text-foreground">{walletInfo.address_short}</code>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(walletInfo.address);
                          toast.success("Address copied!");
                        }}
                        className="p-1 hover:bg-muted rounded"
                      >
                        <Copy className="w-3 h-3 text-muted-foreground" />
                      </button>
                      <a
                        href={`https://polygonscan.com/address/${walletInfo.address}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1 hover:bg-muted rounded"
                      >
                        <ExternalLink className="w-3 h-3 text-muted-foreground" />
                      </a>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground font-mono uppercase">Wallet USDC</p>
                    <p className="font-mono text-lg font-bold text-primary">${walletInfo.usdc_balance?.toFixed(2) || "0.00"}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground font-mono uppercase">Polymarket</p>
                    <p className="font-mono text-lg font-bold text-accent">${walletInfo.polymarket_balance?.toFixed(2) || "0.00"}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground font-mono uppercase">MATIC</p>
                    <p className="font-mono text-sm">{walletInfo.matic_balance?.toFixed(4) || "0.0000"}</p>
                  </div>
                  <div className="text-right border-l border-border pl-4">
                    <p className="text-xs text-muted-foreground font-mono uppercase">Total</p>
                    <p className="font-mono text-lg font-bold">${walletInfo.total_value?.toFixed(2) || "0.00"}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 auto-rows-[minmax(180px,auto)]">
        {/* Sentiment Hero - Spans 8 cols, 2 rows */}
        <Card className="col-span-1 md:col-span-8 row-span-2 bg-card border-border rounded-sm shadow-none">
          <CardHeader className="border-b border-border p-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary" />
                Sentiment Analysis (15-min)
              </CardTitle>
              <Badge className={`${getSignalBadge(sentiment.BTC?.signal)} rounded-none px-2 py-0.5 text-xs font-mono uppercase tracking-widest`}>
                {sentiment.BTC?.signal || "HOLD"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-4">
            {/* Sentiment Scores */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              {["BTC", "ETH", "SOL"].map((asset) => (
                <div
                  key={asset}
                  className="bg-muted rounded-sm p-4 border border-border"
                  data-testid={`sentiment-${asset.toLowerCase()}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-sm uppercase tracking-wider text-muted-foreground">
                      {asset}
                    </span>
                    <span className={`text-xs font-mono uppercase ${getSignalColor(sentiment[asset]?.signal)}`}>
                      {sentiment[asset]?.signal || "HOLD"}
                    </span>
                  </div>
                  <div className="text-4xl font-mono font-bold tracking-tighter">
                    {sentiment[asset]?.score || 50}
                  </div>
                  <div className="text-xs text-muted-foreground font-mono uppercase mt-1">
                    {getSentimentLabel(sentiment[asset]?.score || 50)}
                  </div>
                  {/* Sentiment Bar */}
                  <div className="mt-3 h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full sentiment-gauge"
                      style={{ width: `${sentiment[asset]?.score || 50}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* P&L Chart */}
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={pnlHistory}>
                  <defs>
                    <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(159, 100%, 45%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(159, 100%, 45%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(0, 0%, 15%)" />
                  <XAxis
                    dataKey="timestamp"
                    tick={{ fill: "hsl(0, 0%, 64%)", fontSize: 10, fontFamily: "JetBrains Mono" }}
                    tickFormatter={(value) => new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  />
                  <YAxis
                    tick={{ fill: "hsl(0, 0%, 64%)", fontSize: 10, fontFamily: "JetBrains Mono" }}
                    tickFormatter={(value) => `$${value}`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(0, 0%, 4%)",
                      border: "1px solid hsl(0, 0%, 15%)",
                      borderRadius: "2px",
                      fontFamily: "JetBrains Mono",
                    }}
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value) => [`$${value.toFixed(2)}`, "Cumulative P&L"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="cumulative_pnl"
                    stroke="hsl(159, 100%, 45%)"
                    fill="url(#colorPnl)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Bot Status - Spans 4 cols, 1 row */}
        <Card className="col-span-1 md:col-span-4 row-span-1 bg-card border-border rounded-sm shadow-none">
          <CardHeader className="border-b border-border p-4">
            <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-5 h-5 text-primary" />
              Bot Status
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`w-3 h-3 rounded-full ${
                  botStatus.is_running ? "bg-primary pulse-green" : "bg-destructive"
                }`}
              />
              <span className="font-mono text-xl uppercase tracking-wider">
                {botStatus.is_running ? "RUNNING" : "STOPPED"}
              </span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground font-mono uppercase text-xs">Mode</span>
                <Badge className={`${botStatus.config?.dry_run_mode ? "badge-warning" : "badge-error"} rounded-none px-2 py-0.5 text-xs font-mono`}>
                  {botStatus.config?.dry_run_mode ? "DRY RUN" : "LIVE"}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground font-mono uppercase text-xs">Trade Size</span>
                <span className="font-mono">${botStatus.config?.trade_size_usdc}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground font-mono uppercase text-xs">Assets</span>
                <span className="font-mono">{botStatus.config?.assets_enabled?.join(", ")}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats - Spans 4 cols, 1 row */}
        <Card className="col-span-1 md:col-span-4 row-span-1 bg-card border-border rounded-sm shadow-none">
          <CardHeader className="border-b border-border p-4">
            <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              Quick Stats
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">
                  Total P&L
                </p>
                <p
                  className={`text-2xl font-mono font-bold tracking-tighter ${
                    stats.total_pnl >= 0 ? "number-positive" : "number-negative"
                  }`}
                  data-testid="total-pnl"
                >
                  {formatPnl(stats.total_pnl)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">
                  Win Rate
                </p>
                <p className="text-2xl font-mono font-bold tracking-tighter" data-testid="win-rate">
                  {stats.win_rate}%
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">
                  Total Trades
                </p>
                <p className="text-2xl font-mono font-bold tracking-tighter" data-testid="total-trades">
                  {stats.total_trades}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest mb-1">
                  Open
                </p>
                <p className="text-2xl font-mono font-bold tracking-tighter text-accent">
                  {stats.open_trades}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Trades - Full width */}
        <Card className="col-span-1 md:col-span-12 bg-card border-border rounded-sm shadow-none">
          <CardHeader className="border-b border-border p-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-primary" />
                Recent Trades
              </CardTitle>
              <span className="text-xs text-muted-foreground font-mono uppercase">
                Last 20 trades
              </span>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full data-table">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4">Asset</th>
                    <th className="text-left p-4">Direction</th>
                    <th className="text-left p-4">Amount</th>
                    <th className="text-left p-4">CFGI</th>
                    <th className="text-left p-4">Entry</th>
                    <th className="text-left p-4">Exit</th>
                    <th className="text-left p-4">P&L</th>
                    <th className="text-left p-4">Status</th>
                    <th className="text-left p-4">Time</th>
                    <th className="text-left p-4">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.length === 0 ? (
                    <tr>
                      <td colSpan="10" className="text-center p-8 text-muted-foreground font-mono">
                        No trades yet. Start the bot to begin trading.
                      </td>
                    </tr>
                  ) : (
                    trades.map((trade) => {
                      const entryTime = new Date(trade.timestamp);
                      const exitTime = trade.closed_at ? new Date(trade.closed_at) : null;
                      const duration = exitTime 
                        ? Math.round((exitTime - entryTime) / 1000 / 60) 
                        : null;
                      
                      return (
                        <tr
                          key={trade.id}
                          className="border-b border-border/50 hover:bg-muted/50 transition-colors"
                          data-testid={`trade-row-${trade.id}`}
                        >
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
                          <td className="p-4">
                            <span className={`font-mono text-sm ${
                              trade.cfgi_score <= 19 ? "text-destructive" : 
                              trade.cfgi_score >= 80 ? "text-primary" : 
                              "text-muted-foreground"
                            }`}>
                              {trade.cfgi_score || "-"}
                            </span>
                          </td>
                          <td className="p-4 font-mono">{trade.entry_price?.toFixed(4)}</td>
                          <td className="p-4 font-mono">{trade.exit_price?.toFixed(4) || "-"}</td>
                          <td className={`p-4 font-mono font-medium ${trade.pnl >= 0 ? "number-positive" : "number-negative"}`}>
                            {trade.pnl !== null ? formatPnl(trade.pnl) : "-"}
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
                          <td className="p-4 text-muted-foreground text-xs">
                            <div className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {entryTime.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                            </div>
                            <div className="text-[10px] text-muted-foreground/70">
                              {entryTime.toLocaleDateString()}
                            </div>
                          </td>
                          <td className="p-4 text-muted-foreground text-xs font-mono">
                            {duration !== null ? `${duration}m` : "..."}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
