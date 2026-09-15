---
name: wxo-adk-agent
description: watsonx Orchestrate ADK 네이티브 에이전트 빌드 및 배포 — Python @tool 함수, 에이전트 YAML (collaborator 또는 manager), 연결 설정, `orchestrate` CLI를 통해 호스팅된 Orchestrate 인스턴스에 직접 배포 (로컬 Docker 서버 불필요). 사용자가 watsonx Orchestrate, wxo, WXO, Orchestrate ADK, ADK tool, ADK agent, collaborator agent, manager agent, @tool 데코레이터, ToolResponse, agents import, tools import, env add, env activate, draft vs live, 또는 해커톤 에이전트를 언급할 때 사용.
---

# watsonx Orchestrate 엔터프라이즈 에이전트 구축하기

사용자가 IBM watsonx Orchestrate용 네이티브 ADK 에이전트를 빌드하고 배포할 수 있도록 돕습니다.
에이전트는 세 가지 기본 요소로 구성됩니다: **tools** (Python 함수), **agents** (YAML), **connections** (YAML).
각 요소를 로컬에서 작성하고 `pytest`로 유닛 테스트를 실행한 다음, `orchestrate` CLI를 통해 아티팩트를
공유 호스팅 Orchestrate 인스턴스에 직접 푸시합니다. 로컬 Docker 서버 없음, Lite 스택 없음 — CLI가
호스팅 인스턴스에 직접 통신합니다.

## 이 스킬이 적용되는 경우

- "watsonx Orchestrate 에이전트를 만들어줘 …"
- "…에 대한 ADK 툴을 작성해줘"
- "…에 대한 manager + collaborator 구조가 필요해"
- "이걸 Orchestrate에 배포하려면 어떻게 해?"
- `@tool`, `ToolResponse`, `agents import`, Draft/Live 연결, 또는 `watsonx/openai/gpt-oss-120b`가 언급된 경우.

## 타겟 선택

사용자가 무엇을 만들지 말하지 않았다면 아래 중 하나를 제안하세요.
명시적으로 더 많은 것을 원하지 않는 한 **Tier 1**부터 시작하세요.

### Tier 1 — 단일 툴 collaborator (≈ 2시간)
1. **PTO 잔여 조회** (HR). 모의 HR 엔드포인트 또는 소형 FastAPI 스텁 사용.
2. **GitHub PR 요약** (개발 도구). GitHub REST API에 대한 `list_open_prs(username)` — 무료 토큰, 엔터프라이즈 인증 불필요.
3. **다음 미팅 조회** (생산성). Google Calendar 또는 Notion DB 대체.
4. **경비 조회** (재무). 모의 Concur/SAP 엔드포인트.
5. **날씨 기반 여행 알림** (재미있는 사례). OpenWeather — 지시문 작성에 집중.

### Tier 2 — 멀티 툴 collaborator (≈ 반나절)
6. **IT 헬프데스크 티켓 어시스턴트**: `search_kb` → `create_ticket` → `get_ticket_status`.
7. **영업 리드 보강**: `lookup_account` → `get_recent_news` → `summarize_account`.
8. **조달 RFP 추적기**: `list_open_rfps` → `get_rfp_details` → `check_approval_status`.
9. **문서 요약기**: `list_documents` → `get_document_text` → `summarize` (Box / Drive / Dropbox).

### Tier 3 — Manager + collaborators (하루 종일)
10. **직원 온보딩 오케스트레이터**: HR manager → `hr_records_agent`, `it_provisioning_agent`, `facilities_agent`.
11. **고객 지원 트리아지**: support manager → `refund_agent`, `shipping_agent`, `kb_agent`.
12. **재무 마감 어시스턴트**: finance manager → `journal_entries_agent`, `reconciliation_agent`, `variance_explainer_agent`.

업스트림 API가 속도 제한이 있거나 엔터프라이즈 SSO가 필요한 경우, 20줄짜리 FastAPI 서버로
모의 구현을 제안하세요 — 인증 핸드셰이크가 아닌 에이전트 + 툴 + 배포 메커니즘에 집중합니다.
단일 채팅 턴에서 데모 가능한 사례를 우선적으로 선택하세요.

## 워크플로우

이 스킬은 해커톤이 모든 참가자가 배포하는 **공유 호스팅 Orchestrate 인스턴스**를 제공한다고 가정합니다.
다음 순서로 반복합니다:

1. **로컬에서 코드 작성** — `tools/`에 `@tool` 함수, `agents/`에 에이전트 스펙,
   `connections/`에 연결 설정. 테스트는 툴 파일 옆에 위치.
