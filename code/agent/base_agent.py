import json
import re
import os
from typing import List, Dict, Optional, Tuple, Any
import ast

# ----------------------------
# 配置路径（请根据实际调整）
# ----------------------------


Node_DIR = "../node_index"
CHAPTER_FILE = os.path.join(Node_DIR, "level_1.jsonl")
CATEGORY_FILE = os.path.join(Node_DIR, "level_2.jsonl")
SUBCATEGORY_FILE = os.path.join(Node_DIR, "level_3.jsonl")

Rule_DIR = "../rule_index"
BASE_RULE_FILE0 = os.path.join(Rule_DIR, "chapter_index.jsonl")
BASE_RULE_FILE = os.path.join(Rule_DIR, "level_0.jsonl")
CHAPTER_RULE_FILE = os.path.join(Rule_DIR, "level_1.jsonl")
CATEGORY_RULE_FILE = os.path.join(Rule_DIR, "level_2.jsonl")
SUBCATEGORY_RULE_FILE = os.path.join(Rule_DIR, "level_3.jsonl")



def load_json(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        print(f"⚠️ 警告：{file_path} 不存在，返回空列表")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def load_jsonl(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        print(f"⚠️ 警告：{file_path} 不存在，返回空列表")
        return []
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

def extract_operations(text, required_fields=None):
    if not text or not required_fields:
        return []
    
    candidates = []
    start = text.find('{')
    while start != -1:
        brace_count = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    candidates.append(text[start:i+1])
                    start = i + 1
                    break
        else:
            break
        start = text.find('{', start)

    results = []
    for cand in candidates:
        try:
            # 优先尝试 json.loads（更适合 LLM 输出）
            d = json.loads(cand)
            if isinstance(d, dict):
                valid = True
                for field in required_fields:
                    val = d.get(field)
                    if val is None or (isinstance(val, str) and not val.strip()):
                        valid = False
                        break
                if valid:
                    results.append(d)
        except Exception:
            # 如果 json 失败，再尝试 ast.literal_eval（兼容旧格式）
            try:
                d = ast.literal_eval(cand)
                if isinstance(d, dict):
                    valid = True
                    for field in required_fields:
                        val = d.get(field)
                        if val is None or (isinstance(val, str) and not val.strip()):
                            valid = False
                            break
                    if valid:
                        results.append(d)
            except Exception:
                continue
    return results

icd_chapter_dict = {
    "第一章": "第1章",
    "第二章": "第2章",
    "第三章": "第3章",
    "第四章": "第4章",
    "第五章": "第5章",
    "第六章": "第6章",
    "第七章": "第7章",
    "第八章": "第8章",
    "第九章": "第9章",
    "第十章": "第10章",
    "第十一章": "第11章",
    "第十二章": "第12章",
    "第十三章": "第13章",
    "第十四章": "第14章",
    "第十五章": "第15章",
    "第十六章": "第16章",
    "第十七章": "第17章",
    "第十八章": "第18章",
    "第十九章": "第19章",
    "第二十章": "第20章",
    "第二十一章": "第21章",
    "第二十二章": "第22章"
}
chapter_dict_reversed = {
    "第1章": "第一章",
    "第2章": "第二章",
    "第3章": "第三章",
    "第4章": "第四章",
    "第5章": "第五章",
    "第6章": "第六章",
    "第7章": "第七章",
    "第8章": "第八章",
    "第9章": "第九章",
    "第10章": "第十章",
    "第11章": "第十一章",
    "第12章": "第十二章",
    "第13章": "第十三章",
    "第14章": "第十四章",
    "第15章": "第十五章",
    "第16章": "第十六章",
    "第17章": "第十七章",
    "第18章": "第十八章",
    "第19章": "第十九章",
    "第20章": "第二十章",
    "第21章": "第二十一章",
    "第22章": "第二十二章"
}
def extract_unique_values(node_list, field):
    """
    从节点列表中提取指定字段的所有唯一值。

    参数:
        node_list (list): 节点信息列表，每个元素为 dict，包含 '章节'、'亚目'、'细目' 等字段。
        field (str): 要提取的字段名，如 '章节', '亚目', '细目'

    返回:
        list: 该字段下所有不重复的值，按首次出现顺序排列（或可选排序）
    """
    seen = set()
    unique_values = []
    for node in node_list:
        value = node.get(field)
        if value is not None and value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values
def chat_method2(content, history):
    api_key=''
    model_url=''
    model_name='deepseek-chat'
 
    return generate_gpt4o_path(prompt=content,api_key=api_key,base_url=model_url,image_paths=None,history=history)

def chat_method3(content, history):
    api_key=''
    model_url=''
    model_name='deepseek-chat'
    return generate_gpt4o(prompt=content,api_key=api_key,base_url=model_url,image_paths=None,history=history)
from openai import OpenAI
import base64 
import mimetypes
def generate_gpt4o_path(prompt,api_key,base_url,image_paths=None,history=None):
    client = OpenAI(api_key=api_key, base_url=base_url)
    # 设置 API 密钥
    # 创建消息历史记录，包含之前的对话   
    # 在每一步操作中，您必须通过调用特定的函数来执行以下操作之一：
    messages = []
    system_prompt=f"""
作为专业的质控编码专家，您的任务是根据电子病历内容，以交互方式完成ICD编码的逐级选择。编码路径遵循标准的层级结构：从根节点（level=0）开始，依次经过章节（level=1）、类目（level=2）、亚目（level=3），最终到达编码（level=4）。

每一步操作中，您必须通过调用特定的函数来执行以下操作之一。

### 1. 工具调用规范与策略
您必须根据当前状态选择以下工具之一来执行操作：

1.  **get_child_node (查看路标)**
    *   **作用**：传入 `node_id` 获取子节点列表。
    *   **注意**：调用此函数**不会**改变当前所在的层级。这只是“看地图”，不是“走路”。
    *   **策略**：在 Level 2（类目）和 Level 3（亚目）层级，强烈建议先调用此函数预览子节点列表。
    理由：往往看似“通用”的父节点（如 A16.2 肺结核）下隐藏着极高特异性的“具体病变”编码（如 A16.203 结核性肺纤维变性）。
    警示：如果不先查看子节点就直接下钻其他路径，极易导致“因小失大”，错过最佳编码。只有先“看地图”，才能避免走入死胡同。

2.  **select_next_node (前进下钻)**
    *   **作用**：选定最精确编码进入下一层。
    *   **参数要求**：
        *   `select_node_id`：从当前编码的子节点中选定一个最精确编码。
        *   `evidence_quote`：必须**原文摘录**病历中支持该选择的关键证据。
            *   **【关键：分级/数值校验逻辑】**
            *   **Step 1 查阅标准**：首先检查工具返回的 `node_rules`（节点特殊规则）中是否存在该疾病的分级/分期定义（例如：高血压分级的血压阈值、肾病分期的肌酐标准）。
            *   **Step 2 优先匹配客观数据**：若 **存在** 规则定义，必须在病历（体格检查、化验单）中寻找对应的**客观数值**（如“BP 180/100mmHg”、“肌酐 200μmol/L”）作为证据，以此匹配规则。此时严禁仅摘录“高血压3级”这种结论性描述。
            *   **Step 3 兜底信任**：仅当 **找不到** 明确的节点规则定义，或病历确实缺失客观数据时，才允许直接摘录医生书写的文本诊断（如“出院诊断：高血压3级”）。
        *   `rule_quote`：
            *   **严格相关性检查**：必须引用与当前疾病**章节/系统一致**的规则。**严禁**在处理传染病（如结核、肝炎）时引用肿瘤章节（C/D/Z类）的化疗规则，反之亦然。引用无关规则将被视为严重错误。
            *   存在适用规则时：必须从本 Prompt 中的【主要诊断选择规则】或工具返回的 “当前节点的特殊规则” 中，摘录支持本次决策的具体规则内容。
            *   无适用规则时：若当前选择仅基于病历证据的直接事实匹配（如单纯的解剖部位对应），且未触发任何排他性或优先规则，此字段请记为空字符串 ("")。
    *   **策略**：
        *   **特异性检查**：当考虑选择 XX.8（其他）时，必须先查看 XX.9（未特指）及其子节点；考虑选择 XX.9时，先查看 XX.8及其子节点。
        *   **时效性检查（新增）**：选择编码时，必须确认该疾病或部位是**本次住院期间**存在并处理的。严禁将“既往史”与本次病变混合编码。（例如：本次治疗左侧，既往有右侧，不得选择双侧编码）。
        *   **终末节点名称熔断机制 **：
            触发条件：当您准备选择 Level 4（最终编码）节点时。
            校验逻辑：即将选择的 Level 4 节点名称必须包含病历诊断中的所有核心定语（特别是病原体、性质）。
            熔断案例 1（性质不符）：病历诊断为“晚期先天性梅毒”。您当前位于 A52（晚期梅毒），但发现 A52 下的所有 Level 4 节点（如 A52.100 有症状性神经梅毒）均不包含“先天性”字样。
            结论：当前 Level 4 节点不合适，说明 Level 2 父节点 A52 选择错误。
            操作：严禁选择 A52.xxx，必须调用 backtry_path 回溯，去 A50（先天性梅毒）下寻找包含“晚期”和“先天性”的正确编码。
            熔断案例 2（病原体缺失）：病历诊断为“克里米亚-刚果出血热”。您当前位于 A99（未特指的病毒性出血热），但发现 A99 下的 Level 4 节点（如 A99.x00 病毒性出血热）不包含“克里米亚-刚果”这一具体名称。
            结论：当前 Level 4 节点过于泛化，不合适，说明 Level 2 父节点 A99 选择错误。
            操作：严禁选择 A99.x00，必须调用 backtry_path 回溯，去 A98（其他病毒性出血热）下寻找隐藏的具体病原体编码。
            操作指令：只要当前父节点下的 Level 4 子节点列表中找不到完全匹配核心定语的选项，立刻停止选择，执行回溯寻找更合适的父节点。

3.  **validate_current_node (路况检查)**
    *   **作用**：基于病历自动评估当前路径合理性。建议在 Level 3 或 Level 4 调用。
    *   **策略**：若校验结果提示“不合理”，下一轮 **必须** 调用 `backtry_path` 进行修正。

4.  **backtry_path (掉头/纠错)**
    *   **作用**：回退至指定层级。
    *   **策略**：当出现以下情况时主动调用：
        (1) 校验不通过；
        (2) **死胡同**：当前分支下无匹配项（例如：在“其他器官结核”A18下找不到“多浆膜腔积液”的组合）；
        (3) **逻辑修正**：发现需要查找更上位概念

5.  **finish_selection (到达终点)**
    *   **作用**：当确认当前所在的 Level 4 节点为最终正确编码时，调用此工具提交该节点的 node_id 和 name 以结束流程。
    *   **限制**：仅当当前层级为最终编码（level=4）且通过路径校验时时才允许调用，每次使用backtry_path函数，需要重新进行校验。

---

### 2. 病历阅读与证据运用策略（核心工作流）

Step 1 - 资源锚定与诊疗逻辑校验 (Resource Anchoring & Treatment Logic)
    依据：诊疗经过（核心依据） > 出院诊断列表（参考依据）。
    目的：确定本次住院实际消耗医疗资源的疾病，而非仅仅是入院理由。
    关键操作（诊疗过程为王）：
    扫描诊疗经过：检查是否出现了**“因...未行手术”、“待明确...病因”、“转为保守治疗”或“重点评估...”**等描述。
    不确定信息处理：若患者入院拟行A疾病手术，但诊疗经过显示“因发现B疾病（或B病因不明）暂缓手术，重点完善检查以查明B”，则B为主要诊断，A退为次要诊断。
    资源服务判定：问自己：“医生开具的检查（如CT、造影）、护理及用药，主要是为了解决哪个问题？”以此锁定的疾病为基准候选。

Step 1.5 - 关联扫描与合并诊断 (Association & Combination Check) —— **解决多部位/全身性问题**
    依据：出院诊断列表的全貌。
    规则：检测“基准候选”是否需与其他诊断合并，或是否存在更上位的**全身性诊断**。
    操作：
    1.  **全身 vs 局部判读（重要）**：
        *   **多部位原则**：若病历显示**多部位同时受累**（如：结核性胸膜炎+腹膜炎+心包炎），这通常暗示**全身性/播散性**疾病。
        *   **路径纠错**：此时若你在 A18（单个器官结核）下找不到“多部位”选项，**严禁**强行选择某个单一器官（如只选心包）或拆分编码。**必须回退**，寻找 A19（粟粒性/播散性结核）这类上位编码。
    2.  **联合编码触发**：
        *   多瓣膜病：若同时出现二尖瓣、三尖瓣、主动脉瓣中任意两个及以上的病变，需合并编码至（I08），禁止拆分。
        *   梗阻/感染：若有“胆结石”和“胆囊炎”，必须合并为“胆结石伴胆囊炎”。

Step 2 - 细节细化 (Refinement)
    依据：病理报告 > 手术记录 > 专项检查报告。
    目的：填充ICD编码所需的特异性轴心信息（如具体部位、病理类型）。
    权重原则：病理报告是金标准。若出院诊断与病理不一致，以病理为准。
    **特别注意**：对于高血压、糖尿病等慢性病，若节点规则有明确的分级/分期数值定义，必须回到本步骤查找体格检查（血压）或化验（肌酐/血糖）中的具体数值。



Step 3 - 时效性界定 (Temporal Scope) —— 关键步骤
    规则：严格区分“本次住院情况”与“既往史/陈旧性病变”。
    操作：
    仅编码本次住院期间发现、治疗或护理的疾病/部位。
    既往史仅供参考，不做编码依据。
    案例：本次住院诊断“左侧输卵管积水”并手术，病历既往史提及“右侧输卵管积水”。操作：仅编码“左侧输卵管积水”，禁止编码“双侧输卵管积水”。
Step 4 - 缺项补全 (Information Completion)
    依据：入院记录 / 现病史。
    场景：仅当上述步骤均无法提供必要信息时，才查阅入院记录作为参考。
Step 5 - 证据时序校验 (Chronological Weight Check) —— 核心风控
    规则：越靠近出院时间的医疗记录，编码权重越高。
    逻辑自检：
    在提取 evidence_quote 时，必须优先引用出院诊断、出院诊疗信息，以及靠近出院时的检查或病理报告。
    若引用了“入院记录”，必须检查该信息是否在出院时被排除或修正。

---

### 3. 主要诊断选择规则（导航指南）
**您的所有路径选择必须严格基于以下规则确定主要诊断：**

**一、【核心原则（总则）】**
主要诊断是指本次住院期间：对患者健康危害最严重、消耗医疗资源最多、住院时间最长的疾病或健康问题。
*   **时效性原则**：主要诊断必须是**本次住院期间**发生或处理的疾病。既往已治愈或本次未处理的陈旧性疾病，不得作为主要诊断，且在涉及部位编码（如单侧/双侧）时，必须仅体现本次受累部位。

**二、【具体选择规则（补充规则）】**

*   **病因与临床表现**
    *   若病因诊断能充分涵盖临床表现，优先选择病因诊断。
    *   若临床表现代表疾病严重阶段（如心肌梗死、心力衰竭），且非终末状态，则选择该临床表现。
*   **未确诊情况**
    *   当诊断未明确时，以症状、体征或异常检查结果（R类）作为主要诊断。
    *   怀疑诊断在出院时未被排除：按肯定诊断处理。
    *   怀疑诊断在出院时已被排除：编码为 Z03.-。
*   **急慢性疾病**
    *   慢性病急性发作：优先选择急性编码；若存在对应的合并编码（如 J44.1），**必须使用合并编码**。
*   **后遗症**
    *   后遗症类编码（如 I69.-）仅作为附加编码。主要诊断应为当前正在治疗的具体功能障碍（如“偏瘫”）。
*   **损伤**
    *   选择最严重的损伤；若无法明确严重程度，使用综合编码（如 T07.-）。
    *   优先级：内部损伤 > 浅表伤；颅内损伤 > 颅骨骨折。
*   **产科**
    *   存在产科并发症时，选择最主要的并发症（如 O14.1）。
*   **恶性肿瘤（重中之重）**
    *   **手术/确诊**：本次住院进行了肿瘤切除、活检或首次确诊 -> 选择 **C00-D48 (肿瘤实体)**。
    *   **仅化疗/放疗**：本次住院**未实施手术**，仅接受放疗、化疗、靶向或免疫治疗 -> **必须选择 Z51.-**。
    *   **仅复查**：既往已手术，本次仅复查、随访 -> 选择 **Z08.-**。
    *   *注意：即使既往有肿瘤史，若本次仅处理并发症且未针对肿瘤治疗，选并发症为主诊。*

---

### 4. 节点分析与决策逻辑
在选择节点时，请遵循以下思维过程：
Step 1. 动态规则扫雷 (Global Rule Scanning & Radar)
    地位：工具返回的 当前节点的特殊规则 是当前层级的最高宪法。
    操作 A - 排除项检查 (Exclusions)：
        仔细检查病历是否落入规则提到的**“不包括...”或“排除...”**。
        例：若规则提示“产科破伤风归A34”，即使在产科章节看到破伤风字眼，也必须回退去找A34。
    操作 B - 隐藏菜单匹配 (Inclusion Matching)：
        情报源：特别关注规则中列出的 .8（其他） 或 .9（未特指） 的详细包含列表（例如：“亚目C34.9包含...细支气管...”）。
        触发条件：将病历中的核心诊断名词（包括部位、病因、形态、特定类型等修饰词）与规则文本进行比对。如果病历中的关键修饰词（如**“细支气管”**、“克雷伯菌”、“复发性”）明确出现在规则文本提到的某个“兜底节点”包含列表中。
        决策：必须优先遵循规则文本的指引，进入该节点查找，即使存在另一个看起来名称相关的“直觉节点”（如“中叶”）。
Step 2. 轴心分析与证据回溯 (Axis Analysis & Evidence)
    观察：观察当前子节点列表是按什么维度区分的？（解剖部位？病因？临床表现？）
    回溯：针对该维度，回到病历的 Step 2 (病理/手术) 中寻找确凿证据。
Step 3. 全要素特异性权衡 (Full-Concept Specificity)
    原则：特定实体的匹配度 > 泛化类别的匹配度；疾病性质 > 单纯解剖部位。
    核心逻辑：
        直觉陷阱：不要因为看到了一个符合“大类”的节点（如看到“中叶”选“中叶节点”）就立即停止思考。
        完整性检查：问自己：“当前的节点名称是否覆盖了病历中所有的关键定语？”如果病历是 “A+B”（如：中叶+细支气管），而当前节点只体现了“A”（中叶），但规则提示“A+B”其实在另一个节点下，必须选择后者。
        关键举例：
            正确：选择 K50.002 回肠克罗恩病（优先保留了“克罗恩病”这一核心疾病性质，胜过部位）。
            错误：选择 K50.000x001 末端性回肠炎（虽然“末端”部位很细，但丢失了“克罗恩病”本质，降级为了普通炎症）。
Step 4. 残余类目侦察 (Residual Category Recon)
    认知重塑：在ICD体系中，.9（未特指）和.8（其他）不仅仅是“不知道”，它们经常是特定微细结构或特殊病理类型的“藏身之处”。
    操作指令：
        当病历诊断包含非常具体但未在标准子节点名称中出现的描述时，严禁直接忽略 .8/.9 节点。
        必须先查阅 Step 1 中的规则，或使用 get_child_node 确认这些“兜底”节点中是否隐藏了该特定疾病。
Step 5. 时效性过滤 (Temporal Filtering)
    检查：检查找到的证据是否属于本次住院发生或处理的？
    过滤：严禁将“既往史”与本次病变混合编码。（例如：本次治疗左侧，既往有右侧，不得选择双侧编码）。

---

### 5. 工具函数列表

你可调用的工具函数列表被一个XML格式的<tools></tools>标签包裹：
<tools>
    {tools}
</tools>

在回答用户提出的问题时，根据用户提问的结尾决定响应模式：

    如果用户提问以"/think"结尾，表示启用思考模式。请先输出思考过程，用<think>思考过程</think>\n\n标签包裹（其中"思考过程"替换为你的实际思考内容），然后给出回答。

    如果用户提问以"/no think"结尾，表示不启用思考模式。请先输出固定的空思考标签：<think>\n\n</think>\n\n，然后直接给出回答。

无论是否启用思考模式，在回答过程中需要调用函数时，请使用以下格式：先用XML格式的<tool_call></tool_call>标签包裹，然后使用JSON格式指定函数名称和参数。

<tool_call>
{{
    "name": "function_name",
    "arguments": {{}}
}}
</tool_call>

工具函数返回的结果将通过<tool_response>标签提供给你，格式如下：
<tool_response>
工具返回数据
</tool_response>
"""
# ########输出格式
# 你的输出必须包含以下两个部分，且必须严格遵循本格式：

# 1. 推理过程

# 结合上下文信息，逐步展示你的思考路径。

# 清晰阐述你选择调用特定工具的理由。

# 2. 调用信息

# 此部分必须以严格的、可被Python json.loads() 解析的JSON格式输出。
# JSON
# ```
# {{
#     "name": "function_name",
#     "arguments": {{
#         "parameter1": "value1",
#         "parameter2": "value2"
#     }}
# }}
# ```
    messages.append({"role": "system", "content": system_prompt})
    if history:
        # print(history)
        for h in history:
            if 'user' in h:
                messages.append({"role": "user", "content": h["user"]})
            if "assistant" in h:
                messages.append({"role": "assistant", "content": h["assistant"]})
    if image_paths:  # image_paths 是图片路径组成的列表
        content = [{"type": "text", "text": prompt}]

        for image_path in image_paths:
            with open(image_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode('utf-8')
            mime_type, _ = mimetypes.guess_type(image_path)
            mime_type = mime_type or "image/png"  # fallback
            data_url = f"data:{mime_type};base64,{b64_image}"
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": data_url
                }
            })
        # 构造图文混合消息
        image_message = {
            "role": "user",
            "content": content
        }

        messages.append(image_message)
    else:
        # 纯文本输入
        messages.append({"role": "user", "content": prompt})
    # 调用模型
    response = client.chat.completions.create(
        model="deepseek-chat",##deepseek-r1   qwen3-30b-a3b  qwen3-235b-a22b MOE qwen3-max
        messages=messages,
        temperature=0.0
        # extra_body={"enable_thinking": False},
    )
    
    return response.choices[0].message.content

