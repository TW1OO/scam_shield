import { Image, MessageCircle } from "lucide-react";

export default function Tabs({
  currentTab,
  setCurrentTab,
}) {
  return (
    <div className="tabs-wrap">

      <button
        className={`tab-btn ${currentTab === 0 ? "active" : ""}`}
        onClick={() => setCurrentTab(0)}
      >
        <Image size={18} />
        <span>미디어 분석</span>
      </button>

      <button
        className={`tab-btn ${currentTab === 1 ? "active" : ""}`}
        onClick={() => setCurrentTab(1)}
      >
        <MessageCircle size={18} />
        <span>대화 분석</span>
      </button>

    </div>
  );
}