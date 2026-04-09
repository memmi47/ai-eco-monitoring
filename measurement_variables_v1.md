# AI Eco Monitor - 세그먼트별 측정변수 설계서

## 설계 원칙

1. 각 중분류(Category)는 메모리 반도체 수요를 관측하는 독립적 센서군으로 기능한다
2. 측정변수는 "관측 가능한 이벤트에서 추출 가능한 것"으로 한정한다 (추상적 지표 배제)
3. 각 측정변수에는 반드시 **메모리 전이 경로(Transmission Path)**를 명시한다
4. 하나의 중분류에 복수의 측정변수를 허용하되, 각각이 서로 다른 메모리 수요 경로를 대표해야 한다

---

## A. Physical Infrastructure

### A1. Energy & Power [41개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI DC 전용 전력 프로젝트 규모 (MW) | Nuclear/SMR, Utility, Power/Grid | Oklo-MS 500MW PPA 체결, NuScale SMR 가동 승인 | 전력 확보 -> DC 착공 가능 -> 서버 발주 -> HBM/DRAM 수요 (18-24개월) |
| 전력 인프라 투자 금액 ($ 단위) | ESS, Renewable, Fuel Cell | TerraPower $4B 투자 확정, Bloom Energy DC 연료전지 수주 | 전력 투자 확대 -> DC 가용 용량 증가 -> 서버 밀도 확대 가능성 (장기) |
| 전력 공급 병목 시그널 | Power/Gen, Grid, Utility | 전력망 연결 대기 18개월, 일부 DC 프로젝트 지연 발표 | 전력 병목 -> DC 확장 지연 -> 메모리 수요 이연 (단기 하방) |

### A2. Thermal Management [34개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 액냉(Liquid Cooling) 수주/출하 추이 | Liquid Cool, Thermal/Rack | Vertiv 액냉 수주 전년비 +200%, CoolIT DC 출하 급증 | 액냉 수주 -> 고밀도 GPU 서버 배치 확대 -> HBM 수요 가속 (6-12개월) |
| Rack 전력밀도 변화 (kW/Rack) | Thermal/Mgmt, Thermal/Comp | 60kW -> 120kW 랙 표준화 논의, ASHRAE 가이드라인 변경 | 랙 밀도 상승 -> 서버당 GPU/메모리 탑재량 증가 -> HBM/DRAM 수요 상승 |

### A3. DC Design & EPC [27개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 신규 DC 착공/설계 건수 및 규모 | EPC/Construction, EPC/Design | Fluence 200MW DC 설계 수주, IEC 신규 DC 프로젝트 착공 | 착공 -> 12-18개월 후 서버 입주 -> 메모리 대량 발주 |
| DC 건설 비용 변화 ($/MW) | EPC/Cost, EPC/Electric | DC 건설 단가 $10M/MW -> $12M/MW 상승, 전기공사 비용 급등 | 건설비 상승 -> DC 확장 ROI 하락 -> 투자 지연 가능 (하방 리스크) |

---

## B. Semiconductor & Components

### B1. Semiconductor Equipment & EDA [21개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| HBM/첨단 패키징 관련 장비 수주 | Bonding, Etch/Depo, Test/Handler | AMAT HBM TSV 장비 수주 +50%, Advantest HBM 테스터 출하 | 장비 수주 -> 메모리 업체 증설 의지 확인 -> HBM 공급 증가 (6-9개월) |
| EUV/첨단 공정 장비 출하 | Litho Equipment, Deposition | ASML High-NA 출하, Lam Research GAA 장비 매출 증가 | 첨단 장비 -> 로직칩 미세화 -> 차세대 GPU 양산 -> 차세대 HBM 필요 |
| EDA/IP 라이선스 트렌드 | EDA/IP, IP/Architecture | Synopsys AI 칩 설계 계약 +30%, Cadence 3nm IP 매출 급증 | EDA 활용 -> 신규 ASIC/GPU 설계 착수 -> 2-3년 후 해당 칩용 메모리 수요 |

