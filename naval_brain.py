import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import shap
import logging

# 1. Professional Logging (Replaces basic print statements)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NavalPropulsionAI:
    """
    Production-grade Machine Learning pipeline for Naval Propulsion Health Estimation.
    Replaces naive linear heuristics with a Random Forest Regressor and SHAP explainability.
    """
    def __init__(self, data_path: str):
        self.data_path = data_path
        # n_jobs=-1 uses all CPU cores for faster training
        self.model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1) 
        
        self.feature_cols = [
            'Lever_Pos', 'Speed', 'Torque', 'GT_RPM', 'GG_RPM', 
            'STBD_Torque', 'Port_Torque', 'GT_Turbine_Temp', 
            'C_In_Temp', 'C_Out_Temp', 'T_Exit_Press', 
            'C_In_Press', 'C_Out_Press', 'Exh_Press', 
            'Control_Val', 'Fuel_Flow'
        ]
        self.target_col = 'Compressor_Health'
        self.explainer = None

    def load_and_preprocess(self) -> pd.DataFrame:
        """Loads data, handles formatting, and drops nulls."""
        logging.info(f"⌛ Loading telemetry from {self.data_path}...")
        try:
            # Using your space-separated logic, plus the two health targets
            all_cols = self.feature_cols + [self.target_col, 'Turbine_Health']
            df = pd.read_csv(self.data_path, sep=r'\s+', header=None, names=all_cols)
            df = df.dropna() # Safety net for messy data
            logging.info(f"✅ Loaded {len(df)} telemetry rows successfully.")
            return df
        except Exception as e:
            logging.error(f"❌ Data loading failed: {e}")
            raise

    def train(self, df: pd.DataFrame):
        """Trains the ML model to map physical sensor states to component health."""
        logging.info("🧠 Training Random Forest Regressor on sensor physics...")
        X = df[self.feature_cols]
        y = df[self.target_col]
        
        # Split data to prove the model isn't just memorizing
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(X_train, y_train)
        
        # Evaluate Model Accuracy
        preds = self.model.predict(X_test)
        r2 = r2_score(y_test, preds)
        logging.info(f"📊 Model Performance -> R2 Score: {r2:.4f} (1.0 is perfect)")
        
        # Initialize SHAP Explainer (The "Why" Engine)
        self.explainer = shap.TreeExplainer(self.model)
        
    def predict_and_explain(self, current_sensor_data: pd.DataFrame) -> dict:
        """Predicts current health and outputs SHAP feature importance."""
        if not self.explainer:
            raise ValueError("Model must be trained before predicting.")
            
        pred_health = self.model.predict(current_sensor_data)[0]
        
        # Calculate SHAP values for this specific real-time reading
        single_shap_values = self.explainer.shap_values(current_sensor_data)[0]
        
        # Map SHAP values to feature names and sort by absolute impact
        shap_impact = sorted(zip(self.feature_cols, single_shap_values), key=lambda x: abs(x[1]), reverse=True)
        
        return {
            "predicted_health": pred_health,
            "top_contributors": shap_impact[:3] # Top 3 sensors driving the prediction
        }

# --- Execution Block ---
if __name__ == "__main__":
    # 1. Initialize the AI
    ai_engine = NavalPropulsionAI('navalplantmaintenance.csv')
    
    # 2. Load & Train
    df = ai_engine.load_and_preprocess()
    ai_engine.train(df)
    
    # 3. Simulate a "Current State" reading (taking the last row of the dataset)
    current_state = df[ai_engine.feature_cols].tail(1)
    
    # 4. Predict & Explain
    results = ai_engine.predict_and_explain(current_state)
    
    # 5. The "Senior Engineer" Dashboard Output
    print("\n" + "="*50)
    print(" 🚢 NAVAL PROPULSION AI (XAI ENABLED)")
    print("="*50)
    print(f"PREDICTED COMPRESSOR HEALTH: {results['predicted_health']*100:.2f}%")
    print("-" * 50)
    print("🔍 SHAP EXPLAINABILITY (Why did the AI predict this?):")
    for feature, impact in results['top_contributors']:
        # Negative SHAP impact means this sensor pushed the health score DOWN
        direction = "⬇️ Degrading Health" if impact < 0 else "⬆️ Stabilizing Health" 
        print(f"  • {feature:<15}: {impact:+.5f} impact ({direction})")
    print("="*50)