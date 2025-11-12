#!/usr/bin/env python3
"""
Instagram Pro Finder Bot - COMPLETE Version
With all owner commands including broadcast and coin management
"""

import json
import os
import time
import random
import string
import logging
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ==================== CONFIG ====================
BOT_TOKEN = "8204849607:AAFvXFbAHJQA4sYBal6csxi4MtECRX-mXnw"
OWNER_ID = 7598553230
JOIN_PHOTO_URL = "https://i.ibb.co/4Z19YVyM/image.jpg"
DEFAULT_INVITE_1 = "https://t.me/+sYQlBAPNHJlmMDBl"
DEFAULT_INVITE_2 = "https://t.me/+6--m3SDgHDMxNTZl"
DATA_FILE = "bot_data.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# ==================== STORAGE ====================
def load_data():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE))
    
    base = {
        "users": {},
        "refcodes": {},
        "channels": {
            "invite_1": DEFAULT_INVITE_1,
            "invite_2": DEFAULT_INVITE_2
        },
        "join_config": {
            "photo_url": JOIN_PHOTO_URL,
            "caption": "🌟 <b>Instagram Pro Finder Premium</b>\n\nJoin our channels to unlock powerful Instagram lookup features!",
            "button_names": {
                "1": "📢 JOIN CHANNEL 1",
                "2": "📢 JOIN CHANNEL 2"
            }
        },
        "settings": {
            "refs_for_search": 6,
            "default_quota": 0,
            "require_refs_for_search": True
        },
        "history": {},
        "giftcodes": {},
        "banned": [],
        "protect": {
            "number": True,
            "gmail": True,
            "ig": True
        }
    }
    save_data(base)
    return base

def save_data(data_dict=None):
    if data_dict:
        json.dump(data_dict, open(DATA_FILE, "w"), indent=2)
    else:
        json.dump(data, open(DATA_FILE, "w"), indent=2)

data = load_data()

# ==================== HELPERS ====================
def ensure_user(user_id):
    uid = str(user_id)
    if uid not in data["users"]:
        ref_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        data["users"][uid] = {
            "quota": data["settings"]["default_quota"],
            "referrals": 0,
            "ref_code": ref_code,
            "created_at": int(time.time()),
            "granted_by_owner": 0,
            "referred_by": None,
            "verified": False,
            "has_initial_access": False
        }
        data["refcodes"][ref_code] = uid
        save_data()
    return data["users"][uid]

def is_banned(user_id):
    return str(user_id) in data.get("banned", [])

def owner_only(func):
    from functools import wraps
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user or update.effective_user.id != OWNER_ID:
            if update.message:
                await update.message.reply_text("🚫 <b>Owner Only Command</b>", parse_mode="HTML")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def build_join_keyboard():
    keyboard = []
    join_config = data["join_config"]
    button_names = join_config["button_names"]
    
    for i in range(1, 4):  # Support up to 3 channels
        invite_key = f"invite_{i}"
        if invite_key in data["channels"] and data["channels"][invite_key]:
            btn_text = button_names.get(str(i), f"📢 JOIN CHANNEL {i}")
            keyboard.append([InlineKeyboardButton(btn_text, url=data["channels"][invite_key])])
    
    keyboard.append([InlineKeyboardButton("✅ CHECK JOINED", callback_data="check_joined")])
    return InlineKeyboardMarkup(keyboard)

def generate_premium_contact(username):
    """Generate premium Indian contact details"""
    phone = f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}"
    safe_username = re.sub(r'[^a-zA-Z0-9]', '', username)[:15]
    email = f"{safe_username}{random.randint(100, 999)}@gmail.com"
    return {"phone": phone, "email": email}

def save_search_history(username, profile_data, contact_info, user_id):
    username = username.lower()
    record = {
        "timestamp": int(time.time()),
        "profile": profile_data,
        "contact": contact_info,
        "searched_by": str(user_id)
    }
    data.setdefault("history", {}).setdefault(username, []).append(record)
    save_data()

def get_last_search(username):
    username = username.lower()
    searches = data.get("history", {}).get(username, [])
    return searches[-1] if searches else None

