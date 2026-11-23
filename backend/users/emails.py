import base64
from functools import lru_cache

from django.conf import settings

LOGO_CONTENT_ID = 'drako'
LOGO_PATH = settings.BASE_DIR / 'drako.png'

BRAND_RED = '#e63946'
BRAND_INK = '#1a1a2e'
BRAND_PAPER = '#f8f4ee'


@lru_cache(maxsize=1)
def _logo_base64() -> str:
    with open(LOGO_PATH, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def _format_expiry(seconds: int) -> str:
    days = seconds // 86400
    if days >= 1:
        return f'{days} día' + ('s' if days != 1 else '')
    hours = seconds // 3600
    if hours >= 1:
        return f'{hours} hora' + ('s' if hours != 1 else '')
    minutes = max(seconds // 60, 1)
    return f'{minutes} minuto' + ('s' if minutes != 1 else '')


def build_password_reset_email(user, reset_link: str) -> tuple[str, list[dict]]:
    """Devuelve (html, attachments) para el correo de reset de contraseña."""
    greeting_name = f' {user.first_name}' if user.first_name else ''
    expiry_text = _format_expiry(settings.PASSWORD_RESET_TIMEOUT)

    html = f'''\
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{BRAND_PAPER}; padding:32px 16px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <tr>
    <td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:500px; background-color:#ffffff; border-radius:16px; overflow:hidden;">
        <tr>
          <td align="center" style="padding:40px 32px 8px 32px;">
            <img src="cid:{LOGO_CONTENT_ID}" width="160" height="160" alt="HanziApp" style="display:block; width:160px; height:160px;" />
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:16px 32px 0 32px;">
            <h1 style="margin:0; font-size:22px; line-height:28px; font-weight:700; color:{BRAND_INK};">
              Restablece tu contraseña
            </h1>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:16px 32px 0 32px;">
            <p style="margin:0; font-size:15px; line-height:22px; color:#555555;">
              Hola{greeting_name}, recibimos una solicitud para restablecer la contraseña de tu
              cuenta de HanziApp. Haz clic en el siguiente botón para elegir una nueva.
            </p>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:28px 32px 0 32px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td align="center" bgcolor="{BRAND_RED}" style="border-radius:12px;">
                  <a href="{reset_link}" target="_blank"
                     style="display:inline-block; padding:14px 32px; font-size:15px; font-weight:600; color:#ffffff; text-decoration:none; border-radius:12px;">
                    Restablecer contraseña
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:24px 32px 0 32px;">
            <p style="margin:0; font-size:13px; line-height:20px; color:#999999;">
              Este link expira en {expiry_text}. Si no solicitaste esto, puedes ignorar este correo.
            </p>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:32px 32px 40px 32px;">
            <p style="margin:0; font-size:12px; line-height:18px; color:#bbbbbb;">
              HanziApp · hanziapp.co
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
'''

    attachments = [
        {
            'content': _logo_base64(),
            'filename': 'drako.png',
            'content_id': LOGO_CONTENT_ID,
        },
    ]

    return html, attachments
