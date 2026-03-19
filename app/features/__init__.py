from app.features.adventure.adventure_feature import AdventureFeature
from app.features.tower_feature import TowerFeature
from app.features.adventurenormal import AdventureNormal

FEATURES = {
    AdventureFeature.key: AdventureFeature,
    TowerFeature.key: TowerFeature,
    AdventureNormal.key: AdventureNormal,
}

FEATURE_OPTIONS = [
    (AdventureFeature.key, AdventureFeature.name),
    (TowerFeature.key, TowerFeature.name),
    (AdventureNormal.key, AdventureNormal.name),
]