import re
import logging

# Configure logging for production debugging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiModalMapper:
    """
    Maps NLP-extracted maintenance issues to physical sensor columns.
    Handles spatial context (port/starboard), symptom prioritization, and sensor validation.
    
    Version: 2.1 (Production Ready - Final)
    """
    
    def __init__(self, spatial_format="short", case_sensitive=False):
        """
        Initialize the mapper with asset registry and configuration.
        
        Args:
            spatial_format (str): Sensor naming convention
                - "short": _P/_S (default)
                - "full": _PORT/_STBD
                - "numeric": _1/_2
            case_sensitive (bool): If False, normalizes all column names to uppercase
        """
        # BLOCK 1: Asset Registry - Component to Sensor Mapping
        self.asset_map = {
            "turbine": ["GT_RPM", "GT_EXH_TEMP", "GT_VIB"],
            "bearing": ["BRG_FWD_TEMP", "BRG_AFT_TEMP", "BRG_VIB_RMS"],
            "pump": ["LO_PUMP_PSI", "LO_PUMP_AMP"],
            "compressor": ["COMP_IN_TEMP", "COMP_OUT_PRESS"],
            "injector": ["FUEL_RAIL_PRESS", "CYL_FIRE_TEMP"],
            "seal": ["SEAL_WATER_FLOW", "GLAND_TEMP"]
        }
        
        # BLOCK 2: Symptom-to-Sensor Priority Matrix
        self.symptom_priority = {
            "vibration": ["VIB", "RMS"],
            "overheat": ["TEMP", "EXH_TEMP"],
            "leak": ["FLOW", "PSI"],
            "smoke": ["EXH_TEMP", "FIRE_TEMP"],
            "fire": ["FIRE_TEMP", "EXH_TEMP"],
            "friction": ["VIB", "TEMP"],
            "clog": ["FLOW", "PRESS"]
        }
        
        # BLOCK 3: Symptom Synonym Dictionary (FIX: Concern 4)
        # Maps alternate terms to canonical symptom names
        self.symptom_synonyms = {
            "oscillation": "vibration",
            "shaking": "vibration",
            "tremor": "vibration",
            "hot": "overheat",
            "overheating": "overheat",
            "high temp": "overheat",
            "drip": "leak",
            "leaking": "leak",
            "seepage": "leak",
            "fumes": "smoke",
            "smoking": "smoke",
            "blaze": "fire",
            "burning": "fire",
            "blockage": "clog",
            "clogged": "clog",
            "obstruction": "clog",
            "rubbing": "friction",
            "grinding": "friction"
        }
        
        # BLOCK 4: Spatial Suffix Configuration
        self.spatial_suffixes = {
            "short": {"port": "_P", "starboard": "_S"},
            "full": {"port": "_PORT", "starboard": "_STBD"},
            "numeric": {"port": "_1", "starboard": "_2"}
        }
        
        if spatial_format not in self.spatial_suffixes:
            raise ValueError(f"Invalid spatial_format. Must be one of: {list(self.spatial_suffixes.keys())}")
        
        self.format = spatial_format
        self.case_sensitive = case_sensitive
        
        # Track unknown components for debugging
        self.unknown_components = set()
        self.unknown_symptoms = set()
    
    def normalize_case(self, items):
        """
        Normalize case for consistent matching (FIX: Concern 2).
        
        Args:
            items (list or str): Column names or sensor names
            
        Returns:
            list or str: Normalized items (uppercase if not case_sensitive)
        """
        if self.case_sensitive:
            return items
        
        if isinstance(items, str):
            return items.upper()
        elif isinstance(items, list):
            return [item.upper() for item in items]
        return items
    
    def resolve_symptom_synonyms(self, symptoms):
        """
        Expand symptoms using synonym dictionary (FIX: Concern 4).
        
        Args:
            symptoms (list): Raw symptom list from NLP
            
        Returns:
            list: Canonical symptom names
            
        Example:
            ["oscillation", "hot"] → ["vibration", "overheat"]
        """
        resolved = []
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            
            # Check if it's a synonym
            if symptom_lower in self.symptom_synonyms:
                canonical = self.symptom_synonyms[symptom_lower]
                resolved.append(canonical)
                logger.info(f"Resolved symptom synonym: '{symptom}' → '{canonical}'")
            # Check if it's already canonical
            elif symptom_lower in self.symptom_priority:
                resolved.append(symptom_lower)
            else:
                # Unknown symptom - log it but keep it
                self.unknown_symptoms.add(symptom)
                logger.warning(f"Unknown symptom detected: '{symptom}' (not in priority map or synonyms)")
                resolved.append(symptom_lower)
        
        return list(set(resolved))
    
    def extract_spatial_context(self, text):
        """
        Extract port/starboard context from text using word boundary protection.
        
        Args:
            text (str): Raw maintenance log text
            
        Returns:
            str: "port", "starboard", or "both"
            
        Examples:
            "port side turbine" → "port"
            "starboard GT issue" → "starboard"
            "check both turbines" → "both"
            "transport damaged" → "both" (ignores false match)
        """
        text = text.lower()
        
        # Word boundary patterns prevent false matches like "transport" or "oportune"
        port_pattern = r'\b(port|left|ps)\b'
        stbd_pattern = r'\b(starboard|stbd|right|ss)\b'
        
        has_port = bool(re.search(port_pattern, text))
        has_stbd = bool(re.search(stbd_pattern, text))
        
        if has_port and not has_stbd:
            return "port"
        elif has_stbd and not has_port:
            return "starboard"
        else:
            return "both"
    
    def apply_symptom_filter(self, sensors, symptoms):
        """
        Filter sensors to prioritize those relevant to detected symptoms.
        
        Args:
            sensors (list): Base sensor list from component mapping
            symptoms (list): Detected symptoms from NLP (already resolved)
            
        Returns:
            list: Filtered sensor list (or original if no symptom match)
        """
        if not symptoms:
            return sensors
        
        # Collect all relevant sensor keywords from detected symptoms
        relevant_keywords = []
        for symptom in symptoms:
            if symptom in self.symptom_priority:
                relevant_keywords.extend(self.symptom_priority[symptom])
        
        if not relevant_keywords:
            return sensors
        
        # Filter sensors containing symptom-relevant keywords
        # Normalize for case-insensitive matching
        filtered = []
        for sensor in sensors:
            sensor_upper = sensor.upper()
            if any(kw.upper() in sensor_upper for kw in relevant_keywords):
                filtered.append(sensor)
        
        # Return filtered if we found matches, otherwise return all (safety fallback)
        return filtered if filtered else sensors
    
    def validate_sensors(self, sensor_list, available_columns):
        """
        Validate mapped sensors against actual CSV columns (FIX: Concern 2).
        
        Args:
            sensor_list (list): Sensors from mapping logic
            available_columns (list): Actual column names from CSV/database
            
        Returns:
            dict: Validation report with valid/missing sensors and coverage ratio
        """
        # Normalize both lists for comparison
        normalized_sensors = self.normalize_case(sensor_list)
        normalized_columns = self.normalize_case(available_columns)
        
        # Build lookup set for O(1) checking
        column_set = set(normalized_columns)
        
        # Track valid and missing
        valid = []
        missing = []
        
        for i, norm_sensor in enumerate(normalized_sensors):
            if norm_sensor in column_set:
                # Return original case from sensor_list
                valid.append(sensor_list[i])
            else:
                missing.append(sensor_list[i])
        
        if missing:
            logger.warning(f"Missing sensors in CSV: {missing}")
        
        return {
            "valid_sensors": valid,
            "missing_sensors": missing,
            "coverage": len(valid) / len(sensor_list) if sensor_list else 0.0
        }
    
    def resolve_mapping(self, nlp_result, available_columns=None):
        """
        Core mapping function: NLP output → Sensor columns
        
        Args:
            nlp_result (dict): Output from SemanticEnricher.analyze() containing:
                - original_text: Raw maintenance log
                - components: List of detected parts
                - symptoms: List of detected issues
                - severity_score: Urgency score (0.1-1.0)
                - severity_level: Classification (CRITICAL/WARNING/ROUTINE)
            available_columns (list, optional): CSV columns for validation
            
        Returns:
            dict: Complete mapping result with sensors, severity, and metadata
        """
        detected_parts = nlp_result.get("components", [])
        symptoms = nlp_result.get("symptoms", [])
        raw_text = nlp_result.get("original_text", "").lower()
        
        # FIX: Concern 4 - Resolve symptom synonyms
        resolved_symptoms = self.resolve_symptom_synonyms(symptoms)
        
        # STEP 1: Determine spatial context (port/starboard/both)
        spatial = self.extract_spatial_context(raw_text)
        suffix_map = self.spatial_suffixes[self.format]
        
        # STEP 2: Build base sensor list from detected components
        target_sensors = []
        mapped_components = []
        
        for part in detected_parts:
            if part in self.asset_map:
                base_sensors = self.asset_map[part]
                mapped_components.append(part)
                
                if spatial == "both":
                    # Add sensors for both sides
                    for s in base_sensors:
                        target_sensors.append(s + suffix_map["port"])
                        target_sensors.append(s + suffix_map["starboard"])
                else:
                    # Add sensors for specified side only
                    suffix = suffix_map[spatial]
                    target_sensors.extend([s + suffix for s in base_sensors])
            else:
                # FIX: Concern 3 - Log unknown components
                self.unknown_components.add(part)
                logger.warning(f"Unknown component detected: '{part}' (not in asset_map)")
        
        # Log if no components were mapped
        if not mapped_components and detected_parts:
            logger.error(f"No components mapped! Detected: {detected_parts}, Available: {list(self.asset_map.keys())}")
        
        # STEP 3: Apply symptom-based filtering
        target_sensors = self.apply_symptom_filter(target_sensors, resolved_symptoms)
        target_sensors = list(set(target_sensors))  # Remove duplicates
        
        # STEP 4: Validate against actual CSV columns (if provided)
        validation_result = None
        if available_columns is not None:
            validation_result = self.validate_sensors(target_sensors, available_columns)
            # Use only validated sensors for production safety
            target_sensors = validation_result["valid_sensors"]
        
        # STEP 5: Build comprehensive result
        result = {
            "mapped_sensors": target_sensors,
            "sensor_query_string": ", ".join(target_sensors),
            "severity": nlp_result.get("severity_score", 0.1),
            "severity_level": nlp_result.get("severity_level", "ROUTINE"),
            "spatial_context": spatial,
            "detected_components": detected_parts,
            "mapped_components": mapped_components,  # Only successfully mapped ones
            "unmapped_components": list(self.unknown_components),
            "detected_symptoms": symptoms,
            "resolved_symptoms": resolved_symptoms,  # After synonym expansion
            "original_text": nlp_result.get("original_text", "")
        }
        
        if validation_result:
            result["validation"] = validation_result
        
        return result
    
    def get_diagnostics(self):
        """
        Return diagnostic information about unknown components/symptoms encountered.
        Useful for expanding the asset_map and symptom dictionaries.
        
        Returns:
            dict: Sets of unknown components and symptoms
        """
        return {
            "unknown_components": list(self.unknown_components),
            "unknown_symptoms": list(self.unknown_symptoms),
            "registered_components": list(self.asset_map.keys()),
            "registered_symptoms": list(self.symptom_priority.keys()),
            "symptom_synonyms": self.symptom_synonyms
        }
    
    def get_query_filter(self, mapping_result):
        """
        Generate Pandas query filter from mapping result.
        
        Args:
            mapping_result (dict): Output from resolve_mapping()
            
        Returns:
            dict: Query parameters for DataFrame filtering
        """
        return {
            "columns": mapping_result["mapped_sensors"],
            "severity_threshold": mapping_result["severity"],
            "spatial_filter": mapping_result["spatial_context"]
        }


