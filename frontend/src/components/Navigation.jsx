import { Link, useLocation } from "react-router-dom";
import { Activity, History, Settings, Bot } from "lucide-react";

const Navigation = ({ isRunning }) => {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Dashboard", icon: Activity },
    { path: "/history", label: "History", icon: History },
    { path: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 bg-black/80 backdrop-blur-md border-b border-border">
      <div className="max-w-[1600px] mx-auto px-4 md:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <Bot className="w-8 h-8 text-primary" />
              <div
                className={`absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full ${
                  isRunning ? "bg-primary pulse-green" : "bg-destructive"
                }`}
              />
            </div>
            <div>
              <h1 className="font-mono text-lg font-bold tracking-tight uppercase">
                ACTIVEBOT
              </h1>
              <p className="text-xs text-muted-foreground font-mono uppercase tracking-widest">
                {isRunning ? "RUNNING" : "STOPPED"}
              </p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  data-testid={`nav-${item.label.toLowerCase()}`}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-sm font-mono text-sm uppercase tracking-wider
                    transition-all duration-200
                    ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:inline">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Navigation;
