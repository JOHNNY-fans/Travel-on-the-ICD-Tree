import json
import os
from collections import defaultdict

# ==========================================
# 0. 配置与全局常量
# ==========================================
# ⚠️ 请确保此路径正确
ALL_PATH_FILE = "./merge_path.jsonl" 

CHINESE_NUM_TO_INT = {
    "第一章": 1, "第二章": 2, "第三章": 3, "第四章": 4, "第五章": 5,
    "第六章": 6, "第七章": 7, "第八章": 8, "第九章": 9, "第十章": 10,
    "第十一章": 11, "第十二章": 12, "第十三章": 13, "第十四章": 14, "第十五章": 15,
    "第十六章": 16, "第十七章": 17, "第十八章": 18, "第十九章": 19, "第二十章": 20,
    "第二十一章": 21, "第二十二章": 22,
}

# ==========================================
# 1. 码表索引构建工具 (复用之前逻辑)
# ==========================================
def split_code_name(s):
    if not s or not isinstance(s, str):
        return None, None
    parts = s.split(' ', 1)
    if len(parts) < 2:
        return s.strip(), ""
    return parts[0].strip(), parts[1].strip()

def build_full_hierarchy_index(jsonl_path):
    index_map = {}
    root_node = {"level": 0, "node_id": "root", "name": "根节点"}

    if not os.path.exists(jsonl_path):
        return {}

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                entry = json.loads(line)
                # L1
                l1_raw = entry.get("first_chapter", "")
                l1_code, l1_name = split_code_name(l1_raw)
                if not l1_code: continue
                node_l1 = {"node_id": l1_code, "name": l1_name, "level": 1}
                path_l1 = [root_node, node_l1]
                index_map[l1_code] = path_l1
                
                # L2
                l2_raw = entry.get("second_chapter", "")
                l2_code, l2_name = split_code_name(l2_raw)
                path_l2 = path_l1
                if l2_code:
                    node_l2 = {"node_id": l2_code, "name": l2_name, "level": 2}
                    path_l2 = path_l1 + [node_l2]
                    index_map[l2_code] = path_l2
                
                # L3
                l3_raw = entry.get("third_chapter", "")
                l3_code, l3_name = split_code_name(l3_raw)
                current_parent_path = path_l2
                if l3_code:
                    node_l3 = {"node_id": l3_code, "name": l3_name, "level": 3}
                    path_l3 = path_l2 + [node_l3]
                    index_map[l3_code] = path_l3
                    current_parent_path = path_l3
                
                # L4
                l4_code = entry.get("code")
                l4_name = entry.get("name")
                if l4_code:
                    node_l4 = {"node_id": l4_code, "name": l4_name, "level": 4}
                    path_l4 = current_parent_path + [node_l4]
                    index_map[l4_code] = path_l4
            except:
                continue
    return index_map

# 初始化码表
print(f"🔄 正在加载码表文件: {ALL_PATH_FILE} ...")
CODE_TO_ENTRY = build_full_hierarchy_index(ALL_PATH_FILE)
print(f"✅ 索引构建完成，包含 {len(CODE_TO_ENTRY)} 个节点。")

def coda2path(code):
    """根据 code 获取完整路径"""
    return CODE_TO_ENTRY.get(code, None)


