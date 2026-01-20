# 프로젝트 정리 요약 (Project Organization Summary)

## 📋 정리 계획

### 1. Archive로 이동할 파일들

#### Summary 문서들 → `archive/docs/`
- `ALPHA_V2_IMPLEMENTATION_SUMMARY.md`
- `BRAVO_V2_UPGRADE_SUMMARY.md`
- `WOOD_V2_INTEGRATION_SUMMARY.md`
- `GIT_PUSH_SUMMARY.md`
- `FINAL_SUMMARY.md`
- `CLEANUP_SUMMARY.md`

#### 테스트 파일들 → `archive/tests/`
- `src/tools/test_*.py` (3개)
- `src/engines/wood/test_*.py` (7개)

### 2. Docs로 이동할 파일들

#### 가이드 문서들 → `docs/`
- `LIVE_BETA_GUIDE.md`
- `DEPLOYMENT_GUIDE.md`
- `src/engines/wood/IB_DCF_GUIDE.md`
- `src/engines/wood/OPM_GUIDE.md`
- `src/engines/wood/TRANSACTION_SERVICES_GUIDE.md`

#### 프로젝트 문서들 → `docs/`
- `PROJECT_BLUEPRINT.md`
- `QUICK_START.md`

### 3. 정리할 중복/불필요 파일들

- `app.py` (루트) - `src/app.py`와 중복 확인 필요
- `corp_code.xml` - DART에서 자동 생성되는 파일 (유지 또는 .gitignore 추가)
- `docs_cache/` - 캐시 파일 (유지)

## 🎯 최종 프로젝트 구조

```
mirkwood/
├── README.md
├── requirements.txt
├── .env (사용자 생성 필요)
├── src/
│   ├── main.py (Telegram Bot)
│   ├── agents/ (ZULU, X-RAY, BRAVO, ALPHA)
│   ├── engines/ (WOOD V2)
│   ├── tools/ (DART, Market Scanner, etc.)
│   └── utils/
├── docs/
│   ├── FIRST_PRINCIPLES.md
│   ├── QUICK_START.md
│   ├── PROJECT_BLUEPRINT.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── LIVE_BETA_GUIDE.md
├── archive/
│   ├── docs/ (Summary 문서들)
│   └── tests/ (테스트 파일들)
├── vault/
│   ├── reports/ (Excel 리포트)
│   ├── leads/ (리드 데이터)
│   └── logs/ (로그 파일)
└── knowledge/ (스킬 문서)
```

## ⚠️ 수동 작업 필요

PowerShell 경로 인코딩 문제로 자동화 스크립트 실행이 실패했습니다.
다음 명령어를 수동으로 실행하거나, 파일 탐색기에서 직접 이동하세요:

```powershell
# Python 스크립트 실행 (프로젝트 루트에서)
python organize_project.py
```

또는 파일 탐색기에서:
1. Summary 문서들을 `archive/docs/`로 이동
2. 테스트 파일들을 `archive/tests/`로 이동
3. 가이드 문서들을 `docs/`로 이동

## ✅ 완료된 작업

- [x] Archive 디렉토리 구조 생성 (`archive/docs/`, `archive/tests/`)
- [x] 정리 스크립트 작성 (`organize_project.py`)
- [x] 정리 계획 문서화
