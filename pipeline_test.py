from semantic_test import SemanticEnricher, NAVY_ABBR_MAP, COMPONENTS, SYMPTOMS, SEVERITY_WEIGHTS, STOPWORDS
from MultiModalMapper import MultiModalMapper

enricher = SemanticEnricher(
    NAVY_ABBR_MAP,
    COMPONENTS,
    SYMPTOMS,
    SEVERITY_WEIGHTS,
    STOPWORDS
)

mapper = MultiModalMapper()

log = "gearbox failure port side"

semantic_output = enricher.analyze(log)
mapping_output = mapper.resolve_mapping(semantic_output)

print(semantic_output)
print(mapping_output)