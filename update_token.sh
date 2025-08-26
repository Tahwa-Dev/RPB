#!/bin/bash

BOT_PATH="/home/username/bot"  # مسیر ربات رو درست کن
CONFIG_FILE="$BOT_PATH/config.json"

# گرفتن توکن جدید
read -p "Enter new bot token: " NEW_TOKEN

# آپدیت فایل config.json
echo "{\"bot_token\": \"$NEW_TOKEN\"}" > "$CONFIG_FILE"
echo "✅ Bot token updated!"

# ریستارت ربات
echo "♻️ Restarting bot..."
pkill -f bot.py  # اگه ربات در حال اجراست متوقفش می‌کنه
cd "$BOT_PATH"
nohup python3 bot.py > bot.log 2>&1 &

echo "🤖 Bot restarted successfully!"
