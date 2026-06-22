import telebot
from telebot import types
import time

# التوكن الخاص بي
import os
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MY_CHAT_ID = '8010266076'
bot = telebot.TeleBot(BOT_TOKEN)


# قاموس لحفظ الحالات وبيانات الطلب المعل
user_orders = {}

# أسعار الخدمات (الكمية: السعر)
PRICES = {
    'subs':     {5: 1500, 10: 3000, 15: 4500, 20: 6000},     # الاشتراكات
    'likes':    {5: 1000, 10: 2000, 15: 3000, 20: 4000},     # الإعجابات
    'comments': {5: 1000, 10: 2000, 15: 3000, 20: 4000},     # التعليقات
    'views':    {5: 1000, 10: 2000, 15: 3000, 20: 4000}      # المشاهدات
}

# أسماء الخدمات بالعربية للعرض
SERVICE_NAMES = {
    'likes': '👍 إعجابات',
    'views': '👁️ مشاهدات',
    'comments': '💬 تعليقات',
    'subs': '➕ اشتراكات'
}

# دالة تحديث العداد وضبط النص ليطابق شروط تليجرام (أقل من 120 حرف)
def update_user_count(chat_id=None):
    filename = "users.txt"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            users = f.read().splitlines()
    except FileNotFoundError:
        users = []

    if chat_id and str(chat_id) not in users:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"{chat_id}\n")
        users.append(str(chat_id))
        
    total_users = len(users)
    
    try:
        # نص مختصر، شامل واحترافي يلتزم بحدود الـ 120 حرفاً تماماً لضمان عدم حدوث خطأ
        short_bio = f"GDS STORE 💥 لخدمات الفيسبوك المتكاملة وسرعة التنفيذ. للتواصل: @Hatemgds | 👥 {total_users}"
        
        bot.set_my_short_description(short_bio)
    except Exception as e:
        print(f"فشل تحديث النبذة: {e}")

# 1. الترحيب والقائمة الرئيسية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id in user_orders:
        del user_orders[message.chat.id]
        
    # تحديث الوصف والعداد لحظياً فور دخول المستخدم الجديد
    update_user_count(message.chat.id)
        
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🛍️ خدمات الفيسبوك', '💳 طرق الدفع')
    markup.row('👤 حسابي', '📞 خدمة العملاء')
    bot.send_message(message.chat.id, f"مرحباً بك يا {message.from_user.first_name} في GDS STORE!", reply_markup=markup)

# 2. عرض خدمات الفيسبوك
@bot.message_handler(func=lambda message: message.text == '🛍️ خدمات الفيسبوك')
def show_services(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👍 إعجابات", callback_data='cat_likes'),
               types.InlineKeyboardButton("👁️ مشاهدات", callback_data='cat_views'))
    markup.add(types.InlineKeyboardButton("💬 تعليقات", callback_data='cat_comments'),
               types.InlineKeyboardButton("➕ اشتراكات", callback_data='cat_subs'))
    bot.send_message(message.chat.id, "اختر نوع الخدمة المطلوبة:", reply_markup=markup)

