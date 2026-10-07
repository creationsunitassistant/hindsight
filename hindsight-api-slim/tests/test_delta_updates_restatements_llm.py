"""A delta refresh updates every block a new fact refutes, not just the main one (#5228).

The reported page said the pump's owner was Zhang in one section and, in its source
notes, "no evidence of a manual update or owner change was found". A dated V2 notice
moved ownership to Li. The refresh rewrote the owner paragraph but never touched the
"no evidence of an owner change" line, so the page contradicted itself. Nothing went
wrong applying the ops: the model never emitted one for the stale block.

This is the reporter's page, kept in Chinese: an English version of it did not fail.
On gemini-3.1-flash-lite the old prompt left the stale line 12/12 times, the new one
0/10. A first wording ("check every block") also fixed it but broke
test_delta_keeps_unrefuted_claims_llm (9/10 -> 1/10): the model reasoned from neighbouring
release dates that 0.9.3 never shipped. Hence the rule is limited to blocks about the
same item the fact names.

The stale claim shares its block with an unrelated "not mentioned" claim (spare parts
supplier), and the page has another (emergency shutdown steps); both must survive, so
the fix cannot work by wiping every absence claim.
"""

from __future__ import annotations

import pytest

from hindsight_api import LLMConfig
from hindsight_api.config import _get_raw_config
from hindsight_api.engine.reflect.delta_ops import DeltaOperationList, apply_operations, request_delta_operations
from hindsight_api.engine.reflect.prompts import STRUCTURED_DELTA_SYSTEM_PROMPT, build_structured_delta_prompt
from hindsight_api.engine.reflect.structured_doc import Block, Section, StructuredDocument, render_document
from tests.llm_judge import assert_meets_criteria

pytestmark = pytest.mark.hs_llm_core


def _section(id: str, heading: str, *blocks: tuple[str, str]) -> Section:
    return Section(id=id, heading=heading, level=2, blocks=[Block(id=bid, text=text) for bid, text in blocks])


async def test_a_refuted_absence_claim_in_a_distant_section_is_updated():
    document = StructuredDocument(
        sections=[
            _section(
                "section-1",
                "蓝鹭泵概述",
                (
                    "b1a",
                    "本文档汇总蓝鹭泵（BH-200 型）的工作参数、维护周期、维护责任人及资料来源，"
                    "依据《蓝鹭泵操作与维护手册 V1》整理。",
                ),
            ),
            _section(
                "section-2",
                "工作参数",
                (
                    "b2a",
                    "| 参数 | 数值 |\n| --- | --- |\n| 额定转速 | 1450 rpm |\n| 最大压力 | 6 bar |\n"
                    "| 额定流量 | 120 m³/h |\n| 工作温度 | 5–60 °C |",
                ),
            ),
            _section(
                "section-3",
                "维护周期",
                (
                    "b3a",
                    "- 滤芯：每运行 1000 小时更换一次。\n- 轴承润滑：每运行 2000 小时检查一次。\n- 密封件：每年检查一次。",
                ),
                ("b3b", "手册要求更换滤芯前必须先停机并泄压。"),
            ),
            _section("section-4", "停机安全", ("b4a", "手册要求停机前关闭进口阀门，但未给出完整的紧急停机步骤。")),
            _section(
                "section-5",
                "维护责任",
                ("b0866fc29", "蓝鹭泵的维护责任人为张工（来源：《蓝鹭泵操作与维护手册 V1》）。"),
            ),
            _section(
                "section-6",
                "资料来源与说明",
                ("b6a", "主要来源：《蓝鹭泵操作与维护手册 V1》。"),
                (
                    "b9581bae9",
                    "以上内容均来自手册 V1；资料中未提及备件供应商信息，也未发现手册版本更新或负责人变更的证据。",
                ),
            ),
        ]
    )
    facts = [
        {
            "id": "f1",
            "type": "world",
            "text": "《维护变更通知 V2》于 2026 年 10 月 5 日生效，用以加强蓝鹭泵的维护管理。",
        },
        {
            "id": "f2",
            "type": "world",
            "text": "自 2026 年 10 月 5 日起，蓝鹭泵滤芯更换周期由每运行 1000 小时缩短为每运行 800 小时。",
        },
        {"id": "f3", "type": "world", "text": "自 2026 年 10 月 5 日起，蓝鹭泵维护负责人由张工变更为李工。"},
        {"id": "f4", "type": "world", "text": "《维护变更通知 V2》确认蓝鹭泵的工作参数与停机安全步骤维持不变。"},
    ]
    user_prompt = build_structured_delta_prompt(
        current_document_json=document.model_dump_json(),
        supporting_facts=facts,
        source_query="蓝鹭泵的工作参数、维护周期、维护责任人和资料来源是什么？",
    )
    llm = LLMConfig.from_env().with_config(_get_raw_config())

    op_list = await request_delta_operations(
        llm,
        system_prompt=STRUCTURED_DELTA_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        scope="test_delta_updates_restatements",
        response_format=DeltaOperationList,
        skip_validation=True,
        document=document,
    )
    page = render_document(apply_operations(document, op_list.operations).document)

    await assert_meets_criteria(
        response=page,
        criteria=(
            "1) The page says the current maintenance owner is Li (李工) since 2026-10-05 and the filter interval "
            "is 800 hours. 2) The page does NOT anywhere still claim that no manual version update or no owner "
            "change was found. 3) The page still says the sources do not mention the spare parts supplier "
            "(备件供应商). 4) The page still says the full emergency shutdown steps are not given. 5) The operating "
            "parameters table (1450 rpm, 6 bar) is still present."
        ),
        context=(
            "The page is in Chinese. Before the refresh it said the owner was Zhang (张工), the filter interval "
            "1000 hours, and its source notes said no evidence of a manual version update or owner change was "
            "found (也未发现手册版本更新或负责人变更的证据). The new facts are a V2 notice, effective 2026-10-05, "
            "moving the interval to 800 hours and the owner from Zhang to Li, and keeping parameters and shutdown "
            "steps unchanged. They say nothing about the spare parts supplier."
        ),
    )
