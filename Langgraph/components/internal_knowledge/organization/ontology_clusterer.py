# /components/internal_knowledge/organization/ontology_clusterer.py
from collections import defaultdict
from typing import Dict, List

from schemas.internal_knowledge.labeling import Labeling
from schemas.internal_knowledge.relating_concepts import RelatingConcepts
from schemas.internal_knowledge.ontology import Ontology
from protocols.internal_knowledge import OntologyClustererProtocol
from components.internal_knowledge.organization.organizer import KnowledgeOrganizer
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage

@OrganizationPluginRegistry.register(OrgStage.CLUSTER, name="connected_component", is_default=True)
class ConnectedComponentClusterer(OntologyClustererProtocol):
    """3.4 基于图连通分量的确定性本体聚拢算子（零大模型开销，拓扑严格自洽）"""

    async def cluster(
        self, labels: List[Labeling], relations: List[RelatingConcepts]
    ) -> List[Ontology]:
        if not labels:
            return []

        label_map: Dict[str, Labeling] = {lbl.label_id: lbl for lbl in labels}
        parent: Dict[str, str] = {lid: lid for lid in label_map}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: str, y: str) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        for rel in relations:
            if rel.label_1_id in parent and rel.label_2_id in parent:
                union(rel.label_1_id, rel.label_2_id)

        comp_labels: Dict[str, List[str]] = defaultdict(list)
        for lid in label_map:
            comp_labels[find(lid)].append(lid)

        comp_relations: Dict[str, List[str]] = defaultdict(list)
        for rel in relations:
            if rel.label_1_id in parent:
                comp_relations[find(rel.label_1_id)].append(rel.relation_id)

        ontologies: List[Ontology] = []
        for root_id, lids in comp_labels.items():
            sorted_lids = sorted(lids)
            sorted_rids = sorted(comp_relations.get(root_id, []))

            complex_id = KnowledgeOrganizer.generate_deterministic_id("ont", "|".join(sorted_lids))
            concept_names = [label_map[lid].label for lid in sorted_lids[:5]]
            descriptor = f"知识子图: {' / '.join(concept_names)}"
            if len(sorted_lids) > 5:
                descriptor += f" 等 {len(sorted_lids)} 个核心节点"

            ontologies.append(
                Ontology(
                    complex_id=complex_id,
                    label_ids=sorted_lids,
                    relation_ids=sorted_rids,
                    descriptor=descriptor,
                )
            )

        return ontologies