# 3. معالجة الأزرار التفاعلية (Inline Buttons)
@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_') or call.data.startswith('qty_') or call.data.startswith('pay_') or call.data == 'finish_order')
def callback_query(call):
    chat_id = call.message.chat.id

    if call.data.startswith('cat_'):
        service_type = call.data.split('_')[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        service_prices = PRICES.get(service_type, {})
        for qty, price in service_prices.items():
            button_text = f"📦 {qty} {SERVICE_NAMES[service_type]} 💰 بسعر {price} SDG"
            markup.add(types.InlineKeyboardButton(button_text, callback_data=f'qty_{service_type}_{qty}_{price}'))
            
        bot.edit_message_text("اختر الكمية والسعر المناسب لك:", chat_id, call.message.message_id, reply_markup=markup)
    
    elif call.data.startswith('qty_'):
        _, service_type, qty, price = call.data.split('_')
        user_orders[chat_id] = {
            'service': SERVICE_NAMES[service_type],
            'qty': qty,
            'price': price,
            'status': 'waiting_payment_info',
            'data_collected': []
        }
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("بنكك", callback_data='pay_bankak'),
                   types.InlineKeyboardButton("أوكاش", callback_data='pay_okash'),
                   types.InlineKeyboardButton("فوري", callback_data='pay_fawry'),
                   types.InlineKeyboardButton("كاشي لايت", callback_data='pay_mycash'),
                   types.InlineKeyboardButton("باينانس", callback_data='pay_binance'))
                   
        bot.edit_message_text(f"🛍️ لقد اخترت: {qty} {SERVICE_NAMES[service_type]}\n💰 الإجمالي: {price} SDG\n\nالآن اختر وسيلة الدفع لإتمام عملية التحويل:", 
                              chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith('pay_'):
        data = {
            'pay_bankak': '🏦 بنكك (بنك الخرطوم)\nرقم الحساب: 8582360\nالاسم: حاتم علي بشير علي',
            'pay_okash': '🏦 أوكاش (بنك أمدرمان)\nرقم الحساب: 1812910\nالاسم: حاتم علي بشير علي',
            'pay_fawry': '🏦 فوري (بنك فيصل)\nرقم الحساب: 52204934\nالاسم: حاتم علي بشير علي',
            'pay_mycash': '📱 كاشي لايت\nرقم الحساب: 300332575\nالاسم: حاتم علي بشير علي',
            'pay_binance': '💎 باينانس (Binance)\nID: 1252557005\nالاسم: HATEM GDS'
        }
        payment_info = data.get(call.data, "خطأ في البيانات")
        instructions = (
            f"{payment_info}\n\n"
            f"⚠️ **الخطوة الأخيرة:**\n"
            f"1️⃣ أرسل رابط المنشور هنا.\n"
            f"2️⃣ أرسل لقطة شاشة لإشعار التحويل.\n"
            f"(يمكنك إرسالهما متتابعين، وعند الانتهاء اضغط على زر التأكيد بالأسفل👇)"
        )
        bot.send_message(chat_id, instructions, parse_mode="Markdown")

    elif call.data == 'finish_order':
        if chat_id in user_orders and user_orders[chat_id].get('data_collected'):
            order_data = user_orders[chat_id]
            collected_text = "\n".join([item for item in order_data['data_collected'] if not item.startswith("🖼️")])
            
            alert_text = (
                f"🚨 **طلب جديد مكتمل وجاهز للتنفيذ!**\n"
                f"----------------------------------------\n"
                f"👤 **الزبون:** {chat_id}\n"
                f"📦 **الخدمة:** {order_data['service']}\n"
                f"🔢 **الكمية:** {order_data['qty']}\n"
                f"💰 **المبلغ:** {order_data['price']} SDG\n"
                f"🔗 **النصوص والروابط المرسلة:**\n{collected_text if collected_text else 'لم يرسل نصاً'}\n"
                f"----------------------------------------\n"
                f"💡 *راجع لقطات الشاشة التي وصلتك في المحادثة ثم نفذ الطلب وأرسل الدليل للزبون.*"
            )
            
            try:
                bot.send_message(MY_CHAT_ID, alert_text, parse_mode="Markdown")
                bot.answer_callback_query(call.id, "✅ تم إرسال طلبك بنجاح!")
                bot.send_message(chat_id, "✅ تم إرسال طلبك بالكامل للإدارة بنجاح! جاري المراجعة والتنفيذ، انتظر لقطة شاشة التأكيد قريباً.")
                
                with open("orders.txt", "a", encoding="utf-8") as f:
                    f.write(f"المستخدم: {chat_id}, الخدمة: {order_data['service']}, الكمية: {order_data['qty']} - طلب مكتمل\n")
            except Exception as e:
                print(f"فشل إرسال التنبيه الختامي: {e}")
            
            del user_orders[chat_id]
        else:
            bot.answer_callback_query(call.id, "⚠️ الرجاء إرسال الرابط وصورة الإشعار أولاً!", show_alert=True)

# 4. معالجة الأزرار الثابتة العامة
@bot.message_handler(func=lambda message: message.text in ['💳 طرق الدفع', '📞 خدمة العملاء', '👤 حسابي'])
def handle_menu_buttons(message):
    if message.text == '💳 طرق الدفع':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("بنكك", callback_data='pay_bankak'),
                   types.InlineKeyboardButton("أوكاش", callback_data='pay_okash'),
                   types.InlineKeyboardButton("فوري", callback_data='pay_fawry'),
                   types.InlineKeyboardButton("كاشي لايت", callback_data='pay_mycash'),
                   types.InlineKeyboardButton("باينانس", callback_data='pay_binance'))
        bot.send_message(message.chat.id, "اختر وسيلة الدفع:", reply_markup=markup)
    elif message.text == '📞 خدمة العملاء':
        bot.send_message(message.chat.id, "للتواصل: @Hatemgds")
    elif message.text == '👤 حسابي':
        bot.send_message(message.chat.id, "معلومات حسابك:\nالرصيد الحالي: 0.00$")

