import logging
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# =============================
# ⚙️ إعدادات البوت — عدّل هنا
# =============================
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"   # 👈 ضع توكن البوت هنا
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"  # 👈 ضع مفتاح Claude هنا

# =============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a professional football analyst specializing in match predictions.

LANGUAGE RULE: Detect the language of the user's message and respond in the SAME language.
- If the message is in Arabic → respond fully in Arabic
- If the message is in English → respond fully in English
- If mixed → respond in Arabic

When the user sends a match (e.g. Real Madrid vs Barcelona), provide a comprehensive analysis including:

1. 🏆 **Final Prediction** / **التوقع النهائي**: Most likely winner with percentage
2. ⚽ **Score Prediction** / **توقع النتيجة**: Most probable scoreline
3. 📊 **Team Analysis** / **تحليل الفريقين**: Current form, strengths and weaknesses
4. 🎯 **Betting Tips** / **نصائح الرهان**: Best markets (1X2, BTTS, Over/Under 2.5)
5. ⚠️ **Key Alerts** / **تنبيهات مهمة**: Injuries, venue, pressure

Be confident and use your knowledge of both teams' history and recent performance.
Write in a professional and engaging style.

Always end with a disclaimer in the detected language:
- Arabic: ⚠️ هذا التحليل للترفيه فقط، الرهان على مسؤوليتك الشخصية.
- English: ⚠️ This analysis is for entertainment only. Bet responsibly."""


# ---- Bilingual helpers ----
def is_arabic(text: str) -> bool:
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return arabic_chars > len(text) * 0.2


def msg(ar: str, en: str, text: str) -> str:
    return ar if is_arabic(text) else en


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = """🤖 **بوت توقعات المباريات | Match Prediction Bot** ⚽

🇸🇦 مرحباً! أنا بوتك الذكي لتحليل المباريات. أرسل لي اسم المباراة بالعربية أو الإنجليزية وسأرد بنفس لغتك!

🇬🇧 Hello! I'm your AI football analyst. Send me any match in Arabic or English and I'll reply in your language!

📌 **أمثلة | Examples:**
• ريال مدريد vs برشلونة
• Liverpool vs Arsenal
• الأهلي ضد الزمالك
• PSG vs Bayern Munich

⚠️ للترفيه فقط | For entertainment only."""
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = """📖 **المساعدة**

**الأوامر المتاحة:**
/start - بدء البوت
/help - عرض المساعدة

**كيفية الاستخدام:**
أرسل اسم المباراة بأي صيغة:
• الفريق الأول vs الفريق الثاني
• الفريق الأول ضد الفريق الثاني
• الفريق الأول - الفريق الثاني

**أمثلة:**
• بايرن ميونخ vs دورتموند
• الأهلي ضد الزمالك
• PSG vs Real Madrid"""
    await update.message.reply_text(help_msg, parse_mode="Markdown")


async def analyze_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    
    arabic = is_arabic(user_message)

    # رسالة انتظار
    waiting_msg = await update.message.reply_text(
        "⏳ جاري تحليل المباراة... انتظر لحظة! 🔍" if arabic
        else "⏳ Analyzing the match... please wait! 🔍"
    )
    
    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this match and provide your best predictions: {user_message}"
                }
            ]
        )
        
        analysis = response.content[0].text
        
        await waiting_msg.delete()
        await update.message.reply_text(analysis, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        err = (
            "❌ حدث خطأ. تأكد من صحة مفاتيح API والاتصال بالإنترنت، ثم حاول مرة أخرى."
            if arabic else
            "❌ An error occurred. Check your API keys and internet connection, then try again."
        )
        await waiting_msg.edit_text(err)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_match))
    
    logger.info("✅ البوت يعمل الآن!")
    app.run_polling()


if __name__ == "__main__":
    main()