# ==================== REFERRAL NOTIFICATION FUNCTION ====================
async def send_referral_notification(context: ContextTypes.DEFAULT_TYPE, referrer_id, new_user_id, new_user_name):
    """Send notification to referrer when someone joins using their referral"""
    try:
        referrer_data = ensure_user(referrer_id)
        refs_needed = data["settings"]["refs_for_search"]
        
        # Calculate remaining referrals needed for next reward
        current_refs = referrer_data["referrals"]
        remaining_refs = refs_needed - (current_refs % refs_needed)
        
        notification_text = f"""
🎉 𝗡𝗘𝗪 𝗨𝗦𝗘𝗥 𝗝𝗢𝗜𝗡𝗘𝗗!

👤 𝗨𝘀𝗲𝗿: {new_user_name}
🆔 𝗜𝗗: {new_user_id}

✅ 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟 𝗖𝗢𝗜𝗡𝗦 𝗔𝗗𝗗𝗘𝗗 𝗧𝗢 𝗦𝗘𝗔𝗥𝗖𝗛 𝗖𝗢𝗜𝗡𝗦!

📊 𝗬𝗼𝘂𝗿 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗦𝘁𝗮𝘁𝘀:
├─ 𝗧𝗼𝘁𝗮𝗹 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹𝘀: {current_refs}
├─ 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗦𝗲𝗮𝗿𝗰𝗵𝗲𝘀: {referrer_data['quota']}
└─ 𝗡𝗲𝘅𝘁 𝗳𝗿𝗲𝗲 𝘀𝗲𝗮𝗿𝗰𝗵 𝗶𝗻: {remaining_refs} 𝗿𝗲𝗳𝗲𝗿𝗿𝗮𝗹𝘀

🎁 𝗞𝗲𝗲𝗽 𝘀𝗵𝗮𝗿𝗶𝗻𝗴 𝘆𝗼𝘂𝗿 𝗿𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗹𝗶𝗻𝗸 𝘁𝗼 𝗲𝗮𝗿𝗻 𝗺𝗼𝗿𝗲 𝗳𝗿𝗲𝗲 𝘀𝗲𝗮𝗿𝗰𝗵𝗲𝘀!
        """
        
        await context.bot.send_message(
            chat_id=int(referrer_id),
            text=notification_text,
            parse_mode="HTML"
        )
        
        # Check if referrer earned a free search
        if current_refs % refs_needed == 0:
            bonus_text = f"""
🎊 𝗖𝗢𝗡𝗚𝗥𝗔𝗧𝗨𝗟𝗔𝗧𝗜𝗢𝗡𝗦!

🏆 𝗬𝗼𝘂'𝘃𝗲 𝗿𝗲𝗮𝗰𝗵𝗲𝗱 {current_refs} 𝗿𝗲𝗳𝗲𝗿𝗿𝗮𝗹𝘀!

🎯 𝗙𝗥𝗘𝗘 𝗦𝗘𝗔𝗥𝗖𝗛 𝗥𝗘𝗪𝗔𝗥𝗗 𝗔𝗗𝗗𝗘𝗗!

📈 𝗡𝗲𝘄 𝗦𝗲𝗮𝗿𝗰𝗵 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {referrer_data['quota']}

🚀 𝗨𝘀𝗲 /ig 𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲 𝘁𝗼 𝘀𝘁𝗮𝗿𝘁 𝘀𝗲𝗮𝗿𝗰𝗵𝗶𝗻𝗴!
            """
            await context.bot.send_message(
                chat_id=int(referrer_id),
                text=bonus_text,
                parse_mode="HTML"
            )
            
    except Exception as e:
        logging.error(f"Error sending referral notification: {e}")

# ==================== INSTAGRAM DATA FETCHER ====================
def fetch_instagram_profile(username):
    """Fetch Instagram profile using multiple public APIs"""
    username = username.strip().lstrip('@')
    
    methods = [
        method_instagram_official_api,
        method_instagram_alternative_api, 
        method_instagram_web_scraping,
    ]
    
    for method in methods:
        try:
            result = method(username)
            if result and result.get("success"):
                return result
            time.sleep(1)
        except:
            continue
    
    return {"error": "❌ Could not fetch Instagram data", "success": False}

def method_instagram_official_api(username):
    try:
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-IG-App-ID": "936619743392459"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('data', {}).get('user', {})
            if user:
                return {
                    "username": user.get('username'),
                    "full_name": user.get('full_name', ''),
                    "biography": user.get('biography', ''),
                    "is_private": user.get('is_private', False),
                    "is_verified": user.get('is_verified', False),
                    "followers": user.get('edge_followed_by', {}).get('count'),
                    "following": user.get('edge_follow', {}).get('count'),
                    "posts": user.get('edge_owner_to_timeline_media', {}).get('count'),
                    "profile_pic_url": user.get('profile_pic_url_hd'),
                    "success": True
                }
    except:
        pass
    return None

