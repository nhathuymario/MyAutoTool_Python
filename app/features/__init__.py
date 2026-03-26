from app.features.adventure.adventure_feature import AdventureFeature
from app.features.tower_feature import TowerFeature
from app.features.adventurenormal import AdventureNormal
from app.features.alliance_feature import AllianceFeature

FEATURES = {
    AdventureFeature.key: AdventureFeature,
    TowerFeature.key: TowerFeature,
    AdventureNormal.key: AdventureNormal,
    AllianceFeature.key: AllianceFeature,
}

FEATURE_OPTIONS = [
    (AdventureFeature.key, AdventureFeature.name),
    (TowerFeature.key, TowerFeature.name),
    (AdventureNormal.key, AdventureNormal.name),
    (AllianceFeature.key, AllianceFeature.name),
]