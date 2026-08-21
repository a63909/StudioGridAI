# StudioGrid AI

**AI Production Control Room** — развернутая multi-agent система для реакции на изменения съемочного дня.

Актуальная полная документация, Quick Judge Path и инструкции запуска находятся в [README.md](README.md). Английская версия является основной для All Things Agentic Hackathon.

## Публичное demo

<https://studiogrid-web-729921508335.europe-west3.run.app>

1. Нажать **Reset Demo**.
2. Выбрать **Maya Reed** и запустить задержку **45 минут**.
3. Дождаться реального proposal от Vertex AI Agent Engine.
4. Проверить WHY, evidence, risks, confidence и Technical Evidence.
5. Нажать **Одобрить как человек**.
6. Сравнить schedule BEFORE/AFTER.
7. Найти `HUMAN_DECISION` и обновить страницу для проверки persistence.
8. Запустить Coverage Check и увидеть missing `SH_12`/`SH_13`.

Demo использует полностью вымышленный фильм LAST LIGHT и синтетические данные. Localhost и вход не требуются.

## Что делает система

При `ACTOR_DELAYED` public web через server-side authenticated BFF вызывает private Control API. Тот запускает Google ADK application в Vertex AI Agent Engine. Production Orchestrator направляет событие Schedule Agent; Gemini 3.6 Flash анализирует актеров, сцены, локации, dependencies, порядок и daylight constraints. Агент вызывает typed tool приватного Tool Server и сохраняет PENDING recommendation в Firestore.

AI не может одобрить собственное предложение. Человек APPROVE/REJECT находится за отдельной server-side authority boundary. Approval меняет schedule и создает durable `HUMAN_DECISION`.

Coverage Agent независимо сравнивает planned/completed shots и создает alert для отсутствующих `SH_12` и `SH_13`.

## Проверенный Google Cloud stack

- Gemini 3.6 Flash через Vertex AI
- Google ADK 2.6.3
- Vertex AI Agent Engine
- public Cloud Run `studiogrid-web`
- private Cloud Run `studiogrid-control-api`
- private Cloud Run `studiogrid-tool-server`
- Firestore
- Cloud Trace / safe execution metadata

Архитектура: [source](docs/all-things-agentic/architecture.mmd) · [PNG](docs/all-things-agentic/assets/studiogrid-architecture.png)

## Безопасность

- browser не получает private service URL или token;
- public API принимает только фиксированные demo operations;
- agents не имеют прямого доступа к Firestore;
- typed tools проверяют caller, schema и state transition;
- AGENT/SYSTEM не могут вызвать approval/rejection;
- arbitrary prompt fields запрещены;
- credentials, raw prompts и chain-of-thought не сохраняются в evidence.

Подробнее: [SECURITY.md](SECURITY.md).

## Данные и ограничения

LAST LIGHT — оригинальный fictional production package. Реальные клиенты, studio partnerships, production adoption, измеренная экономия и compliance certification не заявляются. Кнопки demo создают структурированные события; система не заявляет интеграцию с реальными call sheets, email, calendar или IoT.

## Submission materials

- [Official requirements](docs/all-things-agentic/OFFICIAL_REQUIREMENTS.md)
- [English Devpost copy](docs/all-things-agentic/DEVPOST_SUBMISSION_EN.md)
- [Russian reference copy](docs/all-things-agentic/DEVPOST_SUBMISSION_RU.md)
- [Project chronology](docs/all-things-agentic/PROJECT_CHRONOLOGY.md)
- [Video script](docs/all-things-agentic/VIDEO_SCRIPT_EN.md)

Personal eligibility, repository publication, video upload и финальный Devpost submission остаются действиями участника.