### B2. Compute & Silicon [42개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| GPU/AI 가속기 신제품 스펙 변화 | GPU, GPU/CPU, WSE, LPU | GB300: HBM4 288GB, AMD MI400: HBM4 출시 | 차세대 GPU 스펙 -> HBM 세대 전환 및 용량 증가 -> HBM 수요 직결 |
| Custom ASIC 설계 프로젝트 수 | Custom ASIC, Custom SoC, ASIC/Net | Broadcom AI ASIC 고객 4 -> 8, Marvell 맞춤칩 수주 | ASIC 증가 -> GPU 대체/보완 -> HBM/LPDDR 등 다양한 메모리 인터페이스 수요 분산 |
| Edge/NPU 칩 출시 및 스펙 | Edge NPU, NPU, Mobile AP, Edge AI | Qualcomm NPU TOPS +2x, MediaTek Dimensity LPDDR5X 지원 | Edge NPU 성능 향상 -> On-device AI 확산 -> 모바일 LPDDR/UFS 탑재량 증가 |
| 신규 아키텍처 동향 | Neuromorphic, Photonic, Analog AI, In-Memory, CXL | CXL 3.0 컨소시엄 확대, Lightmatter 광 인터커넥트 양산 | 신규 아키텍처 -> 메모리 인터페이스 변화 (CXL 확산 시 풀링 수요), 장기 패러다임 시프트 |

### B3. Memory & Storage [27개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| HBM 공급 동향 및 경쟁 구도 | Memory/HBM, Memory/Fabric | SK Hynix HBM4 양산 시점, Micron HBM 점유율 변화 | 직접 지표: 자사 및 경쟁사 공급 능력이 곧 시장 구조 결정 |
| CXL/메모리 패브릭 채택 | CXL/PCIe, Memory/Compute, Memory I/F | CXL 컨소시엄 신규 회원, MemVerge CXL 풀링 상용화 | CXL 확산 -> 메모리 풀링/디사그리게이션 -> 서버당 DRAM 총량 변화 (상/하 양면) |
| 스토리지 아키텍처 변화 | Storage/SSD, SSD Ctrl, Storage/RAG, HPC Storage | KV Cache용 eSSD 채택 사례, VAST Data AI 스토리지 수주 | AI 워크로드용 스토리지 -> NAND 수요 신규 축 (KV Cache offload, 체크포인팅) |

### B4. Networking & Interconnect [19개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 네트워크 대역폭 세대 전환 | InfiniBand, AI Ethernet, Ethernet Switch | NVIDIA ConnectX-8 출시, Broadcom 800G 이더넷 스위치 | 네트워크 업그레이드 -> GPU 클러스터 규모 확대 가능 -> 클러스터당 HBM 총량 증가 |
| 광 인터커넥트 상용화 진행 | Optical Trans, Optical I/O, Optics/Transport | Ayar Labs 광 I/O 양산, Coherent 800G 모듈 출하 급증 | 광 대역폭 -> 칩간 병목 해소 -> 더 큰 학습 클러스터 -> 메모리 수요 스케일업 |

### B5. Server & System Integration [14개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 서버 출하량/수주 전망 | Server/GPU, Server/ODM, Server/OEM | Dell AI 서버 수주잔고 +$4B, Super Micro GPU 서버 매출 +80% | AI 서버 출하 = 메모리 수요의 가장 직접적 선행 지표 (3-6개월) |
| 서버 아키텍처 구성 변화 | AI System, HPC/AI System, HCI | GB200 NVL72 랙 단위 배치, 단일 서버 메모리 용량 1TB+ 증가 | 서버 구성 변화 -> 서버당 HBM/DRAM/SSD 탑재량 변화 -> 단가x수량 추정 가능 |

### B6. Advanced Packaging & Components [15개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 첨단 패키징 Capa 증설 | Foundry/Pkg, OSAT, Substrate | TSMC CoWoS Capa +100%, ASE HBM 패키징 증설 | 패키징 Capa = HBM 병목. 증설 -> HBM 출하 가능량 증가 |
| ABF/기판 수급 동향 | ABF Film, PCB/Substrate, Substrate | Ajinomoto ABF 증산 투자, Ibiden AI 기판 매출 비중 +15%p | 기판 수급 -> 첨단 패키지 생산 제약/완화 -> HBM 공급 영향 |

---

## C. Operations & Cloud

### C1. DC Operator & Colocation [26개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| DC 가용 용량 확장률 (MW 기준) | Operator/Colo, Infra Deploy | Equinix 300MW 신규 확장, Digital Realty AI 전용존 증설 | DC 용량 확대 -> 서버 입주 가능 공간 확보 -> 메모리 탑재 서버 배치 (6-12개월) |
| 입주율/가동률 변화 | Operator/Colo | Colo 입주율 95%+, 대기 리스트 증가 | 높은 입주율 -> 증설 압력 -> 서버 추가 발주 -> 메모리 수요 |