# 5. استلام الصور والنصوص بشكل متتابع وتجميعها من الزبائن
@bot.message_handler(content_types=['photo', 'text'], func=lambda message: message.chat.id in user_orders and user_orders[message.chat.id].get('status') == 'waiting_payment_info')
def receive_payment_and_link(message):
    chat_id = message.chat.id
    
    if 'data_collected' not in user_orders[chat_id]:
        user_orders[chat_id]['data_collected'] = []

    if message.content_type == 'photo':
        user_orders[chat_id]['data_collected'].append("🖼️ [تم إرسال صورة إشعار]")
        photo_id = message.photo[-1].file_id
        
        caption_info = f"📸 لقطة شاشة تابعة لطلب العميل:\nالزبون: {chat_id}"
        if message.caption:
            caption_info += f"\n📝 الملاحظة المرفقة مع الصورة: {message.caption}"
            user_orders[chat_id]['data_collected'].append(message.caption)
            
        try:
            bot.send_photo(MY_CHAT_ID, photo_id, caption=caption_info)
        except Exception as e:
            print(f"فشل توجيه الصورة: {e}")
            
    else:
        user_orders[chat_id]['data_collected'].append(message.text)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تأكيد وإرسال الطلب بالإشعار", callback_data='finish_order'))
    bot.send_message(chat_id, "📥 تم استلام رسالتك بنجاح في نظام التجميع.\nإذا انتهيت من إرسال (الرابط + صورة الإشعار)، اضغط على الزر أدناه لتأكيد وإرسال طلبك النهائي للادارة:", reply_markup=markup)

# 6. أمر الأدمن: المراسلة المباشرة
@bot.message_handler(commands=['send'])
def direct_send(message):
    if str(message.chat.id) != MY_CHAT_ID:
        return
    
    parts = message.text.split(maxsplit=2)
    
    if len(parts) == 3:
        user_id = parts[1].strip()
        text_to_send = parts[2].strip()
        try:
            bot.send_message(user_id, f"✉️ رسالة من الإدارة بخصوص طلبك:\n\n{text_to_send}")
            bot.reply_to(message, f"🚀 تم إرسال الرسالة بنجاح إلى الزبون: {user_id}")
        except Exception as e:
            bot.reply_to(message, f"❌ فشل الإرسال للزبون {user_id}، السبب: {e}")
            
    elif len(parts) == 2 and message.reply_to_message:
        user_id = parts[1].strip()
        try:
            if message.reply_to_message.content_type == 'photo':
                photo_id = message.reply_to_message.photo[-1].file_id
                caption = message.caption if message.caption else "✅ تم تنفيذ طلبك بنجاح! إليك لقطة شاشة التأكيد من الإدارة."
                bot.send_photo(user_id, photo_id, caption=caption)
                bot.reply_to(message, f"🚀 تم إرسال لقطة الشاشة بنجاح إلى الزبون: {user_id}")
            elif message.reply_to_message.content_type == 'text':
                bot.send_message(user_id, f"✉️ رسالة من الإدارة بخصوص طلبك:\n\n{message.reply_to_message.text}")
                bot.reply_to(message, f"🚀 تم إرسال النص بنجاح إلى الزبون: {user_id}")
        except Exception as e:
            bot.reply_to(message, f"❌ فشل الإرسال للزبون {user_id}، السبب: {e}")
            
    else:
        bot.reply_to(message, "⚠️ **طريقة الاستخدام الخطأ!**\n\n"
                              "1️⃣ **لإرسال نص:** اكتب `/send رقم_الزبون نص الرسالة`\n"
                              "2️⃣ **لإرسال صورة:** قم بعمل رد (Reply) على الصورة واكتب `/send رقم_الزبون`")

# 7. أمر الأدمن: الرد التلقائي عبر الـ Reply
@bot.message_handler(content_types=['photo', 'text'], func=lambda message: str(message.chat.id) == MY_CHAT_ID and message.reply_to_message)
def reply_to_user_via_bot(message):
    if message.text and message.text.startswith('/send'):
        return
        
    try:
        original_text = message.reply_to_message.text if message.reply_to_message.text else message.reply_to_message.caption
        if original_text and "الزبون:" in original_text:
            user_id = original_text.split("الزبون:")[1].split("\n")[0].strip()
            
            if message.content_type == 'photo':
                bot.send_photo(user_id, message.photo[-1].file_id, caption="✅ تم تنفيذ طلبك بنجاح! إليك لقطة شاشة التأكيد من الإدارة.")
                bot.reply_to(message, f"🚀 تم إرسال لقطة الشاشة بنجاح إلى الزبون: {user_id}")
            elif message.content_type == 'text':
                bot.send_message(user_id, f"✉️ رسالة من الإدارة بخصوص طلبك:\n\n{message.text}")
                bot.reply_to(message, f"🚀 تم إرسال الرسالة بنجاح إلى الزبون: {user_id}")
        else:
            bot.reply_to(message, "⚠️ تأكد من عمل Reply على رسالة التنبيه الأصلية التي تحتوي على حقل 'الزبون:'.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء الإرسال: {e}")

# تحديث الوصف قسرياً وفورياً بمجرد تشغيل الكود وتفادي الأخطاء
try:
    update_user_count()
    print("تم تحديث النبذة بنجاح دون تخطي الحد المسموح!")
except Exception as e:
    print(f"حدث خطأ أثناء التحديث التلقائي: {e}")

# تشغيل مستمر
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        time.sleep(5)
