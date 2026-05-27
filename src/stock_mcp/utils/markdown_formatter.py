"""
Markdown格式化工具
提供通用的 Markdown 表格与文档结构格式化（与 MCP Agent 端渲染兼容）
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

Section = Tuple[str, str]

# Agent 端对宽表 Markdown 渲染不稳定，与 get_kline 子表列数对齐
DEFAULT_MAX_TABLE_COLUMNS = 12

# 拆表时优先保留在每组中的锚点列（识别键）
DEFAULT_ANCHOR_COLUMN_NAMES = (
    "日期",
    "交易日期",
    "报告期",
    "财报日期",
    "报告类型",
    "代码",
    "证券代码",
    "股票代码",
    "关联代码",
    "指数代码",
    "板块代码",
    "名称",
    "证券名称",
    "股票名称",
    "关联名称",
    "指数名称",
    "板块名称",
    "排名",
)


def _stringify_cell_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "；".join(_stringify_cell_value(v) for v in value)
    if isinstance(value, dict):
        return "；".join(f"{k}: {_stringify_cell_value(v)}" for k, v in value.items())
    return str(value)


def escape_markdown_table_cell(value: Any) -> str:
    """转义表格单元格内容，避免破坏 Markdown 表格结构。"""
    text = _stringify_cell_value(value).replace("\r\n", "\n").replace("\r", "\n")
    # GFM 表格内不支持反斜杠转义管道符，改用全角竖线
    text = text.replace("|", "｜")
    text = text.replace("\n", "<br>")
    return text


def format_list_to_markdown_table(data_list: Sequence[Mapping[str, Any]]) -> str:
    """
    将列表数据格式化为 Markdown 表格

    Args:
        data_list: 字典列表，键为列名

    Returns:
        Markdown 表格字符串；无数据时返回空字符串
    """
    if not data_list:
        return ""

    columns = list(data_list[0].keys())
    if not columns:
        return ""

    header = "| " + " | ".join(escape_markdown_table_cell(col) for col in columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows: List[str] = []
    for item in data_list:
        row_data = [escape_markdown_table_cell(item.get(col, "")) for col in columns]
        rows.append("| " + " | ".join(row_data) + " |")

    return "\n".join([header, separator, *rows])


def format_dict_to_kv_table(
    data: Mapping[str, Any],
    labels: Optional[Mapping[str, str]] = None,
) -> str:
    """将字典格式化为「字段 | 值」两列 Markdown 表格。"""
    rows: List[Dict[str, str]] = []
    seen: set[str] = set()

    if labels:
        for key, label in labels.items():
            if key in data:
                rows.append({"字段": label, "值": data[key]})
                seen.add(key)

    for key, value in data.items():
        if key not in seen:
            rows.append({"字段": key, "值": value})

    return format_list_to_markdown_table(rows)


def pick_columns(
    rows: Sequence[Mapping[str, Any]],
    columns: Sequence[str],
) -> List[Dict[str, Any]]:
    """从多列行数据中选取子集列，用于拆分宽表。"""
    return [{col: row.get(col, "") for col in columns} for row in rows]


def _detect_anchor_columns(columns: Sequence[str]) -> List[str]:
    anchors: List[str] = []
    for name in DEFAULT_ANCHOR_COLUMN_NAMES:
        if name in columns and name not in anchors:
            anchors.append(name)
    if anchors:
        return anchors
    return [columns[0]] if columns else []


def _split_column_groups(
    columns: Sequence[str],
    max_columns: int,
    anchor_columns: Optional[Sequence[str]] = None,
) -> List[List[str]]:
    if not columns or len(columns) <= max_columns:
        return [list(columns)]

    anchors = list(anchor_columns) if anchor_columns else _detect_anchor_columns(columns)
    anchors = [c for c in anchors if c in columns]
    if not anchors:
        anchors = [columns[0]]

    rest = [c for c in columns if c not in anchors]
    chunk_size = max(1, max_columns - len(anchors))
    groups: List[List[str]] = []
    for i in range(0, len(rest), chunk_size):
        groups.append(anchors + rest[i : i + chunk_size])
    return groups


def _section_title_for_columns(group_cols: Sequence[str], anchors: Sequence[str]) -> str:
    data_cols = [c for c in group_cols if c not in anchors]
    if not data_cols:
        return "数据"
    if len(data_cols) == 1:
        return data_cols[0]
    if len(data_cols) <= 3:
        return "、".join(data_cols)
    return f"{data_cols[0]} … {data_cols[-1]}"


def _table_data_to_sections(
    table_data: Sequence[Mapping[str, Any]],
    *,
    max_columns: int = DEFAULT_MAX_TABLE_COLUMNS,
    anchor_columns: Optional[Sequence[str]] = None,
) -> List[Section]:
    if not table_data:
        return []

    columns = list(table_data[0].keys())
    if len(columns) <= max_columns:
        return [("", format_list_to_markdown_table(table_data))]

    anchors = list(anchor_columns) if anchor_columns else _detect_anchor_columns(columns)
    groups = _split_column_groups(columns, max_columns, anchors)
    sections: List[Section] = []
    for group in groups:
        title = _section_title_for_columns(group, anchors)
        if len(groups) > 1 and title in anchors:
            title = f"数据（{title}）"
        table = format_list_to_markdown_table(pick_columns(table_data, group))
        sections.append((title, table))
    return sections


def format_markdown_report(
    title: str,
    *,
    sections: Optional[Iterable[Section]] = None,
    table: Optional[str] = None,
    table_data: Optional[Sequence[Mapping[str, Any]]] = None,
    footnote: Optional[str] = None,
    max_table_columns: int = DEFAULT_MAX_TABLE_COLUMNS,
    anchor_columns: Optional[Sequence[str]] = None,
) -> str:
    """
    生成与 get_real_time_data / get_kline 一致结构的 Markdown 文档。

    结构：## 标题 → ### 小节（可选）→ 表格 → 脚注
    宽表（列数 > max_table_columns）自动拆成多个 ### 子表，便于 Agent 端渲染。
    """
    parts: List[str] = [f"## {title.strip()}", ""]

    if sections:
        for heading, content in sections:
            heading = heading.strip()
            body = content.strip()
            if not heading and not body:
                continue
            if heading:
                parts.extend([f"### {heading}", ""])
            if body:
                parts.append(body)
                parts.append("")

    if table_data is not None:
        auto_sections = _table_data_to_sections(
            table_data,
            max_columns=max_table_columns,
            anchor_columns=anchor_columns,
        )
        if len(auto_sections) == 1 and not auto_sections[0][0]:
            table = auto_sections[0][1]
        else:
            for heading, body in auto_sections:
                if heading:
                    parts.extend([f"### {heading}", ""])
                if body:
                    parts.append(body.strip())
                    parts.append("")

    if table and table.strip():
        parts.append(table.strip())
        parts.append("")

    if footnote and footnote.strip():
        parts.append(footnote.strip())

    return "\n".join(parts).rstrip() + "\n"