### C2. Hyperscaler & GPU Cloud [31개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| Hyperscaler Capex 규모 및 가이던스 변화 | Hyperscaler (MS, Google, Amazon, Meta) | MS FY26 capex $80B->$95B 상향, Meta AI infra $40B+ | Capex -> 서버/GPU 발주 -> HBM+DRAM+NAND 수요 (6-9개월). 가장 강력한 선행 지표 |
| Neocloud/GPU Cloud 자금 조달 및 확장 | Neocloud, GPU Cloud, DePIN/GPU | CoreWeave $12B 조달, Lambda $500M 확장, Crusoe 신규 DC | Neocloud 확장 -> Hyperscaler 외 추가 GPU 서버 수요 -> 메모리 수요 증분 |
| 추론 서비스 인프라 투자 | Inference ISP, Serverless | Groq 추론 전용 DC 착공, Together AI 추론 서버 10x 증설 | 추론 인프라 -> 서버 DRAM 용량 중심 수요 + KV Cache NAND 수요 (학습 대비 다른 메모리 믹스) |

---

## D. AI Platform & Data Infra

### D1. Data Infrastructure & MLOps [12개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 데이터 파이프라인 처리량 증가율 | Data Cloud, Data Streaming, Data Integration | Databricks 처리량 전년비 +150%, Confluent AI 스트리밍 매출 급증 | 데이터 처리량 -> 학습/추론 워크로드 증가의 간접 지표 -> 서버 증설 수요 |
| ML 모델 배포 빈도 | Model Deploy, Model Serving, Model Hub | HuggingFace 모델 다운로드 10B+/월, Anyscale 배포 건수 급증 | 모델 배포 증가 -> 추론 서버 가동률 상승 -> DRAM/NAND 수요 |

### D2. Vector DB & AI-Native Data [5개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| Vector DB 도입 기업 수 및 데이터 규모 | Pinecone, Weaviate, Chroma 등 | Pinecone 엔터프라이즈 고객 +200%, 인덱스 규모 1B+ 벡터 | Vector DB -> RAG 아키텍처 확산 -> 추론 시 메모리 사용량 증가 (임베딩 캐싱 DRAM 수요) |

### D3. Data Labeling & Synthetic Data [8개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 학습 데이터 생산량 및 투자 규모 | Data Labeling, Synthetic Data, Data-Centric | Scale AI $1B+ 매출, Synthesis AI 고객 급증 | 학습 데이터 증가 -> 모델 학습 규모/빈도 증가 -> GPU/HBM 수요 (간접, 6-12개월) |

### D4. LLM Middleware & Frameworks [6개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| RAG/Agent 프레임워크 채택률 | RAG Framework, LLM Framework, AI Gateway | LangChain 다운로드 +300%, LlamaIndex 엔터프라이즈 도입 확대 | RAG 확산 -> 추론 시 컨텍스트 윈도우 확대 -> KV Cache 메모리 수요 증가 (DRAM+NAND) |

---

## E. Foundation Models & Generation

### E1. Foundation Models & LLM [15개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 모델 파라미터/컨텍스트 윈도우 스케일링 추이 | LLM/AGI, LLM/Research (OpenAI, Anthropic, Google) | GPT-5 2T 파라미터, Gemini 10M 컨텍스트 윈도우 | 파라미터 증가 -> 학습 GPU/HBM 수요 선형 이상 증가, 컨텍스트 확대 -> KV Cache DRAM/NAND |
| 학습 클러스터 규모 발표 | LLM/AGI, Hyperscaler | xAI 200K GPU 클러스터, Meta 600K H100 보유 발표 | 클러스터 규모 = HBM 수요 직접 정량화 가능 (GPU수 x HBM/GPU) |
| 오픈소스 모델 릴리스 빈도 | LLM/Open, LLM/Sovereign | Llama 4 출시, Mistral Large 2 공개, 국가별 소버린 LLM | 오픈소스 -> 학습 복제 수요 확산 -> 중소규모 GPU 클러스터 다수 가동 -> 분산 HBM 수요 |
| 학습-추론 Compute 비율 변화 | LLM 전반 | "추론이 학습의 10x" 발언, test-time compute 논문 | 추론 비중 상승 -> 서버 DRAM 중심 수요 시프트, HBM 대비 DRAM 수요 비중 변화 |

