import { ShieldCheck, Activity } from "lucide-react";

export default function Dashboard() {

    return(

        <div className="dashboard">

            <div className="dashboard-card">

                <div className="dashboard-left">

                    <ShieldCheck size={32}/>

                    <div>

                        <h3>TrustChain AI</h3>

                        <p>

                            실시간 금융사기 예방 시스템

                        </p>

                    </div>

                </div>

                <span className="dashboard-status">

                    ACTIVE

                </span>

            </div>

            <div className="dashboard-grid">

                <div className="stat-card">

                    <Activity size={22}/>

                    <h2>128</h2>

                    <span>분석 완료</span>

                </div>

                <div className="stat-card">

                    ⚠️

                    <h2>7</h2>

                    <span>위험 탐지</span>

                </div>

            </div>

        </div>

    );

}