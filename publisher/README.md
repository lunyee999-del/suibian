# Xiaohongshu Publisher Service

This service exposes a minimal internal publishing endpoint:

```text
POST /internal/publish/xiaohongshu
```

Default behavior:

- `DRY_RUN=true`
- no real publishing actions
- returns a mock publish result

To switch to real browser automation later:

1. Install dependencies with `npm install`
2. Set `DRY_RUN=false`
3. Make sure the persistent browser profile is already logged into Xiaohongshu creator center