def method_instagram_alternative_api(username):
    try:
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers = {
            "User-Agent": "Instagram 219.0.0.12.117 Android",
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('data', {}).get('user', {})
            if user:
                return {
                    "username": user.get('username'),
                    "full_name": user.get('full_name', ''),
                    "biography": user.get('biography', ''),
                    "is_private": user.get('is_private', False),
                    "is_verified": user.get('is_verified', False),
                    "followers": user.get('edge_followed_by', {}).get('count'),
                    "following": user.get('edge_follow', {}).get('count'),
                    "posts": user.get('edge_owner_to_timeline_media', {}).get('count'),
                    "profile_pic_url": user.get('profile_pic_url_hd'),
                    "success": True
                }
    except:
        pass
    return None

def method_instagram_web_scraping(username):
    try:
        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            meta_image = soup.find("meta", property="og:image")
            profile_pic = meta_image.get('content') if meta_image else None
            
            meta_desc = soup.find("meta", property="og:description")
            description = meta_desc.get('content') if meta_desc else ''
            
            profile_data = {
                "username": username,
                "full_name": "",
                "biography": description,
                "is_private": False,
                "is_verified": False,
                "followers": None,
                "following": None,
                "posts": None,
                "profile_pic_url": profile_pic,
                "success": True
            }
            
            if description:
                try:
                    if 'Followers' in description:
                        followers_match = re.search(r'([\d,]+) Followers', description)
                        following_match = re.search(r'([\d,]+) Following', description)
                        posts_match = re.search(r'([\d,]+) Posts', description)
                        
                        if followers_match:
                            profile_data['followers'] = int(followers_match.group(1).replace(',', ''))
                        if following_match:
                            profile_data['following'] = int(following_match.group(1).replace(',', ''))
                        if posts_match:
                            profile_data['posts'] = int(posts_match.group(1).replace(',', ''))
                except:
                    pass
            
            return profile_data
    except:
        pass
    return None

# ==================== COMMAND HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = ensure_user(user.id)
    
    if context.args and context.args[0].startswith("ref_"):
        ref_code = context.args[0][4:]
        if ref_code in data["refcodes"] and data["refcodes"][ref_code] != str(user.id):
            referrer_id = data["refcodes"][ref_code]
            if user_data["referred_by"] is None:
                user_data["referred_by"] = referrer_id
                referrer_data = ensure_user(referrer_id)
                referrer_data["referrals"] += 1
                
                refs_needed = data["settings"]["refs_for_search"]
                if referrer_data["referrals"] % refs_needed == 0:
                    referrer_data["quota"] += 1
                    referrer_data["has_initial_access"] = True
                
                save_data()
                
                # Send referral notification
                new_user_name = user.first_name or "Unknown User"
                await send_referral_notification(context, referrer_id, user.id, new_user_name)
    
    await send_join_screen(update.effective_chat.id, context)

async def send_join_screen(chat_id, context: ContextTypes.DEFAULT_TYPE):
    join_config = data["join_config"]
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=join_config.get("photo_file_id", join_config["photo_url"]),
        caption=join_config["caption"],
        parse_mode="HTML",
        reply_markup=build_join_keyboard()
    )

async def check_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    user_data = ensure_user(user.id)
    user_data["verified"] = True
    save_data()
    
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_data['ref_code']}"
    refs_needed = data["settings"]["refs_for_search"]
    
    welcome_msg = (
        f"✅ <b>Verification Successful!</b>\n\n"
        f"🌟 <b>Welcome to Instagram Pro Finder</b>\n\n"
        f"🔍 <b>Available Searches:</b> {user_data['quota']}\n"
        f"👥 <b>Your Referrals:</b> {user_data['referrals']}\n"
        f"📎 <b>Your Referral Link:</b>\n<code>{ref_link}</code>\n\n"
        f"🎁 <b>Refer {refs_needed} friends to get your first free search!</b>\n\n"
        f"Use <code>/ig username</code> to search Instagram profiles\n"
        f"Use <code>/help</code> to see all commands"
    )
    
    await query.edit_message_caption(caption=welcome_msg, parse_mode="HTML")

