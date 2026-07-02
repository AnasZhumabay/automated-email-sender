import streamlit as st
import datetime
import requests

from utils.validator import validate_contacts_file

st.set_page_config(page_title="Smart Campaign Hub", page_icon="✉️", layout="centered")


st.sidebar.title("⚙️ Настройки интеграции")
webhook_url = st.sidebar.text_input(
    "n8n Webhook URL",
    value="https://YOUR_N8N_HOST/webhook/launch-campaign",
    help="Вставьте Production URL из вашего вебхука в n8n"
)

if "step" not in st.session_state:
    st.session_state.step = 1

if "campaign" not in st.session_state:
    st.session_state.campaign = {
        "title": "",
        "subject": "",
        "schedule_type": "Мгновенно",
        "send_at": None,
        "html_content": "",
        "contacts": None
    }


def go_next(): st.session_state.step += 1


def go_back(): st.session_state.step -= 1



st.title("🚀 Мастер Email-Рассылок")
st.caption("Создание, валидация и отправка кампаний напрямую в n8n")

step_names = {1: "📝 Параметры", 2: "🎨 Контент", 3: "👥 Аудитория", 4: "🏁 Запуск"}
st.info(f"**Шаг {st.session_state.step} из 4:** {step_names[st.session_state.step]}")
st.progress(st.session_state.step / 4)
st.divider()


if st.session_state.step == 1:
    st.subheader("Основные параметры рассылки")

    title = st.text_input(
        "Техническое название рассылки",
        value=st.session_state.campaign["title"],
        placeholder="Например: Новогодняя распродажа 2026"
    )

    subject = st.text_input(
        "Тема письма (увидит получатель)",
        value=st.session_state.campaign["subject"],
        placeholder="Скидки уже ждут тебя, {{name}}!"
    )

    st.write("---")
    st.subheader("🕒 Время запуска")
    stype = st.radio("Когда запустить рассылку?", ["Мгновенно", "Запланировать дату/время"])

    send_at = None
    if stype == "Запланировать дату/время":
        d = st.date_input("Выберите дату", datetime.date.today())
        t = st.time_input("Выберите время", datetime.time(12, 0))
        send_at = datetime.datetime.combine(d, t).isoformat()

    st.session_state.campaign["title"] = title
    st.session_state.campaign["subject"] = subject
    st.session_state.campaign["schedule_type"] = stype
    st.session_state.campaign["send_at"] = send_at


elif st.session_state.step == 2:
    st.subheader("Редактор HTML-письма")
    st.caption("Доступные переменные для подстановки: `{{name}}`, `{{company}}`, `{{email}}`")

    html = st.text_area(
        "HTML Код письма",
        value=st.session_state.campaign["html_content"],
        height=300,
        placeholder="<h1>Привет, {{name}}!</h1>\n<p>Специальное предложение для компании {{company}}.</p>"
    )

    st.session_state.campaign["html_content"] = html

    if html:
        with st.expander("👀 Интерактивный предпросмотр (Live Preview)", expanded=True):
            st.components.v1.html(html, height=250, scrolling=True)


elif st.session_state.step == 3:
    st.subheader("👥 Загрузка списка контактов")
    st.caption("Загрузите файл `.xlsx` или `.csv`. Обязательно наличие колонок: `email` и `name`.")

    file_picker = st.file_uploader("Перетащите файл базы сюда", type=["xlsx", "xls", "csv"])

    if file_picker is not None:
        contacts, errors = validate_contacts_file(file_picker)

        if contacts is not None:
            st.session_state.campaign["contacts"] = contacts

            col_ok, col_err = st.columns(2)
            col_ok.metric("Валидных контактов к отправке", len(contacts))
            col_err.metric("Найдено ошибок / дубликатов", len(errors))

            if errors:
                with st.expander("⚠️ Лог предупреждений (строки пропущены)", expanded=False):
                    for err in errors:
                        st.warning(err)

            if contacts:
                st.write("### 📋 Сформированная база JSON:")
                st.dataframe(contacts, use_container_width=True)
        else:
            for err in errors:
                st.error(err)
            st.session_state.campaign["contacts"] = None
    else:
        st.session_state.campaign["contacts"] = None
        st.info("💡 Ожидание загрузки файла базы данных...")


elif st.session_state.step == 4:
    st.subheader("🏁 Финальный контроль")
    st.write("Проверьте параметры манифеста перед отправкой в n8n.")

    payload = {
        "meta": {
            "title": st.session_state.campaign["title"],
            "subject": st.session_state.campaign["subject"],
            "schedule": st.session_state.campaign["send_at"]
        },
        "content": {
            "html": st.session_state.campaign["html_content"]
        },
        "recipients": st.session_state.campaign["contacts"]
    }

    col1, col2 = st.columns(2)
    col1.markdown(f"**Название:** {payload['meta']['title']}")
    col1.markdown(f"**Тема письма:** {payload['meta']['subject']}")

    sch_time = payload['meta']['schedule'] if payload['meta']['schedule'] else "Мгновенно"
    col2.markdown(f"**Время старта:** `{sch_time}`")
    col2.markdown(f"**Всего писем:** `{len(payload['recipients']) if payload['recipients'] else 0}`")

    st.write("---")
    with st.expander("🔍 Посмотреть полный JSON-пакет отправки"):
        st.json(payload)


st.divider()
col_back, col_space, col_next = st.columns([1, 2, 1])

with col_back:
    if st.session_state.step > 1:
        st.button("⬅️ Назад", on_click=go_back, use_container_width=True)

with col_next:
    if st.session_state.step < 4:
        is_disabled = False
        if st.session_state.step == 1:
            is_disabled = not st.session_state.campaign["title"] or not st.session_state.campaign["subject"]
        elif st.session_state.step == 2:
            is_disabled = not st.session_state.campaign["html_content"]
        elif st.session_state.step == 3:
            is_disabled = st.session_state.campaign["contacts"] is None or len(
                st.session_state.campaign["contacts"]) == 0

        st.button("Вперед ➡️", on_click=go_next, disabled=is_disabled, use_container_width=True)
    else:
        if st.button("🔥 ЗАПУСТИТЬ", type="primary", use_container_width=True):
            if "YOUR_N8N_HOST" in webhook_url:
                st.error("❌ Сначала укажите корректный URL вебхука n8n в левой панели!")
            else:
                with st.spinner("Передача данных в сценарий n8n..."):
                    try:
                        response = requests.post(webhook_url, json=payload, timeout=15)

                        if response.status_code in [200, 201]:
                            st.balloons()
                            st.success(f"🎉 Успешно! n8n принял задачу. Код ответа: {response.status_code}")
                        else:
                            st.error(f"❌ Ошибка n8n: Сервер вернул код {response.status_code}. Ответ: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Не удалось связаться с n8n. Проверьте сеть или URL. Ошибка: {str(e)}")