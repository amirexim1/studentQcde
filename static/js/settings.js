// مدیریت تم و شخصی‌سازی
document.addEventListener('DOMContentLoaded', function() {
    // بارگذاری تنظیمات ذخیره شده
    loadSettings();
    
    // دکمه تغییر تم تاریک/روشن
    setupThemeToggle();
    
    // انتخابگر تم رنگی
    setupColorThemeSelector();
    
    // انتخابگر فونت
    setupFontSelector();
});

// بارگذاری تنظیمات از localStorage
function loadSettings() {
    const savedTheme = localStorage.getItem('darkMode');
    const savedColorTheme = localStorage.getItem('colorTheme');
    const savedFont = localStorage.getItem('fontFamily');
    
    if (savedTheme === 'true') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    
    if (savedColorTheme) {
        document.body.className = savedColorTheme;
    }
    
    if (savedFont) {
        document.documentElement.style.setProperty('--font-body', savedFont);
    }
}

// تنظیم دکمه تغییر تم
function setupThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('darkMode', newTheme === 'dark');
            
            // به‌روزرسانی آیکون
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
        });
    }
}

// تنظیم انتخابگر تم رنگی
function setupColorThemeSelector() {
    const themeSelectors = document.querySelectorAll('.theme-selector');
    themeSelectors.forEach(selector => {
        selector.addEventListener('click', function() {
            const theme = this.dataset.theme;
            document.body.className = theme;
            localStorage.setItem('colorTheme', theme);
            
            // حذف کلاس active از همه
            document.querySelectorAll('.theme-selector').forEach(s => {
                s.classList.remove('active');
            });
            
            // افزودن کلاس active به انتخاب شده
            this.classList.add('active');
        });
    });
}

// تنظیم انتخابگر فونت
function setupFontSelector() {
    const fontSelectors = document.querySelectorAll('.font-selector');
    fontSelectors.forEach(selector => {
        selector.addEventListener('click', function() {
            const font = this.dataset.font;
            document.documentElement.style.setProperty('--font-body', font);
            localStorage.setItem('fontFamily', font);
            
            // حذف کلاس active از همه
            document.querySelectorAll('.font-selector').forEach(s => {
                s.classList.remove('active');
            });
            
            // افزودن کلاس active به انتخاب شده
            this.classList.add('active');
        });
    });
}

// ذخیره تنظیمات کاربر در سرور (اگر لاگین باشد)
async function saveUserSettings(settings) {
    try {
        const response = await fetch('/api/save-settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        });
        
        if (response.ok) {
            console.log('تنظیمات با موفقیت ذخیره شد');
        }
    } catch (error) {
        console.error('خطا در ذخیره تنظیمات:', error);
    }
}

// نمایش مودال تنظیمات
function showSettingsModal() {
    const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
    modal.show();
}

// ریست کردن تنظیمات به پیش‌فرض
function resetSettings() {
    localStorage.removeItem('darkMode');
    localStorage.removeItem('colorTheme');
    localStorage.removeItem('fontFamily');
    
    document.documentElement.removeAttribute('data-theme');
    document.body.className = '';
    document.documentElement.style.setProperty('--font-body', "'Vazirmatn', Tahoma, Arial, sans-serif");
    
    location.reload();
}

// انیمیشن اعداد
function animateNumber(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target.toLocaleString('fa-IR');
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current).toLocaleString('fa-IR');
        }
    }, 16);
}

// فرمت کردن اعداد به فارسی
function toPersianNumber(num) {
    const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    return num.toString().replace(/\d/g, x => persianDigits[x]);
}

// تبدیل عدد انگلیسی به فارسی برای تمام عناصر صفحه
function convertNumbersToPersian() {
    const elements = document.querySelectorAll('.persian-number');
    elements.forEach(el => {
        const text = el.textContent;
        el.textContent = text.replace(/\d+/g, num => toPersianNumber(num));
    });
}

// اجرای تبدیل اعداد هنگام لود صفحه
document.addEventListener('DOMContentLoaded', convertNumbersToPersian);

// مدیریت تایمر پومودورو
class PomodoroTimer {
    constructor(workDuration = 25, breakDuration = 5) {
        this.workDuration = workDuration * 60;
        this.breakDuration = breakDuration * 60;
        this.timeLeft = this.workDuration;
        this.isRunning = false;
        this.isBreak = false;
        this.interval = null;
    }
    
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.interval = setInterval(() => {
            this.timeLeft--;
            this.updateDisplay();
            
            if (this.timeLeft <= 0) {
                this.switchMode();
            }
        }, 1000);
    }
    
    pause() {
        this.isRunning = false;
        clearInterval(this.interval);
    }
    
    reset() {
        this.pause();
        this.isBreak = false;
        this.timeLeft = this.workDuration;
        this.updateDisplay();
    }
    
    switchMode() {
        this.isBreak = !this.isBreak;
        this.timeLeft = this.isBreak ? this.breakDuration : this.workDuration;
        
        // پخش صدا
        this.playNotification();
        
        // نمایش پیام
        const message = this.isBreak ? 'زمان استراحت!' : 'زمان مطالعه!';
        alert(message);
    }
    
    updateDisplay() {
        const display = document.getElementById('timerDisplay');
        if (!display) return;
        
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    playNotification() {
        // می‌توانید صدای دلخواه اضافه کنید
        const audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
        audio.play().catch(e => console.log('Audio play failed:', e));
    }
}

// صادرات برای استفاده جهانی
window.PomodoroTimer = PomodoroTimer;
window.toPersianNumber = toPersianNumber;
window.showSettingsModal = showSettingsModal;
window.resetSettings = resetSettings;
window.animateNumber = animateNumber;
