import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Bot, Lock } from "lucide-react";

const Login = ({ onLogin }) => {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const success = await onLogin(password);
    
    if (!success) {
      setError("Invalid password");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-background grid-bg flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-card border-border rounded-sm shadow-none">
        <CardHeader className="text-center border-b border-border p-6">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <Bot className="w-16 h-16 text-primary" />
              <Lock className="w-6 h-6 text-muted-foreground absolute -bottom-1 -right-1" />
            </div>
          </div>
          <CardTitle className="text-2xl font-mono uppercase tracking-wider">
            ACTIVEBOT
          </CardTitle>
          <p className="text-muted-foreground text-sm mt-2">
            Enter password to access dashboard
          </p>
        </CardHeader>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="font-mono bg-muted border-input text-center text-lg tracking-widest"
                data-testid="password-input"
                autoFocus
              />
            </div>
            
            {error && (
              <p className="text-destructive text-sm text-center font-mono">{error}</p>
            )}
            
            <Button
              type="submit"
              disabled={loading || !password}
              data-testid="login-btn"
              className="w-full font-mono uppercase tracking-wider bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {loading ? "Verifying..." : "Access Dashboard"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