### E2. AI Video & Creative Generation [14개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 비디오/이미지 생성 서비스 사용량 | Video Gen, Image Gen, Creative Suite | Sora 일 100만 생성, Midjourney 1,600만 사용자 | 생성형 AI -> 추론 GPU 가동 -> DRAM/HBM 수요 (비디오는 이미지 대비 10x+ compute) |
| 멀티모달 모델 스펙 변화 | 3D/Video, Avatar Video, Multimodal | 비디오 생성 해상도 4K 표준화, 실시간 렌더링 등장 | 고해상도 멀티모달 -> 프레임당 메모리 사용량 급증 -> GPU 메모리 수요 가속 |

### E3. AI Voice & Audio [12개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 음성 AI API 호출량/매출 성장률 | Voice Synthesis, Speech-to-Text, Voice Platform | ElevenLabs ARR $330M (전년비 +400%), Deepgram API 호출 +500% | 음성 AI 확산 -> 실시간 추론 서버 수요 -> 낮은 지연시간 요구 -> 고대역 DRAM 수요 |
| Voice Agent 상용 배치 건수 | Voice Agent, Voice Infra, Enterprise Voice | Vapi 월 1억 콜, Parloa $350M 시리즈 D | 음성 에이전트 -> 항시 가동 추론 인프라 -> 서버 상시 DRAM 점유율 상승 |

---

## F. AI Developer Tools & Agents

### F1. AI Coding Agents & IDE [19개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 코딩 도구 사용자 수/ARR | AI-Native IDE, Code Assistant, Coding Agent | Cursor DAU 1M+, GitHub Copilot 20M+, Claude Code 런레이트 $500M+ | 코딩 AI 사용 -> 코드 생성 API 호출 급증 -> 추론 서버 수요 -> DRAM |
| 코딩 AI 모델 전용 학습 투자 | Code LLM, Enterprise Code | Poolside $626M 조달, Magic AI 100M 컨텍스트 모델 학습 | 코드 특화 모델 학습 -> 별도 GPU 클러스터 운용 -> HBM 수요 |

### F2. AI Agent Infra & Orchestration [14개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| Agent 플랫폼 기업 수/사용자 성장 | Agent Platform, Multi-Agent, Agent OS | Sierra ARR $150M, CrewAI Fortune500 60% 채택 | Agent 확산 -> 다중 LLM 호출 체인 -> 추론 compute 승수 효과 -> DRAM/NAND |
| Agent 실행 환경 인프라 투자 | Agent Sandbox, Tool Integration, Workflow Agent | E2B 샌드박스 사용량 +10x, Composio 3,000+ 앱 연동 | Agent 인프라 -> 상시 가동 추론 서버 + 상태 관리 메모리 -> DRAM 수요 |

---

## G. Enterprise AI Applications

### G1. Enterprise AI & Workflow [10개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 엔터프라이즈 AI 도입률/계약 규모 | Enterprise AI, Enterprise Agent, RPA/Agent | ServiceNow AI 계약 ACV +40%, UiPath AI Agent 전환 | Enterprise AI 도입 -> 기업별 추론 인프라 구축 (프라이빗 클라우드) -> 서버 DRAM 수요 |

### G2. Conversational AI & Voice Platform [10개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 컨택센터 AI 전환율 | Contact Center, CX Agent, CX AI | Kore.ai 400+ 엔터프라이즈, Cognigy Gartner MQ 리더 | 컨택센터 -> 실시간 음성+텍스트 추론 -> 항시 가동 서버 수요 -> DRAM |

### G3. AI Productivity & Collaboration [12개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI Productivity 도구 MAU 성장률 | AI Writing, Meeting AI, Presentations | Notion AI MAU 30M+, Otter.ai 기업 도입 +100% | 프로덕티비티 AI -> 일상적 추론 API 호출 -> 추론 서버 항시 가동 기반 수요 |

### G4. AI Search, Browser & Consumer [7개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 검색 쿼리 볼륨 | AI Search, AI Browser, Neural Search | Perplexity MAU 100M+, Brave AI 검색 비중 30%+ | AI 검색 -> 검색당 추론 compute 10x (기존 검색 대비) -> 서버 DRAM/GPU 수요 |

### G5. Industrial/Process AI [10개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 제조/산업 AI 도입 규모 | Mfg AI Platform, Industrial AI, Predictive Maint | Siemens Industrial Copilot 수주, Sight Machine 매출 +70% | 산업 AI -> Edge 서버/On-prem GPU 수요 -> Edge DRAM + 산업용 SSD |
| Digital Twin 활용 확대 | Digital Twin, Simulation | NVIDIA Omniverse 엔터프라이즈 도입, Ansys AI 시뮬레이션 | Digital Twin -> 대규모 시뮬레이션 compute -> HPC 서버 메모리 수요 |

