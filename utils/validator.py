import pandas as pd
import re

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


def validate_contacts_file(uploaded_file):

    errors = []
    valid_contacts = []

    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        return None, [f"❌ Не удалось прочитать файл: {str(e)}"]

    df.columns = [str(col).strip().lower() for col in df.columns]

    required_cols = ['email', 'name']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return None, [f"❌ В файле отсутствуют обязательные колонки: {', '.join(missing_cols)}"]

    df['name'] = df['name'].fillna("Уважаемый клиент")
    if 'company' in df.columns:
        df['company'] = df['company'].fillna("")
    else:
        df['company'] = ""
    seen_emails = set()

    for idx, row in df.iterrows():
        row_num = idx + 2
        raw_email = str(row['email']).strip()

        if pd.isna(row['email']) or raw_email == "" or raw_email.lower() == "nan":
            errors.append(f"Строка {row_num}: Пустой email-адрес.")
            continue

        if not re.match(EMAIL_REGEX, raw_email):
            errors.append(f"Строка {row_num}: Некорректный формат email ({raw_email}).")
            continue

        if raw_email in seen_emails:
            errors.append(f"Строка {row_num}: Дубликат email ({raw_email}) игнорирован.")
            continue

        seen_emails.add(raw_email)

        valid_contacts.append({
            "email": raw_email,
            "name": str(row['name']).strip(),
            "company": str(row['company']).strip()
        })

    return valid_contacts, errors