def generate_gpt4o(prompt,api_key,base_url,image_paths=None,history=None):
    client = OpenAI(api_key=api_key, base_url=base_url)
    # 设置 API 密钥
    # 创建消息历史记录，包含之前的对话
    messages = []
    system_prompt="""你是一个强大的人工智能助手，能够基于用户的输入回答问题。
    在回答用户提出的问题时，根据用户提问的结尾决定响应模式：

    如果用户提问以"/think"结尾，表示启用思考模式。请先输出思考过程，用<think>思考过程</think>\n\n标签包裹（其中"思考过程"替换为你的实际思考内容），然后给出回答。

    如果用户提问以"/no think"结尾，表示不启用思考模式。请先输出固定的空思考标签：<think>\n\n</think>\n\n，然后直接给出回答。"""
    messages.append({"role": "system", "content": system_prompt})
    if history:
        # print(history)
        for h in history:
            if 'user' in h:
                messages.append({"role": "user", "content": h["user"]})
            if "assistant" in h:
                messages.append({"role": "assistant", "content": h["assistant"]})
    if image_paths:  # image_paths 是图片路径组成的列表
        content = [{"type": "text", "text": prompt}]

        for image_path in image_paths:
            with open(image_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode('utf-8')
            mime_type, _ = mimetypes.guess_type(image_path)
            mime_type = mime_type or "image/png"  # fallback
            data_url = f"data:{mime_type};base64,{b64_image}"
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": data_url
                }
            })
        # 构造图文混合消息
        image_message = {
            "role": "user",
            "content": content
        }

        messages.append(image_message)
    else:
        # 纯文本输入
        messages.append({"role": "user", "content": prompt})
    # 调用模型
    response = client.chat.completions.create(
        model="deepseek-chat",##deepseek-r1   qwen3-30b-a3b  qwen3-235b-a22b MOE qwen3-max
        messages=messages,
        temperature=0.0
        # extra_body={"enable_thinking": False},
    )
    
    return response.choices[0].message.content



