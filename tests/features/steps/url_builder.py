from __future__ import annotations

from urllib.parse import urljoin

from dssgherkin.typings.generic_context_type import AugmentedBehaveContext


def get_cookie_as_str(ctx: AugmentedBehaveContext) -> str:
    assert ctx.dss_cookies
    cookies_as_str = ""
    for c in ctx.dss_cookies:
        name = c.get("name", "")
        value = c.get("value", "")
        if name and value:
            cookies_as_str += f"{name}={value};"

    return cookies_as_str


def get_cookie_as_dict(ctx: AugmentedBehaveContext) -> dict[str, str]:
    assert ctx.dss_cookies
    return {
        cookie.get("name", ""): cookie.get("value", "") for cookie in ctx.dss_cookies
    }


def create_backend_url(ctx: AugmentedBehaveContext):
    return urljoin(ctx.dss_client.host, ctx.current_webapp_path)


def create_api_url(ctx: AugmentedBehaveContext, path: str):
    base = create_backend_url(ctx)
    return urljoin(base, path)