2. **`pytest`로 테스트** — `pytest tools/`는 모의 객체를 사용해 툴의 HTTP 로직을 검증합니다.
   이것이 유일한 빠른 피드백 루프이므로 충실하게 작성하세요.
3. **모든 import 전에 `orchestrate env list` 실행** — 호스팅 환경이 활성화되어 있는지 확인.
   이를 빠뜨리는 것이 함정 #7입니다.
4. **호스팅 인스턴스로 import** — `connections add` → `tools import` →
   `agents import` 순서로, 호스팅 환경에 직접 적용.
5. **호스팅 채팅 UI에서 테스트** — 에이전트의 LLM 동작이 실제로 실행되는 곳입니다.

로컬 서버 없음. Docker 없음. Lite UI 없음. ADK CLI는 활성화된 환경과 직접 통신하며,
유일한 "배포 대상"은 호스팅 인스턴스입니다.

## 멘탈 모델

- **Tool** = Python `@tool` 데코레이터가 붙은 함수. 데코레이터의 docstring이
  에이전트의 LLM이 호출 여부를 결정할 때 읽는 내용입니다.
- **Agent** = `name`, `llm`, `instructions`, `tools` 목록(함수명 문자열),
  `collaborators` 목록(다른 에이전트)을 가진 YAML 스펙.
- **Connection** = `app_id`와 인증 종류를 명시하는 YAML 설정. 툴이 필요한
  `app_id`를 선언하면 ADK가 런타임에 자격 증명을 주입합니다.
- **Manager vs collaborator** = 순수 라우터 vs 작업자. Manager는 `tools:`가 비어 있고
  `collaborators:`가 채워져 있습니다. Collaborator는 그 반대입니다.
- **Draft vs Live** = 호스팅 인스턴스는 연결당 두 개의 자격 증명 슬롯을 유지합니다.
  반복 중에는 Draft를 설정하고, 최종 사용자에게 노출하기 전에 Live로 승격합니다.

## 권장 프로젝트 레이아웃

전체 구조는 `starter/project_layout.md`를 참고하세요. 한 가지 규칙:

**파일명 스템 == `@tool` 함수명 == 에이전트 YAML `name:` == `tools:`의 문자열.**

하나를 바꾸면 나머지 세 개도 모두 바꿔야 합니다. 이 규칙을 지키면 함정 #1이 구조적으로 방지됩니다.

```
my-wxo-agent/
  agents/my_agent.yaml          # name: my_agent
  tools/my_tool.py              # def my_tool(...)
  tools/my_tool_test.py
  connections/my_app.yaml       # app_id: my_app
  .env                          # starter/env.example에서 복사
  requirements.txt              # starter/requirements.txt에서 복사
```

## Step 1 — 툴 작성

`references/tool_template.py`를 복사하고 수정하세요. 핵심 규칙:

1. **`@tool(expected_credentials=[...])`** — 툴이 필요로 하는 연결을 항상 나열하세요.
   외부 API가 없더라도 (`[]`) 인자를 유지하세요.
2. **`ToolResponse[T]` 반환** — 예외를 발생시키지 마세요. 모든 오류를 `ErrorDetails`로
   래핑하여 에이전트의 "Error Handling" 지시문이 이를 표시할 수 있도록 하세요.
3. **Google 스타일 docstring** — 한 줄 요약 + 빈 줄 + `Args:` (모든 파라미터, 비어 있지 않은 설명) + `Returns:`.
   ADK는 이를 기반으로 LLM의 툴 스키마를 생성합니다. args가 빠지면 LLM이 툴을 호출할 수 없습니다.
4. **Snake_case 함수명** — 이 정확한 문자열이 에이전트 YAML의 `tools:` 아래에 들어갑니다.
   파일명 스템과 일치시키세요.

템플릿은 공유 유틸리티 의존성 없이 `ToolResponse`와 `ErrorDetails`를 인라인으로 포함합니다.
형태는 wxo-domains 레포와 동일하므로, 나중에 업스트림에 기여할 때 코드를 그대로 이식할 수 있습니다.

## Step 2 — 동위치 테스트 작성

`references/tool_test_template.py`를 복사하고 수정하세요. HTTP 경계에서 `requests`를 모킹하고;
`ToolResponse` 형태를 검증하세요. 최소 두 개의 테스트: 정상 경로 (200)와 오류 경로 (5xx).
`pytest tools/`로 실행하세요.

`result.tool_output`에서 `AttributeError`가 발생하면, ADK 버전이 반환값을 `.content`로
감싸고 있는 것입니다 — `result.content.tool_output`을 시도해보세요. 템플릿은 두 경우 모두 처리합니다.

