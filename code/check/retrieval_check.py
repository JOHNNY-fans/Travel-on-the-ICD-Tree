import json
import os
from collections import defaultdict

# ==========================================
# 0. 配置与全局常量
# ==========================================
# 请确保此路径正确，指向你的全量码表文件
ALL_PATH_FILE = "./merge_path.jsonl"  # 示例路径，请修改为实际路径

# 中文数字映射（用于排序）
CHINESE_NUM_TO_INT = {
    "第一章": 1, "第二章": 2, "第三章": 3, "第四章": 4, "第五章": 5,
    "第六章": 6, "第七章": 7, "第八章": 8, "第九章": 9, "第十章": 10,
    "第十一章": 11, "第十二章": 12, "第十三章": 13, "第十四章": 14, "第十五章": 15,
    "第十六章": 16, "第十七章": 17, "第十八章": 18, "第十九章": 19, "第二十章": 20,
    "第二十一章": 21, "第二十二章": 22,
}

# ==========================================
# 1. 码表索引构建工具
# ==========================================

def split_code_name(s):
    """
    辅助工具：将 "B26.2+ 流行性腮腺炎性脑炎" 切割为 "B26.2+" 和 "流行性腮腺炎性脑炎"
    """
    if not s or not isinstance(s, str):
        return None, None
    parts = s.split(' ', 1)
    if len(parts) < 2:
        return s.strip(), ""
    return parts[0].strip(), parts[1].strip()

def build_full_hierarchy_index(jsonl_path):
    index_map = {}
    
    # === 定义固定的根节点 ===
    root_node = {
        "level": 0,
        "node_id": "root",
        "name": "根节点"
    }

    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(f"码表文件不存在: {jsonl_path}")

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            entry = json.loads(line)
            
            # --- Level 1 (First Chapter) ---
            # 注意：此处使用 strict key access，如果码表格式不统一会报错
            l1_raw = entry["first_chapter"]
            l1_code, l1_name = split_code_name(l1_raw)
            if not l1_code: continue 
            
            node_l1 = {"node_id": l1_code, "name": l1_name, "level": 1}
            path_l1 = [root_node, node_l1]
            index_map[l1_code] = path_l1
            
            # --- Level 2 (Second Chapter) ---
            l2_raw = entry["second_chapter"]
            l2_code, l2_name = split_code_name(l2_raw)
            
            path_l2 = path_l1 
            if l2_code:
                node_l2 = {"node_id": l2_code, "name": l2_name, "level": 2}
                path_l2 = path_l1 + [node_l2]
                index_map[l2_code] = path_l2
            
            # --- Level 3 (Third Chapter) ---
            l3_raw = entry["third_chapter"]
            l3_code, l3_name = split_code_name(l3_raw)
            
            current_parent_path = path_l2
            
            if l3_code:
                node_l3 = {"node_id": l3_code, "name": l3_name, "level": 3}
                path_l3 = path_l2 + [node_l3]
                index_map[l3_code] = path_l3
                current_parent_path = path_l3
            
            # --- Level 4 (Code) ---
            l4_code = entry["code"]
            l4_name = entry["name"]
            
            if l4_code:
                node_l4 = {"node_id": l4_code, "name": l4_name, "level": 4}
                path_l4 = current_parent_path + [node_l4]
                index_map[l4_code] = path_l4

    return index_map

# ==========================================
# 2. 全局索引初始化
# ==========================================
print(f"🔄 正在加载码表文件: {ALL_PATH_FILE} ...")
try:
    CODE_TO_ENTRY = build_full_hierarchy_index(ALL_PATH_FILE)
    print(f"✅ 索引构建完成，包含 {len(CODE_TO_ENTRY)} 个节点。")
except Exception as e:
    print(f"❌ 码表加载失败: {e}")
    print("⚠️ 请修正 ALL_PATH_FILE 路径后重试。后续计算将因为找不到路径而全部判错。")
    CODE_TO_ENTRY = {}

def coda2path(code):
    """根据 code 获取完整路径 (Root -> L1 -> L2 -> L3 -> L4)"""
    if code not in CODE_TO_ENTRY:
        return None
    return CODE_TO_ENTRY[code]

# ==========================================
# 3. 统计核心逻辑
# ==========================================