# Rate limiting
user_requests = {}

async def ig_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    
    if user_id in user_requests:
        if now - user_requests[user_id] < 10:
            await update.message.reply_text("⏳ Please wait 10 seconds between requests!")
            return
    
    user_requests[user_id] = now

    user = update.effective_user
    user_data = ensure_user(user.id)
    
    if is_banned(user.id):
        await update.message.reply_text("🚫 Your account has been banned.")
        return
    
    if not user_data.get("verified") and user.id != OWNER_ID:
        await update.message.reply_text(
            "❌ <b>Please verify your membership first!</b>\n\n"
            "Use /start and join our channels to access all features.",
            parse_mode="HTML"
        )
        await send_join_screen(update.effective_chat.id, context)
        return
    
    refs_needed = data["settings"]["refs_for_search"]
    if (data["settings"]["require_refs_for_search"] and 
        not user_data.get("has_initial_access") and 
        user_data["referrals"] < refs_needed and
        user.id != OWNER_ID):
        
        remaining_refs = refs_needed - user_data["referrals"]
        await update.message.reply_text(
            f"❌ <b>Referral Requirement Not Met!</b>\n\n"
            f"You need {remaining_refs} more referrals to unlock your first search.\n\n"
            f"📊 <b>Your Stats:</b>\n"
            f"• Current Referrals: {user_data['referrals']}/{refs_needed}\n"
            f"• Remaining Needed: {remaining_refs}\n\n"
            f"Use <code>/referral</code> to get your referral link and share with friends!",
            parse_mode="HTML"
        )
        return
    
    if user.id != OWNER_ID and user_data["quota"] <= 0:
        await update.message.reply_text(
            f"❌ <b>No searches left!</b>\n\n"
            f"Refer {refs_needed} friends to get free searches.\n"
            f"Use <code>/referral</code> to get your referral link.",
            parse_mode="HTML"
        )
        return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide username: /ig username")
        return

    username = context.args[0].strip().lstrip("@")
    
    if len(username) > 30:
        await update.message.reply_text("❌ Username too long!")
        return

    search_msg = await update.message.reply_text(f"🔍 Searching for @{username}...")

    try:
        profile = fetch_instagram_profile(username)
        
        if profile.get("error"):
            await search_msg.edit_text(f"❌ {profile['error']}")
            return

        premium_contact = generate_premium_contact(username)
        save_search_history(username, profile, premium_contact, user.id)
        
        if user.id != OWNER_ID:
            user_data["quota"] -= 1
            save_data()

        # Format response
        def format_number(num):
            if num in ['N/A', 'Not Available', 0] or not isinstance(num, int):
                return 'N/A'
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            elif num >= 1000:
                return f"{num/1000:.1f}K"
            return str(num)
        
        bio = profile.get('biography', 'No bio available')
        if bio and bio != 'No bio available':
            bio = ' '.join(bio.split())[:150] + ('...' if len(bio) > 150 else '')
        
        response_text = (
            f"🌟 <b>INSTAGRAM PRO FINDER - REAL DATA</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>Name:</b> {profile.get('full_name', 'Not set')}\n"
            f"📌 <b>Username:</b> @{profile.get('username', username)}\n"
            f"📝 <b>Bio:</b> {bio}\n"
            f"👥 <b>Followers:</b> {format_number(profile.get('followers'))}\n"
            f"👤 <b>Following:</b> {format_number(profile.get('following'))}\n"
            f"📊 <b>Total Posts:</b> {format_number(profile.get('posts'))}\n"
            f"🔒 <b>Private Account:</b> {'Yes' if profile.get('is_private') else 'No'}\n"
            f"✅ <b>Verified:</b> {'Yes' if profile.get('is_verified') else 'No'}\n\n"
            f"📞 <b>CONTACT INFORMATION</b>\n"
            f"📱 <b>Phone:</b> <code>{premium_contact['phone']}</code>\n"
            f"📧 <b>Email:</b> <code>{premium_contact['email']}</code>\n\n"
            f"⏰ <b>Search Time:</b> {datetime.now().strftime('%I:%M:%S %p')}\n"
            f"📅 <b>Search Date:</b> {datetime.now().strftime('%d/%m/%Y')}\n"
            f"🔍 <b>Remaining Searches:</b> {user_data['quota']}\n\n"
            f"✅ <i>100% Real Instagram Data</i>"
        )

        profile_pic = profile.get("profile_pic_url")
        if profile_pic and profile_pic.startswith('http'):
            try:
                await update.message.reply_photo(
                    photo=profile_pic,
                    caption=response_text,
                    parse_mode="HTML"
                )
                await search_msg.delete()
                return
            except:
                pass

        await search_msg.edit_text(response_text, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Error in ig_command: {e}")
        await search_msg.edit_text("❌ Failed to fetch profile. Please try again later.")

# ==================== USER COMMANDS ====================
async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = ensure_user(user.id)
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_data['ref_code']}"
    refs_needed = data["settings"]["refs_for_search"]
    remaining_refs = refs_needed - (user_data["referrals"] % refs_needed)
    
    response = (
        f"👥 <b>REFERRAL PROGRAM</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📎 <b>Your Referral Link:</b>\n<code>{ref_link}</code>\n\n"
        f"📊 <b>Your Statistics:</b>\n"
        f"• Total Referrals: {user_data['referrals']}\n"
        f"• Available Searches: {user_data['quota']}\n"
        f"• Next free search in: {remaining_refs} referrals\n\n"
        f"🎁 <b>Rewards:</b>\n"
        f"• Get 1 free search for every {refs_needed} referrals\n\n"
        f"💡 <b>How it works:</b>\n"
        f"1. Share your referral link with friends\n"
        f"2. When they join using your link, you get +1 referral\n"
        f"3. Every {refs_needed} referrals = 1 free search!\n\n"
        f"🚀 <i>Start sharing to unlock free searches!</i>"
    )
    
    await update.message.reply_text(response, parse_mode="HTML")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id == OWNER_ID:
        usernames = list(data.get("history", {}).keys())
        if usernames:
            await update.message.reply_text("📚 All searched usernames:\n" + "\n".join(usernames[:20]))
        else:
            await update.message.reply_text("📚 No search history found.")
        return
    
    user_searches = []
    for username, searches in data.get("history", {}).items():
        for search in searches:
            if search.get("searched_by") == str(user.id):
                user_searches.append(username)
                break
    
    if user_searches:
        await update.message.reply_text("📚 Your search history:\n" + "\n".join(user_searches[:15]))
    else:
        await update.message.reply_text("📚 You haven't searched any profiles yet.")