## Step 3 — 연결 설정 (툴이 외부 API를 호출하는 경우에만)

적절한 인증 종류를 선택하세요:

- `key_value` — 단일 토큰 또는 임의의 키/값 쌍. 가장 간단. → `references/connection_basic_auth.yaml` 변형 A.
- `basic` — 사용자명 + 비밀번호. → `references/connection_basic_auth.yaml` 변형 B.
- `bearer` — 불투명 bearer 토큰.
- `api_key` — 표준 API 키 헤더.
- `oauth_auth_code_flow` — 사용자별 OAuth 흐름. → `references/connection_oauth.yaml`.
- `oauth_auth_client_credentials_flow` — 기계 간 통신, 사용자 없음.

전체 스키마는 `references/yaml_schema.md`에 있습니다. YAML의 `app_id`는 툴의
`ExpectedCredentials(...)`의 `app_id` 및 `orchestrate connections add`에 전달하는
`--app-id`와 일치해야 합니다.

## Step 4 — 에이전트 YAML 작성

두 가지 시작점:

- **Collaborator** (툴을 호출하는 작업자): `references/agent_collaborator.yaml` 복사.
- **Manager** (다른 에이전트에 위임하는 순수 라우터): `references/agent_manager.yaml` 복사.

에이전트가 여러 가지 명확히 구분된 작업 유형에 걸쳐 있지 않다면 단일 collaborator를 기본으로 사용하세요.
Manager는 LLM 홉을 하나 더 추가합니다 — 명확히 분리된 관심사에 걸쳐 ~5개 이상의 툴이 있을 때만 가치가 있습니다.

지시문 작성 시: `## Role` 단락으로 시작하고, `## Tool Usage Guidelines`, `## How To Use Tools`,
`## Handling ToolResponse`, `## Scope Control` 같은 섹션을 추가하세요. 각 툴을 *언제* 호출할지를
구체적으로 명시하고, *무엇을* 하는지는 함수 docstring에서 이미 다루고 있습니다.

## Step 5 — 호스팅 인스턴스에 배포

초기 설정 상세 내용은 `references/remote_setup.md`에, 전체 배포 명령어는
`references/deploy_recipe.md`에 있습니다. 요약:

```bash
# 최초 1회: 호스팅 환경 등록. --activate는 사용하지 마세요 (비TTY 셸에서 인터랙티브
# 키 입력을 요청하므로). add와 activate를 분리하세요.
# 비프로덕션 인스턴스는 --iam-url과 --type을 반드시 설정해야 합니다 —
# 티어별 표는 remote_setup.md를 참고하세요. 기본값은 prod에서만 올바릅니다.
orchestrate env add --name $WO_ENV_NAME --url $WO_INSTANCE_URL \
    --iam-url $WO_IAM_URL --type $WO_AUTH_TYPE
orchestrate env activate $WO_ENV_NAME --api-key $WO_INSTANCE_API_KEY

# 배포할 때마다:
orchestrate env list                                                          # 호스팅 환경이 활성화되어 있는지 확인
pytest tools/                                                                 # 마지막 로컬 검증
orchestrate connections add --app-id my_app                                   # 툴이 API를 호출하는 경우
orchestrate connections configure --app-id my_app --env draft --type team --kind key_value
orchestrate connections set-credentials --app-id my_app --env draft -e token=$MY_APP_TOKEN
orchestrate tools import --kind python --file tools/my_tool.py \
    --app-id my_app --requirements-file requirements.txt
orchestrate agents import --file agents/my_agent.yaml

# 그 다음 $WO_INSTANCE_URL/manage/connectors를 열어 Draft → Live로 승격.
# 그 다음 $WO_INSTANCE_URL/chat을 열어 데모.
```

**모든 import 전 정상 확인**: `orchestrate env list`를 실행하세요. 활성 환경이 없으면
import가 유효한 곳으로 가지 않습니다 — 함정 #7.

**`env activate`가 `Scope not found`로 실패하는 경우** — 인스턴스 티어에 맞지 않는
`--iam-url`입니다. 잘못된 키가 아닌 함정 #8입니다.

## Step 6 — Journey Success 테스트 케이스 업로드

에이전트가 호스팅 채팅에서 올바르게 응답하면, *올바른* 궤적(어떤 툴이 어떤 순서로,
어떤 인자로 호출되어야 하며, 어떤 종류의 응답으로 이어지는지)을 인코딩하는 테스트 케이스를 작성하세요.
심사위원이 Orchestrate UI의 에이전트 "Tests" 탭에서 실행하고 Journey Success를 채점합니다.

