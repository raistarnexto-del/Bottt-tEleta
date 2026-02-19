import telebot

# التوكن الخاص بك
TOKEN = '8505457388:AAGZSyQjXYpBNO5ED0O3XMg6dF6vkKpwnis'

# إنشاء كائن البوت
bot = telebot.TeleBot(TOKEN)

# التعامل مع أمر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أنا بوت سريع جداً يعمل بلغة Python ⚡")

# الرد على أي رسالة نصية أخرى
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"لقد أرسلت: {message.text}")

# تشغيل البوت فوراً
print("البوت يعمل الآن...")
bot.infinity_polling()