# ==========================================
# 2. 核心统计逻辑
# ==========================================
def calculate_chapter_accuracy(file_path):
    print(f"\n{'='*90}")
    print(f"📊 分析文件: {file_path}")
    print(f"{'='*90}")

    # 章节统计
    chapter_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    
    # 全局层级统计
    global_stats = {
        "total": 0,
        "l1_correct": 0,
        "l2_correct": 0,
        "l3_correct": 0,
        "l4_correct": 0
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # === 1. 提取基础信息 ===
                answer_path = data.get("answer_path", [])
                suggest_icd = str(data.get("suggest_icd", "")).strip()
                answer_code = str(data.get("answer_code", "")).strip()

                # 基础校验
                if not answer_code: 
                    continue
                if not answer_path or len(answer_path) < 1:
                    continue

                # 获取章节归属
                chapter = answer_path[0].get("node_id", "").strip()
                if not chapter or chapter not in CHINESE_NUM_TO_INT:
                    continue

                # === 2. 获取预测路径 ===
                # 注意：如果 suggest_icd 为空或不在码表中，predict_path 为 None
                predict_path = coda2path(suggest_icd)

                # === 3. 层级比对逻辑 ===
                chapter_stats[chapter]["total"] += 1
                global_stats["total"] += 1

                is_l1_ok = False
                is_l2_ok = False
                is_l3_ok = False
                is_l4_ok = False

                if predict_path:
                    # --- Level 1 Check ---
                    # answer_path[0] (Level 1) vs predict_path[1] (Level 1, index 0 is root)
                    if len(answer_path) >= 1 and len(predict_path) > 1:
                        if answer_path[0].get("node_id") == predict_path[1]["node_id"]:
                            is_l1_ok = True

                    # --- Level 2 Check ---
                    if is_l1_ok and len(answer_path) >= 2 and len(predict_path) > 2:
                        if answer_path[1].get("node_id") == predict_path[2]["node_id"]:
                            is_l2_ok = True

                    # --- Level 3 Check ---
                    # 规则：若 answer 无 L3 (长度<3) 但 L2 正确，认为 L3 正确。
                    if is_l2_ok:
                        if len(answer_path) >= 3:
                            # 答案有 L3，必须比对
                            if len(predict_path) > 3:
                                if answer_path[2].get("node_id") == predict_path[3]["node_id"]:
                                    is_l3_ok = True
                            else:
                                # 答案有 L3，但预测路径没有 L3
                                is_l3_ok = False
                        else:
                            # 答案没有 L3 (例如 I10)，但 L2 已正确，视为 L3 正确
                            is_l3_ok = True
                    
                    # --- Level 4 Check (Code) ---
                    if suggest_icd == answer_code:
                        is_l4_ok = True

                # === 4. 更新统计 ===
                if is_l1_ok: global_stats["l1_correct"] += 1
                if is_l2_ok: global_stats["l2_correct"] += 1
                if is_l3_ok: global_stats["l3_correct"] += 1
                if is_l4_ok: 
                    global_stats["l4_correct"] += 1
                    chapter_stats[chapter]["correct"] += 1

        # === 输出各章 Acc 表 ===
        if not chapter_stats:
            print("❌ 未找到有效的章节数据。")
            return

        all_chapters = sorted(chapter_stats.keys(), key=lambda x: CHINESE_NUM_TO_INT.get(x, 999))

        print(f"{'章节':<25} {'样本数':<10} {'正确数':<10} {'准确率(Acc)':<12}")
        print("-" * 75)
        for chap in all_chapters:
            stat = chapter_stats[chap]
            total = stat["total"]
            correct = stat["correct"]
            acc = (correct / total * 100) if total > 0 else 0.0
            print(f"{chap:<25} {total:<10} {correct:<10} {acc:.2f}%")

        # === 输出汇总与层级分析 ===
        total_all = global_stats["total"]
        if total_all > 0:
            overall_acc = global_stats["l4_correct"] / total_all * 100
            print("-" * 75)
            print(f"{'总计 (Code)':<25} {total_all:<10} {global_stats['l4_correct']:<10} {overall_acc:.2f}%")

            # 新增：各层级详细准确率
            print("\n📊 各层级准确率详情 (Hierarchy Analysis):")
            print("-" * 75)
            print(f"{'层级':<20} {'描述':<20} {'正确数':<10} {'准确率':<10}")
            print("-" * 75)
            
            l1_acc = global_stats["l1_correct"] / total_all * 100
            print(f"{'Level 1':<20} {'章节 (Chapter)':<20} {global_stats['l1_correct']:<10} {l1_acc:.2f}%")
            
            l2_acc = global_stats["l2_correct"] / total_all * 100
            print(f"{'Level 2':<20} {'类目 (Category)':<20} {global_stats['l2_correct']:<10} {l2_acc:.2f}%")
            
            l3_acc = global_stats["l3_correct"] / total_all * 100
            print(f"{'Level 3':<20} {'亚目 (Subcat)':<20} {global_stats['l3_correct']:<10} {l3_acc:.2f}%")
            
            l4_acc = global_stats["l4_correct"] / total_all * 100
            print(f"{'Level 4':<20} {'编码 (Code)':<20} {global_stats['l4_correct']:<10} {l4_acc:.2f}%")
            print("-" * 75)

    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")

# ================= 执行 =================
if __name__ == "__main__":
    file_paths = [
        './1229_test/deepseek/deepseek_recall.jsonl',
        './1229_test/qwen3-plus/qwen3-plus.jsonl',
        './1229_test/gemini/gemini_recall.jsonl',
        './1229_test/qwen3-30b/qwen3-30b_recall.jsonl'
    ]

    # 仅当码表构建成功时执行
    if CODE_TO_ENTRY:
        for fp in file_paths:
            calculate_chapter_accuracy(fp)
    else:
        print("❌ 码表加载失败，无法进行层级分析，请检查路径。")