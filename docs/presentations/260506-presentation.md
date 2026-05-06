# End-to-End GPU-based AutoML: 핵심 기능과 설계 전략
**Subtitle**: GUAM (GPU-based Auto-ML for Robust Large-Scale Computation) 프로젝트를 중심으로
**Date**: 2026-05-06

---

## 🚀 Introduction: 왜 GPU-based AutoML인가?
기존의 CPU 기반 AutoML은 대규모 데이터셋과 복잡한 앙상블 과정에서 병목 현상(Bottleneck)에 직면.  
이를 해결하기 위해 RAPIDS 생태계(cuDF, cuML)를 활용한 GPU 가속이 필수적이지만,  
**8GB~16GB 수준의 제한된 VRAM(비디오 메모리) 한계**를 극복하지 못하면 오히려 잦은 OOM(Out Of Memory) 크래시로 인해 시스템의 신뢰성이 크게 저하.

따라서, 성공적이고 견고한(Robust) End-to-End GPU AutoML을 구축하기 위한 **최우선 핵심 기능 3가지**를 제안하고자 함.

---

## 🥇 Top 1. 지능형 GPU 메모리 관리 및 페이징 (Intelligent VRAM Management & Paging)
한정된 VRAM을 효율적으로 통제하여 시스템의 '생존성(Robustness)'을 보장하는 것.

*   **RMM (RAPIDS Memory Manager) 풀 최적화**: 
    *   동적 메모리 할당으로 인한 파편화(Fragmentation)를 방지하기 위해 초기 메모리 풀(Pool)을 고정하고 적응형으로 관리.
*   **Paged Memory & OOM 회피 메커니즘**:
    *   가용 VRAM을 실시간으로 추적하여, 모델 학습에 필요한 메모리가 부족할 경우 해당 모델을 안전하게 Skip하거나 CPU RAM으로 데이터를 임시 페이징(Swapping)하는 아키텍처가 필수적.
*   **프로세스 격리 (Process Isolation)**:
    *   Python의 GC(Garbage Collector)에만 의존하지 않고,  
    각 벤치마크/학습 단위를 독립된 서브프로세스로 분리하여 종료 시 OS 레벨에서 메모리를 100% 강제 회수(Deep Clean)하는 딥 클리닝 프로토콜이 도입 필요.

---

## 🥈 Top 2. CPU 간섭 없는 제로 카피 데이터 파이프라인 (Zero-Copy GPU Data Pipeline)
데이터 로드부터 전처리, 학습, 평가까지의 모든 과정이 GPU 내에서만 이루져야함(End-to-End).

*   **GPU-Native 데이터 로더 및 전처리**:
    *   `cuDF`를 활용한 병렬 데이터 I/O 적용.
    *   범주형 데이터 및 결측치를 GPU 메모리 상에서 직접 처리하는 Data Hardening(데이터 경화) 기술  
        (예: `CuPy` 객체 타입 충돌을 막기 위한 강제 수치화 및 정규화).
*   **Zero-Copy 전달**:
    *   Data Layer(전처리)에서 Algorithm Pool(RF, GLM, XGBoost)로 데이터가 넘어갈 때,  
        호스트 메모리(CPU RAM)로의 데이터 복사 없이 디바이스 포인터만 전달하여 병목을 원천 차단.

---

## 🥉 Top 3. 대규모 확장을 위한 분산 컴퓨팅 및 스케줄링 (Distributed Computation & Orchestration)
단일 GPU의 물리적 한계를 넘어 'Large-Scale Computation'을 실현하기 위한 오케스트레이션 기능.

*   **Dask-CUDA 기반의 Multi-GPU 확장성**:
    *   데이터 크기가 단일 VRAM을 초과할 경우(Out-of-core), Dask-cuDF를 통해 여러 GPU 혹은 워커(Worker)에 데이터를 분산시켜 처리하는 기능.
*   **Time-Budget 기반의 지능형 스케줄러**:
    *   사용자가 부여한 시간(예: 1분, 3분, 5분) 내에서 최적의 모델 조합을 찾아내기 위해, 무거운 모델과 가벼운 모델의 학습 우선순위를 동적으로 조정하는 스케줄링.
*   **비동기식 하이퍼파라미터 튜닝**:
    *   탐색(Search) 공간을 여러 GPU에 분산시켜 앙상블(Stacked Ensembles)을 위한 다양성(Diversity)을 빠른 시간 내에 확보.

---

## 🎯 Conclusion
완벽한 **End-to-End GPU-based AutoML**은 단순히 "빠른 알고리즘"의 집합이 아님.  
데이터가 GPU에 올라가는 순간부터 결과가 도출될 때까지  
**1) 메모리 한계를 지능적으로 방어하고, 2) CPU 개입을 0으로 만들며, 3) 스케일 아웃을 지원하는 유기적인 시스템 인프라**를 구축하는 것이 핵심.