def GetContent(process_dict: dict, previous_func: str, params: dict) -> dict:
    """
    增强功能：
    - 空二级字段 → 输出原始内容
    - 单二级字段 → 输出 <fieldname>一级-二级</fieldname>
    - 多二级字段 + 非列表 → 聚合输出
    - 多二级字段 + 列表 → 每项独立输出为 <fieldname>一级1</fieldname>, <fieldname>一级2</fieldname>...
    """
    # 预处理
    now_func="GetContent"
    emr_dict = process_dict.get("emr_dict", {}) 
    field_names = params.get("field_name", [])
    
    if not field_names:
        process_dict[now_func + "_output"] = "无字段可提取"
        return process_dict

    from collections import OrderedDict
    fields_group = OrderedDict()
    for first, second in field_names:
        if first not in fields_group:
            fields_group[first] = []
        fields_group[first].append(second)

    content_lines = []

    for first_field, second_fields in fields_group.items():
        try:
            value = emr_dict.get(first_field)
            if value is None:  
                content_lines.append(f"<fieldname>{first_field}</fieldname>:该字段缺失")
                continue

            # ===== 情况1：存在空二级字段 → 输出原始内容 =====
            if any(not sec or sec == "" for sec in second_fields):
                raw_str = str(value)
                content_lines.append(f"<fieldname>{first_field}</fieldname>: {raw_str}")
                continue

            # 过滤有效二级字段
            valid_seconds = [sec for sec in second_fields if sec]

            # ===== 情况2：一级字段是列表 → 每项独立输出 =====
            if isinstance(value, list):
                valid_items = [item for item in value if isinstance(item, dict)]
                if not valid_items:
                    content_lines.append(f"<fieldname>{first_field}</fieldname>:内容缺失")
                    continue

                for idx, item in enumerate(valid_items, start=1):
                    parts = []
                    for sec in valid_seconds:
                        val = item.get(sec, "内容缺失")
                        if val in (None, ''):
                            val = "内容缺失"
                        elif not isinstance(val, str):
                            val = str(val)
                        parts.append(f"<{sec}>{val}</{sec}>")
                    inner_content = "；".join(parts)
                    tag_name = f"{first_field}{idx}"
                    content_lines.append(f"<fieldname>{tag_name}</fieldname>: {inner_content}")

            # ===== 情况3：非列表 → 正常处理（单字段 or 多字段聚合）=====
            else:
                parts = []
                for sec in valid_seconds:
                    if isinstance(value, dict):
                        val = value.get(sec, "内容缺失")
                    else:
                        val = "内容缺失"
                    if val in (None, ''):
                        val = "内容缺失"
                    elif not isinstance(val, str):
                        val = str(val)
                    parts.append(f"<{sec}>{val}</{sec}>")
                inner_content = "；".join(parts)

                if len(valid_seconds) == 1:
                    second_field = valid_seconds[0]
                    tag_name = f"{first_field}-{second_field}"
                    line = f"<fieldname>{tag_name}</fieldname>: {inner_content}"
                else:
                    line = f"<fieldname>{first_field}</fieldname>: {inner_content}"
                content_lines.append(line)

        except Exception as e:
            print(f"Error in GetContent for {first_field}: {str(e)}")
            content_lines.append(f"<fieldname>{first_field}</fieldname>:该字段缺失")

    # 合并输出，用 <splitpoint> 分隔
    now_func_output = "<splitpoint>\n".join(content_lines)
    process_dict[now_func + "_output"] = now_func_output
    return process_dict

