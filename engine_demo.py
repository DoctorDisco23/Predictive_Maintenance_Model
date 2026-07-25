import pandas as pd
import numpy as np
import time
import os
import random
import select
import sys
from datetime import datetime, timedelta

# --- MOCK CLASSES (Replace with your actual imports) ---
from MultiModalMapper import MultiModalMapper
from semantic_test import SemanticEnricher, NAVY_ABBR_MAP, COMPONENTS, SYMPTOMS, SEVERITY_WEIGHTS, STOPWORDS

# 1. INITIALIZE CORE ENGINES
enricher = SemanticEnricher(NAVY_ABBR_MAP, COMPONENTS, SYMPTOMS, SEVERITY_WEIGHTS, STOPWORDS)
mapper = MultiModalMapper()

# 2. DATA STRATEGY: Time-Series Stream Simulation
column_names = ['Lever_Pos', 'Speed', 'Torque', 'GT_RPM', 'GG_RPM', 'STBD_Torque', 'Port_Torque', 'GT_Turbine_Temp', 'C_In_Temp', 'C_Out_Temp', 'T_Exit_Press', 'C_In_Press', 'C_Out_Press', 'Exh_Press', 'Control_Val', 'Fuel_Flow', 'Compressor_Health', 'Turbine_Health']
df = pd.read_csv('navalplantmaintenance.csv', sep=r'\s+', header=None, names=column_names)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def start_demo():
    ai_risk_penalty = 0
    start_time = datetime.utcnow()
    
    print("🚀 STARTING LIVE TELEMETRY STREAM... (Press 'q' + Enter to stop)")
    time.sleep(2)

    for i in range(len(df)):
        clear_screen()
        row = df.iloc[i].copy()
        
        # 3.4 Inject Sensor Noise
        row['GT_Turbine_Temp'] += random.uniform(-1.5, 1.5)
        
        # 2.1 System Metadata
        current_ts = (start_time + timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # 2.4 Prognostics Layer: RUL + Uncertainty Bounds
        base_rul = min((row['Compressor_Health'] - 0.948) * 19230, (row['Turbine_Health'] - 0.948) * 19230)
        
        # SLOWER PROGRESSION LOGIC: Penalty now grows over time once triggered
        current_rul = max(0, base_rul - (i * 0.1) - ai_risk_penalty)
        uncertainty = current_rul * 0.05 
        
        # 2.9 Adjusted Risk Index for Smoother Transitions
        risk_score = min(1.0, ai_risk_penalty / 150) if ai_risk_penalty > 0 else 0.02

        # --- 5.0 REFINED DASHBOARD OUTPUT ---
        print("="*90)
        print(f" SYSTEM ID: NAVAL-GT-01 | MODE: CRUISE | {current_ts}")
        state = '🟢 NOMINAL' if risk_score < 0.25 else '🟡 DEGRADED' if risk_score < 0.6 else '🔴 CRITICAL'
        print(f" OPERATIONAL STATE: {state}")
        print("="*90)
        
        print(f" [HEALTH]   SYS_HEALTH: {(1.0 - risk_score)*100:>5.1f}% | COMP: {row['Compressor_Health']*100:.2f}% | TURB: {row['Turbine_Health']*100:.2f}%")
        print(f" [SENSORS]  GT_TEMP: {row['GT_Turbine_Temp']:>6.1f}°C | C_OUT_PRESS: {row['C_Out_Press']:>5.2f} bar | FUEL_FLW: {row['Fuel_Flow']:>5.2f} kg/s")
        print("-" * 90)
        
        trend_icon = "📉 ACCELERATING" if risk_score > 0.6 else "📉 DECREASING" if risk_score > 0.1 else "➡️ STABLE"
        print(f" [PROGNOSIS] EST. RUL: {current_rul:>6.1f} HRS (±{uncertainty:.1f}) | CONFIDENCE: {98 - (risk_score*50):.1f}%")
        print(f" [TREND]     DIRECTION: {trend_icon} | FAILURE RISK (24H): {risk_score*100:>4.1f}%")
        print("-" * 90)

        # Actionable Output
        if risk_score > 0.6:
            print(f" [ACTION]   🚨 CRITICAL: Immediate inspection required. Power down initiated.")
        elif risk_score > 0.25:
            print(f" [ACTION]   ⚠️ WARNING: Elevated risk detected. Schedule borescope within 24hrs.")
        else:
            print(f" [ACTION]   ✅ Status Nominal. Continue standard mission profile.")
        
        print("="*90)
        print("\n(Type a log and hit Enter to analyze, or wait for next update...)")

        # NON-BLOCKING INPUT (Wait 2 seconds for user input, then move forward)
        # Note: On Windows, use msvcrt; on Linux/Mac, use select.
        if sys.platform == "win32":
            import msvcrt
            time.sleep(2)
            if msvcrt.kbhit():
                user_log = input("📝 LOG ENTRY: ").strip().lower()
            else:
                user_log = None
        else:
            rlist, _, _ = select.select([sys.stdin], [], [], 2.0)
            user_log = sys.stdin.readline().strip().lower() if rlist else None

        if user_log == 'q': break

        if user_log:
            print("\n" + " "*25 + ">>> 2.6 EXPLAINABILITY LAYER <<<")
            analysis = enricher.analyze(user_log)
            severity = analysis.get('severity', 0)
            
            # Refined severity for smoother progression
            if any(w in user_log for w in ["fire", "smoke"]):
                severity = max(severity, 0.8)
            
            print(f" [REASONING] Log identified as {analysis['components'] if analysis['components'] else 'General'}.")
            print(f" [REASONING] Correlation: Human reports {analysis['symptoms']}.")
            
            # Apply penalty: it now adds to the existing risk for a cumulative "slower" progression
            impact = severity * 60 
            ai_risk_penalty += impact
            print(f" [IMPACT]    Risk factor registered. Health impact: -{impact:.1f} hours.")
            time.sleep(2)

if __name__ == "__main__":
    start_demo()