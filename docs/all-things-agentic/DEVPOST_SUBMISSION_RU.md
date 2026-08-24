# Devpost submission — русский справочный вариант

Английский файл `DEVPOST_SUBMISSION_EN.md` является основной copy-ready версией. Этот текст нужен для проверки смысла.

## Название / тэглайн / категория

- **StudioGrid AI**
- **AI Production Control Room**
- **The Taskmaster**

## Одной строкой

StudioGrid превращает одну производственную задачу на естественном языке в валидированный, доказательный операционный workflow на Gemini, Google ADK и Vertex AI Agent Engine: автономно там, где агент имеет полномочия, и с детерминированным human approval только для значимого изменения расписания.

## Проблема

Съёмочный день — живая система ограничений. Задержки актёров, недостающие обязательные кадры, зависимости сцен, окна локаций, daylight, завершённая и заблокированная работа постоянно меняют допустимый план. Обычные инструменты фиксируют расписание, но не выполняют операционное рассуждение, необходимое после изменения реальности.

## Решение

**Give StudioGrid the production problem, not the steps.**

Пользователь один раз вводит ограниченную производственную цель. Tool-less Gemini 3.6 Flash classifier преобразует недоверенный текст только в строгий typed intent. После Pydantic-валидации private Control API запускает существующий Google ADK workflow в Vertex AI Agent Engine. Schedule/Coverage specialist получает server-built production context, вызывает typed authenticated private tool и сохраняет результат в Firestore.

Raw command не передаётся tool-enabled specialist agents.

## Два слоя reasoning

### 1. Safe command routing

Gemini Command Router:

- не имеет tools;
- не имеет mutation authority;
- не может вызвать Tool Server;
- возвращает только `ACTOR_DELAY`, `CHECK_COVERAGE` или `UNSUPPORTED`;
- не нормализует неподдерживаемую команду в разрешённый сценарий.

### 2. Operational agent execution

Validated typed operation поступает в Vertex AI Agent Engine. Google ADK Production Orchestrator делегирует Schedule Agent или Coverage Agent. Specialist рассуждает над серверным фактическим контекстом и вызывает только узкие typed tools.

## Главный Taskmaster proof — Coverage

Команда:

`Check SC_05 and make sure all required coverage is complete.`

После одной команды StudioGrid:

1. маршрутизирует `CHECK_COVERAGE`;
2. запускает Coverage Agent;
3. проверяет фактическое planned/completed state;
4. определяет, что для `SC_05` снят 1 из 3 обязательных кадров (`33.3%`);
5. находит отсутствующие `SH_12` и `SH_13`;
6. вызывает `create_coverage_alert`;
7. сохраняет `OPEN` alert и execution evidence.

Дополнительное действие пользователя после команды не требуется.

## Schedule — автономность и граница полномочий

Команда:

`Maya Reed is 45 minutes late. Keep today's shoot on schedule.`

Gemini возвращает `ACTOR_DELAY`. Schedule Agent анализирует актуальные actors/scenes/locations/dependencies/completed work/schedule/daylight и создаёт PENDING recommendation с evidence, affected scenes, expected benefit, risks, confidence и proposed order. Текущее расписание остаётся неизменным.

Human approval — не ручная orchestration. Человек не выбирает сцены и не объясняет агенту решение. Autonomous workflow уже завершён; approval только передаёт полномочие на consequential mutation.

**Autonomy where the agent has authority; deterministic human approval where a high-impact mutation crosses an authority boundary.**

## Архитектура

```text
Public browser
  → public Cloud Run web / authenticated BFF
  → IAM-private Control API
  → tool-less Gemini Command Router
  → strict Pydantic typed allowlist
  → Vertex AI Agent Engine
  → Google ADK Production Orchestrator
      ├─ Schedule Agent
      └─ Coverage Agent
  → Gemini specialist reasoning over server-built context
  → typed authenticated private tools
  → IAM-private Tool Server
  → Firestore
```

Schedule approval проходит отдельным human-only путём через server-side `ApprovalGate`.

## Security / prompt injection defense

- Public UI принимает bounded natural-language production commands.
- Raw text видит только isolated tool-less router.
- Pydantic проверяет model output и точный allowlist.
- Specialist получает typed operation/context, а не raw command.
- Unsupported location/weather/equipment/arbitrary mutation/approval-bypass команды fail closed.
- Agents не имеют прямого доступа к Firestore.
- `ApprovalGate` блокирует AGENT и SYSTEM для schedule approval/rejection.

## Проверенный scope

Public contest build намеренно поддерживает только:

- точные synthetic actor-delay combinations: Maya / 45 минут и Daniel / 30 минут;
- fixed `SC_05` shot-coverage workflow.

Это не заявление о понимании любых производственных команд. Узкий allowlist — часть production/security discipline.

## Public demo

<https://studiogrid-web-729921508335.europe-west3.run.app>

Путь: Reset → Coverage-команда → `SC_05`, `1/3`, `33.3%`, `SH_12`, `SH_13`, `OPEN`, execution ID → Reset → Maya-команда → PENDING proposal → optional HUMAN APPROVE/REJECT.

Repository: <https://github.com/a63909/StudioGridAI>

## Google stack

- Gemini 3.6 Flash via Vertex AI
- Google ADK 2.6.3
- Vertex AI Agent Engine
- Cloud Run
- Firestore
- Cloud Trace

## Data

Оригинальный вымышленный synthetic package **LAST LIGHT**. Реальные клиенты и данные киностудий не используются.

## Главный вывод

Автономность и полномочия — разные вещи. Coverage полностью заканчивается автономно. Schedule тоже автономно заканчивает анализ, tool execution и persistence, но реальный high-impact reorder остаётся human-authorized.
