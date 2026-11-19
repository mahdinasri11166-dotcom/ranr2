# GGUF Runner v2.9

**تیم توسعهٔ نو** — مهدی طریری · محسن طریفی

رانر محلی GGUF با چت دسکتاپ، Agent + Approval Gate، OSINT دفاعی، Case، RAG محلی، Plugin و گزارش HTML.

## نصب

```bat
SETUP.bat
FirstRun.bat
:: یا: GGUF-Runner.bat → W
:: مدل .gguf را در models\ بگذارید (ویزارد راهنمایی می‌کند)
CHAT.bat
```

Doctor: `scripts\doctor.bat`

## قابلیت‌های ۲.۶

- سشن: `/sessions` `/open` `/export` ذخیره و خروجی Markdown
- Case OSINT: `/case list|new|export` + ابزارهای `case_*`
- RAG محلی: `/buildrag` `/rag <query>` از books/memory/cases
- OSINT: دامنه، crt.sh، ایمیل DNS، username موازی، metadata، گزارش فارسی
- Plugin در `workspace\plugins\`
- Browser فقط‌خواندنی با Approval
- نصب‌کننده NSIS آفلاین + portable (GitHub Actions با fail سخت)
- ایجنت ۴ لایه (کد، وب، حافظه، سیستم)
- API سازگار با OpenAI روی `http://127.0.0.1:8787/v1` (`scripts\start_openai_api.bat`)
- گراف دامنه SVG داخل گزارش HTML

## عمداً غیرفعال

brute-force و اسکنر آسیب‌پذیری تهاجمی — همیشه `blocked`.

## مجوز

MIT