def ICD_GetContent_v2(process_dict: dict, previous_func: str, params: dict) -> dict:
    """
    增强功能：
    - 空二级字段 → 输出原始内容
    - 单二级字段 → 输出 <fieldname>一级-二级</fieldname>
    - 多二级字段 + 非列表 → 聚合输出
    - 多二级字段 + 列表 → 每项独立输出为 <fieldname>一级1</fieldname>, <fieldname>一级2</fieldname>...
    """
    # 预处理
    now_func="GetContent"
    emr_dict = process_dict.get("emr_dict", {}) 
    error_hanppe=process_dict.get("error_hanppen",False)
    if error_hanppe:
        return process_dict

    file_name_list=params.get("field_name")
    from collections import defaultdict
    grouped = defaultdict(list)
    for item in file_name_list:
        if isinstance(item, list) and len(item) == 2:  # 防御性编程：确保是 [doc, field]
            grouped[item[0]].append(item)
    file_content={}
    item_str_list=""
    for doc_name, fields in grouped.items():
        item_str=GetContent(process_dict, None, {"field_name": fields})['GetContent_output']
        if '该字段缺失' in item_str or '内容缺失' in item_str:
            continue
        else:
            item_str_list+=item_str+"\n"
            file_content[doc_name]=item_str
    process_dict['file_content']=file_content
    print(file_content.keys())
    return process_dict



tools = [
    {
        "name": "get_child_node",
        "description": "获取指定节点下的所有子节点信息。node_id 必须从系统已记录的 node_list 中选择（node_list 包含用户此前通过本工具或路径选择所查看过的节点及其子节点）。",
        "parameters": {
            "type": "object",
            "properties": {
                "node_id": {
                "type": "string",
                "description": "指定节点的node_id，必须属于系统当前维护的 node_list 范围内"
                }
            },
            "required": ["node_id"],

        }
    },
    {
        "name": "select_next_node",
        "description": "该步骤通过选定子节点来更新当前节点，从而进入编码树的下一层级。",
        "parameters": {
            "type": "object",
            "properties": {
                "selected_node_id": {
                    "type": "string",
                    "description": "所选节点ID必须来自当前节点的子节点列表，不可选择列表外的节点。"
                },
                "evidence_quote": {
                    "type": "string",
                    "description": "【关键证据】支持从当前父节点进入该子节点的电子病历原文片段。"
                },
                "rule_quote": {
                    "type": "string",
                    "description": "【规则依据】支持本次选择的ICD编码规则或优先原则。"
                }   
            },
            "required": ["selected_node_id","evidence_quote","rule_quote"],

        }
        
    },
    {  
        "name": "validate_current_node",
        "description": "基于电子病历内容，评估当前选择的编码节点是否合理。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],

        }
        
    },
    {
        "name": "backtry_path",
        "description": "该步骤通过选定回退层级来更新当前节点，从而返回到编码树的指定层级。",
        "parameters": {
        "type": "object",
        "properties": {
                "level": {
                "type": "integer",
                "description": "指定应回退到的目标层级（0=根节点, 1=章节, 2=类目, 3=亚目）",
                "minimum": 0,
                "maximum": 3
                }
            },
            "required": ["level"],
        }
        
    },
    {
        "name": "finish_selection",
        "description": "结束编码选择流程。仅当当前层级为最终编码（level=4）且已通过至少一次节点校验（即 validate_current_node）时允许调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "node_id": {
                "type": "string",
                "description": "最终选定节点的编号",
                },
                "name": {
                "type": "string",
                "description": "最终选定节点的名称",
                }
            },
        "required": ["node_id","name"],
        }
    }
]

def format_chapter(chapter_data):
    """将单个章节的 JSON 对象转换为指定格式的字符串"""
    chapter_name = chapter_data["chapter"]
    sub_codes = chapter_data["sub_codes"]
    lines = [f"{chapter_name}包含"]
    for item in sub_codes:
        code_range = item["节范围"]
        name = item["节名称"]
        lines.append(f"{code_range}，{name}")
    return "\n".join(lines)

def get_coding_rule(node_id,level):
    node_rule_list=[]
    if level==0:
        rule_list=load_jsonl(BASE_RULE_FILE0)
        for item in rule_list:
            # print(item)
            rule_content=format_chapter(item)
            node_rule_list.append(rule_content)
        rule_list=load_jsonl(BASE_RULE_FILE)
        for rule_item in rule_list:
            node_rule_list.append(rule_item['rule_content'])
    elif level==1:
        rule_list=load_jsonl(CHAPTER_RULE_FILE)
        node_dict={}
        for item in rule_list:
            node_dict[item['chapter']]=item
        if node_id not in node_dict:
            return 0,None
        else:
            rule_list=node_dict[node_id]['chapter_rules']
            for item in rule_list:
                node_rule_list.append(item['rule_content'])
    elif level==2:
        rule_list=load_jsonl(CATEGORY_RULE_FILE)
        node_dict={}
        for item in rule_list:
            node_dict[item['sub_chapter']]=item
        if node_id not in node_dict:
            return 0,None
        else:
            rule_list=node_dict[node_id]['category_rules']
            for item in rule_list:
                node_rule_list.append(item['rule_content'])
    elif level==3:
        rule_list=load_jsonl(SUBCATEGORY_RULE_FILE)
        node_dict={}
        for item in rule_list:
            node_dict[item['de_chapter']]=item
        if node_id not in node_dict:
            return 0,None
        else:
            rule_list=node_dict[node_id]['subcategory_rules']
            for item in rule_list:
                node_rule_list.append(item['rule_content'])
    if not node_rule_list:
        node_rule_list.append('该编码下无特殊编码规则，请根据电子病历内容和ICD节点信息判断选择路径')
    return 1,node_rule_list

import copy
def backtry_path(pass_flag, level, node, path, parent_node, current_coding_trace):
    """
    level: 目标回退层级 (0=Root, 1=Chapter, etc.)
    current_coding_trace: [{'level':1, ...}, {'level':2, ...}] (不包含Level 0)
    """
    
    # --- 1. 节点与路径处理 (保持原逻辑) ---
    if level == 0:
        new_parent_node = {"level": 0, "node_id": "root", "name": "根节点"}
    else:
        new_parent_node = parent_node 

    current_path_list = path[-1]
    new_path_list = []
    target_item = None

    for item in current_path_list:
        item_copy = copy.deepcopy(item)
        if item_copy['level'] == level:
            target_item = item_copy
            new_path_list.append(item_copy)
            break 
        else:
            new_path_list.append(item_copy)
            new_parent_node = item_copy

    # print(f"当前尝试回退至 Level: {level}")
    
    if not target_item:
        # print("回退失败：在当前路径中未找到指定层级")
        return 0, node, path, parent_node, current_coding_trace

    path.append(new_path_list)
    
    # --- 2. 证据链回溯处理 (核心修改) ---
    
    # 逻辑说明：
    # 如果回退到 Level 0: 条件为 trace_level <= 0。
    #   由于 trace 中最小 level 是 1，所有条目都不满足，结果为 [] (正确，回到根节点无证据)。
    # 如果回退到 Level 1: 条件为 trace_level <= 1。
    #   保留 Level 1 的证据，丢弃 Level 2, 3... 的证据 (正确，保留了进入该章节的依据)。
    
    new_coding_trace = [
        trace for trace in current_coding_trace 
        if trace['level'] <= level
    ]
    
    # print(f"证据链已回退，保留前 {len(new_coding_trace)} 条记录")

    # --- 3. 获取子节点与规则 ---
    c_code, child_list = get_child_node(target_item['node_id'], target_item['level'])
    r_code, rule_list = get_coding_rule(target_item['node_id'], target_item['level'])
    pc_code, pchild_list = get_child_node(new_parent_node['node_id'], new_parent_node['level'])

    new_node = {
        "level": target_item['level'],
        "node_id": target_item['node_id'],
        "name": target_item['name'],
        "check_rules": rule_list,
        "child_node": child_list
    }

    new_parent_node_struct = {
        "level": new_parent_node['level'],
        "node_id": new_parent_node['node_id'],
        "name": new_parent_node['name'],
        "check_rules": [],
        "child_node": pchild_list
    }

    return 1, new_node, path, new_parent_node_struct, new_coding_trace
    
def up_data_node_list(node,node_list):
    node_dict = {item["node_id"]: item for item in node_list}
    if node['level']!=0:
    # 添加当前节点,根节点不添加
        node_dict[node["node_id"]] = {
            "level": node["level"],
            "node_id": node["node_id"],
            "name": node["name"]
        }
    # 添加所有子节点
    for child in node["child_node"]:
        node_dict[child["node_id"]] = {
            "level": child["level"],
            "node_id": child["node_id"],
            "name": child["name"]
        }

    # 转换回列表并返回
    return list(node_dict.values())

def up_data_node_list_after_call(child_list,node_list):
    if child_list is None:
        return node_list
    node_dict = {item["node_id"]: item for item in node_list}
    for child in child_list:
        node_dict[child["node_id"]] = {
            "level": child["level"],
            "node_id": child["node_id"],
            "name": child["name"]
        }

    # 转换回列表并返回
    return list(node_dict.values())

def format_path_to_str(path):
    """
    将路径列表转换为 'node_id name -> node_id name' 格式的字符串。
    
    参数:
        path (list): 节点路径列表，每个元素为 dict，包含 'node_id', 'name', 'level'
    
    返回:
        str: 格式化后的路径字符串，如 "A00 霍乱 -> A00.0 霍乱弧菌"
    """
    return " -> ".join(f"{node['node_id']} {node['name']}" for node in path)





