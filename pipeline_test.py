import pandas as pd
import logging
from semantic_test import SemanticEnricher, NAVY_ABBR_MAP, COMPONENTS, SYMPTOMS, SEVERITY_WEIGHTS, STOPWORDS
from MultiModalMapper import MultiModalMapper
from naval_brain import NavalPropulsionAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MultimodalDiagnosticPipeline:
    """
    Integrates NLP-based maintenance logs with ML-based sensor diagnostics.
    This is the 'Senior Engineer' flex: a closed-loop system where human context 
    drives targeted AI analysis.
    """
    def __init__(self, data_path: str):
        # 1. Initialize the NLP Brain
        self.enricher = SemanticEnricher(
            NAVY_ABBR_MAP, COMPONENTS, SYMPTOMS, SEVERITY_WEIGHTS, STOPWORDS
        )
        self.mapper = MultiModalMapper(spatial_format="short", case_sensitive=False)
        
        # 2. Initialize the AI Brain (ML + SHAP)
        self.ai_engine = NavalPropulsionAI(data_path)
        self.df = None
        self.is_trained = False

    def initialize(self):
        """Loads data and trains the AI model."""
        logging.info("🚀 Initializing Multimodal Pipeline...")
        self.df = self.ai_engine.load_and_preprocess()
        self.ai_engine.train(self.df)
        self.is_trained = True
        logging.info("✅ Pipeline Ready. AI Model Trained.")

    def process_maintenance_log(self, log_text: str):
        """
        Takes a raw technician log and returns a combined diagnostic report.
        """
        if not self.is_trained:
            raise RuntimeError("Pipeline not initialized. Call .initialize() first.")

        # Step 1: NLP Enrichment (The 'Human' Layer)
        semantic_output = self.enricher.analyze(log_text)
        
        # Step 2: Sensor Mapping (The 'Bridge' Layer)
        mapping_result = self.mapper.resolve_mapping(
            semantic_output, 
            available_columns=self.ai_engine.feature_cols
        )

        # Step 3: AI Diagnostics (The 'Machine' Layer)
        # We use the last row of data as the "current state" for this demo
        current_state = self.df[self.ai_engine.feature_cols].tail(1)
        ai_prediction = self.ai_engine.predict_and_explain(current_state)

        # Step 4: Combine Results into a Senior-Engineer Report
        report = {
            "log_entry": log_text,
            "nlp_insights": {
                "detected_components": mapping_result["mapped_components"],
                "resolved_symptoms": mapping_result["resolved_symptoms"],
                "spatial_context": mapping_result["spatial_context"],
                "targeted_sensors": mapping_result["mapped_sensors"]
            },
            "ai_diagnostics": {
                "predicted_health": ai_prediction["predicted_health"],
                "top_contributors": ai_prediction["top_contributors"][:3] # Top 3 drivers
            }
        }
        
        return report

# --- Execution Block ---
if __name__ == "__main__":
    # Initialize the pipeline
    pipeline = MultimodalDiagnosticPipeline('navalplantmaintenance.csv')
    pipeline.initialize()

    # Simulate a technician log
    technician_log = "Noticed severe vibration and high temp on the port side turbine."
    
    # Process the log
    report = pipeline.process_maintenance_log(technician_log)

    # Display the "Senior Engineer" Dashboard Output
    print("\n" + "="*60)
    print(" 🛠️  MULTIMODAL DIAGNOSTIC REPORT")
    print("="*60)
    print(f"LOG ENTRY: \"{report['log_entry']}\"")
    print("-" * 60)
    print("🔍 NLP INSIGHTS:")
    print(f"  • Components : {report['nlp_insights']['detected_components']}")
    print(f"  • Symptoms   : {report['nlp_insights']['resolved_symptoms']}")
    print(f"  • Spatial    : {report['nlp_insights']['spatial_context']}")
    print(f"  • Sensors    : {report['nlp_insights']['targeted_sensors']}")
    print("-" * 60)
    print("🧠 AI DIAGNOSTICS:")
    print(f"  • Predicted Health: {report['ai_diagnostics']['predicted_health']*100:.2f}%")
    print("  • Top Drivers (SHAP):")
    for feature, impact in report['ai_diagnostics']['top_contributors']:
        direction = "⬇️ Degrading" if impact < 0 else "⬆️ Stabilizing"
        print(f"    - {feature:<15}: {impact:+.5f} ({direction})")
    print("="*60)