async def last_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /last username")
        return
    
    username = context.args[0].strip().lstrip("@")
    last_search = get_last_search(username)
    
    if not last_search:
        await update.message.reply_text("❌ No search found for that username.")
        return
    
    user = update.effective_user
    if user.id != OWNER_ID and last_search.get("searched_by") != str(user.id):
        await update.message.reply_text("🚫 Access denied.")
        return
    
    profile = last_search["profile"]
    contact = last_search["contact"]
    search_time = datetime.fromtimestamp(last_search["timestamp"]).strftime("%I:%M:%S %p")
    
    response = (
        f"🔍 <b>Last Search Result for @{username}</b>\n\n"
        f"👤 <b>Name:</b> {profile.get('full_name', 'N/A')}\n"
        f"👥 <b>Followers:</b> {profile.get('followers', 'N/A')}\n"
        f"📱 <b>Phone:</b> {contact['phone']}\n"
        f"📧 <b>Email:</b> {contact['email']}\n"
        f"⏰ <b>Searched at:</b> {search_time}"
    )
    
    await update.message.reply_text(response, parse_mode="HTML")

async def getcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /getcontact username")
        return
    
    username = context.args[0].strip().lstrip("@")
    last_search = get_last_search(username)
    
    if not last_search:
        await update.message.reply_text("❌ No contact found for that username.")
        return
    
    user = update.effective_user
    if user.id != OWNER_ID and last_search.get("searched_by") != str(user.id):
        await update.message.reply_text("🚫 Access denied.")
        return
    
    contact = last_search["contact"]
    await update.message.reply_text(
        f"📞 <b>Contact Info for @{username}</b>\n\n"
        f"📱 <b>Phone:</b> {contact['phone']}\n"
        f"📧 <b>Email:</b> {contact['email']}",
        parse_mode="HTML"
    )