def get_child_node(node_id,level):
####根据node_id,level，获得子节点 返回【int，list】0表示节点错误 1表示正常 -1表示层级错误

    child_node_list=[]
    if level==0:
        node_list=load_jsonl(CHAPTER_FILE)
        for node_item in node_list:
            child_node_list.append({'node_id':node_item["chapter"],"name":node_item["name"],"level":1})
    elif level==1:
        node_dict={}
        node_list=load_jsonl(CHAPTER_FILE)
        for node_item in node_list:
            node_dict[node_item["chapter"]]=node_item
        if node_id not in node_dict:
            return 0,None
        else:
            node_list=node_dict[node_id]['sub_code']
            for node_item in node_list:
                child_node_list.append({'node_id':node_item["code"],"name":node_item["name"],"level":2})
    elif level==2:
        node_dict={}
        node_list=load_jsonl(CATEGORY_FILE)
        for node_item in node_list:
            node_dict[node_item["sub_chapter"]]=node_item
        if node_id not in node_dict:
            return 0,None
        else:
            node_list=node_dict[node_id]['sub_code']
            ####可能存在类目节点的下级节点没有亚目节点，而是直接为最终节点
            if not node_list:
                node_dict={}
                node_list=load_jsonl(SUBCATEGORY_FILE)
                for node_item in node_list:
                    node_dict[node_item["de_chapter"]]=node_item
                if node_id not in node_dict:
                    return 0,None
                else:
                    node_list=node_dict[node_id]['sub_code']
                    # desc_dict={}
                    # desc_list=load_jsonl(ITEM_DESC_FILE)
                    # for desc_item in desc_list:
                    #     desc_dict[desc_item["code"]]=desc_item
                    
                    for node_item in node_list:
                        # desc=desc_dict[node_item["code"]]['desc']
                        # child_node_list.append({'node_id':node_item["code"],"name":node_item["name"],"level":4,"desc":desc})
                        child_node_list.append({'node_id':node_item["code"],"name":node_item["name"],"level":4})
            else:
                for node_item in node_list:
                    child_node_list.append({'node_id':node_item["code"],"name":node_item["name"],"level":3})
    elif level==3:
        node_dict={}
        node_list=load_jsonl(SUBCATEGORY_FILE)
        for node_item in node_list:
            node_dict[node_item["de_chapter"]]=node_item
        if node_id not in node_dict:
            return 0,None
        else:
            node_list=node_dict[node_id]['sub_code']
            # desc_dict={}
            # desc_list=load_jsonl(ITEM_DESC_FILE)
            # for desc_item in desc_list:
            #     desc_dict[desc_item["code"]]=desc_item
            
            for node_item in node_list:
                # desc=desc_dict[node_item["code"]]['desc']
                # child_node_list.append({'node_id':node_item["code"],"name":node_item["name"],"level":4,"desc":desc})
                child_node_list.append({'node_id':node_item["code"],"name":node_item["name"],"level":4})
            # for node_item in node_list:
            #     child_node_list.append({'node_id':node_item["code"],"name":node_item["name"],"level":4})
    else:
        return -1,None
    return 1,child_node_list

def select_next_node(node,select_node_id,path):
    sub_node_list=node['child_node']
    node_dict={}
    for item in sub_node_list:
        node_dict[item['node_id']]=item
    if select_node_id not in node_dict:
        return 0,node,path
    else:
        if node_dict[select_node_id]['level']==4:
            node={"level":node_dict[select_node_id]['level'],"node_id":select_node_id,"name":node_dict[select_node_id]['name'],"check_rules":['该编码下无特殊编码规则，请根据电子病历内容和ICD节点信息判断选择路径'],"child_node":[]}
            path[-1].append({"level":node_dict[select_node_id]['level'],"node_id":select_node_id,"name":node_dict[select_node_id]['name']})
            return 1,node,path
        else:
            c_code,child_list=get_child_node(select_node_id,node_dict[select_node_id]['level'])
            r_code,rule_list=get_coding_rule(select_node_id,node_dict[select_node_id]['level'])
            if c_code==1 and r_code==1:
                node={"level":node_dict[select_node_id]['level'],"node_id":select_node_id,"name":node_dict[select_node_id]['name'],"check_rules":rule_list,"child_node":child_list}
                path[-1].append({"level":node_dict[select_node_id]['level'],"node_id":select_node_id,"name":node_dict[select_node_id]['name']})
                return 1,node,path
            else:
                return -1,node,path

def check_emr_content(process_dict,part,params):
    new_params={}
    if "field_name" not in params:
        new_params={"field_name": []}
        filtered=[]
    
    filtered = [
        [record, field] for record, field in params["field_name"]
        if record == part
    ]
    # new_params={"field_name": filtered}
    item_str=GetContent(process_dict, None, {"field_name": filtered})['GetContent_output']
    return item_str




