"""
sch2qa.py — Convert KiCad schematic subgraph data into VLM-format QA pairs.

Usage:
    python src/sch2qa.py                      # process all entries
    python src/sch2qa.py --max-entries 50     # process first N entries
    python src/sch2qa.py --sample             # only 10 entries for testing

Output:
    <output_dir>/QAs/train.jsonl         — QA pairs in VLM format
    <output_dir>/images/<eid>/<png>      — subgraph PNGs (copied)
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
import argparse
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────
RAW_DATA   = Path("/mnt/yjsj/data/open_schematics/kicad_sch_data/subgraph_export_0506")
OUTPUT_DIR = Path("/mnt/yjsj/zixigu/model_train/Qwen3.5-9B-SFT/data")

# ── QA templates ────────────────────────────────────────────────────────

COMP_CAT_CN = {
    "resistor": "电阻",
    "capacitor": "电容",
    "connector": "连接器",
    "light_diode": "LED",
    "ic": "集成电路",
    "diode": "二极管",
    "switch": "开关",
    "inductor": "电感",
    "test_point": "测试点",
    "protection": "保护器件",
    "polarized_capacitor": "极性电容",
    "mechanical": "机械元件",
    "transistor_fet": "MOSFET",
    "transistor_bjt": "三极管",
    "logic_gate": "逻辑门",
    "crystal_oscillator": "晶振",
    "actuator": "执行器",
    "sensor": "传感器",
    "relay": "继电器",
    "connector/female": "连接器(母)",
    "connector/male": "连接器(公)",
}

def cat_cn(cat: str) -> str:
    return COMP_CAT_CN.get(cat, cat)


def format_components(comp_list: list) -> list[dict]:
    """Return sorted component dicts from compact component entries."""
    result = []
    for c in comp_list:
        ref, _ = c[0]
        value, _ = c[1]
        category = c[2]
        result.append({"ref": ref, "value": value, "category": category})
    result.sort(key=lambda x: x["ref"])
    return result


def build_function_description(
    title: str, comps: list[dict], nets: list[list],
) -> str:
    """Template 1: circuit function and main components description."""
    if not comps:
        return f"这是一个{title}电路子图，未检测到独立元器件。"

    # Group by category
    by_cat: dict[str, list[str]] = {}
    for c in comps:
        by_cat.setdefault(c["category"], []).append(f"{c['ref']}({c['value']})")

    cat_lines = []
    for cat, items in by_cat.items():
        label = cat_cn(cat)
        cat_lines.append(f"{label}：{'、'.join(items)}")

    comp_summary = "；".join(cat_lines)

    # Net summary
    net_names = [n[0] for n in nets if not n[0].startswith("Net-")]
    net_part = f"主要网络有{'、'.join(net_names)}。" if net_names else ""

    return (
        f"这是一个{title}电路子图。"
        f"包含{len(comps)}个元器件：{comp_summary}。"
        f"{net_part}"
    )


def build_component_inventory(comps: list[dict]) -> str:
    """Template 2: detailed component inventory."""
    if not comps:
        return "该子图未检测到独立元器件。"

    lines = [f"共{len(comps)}个元器件："]
    for c in comps:
        lines.append(f"- {c['ref']}: {c['value']} ({cat_cn(c['category'])})")
    return "\n".join(lines)


def build_connectivity_description(comps: list[dict], nets: list[list]) -> str:
    """Template 3: net connectivity analysis."""
    if not nets:
        return "该子图未检测到网络连接。"

    # Build component lookup
    comp_map = {c["ref"]: f"{c['ref']}({c['value']})" for c in comps}

    lines = [f"共{len(nets)}个网络："]
    for net in nets:
        name = net[0]
        conns = net[2] if len(net) > 2 else []
        conn_strs = []
        for conn in conns:
            parts = conn.split(".")
            if len(parts) == 2:
                cref, pin = parts
                display = comp_map.get(cref, cref)
                conn_strs.append(f"{display} 的引脚 {pin}")
        lines.append(f"- {name}: 连接 {'、'.join(conn_strs)}")
    return "\n".join(lines)


# ── Main logic ──────────────────────────────────────────────────────────

def iter_entries(max_entries: int | None = None):
    """Yield (entry_id, entry_path) sorted numerically."""
    entries = sorted(
        [d for d in os.listdir(RAW_DATA) if d.isdigit()],
        key=int,
    )
    if max_entries is not None:
        entries = entries[:max_entries]
    for eid in entries:
        yield eid, RAW_DATA / eid


def iter_subgraphs(entry_path: Path):
    """Yield (subgraph_id, subgraph_path, meta, compact_data) for each valid subgraph."""
    subdirs = sorted(
        [d for d in os.listdir(entry_path) if d.isdigit()],
        key=int,
    )
    for sd in subdirs:
        sp = entry_path / sd
        # meta
        meta_path = sp / "meta.json"
        if not meta_path.exists():
            continue
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # compact json
        compact_path = sp / "compact" / f"s{sd}_compact.json"
        compact = None
        if compact_path.exists():
            try:
                with open(compact_path) as f:
                    compact = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        yield sd, sp, meta, compact


def copy_image(entry_id: str, subgraph_id: str, subgraph_path: Path) -> str | None:
    """Copy subgraph PNG to output images dir. Returns relative path or None."""
    pngs = sorted(
        [f for f in os.listdir(subgraph_path) if f.endswith(".png")]
    )
    if not pngs:
        return None
    src = subgraph_path / pngs[0]

    dst_dir = OUTPUT_DIR / "images" / entry_id
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / pngs[0]
    if not dst.exists():
        shutil.copy2(src, dst)
    return f"data/images/{entry_id}/{pngs[0]}"


def build_qa_pairs(
    title: str,
    comps: list[dict],
    nets: list[list],
    image_rel: str,
) -> list[dict]:
    """Generate 2 QA pairs in VLM format."""
    pairs = []

    # Type 1: function description
    func_desc = build_function_description(title, comps, nets)
    pairs.append({
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_rel},
                    {"type": "text", "text": "描述这个电路子图的功能和主要元器件组成"},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": func_desc},
                ],
            },
        ]
    })

    # Type 2: component inventory
    inv_desc = build_component_inventory(comps)
    pairs.append({
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image_rel},
                    {"type": "text", "text": "列出该电路中的所有元器件及其参数"},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": inv_desc},
                ],
            },
        ]
    })

    # Type 3: connectivity (only if nets exist)
    if nets:
        conn_desc = build_connectivity_description(comps, nets)
        pairs.append({
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_rel},
                        {"type": "text", "text": "分析该电路的网络连接关系"},
                    ],
                },
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": conn_desc},
                    ],
                },
            ]
        })

    return pairs


def process_one_entry(entry_id: str, entry_path: Path) -> int:
    """Process a single entry, return number of QA pairs generated."""
    qa_count = 0
    for sg_id, sg_path, meta, compact in iter_subgraphs(entry_path):
        ie = meta.get("annotated_index_entry", {})
        title = ie.get("title", f"子图{sg_id}")
        counts = ie.get("counts", {})

        # Extract component / net data
        comps = []
        nets = []
        if compact is not None:
            comps = format_components(compact.get("component", []))
            nets = compact.get("net", [])

        # Skip if zero components (nothing meaningful to ask)
        comp_count = counts.get("components", len(comps))
        if comp_count == 0 and not title:
            continue

        # Copy image
        image_rel = copy_image(entry_id, sg_id, sg_path)
        if image_rel is None:
            continue

        # Generate QA pairs
        pairs = build_qa_pairs(title, comps, nets, image_rel)
        qa_count += len(pairs)

        # Append to jsonl file
        with open(jsonl_path, "a") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    return qa_count


def build_summary():
    """Build a summary of what was generated."""
    # Count QAs
    qa_total = 0
    if jsonl_path.exists():
        with open(jsonl_path) as f:
            qa_total = sum(1 for _ in f)

    # Count images
    img_dir = OUTPUT_DIR / "images"
    img_count = 0
    if img_dir.exists():
        for root, dirs, files in os.walk(img_dir):
            img_count += sum(1 for f in files if f.endswith(".png"))

    return {
        "qa_total": qa_total,
        "image_total": img_count,
        "jsonl_file": str(jsonl_path),
        "images_dir": str(img_dir),
    }


# ── CLI ────────────────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert KiCad subgraph data to VLM QA pairs",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Process only 10 entries for testing",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=None,
        help="Max entries to process",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output without asking",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    global OUTPUT_DIR, jsonl_path
    OUTPUT_DIR = args.output_dir
    jsonl_path = OUTPUT_DIR / "QAs" / "train.jsonl"

    max_entries = args.max_entries
    if args.sample:
        max_entries = 10

    # Ensure output dirs
    qa_dir = OUTPUT_DIR / "QAs"
    qa_dir.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "images").mkdir(parents=True, exist_ok=True)

    # Clear existing jsonl if starting fresh
    if jsonl_path.exists():
        if args.force:
            jsonl_path.write_text("")
            print("  → Overwritten (--force).")
        else:
            ans = input(f"  {jsonl_path} exists. Append (a) or overwrite (o)? [a/o] ")
            if ans.lower() == "o":
                jsonl_path.write_text("")
                print("  → Overwritten.")
            else:
                print("  → Appending.")

    # Process
    total_qas = 0
    processed_entries = 0
    start = time.time()

    for eid, epath in iter_entries(max_entries):
        try:
            n = process_one_entry(eid, epath)
            total_qas += n
            processed_entries += 1
            if processed_entries % 100 == 0:
                elapsed = time.time() - start
                print(
                    f"  [{processed_entries}] {eid}: {n} QAs "
                    f"(total: {total_qas}, {elapsed:.0f}s)"
                )
        except Exception as exc:
            print(f"  ❌ Entry {eid} failed: {exc}", file=sys.stderr)

    elapsed = time.time() - start
    summary = build_summary()
    print(f"\n✅ Done in {elapsed:.0f}s")
    print(f"   Entries processed: {processed_entries}")
    print(f"   QA pairs: {summary['qa_total']}")
    print(f"   Images:   {summary['image_total']}")
    print(f"   JSONL:    {summary['jsonl_file']}")


jsonl_path = OUTPUT_DIR / "QAs" / "train.jsonl"

if __name__ == "__main__":
    main()
