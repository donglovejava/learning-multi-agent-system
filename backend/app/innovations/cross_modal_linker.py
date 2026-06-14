"""跨模态知识关联（IN-01, P1）。

将文档、视频、题目、代码等不同模态的资源关联到同一个知识图谱节点，
实现"学一个自动推其他"的跨模态跳转能力。

设计依据：设计说明书 §3.4。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CrossModalLinker:
    """跨模态知识关联器。

    依赖 Neo4j driver。通过 ``HAS_RESOURCE`` 关系把资源节点挂到知识点节点上，
    并支持按时间戳查询视频片段对应的文档段落。
    """

    def __init__(self, driver: Any) -> None:
        # driver: neo4j.GraphDatabase.driver 实例（由 DI 注入，便于测试 mock）
        self._driver = driver

    def link_resources(self, knowledge_id: str, resources: list[dict]) -> int:
        """将一组不同模态的资源关联到同一知识点。

        Args:
            knowledge_id: 知识点 ID。
            resources: 资源列表，每项含 id/type/url/modal/metadata。

        Returns:
            成功关联的资源数量。
        """
        linked = 0
        with self._driver.session() as session:
            for res in resources:
                session.run(
                    """
                    MATCH (k:Knowledge {id: $kid})
                    MERGE (r:Resource {id: $rid})
                    SET r.type = $type, r.url = $url, r.metadata = $metadata
                    MERGE (k)-[:HAS_RESOURCE {modal: $modal}]->(r)
                    """,
                    kid=knowledge_id,
                    rid=res["id"],
                    type=res["type"],
                    url=res.get("url", ""),
                    metadata=res.get("metadata", {}),
                    modal=res.get("modal", "text"),
                )
                linked += 1
        logger.info("知识点 %s 关联了 %d 个跨模态资源", knowledge_id, linked)
        return linked

    def get_related_resources(
        self, knowledge_id: str, current_type: str
    ) -> list[dict]:
        """获取与当前资源关联的其他模态资源。"""
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (k:Knowledge {id: $kid})-[:HAS_RESOURCE]->(r:Resource)
                WHERE r.type <> $current_type
                RETURN r.id AS id, r.type AS type, r.url AS url,
                       r.metadata AS metadata
                """,
                kid=knowledge_id,
                current_type=current_type,
            )
            return [dict(record) for record in result]

    def get_timestamp_link(self, video_id: str, timestamp: float) -> dict | None:
        """根据视频时间戳获取关联的文档段落。"""
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (v:Resource {id: $vid, type: 'video'})<-[:HAS_RESOURCE]-(k:Knowledge)
                      -[:HAS_RESOURCE]->(d:Resource {type: 'document'})
                WHERE $timestamp >= v.start_time AND $timestamp <= v.end_time
                RETURN d.id AS doc_id, d.url AS doc_url
                """,
                vid=video_id,
                timestamp=timestamp,
            )
            record = result.single()
            return dict(record) if record else None
