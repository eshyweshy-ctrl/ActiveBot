import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import {
  Settings as SettingsIcon,
  DollarSign,
  Send,
  Bitcoin,
  Coins,
  Save,
  TestTube,
  AlertTriangle,
} from "lucide-react";

const Settings = ({ config, onUpdateConfig, onTestTelegram }) => {
  const [tradeSize, setTradeSize] = useState(config?.trade_size_usdc || 10);
  const [assetsEnabled, setAssetsEnabled] = useState(config?.assets_enabled || ["BTC", "ETH", "SOL"]);
  const [dryRunMode, setDryRunMode] = useState(config?.dry_run_mode ?? true);
  const [telegramEnabled, setTelegramEnabled] = useState(config?.telegram_enabled || false);
  const [telegramChatId, setTelegramChatId] = useState(config?.telegram_chat_id || "");
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  const toggleAsset = (asset) => {
    if (assetsEnabled.includes(asset)) {
      if (assetsEnabled.length > 1) {
        setAssetsEnabled(assetsEnabled.filter((a) => a !== asset));
      }
    } else {
      setAssetsEnabled([...assetsEnabled, asset]);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    await onUpdateConfig({
      trade_size_usdc: tradeSize,
      assets_enabled: assetsEnabled,
      dry_run_mode: dryRunMode,
      telegram_enabled: telegramEnabled,
      telegram_chat_id: telegramChatId,
    });
    setSaving(false);
  };

  const handleTestTelegram = async () => {
    if (!telegramChatId) return;
    setTesting(true);
    await onTestTelegram(telegramChatId);
    setTesting(false);
  };

  const assets = [
    { id: "BTC", label: "Bitcoin", icon: Bitcoin },
    { id: "ETH", label: "Ethereum", icon: Coins },
    { id: "SOL", label: "Solana", icon: Coins },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight uppercase font-mono">
            Settings
          </h2>
          <p className="text-muted-foreground text-sm">
            Configure your trading bot parameters
          </p>
        </div>
        <Button
          onClick={handleSave}
          disabled={saving}
          data-testid="save-settings-btn"
          className="font-mono uppercase tracking-wider bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <Save className="w-4 h-4 mr-2" />
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Trade Size */}
        <Card className="bg-card border-border rounded-sm shadow-none">
          <CardHeader className="border-b border-border p-4">
            <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-primary" />
              Trade Size
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-6">
              <div className="text-center">
                <span className="text-5xl font-mono font-bold tracking-tighter text-primary">
                  ${tradeSize}
                </span>
                <p className="text-muted-foreground text-sm font-mono mt-1">USDC per trade</p>
              </div>
              
              <div className="space-y-4">
                <Slider
                  value={[tradeSize]}
                  onValueChange={([value]) => setTradeSize(value)}
                  min={1}
                  max={1000}
                  step={1}
                  data-testid="trade-size-slider"
                  className="py-4"
                />
                <div className="flex justify-between text-xs text-muted-foreground font-mono">
                  <span>$1</span>
                  <span>$1000</span>
                </div>
              </div>

              {/* Quick Select Buttons */}
              <div className="flex gap-2 justify-center">
                {[10, 25, 50, 100, 250].map((amount) => (
                  <Button
                    key={amount}
                    variant={tradeSize === amount ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTradeSize(amount)}
                    data-testid={`quick-select-${amount}`}
                    className="font-mono"
                  >
                    ${amount}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Asset Selection */}
        <Card className="bg-card border-border rounded-sm shadow-none">
          <CardHeader className="border-b border-border p-4">
            <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
              <Coins className="w-5 h-5 text-primary" />
              Assets to Trade
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-4">
              {assets.map((asset) => {
                const Icon = asset.icon;
                const isEnabled = assetsEnabled.includes(asset.id);
                return (
                  <div
                    key={asset.id}
                    className={`
                      flex items-center justify-between p-4 rounded-sm border transition-all cursor-pointer
                      ${isEnabled ? "border-primary bg-primary/10" : "border-border hover:border-muted-foreground"}
                    `}
                    onClick={() => toggleAsset(asset.id)}
                    data-testid={`asset-toggle-${asset.id.toLowerCase()}`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className={`w-6 h-6 ${isEnabled ? "text-primary" : "text-muted-foreground"}`} />
                      <div>
                        <p className="font-mono font-medium">{asset.id}</p>
                        <p className="text-xs text-muted-foreground">{asset.label}</p>
                      </div>
                    </div>
                    <Switch checked={isEnabled} onCheckedChange={() => toggleAsset(asset.id)} />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Trading Mode */}
        <Card className="bg-card border-border rounded-sm shadow-none">
          <CardHeader className="border-b border-border p-4">
            <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              Trading Mode
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-sm border border-border">
                <div>
                  <p className="font-mono font-medium">Dry Run Mode</p>
                  <p className="text-xs text-muted-foreground">
                    Simulate trades without real money
                  </p>
                </div>
                <Switch
                  checked={dryRunMode}
                  onCheckedChange={setDryRunMode}
                  data-testid="dry-run-toggle"
                />
              </div>
              
              {!dryRunMode && (
                <div className="p-4 bg-destructive/10 border border-destructive/50 rounded-sm">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-mono font-medium text-destructive">Live Trading Enabled</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Real money will be used for trades. Make sure your wallet is funded and you understand the risks.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <Badge
                className={`${dryRunMode ? "badge-warning" : "badge-error"} rounded-none px-3 py-1 text-sm font-mono uppercase w-full justify-center`}
              >
                {dryRunMode ? "DRY RUN MODE" : "LIVE TRADING MODE"}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Telegram Notifications */}
        <Card className="bg-card border-border rounded-sm shadow-none">
          <CardHeader className="border-b border-border p-4">
            <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
              <Send className="w-5 h-5 text-primary" />
              Telegram Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-sm border border-border">
                <div>
                  <p className="font-mono font-medium">Enable Notifications</p>
                  <p className="text-xs text-muted-foreground">
                    Receive trade alerts via Telegram
                  </p>
                </div>
                <Switch
                  checked={telegramEnabled}
                  onCheckedChange={setTelegramEnabled}
                  data-testid="telegram-toggle"
                />
              </div>

              {telegramEnabled && (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="chat-id" className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                      Chat ID
                    </Label>
                    <Input
                      id="chat-id"
                      value={telegramChatId}
                      onChange={(e) => setTelegramChatId(e.target.value)}
                      placeholder="Enter your Telegram chat ID"
                      className="mt-2 font-mono bg-muted border-input"
                      data-testid="telegram-chat-id-input"
                    />
                    <p className="text-xs text-muted-foreground mt-2">
                      Get your chat ID by messaging @userinfobot on Telegram
                    </p>
                  </div>

                  <Button
                    variant="outline"
                    onClick={handleTestTelegram}
                    disabled={!telegramChatId || testing}
                    data-testid="test-telegram-btn"
                    className="w-full font-mono uppercase tracking-wider"
                  >
                    <TestTube className="w-4 h-4 mr-2" />
                    {testing ? "Sending..." : "Send Test Message"}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trading Rules Info */}
      <Card className="bg-card border-border rounded-sm shadow-none">
        <CardHeader className="border-b border-border p-4">
          <CardTitle className="text-lg font-mono uppercase tracking-wider flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-primary" />
            Trading Rules
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 bg-muted rounded-sm border border-border">
              <h4 className="font-mono font-medium text-primary mb-2">EXTREME FEAR (0-19)</h4>
              <p className="text-sm text-muted-foreground">
                Buy YES tokens - expecting price to go UP
              </p>
            </div>
            <div className="p-4 bg-muted rounded-sm border border-border">
              <h4 className="font-mono font-medium text-muted-foreground mb-2">NEUTRAL (20-79)</h4>
              <p className="text-sm text-muted-foreground">
                No trade - wait for extreme sentiment
              </p>
            </div>
            <div className="p-4 bg-muted rounded-sm border border-border">
              <h4 className="font-mono font-medium text-destructive mb-2">EXTREME GREED (80-100)</h4>
              <p className="text-sm text-muted-foreground">
                Buy NO tokens - expecting price to go DOWN
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;