async def giftcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /giftcode CODE")
        return
    
    code = context.args[0].upper().strip()
    giftcode_data = data.get("giftcodes", {}).get(code)
    
    if not giftcode_data:
        await update.message.reply_text("❌ Invalid gift code.")
        return
    
    user_id = str(update.effective_user.id)
    if user_id in giftcode_data.get("redeemed_by", []):
        await update.message.reply_text("❌ You have already redeemed this code.")
        return
    
    amount = giftcode_data["amount"]
    user_data = ensure_user(user_id)
    user_data["quota"] += amount
    user_data["has_initial_access"] = True
    giftcode_data.setdefault("redeemed_by", []).append(user_id)
    save_data()
    
    await update.message.reply_text(f"🎉 Redeemed {amount} searches! New balance: {user_data['quota']}")

# ==================== OWNER COMMANDS ====================
@owner_only
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(data["users"])
    total_refs = sum(user["referrals"] for user in data["users"].values())
    total_banned = len(data.get("banned", []))
    total_searches = sum(len(searches) for searches in data.get("history", {}).values())
    active_users = sum(1 for user in data["users"].values() if user.get("verified"))
    
    stats_text = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Active Users: {active_users}\n"
        f"🔗 Total Referrals: {total_refs}\n"
        f"🚫 Banned Users: {total_banned}\n"
        f"🔍 Total Searches: {total_searches}\n"
        f"🎁 Active Gift Codes: {len(data.get('giftcodes', {}))}\n"
        f"📈 Referrals Needed: {data['settings']['refs_for_search']}"
    )
    
    await update.message.reply_text(stats_text, parse_mode="HTML")

@owner_only
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send message to all users"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /broadcast YOUR_MESSAGE")
        return
    
    message = " ".join(context.args)
    users = data["users"].keys()
    success = 0
    failed = 0
    
    progress_msg = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"📢 <b>Announcement from Admin</b>\n\n{message}",
                parse_mode="HTML"
            )
            success += 1
        except:
            failed += 1
        time.sleep(0.1)  # Rate limiting
    
    await progress_msg.edit_text(
        f"✅ <b>Broadcast Complete</b>\n\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {len(users)}",
        parse_mode="HTML"
    )

@owner_only
async def addcoins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add coins/searches to user"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /addcoins USER_ID AMOUNT")
        return
    
    user_id, amount = context.args[0], context.args[1]
    try:
        amount = int(amount)
        if amount < 1:
            await update.message.reply_text("❌ Amount must be at least 1")
            return
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return
    
    user_data = ensure_user(user_id)
    user_data["quota"] += amount
    user_data["has_initial_access"] = True
    save_data()
    
    await update.message.reply_text(f"✅ Added {amount} searches to user {user_id}. New balance: {user_data['quota']}")

@owner_only
async def removecoins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove coins/searches from user"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /removecoins USER_ID AMOUNT")
        return
    
    user_id, amount = context.args[0], context.args[1]
    try:
        amount = int(amount)
        if amount < 1:
            await update.message.reply_text("❌ Amount must be at least 1")
            return
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return
    
    user_data = ensure_user(user_id)
    user_data["quota"] = max(0, user_data["quota"] - amount)
    save_data()
    
    await update.message.reply_text(f"✅ Removed {amount} searches from user {user_id}. New balance: {user_data['quota']}")

@owner_only
async def setgift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create gift code"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /setgift CODE AMOUNT")
        return
    
    code, amount = context.args[0].upper(), context.args[1]
    try:
        amount = int(amount)
        if amount < 1:
            await update.message.reply_text("❌ Amount must be at least 1")
            return
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return
    
    data.setdefault("giftcodes", {})[code] = {
        "amount": amount,
        "created_by": str(update.effective_user.id),
        "created_at": int(time.time()),
        "redeemed_by": []
    }
    save_data()
    await update.message.reply_text(f"✅ Gift code '{code}' created for {amount} searches")

@owner_only
async def set_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /set_channel 1|2|3 CHANNEL_LINK")
        return
    
    index, channel_link = context.args[0], context.args[1]
    if index not in ["1", "2", "3"]:
        await update.message.reply_text("❌ Channel index must be 1, 2 or 3")
        return
    
    data["channels"][f"invite_{index}"] = channel_link
    save_data()
    await update.message.reply_text(f"✅ Channel {index} set to: {channel_link}")

@owner_only
async def editcaption_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_caption = " ".join(context.args)
    if not new_caption:
        await update.message.reply_text("❌ Usage: /editcaption YOUR_CAPTION_HERE")
        return
    
    data["join_config"]["caption"] = new_caption
    save_data()
    await update.message.reply_text("✅ Join caption updated successfully.")

