import { useEffect, useState } from "react";

export default function RiskCard({
  risk,
  desc,
}) {

  const [displayRisk, setDisplayRisk] = useState(0);

  useEffect(() => {

    let value = 0;

    const timer = setInterval(() => {

      value++;

      setDisplayRisk(value);

      if (value >= risk) {

        clearInterval(timer);

      }

    }, 15);

    return () => clearInterval(timer);

  }, [risk]);

  const color =
    risk >= 80
      ? "#D93025"
      : risk >= 50
      ? "#FF9800"
      : "#1B8A4C";

  return (

    <div className="risk-card">

      <div
        className="risk-circle"
        style={{
          borderColor: color,
          color,
        }}
      >

        {displayRisk}%

      </div>

      <div className="risk-desc">

        {desc}

      </div>

      <div className="risk-progress">

        <div
          className="risk-progress-fill"
          style={{
            width: `${displayRisk}%`,
            background: color,
          }}
        />

      </div>

    </div>

  );

}