def validate_current_node(parent_node,currnt_node,currnt_path,file_content,current_coding_trace,answer_path):
#     # print("父节点")
#     # print(parent_node)
    
    # A. 纵向路径（静态结构与规则）
    path_context_str = ""
    # 建立一个 ID 到 Name 的映射，方便后面给 Trace 补全名称
    id_to_name_map = {} 
    
    for idx, node in enumerate(currnt_path):
        id_to_name_map[node['node_id']] = node['name']
        
        # 修改：不使用 .get('rules', [])
        if 'rules' in node and node['rules']:
            rules = node['rules']
            rules_str = "\n      - ".join(rules)
            rules_str = "\n      - " + rules_str
        else:
            rules_str = "无特殊规则"
            
        indent = "  " * idx
        path_context_str += f"{indent}-> [Level {node['level']}] {node['node_id']} {node['name']}\n{indent}   【节点对应规则】:{rules_str}\n"

    # B. 历史决策轨迹（动态推理过程）
    trace_context_str = ""
    if current_coding_trace:
        for step in current_coding_trace:
            # 修改：不使用 .get(id, default)
            node_id = step['node_id']
            if node_id in id_to_name_map:
                node_name = id_to_name_map[node_id]
            else:
                node_name = "未知名称"
            
            # 修改：不使用 .get('step_evidence', '无')
            if 'step_evidence' in step:
                evidence = step['step_evidence']
            else:
                evidence = "无"
                
            # 修改：不使用 .get('step_rule', '无')
            if 'step_rule' in step:
                rule = step['step_rule']
            else:
                rule = "无"

            trace_context_str += f"-> [Level {step['level']}] 选择了: {node_id} ({node_name})\n"
            trace_context_str += f"   [Agent引用证据]: {evidence}\n"
            trace_context_str += f"   [Agent引用规则]: {rule}\n"
    else:
        trace_context_str = "无历史轨迹（可能是首层或回退后重置）。"

    # C. 横向兄弟节点
    siblings_str = ""
    # 修改：不使用 .get('child_node', [])
    if 'child_node' in parent_node and parent_node['child_node']:
        siblings = parent_node['child_node']
        for sib in siblings:
            marker = "★(当前选择)" if sib['node_id'] == currnt_node['node_id'] else ""
            siblings_str += f"- {sib['node_id']} {sib['name']} {marker}\n"
    else:
        siblings_str = "无（当前为根节点下的直接选择或无兄弟节点）"

    # --- 2. 构建校验 Prompt ---
    # print(path_context_str)
    # print("---------------------------------------")
    # print(siblings_str)
    vaild_prompt = f"""
### 角色定义
你是一名**极其严苛**的医疗ICD编码校验专家。
你的核心职责是充当“守门员”，不仅要审查**结果**是否正确，还要审查Agent的**推理依据（证据和规则）**是否真实有效。

### 输入信息
**1. 电子病历内容**：
{file_content}

**2. 待校验的编码路径（静态层级与系统规则）**：
{path_context_str}

**3. 历史决策轨迹（Agent的推理依据） —— *请重点核查此处的真实性***：
{trace_context_str}

**4. 当前层级的候选列表（横向上下文/兄弟节点）**：
{siblings_str}

**5. 当前最终选择**：
{currnt_node['node_id']} {currnt_node['name']}

---

### 【核心校验标准】（必须严格遵守的法典）

#### A. 病历阅读与证据运用策略
**Step 1 - 初步判定**：依据 **出院记录** 快速锚定核心原因。
**Step 2 - 细节细化**：依据 **病理报告 > 手术记录 > 专项检查** 填充特异性信息（部位/类型）。**病理是金标准**，若与出院诊断不一致，以病理为准。
**Step 3 - 时效性界定 (关键步骤)**：
*   **规则**：严格区分“本次住院情况”与“既往史/陈旧性病变”。
*   **操作**：仅编码本次住院期间**发现、治疗或护理**的疾病/部位。**既往史仅供参考，不做编码依据**。
    *   *案例*：本次治疗“左侧”，既往有“右侧”，**禁止**编码“双侧”。
**Step 4 - 缺项补全**：仅当上述步骤无法提供信息时，才查阅入院记录。

注意：   证据运用的“三不原则” (Anti-Hallucination)
    1.  **不推断**：**体征/检查结果 $\neq$ 临床诊断**。
        *   *严禁案例*：看到“盆腔积血”，**不得**推断为“异位妊娠**破裂**”，除非医生明确写了“破裂”。
        *   *严禁案例*：看到“包块/结节/占位”，**不得**推断为“**肿瘤**”，除非病理或诊断明确写了“瘤/癌”。
    2.  **不拼接**：主要诊断的部位信息必须来自主诊本身，不得将次要诊断的部位强加给主诊。
    3.  **不跨越时效**：
        *   *严禁案例*：本次住院治疗“左侧”，既往史提及“右侧”，**不得**编码“双侧”。

#### B. 主要诊断选择规则
    **一、【核心原则（总则）】**
    主要诊断是指本次住院期间：对患者健康危害最严重、消耗医疗资源最多、住院时间最长的疾病或健康问题。
    *   **时效性原则**：主要诊断必须是**本次住院期间**发生或处理的疾病。既往已治愈或本次未处理的陈旧性疾病，不得作为主要诊断，且在涉及部位编码（如单侧/双侧）时，必须仅体现本次受累部位。

    **二、【具体选择规则（补充规则）】**

    *   **病因与临床表现**
        *   若病因诊断能充分涵盖临床表现，优先选择病因诊断。
        *   若临床表现代表疾病严重阶段（如心肌梗死、心力衰竭），且非终末状态，则选择该临床表现。
    *   **未确诊情况**
        *   当诊断未明确时，以症状、体征或异常检查结果（R类）作为主要诊断。
        *   怀疑诊断在出院时未被排除：按肯定诊断处理。
        *   怀疑诊断在出院时已被排除：编码为 Z03.-。
    *   **急慢性疾病**
        *   慢性病急性发作：优先选择急性编码；若存在对应的合并编码（如 J44.1），**必须使用合并编码**。
    *   **后遗症**
        *   后遗症类编码（如 I69.-）仅作为附加编码。主要诊断应为当前正在治疗的具体功能障碍（如“偏瘫”）。
    *   **损伤**
        *   选择最严重的损伤；若无法明确严重程度，使用综合编码（如 T07.-）。
        *   优先级：内部损伤 > 浅表伤；颅内损伤 > 颅骨骨折。
    *   **产科**
        *   存在产科并发症时，选择最主要的并发症（如 O14.1）。
    *   **恶性肿瘤（重中之重）**
        *   **手术/确诊**：本次住院进行了肿瘤切除、活检或首次确诊 -> 选择 **C00-D48 (肿瘤实体)**。
        *   **仅化疗/放疗**：本次住院**未实施手术**，仅接受放疗、化疗、靶向或免疫治疗 -> **必须选择 Z51.-**。
        *   **仅复查**：既往已手术，本次仅复查、随访 -> 选择 **Z08.-**。
        *   *注意：即使既往有肿瘤史，若本次仅处理并发症且未针对肿瘤治疗，选并发症为主诊。*
  

---

### 校验任务（三维度审查）

请严格按照以下逻辑进行判断。**任何一个维度不通过，校验结果即为“不符合”。**

#### 第一维度：推理依据真实性校验（Consistency Check）
**目标**：检查“历史决策轨迹”中 Agent 填写的证据和规则是否造假。
1.  **证据真实性**：
    *   Agent 引用的 `[Agent引用证据]` 是否能在电子病历原文中**逐字找到**？
    *   *错误示范*：Agent 引用了“病理示恶性肿瘤”，但病历原文只有“待排肿瘤”。 -> **不符合**。
2.  规则引用审查（豁免模式）：
跳过此检查。即使 Agent 引用了完全无关的规则，只要它选对了节点，本项视为通过。

#### 第二维度：主要诊断方向校验（定性判断）
1.  **规则冲突**：是否违反排除项或肿瘤/产科核心规则？
2.  **时效性**：是否为本次住院主要治疗的疾病？

#### 第三维度：特异性与横向对比校验（定量判断）
**目标**：在剔除错误修饰词的同时，确保选择的是**全维度最精准**的编码。

1.  **过度编码审查（Over-coding Check）**：
    *   **检查对象**：编码名称中的修饰词（如：**陈旧性、破裂、出血、梗阻、双侧**）。
    *   **判定**：若病历原文未出现该修饰词，视为**不符合**。（如：病历无“陈旧性”，选了O00.116即错）。

2.  **横向对比与全维度特异性**：
    *   扫描 **“4. 当前层级的候选列表”**。
    *   **是否存在比当前节点包含更多病历实证信息的选项？**
        *   **【解剖部位】**：病历写“伞端/伞部”，兄弟节点是否有“伞部”？（优于笼统的“输卵管”）。
        *   **【病因/病理】**：病历写“细菌性”或“化脓性”，兄弟节点是否有对应项？
        *   **【急慢性】**：病历写“急性”，兄弟节点是否有“急性”？
    *   **判定**：若兄弟节点中存在一个选项，它**既剔除了（步骤1中发现的）错误修饰词**，又**包含了上述任一维度的正确细节**，则当前选择**不符合**。建议改选该兄弟节点。

3. **特殊规则归类优先**
*   **触发场景**：Agent 选择了 **.9（未特指）** 或 **.8（其他）**，而兄弟节点中存在看似更具体的“解剖部位”选项（如 .2 中叶、.1 上叶）。
*   **强制动作**：**必须查阅** 输入信息“2. 待校验的编码路径” 中的 `node_rules` 或 `check_rules`。
*   **判决逻辑**：
    *   如果规则**明确指出**病历中的具体诊断（如“细支气管恶性肿瘤”、“卡波西肉瘤”）被归类在 **.9** 或 **.8** 下。
    *   **结论**：**Agent 的选择正确**。规则归类优先级 > 字面解剖匹配度。
    *   *案例*：病历为“右肺中叶细支气管肺泡癌”。Agent 选 C34.9。虽然兄弟节点 C34.2（中叶）看似更好，但规则提示“细支气管癌归入 C34.9”。此时 C34.9 胜出，校验通过。

4. **常规特异性判定**：
*   **仅在未触发 Step 3 豁免时执行**：
*   若兄弟节点中存在一个选项，它**既包含了更多病历实证细节（部位/病因/急慢性）**，又**未被特殊规则排除**，则当前选择**不符合**。


        ---

        ### 输出格式
        ```json
        {{
            "校验结果": "符合" 或 "不符合",
            "理由": "简明扼要。若不符合，请明确指出：'病历支持兄弟节点 XX(ID)，优于当前选择 YY'，或者 '违反了 Level X 的规则...'。"
        }}
"""   


    for _ in range(3):
        vaild_prompt=vaild_prompt+"。/think"
        check_prompt=chat_method3(vaild_prompt,[])
        # print("-----------------------------------------反思校验----------------------")
        # print(check_prompt)
        check_answer_content=extract_operations(check_prompt,["校验结果","理由"])
        check_answer_content=check_answer_content[-1]
        if check_answer_content["校验结果"] in ["符合","不符合"]:
            break
    return check_answer_content["校验结果"],check_prompt


# def validate_current_node(parent_node,currnt_node,currnt_path,file_content,current_coding_trace,answer_path):
#     """
#     只根据 currnt_node 与 answer_path 进行比对。
#     返回值仅为: (status, message)
#     语气调整：改为引导性、推荐性话术。
#     """
    
#     current_id = currnt_node['node_id']
#     current_level = currnt_node['level']
    
#     # 1. 提取目标节点（答案的最后一个）
#     target_node = answer_path[-1]
#     target_id = target_node['node_id']

#     # 2. 构建查找索引
#     answer_id_map = {item['node_id']: i for i, item in enumerate(answer_path)}
#     answer_level_map = {item['level']: item for item in answer_path}

#     # =======================================================
#     # 情况 A: 刚好到达终点 (Success)
#     # =======================================================
#     if current_id == target_id:
#         return "符合", "当前编码与预期诊断完全一致。"

#     # =======================================================
#     # 情况 B: 节点在正确路径上，但未结束 (In Progress)
#     # =======================================================
#     if current_id in answer_id_map:
#         idx = answer_id_map[current_id]
        
#         # 检查是否还有下一个节点
#         if idx < len(answer_path) - 1:
#             next_node = answer_path[idx + 1]
#             # 语气修改：引导下一步
#             message = (
#                 f"当前节点({current_id})路径正确，建议继续下钻。"
#                 f"在下一层级中，建议重点关注并选择：{next_node['name']} ({next_node['node_id']})。"
#             )
#             return "不符合", message
#         else:
#             return "符合", "当前编码与预期诊断完全一致。"

#     # =======================================================
#     # 情况 C: 节点错误 (Off Track)
#     # =======================================================
#     else:
#         # 获取当前层级在标准路径中对应的节点
#         should_be_node = answer_level_map.get(current_level)
#         back_level = current_level - 1 if current_level > 0 else 0
        
#         if should_be_node:
#             # 语气修改：推荐正确选项，而非生硬告知答案
#             rec_msg = f"建议尝试寻找更符合病历的节点：{should_be_node['name']} ({should_be_node['node_id']})"
#         else:
#             rec_msg = "建议重新审视病历中关于该层级的描述。"

#         # 语气修改：指出偏离并给出建议
#         message = (
#             f"当前节点 {current_id} ({currnt_node['name']}) 似乎偏离了最佳诊断路径。\n"
#             f"建议回退至上一级（Level {back_level}），并{rec_msg}。"
#         )
        
#         return "不符合", message





