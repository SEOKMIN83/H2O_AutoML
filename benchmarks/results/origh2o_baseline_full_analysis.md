# Original H2O AutoML Baseline Performance Report (35 OpenML Datasets)

## 1. Experiment Overview
본 실험은 Paged AutoML의 성능 평가를 위한 기준점(Baseline)을 확립하기 위해 수행되었습니다. 기존 H2O AutoML 아키텍처를 사용하여 35개의 OpenML 벤치마크 데이터셋에 대해 1분, 3분, 5분의 제한 시간(Time Budget)을 부여하고 성능 변화 추이를 분석했습니다.

- **Target Task**: 이진 분류(Binary Classification) 및 다중 분류(Multiclass Classification)
- **Metrics**: ROC-AUC (20개 데이터셋), Logloss (15개 데이터셋)
- **Time Budgets**: 1 minute, 3 minutes, 5 minutes

---

## 2. Key Findings & Presentation Insights

### Insight 1: 탐색 시간 확보에 따른 비선형적 성능 도약 (The "Time Budget" Threshold)
제한된 시간 내에 강력한 앙상블 모델을 구축하는 AutoML의 특성상, 특정 데이터셋에서는 1분에서 3분으로 넘어갈 때 압도적인 성능 향상이 관찰되었습니다.
- **주요 사례**: `blood-transfusion-service-center` 데이터셋의 경우 1분 탐색 시 **0.526**에 불과했던 AUC가 3분 탐색 시 **0.7892**로 급상승하며, 5분에는 **0.8014**로 안정화되었습니다.
- **발표 포인트**: 복잡한 피처 공간을 가진 데이터셋일수록 Base Model 학습과 Meta-Learner 튜닝을 위한 최소한의 물리적 시간(3분 이상)이 확보되어야 함을 증명합니다.

### Insight 2: 조기 수렴(Early Convergence)과 시간의 역설
모든 데이터셋이 더 많은 시간을 부여받는다고 해서 성능이 무한정 오르지는 않습니다.
- **주요 사례**: 
  - `kr-vs-kp`, `riccardo`, `nomao` 등의 데이터셋은 1분 만에 이미 **0.99 이상**의 극단적인 수렴(Convergence)을 달성했습니다.
  - 흥미롭게도 `australian` 데이터셋은 1분(0.9502)에서 3분(0.9491), 5분(0.9397)으로 갈수록 오히려 성능이 미세하게 하락하거나 정체되는 현상을 보였습니다.
- **발표 포인트**: 시간이 늘어남에 따라 과적합(Overfitting)된 모델이 앙상블에 포함되거나, 불필요한 모델 탐색으로 인해 최적의 가중치를 잃을 수 있습니다. 이는 제한된 메모리(VRAM) 내에서 **효율적인 모델 프루닝(Pruning)과 메모리 페이징(Paging)**이 얼마나 중요한지 역설하는 강력한 증거가 됩니다.

### Insight 3: 안정적인 하한선 방어 능력
H2O AutoML 시스템은 시간이 매우 촉박한 1분(60초) 예산에서도 대다수의 데이터셋에 대해 준수한 성능(AUC 0.75~0.85 이상)을 방어해 냈습니다 (`credit-g`: 0.7575, `kc1`: 0.827 등).
- **발표 포인트**: 기존 시스템도 충분히 훌륭합니다. 하지만 우리의 목표는 이 **훌륭한 성능(Accuracy)을 100% 유지하면서, 8GB VRAM이라는 극한의 환경에서도 OOM(Out of Memory) 없이 35개 데이터셋을 모두 완주할 수 있는 'Paged AutoML' 시스템을 증명**하는 것입니다.

---

## 3. Next Steps: The Paged AutoML Challenge
본 Baseline 결과를 바탕으로, 새롭게 설계된 **Paged AutoML**이 다음 두 가지 가설을 입증할 것입니다.

1. **Accuracy Retention**: Paged 메모리 관리 오버헤드가 발생하더라도, Original H2O AutoML이 기록한 본 성능 지표(ROC-AUC, Logloss)와 동등하거나 그 이상의 성능을 달성할 수 있는가?
2. **Resource Efficiency**: 5분 이상의 긴 Time Budget에서 필연적으로 발생하는 VRAM 파편화와 OOM 크래시를 완벽하게 회피할 수 있는가?