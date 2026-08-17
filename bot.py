import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app import User, StudySession, ClassSchedule, Exam, Assignment, MeditationSession, IRAN_TZ
import pytz

# Database setup for bot (shared with web app)
DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@localhost/student_tracker')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Bot token
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Conversation states
SELECT_ACTION, ENTER_SUBJECT, ENTER_DURATION, ENTER_TOPIC, ENTER_NOTES = range(5)

# User session storage for conversation
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - welcome message"""
    await update.message.reply_text(
        '👋 سلام! به ربات پیگیری مطالعه خوش آمدید.\n\n'
        'دستورات available:\n'
        '/study - ثبت جلسه مطالعه جدید\n'
        '/meditation - ثبت جلسه مدیتیشن\n'
        '/today - نمایش برنامه امروز\n'
        '/stats - نمایش آمار عملکرد\n'
        '/help - راهنما\n\n'
        'برای شروع یکی از دستورات بالا را انتخاب کنید.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await update.message.reply_text(
        '📚 راهنمای ربات:\n\n'
        '/study - ثبت جلسه مطالعه جدید\n'
        '/meditation - ثبت جلسه مدیتیشن\n'
        '/today - نمایش برنامه امروز (کلاس‌ها، آزمون‌ها، تکالیف)\n'
        '/stats - نمایش آمار عملکرد هفتگی\n'
        '/exams - مشاهده آزمون‌های پیش‌رو\n'
        '/assignments - مشاهده تکالیف\n'
        '/link - اتصال اکانت وب به تلگرام\n\n'
        'برای استفاده از ربات، ابتدا باید اکانت وب خود را متصل کنید.'
    )

async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Link Telegram account to web account"""
    if len(context.args) < 1:
        await update.message.reply_text(
            '❌ لطفاً نام کاربری وب خود را وارد کنید:\n'
            'مثال: /link username'
        )
        return
    
    username = context.args[0]
    telegram_id = str(update.effective_user.id)
    
    session = Session()
    try:
        user = session.query(User).filter_by(username=username).first()
        
        if not user:
            await update.message.reply_text('❌ کاربری با این نام کاربری یافت نشد.')
            return
        
        # Check if this telegram_id is already linked
        existing = session.query(User).filter_by(telegram_id=telegram_id).first()
        if existing and existing.id != user.id:
            await update.message.reply_text('⚠️ این اکانت تلگرام قبلاً به کاربر دیگری متصل است.')
            return
        
        # Link accounts
        user.telegram_id = telegram_id
        session.commit()
        
        await update.message.reply_text(
            f'✅ اکانت شما با موفقیت متصل شد!\n'
            f'کاربر: {user.full_name or user.username}\n\n'
            'حالا می‌توانید از تمام امکانات ربات استفاده کنید.'
        )
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f'❌ خطا: {str(e)}')
    finally:
        session.close()

async def study_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start study session logging"""
    user_sessions[update.effective_user.id] = {'step': 'subject'}
    
    await update.message.reply_text(
        '📚 ثبت جلسه مطالعه جدید\n\n'
        'لطفاً نام درس/موضوع را وارد کنید:'
    )
    
    return ENTER_SUBJECT

async def study_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subject input"""
    user_sessions[update.effective_user.id] = {
        'step': 'duration',
        'subject': update.message.text
    }
    
    await update.message.reply_text(
        '⏱ مدت زمان مطالعه را به دقیقه وارد کنید:\n'
        '(مثال: 45)'
    )
    
    return ENTER_DURATION

async def study_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration input"""
    try:
        duration = int(update.message.text)
        
        user_sessions[update.effective_user.id].update({
            'step': 'topic',
            'duration': duration
        })
        
        await update.message.reply_text(
            '📝 موضوع یا مبحث مطالعه شده را وارد کنید (اختیاری):\n'
            'یا برای رد کردن کلمه "ندارد" را بنویسید.'
        )
        
        return ENTER_TOPIC
    except ValueError:
        await update.message.reply_text('❌ لطفاً یک عدد معتبر وارد کنید:')
        return ENTER_DURATION

async def study_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle topic input"""
    topic = update.message.text if update.message.text != 'ندارد' else None
    
    user_sessions[update.effective_user.id].update({
        'step': 'notes',
        'topic': topic
    })
    
    await update.message.reply_text(
        '📝 یادداشت‌های خود را وارد کنید (اختیاری):\n'
        'یا برای رد کردن کلمه "ندارد" را بنویسید.'
    )
    
    return ENTER_NOTES