---

## H. Vertical AI

### H1. Healthcare & Life Science AI [15개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 신약개발 파이프라인 수 | Drug Discovery, Protein Models, Comp Chemistry | Recursion Phase 2 진입 +5건, Insilico Medicine AI 신약 승인 | 신약개발 AI -> 분자 시뮬레이션/단백질 접힘 -> HPC GPU 클러스터 -> HBM |
| 의료 AI FDA/CE 승인 건수 | Medical Imaging, Radiology AI, Digital Pathology | PathAI FDA 승인, Viz.ai 적응증 확대 | 승인 -> 병원 배치 -> 추론 Edge 서버 -> 의료용 DRAM/SSD (소규모이나 고부가) |

### H2. Legal AI [7개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 법률 AI 플랫폼 도입 로펌 수 | Legal Research, Contract AI, eDiscovery | Harvey AI Top100 로펌 60% 도입, Casetext 합병 후 확장 | 법률 AI -> 대규모 문서 RAG 추론 -> 긴 컨텍스트 DRAM 수요 (간접, 수량 제한적) |

### H3. Financial Services AI [8개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 금융 AI 거래량/처리량 변화 | Financial Agent, Fraud Detection, AML/Compliance | Featurespace 실시간 사기탐지 거래 +10B건, Upstart AI 대출 +50% | 금융 AI -> 실시간 대규모 추론 -> 저지연 DRAM 수요 (금융 특성상 on-prem 비중 높음) |

### H4. Defense & Government AI [8개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 국방 AI 예산/계약 규모 | Defense Analytics, Autonomous Systems, European Defense | Anduril $10B+ 수주, Palantir 국방 AI 계약 +60%, NATO AI 예산 확대 | 국방 AI -> 전용 GPU/Edge 서버 수요 (비민수, 보안 등급) -> 내방사선 메모리 등 특수 수요 |
| 자율 무기 체계 개발/배치 | Autonomous Drones, Autonomous Naval | Shield AI V-BAT 양산, Saab 자율 잠수함 배치 | 자율 시스템 -> 임베디드 AI compute -> Edge DRAM/NAND (소량이나 고마진) |

### H5. Supply Chain & Logistics AI [6개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 공급망 AI 플랫폼 도입 기업 수 | SC Intelligence, Supply Chain Plan, SC Visibility | o9 Solutions ARR +80%, FourKites 실시간 추적 확대 | 공급망 AI -> 기업 on-prem/클라우드 추론 -> 서버 DRAM (간접, 누적 효과) |

### H6. Marketing, Sales & AdTech AI [7개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 마케팅/세일즈 도구 ARR 성장 | Revenue AI, Sales Intel, Marketing AI | 6sense ARR $300M+, Gong AI 매출 +50% | 마케팅 AI -> SaaS 추론 API 사용 -> 클라우드 추론 서버 수요 (간접) |

### H7. HR & Talent AI [5개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 채용/인재관리 플랫폼 사용 규모 | Recruiting AI, Talent Intelligence, People Analytics | Eightfold 대기업 도입 +200사, Pymetrics 평가 건수 +5M | HR AI -> 추론 API 소비 -> 클라우드 서버 수요 (간접, 미약) |

### H8. Climate & Sustainability AI [5개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 기후 AI 규제/의무화 진행 | Carbon Accounting, Climate Risk, Carbon Management | EU CSRD 의무화, SEC 기후 공시 규정 시행 | 기후 규제 -> 기업별 AI 기반 탄소 분석 인프라 -> 추론 서버 (간접) |

### H9. Education AI [5개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 교육 플랫폼 사용자 수 | AI Tutoring, Language Learning | Duolingo AI 사용자 100M+, Khan Academy Khanmigo 확대 | 교육 AI -> 대규모 동시 추론 세션 -> 클라우드 서버 DRAM (간접) |

### H10. Autonomous Vehicles [8개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AV 학습 클러스터 규모 | End-to-End AV, FSD, ADAS/AV | Tesla Dojo 확장, Waymo 학습 인프라 투자 | AV 학습 -> 대규모 GPU 클러스터 (비디오 학습은 텍스트 대비 메모리 집약) -> HBM |
| 자율주행 차량 출하/배치 수 | Robotaxi, AV Trucking, Autonomous Freight | Waymo 일 200K 유료 탑승, Aurora 자율 트럭 상용화 | 차량 출하 -> 차량당 LPDDR5X + UFS/eMMC 탑재 -> 모바일 메모리 수요 |

