# انتشار روی GitHub و گرفتن خروجی نصب

## ۱. ساخت مخزن و آپلود

```bash
# در پوشه پروژه
git init
git add .
git commit -m "GGUF Runner v2.3 — complete with Python core"
git branch -M main
git remote add origin https://github.com/YOUR_USER/GGUF-Runner.git
git push -u origin main
```

## ۲. ساخت Release (نصب‌کننده + Portable)

```bash
git tag v2.3.0
git push origin v2.3.0
```

یا از تب **Actions** در GitHub روی workflowهای زیر **Run workflow** بزنید:

| Workflow | خروجی |
|----------|--------|
| `Build Release (portable + llama-server)` | ZIP قابل حمل با `llama-server.exe` |
| `Build NSIS Setup EXE (Offline-ready)` | نصب‌کننده EXE با Python توکار |

فایل‌ها در **Releases** ظاهر می‌شوند.

## ۳. استفاده کاربر نهایی

1. دانلود `GGUF-Runner-Setup-*.exe` یا نسخه portable
2. نصب / استخراج
3. `SETUP.bat` (اگر Python توکار نبود)
4. کپی مدل `.gguf` در `models\`
5. `CHAT.bat`

## نکات

- برای بیلد NSIS روی runner ویندوز، نصب `makensis` در workflow لازم است (در صورت نیاز به workflow اضافه کنید).
- `llama-cpp-python` روی CI ممکن است زمان‌بر باشد؛ اگر wheel آماده نباشد، کاربر یک‌بار با اینترنت `SETUP.bat` را اجرا می‌کند.