async def study_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notes input and save session"""
    notes = update.message.text if update.message.text != 'ندارد' else None
    user_data = user_sessions.get(update.effective_user.id)
    
    # Find user by telegram_id
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=str(update.effective_user.id)).first()
        
        if not user:
            await update.message.reply_text(
                '❌ اکانت شما به وب متصل نیست.\n'
                'لطفاً ابتدا با دستور /link username اکانت خود را متصل کنید.'
            )
            return ConversationHandler.END
        
        # Create study session
        study_session = StudySession(
            user_id=user.id,
            subject=user_data['subject'],
            topic=user_data.get('topic'),
            duration_minutes=user_data['duration'],
            notes=notes,
            end_time=datetime.now(IRAN_TZ)
        )
        
        session.add(study_session)
        session.commit()
        
        await update.message.reply_text(
            '✅ جلسه مطالعه با موفقیت ثبت شد!\n\n'
            f'📚 درس: {user_data["subject"]}\n'
            f'⏱ مدت: {user_data["duration"]} دقیقه\n'
            f'📝 موضوع: {user_data.get("topic", "-")}\n'
            f'📄 یادداشت: {notes or "-"}'
        )
        
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f'❌ خطا در ثبت: {str(e)}')
    finally:
        session.close()
    
    del user_sessions[update.effective_user.id]
    return ConversationHandler.END

async def meditation_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start meditation session logging"""
    await update.message.reply_text(
        '🧘 ثبت جلسه مدیتیشن جدید\n\n'
        'لطفاً مدت زمان را به دقیقه وارد کنید:'
    )
    
    return ENTER_DURATION

