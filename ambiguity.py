"""ambiguity —— 检测评测题目里可能存在多种合理答案的地方。

找出题干中缺少限定、允许多种答案的表述，标出歧义位置

定位：
  标的是「题目本身写得不够确定」，不是「模型答错了」

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到 评测题目歧义 领域的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python ambiguity.py --help
    python ambiguity.py --file input.txt
    python ambiguity.py --text "示例内容"
    python ambiguity.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 领域规则表：每条规则独立可核查，命中即报，不做推断。
RULES: list[dict] = [
    {
        "name": "评测题目歧义·缺失",
        "why": "缺少评测题目歧义的关键要素时无法给出可靠判定",
        "severity": "high",
        "keywords": ['缺失', 'missing', 'absent', '缺少', '没有'],
    },
    {
        "name": "评测题目歧义·冲突",
        "why": "同一份输入里两处评测题目歧义描述互相矛盾",
        "severity": "high",
        "keywords": ['冲突', 'conflict', 'contradict', '矛盾', '不一致', '相反'],
    },
    {
        "name": "评测题目歧义·越界",
        "why": "评测题目歧义的取值超出常规范围",
        "severity": "medium",
        "keywords": ['越界', 'out of range', 'outlier', '越界', '超限', '超过'],
    },
    {
        "name": "评测题目歧义·退化",
        "why": "评测题目歧义的信息量不足以支撑结论",
        "severity": "medium",
        "keywords": ['退化', 'degrade', 'insufficient', '不足', '太少', '无法'],
    },
    {
        "name": "评测题目歧义·泄漏",
        "why": "评测题目歧义相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['泄漏', 'leak', 'expose', '泄漏', '暴露', '明文'],
    },
    {
        "name": "评测题目歧义·重复",
        "why": "同一处评测题目歧义信息被反复传递",
        "severity": "low",
        "keywords": ['重复', 'duplicate', 'repeat', '重复', 'again'],
    },
    {
        "name": "评测题目歧义·陈旧",
        "why": "评测题目歧义的时效性已经过期",
        "severity": "medium",
        "keywords": ['陈旧', 'stale', 'expired', '过期', '陈旧', '旧版'],
    },
    {
        "name": "评测题目歧义·不可核",
        "why": "评测题目歧义的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['不可核', 'unverifiable', 'no evidence', '无法追溯', '没有来源'],
    },
]

# 特征规则：(名称, 正则, 说明)
SIGNATURE_RULES: list[tuple[str, str, str]] = [('invisible', '[\\u200b-\\u200f\\u202a-\\u202e\\u2060-\\u2064\\ufeff]', '不可见控制字符'), ('fullwidth', '[\\uff01-\\uff5e]', '全角字符'), ('homoglyph', '[\\u0430-\\u044f\\u0450-\\u045f]', '西里尔同形字'), ('override', '(ignore (all )?previous|ignore above|disregard)', '覆盖指令'), ('role_switch', '(you are now|act as|pretend to be)', '角色切换'), ('exfil', '(send|post|upload).{0,30}(http|www\\\\.)', '外传意图'), ('评测题目歧义', '评测题目歧义', '领域关键词「评测题目歧义」')]



PATTERNS: list[tuple[str, re.Pattern]] = [
    (name, re.compile(pat, re.I)) for name, pat, _ in SIGNATURE_RULES
]


def ambiguity_locate(text: str) -> list[dict]:
    """定位所有命中的特征片段。"""
    out: list[dict] = []
    for name, rx in PATTERNS:
        for m in rx.finditer(text):
            out.append({
                "feature": name,
                "start": m.start(),
                "end": m.end(),
                "snippet": m.group(0)[:80],
            })
    out.sort(key=lambda d: (d["start"], d["feature"]))
    return out


def ambiguity_density(text: str) -> float:
    """可疑字符密度。"""
    if not text:
        return 0.0
    hits = ambiguity_locate(text)
    covered = sum(d["end"] - d["start"] for d in hits)
    return covered / len(text)


def ambiguity_analyze(text: str) -> dict:
    """主分析：返回命中位置与密度。"""
    hits = ambiguity_locate(text)
    by_feature: dict[str, int] = {}
    for h in hits:
        by_feature[h["feature"]] = by_feature.get(h["feature"], 0) + 1
    return {
        "length": len(text),
        "hits": hits,
        "hit_count": len(hits),
        "by_feature": by_feature,
        "density": round(ambiguity_density(text), 4),
        "clean": not hits,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"长度：{result['length']}  命中：{result['hit_count']}  密度：{result['density']}")
    out.append("")
    for h in result["hits"]:
        out.append(f"  {h['feature']:<14} @{h['start']:>5}  {h['snippet']!r}")
    if result["clean"]:
        out.append("没有命中任何特征规则。")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="ambiguity",
        description="找出题干中缺少限定、允许多种答案的表述，标出歧义位置（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python ambiguity.py --file input.txt\n"
            "  python ambiguity.py --text '示例内容'\n"
            "  python ambiguity.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = ambiguity_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
