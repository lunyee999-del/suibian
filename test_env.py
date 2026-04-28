from app.core.settings import Settings
s = Settings.load()
print(f"DRY_RUN is {s.dry_run}")