async def meditation_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meditation duration and save"""
    try:
        duration = int(update.message.text)
        
        session = Session()
        try:
            user = session.query(User).filter_by(telegram_id=str(update.effective_user.id)).first()
            
            if not user:
                await update.message.reply_text(
                    '❌ اکانت شما به وب متصل نیست.\n'
                    'لطفاً ابتدا با دستور /link username اکانت خود را متصل کنید.'
                )
                return ConversationHandler.END
            
            meditation = MeditationSession(
                user_id=user.id,
                duration_minutes=duration,
                session_type='عمومی'
            )
            
            session.add(meditation)
            session.commit()
            
            await update.message.reply_text(
                '✅ جلسه مدیتیشن ثبت شد!\n\n'
                f'⏱ مدت: {duration} دقیقه\n'
                '🧘 عالی بود!'
            )
        except Exception as e:
            session.rollback()
            await update.message.reply_text(f'❌ خطا: {str(e)}')
        finally:
            session.close()
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('❌ لطفاً یک عدد معتبر وارد کنید:')
        return ENTER_DURATION

async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's schedule"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=str(update.effective_user.id)).first()
        
        if not user:
            await update.message.reply_text(
                '❌ اکانت شما به وب متصل نیست.\n'
                'لطفاً ابتدا با دستور /link username اکانت خود را متصل کنید.'
            )
            return
        
        today = datetime.now(IRAN_TZ).date()
        today_day = today.weekday()
        
        # Get today's classes
        classes = session.query(ClassSchedule).filter_by(
            user_id=user.id,
            day_of_week=today_day
        ).order_by(ClassSchedule.start_time).all()
        
        # Get upcoming exams
        exams = session.query(Exam).filter(
            Exam.user_id == user.id,
            Exam.exam_date >= datetime.now(IRAN_TZ),
            Exam.status == 'upcoming'
        ).order_by(Exam.exam_date).limit(3).all()
        
        # Get pending assignments
        assignments = session.query(Assignment).filter(
            Assignment.user_id == user.id,
            Assignment.due_date >= datetime.now(IRAN_TZ),
            Assignment.status == 'pending'
        ).order_by(Assignment.due_date).limit(3).all()
        
        message = f'📅 برنامه امروز ({today.strftime("%Y/%m/%d")}):\n\n'
        
        if classes:
            message += '🏫 کلاس‌های امروز:\n'
            for cls in classes:
                message += f'  • {cls.subject} | {cls.start_time.strftime("%H:%M")} - {cls.end_time.strftime("%H:%M")}\n'
            message += '\n'
        else:
            message += '🏫 کلاسی برای امروز ندارید.\n\n'
        
        if exams:
            message += '📝 آزمون‌های پیش‌رو:\n'
            for exam in exams:
                message += f'  • {exam.subject} - {exam.exam_date.strftime("%Y/%m/%d %H:%M")}\n'
            message += '\n'
        
        if assignments:
            message += '📚 تکالیف:\n'
            for assign in assignments:
                message += f'  • {assign.title} - مهلت: {assign.due_date.strftime("%Y/%m/%d")}\n'
        
        if not exams and not assignments:
            message += '✨ آزمون یا تکلیفی برای نمایش وجود ندارد.'
        
        await update.message.reply_text(message)
    finally:
        session.close()

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show weekly statistics"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=str(update.effective_user.id)).first()
        
        if not user:
            await update.message.reply_text(
                '❌ اکانت شما به وب متصل نیست.\n'
                'لطفاً ابتدا با دستور /link username اکانت خود را متصل کنید.'
            )
            return
        
        today = datetime.now(IRAN_TZ).date()
        week_start = today - timedelta(days=today.weekday())
        
        # Study stats
        study_sessions = session.query(StudySession).filter(
            StudySession.user_id == user.id,
            StudySession.start_time >= week_start
        ).all()
        
        total_study_minutes = sum(s.duration_minutes or 0 for s in study_sessions)
        total_sessions = len(study_sessions)
        
        # Meditation stats
        meditations = session.query(MeditationSession).filter(
            MeditationSession.user_id == user.id,
            MeditationSession.session_date >= week_start
        ).all()
        
        total_meditation_minutes = sum(m.duration_minutes or 0 for m in meditations)
        total_meditations = len(meditations)
        
        # Completed items
        completed_assignments = session.query(Assignment).filter_by(
            user_id=user.id,
            status='completed'
        ).count()
        
        completed_exams = session.query(Exam).filter_by(
            user_id=user.id,
            status='completed'
        ).count()
        
        message = (
            '📊 آمار عملکرد این هفته:\n\n'
            f'📚 جلسات مطالعه: {total_sessions}\n'
            f'⏱ مجموع زمان مطالعه: {total_study_minutes} دقیقه\n\n'
            f'🧘 جلسات مدیتیشن: {total_meditations}\n'
            f'🕐 مجموع زمان مدیتیشن: {total_meditation_minutes} دقیقه\n\n'
            f'✅ تکالیف انجام‌شده: {completed_assignments}\n'
            f'📝 آزمون‌های داده‌شده: {completed_exams}\n\n'
            '💪 ادامه بده!'
        )
        
        await update.message.reply_text(message)
    finally:
        session.close()

async def show_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show upcoming exams"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=str(update.effective_user.id)).first()
        
        if not user:
            await update.message.reply_text('❌ اکانت شما متصل نیست. از /link استفاده کنید.')
            return
        
        exams = session.query(Exam).filter(
            Exam.user_id == user.id,
            Exam.exam_date >= datetime.now(IRAN_TZ),
            Exam.status == 'upcoming'
        ).order_by(Exam.exam_date).limit(10).all()
        
        if not exams:
            await update.message.reply_text('🎉 هیچ آزمونی پیش‌رو نیست!')
            return
        
        message = '📝 آزمون‌های پیش‌رو:\n\n'
        for exam in exams:
            message += f'• {exam.subject}\n'
            message += f'  تاریخ: {exam.exam_date.strftime("%Y/%m/%d %H:%M")}\n'
            if exam.exam_type:
                message += f'  نوع: {exam.exam_type}\n'
            message += '\n'
        
        await update.message.reply_text(message)
    finally:
        session.close()

async def show_assignments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending assignments"""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=str(update.effective_user.id)).first()
        
        if not user:
            await update.message.reply_text('❌ اکانت شما متصل نیست. از /link استفاده کنید.')
            return
        
        assignments = session.query(Assignment).filter(
            Assignment.user_id == user.id,
            Assignment.status == 'pending',
            Assignment.due_date >= datetime.now(IRAN_TZ)
        ).order_by(Assignment.due_date).limit(10).all()
        
        if not assignments:
            await update.message.reply_text('🎉 همه تکالیف انجام شده!')
            return
        
        message = '📚 تکالیف در انتظار:\n\n'
        for assign in assignments:
            days_left = (assign.due_date.date() - datetime.now(IRAN_TZ).date()).days
            message += f'• {assign.title}\n'
            message += f'  درس: {assign.subject}\n'
            message += f'  مهلت: {assign.due_date.strftime("%Y/%m/%d")}'
            if days_left <= 2:
                message += f' ⚠️ ({days_left} روز مانده)'
            message += '\n\n'
        
        await update.message.reply_text(message)
    finally:
        session.close()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    if update.effective_user.id in user_sessions:
        del user_sessions[update.effective_user.id]
    
    await update.message.reply_text('❌ عملیات لغو شد.')
    return ConversationHandler.END

def main():
    """Main function to run the bot"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Study conversation handler
    study_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('study', study_start)],
        states={
            ENTER_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, study_subject)],
            ENTER_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, study_duration)],
            ENTER_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, study_topic)],
            ENTER_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, study_notes)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Meditation conversation handler
    meditation_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('meditation', meditation_start)],
        states={
            ENTER_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, meditation_duration)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('link', link_account))
    app.add_handler(study_conv_handler)
    app.add_handler(meditation_conv_handler)
    app.add_handler(CommandHandler('today', show_today))
    app.add_handler(CommandHandler('stats', show_stats))
    app.add_handler(CommandHandler('exams', show_exams))
    app.add_handler(CommandHandler('assignments', show_assignments))
    
    # Run bot
    print('Bot is running...')
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