### H11. Agriculture & Geospatial AI [5개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 위성/농업 AI 데이터 처리량 | Satellite AI, Geospatial Intel, Precision Farm | Planet Labs 이미지 처리량 +200%, John Deere AI 스프레이 채택 | 위성 데이터 -> 이미지 분석 서버 -> GPU/DRAM 수요 (니치이나 성장) |

---

## I. Security & Governance

### I1. AI Security & Safety [20개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 보안 솔루션 도입 기업 수/매출 | AI Security, Agent Security, ML Security | Wiz $500M+ ARR, HiddenLayer AI 모델 보안 수주 | AI 보안 -> 보안 추론 워크로드 추가 (모든 AI 서버에 보안 레이어) -> DRAM 추가 오버헤드 |
| AI 관련 사이버 공격/규제 이벤트 | Prompt Protection, ML Model Sec, Data Security | AI 모델 탈취 사건, EU AI Act 보안 요건 강화 | 보안 규제 -> On-prem AI 수요 증가 (클라우드 대비) -> 기업 전용 서버 수요 -> DRAM |

### I2. AI Governance & Compliance [10개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 규제 입법/시행 건수 | AI Governance, Compliance, Data Governance | EU AI Act 시행, 중국 AI 규제 강화, 미국 행정명령 | 규제 강화 -> 모델 감사/모니터링 인프라 -> 추가 서버 수요 (간접) |

### I3. AI Observability & AIOps [11개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| AI 인프라 관리 도구 도입 확대 | AIOps, DCIM, Observability | Datadog AI 모니터링 매출 +40%, Run.ai GPU 오케스트레이션 | AIOps -> GPU 활용률 최적화 -> 동일 GPU 대비 더 많은 워크로드 -> 메모리 가동률 상승 |

### I4. Edge AI Infrastructure [4개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| Edge AI 디바이스 출하 및 최적화 도구 확산 | Edge AI Infra, Edge AI Opt, Edge SoC | Hailo Edge AI 프로세서 100만개 출하, Qualys Edge AI 배포 | Edge AI -> 엣지 디바이스당 LPDDR/eMMC 탑재 -> 소량이나 기기 수 곱셈 효과 |

---

## J. Robotics & Embodied AI

### J1. Robotics & Embodied AI [16개사]

| 측정변수 | 관측 대상 | 시그널 예시 | 메모리 전이 경로 |
|----------|-----------|-------------|------------------|
| 로봇 출하량 전망 (산업용 + 서비스 + 휴머노이드) | Industrial Robot, Service Robot, Humanoid, Cobot | Figure 02 양산 시작, Boston Dynamics Spot 10K대 배치 | 로봇 출하 -> 로봇당 Edge SoC + LPDDR + NAND -> 신규 메모리 시장 세그먼트 |
| 로봇 Foundation Model 학습 투자 | Robot Foundation, Robot AI | Physical Intelligence $400M 조달, Covariant 대규모 학습 | 로봇 파운데이션 모델 -> 비디오+물리 시뮬레이션 학습 -> 매우 메모리 집약적 -> HBM 수요 |
| 휴머노이드 상용화 타임라인 | Humanoid | Figure AI 2027 공장 배치 목표, Tesla Optimus 시범 가동 | 휴머노이드 대량 양산 시 -> 대당 LPDDR5X 16-32GB + 고용량 NAND -> 장기 신규 수요 축 |

---

## 부록: 측정변수 요약 통계

- 총 35개 중분류에 대해 **59개 측정변수** 정의
- 메모리 전이 경로 유형 분류
  - HBM 직결: B1(장비), B2(GPU 스펙), B5(서버 출하), B6(패키징), C2(Hyperscaler capex), E1(모델 스케일)
  - 서버 DRAM: C1-C2(DC/클라우드), D1-D4(데이터 인프라), E3(음성), F1-F2(코딩/에이전트), G1-G4(엔터프라이즈)
  - NAND/SSD: B3(스토리지), D4(RAG/KV Cache), E1(컨텍스트 윈도우)
  - 모바일 LPDDR/UFS: B2(Edge NPU), H10(AV), I4(Edge AI), J1(로보틱스)
  - 간접/장기: A1-A3(인프라), H1-H9(버티컬), I1-I3(보안/거버넌스)
