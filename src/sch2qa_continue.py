"""
sch2qa_continue.py — Continue processing remaining entries for QA generation.

Usage:
    python src/sch2qa_continue.py
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

RAW_DATA = Path("/mnt/yjsj/data/open_schematics/kicad_sch_data/subgraph_export_0506")
OUTPUT_DIR = Path("/mnt/yjsj/zixigu/model_train/Qwen3.5-9B-SFT/data")
JSONL_PATH = OUTPUT_DIR / "QAs" / "train.jsonl"

COMP_CAT_CN = {
    "resistor": "电阻", "capacitor": "电容", "connector": "连接器",
    "light_diode": "LED", "ic": "集成电路", "diode": "二极管",
    "switch": "开关", "inductor": "电感", "test_point": "测试点",
    "protection": "保护器件", "polarized_capacitor": "极性电容",
    "mechanical": "机械元件", "transistor_fet": "MOSFET",
    "transistor_bjt": "三极管", "logic_gate": "逻辑门",
    "crystal_oscillator": "晶振", "actuator": "执行器",
    "sensor": "传感器", "relay": "继电器",
}

def cat_cn(cat):
    return COMP_CAT_CN.get(cat, cat)

def copy_image(entry_id, sg_id, sg_path):
    pngs = sorted([f for f in os.listdir(sg_path) if f.endswith(".png")])
    if not pngs:
        return None
    src = sg_path / pngs[0]
    dst_dir = OUTPUT_DIR / "images" / entry_id
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / pngs[0]
    if not dst.exists():
        shutil.copy2(src, dst)
    return f"data/images/{entry_id}/{pngs[0]}"

def build_qa_pairs(title, comps, nets, image_rel):
    pairs = []
    # Type 1: function description
    if comps:
        by_cat = {}
        for c in comps:
            by_cat.setdefault(c["category"], []).append(f"{c['ref']}({c['value']})")
        cat_lines = ["{}：{}".format(cat_cn(cat), "、".join(items)) for cat, items in by_cat.items()]
        comp_summary = "；".join(cat_lines)
        net_names = [n[0] for n in nets if not n[0].startswith("Net-")]
        net_part = "主要网络有{}。".format("、".join(net_names)) if net_names else ""
        desc = "这是一个{}电路子图。包含{}个元器件：{}。{}".format(title, len(comps), comp_summary, net_part)
    else:
        desc = "这是一个{}电路子图，未检测到独立元器件。".format(title)
    pairs.append({
        "messages": [
            {"role": "user", "content": [
                {"type": "image", "image": image_rel},
                {"type": "text", "text": "描述这个电路子图的功能和主要元器件组成"}
            ]},
            {"role": "assistant", "content": [{"type": "text", "text": desc}]}
        ]
    })
    # Type 2: component inventory
    if comps:
        inv = "共{}个元器件：\n".format(len(comps)) + "\n".join("- {}: {} ({})".format(c["ref"], c["value"], cat_cn(c["category"])) for c in comps)
    else:
        inv = "该子图未检测到独立元器件。"
    pairs.append({
        "messages": [
            {"role": "user", "content": [
                {"type": "image", "image": image_rel},
                {"type": "text", "text": "列出该电路中的所有元器件及其参数"}
            ]},
            {"role": "assistant", "content": [{"type": "text", "text": inv}]}
        ]
    })
    # Type 3: connectivity
    if nets:
        comp_map = {c["ref"]: "{}".format(c["ref"]) for c in comps}
        conn_lines = ["共{}个网络：".format(len(nets))]
        for net in nets:
            name = net[0]
            conns = net[2] if len(net) > 2 else []
            parts = ["{} 引脚 {}".format(comp_map.get(c.split(".")[0], c.split(".")[0]), c.split(".")[1]) if "." in c else c for c in conns]
            conn_lines.append("- {}: 连接 {}".format(name, "、".join(parts)))
        pairs.append({
            "messages": [
                {"role": "user", "content": [
                    {"type": "image", "image": image_rel},
                    {"type": "text", "text": "分析该电路的网络连接关系"}
                ]},
                {"role": "assistant", "content": [{"type": "text", "text": "\n".join(conn_lines)}]}
            ]
        })
    return pairs

def main():
    all_entries = sorted([d for d in os.listdir(RAW_DATA) if d.isdigit()], key=int)
    # Determine which entries already have images processed
    img_dir = OUTPUT_DIR / "images"
    done = set(d for d in os.listdir(img_dir) if d.isdigit()) if img_dir.exists() else set()
    remaining = [e for e in all_entries if e not in done]
    print(f"Total entries: {len(all_entries)}")
    print(f"Already done: {len(done)}")
    print(f"Remaining: {len(remaining)}")

    if not remaining:
        print("All done!")
        return

    total_qas = 0
    processed = 0
    errors = []
    start = time.time()

    for eid in remaining:
        epath = RAW_DATA / eid
        try:
            subdirs = sorted([d for d in os.listdir(epath) if d.isdigit()], key=int)
            entry_qas = 0
            for sg_id in subdirs:
                sg_path = epath / sg_id
                meta_path = sg_path / "meta.json"
                if not meta_path.exists():
                    continue
                with open(meta_path) as f:
                    meta = json.load(f)
                ie = meta.get("annotated_index_entry", {})
                title = ie.get("title", "子图{}".format(sg_id))
                # Read compact json
                compact_path = sg_path / "compact" / "s{}_compact.json".format(sg_id)
                comps = []
                nets = []
                if compact_path.exists():
                    with open(compact_path) as f:
                        cd = json.load(f)
                    for c in cd.get("component", []):
                        comps.append({"ref": c[0][0], "value": c[1][0], "category": c[2]})
                    nets = cd.get("net", [])
                # Copy image
                image_rel = copy_image(eid, sg_id, sg_path)
                if image_rel is None:
                    continue
                # Generate QA pairs
                pairs = build_qa_pairs(title, comps, nets, image_rel)
                entry_qas += len(pairs)
                with open(JSONL_PATH, "a") as f:
                    for pair in pairs:
                        f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            total_qas += entry_qas
            processed += 1
            if processed % 100 == 0:
                elapsed = time.time() - start
                print(f"  [{processed}/{len(remaining)}] e{eid}: {entry_qas} QAs (total: {total_qas}, {elapsed:.0f}s)")
        except Exception as exc:
            errors.append((eid, str(exc)))
            print(f"  ❌ Entry {eid} failed: {exc}", file=sys.stderr)

    elapsed = time.time() - start
    print(f"\n✅ Done in {elapsed:.0f}s")
    print(f"   Entries processed: {processed}")
    print(f"   QA pairs added: {total_qas}")
    print(f"   Errors: {len(errors)}")
    if errors:
        print(f"   First 5 errors: {errors[:5]}")

    # Summary
    with open(JSONL_PATH) as f:
        total = sum(1 for _ in f)
    img_count = sum(1 for _, _, files in os.walk(OUTPUT_DIR / "images") for f in files if f.endswith(".png"))
    print(f"\n=== Final Summary ===")
    print(f"Total QA pairs: {total}")
    print(f"Total images:   {img_count}")
    print(f"JSONL file:     {JSONL_PATH}")
    print(f"Images dir:     {OUTPUT_DIR / 'images'}")

if __name__ == "__main__":
    main()
