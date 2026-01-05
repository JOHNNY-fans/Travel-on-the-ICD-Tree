import os,json
import base64,mimetypes
from ICD_retrival import ICDRetriever as ICDRetriever2
import re,ast

def extract_operations(text,required_fields):
    """
        text: 输入的文本内容
        required_fields: 需要验证的字段列表，默认为["操作名称", "操作时间", "原文依据"]
    """
    if not text:
        return []
    if required_fields is None:
        required_fields = ["操作名称", "操作时间", "原文依据"]
    pattern = r'\{[^{}]*\}'
    matches = re.findall(pattern, text)
    
    dicts = []
    for match in matches:
        try:
            d = ast.literal_eval(match)
            if isinstance(d, dict):
                # 检查必需字段且为非空字符串
                if all(
                    isinstance(d.get(k), str) and len(d.get(k, "").strip()) > 0
                    for k in required_fields
                ):
                    dicts.append(d)
        except (ValueError, SyntaxError, TypeError):
            continue
    
    return dicts
def chat_method2(content, max_tokens=4096):
    api_key=None

    model_name = "qwen3-30b-a3b"
    model_url='XXXXX'
    api_key='XXXXX'
    return generate_gpt4o(prompt=content,model_name=model_name,api_key=api_key,base_url=model_url)
from openai import OpenAI

def generate_gpt4o(prompt,model_name,api_key,base_url,image_paths=None,history=None):
    client = OpenAI(api_key=api_key, base_url=base_url)
    # 设置 API 密钥
    # 创建消息历史记录，包含之前的对话
    messages = []
    if history:
        for h in history:
            messages.append({"role": "user", "content": h["user"]})
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
        model=model_name,
        messages=messages,
        temperature=0.0,
        extra_body={"enable_thinking": False},
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
    process_dict[now_func + "_output"] = item_str_list
    print(file_content.keys())
    return process_dict

def getContentSummary(process_dict:dict, previous_func:str, params:dict):
    error_hanppe = process_dict.get("error_hanppen", False)
    if error_hanppe:
        return process_dict
    file_content=process_dict.get("file_content", "")
    prompt=f"""请根据以下病历内容，推荐患者本次住院期间主要诊断。主要诊断必须：1.诊断命名规范：名称应简洁明确，包含解剖部位、病变性质（如炎症、肿瘤、损伤等）及必要病理/临床特征（如“左肺上叶腺癌”“急性前壁心肌梗死”）。2.有明确的原文依据支撑；3.仅基于本次住院期间记录的病历信息；3.不得引用或依赖非本次住院期间的病历资料（如既往史、门诊记录、外院资料等）作为诊断依据。
主要诊断选择原则：
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
    病历内容：{file_content}
    ```json
        {{
            "推荐诊断": "XXXX",
            "病历依据": "XXXX"
        }}
    ]
    ```
    """
    response=chat_method2(prompt)
    # print(response)
    content_summary=extract_operations(response,["推荐诊断","病历依据"])
    content_summary=content_summary[0:1]
    process_dict['content_summary']=content_summary
    return process_dict

def merge_round_robin_advanced(sub_lists):
    """
    合并策略：
      第 i 轮：
        - 依次取 sub_lists 中每一个子列表的第 i 项（如果存在）
    """
    merged = []
    
    # 如果 sub_lists 为空，直接返回空列表
    if not sub_lists:
        return merged

    # 计算最大轮次（即最长子列表的长度）
    max_round = max(len(sub) for sub in sub_lists)

    for i in range(max_round):
        # 遍历 sub_lists 中的每一个子列表
        for sub in sub_lists:
            if i < len(sub):
                merged.append(sub[i])

    return merged

