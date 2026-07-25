import re
from rapidfuzz import process, fuzz

# --- DATA DICTIONARIES ---
NAVY_ABBR_MAP = {
    "gt": "gas turbine", "lo": "lube oil", "cpp": "controllable pitch propeller",
    "mpde": "main propulsion diesel engine", "hpt": "high pressure turbine", 
    "lpt": "low pressure turbine"
}

COMPONENTS = ["bearing", "compressor", "turbine", "injector", "pump", "seal"]

# FIXED: Added fire as a symptom
SYMPTOMS = ["vibration", "overheat", "leak", "smoke", "clog", "friction", "fire"]

SEVERITY_WEIGHTS = {
    "critical": 0.5, "smoke": 0.5, "seized": 0.6, "severe": 0.4, 
    "heavy": 0.3, "fire": 0.7, "slight": -0.2, "minor": -0.2, 
    "routine": -0.3, "normal": -0.3
}

# FIXED: Added stopwords to prevent false matches
STOPWORDS = {"in", "the", "a", "an", "and", "or", "of", "to", "for", "with", "on", "at", "from"}

class SemanticEnricher:
    """
    Extracts maintenance components, symptoms, and calculates urgency severity
    from noisy naval engineering text with typo tolerance.
    """
    
    def __init__(self, abbr_map, components, symptoms, severity_map, stopwords):
        self.abbr_map = abbr_map
        self.components = components
        self.symptoms = symptoms
        self.severity_map = severity_map
        self.stopwords = stopwords
        # Cache severity keys for performance
        self.severity_keys = list(severity_map.keys())
        self.threshold = 85  # FIXED: Restored to 85 for precision
        self.min_word_length = 3  # FIXED: Skip very short words

    def clean_and_expand(self, text):
        """
        Step 1: Expand naval jargon abbreviations
        Step 2: Strip punctuation for clean tokenization
        """
        if not text or not isinstance(text, str):
            return ""
        
        text = text.lower()
        
        # Abbreviation expansion with word boundaries
        for abbr, full in self.abbr_map.items():
            text = re.sub(r'\b' + re.escape(abbr) + r'\b', full, text)
        
        # Punctuation stripping
        text = re.sub(r'[^\w\s]', '', text)
        
        return text

    def extract_features(self, text):
        """
        Extracts components and symptoms from text using fuzzy matching.
        
        Returns:
            tuple: (found_parts, found_issues, clean_text)
        """
        if not text or not isinstance(text, str):
            return [], [], ""
        
        clean_text = self.clean_and_expand(text)
        found_parts = []
        found_issues = []

        for word in clean_text.split():
            # FIXED: Skip stopwords and very short words
            if word in self.stopwords or len(word) < self.min_word_length:
                continue
            
            # Component fuzzy search
            c_res = process.extractOne(word, self.components, scorer=fuzz.WRatio)
            if c_res and c_res[1] >= self.threshold:
                found_parts.append(c_res[0])
            
            # Symptom fuzzy search
            s_res = process.extractOne(word, self.symptoms, scorer=fuzz.WRatio)
            if s_res and s_res[1] >= self.threshold:
                found_issues.append(s_res[0])

        return list(set(found_parts)), list(set(found_issues)), clean_text

    def calculate_severity(self, clean_text, detected_issues):
        """
        Quantifies urgency with fuzzy-tolerant severity adjective detection.
        
        Severity Scale:
        - 0.7+ = CRITICAL (immediate action required)
        - 0.4-0.7 = WARNING (schedule maintenance)
        - <0.4 = ROUTINE (monitor)
        
        Args:
            clean_text: Preprocessed text string
            detected_issues: List of identified symptoms
            
        Returns:
            float: Severity score between 0.1 and 1.0
        """
        # FIXED: Don't return early - check for severity modifiers first
        score = 0.3 if detected_issues else 0.1
        
        # Add base score for number of issues
        if detected_issues:
            score += 0.2 * len(detected_issues)
        
        # Scan for severity modifiers
        for word in clean_text.split():
            if word in self.stopwords or len(word) < self.min_word_length:
                continue
                
            best_match = process.extractOne(word, self.severity_keys, 
                                           scorer=fuzz.WRatio)
            if best_match and best_match[1] >= self.threshold:
                modifier = self.severity_map[best_match[0]]
                score += modifier
                
                # FIXED: If we detect critical modifiers, ensure non-zero severity
                if modifier > 0 and score < 0.3:
                    score = 0.3
        
        # Clamp to valid range
        return round(max(0.1, min(1.0, score)), 2)

    def analyze(self, text):
        """
        Complete analysis pipeline for a maintenance report.
        
        Returns:
            dict: Analysis results with parts, issues, severity, and metadata
        """
        parts, issues, clean = self.extract_features(text)
        severity = self.calculate_severity(clean, issues)
        
        # Classify severity level
        if severity >= 0.7:
            level = "CRITICAL"
        elif severity >= 0.4:
            level = "WARNING"
        else:
            level = "ROUTINE"
        
        return {
            "original_text": text,
            "components": parts,
            "symptoms": issues,
            "severity_score": severity,
            "severity_level": level,
            "cleaned_text": clean
        }


# --- COMPREHENSIVE TEST SUITE ---
def run_audit():
    """Validates typo tolerance, punctuation handling, and severity scaling."""
    
    enricher = SemanticEnricher(NAVY_ABBR_MAP, COMPONENTS, SYMPTOMS, SEVERITY_WEIGHTS, STOPWORDS)
    
    audit_cases = [
        ("critial smoek in gt!!", "Critical typos + punctuation"),
        ("hevy vibratn; check lpt", "Typos + semicolon"),
        ("routine check: no issues", "Healthy baseline (no symptoms)"),
        ("minor leakng...", "Trailing dots + low severity"),
        ("fire in mpde bearing!!", "Multi-word expansion + critical"),
        ("severe friction and overheat in compressor", "Multiple issues"),
        ("normal pump operation", "Negative severity modifier"),
        ("", "Empty string edge case"),
        ("seized turbine with smoke", "Extreme severity combo")
    ]
    
    print("=" * 80)
    print("SEMANTIC ENRICHER v1.1 - AUDIT REPORT (BUGS FIXED)")
    print("=" * 80 + "\n")
    
    for case, description in audit_cases:
        result = enricher.analyze(case)
        
        print(f"TEST: {description}")
        print(f"INPUT: '{case}'")
        print(f"COMPONENTS: {result['components']}")
        print(f"SYMPTOMS: {result['symptoms']}")
        print(f"SEVERITY: {result['severity_score']} ({result['severity_level']})")
        print(f"CLEANED: '{result['cleaned_text']}'")
        print("-" * 80 + "\n")


if __name__ == "__main__":
    run_audit()