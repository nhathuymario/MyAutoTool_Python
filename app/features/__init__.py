from app.features.adventure.adventure_feature import AdventureFeature
from app.features.tower_feature import TowerFeature

FEATURES = {
    AdventureFeature.key: AdventureFeature,
    TowerFeature.key: TowerFeature,
}

FEATURE_OPTIONS = [
    (AdventureFeature.key, AdventureFeature.name),
    (TowerFeature.key, TowerFeature.name),
]