import json
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def compress_history_prompt(full_prompt_content):
    tag_start = "<tool_response>"
    tag_end = "</tool_response>"
    
    if tag_start not in full_prompt_content or tag_end not in full_prompt_content:
        return full_prompt_content

    try:
        # 1. 切割字符串
        start_idx = full_prompt_content.find(tag_start) + len(tag_start)
        end_idx = full_prompt_content.find(tag_end)
        
        prefix = full_prompt_content[:full_prompt_content.find(tag_start)]
        raw_str = full_prompt_content[start_idx:end_idx].strip()
        suffix = full_prompt_content[end_idx + len(tag_end):]
        
        data = None
        eval_context = {"null": None, "true": True, "false": False}
        
        # 2. 尝试解析 (Eval -> JSON -> 清洗后JSON -> 清洗后Eval)
        try:
            data = eval(raw_str, eval_context)
        except:
            pass
        
        if data is None:
            try:
                data = json.loads(raw_str)
            except:
                pass

        if data is None:
            try:
                # 暴力清洗转义符
                clean_str = raw_str.replace('\\"', '"').replace('\\\\', '\\')
                data = json.loads(clean_str)
            except:
                try:
                    data = eval(clean_str, eval_context)
                except:
                    pass

        if data is None or not isinstance(data, dict):
            return full_prompt_content

        # 3. 执行压缩
        compressed_data = copy.deepcopy(data)
        
        # 自动定位：是在根目录还是在 result 下
        target_dict = compressed_data
        if "result" in compressed_data and isinstance(compressed_data["result"], dict):
            target_dict = compressed_data["result"]
        
        # 压缩逻辑
        if "当前节点的子节点" in target_dict:
            val = target_dict["当前节点的子节点"]
            if isinstance(val, list):
                count = len(val)
                target_dict["当前节点的子节点"] = f"[{count} 个子节点数据已折叠]"
        
        if "当前节点的特殊规则" in target_dict:
            target_dict["当前节点的特殊规则"] = "[规则已折叠]"
            
        new_json_str = json.dumps(compressed_data, ensure_ascii=False)
        return f"{prefix}{tag_start}\n{new_json_str}\n{tag_end}{suffix}"

    except Exception as e:
        return full_prompt_content



