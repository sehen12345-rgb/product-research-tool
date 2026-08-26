# 경쟁사 상품 리서치 자동화 도구

링크만 붙여넣으면 쿠팡·스마트스토어·네이버쇼핑 상품 정보를 자동 추출·정리해주는 데스크탑 앱.

---

## 개발 환경

| 항목 | 내용 |
|------|------|
| 언어 | Python 3.11+ |
| GUI 프레임워크 | PyQt6 |
| 스크래핑 | Playwright (Chromium headless) |
| HTML 파싱 | BeautifulSoup4 |
| AI 파싱 보조 | Claude API (claude-sonnet-4-6) |
| 데이터 저장 | SQLite3 (로컬) |
| 데이터 내보내기 | openpyxl (Excel), csv |
| 패키지 관리 | pip + requirements.txt |
| OS | Windows 11 |

### 설치 방법

```bash
git clone https://github.com/sehen12345-rgb/product-research-tool.git
cd product-research-tool
pip install -r requirements.txt
playwright install chromium
python main.py
```

---

## 아키텍처

```
product-research-tool/
├── main.py                  # 앱 진입점
├── requirements.txt
├── README.md
│
├── ui/                      # PyQt6 UI 컴포넌트
│   ├── main_window.py       # 메인 윈도우
│   ├── input_panel.py       # URL 입력 패널
│   ├── result_table.py      # 결과 테이블 위젯
│   └── styles.py            # 공통 스타일시트 (QSS)
│
├── scrapers/                # 플랫폼별 스크래퍼
│   ├── base.py              # 스크래퍼 추상 기본 클래스
│   ├── coupang.py           # 쿠팡 스크래퍼
│   ├── smartstore.py        # 네이버 스마트스토어 스크래퍼
│   └── naver_shopping.py    # 네이버쇼핑 스크래퍼
│
├── parser/
│   └── ai_parser.py         # Claude API로 비정형 상품 정보 파싱
│
├── db/
│   ├── database.py          # SQLite 연결·마이그레이션
│   └── models.py            # 상품 데이터 모델
│
└── export/
    ├── excel_exporter.py    # Excel(.xlsx) 내보내기
    └── csv_exporter.py      # CSV 내보내기
```

### 데이터 흐름

```
URL 입력
  → 플랫폼 감지 (쿠팡/스마트스토어/네이버쇼핑)
  → Playwright로 페이지 렌더링
  → BeautifulSoup으로 1차 파싱
  → 추출 실패 필드는 Claude API로 보조 파싱
  → 결과 SQLite 저장
  → 테이블에 실시간 표시
  → Excel/CSV 내보내기
```

### 추출 필드

| 필드 | 설명 |
|------|------|
| 플랫폼 | 쿠팡 / 스마트스토어 / 네이버쇼핑 |
| 상품명 | 전체 상품명 |
| 브랜드 | 브랜드·제조업체명 |
| 가격 | 판매가 (할인가 포함) |
| 원가 | 정가 (있을 경우) |
| 칼로리 | kcal (식품의 경우) |
| 영양성분 | 단백질·탄수화물·지방 등 |
| 제조사/원산지 | 상품 상세 정보 |
| 리뷰 수 | 누적 리뷰 개수 |
| 평점 | 별점 |
| 상세페이지 URL | 원본 링크 |
| 수집 일시 | 자동 기록 |

---

## 디자인 가이드

### 테마

- 전체 톤: 모던 다크 테마 (VS Code 계열)
- 배경: `#1e1e2e`
- 서브 배경 (패널): `#2a2a3d`
- 포인트 컬러: `#7c6af7` (보라 계열)
- 성공: `#4ade80`
- 에러: `#f87171`
- 텍스트: `#e2e8f0`
- 서브 텍스트: `#94a3b8`

### 폰트

- 기본: `Pretendard` (없으면 `Segoe UI`)
- 테이블: `Consolas` (숫자 정렬용)
- 사이즈: 기본 13px, 제목 16px, 소제목 14px