class ICDRuleManager:
    def __init__(self, level1_path, level2_path, level3_path):
        """
        初始化：加载三个层级的规则文件到内存字典中。
        """
        self.rules_l1 = self._load_jsonl(level1_path, key_field="chapter")
        self.rules_l2 = self._load_jsonl(level2_path, key_field="sub_chapter")
        self.rules_l3 = self._load_jsonl(level3_path, key_field="de_chapter")
        
        # 预生成数字映射表 (0-99)，用于将 "第18章" 转为 "第十八章"
        self.num_map = self._generate_num_map()

    def _generate_num_map(self):
        """生成阿拉伯数字到中文数字的映射 (支持0-99)"""
        chars = '零一二三四五六七八九十'
        mapping = {}
        for i in range(100):
            s_i = str(i)
            if i <= 10:
                mapping[s_i] = chars[i]
            elif i < 20:
                mapping[s_i] = '十' + chars[i % 10]
            else:
                tens = chars[i // 10]
                unit = chars[i % 10]
                if unit == '零':
                    mapping[s_i] = f"{tens}十"
                else:
                    mapping[s_i] = f"{tens}十{unit}"
        return mapping

    def _load_jsonl(self, path, key_field):
        """读取 jsonl 文件并建立索引"""
        data_map = {}
        if not os.path.exists(path):
            print(f"⚠️ 警告: 文件未找到 - {path}")
            return data_map
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        item = json.loads(line)
                        key = item.get(key_field)
                        if key:
                            data_map[key] = item
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"读取文件 {path} 出错: {e}")
        return data_map

    def _get_chapter_key(self, raw_str):
        """
        输入: "第18章“症状...”"
        输出: "第十八章" (匹配 level_1.jsonl 的 key)
        """
        if not raw_str: return ""
        # 提取 "第" 和 "章" 之间的数字
        match = re.search(r"第(\d+)章", raw_str)
        if match:
            num = match.group(1)
            cn_num = self.num_map.get(num, num)
            return f"第{cn_num}章"
        return raw_str.split("“")[0] # 兜底策略

    def _get_code_key(self, raw_str):
        """
        输入: "R16 肝大和脾大..."
        输出: "R16"
        """
        if not raw_str: return ""
        return raw_str.split(" ")[0].strip()

    def get_rules_text(self, items):
        """
        主函数：输入 items 列表，返回格式化的规则文本
        """
        if not items:
            return ""

        # 1. 提取去重后的 Key
        chapters = set()
        categories = set()
        sub_categories = set()

        for item in items:
            if item.get('章节'):
                chapters.add(self._get_chapter_key(item['章节']))
            if item.get('类目'):
                categories.add(self._get_code_key(item['类目']))
            if item.get('亚目'):
                sub_categories.add(self._get_code_key(item['亚目']))

        lines = []

        # 2. 获取第一层级（章节）规则
        if chapters:
            lines.append("【层级一：章节规则】")
            # 排序以保证输出顺序固定
            for chap in sorted(chapters):
                rule_data = self.rules_l1.get(chap)
                if rule_data:
                    name = rule_data.get('name', '').replace('“', '').replace('”', '')
                    lines.append(f"当涉及 {chap} ({name}) 时,需要注意以下规则：")
                    
                    rules = rule_data.get("chapter_rules", [])
                    if not rules:
                        lines.append("  (无特定规则)")
                    for idx, r in enumerate(rules, 1):
                        content = r.get("rule_content", "").strip()
                        lines.append(f"  {idx}. {content}")

        # 3. 获取第二层级（类目）规则
        if categories:
            # 检查是否有匹配的规则，如果所有类目都没规则，就不打印标题
            found_any = False
            temp_lines = []
            for cat in sorted(categories):
                rule_data = self.rules_l2.get(cat)
                if rule_data:
                    found_any = True
                    temp_lines.append(f"当涉及类目 {cat} ({rule_data.get('name', '')}) 时,需要注意以下规则：")
                    rules = rule_data.get("category_rules", [])
                    for idx, r in enumerate(rules, 1):
                    
                        content = r.get("rule_content", "").strip()
                        temp_lines.append(f"  {idx}.  {content}")
            
            if found_any:
                lines.append("\n【层级二：类目规则】")
                lines.extend(temp_lines)

        # 4. 获取第三层级（亚目）规则
        if sub_categories:
            found_any = False
            temp_lines = []
            for sub in sorted(sub_categories):
                rule_data = self.rules_l3.get(sub)
                if rule_data:
                    rules = rule_data.get("subcategory_rules", [])
                    if rules: # 只有当规则列表不为空时才显示
                        found_any = True
                        temp_lines.append(f"当涉及亚目 {sub} ({rule_data.get('name', '')}) 时,需要注意以下规则：")
                        for idx, r in enumerate(rules, 1):
                            content = r.get("rule_content", "").strip()
                            temp_lines.append(f"  {idx}. {content}")
            
            if found_any:
                lines.append("\n【层级三：亚目规则】")
                lines.extend(temp_lines)

        return "\n".join(lines)

