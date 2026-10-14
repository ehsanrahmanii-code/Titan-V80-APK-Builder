# TITAN PRO V80 — Android APK Builder (Chaquopy)

ساخت کامل APK خودکفا از سیستم ماژولار TITAN PRO V80.

## ساخت APK

1. به تب **Actions** بروید
2. workflow **Build Titan V80 APK** را انتخاب کنید
3. **Run workflow** را بزنید
4. بعد از اتمام، APK را از بخش Artifacts دانلود کنید

APK شامل تمام لایه‌های V80 + numpy + pandas + flask و وابستگی‌ها است.

## ساختار
- `app/src/main/python/titan/` — کل موتور ماژولار V80
- `app/src/main/python/android_main.py` — نقطه شروع سرور روی اندروید
- سرور روی `127.0.0.1:5000` اجرا می‌شود و WebView آن را نشان می‌دهد

نسخه: **80.0.0**
