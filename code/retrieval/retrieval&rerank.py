import retrieval&rerank_tools as tool_icd
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# === 配置路径 ===


test_file ='./data/code4detail.json'
out_file = "./deepseek/deepseek_recall.jsonl"

file_lock = threading.Lock()

def load_existing_patient_ids(output_file):
    """从 jsonl 文件加载已处理的 patient_id"""
    if not os.path.exists(output_file):
        return set()
    existing = set()
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                existing.add(data['patient_id'])
            except Exception as e:
                print(f"⚠️ 解析已有行失败: {e}")
    return existing

def write_result_to_jsonl(result, output_file):
    """线程安全写入单条结果"""
    with file_lock:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

def process_single_record(data):
    """
    使用 step_by_step_tool 逐函数处理单条记录
    返回 output_data 或 None（出错时）
    """
    patient_id = data['patient_id']
    try:
        process_dict = {"emr_dict": data["emr_dict"]}

        # 严格按照顺序调用工具函数
        process_dict = tool_icd.ICD_GetContent_v2(
            process_dict, previous_func="getMainCode",
            params={"field_name": [
                ["入院记录", ""],
                ["检查报告", ""],
                ["手术记录", ""],
                ["出院记录", "文档内容"],
                ["病理报告", ""],
            ]}
        )

        process_dict = tool_icd.getContentSummary(process_dict, previous_func="", params={})
        process_dict = tool_icd.ICD_CALL_DESIESE_with_item(process_dict, previous_func="", params={})
        process_dict = tool_icd.ICD_Jugde_rethink(process_dict, previous_func="", params={})


        result = tool_icd.ICD_Result(process_dict)

        # 提取关键字段

        suggest_icd = result.get("suggest_icd")
        suggest_name = result.get("suggest_name")


        output_data = {
            'patient_id': patient_id,
            'suggest_icd':suggest_icd,
            'suggest_name':suggest_name,
            'answer_code': data.get('answer_code', ''),
            'answer_code_name': data.get('answer_code_name', ''),
            "answer_path":data["answer_path"],
            'all_results': result,
        }

        return output_data

    except Exception as e:
        
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
        print(f"⚠️ 处理 {patient_id} 时出错: {str(error_details)}")
        
        return {
            "patient_id": data.get("patient_id", "unknown"),
            "error": f"{error_info['error_type']}: {error_info['error_message']}",
            "error_details": error_details,  # 完整的堆栈信息
            "file": error_info["file"],
            "line": error_info["line"]
        }

def main():
    # 加载数据
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    existing_ids = load_existing_patient_ids(out_file)
    print(f"已加载 {len(existing_ids)} 个已处理的 patient_id")

    # 过滤未处理记录
    filtered_data = [d for d in test_data if d['patient_id'] not in existing_ids]
    print(f"共 {len(test_data)} 条，剩余 {len(filtered_data)} 条待处理")

    if not filtered_data:
        print("✅ 无新记录需要处理")
        return

    success_count = 0
    max_workers = 8  # 可根据 GPU/CPU 资源调整

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_record, data) for data in filtered_data]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Processing Records",
            unit="record",
            ncols=100,
            colour="#2ca02c"
        ):
            output = future.result()
            if 'error' not in output:
                write_result_to_jsonl(output, out_file)
                success_count += 1
            else:
                write_result_to_jsonl(output, 'XXX.jsonl')

    print(f"✅ 并发处理完成！成功: {success_count} 条，结果追加至: {out_file}")

if __name__ == '__main__':
    main()