# Devpost submission — русский справочный вариант

Английский файл `DEVPOST_SUBMISSION_EN.md` является основной copy-ready версией. Этот перевод нужен для внутренней проверки смысла и не заменяет обязательные англоязычные материалы.

## Название

StudioGrid AI

## Тэглайн

AI Production Control Room

## Категория

The Taskmaster

## Одной строкой

StudioGrid превращает сбой на съемочной площадке в доказательное изменение расписания через реальный Google ADK multi-agent workflow, оставляя значимое решение за человеком.

## Проблема

Съемочный день — живая система ограничений. Актер опаздывает, естественный свет исчезает, локации доступны в узкие окна, сцены снимаются не по порядку, а обязательное покрытие может оставаться незавершенным. Одно изменение влияет сразу на актеров, камеру, локации, арт-департамент, continuity и монтаж.

Обычные производственные системы фиксируют план. StudioGrid выполняет операционную работу, которая возникает, когда реальность перестает совпадать с планом.

## Решение

StudioGrid AI получает структурированное событие и запускает развернутый Production Orchestrator. Он направляет задачу Schedule Agent или Coverage Agent. Агент анализирует фактическое состояние производства, Gemini 3.6 Flash рассуждает над проверенным контекстом, а результат создается через типизированный приватный tool и сохраняется в Firestore.

Это не чатбот и не генератор сценариев. Это ограниченный по полномочиям операционный workflow.

## Почему это agentic

Пользователь сообщает событие, а не решение. При задержке Maya Reed на 45 минут пользователь не выбирает новую сцену, не перечисляет зависимости и не собирает рекомендацию. Vertex AI Agent Engine запускает Google ADK application; Production Orchestrator делегирует Schedule Agent; модель анализирует актеров, сцены, локации, зависимости, порядок, daylight constraints и вызывает `create_schedule_proposal()`.

До вмешательства человека уже существует сохраненная PENDING-рекомендация с причиной, evidence, ожидаемой пользой, рисками, confidence и конкретным reorder. Человек появляется только на границе значимого изменения состояния.

## Golden workflow

1. **FACT:** Maya Reed (`ACT_02`) задерживается на 45 минут.
2. Private Control API формирует структурированное событие.
3. Vertex AI Agent Engine запускает Production Orchestrator.
4. Orchestrator направляет событие Schedule Agent.
5. Gemini 3.6 Flash анализирует актуальные ограничения.
6. Schedule Agent вызывает приватный типизированный tool.
7. Firestore сохраняет PENDING recommendation и безопасные execution metadata.
8. AI не может одобрить или отклонить собственную рекомендацию.
9. Production manager нажимает APPROVE.
10. Control API применяет reorder и записывает `HUMAN_DECISION`.
11. После refresh состояние остается сохраненным.

## Что агент делает автономно

- маршрутизирует событие специалисту;
- строит контекст из текущего production state;
- анализирует ограничения и доступную работу;
- выбирает разрешенный typed tool;
- создает и сохраняет proposal или coverage alert;
- записывает safe evidence;
- при ошибке прекращает изменение состояния безопасно.

## Зачем нужен human approval

Изменение съемочного расписания затрагивает всю группу. Поэтому StudioGrid разделяет автономность и полномочия. AI может создать PENDING proposal, но не получает tools APPROVE/REJECT. Server-side `ApprovalGate` блокирует AGENT и SYSTEM независимо от текста prompt или поведения модели.

Человек не ведет агента по шагам. Он только разрешает или отклоняет уже подготовленное значимое изменение.

## Multi-agent архитектура

Публичный Next.js web работает в Cloud Run. Server-side BFF получает Google ID token для приватного Control API. Control API вызывает развернутый Vertex AI Agent Engine. Google ADK Production Orchestrator делегирует Schedule Agent или Coverage Agent. Специалисты используют Gemini 3.6 Flash и вызывают типизированные инструменты второго приватного Cloud Run сервиса. Firestore хранит production state, proposals, alerts, events, demo sessions и execution evidence.

## Schedule Agent

Обрабатывает `ACTOR_DELAYED`: получает проверенные связи актеров и сцен, текущий порядок, подходящие альтернативы, location windows, dependencies и daylight constraints. Может создать только PENDING proposal. ACT_02/Maya и ACT_03/Daniel проходят один общий workflow с разными актерами.

## Coverage Agent

Сравнивает planned/completed shots. В golden demo он находит отсутствующие `SH_12` и `SH_13` и создает OPEN coverage alert через `create_coverage_alert()`.

## Google Cloud stack

- **Google ADK 2.6.3:** orchestration graph и specialist agents.
- **Gemini 3.6 Flash:** reasoning по серверному production context через Vertex AI.
- **Vertex AI Agent Engine:** реальный удаленный ADK runtime.
- **Cloud Run:** публичный web, приватный Control API, приватный Tool Server.
- **Firestore:** durable state, proposals, alerts, events и evidence.
- **Cloud Trace:** связь публичного действия с cloud execution через trace/correlation identifiers.

## Security и prompt injection defense

Browser видит только public web. BFF принимает небольшой allowlist операций, ограничивает размер и rate, а приватный API вызывается с server-side identity token. Arbitrary prompts не передаются: Pydantic запрещает лишние поля. Даже если модель попытается вызвать approval tool, server-side gate отклонит вызов. Agents не имеют прямого доступа к Firestore и используют отдельный IAM-private Tool Server.

## Failure handling

Invalid tool mutation завершается `ToolServerError`, сохраняет ERROR trace и не создает proposal. Firestore startup failure отключает AI runtime вместо скрытого перехода в непроверенное состояние.

## FACT / INFERENCE / RECOMMENDATION / HUMAN_DECISION

- **FACT:** Maya Reed задерживается на 45 минут.
- **INFERENCE:** actor-dependent scenes временно заблокированы.
- **RECOMMENDATION:** конкретный reorder доступной работы.
- **HUMAN_DECISION:** одобрить или отклонить сохраненную рекомендацию.

## Public demo

<https://studiogrid-web-729921508335.europe-west3.run.app>

Путь: Reset Demo → Maya Reed 45m → дождаться PENDING → открыть evidence → APPROVE → сравнить before/after → найти `HUMAN_DECISION` → Coverage Check.

## Data sources

Оригинальный полностью вымышленный пакет **LAST LIGHT**: синтетические актеры, локации, сцены, shots, dependencies, continuity facts и schedule. Реальные клиенты и данные киностудий не используются.

## Что мы узнали

Автономность и полномочия — разные вещи. Агент может выполнить сложную операционную работу, а детерминированный сервис сохранить контроль над высокорисковым изменением. И убедительное agentic demo требует durable evidence: proposal, tool result, state mutation и human decision должны переживать refresh и связываться с remote execution.

## Сложности

- Развернуть ADK multi-agent app в Agent Engine и оставить Tool Server приватным.
- Провести service-to-service identity через public web, private control, managed agent runtime и private tools.
- Совместить deterministic reset с durable Firestore evidence.
- Показать техническое доказательство без credentials, prompts и chain-of-thought.

## Что дальше

Возможные следующие шаги: opt-in production integrations, более богатый constraint solver, resumable event ingestion, уведомления по ролям и расширенная observability. Это roadmap, а не заявления о текущем продукте.
