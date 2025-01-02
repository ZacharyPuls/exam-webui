from typing import Final

NICEGUI_STORAGE_SECRET: Final[str] = ""

ENTRA_CLIENT_ID: Final[str] = "2ca41128-31df-4961-962e-8ad7aafec3fd"
ENTRA_CLIENT_SECRET: Final[str] = ""
ENTRA_TENANT_ID: Final[str] = "9936d6dc-55b6-427a-a12c-f0a4510ff303"
ENTRA_APPLICATION_SCOPE: Final[list[str]] = ["User.ReadBasic.All"]
ENTRA_AUTHORITY: Final[str] = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}"
ENTRA_GRAPH_ENDPOINT: Final[str] = "https://graph.microsoft.com/v1.0/users"
ENTRA_LOGOUT_ENDPOINT: Final[str] = (
    f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/oauth2/v2.0/logout"
)
ENTRA_JWKS_URL: Final[str] = (
    f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys"
)
OAUTH_REDIRECT_URI: Final[str] = "/auth/callback"