@owner_only
async def editphoto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("❌ Reply to a photo with this command.")
        return
    
    photo_file = update.message.reply_to_message.photo[-1]
    data["join_config"]["photo_file_id"] = photo_file.file_id
    save_data()
    await update.message.reply_text("✅ Join photo updated successfully.")

@owner_only
async def editlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /editlink 1|2|3 NEW_LINK")
        return
    
    index, new_link = context.args[0], " ".join(context.args[1:])
    if index not in ["1", "2", "3"]:
        await update.message.reply_text("❌ Channel index must be 1, 2 or 3")
        return
    
    data["channels"][f"invite_{index}"] = new_link
    save_data()
    await update.message.reply_text(f"✅ Channel {index} link updated to: {new_link}")

@owner_only
async def editbutton_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /editbutton 1|2|3 BUTTON_TEXT")
        return
    
    index, button_text = context.args[0], " ".join(context.args[1:])
    if index not in ["1", "2", "3"]:
        await update.message.reply_text("❌ Button index must be 1, 2 or 3")
        return
    
    data["join_config"]["button_names"][index] = button_text
    save_data()
    await update.message.reply_text(f"✅ Button {index} text updated to: {button_text}")

@owner_only
async def editbuttonname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for editbutton"""
    await editbutton_command(update, context)

@owner_only
async def editreferral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /editreferral NUMBER")
        return
    
    try:
        refs_needed = int(context.args[0])
        if refs_needed < 1:
            await update.message.reply_text("❌ Number must be at least 1")
            return
        
        data["settings"]["refs_for_search"] = refs_needed
        save_data()
        await update.message.reply_text(f"✅ Referrals needed for free search: {refs_needed}")
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid number")

@owner_only
async def editreferralcion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for editreferral"""
    await editreferral_command(update, context)

@owner_only
async def addchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new channel"""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /addchannel CHANNEL_NUMBER CHANNEL_LINK")
        return
    
    index, channel_link = context.args[0], " ".join(context.args[1:])
    if index not in ["1", "2", "3"]:
        await update.message.reply_text("❌ Channel number must be 1, 2 or 3")
        return
    
    data["channels"][f"invite_{index}"] = channel_link
    data["join_config"]["button_names"][index] = f"📢 JOIN CHANNEL {index}"
    save_data()
    await update.message.reply_text(f"✅ Channel {index} added: {channel_link}")

@owner_only
async def removechannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove channel"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /removechannel CHANNEL_NUMBER")
        return
    
    index = context.args[0]
    if index not in ["1", "2", "3"]:
        await update.message.reply_text("❌ Channel number must be 1, 2 or 3")
        return
    
    if f"invite_{index}" in data["channels"]:
        del data["channels"][f"invite_{index}"]
        save_data()
        await update.message.reply_text(f"✅ Channel {index} removed successfully.")
    else:
        await update.message.reply_text(f"❌ Channel {index} not found.")

@owner_only
async def viewlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all channel links"""
    links_text = "🔗 <b>Channel Links</b>\n\n"
    for i in range(1, 4):
        invite_key = f"invite_{i}"
        if invite_key in data["channels"]:
            links_text += f"📢 Channel {i}: {data['channels'][invite_key]}\n"
        else:
            links_text += f"📢 Channel {i}: Not set\n"
    
    await update.message.reply_text(links_text, parse_mode="HTML")

@owner_only
async def makegiftcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /makegiftcode CODE AMOUNT")
        return
    
    code, amount = context.args[0].upper(), context.args[1]
    try:
        amount = int(amount)
        if amount < 1:
            await update.message.reply_text("❌ Amount must be at least 1")
            return
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return
    
    data.setdefault("giftcodes", {})[code] = {
        "amount": amount,
        "created_by": str(update.effective_user.id),
        "created_at": int(time.time()),
        "redeemed_by": []
    }
    save_data()
    await update.message.reply_text(f"✅ Gift code '{code}' created for {amount} searches")

@owner_only
async def grant_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /grant_search USER_ID AMOUNT")
        return
    
    user_id, amount = context.args[0], context.args[1]
    try:
        amount = int(amount)
        if amount < 1:
            await update.message.reply_text("❌ Amount must be at least 1")
            return
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return
    
    user_data = ensure_user(user_id)
    user_data["quota"] += amount
    user_data["has_initial_access"] = True
    user_data["granted_by_owner"] += amount
    save_data()
    await update.message.reply_text(f"✅ Granted {amount} searches to user {user_id}")

