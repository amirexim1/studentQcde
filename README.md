# Student Study Tracker - وبسایت و ربات تلگرامی پیگیری مطالعه

یک سیستم کامل برای ثبت و پیگیری مطالعه با امکان مدیریت برنامه کلاسی، آزمون‌ها، تکالیف، مدیتیشن و گزارش عملکرد.

## ویژگی‌ها

### وبسایت
- ✅ ثبت‌نام و ورود کاربران
- 📖 ثبت جلسات مطالعه با جزئیات کامل
- 📅 برنامه هفتگی کلاس‌ها
- 📝 مدیریت آزمون‌ها و تکالیف
- 🧘 ثبت جلسات مدیتیشن
- 📊 گزارش عملکرد با نمودارهای تعاملی
- 🌐 رابط کاربری فارسی و راست‌چین

### ربات تلگرام
- 🤖 اتصال اکانت تلگرام به وبسایت
- 📖 ثبت سریع جلسات مطالعه
- 🧘 ثبت جلسات مدیتیشن
- 📅 مشاهده برنامه روزانه
- 📊 دریافت آمار عملکرد
- 📝 مشاهده آزمون‌ها و تکالیف

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.8+
- MySQL Database
- Telegram Bot Token (برای ربات)

### مراحل نصب

1. **کلون کردن پروژه**
```bash
git clone <repository-url>
cd studentQcde
```

2. **نصب وابستگی‌ها**
```bash
pip install -r requirements.txt
```

3. **تنظیم متغیرهای محیطی**

متغیرهای زیر را در Railway یا محیط اجرا تنظیم کنید:

```bash
# کلید امنیتی
SECRET_KEY=your-secret-key-here

# آدرس دیتابیس MySQL
DATABASE_URL=mysql+pymysql://username:password@host:port/database_name

# توکن ربات تلگرام (اختیاری)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

4. **اجرای وبسایت**
```bash
python app.py
```

5. **اجرای ربات تلگرام** (اختیاری)
```bash
python bot.py
```

## ساختار پروژه

```
studentQcde/
├── app.py              # برنامه اصلی Flask
├── bot.py              # ربات تلگرام
├── templates/          # قالب‌های HTML
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── study_log.html
│   ├── schedule.html
│   ├── exams.html
│   ├── assignments.html
│   ├── meditation.html
│   └── reports.html
├── static/             # فایل‌های استاتیک
└── requirements.txt    # وابستگی‌ها
```

## اتصال به Railway

1. پروژه را به GitHub Push کنید
2. در Railway یک پروژه جدید بسازید
3. Repository خود را متصل کنید
4. یک MySQL Database اضافه کنید
5. متغیرهای محیطی را تنظیم کنید
6. Deploy کنید

## دستورات ربات تلگرام

- `/start` - شروع ربات
- `/study` - ثبت جلسه مطالعه جدید
- `/meditation` - ثبت جلسه مدیتیشن
- `/today` - نمایش برنامه امروز
- `/stats` - آمار عملکرد هفتگی
- `/exams` - آزمون‌های پیش‌رو
- `/assignments` - تکالیف در انتظار
- `/link username` - اتصال اکانت وب به تلگرام
- `/help` - راهنما

## پایگاه داده

پروژه از جداول زیر استفاده می‌کند:
- `users` - اطلاعات کاربران
- `study_sessions` - جلسات مطالعه
- `class_schedules` - برنامه کلاسی
- `exams` - آزمون‌ها
- `assignments` - تکالیف
- `meditation_sessions` - جلسات مدیتیشن

## تکنولوژی‌ها

- **Backend**: Flask, SQLAlchemy
- **Database**: MySQL
- **Frontend**: Bootstrap 5, Chart.js
- **Bot**: python-telegram-bot
- **Deployment**: Railway

## لایسنس

این پروژه برای استفاده شخصی و آموزشی توسعه یافته است.