def ICD_CALL_DESIESE_with_item(process_dict:dict, previous_func:str, params:dict):
    """
    召回上下位关系
    {"params": {"ICD_source":"ICD10-clinic"},"function_name": "ICD_CallChild"}
    """
    # 预处理
    error_hanppe = process_dict.get("error_hanppen", False)
    if error_hanppe:
        return process_dict
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    ICD_SOURCE_DIR = os.path.join(CURRENT_DIR,'base_info')
    nodes_file = os.path.join(ICD_SOURCE_DIR, 'ICD-10-clinic-processed.jsonl')
    node_dict={}
    with open(nodes_file, 'r', encoding='utf-8') as f:
        for line in f:
            item=json.loads(line.strip())
            node_dict[item['code']]=item
    retriever3 = ICDRetriever2(sources="ICD-10-fix", k=40)
    sub_results_lists = []  
    content_summary=process_dict.get('content_summary',[])
    for item in content_summary:
        sub_list=retriever3.retrieve(item['推荐诊断'])
        sub_results_lists.append(sub_list)
    final_results = merge_round_robin_advanced(sub_results_lists)
    seen_codes = set()
    merged = []
    cnt=0
    for item in final_results:
        if cnt>40:
            break
        if item['code'] not in seen_codes:
            seen_codes.add(item['code'])
            merged.append(item)
            cnt+=1

    new_items=[]
    for item in merged:
        new_item=node_dict[item['code']]
        new_item['章节']=new_item['first_chapter']
        new_item['类目']=new_item['second_chapter']
        new_item['亚目']=new_item['third_chapter']
        new_item.pop('first_chapter')
        new_item.pop('second_chapter')
        new_item.pop('third_chapter')
        new_items.append(new_item)
    # print(new_items)
    process_dict["Call_ICD_List"]=new_items
    return process_dict




def ICD_Jugde_rethink(process_dict:dict, previous_func:str, params:dict):

    now_func = ICD_Jugde_rethink.__name__
    file_content=process_dict.get("file_content","")
    re_think_time=params.get("re_think_time",3)
    # 正式处理
    ICD_source=params.get("ICD_source")
    main_icd=process_dict.get("main_icd")
    main_name=process_dict.get("main_name")
    unique_data=process_dict.get("Call_ICD_List",[])

    manager = ICDRuleManager(
    level1_path="./rule_index/level_1.jsonl",
    level2_path="./rule_index/level_2.jsonl",
    level3_path="./rule_index/level_3.jsonl"
    )
    rule_text = manager.get_rules_text(unique_data)
    icd_prompt=f"""
任务描述：
- 你是一位专业的临床医生兼疾病分类专家，请根据提供的病历内容与基于病案主要诊断获得的候选ICD编码列表，严格依据临床诊疗逻辑与ICD编码规范，从中选择1个最精确、最具体的1个ICD编码。

- 选择原则：
  1. **【最高优先级：规则强制性】** 在进行任何选择前，**必须逐条核对并优先遵循输入的 <rules>（ICD编码规则）**。
     - 若规则指出某情况“不包括”或需“转归/转码”（例如：HIV无症状转Z21、局部感染不归入本章等），**必须严格执行转码**，即使候选列表中有看起来更符合字面描述的其他编码，也必须服从规则。
     - 规则的效力高于“编码越具体越优先”的原则。
  2. **必须优先选择能体现解剖部位、病因、病理类型、临床分期或并发症的子类编码，编码越具体越优先。
  3. **在选择具体编码时，必须严格依据病历原文中的客观临床证据，选定编码后，需逐条回溯并明确标注其在病历中的具体依据，确保编码选择有据可循、可追溯、可验证。若发现病历内容中没有支持依据，不可选择该编码。
  4. **在选择原文依据时，必须严格优先选择本次住院的信息，非本次住院信息仅供参考。
  5. **在未明确排除其他可能性前，禁止使用未特指编码。
  6. **病历中可能存在支持准确编码的关键临床细节，此时应优先依据客观临床证据而非诊断本身进行编码匹配。

输入要素：
- 病历记录内容：<content>{file_content}</content>
- ICD备选列表：{unique_data}
- **ICD强制校验规则**：<rules>{rule_text}</rules>

思考步骤：
1. **【临床事实提取】** 仔细阅读病历内容，主动挖掘并提取支持编码的关键临床信息（部位、病因、病理、分期、症状状态）。**特别注意：提取患者是否存在“无症状携带”、“既往病史”、“并发症”或“特定部位感染”等可能触发ICD特殊规则的状态。**
2. **【规则命中审查】** **（关键步骤）** 将提取的临床信息与 `<rules>` 中的每一条规则进行比对：
   - 检查是否触犯“不包括”条款？
   - 检查是否符合“转归至...”的条件（如HIV无症状转Z21）？
   - 检查是否属于“特殊组合”或“双重编码”要求？
   - **如果命中规则，该规则的指令直接覆盖后续的字面匹配逻辑。**
3. **【编码匹配与排除】** 逐一对比备选编码。若步骤2中命中了强制规则，直接锁定符合规则的编码；若未命中规则，则按照“部位、病因、病理”的匹配度，优先选择病理报告和手术记录支撑的最细分子目。
4. **【最终验证】** 综合以上信息，确定最终编码。再次确认该编码没有违反 `<rules>` 中的任何条款。
输出格式，以标准JSON格式输出：
```
json
{{
    "分析过程":""
    "选择编码":"",
    "选择编码名称":"",
    "选择理由":"请明确说明选择该编码的临床依据：必须从病历原文中直接引用支持性证据并结合ICD编码规则，解释为何该编码最精确反映患者实际病情。禁止使用笼统描述。"
}}
```
"""
    # prompt: str, select_list: list, k: int, max_retries=3
    response=chat_method2(icd_prompt)
    # print(response)
    answer_content=extract_operations(response,["分析过程","选择编码","选择编码名称","选择理由"])
    answer_content=answer_content[0]
    icd_select_final=answer_content['选择编码']
    reason=answer_content['选择理由']
    think=answer_content['分析过程']
    reason_before=reason
    think_before=think
    icd_select_final_info={"code":answer_content['选择编码'],"name":answer_content['选择编码名称']}
    # print(unique_data)
    for node in unique_data:
        # print(node)
        if icd_select_final==node['code']:
            icd_select_final_info=node
            break

    think_message=process_dict.get("think_message",[])


    think_step=f"\n根据病历内容，推荐{icd_select_final_info['code']}_{icd_select_final_info['name']}为主要编码，理由如下\n{think_before}\n{reason_before}\n"
    think_message.append(think_step)
    


    process_dict["icd_select_final"] = icd_select_final_info
    process_dict['think_message']=think_message
    process_dict['think']=think
    process_dict['reason']=reason
    return process_dict