테스트 케이스는 JSON 파일로 존재하며 (`references/evaluation_template.json` 참고) HTTP API를
통해 업로드합니다 — 호스팅 테스트 케이스 업로드를 위한 `orchestrate` CLI 명령어는 없습니다.
전체 스키마, 업로드 헬퍼, 채점 규칙은 `references/evaluation_recipe.md`에 있습니다.

요약:
```bash
# JWT 획득, 에이전트 id 확인, JSON을 멀티파트로 업로드.
TOKEN=$(curl -fsS -X POST "$WO_IAM_URL/siusermgr/api/1.0/apikeys/token" \
    -H "Content-Type: application/json" \
    -d "{\"apikey\":\"$WO_INSTANCE_API_KEY\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
AGENT_ID=$(curl -fsS -H "Authorization: Bearer $TOKEN" \
    "$WO_INSTANCE_URL/v1/orchestrate/agents" \
    | python3 -c "import sys,json; print(next(a['id'] for a in json.load(sys.stdin) if a['name']=='my_agent'))")
curl -fsS -X POST -H "Authorization: Bearer $TOKEN" \
    "$WO_INSTANCE_URL/v1/orchestrate/agent/$AGENT_ID/test_case/v2" \
    -F "file=@tests/my_test.json;type=application/json"
```

Journey Success는 각 실행에서 네 가지를 채점합니다: 툴 호출 커버리지, 툴 호출 순서 (`goals` DAG),
인자별 매칭 (`strict` / `fuzzy` / `optional`), 텍스트 응답 키워드.
`goal_details`를 신중하게 계획하세요 — 키워드를 과도하게 지정하는 것이 해커톤 테스트가
불필요하게 실패하는 #1 원인입니다.

## 검증 체크리스트

호스팅 인스턴스에 대해 다음이 완료되면 작업이 끝납니다:

1. `pytest tools/`가 로컬에서 통과.
2. `orchestrate env list`가 호스팅 환경을 활성으로 표시.
3. `orchestrate tools list`가 툴의 함수명을 표시.
4. `orchestrate agents list`가 에이전트를 표시.
5. `$WO_INSTANCE_URL/manage/connectors`가 Draft와 Live 모두에서 연결을 연결됨으로 표시.
6. 호스팅 채팅 URL에 에이전트가 표시되고, 데모 프롬프트가 툴을 통해 왕복하여 합리적인 답변을 반환.
7. Journey Success 테스트 케이스가 깔끔하게 업로드되고
   (`{"test_case_ids":["..."],"total_test_cases":1}`), 에이전트의 "Tests" 탭에 나타나며,
   UI에서 실행 시 **통과**됨.

단계가 실패하면 `references/deploy_recipe.md` 하단의 "Common failure → fix" 표를 참고하세요.

## 흔한 함정 (각 한 줄)

`references/pitfalls.md`에 잘못된/올바른 전체 예제가 있습니다.

1. **`tools:` 문자열이 함수명과 불일치** — 세 가지가 일치하도록 유지하세요.
2. **Manager에 비어 있지 않은 `tools:`** — manager는 라우팅만 합니다; 항상 `tools: []`.
3. **Google docstring 누락** — `Args:` 아래에 모든 인자, `Returns:` 포함.
4. **`@tool`에서 예외 발생** — 항상 `error_details`와 함께 `ToolResponse`를 반환하세요.
5. **LLM 문자열 오타** — `watsonx/openai/gpt-oss-120b`를 고수하세요.
6. **잘못된 import 순서** — connections → tools → agents.
7. **모든 import 전 `orchestrate env list` 누락** — 활성 환경이 없으면 import가 유효한 곳으로 가지 않습니다.
8. **env activate 시 `Scope not found`** — 인스턴스 티어에 맞지 않는 `--iam-url`이며, 잘못된 키가 아닙니다.
   CLI 기본값은 프로덕션 IAM을 가정합니다; 스테이징/테스트는 명시적인 오버라이드가 필요합니다.

## 강권하는 기본값

- 특별한 이유가 없다면 모든 곳에 `llm: watsonx/openai/gpt-oss-120b`.
- `style: default` (chain-of-thought 추론이 사용 사례에 필요하다는 것을 알 때만 `react` 사용).
- 파일당 하나의 `@tool`, 파일명 스템이 함수명과 일치.
- YAML당 하나의 에이전트, 파일명 스템이 `name:` 필드와 일치.
- 연결 YAML당 하나의 `app_id`, 스템이 `app_id`와 일치.

## 예제

동작하는 엔드투엔드 예제는 `examples/`에 있습니다. 각 하위 디렉터리는 참고하거나 복사하거나
그대로 배포할 수 있는 독립적인 프로젝트입니다. 참조 템플릿이 너무 추상적으로 느껴질 때
시작점으로 활용하세요.

