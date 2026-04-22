"""
H2O AutoML Baseline Research - Benchmark Suite 
- 시간별 성능(1, 3, 5분)을 가로행으로 통합 관리합니다.
- H2O 클러스터를 매 실험마다 재시작하여 메모리 효율을 극대화합니다.
- 실험 중단 시 '데이터셋의 특정 시간대'부터 정확히 이어서 시작합니다.
"""

import os
import socket
import subprocess
import time
import argparse
import logging
import psutil  # 시스템 RAM 모니터링용
import pandas as pd
from pathlib import Path
import h2o
import openml
from h2o.automl import H2OAutoML

# ---------------------------------------------------------
# 1. 인자 및 경로 설정
# ---------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--mem_size", type=str, default="16G", help="H2O JVM에 할당할 메모리")
parser.add_argument("--max_models", type=int, default=None, help="데이터셋당 최대 모델 수 제한 (복원됨)")
parser.add_argument("--exclude_heavy", action="store_true", help="무거운 알고리즘(DL/Ensemble) 제외")
args = parser.parse_args()

# RESULT_DIR를 results 폴더로 바로 지정
BASE_DIR = Path(__file__).resolve().parent.parent
RESULT_DIR = BASE_DIR / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# 캡처하신 이미지 포맷을 위한 시간 리스트
TIME_STEPS = [1, 3, 5] 

# 실험 대상 35개 데이터셋 전역 정의
FULL_DATASETS = {
    "auc": ["australian", "blood-transfusion-service-center", "credit-g", "kc1", "jasmine", "kr-vs-kp", "sylvine", "phoneme", "christine", "guillermo", "riccardo", "amazon_employee_access", "nomao", "bank-marketing", "adult", "kddcup09_appetency", "apsfailure", "numerai28.6", "higgs", "miniboone"],
    "logloss": ["car", "cnae-9", "connect-4", "dilbert", "fabert", "fashion-mnist", "helena", "jannis", "jungle_chess_2pcs_raw_endgame_complete", "mfeat-factors", "robert", "segment", "shuttle", "vehicle", "volkert"]
}

# ---------------------------------------------------------
# 2. 유틸리티 함수 (시스템 관리 및 경로 결정)
# ---------------------------------------------------------
def get_memory_info():
    """현재 시스템의 실시간 RAM 점유율을 기록합니다."""
    mem = psutil.virtual_memory()
    return f"RAM: {mem.percent}% ({mem.used / (1024**3):.1f}GB 사용 중)"

def get_dynamic_paths(verified_list):
    """
    모든 데이터셋의 모든 시간대(1, 3, 5분)가 완료되었을 때만 다음 세트로 넘어갑니다.
    중간에 끊기면 해당 세트 파일에 이어서 기록합니다.
    """
    all_targets = verified_list["auc"] + verified_list["logloss"]
    set_idx = 1
    while True:
        csv_path = RESULT_DIR / f"full_results_v4_set{set_idx}.csv"
        log_path = RESULT_DIR / f"telemetry_v4_set{set_idx}.log"
        
        if not csv_path.exists(): 
            return csv_path, log_path
        
        df = pd.read_csv(csv_path)
        # 데이터셋 존재 여부와 마지막 시간 컬럼(5min) 기입 여부를 동시에 체크
        if all(ds in df['dataset'].tolist() for ds in all_targets) and not df[f"{TIME_STEPS[-1]}min"].isnull().any():
            set_idx += 1
            continue
        return csv_path, log_path

