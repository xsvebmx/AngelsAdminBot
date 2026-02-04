from remnawave import RemnawaveSDK
from config import REMNAWAVE_BASE_URL, REMNAWAVE_TOKEN, EGAMES_COOKIE


def get_sdk() -> RemnawaveSDK:
    return RemnawaveSDK(
        base_url=REMNAWAVE_BASE_URL,
        token=REMNAWAVE_TOKEN,
        custom_headers={
            "Cookie": EGAMES_COOKIE
        }
    )