def calculate_chapter_accuracy(data_file_path):
    """计算全量数据的章节准确率及各层级准确率"""
    
    if not os.path.exists(data_file_path):
        print(f"⚠️ 文件不存在: {data_file_path}")
        return

    print(f"\n{'='*90}")
    print(f"📊 分析文件: {data_file_path}")
    print(f"🎯 模式: Call_ICD_List Top1 准确率 + 多层级(L1-L4)验证")
    print(f"{'='*90}")

    # 章节统计容器
    chapter_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    
    # 全局层级统计容器
    global_stats = {
        "total": 0,
        "l1_correct": 0,
        "l2_correct": 0,
        "l3_correct": 0,
        "l4_correct": 0
    }

    with open(data_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 不使用 try-except，让 JSON 错误直接抛出（严格模式）
            data = json.loads(line)

            # === 1. 提取基础信息 ===
            # 使用 data['key'] 而不是 .get()
            answer_code = str(data['answer_code']).strip()
            
            # 提取 Top1 预测代码
            call_icd_list = data['all_results']['Call_ICD_List']
            if call_icd_list:
                predict_code = str(call_icd_list[0]['code']).strip()
            else:
                predict_code = ""

            # === 2. 提取 answer_path 用于章节归类和路径对比 ===
            answer_path = data['answer_path']
            
            # 校验数据有效性：至少需要有 Level 1 (Chapter) 节点
            if not answer_path or len(answer_path) < 1:
                continue
            
            # 获取章节名称 (例如 "第一章") 用于分组统计
            # 假设 answer_path[0] 是 Level 1
            chapter = answer_path[0]['node_id'].strip()
            if not chapter or chapter not in CHINESE_NUM_TO_INT:
                continue

            # === 3. 获取预测路径 ===
            # predict_path 结构: [Root, L1, L2, L3, L4] (由 build_full_hierarchy_index 生成)
            predict_path = coda2path(predict_code)

            # === 4. 层级比对逻辑 ===
            global_stats["total"] += 1
            chapter_stats[chapter]["total"] += 1

            # 标记当前样本各层级是否正确
            is_l1_ok = False
            is_l2_ok = False
            is_l3_ok = False
            is_l4_ok = False

            # 如果 predict_path 为 None，所有层级均为 False，不需要处理
            if predict_path:
                # --- Level 1 Check ---
                # answer_path[0] 对应 predict_path[1] (因为 predict_path 有 Root)
                if len(answer_path) >= 1 and len(predict_path) > 1:
                    if answer_path[0]['node_id'] == predict_path[1]['node_id']:
                        is_l1_ok = True

                # --- Level 2 Check ---
                # answer_path[1] 对应 predict_path[2]
                if is_l1_ok and len(answer_path) >= 2 and len(predict_path) > 2:
                    if answer_path[1]['node_id'] == predict_path[2]['node_id']:
                        is_l2_ok = True

                # --- Level 3 Check ---
                # 规则：若 answer 无 L3 但 L2 正确，认为 L3 正确。
                if is_l2_ok:
                    if len(answer_path) >= 3:
                        # 答案有 L3，必须比对
                        if len(predict_path) > 3:
                            if answer_path[2]['node_id'] == predict_path[3]['node_id']:
                                is_l3_ok = True
                        else:
                            # 答案有 L3，但预测路径没有 L3，判错
                            is_l3_ok = False
                    else:
                        # 答案没有 L3 (例如 I10)，但 L2 已正确，判对
                        is_l3_ok = True
                
                # --- Level 4 Check (Code) ---
                if answer_code == predict_code and answer_code != "":
                    is_l4_ok = True

            # === 5. 更新统计计数 ===
            if is_l1_ok: global_stats["l1_correct"] += 1
            if is_l2_ok: global_stats["l2_correct"] += 1
            if is_l3_ok: global_stats["l3_correct"] += 1
            if is_l4_ok:
                global_stats["l4_correct"] += 1
                # 更新分章节的正确数 (章节统计仅看最终 Code 是否正确)
                chapter_stats[chapter]["correct"] += 1

    # === 输出结果 ===
    if not chapter_stats:
        print("❌ 未在文件中找到有效的匹配数据。")
        return

    # 按照章节顺序排序
    all_chapters = sorted(chapter_stats.keys(), key=lambda x: CHINESE_NUM_TO_INT.get(x, 999))

    print(f"{'章节':<25} {'样本数':<10} {'Top1正确':<10} {'准确率(Acc)':<12}")
    print("-" * 75)
    
    for chap in all_chapters:
        stat = chapter_stats[chap]
        total = stat["total"]
        correct = stat["correct"]
        acc = (correct / total * 100) if total > 0 else 0.0
        print(f"{chap:<25} {total:<10} {correct:<10} {acc:.2f}%")

    # 汇总统计
    total_all = sum(s["total"] for s in chapter_stats.values())
    correct_all = sum(s["correct"] for s in chapter_stats.values())
    
    if total_all > 0:
        overall_acc = correct_all / total_all * 100
        print("-" * 75)
        print(f"{'总计 (Level 4)':<25} {total_all:<10} {correct_all:<10} {overall_acc:.2f}%")

        # === 新增：各层级详细准确率 ===
        print("\n📊 各层级准确率详情 (Hierarchy Analysis):")
        print("-" * 75)
        print(f"{'层级':<20} {'描述':<20} {'正确数':<10} {'准确率':<10}")
        print("-" * 75)
        
        # Level 1
        l1_acc = global_stats["l1_correct"] / total_all * 100
        print(f"{'Level 1':<20} {'章节 (Chapter)':<20} {global_stats['l1_correct']:<10} {l1_acc:.2f}%")
        
        # Level 2
        l2_acc = global_stats["l2_correct"] / total_all * 100
        print(f"{'Level 2':<20} {'类目 (Category)':<20} {global_stats['l2_correct']:<10} {l2_acc:.2f}%")
        
        # Level 3
        l3_acc = global_stats["l3_correct"] / total_all * 100
        print(f"{'Level 3':<20} {'亚目 (Subcat)':<20} {global_stats['l3_correct']:<10} {l3_acc:.2f}%")
        
        # Level 4
        l4_acc = global_stats["l4_correct"] / total_all * 100
        print(f"{'Level 4':<20} {'编码 (Code)':<20} {global_stats['l4_correct']:<10} {l4_acc:.2f}%")
        print("-" * 75)

# ================= 执行 =================
if __name__ == "__main__":
    # 设置需要计算 Accuracy 的数据文件列表
    data_files = [
        './1229_test/deepseek/deepseek_recall.jsonl',
        './1229_test/qwen3-plus/qwen3-plus.jsonl',
        './1229_test/gemini/gemini_recall.jsonl',
        './1229_test/qwen3-30b/qwen3-30b_recall.jsonl'
    ]

    # 只有当码表加载成功时才执行
    if CODE_TO_ENTRY:
        for df in data_files:
            calculate_chapter_accuracy(df)