| 디렉터리 | 패턴 | 보여주는 것 |
|---|---|---|
| [`examples/personal_banking/`](examples/personal_banking/) | 멀티 툴 collaborator | `list_accounts`, `transfer_money`, `get_contact`, `change_contact`를 Astra DB 백엔드에 연결; `import-all.sh`로 엔드투엔드 배포 |
| [`examples/customer_care/`](examples/customer_care/) | Manager + 두 collaborator | 분리된 `customer_care`와 `servicenow` 툴 패키지; manager가 라우팅; 멀티 패키지 `requirements.txt` 분리 방법 제시 |
| [`examples/customer_care_planner/`](examples/customer_care_planner/) | Planner 스타일 에이전트 | `customer_care`와 동일한 도메인이지만 `planner` 스타일과 `format_task_results` 조인 툴 사용; 기본 스타일 버전과 비교하여 트레이드오프 이해 |
| [`examples/healthcare_provider/`](examples/healthcare_provider/) | OpenAPI 툴 (Python 없음) | 사전 구축된 OpenAPI 스펙 (`get-healthcare-providers.yml`)을 직접 import — Python `@tool` 불필요; `openapi` 툴 종류 제시 |
| [`examples/ibm_knowledge/`](examples/ibm_knowledge/) | 지식 베이스 에이전트 | `stock_price` 툴과 벡터 지식 베이스 연결; 정적 및 동적 모드 변형 + 깔끔한 정리를 위한 `remove_all.sh` 포함 |
| [`examples/agentic_memory/`](examples/agentic_memory/) | Agentic 메모리 / 티켓 생성 | 플랫 파일 예제: 같은 디렉터리에 하나의 `@tool` (`create_patient_support_ticket.py`) + 하나의 에이전트 YAML; 최소 구조, 형태 학습에 적합 |
| [`examples/voice_enabled_elevenlabs/`](examples/voice_enabled_elevenlabs/) | 음성 채널 | 에이전트에 ElevenLabs TTS 음성 설정을 첨부하는 방법; `voice/`에 두 가지 설정 변형 (표준 및 고급) 포함 |

### 언제 예제를 볼 것인가

- **"manager/collaborator 분리가 필요해"** → `customer_care/` 또는 `customer_care_planner/`
- **"Python을 작성하지 않고 기존 REST API를 호출하고 싶어"** → `healthcare_provider/`
- **"영속적 메모리나 티켓 생성이 필요해"** → `agentic_memory/`
- **"툴과 함께 지식 베이스가 필요해"** → `ibm_knowledge/`
- **"음성 지원 에이전트를 만들고 있어"** → `voice_enabled_elevenlabs/`
- **"완전한 멀티 툴 CRUD 예제가 필요해"** → `personal_banking/`

## 참조 파일

- `references/tool_template.py` — `ToolResponse`/`ErrorDetails`가 인라인으로 포함된 실행 가능한 `@tool` 스켈레톤.
- `references/tool_test_template.py` — pytest 정상/오류 경로 템플릿.
- `references/agent_collaborator.yaml` — 작업자 에이전트 템플릿.
- `references/agent_manager.yaml` — 라우터 에이전트 템플릿.
- `references/connection_basic_auth.yaml` — `key_value` 및 `basic` 인증 설정.
- `references/connection_oauth.yaml` — `oauth_auth_code_flow` 설정.
- `references/yaml_schema.md` — 에이전트 및 연결에 대한 전체 필드별 스키마.
- `references/deploy_recipe.md` — 호스팅 인스턴스 엔드투엔드 명령어 (로컬 서버 불필요).
- `references/evaluation_template.json` — 인라인 스키마 주석이 포함된 Journey Success 테스트 케이스 스켈레톤.
- `references/evaluation_recipe.md` — 업로드 헬퍼, 채점 규칙, 흔한 실패.
- `references/remote_setup.md` — 최초 1회 호스팅 인스턴스 등록 + Draft → Live 승격.
- `references/pitfalls.md` — 잘못된 코드 vs 올바른 코드 예제가 있는 일곱 가지 함정.
- `starter/INSTALL.md` — `orchestrate` CLI 설치 (uv 기반 경로, pip 대체). Python 버전 오류가 발생하면 먼저 읽으세요.
- `starter/requirements.txt` — 버전이 고정된 의존성. Python 3.11–3.13만 지원 (3.14 미지원).
- `starter/env.example` — 환경 변수 스켈레톤.
- `starter/project_layout.md` — 권장 디렉터리 레이아웃 및 명명 규칙.
