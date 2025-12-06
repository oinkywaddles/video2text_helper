"""
平台配置

维护各平台的默认设置，如 cookie 策略、字幕语言优先级等。
"""

from typing import Dict, List, Any


PLATFORM_CONFIG: Dict[str, Dict[str, Any]] = {
    'bilibili': {
        'use_cookies': True,  # B站需要 cookies 才能访问
        'cookie_browser': 'chrome',
        'subtitle_lang_priority': ['zh-Hans', 'zh-Hant', 'zh', 'en'],
    },
    'youtube': {
        'use_cookies': False,  # YouTube 默认不需要 cookies
        'cookie_browser': 'chrome',
        'subtitle_lang_priority': ['en', 'zh-Hans', 'zh', 'zh-Hant'],
    },
    'default': {
        'use_cookies': False,
        'cookie_browser': 'chrome',
        'subtitle_lang_priority': ['zh-Hans', 'en', 'zh'],
    }
}


def get_platform_config(platform: str) -> Dict[str, Any]:
    """
    获取平台配置

    Args:
        platform: 平台名称 ('bilibili', 'youtube', 等)

    Returns:
        平台配置字典
    """
    return PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG['default'])


def get_default_use_cookies(platform: str) -> bool:
    """获取平台默认的 cookie 使用策略"""
    return get_platform_config(platform).get('use_cookies', False)


def get_cookie_browser(platform: str) -> str:
    """获取平台默认的 cookie 来源浏览器"""
    return get_platform_config(platform).get('cookie_browser', 'chrome')


def get_subtitle_lang_priority(platform: str) -> List[str]:
    """获取平台的字幕语言优先级"""
    return get_platform_config(platform).get('subtitle_lang_priority', ['zh-Hans', 'en'])
