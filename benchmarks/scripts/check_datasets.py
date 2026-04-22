"""
OpenML Dataset Validator & Report Generator
- 모든 데이터셋의 존재 여부를 전수 조사합니다.
- 검색 결과와 추천 명칭을 Markdown 보고서로 자동 생성합니다.
- 연구 기록의 무결성을 위해 'results' 폴더에 저장됩니다.
"""

import openml
import pandas as pd
from pathlib import Path
from datetime import datetime

# 1. 검증 대상 리스트
FULL_DATASETS = {
    "auc": ["australian", "blood-transfusion-service-center", "credit-g", "kc1", "jasmine", "kr-vs-kp", "sylvine", "phoneme", "christine", "guillermo", "riccardo", "amazon_employee_access", "nomao", "bank-marketing", "adult", "kddcup09_appetency", "apsfailure", "numerai28.6", "higgs", "miniboone"],
    "logloss": ["car", "cnae-9", "connect-4", "dilbert", "fabert", "fashion-mnist", "helena", "jannis", "jungle_chess_2pcs_raw_endgame_complete", "mfeat-factors", "robert", "segment", "shuttle", "vehicle", "volkert"]
}

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
RESULT_DIR = BASE_DIR / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = RESULT_DIR / "dataset_check_report.md"

def search_similar(keyword):
    """유사 명칭 검색 후 마크다운 표 형식으로 반환"""
    try:
        df = openml.datasets.list_datasets(data_name=keyword, output_format='dataframe')
        if df is not None and not df.empty:
            return df[['did', 'name', 'version', 'NumberOfInstances', 'NumberOfFeatures']].head(5).to_markdown(index=False)
    except:
        return None
    return None

def run_validation():
    report_content = []
    report_content.append(f"# 📊 OpenML Dataset Validation Report\n")
    report_content.append(f"- **생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_content.append(f"- **검증 대상**: 총 {sum(len(v) for v in FULL_DATASETS.values())}개 데이터셋\n")
    report_content.append("---")

    summary_table = []
    detail_logs = []

    for m_type, ds_list in FULL_DATASETS.items():
        detail_logs.append(f"\n## 🔍 Metric: {m_type.upper()} Detail Logs")
        
        for ds_name in ds_list:
            print(f"Checking: {ds_name}...")
            try:
                # 데이터셋 존재 여부 확인
                openml.datasets.get_dataset(ds_name, download_data=False)
                summary_table.append({"Dataset": ds_name, "Metric": m_type, "Status": "✅ OK", "Action": "-"})
                detail_logs.append(f"### ✅ {ds_name}\n- 상태: 정상 확인됨")
            
            except Exception:
                # 검색 키워드 추출 (언더바 제거 등)
                search_key = ds_name.split('_')[0] if '_' in ds_name else ds_name
                summary_table.append({"Dataset": ds_name, "Metric": m_type, "Status": "❌ MISSING", "Action": f"Search '{search_key}'"})
                
                detail_logs.append(f"### ❌ {ds_name}\n- **상태**: 찾을 수 없음\n- **검색 시도 키워드**: `{search_key}`")
                
                suggestions = search_similar(search_key)
                if suggestions:
                    detail_logs.append(f"\n#### 💡 Suggested Names from OpenML:\n\n{suggestions}\n")
                else:
                    detail_logs.append("\n- **알림**: 유사한 이름의 데이터셋을 찾지 못했습니다. 수동 확인이 필요합니다.\n")

    # 요약 표 작성
    report_content.append("\n## 📌 Summary Status Table\n")
    report_content.append(pd.DataFrame(summary_table).to_markdown(index=False))
    report_content.append("\n" + "---")
    
    # 상세 로그 합치기
    report_content.extend(detail_logs)

    # 파일 저장
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))
    
    print(f"\n[완료] 보고서가 생성되었습니다: {REPORT_FILE}")

if __name__ == "__main__":
    run_validation()