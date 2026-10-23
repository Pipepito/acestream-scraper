"""Only fixed application-owned messages may cross the Telegram API boundary."""
class TelegramActionError(ValueError):
    pass