def process_single_patient(select_data):
    try:
        patient_id = select_data["patient_id"]
        process_dict = dict()
        process_dict["emr_dict"] = select_data["emr_dict"]
        answer_code=select_data["answer_code"]
        answer_code_name=select_data["answer_code_name"]
        answer_path=select_data['answer_path']
        current_coding_trace=[]
        check_path_id=1

        if "patient" in patient_id or "PID_" in patient_id:
            process_dict = ICD_GetContent_v2(
                process_dict,
                previous_func="getMainCode",
                params={
                    "field_name": [
                        ["入院记录",""],
                        ["检查报告",""],
                        ["手术记录",""],
                        ["出院记录","文档内容"],
                        ["病理报告",""]
                    ]
                }
            )
           

        else:
            process_dict = ICD_GetContent_v2(
                        process_dict,
                        previous_func="getMainCode",
                        params={
                            "field_name": [
                                ["入院记录","文档内容"],
                                ["首次病程记录","诊断依据"],
                                ["主治医师首次查房记录","文档内容"],
                                ["主任医师首次查房记录","文档内容"],
                                ["手术记录","文档内容"],
                                ["会诊记录","文档内容"],
                                ["出院记录","诊疗经过"]
                            ]
                        }
                    )


        node = {"level": 0, "node_id": "root", "name": "根节点", "check_rules": [], "child_node": []}
        all_path = [[]]
        file_content = process_dict['file_content']

        a_code, code_list = get_child_node("root", 0)
        b_code, rule_list = get_coding_rule("root", 0)
        node["check_rules"] = rule_list
        node["child_node"] = code_list
        node_info = {"level": node["level"], "node_id": node["node_id"], "name": node['name']}
        parent_node = {}
        all_path[-1].append(node_info)

        node_list_all = []
        node_list_all = up_data_node_list(node=node, node_list=node_list_all)
        currnt_path = all_path[-1]
        currnt_path_info = format_path_to_str(currnt_path)
        history_list = []
        action_list = []
        stf_data=[]
        validate_list_check=[]
        check_time=0
        max_turn_cnt = 40
        check_finish=False
        base_prompt = f"""
        #############
        输入信息：
        病历内容：{file_content}
        当前节点：{node_info}
        当前节点的子节点：{node["child_node"]}
        当前维护的 node_list ：{node_list_all}
        当前节点的特殊规则：{node["check_rules"]}
        当前路径：{currnt_path_info}
        """
        base_prompt = base_prompt+"。/think"
        stf_data.append({"role":"user","content":base_prompt})


        finil_select = False
        for _ in range(max_turn_cnt):


            if len(history_list) >= 2:
                # history_list 的结构通常是 [User, Assistant, User, Assistant...]
                # 最后一条如果是 Assistant 的回复，倒数第二条就是 User 的 Prompt (也就是上一轮的 base_prompt)
                last_user_index = -2 if  'assistant' in history_list[-1] else -1
                
                # 只有当它是 User 角色时才压缩
                if 'user' in history_list[last_user_index]:
                    original_content = history_list[last_user_index]['user']
                    # 执行压缩
                    compressed_content = compress_history_prompt(original_content)
                    # 更新历史记录
                    history_list[last_user_index]['user'] = compressed_content
            # print(history_list)
            responce = chat_method2(base_prompt, history_list)
            # # print(base_prompt)
            # # print(len(history_list))
            # print(responce)
            if history_list and 'error' in history_list[-1]:
                history_list.append({'user': base_prompt,'error':True})
            else:
                history_list.append({'user': base_prompt})

            # history_list = [item for item in history_list if 'error' not in item]
            answer_tools = extract_operations(responce, ['name', 'arguments'])

            check_node_list_dict = {item['node_id']: item for item in node_list_all}
            check_sub_list_dict = {item['node_id']: item for item in node["child_node"]}

            if not answer_tools:
                geshi=f"""调用函数出错，格式错误。应该使用`<tool_call></tool_call>`标签包裹，然后内部使用**有效的JSON对象**指定函数名称和参数禁止在内部使用XML子标签格式**（如`<name>`、`<arguments>`等）
正确格式示例：
<tool_call>
{{
    "name": "function_name",
    "arguments": {{}}
}}
</tool_call>"
"""
                tool_response={"error":geshi}
                base_prompt=f"""<tool_response>\n{tool_response}\n</tool_response>。 /think"""
                history_list.append({'assistant': responce,'error':True})
                continue

            answer_tool = answer_tools[-1]
            action_list.append(answer_tool['name'])
            
            if answer_tool['name'] == 'get_child_node':
                if 'node_id' not in answer_tool['arguments']:
                    tool_response={"error":"调用函数出错，node_id没有出现在arguments中"}
                    base_prompt = tool_response
                    base_prompt="调用函数出错，node_id没有出现在arguments中"
                    
                else:
                    node_id = answer_tool['arguments']['node_id']
                    if node_id not in check_node_list_dict:
                        base_prompt = f"调用函数出错，你选择的node_id不在维护的node_list中。你选择的node_id为{node_id}，当前维护的 node_list ：{node_list_all}"
                        tool_response={"error":base_prompt}
                        # base_prompt=tool_response

                    else:
                        model_node = check_node_list_dict[node_id]
                        if model_node['level']==4:
                            tool_response={"选择node_id":node_id,"对应子节点":[]}
                            base_prompt = f"调用函数成功。你选择的node_id为{node_id}，其没有子节点"
                        else:
                            c_code, model_node_child = get_child_node(model_node['node_id'], model_node['level'])
                            node_list_all = up_data_node_list_after_call(model_node_child, node_list_all)
                            tool_response={"选择node_id":node_id,"对应子节点":model_node_child}
                            base_prompt = f"调用函数成功。你选择的node_id为{node_id}，其子节点为：{model_node_child}"
                        # base_prompt=tool_response

            elif answer_tool['name'] == 'select_next_node':
                if 'selected_node_id' not in answer_tool['arguments']:
                    base_prompt = "调用函数出错，selected_node_id没有出现在arguments中"
                    tool_response={"error":base_prompt}
                    # base_prompt=tool_response
                elif 'evidence_quote' not in answer_tool['arguments']:
                    base_prompt = "调用函数出错，evidence_quote没有出现在arguments中"
                    tool_response={"error":base_prompt}
                elif 'rule_quote' not in answer_tool['arguments']:
                    base_prompt = "调用函数出错，rule_quote没有出现在arguments中"
                    tool_response={"error":base_prompt}

                else:
                    node_id = answer_tool['arguments']['selected_node_id']
                    step_evidence = answer_tool['arguments']['evidence_quote']
                    step_rule = answer_tool['arguments']['rule_quote']
                    if node_id not in check_sub_list_dict:
                        base_prompt = f"调用函数出错，你选择的node_id不在当前节点的子节点列表中。你选择的node_id为{node_id}，当前节点为{node_info}，子节点列表：{node['child_node']}"
                        tool_response={"error":base_prompt}
                        # base_prompt=tool_response
                    else:
                        parent_node = node
                        s_code, node, path = select_next_node(node=node, select_node_id=node_id, path=all_path)
                        node_info = {"level": node["level"], "node_id": node["node_id"], "name": node['name']}
                        currnt_path = all_path[-1]
                        currnt_path_info = format_path_to_str(currnt_path)
                        base_prompt = f"""下移成功：
                        当前节点：{node_info}
                        当前节点的子节点：{node["child_node"]}
                        当前节点的特殊规则：{node["check_rules"]}
                        当前路径：{currnt_path_info}
                        """
                        tool_response={"当前节点":node_info,"当前节点的子节点":node["child_node"],"当前节点的特殊规则":node["check_rules"],"当前路径":currnt_path_info}
                        node_list_all = up_data_node_list_after_call(node["child_node"], node_list_all)
                        current_coding_trace.append({'node_id':node_info['node_id'],'level':node_info['level'],'step_evidence':step_evidence,'step_rule':step_rule})
                        # base_prompt=tool_response

            elif answer_tool['name'] == 'validate_current_node':
                if node_info['level']!=4:
                    base_prompt = "请选择到level4层次的最终结点后再选择校验"
                    tool_response={"error":base_prompt}
                else:
                    currnt_path = all_path[-1]
                    currnt_path_rule=[]
                    for item in currnt_path :
                        if item['node_id']=='root':
                            continue
                        r_flag,rules=get_coding_rule(item['node_id'],item['level'])
                        new_item={"node_id":item['node_id'],"name":item['name'],"level":item['level'],'rules':rules}
                        currnt_path_rule.append(new_item)
                    
                    check_pass, reason = validate_current_node(
                        parent_node=parent_node,
                        currnt_node=node_info,
                        currnt_path=currnt_path_rule,
                        file_content=file_content,
                        current_coding_trace=current_coding_trace,
                        answer_path=answer_path
                    )

                    check_time+=1
                    if check_pass == '符合':
                        base_prompt = f"经校验：当前选择编码符合病历内容。理由如下：{reason}"
                        tool_response={"校验结果":"符合","理由":reason}
                        check_finish=True
                    else:
                        base_prompt = f"经校验：当前选择编码不符合病历内。理由如下：{reason}"
                        tool_response={"校验结果":"不符合","理由":reason}
                    validate_list_check.append({"path_id":check_path_id,"check_pass":check_pass,"check_reason":reason,"current_coding_trace":current_coding_trace})
                    check_path_id+=1
                
            elif answer_tool['name'] == 'backtry_path':
                if 'level' not in answer_tool['arguments']:
                    base_prompt = "调用函数出错，level 没有出现在arguments中"
                    tool_response={"error":base_prompt}
                    # base_prompt=tool_response
                else:
                    model_level = answer_tool['arguments']['level']
                    if model_level not in [0,1,2,3]:
                        base_prompt = "调用函数出错，你选择的level不属于[0,1,2,3]"
                        tool_response={"error":base_prompt}
                        # base_prompt=tool_response
                    else:
                        v_code, node, all_path, parent_node,current_coding_trace = backtry_path(pass_flag=0, level=model_level, node=node, path=all_path, parent_node=parent_node,current_coding_trace=current_coding_trace)
                        node_info = {"level": node["level"], "node_id": node["node_id"], "name": node['name']}
                        currnt_path = all_path[-1]
                        currnt_path_info = format_path_to_str(currnt_path)
                        base_prompt = f"""调用函数成功，成功回退节点。
                        当前节点：{node_info}
                        当前节点的子节点：{node["child_node"]}
                        当前节点的特殊规则：{node["check_rules"]}
                        当前路径：{currnt_path_info}
                        """
                        tool_response={"当前节点":node_info,"当前节点的子节点":node["child_node"],"当前节点的特殊规则":node["check_rules"],"当前路径":currnt_path_info}
                        check_finish=False
                        # base_prompt=tool_response

            elif answer_tool['name'] == 'finish_selection':

                if 'node_id' not in answer_tool['arguments']:
                    base_prompt = "调用函数出错，node_id没有出现在arguments中"
                    tool_response = {"error": base_prompt}
                elif 'name' not in answer_tool['arguments']:
                    base_prompt = "调用函数出错，name没有出现在arguments中"
                    tool_response = {"error": base_prompt}
                
                # 2. 业务逻辑校验
                else:
                    # 提取参数方便后续比对
                    args = answer_tool['arguments']
                    submit_node_id = args['node_id']
                    submit_name = args['name']

                    # 逻辑A: 层级校验
                    if node_info['level'] != 4:
                        base_prompt = f"""
                        当前节点为{node_info['level']},所在层级不为最终编码，无法停止
                        当前节点的子节点：{node.get("child_node", "无")}
                        当前节点的特殊规则：{node.get("check_rules", "无")}
                        当前路径：{currnt_path_info}
                        """
                        tool_response = {"error": base_prompt}
                    
                    # 逻辑B: 流程校验 (是否已通过 validate_current_node)
                    elif not check_finish:
                        base_prompt = f"""
                        当前路径未经过校验，无法退出
                        """
                        tool_response = {"error": base_prompt}

                    # 逻辑C: 一致性校验 (防止模型提交的参数与当前实际停留节点不符)
                    elif submit_node_id != node_info['node_id'] or submit_name != node_info['name']:
                        base_prompt = f"""
                        提交参数错误：提交的最终编码信息与当前所在节点不一致。
                        当前所在节点：ID="{node_info['node_id']}", Name="{node_info['name']}"
                        你提交的信息：ID="{submit_node_id}", Name="{submit_name}"
                        请提交当前节点的正确信息。
                        """
                        tool_response = {"error": base_prompt}

                    # 3. 校验全部通过，结束流程
                    else:
                        stf_data.append({"role":"assistant","think_content":responce,"answer_content":answer_tool})
                        history_list.append({'assistant': responce})
                        finil_select = True
                        break
                tool_response={"tool_name":answer_tool['name'],"result":tool_response}

            else:
                base_prompt = "调用函数失败，name参数名错误。"
                tool_response={"error":base_prompt}
            base_prompt=f"""<tool_response>\n{tool_response}\n</tool_response>。 /think"""
            if "error" in tool_response:  #######如果出错了，就不加入训练数据中  且这一轮对话需要删除
                # print(f"{patient_id}执行过程中出现错误")
                history_list.append({'assistant': responce,'error':True})
                continue
            else:
                history_list.append({'assistant': responce})
            

        # 收集最终结果
        result = {
            "patient_id": select_data["patient_id"],
            "answer_code": select_data.get("answer_code", ""),
            "answer_code_name": select_data.get("answer_code_name", ""),
            "answer_path":answer_path,
            "final_node": node_info,
            "final_path_str": currnt_path_info,
            "all_path": all_path,
            "action_list": action_list,
            "message": history_list,
            "validate_list_check":validate_list_check
        }
        return result
    except Exception as e:
        # 获取完整的异常信息，包括文件名、行号、错误类型和具体信息
        import traceback
        
        # 方法1: 使用traceback获取完整堆栈
        error_details = traceback.format_exc()
        
        # 方法2: 获取关键信息
        error_info = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "file": __file__,  # 当前文件
            "line": e.__traceback__.tb_lineno if hasattr(e, '__traceback__') else "unknown"
        }
        
        return {
            "patient_id": select_data.get("patient_id", "unknown"),
            "error": f"{error_info['error_type']}: {error_info['error_message']}",
            "error_details": error_details,  # 完整的堆栈信息
            "file": error_info["file"],
            "line": error_info["line"]
        }

import json
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


TEST_DATA_FILE = "../data/code4detail.json"  # 替换为实际路径
OUTPUT_JSONL_FILE = "./deepseek/deepseek_base_agnt.jsonl"
EXEC_ERROR_JSONL_FILE = "./deepseek_paper_error.jsonl"
if __name__ == '__main__':

  
    with open(TEST_DATA_FILE, 'r', encoding='utf-8') as f:
        patient_data = json.load(f)
    processed_ids = set()
    if os.path.exists(OUTPUT_JSONL_FILE):
        with open(OUTPUT_JSONL_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    processed_ids.add(record.get("patient_id"))

    # 过滤未处理的病人
    to_process = [data for data in patient_data if data["patient_id"] not in processed_ids]

    print(f"总病人数量: {len(patient_data)}，已处理: {len(processed_ids)}，待处理: {len(to_process)}")

    def process_and_save(data):
        """处理单个病人数据并返回结果"""
        result = process_single_patient(data)
        if "error" in result:
            return ("error", result)
        
        final_node = result['final_node']
        model_code = final_node['node_id']
        answer_code = result['answer_code']
        
        if (model_code ==answer_code) and final_node['level'] == 4:
            return ("success", result)
        else:
            return ("data_error", result)

    # 并发处理
    max_workers = min(32, len(to_process))  # 设置最大线程数，可根据需要调整
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_data = {executor.submit(process_and_save, data): data for data in to_process}
        
        # 使用tqdm显示进度
        for future in tqdm(as_completed(future_to_data), total=len(to_process), desc="Processing patients"):
            result = future.result()
            if result is not None:
                result_type, data_result = result
                if result_type == "success":
                    with open(OUTPUT_JSONL_FILE, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(data_result, ensure_ascii=False) + '\n')
                elif result_type == "data_error":
                    with open(OUTPUT_JSONL_FILE, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(data_result, ensure_ascii=False) + '\n')
                else:
                    with open(EXEC_ERROR_JSONL_FILE, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(data_result, ensure_ascii=False) + '\n')

            

    print("✅ 所有病人处理完成（或跳过）并已保存到", OUTPUT_JSONL_FILE)