# ============================================================================
# PRODUCTION TEST SUITE
# ============================================================================

def run_production_tests():
    """
    Comprehensive test suite validating all mapper functionality.
    Tests: spatial detection, symptom filtering, validation, edge cases, synonyms.
    """
    
    # Initialize mapper (case-insensitive mode)
    mapper = MultiModalMapper(spatial_format="short", case_sensitive=False)
    
    # Mock CSV columns with INCONSISTENT CASING (realistic scenario)
    mock_csv_columns = [
        "gt_rpm_p", "GT_RPM_S",  # Mixed case
        "gt_exh_temp_p", "GT_EXH_TEMP_S",
        "GT_VIB_P", "gt_vib_s",
        "brg_fwd_temp_p", "BRG_FWD_TEMP_S",
        "BRG_AFT_TEMP_P", "brg_vib_rms_p", "BRG_VIB_RMS_S",
        "LO_PUMP_PSI_P", "lo_pump_psi_s",
        "LO_PUMP_AMP_P",
        "COMP_IN_TEMP_S", "comp_out_press_s",
        "seal_water_flow_p"
    ]
    
    test_cases = [
        {
            "name": "Critical vibration with spatial context",
            "nlp_output": {
                "original_text": "critical vibration in port gt hpt",
                "components": ["turbine"],
                "symptoms": ["vibration"],
                "severity_score": 0.9,
                "severity_level": "CRITICAL"
            }
        },
        {
            "name": "Synonym expansion test (oscillation → vibration)",
            "nlp_output": {
                "original_text": "severe oscillation starboard bearing",
                "components": ["bearing"],
                "symptoms": ["oscillation"],  # Should resolve to "vibration"
                "severity_score": 0.8,
                "severity_level": "CRITICAL"
            }
        },
        {
            "name": "Unknown component (gearbox not in asset_map)",
            "nlp_output": {
                "original_text": "gearbox failure port side",
                "components": ["gearbox"],  # Not in asset_map
                "symptoms": [],
                "severity_score": 0.7,
                "severity_level": "WARNING"
            }
        },
        {
            "name": "Case insensitive validation",
            "nlp_output": {
                "original_text": "pump leak detected",
                "components": ["pump"],
                "symptoms": ["leak"],
                "severity_score": 0.5,
                "severity_level": "WARNING"
            }
        },
        {
            "name": "Multiple symptoms with synonyms",
            "nlp_output": {
                "original_text": "hot compressor with grinding noise",
                "components": ["compressor"],
                "symptoms": ["hot", "grinding"],  # hot→overheat, grinding→friction
                "severity_score": 0.8,
                "severity_level": "CRITICAL"
            }
        },
        {
            "name": "Both sides with fire",
            "nlp_output": {
                "original_text": "fire in injector",
                "components": ["injector"],
                "symptoms": ["fire"],
                "severity_score": 1.0,
                "severity_level": "CRITICAL"
            }
        }
    ]
    
    print("=" * 80)
    print("MULTIMODAL MAPPER v2.1 - PRODUCTION TEST SUITE (FINAL)")
    print("=" * 80 + "\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"TEST {i}: {test['name']}")
        print(f"INPUT: '{test['nlp_output']['original_text']}'")
        print("-" * 80)
        
        # Run mapping with validation
        result = mapper.resolve_mapping(
            test['nlp_output'], 
            available_columns=mock_csv_columns
        )
        
        # Display results
        print(f"Components       : {result['detected_components']}")
        if result['unmapped_components']:
            print(f"⚠️  Unmapped     : {result['unmapped_components']}")
        print(f"Mapped           : {result['mapped_components']}")
        print(f"Symptoms (raw)   : {result['detected_symptoms']}")
        if result['detected_symptoms'] != result['resolved_symptoms']:
            print(f"Symptoms (resolved): {result['resolved_symptoms']}")
        print(f"Spatial          : {result['spatial_context']}")
        print(f"Severity         : {result['severity']} ({result['severity_level']})")
        print(f"Mapped Sensors   : {result['mapped_sensors']}")
        
        if "validation" in result:
            val = result["validation"]
            print(f"\nValidation:")
            print(f"  ✓ Valid      : {val['valid_sensors']}")
            if val['missing_sensors']:
                print(f"  ✗ Missing    : {val['missing_sensors']}")
            print(f"  Coverage     : {val['coverage']:.0%}")
        
        print(f"\nQuery String     : {result['sensor_query_string']}")
        print("=" * 80 + "\n")
    
    # Show diagnostics
    print("\n" + "=" * 80)
    print("DIAGNOSTICS REPORT")
    print("=" * 80)
    diag = mapper.get_diagnostics()
    if diag['unknown_components']:
        print(f"⚠️  Unknown Components: {diag['unknown_components']}")
        print("   → Add these to asset_map if they're valid")
    if diag['unknown_symptoms']:
        print(f"⚠️  Unknown Symptoms: {diag['unknown_symptoms']}")
        print("   → Add these to symptom_priority or symptom_synonyms")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_production_tests()