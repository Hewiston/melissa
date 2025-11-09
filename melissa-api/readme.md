# Melissa API (M1-A)
Запуск:
1) Создай `.env` на основе `.env.example` и вставь API_ED25519_PRIVKEY_B64.
2) Установи зависимости и стартуй сервер:
   - pip install -e .
   - uvicorn src.main:app --reload
Проверки:
- GET /health -> {"ok": true}
- POST /v1/compile -> получает bundle с подписью.