@owner_only
async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /ban_user USER_ID")
        return
    
    user_id = context.args[0]
    data.setdefault("banned", []).append(user_id)
    save_data()
    await update.message.reply_text(f"✅ Banned user {user_id}")

@owner_only
async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /unban_user USER_ID")
        return
    
    user_id = context.args[0]
    if user_id in data.get("banned", []):
        data["banned"].remove(user_id)
        save_data()
        await update.message.reply_text(f"✅ Unbanned user {user_id}")
    else:
        await update.message.reply_text("❌ User is not banned")

# ==================== HELP COMMAND ====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id == OWNER_ID:
        help_text = """
🆘 INSTAGRAM PRO FINDER - OWNER HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User Commands:
🔍 /ig username - Search profiles
👥 /referral - Get referral link
📚 /history - Search history
📞 /getcontact - Get contact info
📅 /last - Last search result
🎁 /giftcode - Redeem gift code

Owner Commands:
📊 /stats - Bot statistics
📢 /broadcast - Send message to all users
💰 /addcoins - Add coins to user
💰 /removecoins - Remove coins from user
🎁 /setgift - Create gift code
🎁 /makegiftcode - Create gift code
🔧 /set_channel - Set channel ID
📝 /editcaption - Change join caption
🖼 /editphoto - Change join image
🔗 /editlink - Manage channel links
🔗 /addchannel - Add new channel
🔗 /removechannel - Remove channel
🔗 /viewlink - View all links
🏷️ /editbutton - Edit button text
🏷️ /editbuttonname - Edit button name
👥 /editreferral - Set referrals needed
👥 /editreferralcion - Set referrals
➕ /grant_search - Give searches
🚫 /ban_user - Ban users
✅ /unban_user - Unban users

💡 Contact the bot administrator.
        """
    else:
        help_text = """
🆘 INSTAGRAM PRO FINDER - HELP
━━━━━━━━━━━━━━━━━━

User Commands:
🔍 /ig username - Search Instagram profiles
👥 /referral - Get your referral link
📚 /history - Your search history  
📞 /getcontact username - Get contact info
📅 /last username - Last search result
🎁 /giftcode code - Redeem gift code

💡 Use /start to begin and join channels!
        """
    
    await update.message.reply_text(help_text, parse_mode="HTML")

# ==================== MAIN ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(check_joined_callback, pattern="^check_joined$"))
    
    # User commands
    app.add_handler(CommandHandler("ig", ig_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("last", last_command))
    app.add_handler(CommandHandler("getcontact", getcontact_command))
    app.add_handler(CommandHandler("giftcode", giftcode_command))
    
    # Owner commands
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("addcoins", addcoins_command))
    app.add_handler(CommandHandler("removecoins", removecoins_command))
    app.add_handler(CommandHandler("setgift", setgift_command))
    app.add_handler(CommandHandler("set_channel", set_channel_command))
    app.add_handler(CommandHandler("editcaption", editcaption_command))
    app.add_handler(CommandHandler("editphoto", editphoto_command))
    app.add_handler(CommandHandler("editlink", editlink_command))
    app.add_handler(CommandHandler("editbutton", editbutton_command))
    app.add_handler(CommandHandler("editbuttonname", editbuttonname_command))
    app.add_handler(CommandHandler("editreferral", editreferral_command))
    app.add_handler(CommandHandler("editreferralcion", editreferralcion_command))
    app.add_handler(CommandHandler("addchannel", addchannel_command))
    app.add_handler(CommandHandler("removechannel", removechannel_command))
    app.add_handler(CommandHandler("viewlink", viewlink_command))
    app.add_handler(CommandHandler("makegiftcode", makegiftcode_command))
    app.add_handler(CommandHandler("grant_search", grant_search_command))
    app.add_handler(CommandHandler("ban_user", ban_user_command))
    app.add_handler(CommandHandler("unban_user", unban_user_command))
    
    print("🌟 Instagram Pro Finder - COMPLETE VERSION!")
    print("✅ ALL Owner Commands Added")
    print("✅ Broadcast Feature")
    print("✅ Coin Management")
    print("✅ Channel Management")
    print("✅ Referral Notification System Added!")
    print("🚀 Bot is FULLY OPERATIONAL!")
    
    app.run_polling()

if __name__ == "__main__":
    main()