from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from src.storage.devrepo import activate_device_by_code

router = APIRouter()

_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Link Device</title>
  <style>
    body {{ font-family: system-ui, sans-serif; padding: 24px; }}
    form {{ display: flex; gap: 8px; }}
    input {{ padding: 8px; font-size: 16px; }}
    button {{ padding: 8px 12px; font-size: 16px; cursor: pointer; }}
    .msg {{ margin-top: 16px; }}
  </style>
</head>
<body>
  <h1>Link Device</h1>
  <p>Вставьте код из консоли движка (например, <code>ABCD-1234</code>):</p>
  <form method="post" action="/link">
    <input type="text" name="user_code" placeholder="XXXX-YYYY" required />
    <button type="submit">Активировать</button>
  </form>
  {message}
</body>
</html>
"""

@router.get("/link", response_class=HTMLResponse)
def link_form():
    return _HTML.format(message="")

@router.post("/link", response_class=HTMLResponse)
def link_submit(user_code: str = Form(...)):
    device_id = activate_device_by_code(user_code, user_id="u_demo")
    if device_id:
        msg = f'<div class="msg">✅ Устройство привязано: <code>{device_id}</code>. Можно вернуться в консоль движка.</div>'
    else:
        msg = '<div class="msg">❌ Код не найден или срок истёк. Проверьте и попробуйте снова.</div>'
    return _HTML.format(message=msg)
