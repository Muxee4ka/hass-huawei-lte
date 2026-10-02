<h1 align="center">Huawei LTE + SMS — форк интеграции для Home Assistant</h1>

<p align="center">
  <a href="https://github.com/Muxee4ka/hass-huawei-lte/actions/workflows/tests.yml"><img src="https://github.com/Muxee4ka/hass-huawei-lte/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS: Custom"></a>
  <a href="https://github.com/Muxee4ka/hass-huawei-lte/releases"><img src="https://img.shields.io/github/v/release/Muxee4ka/hass-huawei-lte?display_name=tag" alt="Release"></a>
</p>

Штатная интеграция **Huawei LTE** из Home Assistant (based on core **2026.9.4**), к которой
добавлено чтение входящих SMS. Домен тот же — `huawei_lte`: форк **заменяет** встроенную
интеграцию, существующая запись, сущности и история сохраняются.

## Что добавлено

- **Event-сущность «Входящее SMS»** (`event.<модем>_incoming_sms`), тип `received`,
  данные: `phone`, `text`, `date`, `index`. Старые SMS при первом запуске событий не дают;
  SMS, пришедшие пока HA был выключен, приходят событиями после старта.
- **Службы:** `huawei_lte.sms_mark_read`, `huawei_lte.sms_delete` (поле `index` — число
  или список), `huawei_lte.sms_delete_read` (удалить все прочитанные).
- **Опция «После получения SMS»:** ничего / пометить прочитанным / удалить.
- **Blueprint «Переслать SMS»** — в Telegram, push или любое действие, с фильтрами
  по отправителю и словам.
- Тексты и номера SMS не попадают в выгрузку диагностики.

[![Импортировать blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FMuxee4ka%2Fhass-huawei-lte%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fhuawei_lte%2Fforward_sms.yaml)

## Установка

1. HACS → Интеграции → ⋮ → Пользовательские репозитории →
   `https://github.com/Muxee4ka/hass-huawei-lte`, категория «Интеграция».
2. Установить «Huawei LTE (SMS fork)», перезапустить HA.
3. В логе появится предупреждение, что `huawei_lte` переопределена custom-интеграцией, — так и задумано.

**Откат:** удалить из HACS и перезапустить HA — вернётся встроенная интеграция.

## Как это работает

Список SMS запрашивается в обычном цикле опроса интеграции (30 с) и только когда
меняется счётчик входящих/непрочитанных, — лишних запросов к модему нет. Новым считается
сообщение, которого нет в журнале последних 200 виденных (ключ — индекс, дата и отправитель);
журнал хранится в `.storage` и переживает рестарт.

## Пример автоматизации

```yaml
triggers:
  - trigger: state
    entity_id: event.e3372_incoming_sms
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.attributes.phone == 'RSCHS' }}"
actions:
  - action: telegram_bot.send_message
    data:
      message: "📩 {{ trigger.to_state.attributes.text }}"
```

## Совместимость

Проверено на Huawei E3372 (HiLink) без пароля. Другие HiLink-модемы и роутеры
(B310, B525, B535 …) должны работать, если их веб-интерфейс показывает SMS;
если модем не отдаёт список SMS, сущность просто не создаётся, остальное работает.

## Разработка

```bash
uv venv --python 3.14 .venv && . .venv/bin/activate
uv pip install -r requirements_test.txt
pytest
```

- `scripts/sync_upstream.sh <версия HA>` — обновить базу ядра (ветка `upstream`),
  затем `git merge upstream`, `scripts/port_core_tests.sh <версия>`,
  `python3 scripts/apply_overlay.py`, `pytest`.
- Еженедельный workflow открывает issue, если `huawei_lte` в новом релизе HA изменилась.
- Свои строки переводов — только в `overlay/translations/`.
- `tests/core/` — тесты ядра для `huawei_lte`, перенесённые без изменений логики.

## Лицензия

Apache-2.0. Изменённая копия кода Home Assistant Core — см. `NOTICE`.