def ICD_Result(process_dict:dict, error:str=None, no_use:bool=False) -> dict:
    '''
    params: process_dict 过程结果字典
    params: rule_dict 规则的参数字典
    params: emr_dict 电子病历内容字典
    params: error 意外情况下，传入错误信息
    params: no_use 规则不适用标志,默认False,如果为True则表示该规则不适用于当前病历

    输出规则执行结果的字典
    flag: 几种值代表的含义
        -1: 处理过程中发生错误
        0: 不符合要求
        1: 符合要求
        2: 规则不适用 
    '''
    result = {}
    if error:
        result["flag"] = -1
        result["conculsion"] = "处理过程中发生错误"
        result["explanation"] = error
        return result
    if no_use: # 规则不适用
        result["flag"] = 2
        result["conculsion"] = "规则不适用"
        result["explanation"] = "该规则不适用于当前病历,病历无需执行该规则的质控审查,不计算扣分"
        return result
    
    icd_select_final=process_dict.get("icd_select_final",{})
    if 'code' in icd_select_final:
        icd_select_final_code=icd_select_final['code']
    else:
        icd_select_final_code="暂无推荐"
    if 'name' in icd_select_final:
        icd_select_final_name=icd_select_final['name']
    else:
        icd_select_final_name="暂无推荐"
    main_icd=process_dict.get("main_icd")###重新选择过的编码
    main_name=process_dict.get("main_name")
    think=process_dict.get("think","")
    reason=process_dict.get("reason","")
    
    file_content=process_dict.get("file_content","")
    think_message=process_dict.get("think_message","")
    
    result['suggest_icd'] = icd_select_final_code
    result['suggest_name']=icd_select_final_name
    result["explanation"]=think+"\n"+reason
    result['icd_select_final_before']=process_dict.get('icd_select_final_before',{})
    result['Call_ICD_List']=process_dict.get('Call_ICD_List',[])
    result['Call_ICD_List2']=process_dict.get('Call_ICD_List2',[])
    result['DiseaseDesc']=process_dict.get('content_summary','')
    # disease_desc=process_dict['DiseaseDesc']
    return result