### 레이아웃

```
┌─────────────────────────────────────────────────┐
│  [로고]  경쟁사 상품 리서치 도구          [최소화][닫기] │
├─────────────────────────────────────────────────┤
│  URL 입력창 (여러 줄 가능)        [수집 시작] [초기화]  │
├─────────────────────────────────────────────────┤
│  [전체 N개] [쿠팡 N] [스마트스토어 N] [네이버쇼핑 N]   │
│  [Excel 내보내기] [CSV 내보내기] [선택 삭제]            │
├─────────────────────────────────────────────────┤
│  플랫폼 │ 상품명 │ 브랜드 │ 가격 │ 칼로리 │ 리뷰 │ ▼  │
│  ───────────────────────────────────────────── │
│  쿠팡   │ OOO   │ OO    │ 15,900│ 250   │ 1.2k │    │
│  ...                                            │
├─────────────────────────────────────────────────┤
│  상태바: 수집 중... 3/5  ████████░░  [로그]          │
└─────────────────────────────────────────────────┘
```

### UX 원칙

- URL 여러 개를 한 번에 붙여넣기 가능 (줄바꿈 구분)
- 수집 진행 상황을 프로그레스 바로 실시간 표시
- 실패한 URL은 빨간색으로 표시 + 재시도 버튼
- 더블클릭으로 원본 상품 페이지 열기
- 컬럼 정렬·필터 지원

---

## 배포 환경

- 실행 방식: 로컬 Python 실행 (서버 없음)
- 배포 대상: Windows 단독 실행 파일 (`.exe`) — PyInstaller 사용
- GitHub 저장소: `github.com/sehen12345-rgb/product-research-tool`
- 인터넷 연결 필요: 스크래핑 + Claude API 호출 시

### 빌드 명령

```bash
pyinstaller --onefile --windowed --name ProductResearch main.py
```

---

## TODO 리스트

### Phase 1 — 기반 구축
- [ ] 프로젝트 초기 설정 (requirements.txt, 폴더 구조)
- [ ] SQLite DB 스키마 설계 및 초기화 (`db/`)
- [ ] 상품 데이터 모델 (`db/models.py`)
- [ ] 메인 윈도우 PyQt6 UI 뼈대 (`ui/main_window.py`)
- [ ] URL 입력 패널 (`ui/input_panel.py`)
- [ ] 다크 테마 스타일시트 (`ui/styles.py`)

### Phase 2 — 스크래핑 엔진
- [ ] Playwright 기반 스크래퍼 추상 클래스 (`scrapers/base.py`)
- [ ] 쿠팡 스크래퍼 (`scrapers/coupang.py`)
- [ ] 스마트스토어 스크래퍼 (`scrapers/smartstore.py`)
- [ ] 네이버쇼핑 스크래퍼 (`scrapers/naver_shopping.py`)
- [ ] 플랫폼 자동 감지 로직

### Phase 3 — AI 보조 파싱
- [ ] Claude API 연동 (`parser/ai_parser.py`)
- [ ] HTML에서 칼로리·영양성분·제조사 추출 프롬프트 최적화
- [ ] 파싱 실패 필드 fallback 처리

### Phase 4 — UI 완성
- [ ] 결과 테이블 위젯 (`ui/result_table.py`)
- [ ] 탭 필터 (전체/쿠팡/스마트스토어/네이버쇼핑)
- [ ] 컬럼 정렬·필터 기능
- [ ] 진행 상황 프로그레스 바
- [ ] 더블클릭 → 브라우저에서 상품 페이지 열기

### Phase 5 — 내보내기
- [ ] Excel 내보내기 (`export/excel_exporter.py`)
- [ ] CSV 내보내기 (`export/csv_exporter.py`)

### Phase 6 — 마무리
- [ ] 에러 핸들링 및 재시도 로직
- [ ] exe 빌드 테스트 (PyInstaller)
- [ ] GitHub 릴리즈

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-08-26 | 프로젝트 시작, README 및 문서 초안 작성 |
