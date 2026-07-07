import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";

export default function Header() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();

      setTime(
        `${now.getHours()}:${String(now.getMinutes()).padStart(2, "0")}`
      );
    };

    updateTime();

    const timer = setInterval(updateTime, 60000);

    return () => clearInterval(timer);
  }, []);

  return (
    <>
      <div className="statusbar">
        <span className="status-time">{time}</span>
      </div>

      <header className="header">
        <div className="header-card">

          <div className="logo-section">
            <div className="logo-icon">
              <ShieldCheck size={28} />
            </div>

            <div>
              <p className="logo-title">TrustChain</p>
              <p>AI Fraud Detection</p>
            </div>
          </div>

          <div className="ai-chip">
            <span className="live-dot"></span>
            AI ACTIVE
          </div>

        </div>
      </header>
    </>
  );
}