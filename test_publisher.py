from app.core.settings import Settings
from app.web_ui import WebUiServer
ui = WebUiServer(Settings.load())
print(ui.start_publisher())