def start_h2o():
    """깨끗한 환경을 위해 H2O 서버를 물리적으로 재시작합니다."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80)); wsl_ip = s.getsockname()[0]; s.close()
    import h2o.backend
    jar_path = os.path.join(os.path.dirname(h2o.backend.__file__), "bin", "h2o.jar")
    # 백그라운드 프로세스로 실행
    cmd = ["java", f"-Xmx{args.mem_size}", "-jar", jar_path, "-ip", wsl_ip, "-port", "54321"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(10) # 부팅 대기
    h2o.init(url=f"http://{wsl_ip}:54321")

# ---------------------------------------------------------
# 3. 메인 실험 루프
# ---------------------------------------------------------
def run():
    # 사전 검증 (OpenML 서버 확인)
    verified = {"auc": [], "logloss": []}
    for m_type, ds_list in FULL_DATASETS.items():
        for ds in ds_list:
            try: 
                openml.datasets.get_dataset(ds, download_data=False)
                verified[m_type].append(ds)
            except: 
                print(f"[Skip] {ds}를 찾을 수 없습니다.")
            
    output_file, log_file = get_dynamic_paths(verified)
    
    # 로깅 설정 초기화 및 결정된 파일명 적용
    for h in logging.root.handlers[:]: logging.root.removeHandler(h)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
                        handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
    
    # 결과 데이터프레임 로드 혹은 신규 생성 (캡처하신 구조와 동일하게 컬럼 생성)
    if output_file.exists():
        df_results = pd.read_csv(output_file)
    else:
        df_results = pd.DataFrame(columns=["dataset", "metric"] + [f"{t}min" for t in TIME_STEPS])

    # 지표별, 데이터셋별 루프
    for m_type in ["auc", "logloss"]:
        metric = "AUC" if m_type == "auc" else "logloss"
        for ds_name in verified[m_type]:
            # 행(Row) 존재 확인 및 전체 완료 여부 체크
            if ds_name in df_results['dataset'].values:
                row_idx = df_results.index[df_results['dataset'] == ds_name][0]
                # 이미 1, 3, 5분이 다 차있다면 다음 데이터셋으로
                if not df_results.iloc[row_idx][[f"{t}min" for t in TIME_STEPS]].isnull().any():
                    continue
            else:
                # 새로운 데이터셋 발견 시 행 추가
                new_row = {"dataset": ds_name, "metric": "roc-auc" if m_type == "auc" else "-logloss"}
                df_results = pd.concat([df_results, pd.DataFrame([new_row])], ignore_index=True)

            # [시간별 루프] 1분 -> 3분 -> 5분 순차 진행
            for t in TIME_STEPS:
                col_name = f"{t}min"
                row_idx = df_results.index[df_results['dataset'] == ds_name][0]
                
                # 특정 시간대의 결과가 이미 있다면 건너뛰기 
                if pd.notnull(df_results.at[row_idx, col_name]): continue

                start_h2o()
                try:
                    logging.info(f"==> [{ds_name}] {t}min 실험 가동 | {get_memory_info()}")
                    dataset = openml.datasets.get_dataset(ds_name)
                    X, y, _, _ = dataset.get_data(target=dataset.default_target_attribute)
                    hf = h2o.H2OFrame(pd.concat([X, y], axis=1))
                    hf[dataset.default_target_attribute] = hf[dataset.default_target_attribute].asfactor()
                    train, test = hf.split_frame(ratios=[0.8], seed=42)

                    # AutoML 파라미터 적용 (max_models 포함)
                    aml = H2OAutoML(max_runtime_secs=t * 60, 
                                    max_models=args.max_models, 
                                    seed=42, 
                                    sort_metric=metric,
                                    exclude_algos=["DeepLearning", "StackedEnsemble"] if args.exclude_heavy else [])
                    aml.train(y=dataset.default_target_attribute, training_frame=train)
                    
                    # 결과 추출 및 소수점 4자리 반올림
                    score = "N/A"
                    if aml.leader:
                        perf = aml.leader.model_performance(test)
                        val = perf.auc() if m_type == "auc" else -perf.logloss()
                        score = round(val, 4)
                    
                    # 특정 칸(Cell)에 결과 기록 후 즉시 저장
                    df_results.at[row_idx, col_name] = score
                    df_results.to_csv(output_file, index=False)
                    logging.info(f"==> 기록 완료: {ds_name} ({t}min) = {score}")
                except Exception as e:
                    logging.error(f"!! 에러 발생 {ds_name} ({t}min): {e}")
                    df_results.at[row_idx, col_name] = "Error"
                finally:
                    # 다음 시간을 위해 서버 완전 종료
                    h2o.cluster().shutdown()
                    time.sleep(5)

if __name__ == "__main__":
    run()