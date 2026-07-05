import { useState } from "react";

import Header from "./components/Header";
import Tabs from "./components/Tabs";
import MediaGuard from "./components/MediaGuard";
import ConversationGuard from "./components/ConversationGuard";
import BottomControlBar from "./components/BottomControlBar";
import BottomSheet from "./components/BottomSheet";

function App() {
  // 현재 선택된 탭
  const [currentTab, setCurrentTab] = useState(0);

  // 분석 결과 존재 여부
  const [showBottomBar, setShowBottomBar] = useState(false);

  // BottomSheet 열림 여부
  const [sheetOpen, setSheetOpen] = useState(false);

  // 분석 결과 데이터
  const [analysisResult, setAnalysisResult] = useState(null);

  return (
    <div className="phone">

      <Header />

      <Tabs
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
      />

      <div className="slider-wrap">

        {currentTab === 0 ? (

          <MediaGuard
            setShowBottomBar={setShowBottomBar}
            setAnalysisResult={setAnalysisResult}
            openBottomSheet={() => setSheetOpen(true)}
          />

        ) : (

          <ConversationGuard
            setShowBottomBar={setShowBottomBar}
            setAnalysisResult={setAnalysisResult}
            openBottomSheet={() => setSheetOpen(true)}
          />

        )}

      </div>

      {showBottomBar && (
        <BottomControlBar
          onOpen={() => setSheetOpen(true)}
        />
      )}

      <BottomSheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        result={analysisResult}
      />

    </div>
  );
}

export default App;