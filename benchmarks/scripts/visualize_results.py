import argparse
import pandas as pd
from pathlib import Path
from tabulate import tabulate

def generate_table(input_file_path: str, output_file_path: str):
    input_path = Path(input_file_path)
    output_path = Path(output_file_path)

    if not input_path.exists():
        print(f"[!] {input_path} 파일이 없습니다. 먼저 실험을 완료하거나 경로를 확인하세요.")
        return

    # 1. 데이터 로드
    df = pd.read_csv(input_path)

    # 2. 데이터 가독성을 위한 정리
    # 숫자가 없는 칸(N/A)은 '-'로 표시
    df = df.fillna('-')

    # 3. 터미널용 표 생성 (Tabulate 사용)
    # 이미지에서 보신 것처럼 깔끔한 격자(grid) 스타일로 출력합니다.
    table_view = tabulate(df, headers='keys', tablefmt='grid', showindex=False)
    
    # 4. Markdown용 표 생성
    # README 등에 바로 붙여넣을 수 있는 형식입니다.
    markdown_view = tabulate(df, headers='keys', tablefmt='github', showindex=False)

    # 결과 출력
    print("\n" + "="*20 + " [ AutoML Benchmark Summary ] " + "="*20)
    print(table_view)
    print("="*65 + "\n")

    # 5. 출력 파일의 부모 디렉토리가 없다면 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 6. 파일로 저장 (Markdown 형식)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_view)
    
    print(f"[System] 마크다운 요약본이 저장되었습니다: {output_path}")


if __name__ == "__main__":
    # 명령행 인자 파서 설정
    parser = argparse.ArgumentParser(description="AutoML 벤치마크 결과를 표 형태로 시각화하고 Markdown으로 저장합니다.")
    
    # -i 또는 --input 으로 입력 파일 경로를 받음 (필수)
    parser.add_argument("-i", "--input", required=True, help="입력 CSV 파일 경로 (예: results/full_results_v2_set1.csv)")
    
    # -o 또는 --output 으로 출력 파일 경로를 받음 (필수)
    parser.add_argument("-o", "--output", required=True, help="출력 Markdown 파일 경로 (예: results/orig_h2o_baseline_full_analysis.md)")
    
    args = parser.parse_args()
    
    # 함수 실행
    generate_table(args.input, args.output)