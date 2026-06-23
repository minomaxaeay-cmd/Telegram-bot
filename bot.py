# Iron Dominion Telegram bot handlers (resilient avatar setup, multi-currency + siege UI).
# Co-authored with CoCo
# bot.py - Iron Dominion Bot Handlers

import telebot
from telebot import types
import time
import sqlite3
import random
from datetime import datetime
import json
import re
import html

from . import config
from . import database
from . import game_logic

# Initialize DB
database.init_db()

bot = telebot.TeleBot(config.API_TOKEN, threaded=False)

# --- STATE MANAGERS ---
def get_state(user_id):
    """Retrieves state, safely handling JSON or plain strings."""
    conn = database.get_db()
    c = conn.cursor()
    c.execute("SELECT state FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    if res and res['state']:
        try:
            return json.loads(res['state'])
        except:
            return res['state'] # Legacy plain string
    return None

def set_state(user_id, state_data):
    """Saves state as JSON string."""
    val = json.dumps(state_data) if isinstance(state_data, (dict, list)) else state_data
    conn = database.get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET state = ? WHERE user_id = ?", (val, user_id))
    conn.commit()
    conn.close()

# --- MENUS ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True, row_width=2)
    markup.add("🏰 Fiefdom", "🗺️ War Map", "⚔️ Army", "📜 Reports")
    markup.add("👤 My Profile", "🍻 Tavern (Global Chat)")
    markup.add("🤝 Alliance", "🏆 Leaderboard")
    markup.add("🔍 Search Player", "📊 Status")
    return markup

def resource_line(user):
    """One-line summary of all four currencies for menus/headers."""
    def amt(field):
        try:
            v = user[field]
        except (KeyError, IndexError, TypeError):
            v = None
        return int(v) if v is not None else 0
    return (f"💰 {amt('gold')}  ⛓️ {amt('iron')}  "
            f"🌾 {amt('grain')}  ✝️ {amt('faith')}")

# --- SAFETY HELPERS ---
def esc(value):
    """HTML-escapes user-supplied text so it cannot break captions/markup."""
    if value is None:
        return ""
    return html.escape(str(value))


TAVERN_LINK_RE = re.compile(r"(?:https?://|www\.|t\.me/|telegram\.me/)", re.IGNORECASE)

def tavern_sender_link(user):
    """Clickable Tavern identity label using Telegram's tg://user link."""
    return (f"<a href=\"tg://user?id={int(user['user_id'])}\">"
            f"{esc(get_lord_name(user))}({esc(user['game_id'])})</a>")

def format_tavern_message(user, message_text):
    return f"{tavern_sender_link(user)}: {esc(message_text)}"

def tavern_validation_error(message_text):
    if len(message_text) > config.MAX_CHAT_LENGTH:
        return f"❌ Message too long! ({len(message_text)}/{config.MAX_CHAT_LENGTH})"
    if "@" in message_text:
        return "❌ Tavern messages cannot include @ mentions."
    if TAVERN_LINK_RE.search(message_text):
        return "❌ Tavern messages cannot include links."
    return None

def send_tavern_message_to_active_lords(sender, message_text):
    formatted = format_tavern_message(sender, message_text)
    for tavern_user_id in database.get_tavern_user_ids(exclude_user_id=sender['user_id']):
        try:
            bot.send_message(tavern_user_id, formatted, parse_mode="HTML", disable_web_page_preview=True)
        except Exception:
            pass

def safe_render(chat_id, text, markup, edit_msg_id=None):
    """Edits the target message in place; if that fails (e.g. it's a photo
    message coming from a profile view), it deletes it and sends a fresh one.
    Keeps inline navigation consistent across all menus."""
    if edit_msg_id:
        try:
            bot.edit_message_text(text, chat_id, edit_msg_id, parse_mode="HTML", reply_markup=markup)
            return
        except Exception:
            try:
                bot.delete_message(chat_id, edit_msg_id)
            except:
                pass
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

# --- PROTECTION / ALLIANCE HELPERS ---
def protection_remaining(user):
    """Returns remaining newbie-shield seconds (0 if expired or waived)."""
    # A player who has waived their shield (see database.waive_protection) is
    # treated as fully exposed, regardless of how recently they joined.
    try:
        if user.get('protection_waived'):
            return 0
    except AttributeError:
        if 'protection_waived' in user.keys() and user['protection_waived']:
            return 0
    elapsed = time.time() - user['joined_date']
    rem = config.NEWBIE_PROTECTION_SECONDS - elapsed
    return int(rem) if rem > 0 else 0

def fmt_duration(seconds):
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

def check_pvp_allowed(attacker_id, defender_id):
    """Validates newbie protection and alliance rules for an offensive action.
    Returns (allowed, reason, block_code). block_code is one of:
    None, 'ally', 'self_shield' (attacker is shielded), 'target_shield'."""
    if database.are_allies(attacker_id, defender_id):
        return False, "🤝 You cannot act against a member of your own alliance!", "ally"

    attacker = database.get_user(attacker_id)
    defender = database.get_user(defender_id)

    atk_rem = protection_remaining(attacker)
    if atk_rem > 0:
        return False, f"🛡️ You are under newbie protection ({fmt_duration(atk_rem)} left). Attacking ends your shield.", "self_shield"

    def_rem = protection_remaining(defender)
    if def_rem > 0:
        return False, f"🛡️ This lord is under newbie protection for another {fmt_duration(def_rem)}.", "target_shield"

    return True, None, None

def send_waive_prompt(chat_id, target_id, context):
    """Offers a shielded player the choice to drop their newbie protection so they
    can attack/spy. context is 'attack' or 'spy'. No standalone button — this is
    surfaced only when the player actually tries an offensive action."""
    user = database.get_user(chat_id)
    rem = protection_remaining(user)
    verb = "attack" if context == "attack" else "spy on"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⚔️ Waive Protection & Continue",
                                          callback_data=f"waive:{context}:{target_id}"))
    markup.add(types.InlineKeyboardButton("🛡️ Keep My Shield", callback_data="waive_cancel"))
    bot.send_message(
        chat_id,
        f"🛡️ <b>NEWBIE PROTECTION ACTIVE</b> ({fmt_duration(rem)} left)\n\n"
        f"You can't {verb} another lord while shielded. Waiving lets you strike now — "
        f"but your shield drops <b>permanently</b>, so other lords can attack and spy on you too.\n\n"
        f"Lift your shield and continue?",
        parse_mode="HTML", reply_markup=markup)

# --- UI HELPERS ---
def get_lord_name(user):
    """Returns display_name if set, otherwise falls back to Telegram username."""
    try:
        display_name = user['display_name']
    except (KeyError, IndexError, TypeError):
        display_name = None
    if display_name:
        return display_name
    return user['username']

def send_profile_view(chat_id, target_user):
    """Displays ANOTHER player's profile with attack/espionage options."""
    buildings = database.get_buildings(target_user['user_id'])
    power = game_logic.calculate_power_score(buildings)
    castle_lvl = buildings.get('castle', 1)
    
    t_name = config.TRIBES[target_user['tribe']]['name']
    lord_name = esc(get_lord_name(target_user))
    join_dt = datetime.fromtimestamp(target_user['joined_date'])
    date_str = join_dt.strftime("%b %Y")
    renown = target_user['renown'] if 'renown' in target_user.keys() else 0

    caption = (f"📜 <b>LORD PROFILE</b>\n\n"
               f"👤 <b>{lord_name}</b>\n"
               f"🆔 ID: <code>{target_user['game_id']}</code>\n"
               f"🚩 Tribe: {t_name}\n"
               f"📅 Joined: {date_str}\n\n"
               f"<b>Intelligence Report:</b>\n"
               f"🏰 Castle Level: {castle_lvl}\n"
               f"🎖️ Renown: {renown}\n"
               f"📈 Power Score: {power}")

    shield = protection_remaining(target_user)
    if shield > 0:
        caption += f"\n🛡️ <b>Newbie Protection:</b> {fmt_duration(shield)} left"
               
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Only show attack/spy options when viewing someone else
    if chat_id != target_user['user_id']:
        markup.add(
            types.InlineKeyboardButton("⚔️ Attack", callback_data=f"pre_attack:{target_user['user_id']}"),
            types.InlineKeyboardButton("🕵️ Espionage", callback_data=f"spy_menu:{target_user['user_id']}")
        )
        markup.add(
            types.InlineKeyboardButton("💬 Message", callback_data=f"dm:{target_user['user_id']}")
        )
    
    markup.add(types.InlineKeyboardButton("🗺️ Back to Map", callback_data="refresh:map"))
    
    try:
        bot.send_photo(chat_id, target_user['avatar_id'], caption=caption, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"[IronDominion] send_profile_view photo failed: {e}")
        bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)

def show_my_profile(chat_id):
    """Displays YOUR OWN profile with edit options."""
    user = database.get_user(chat_id)
    buildings = database.get_buildings(chat_id)
    units = database.get_units(chat_id)
    power = game_logic.calculate_power_score(buildings)
    castle_lvl = buildings.get('castle', 1)
    
    t_name = config.TRIBES[user['tribe']]['name']
    lord_name = esc(get_lord_name(user))
    join_dt = datetime.fromtimestamp(user['joined_date'])
    date_str = join_dt.strftime("%b %Y")
    renown = user['renown'] if 'renown' in user.keys() else 0
    
    # Calculate army stats
    total_troops = sum(v for k, v in units.items() if config.UNITS[k]['combat_valid'])
    spy_count = units.get('spy', 0)
    current_stance = config.STANCE_STATS.get(user.get('stance', 'standard'), {}).get('name', 'Standard')

    caption = (f"👤 <b>MY PROFILE</b>\n\n"
               f"⚜️ <b>{lord_name}</b>\n"
               f"🆔 ID: <code>{user['game_id']}</code>\n"
               f"🚩 Tribe: {t_name}\n"
               f"📅 Joined: {date_str}\n\n"
               f"<b>Treasury:</b>\n"
               f"💰 Gold: {int(user['gold'])}\n"
               f"⛓️ Iron: {int(user['iron']) if 'iron' in user.keys() and user['iron'] is not None else 0}\n"
               f"🌾 Grain: {int(user['grain']) if 'grain' in user.keys() and user['grain'] is not None else 0}\n"
               f"✝️ Faith: {int(user['faith']) if 'faith' in user.keys() and user['faith'] is not None else 0}\n\n"
               f"<b>Kingdom Status:</b>\n"
               f"🏰 Castle Level: {castle_lvl}\n"
               f"⚔️ Army Size: {total_troops}\n"
               f"🕵️ Rogues: {spy_count}\n"
               f"🛡️ Stance: {current_stance}\n"
               f"🎖️ Renown: {renown}\n"
               f"📈 Power Score: {power}")

    # Active blessings (temporary Faith buffs)
    active = database.get_active_blessings(chat_id)
    if active:
        now = time.time()
        eff_name = {b['effect']: b['name'] for b in config.BLESSING_DEFS.values()}
        lines = [f"{eff_name.get(eff, eff)} ({fmt_duration(exp - now)} left)"
                 for eff, exp in active.items()]
        caption += "\n\n<b>✨ Blessings:</b>\n" + "\n".join(lines)
               
    shield = protection_remaining(user)
    if shield > 0:
        caption += f"\n🛡️ <b>Newbie Protection:</b> {fmt_duration(shield)} left"

    # Find current avatar index for navigation. If the player's stored avatar is no
    # longer in the gallery (e.g. an admin swapped that slot), use -1 so Prev/Next
    # walk into the gallery from its ends (Next -> image #1, Prev -> last) instead of
    # silently skipping past image #1. Their actual face is still shown above; nav
    # only changes it once they pick.
    avatar_ids = database.get_avatars()
    if user['avatar_id'] in avatar_ids:
        current_idx = avatar_ids.index(user['avatar_id'])
    else:
        current_idx = -1
               
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ Change Name", callback_data="edit:name"))
    markup.row(
        types.InlineKeyboardButton("⬅️ Prev Face", callback_data=f"edit:av_prev:{current_idx}"),
        types.InlineKeyboardButton("Next Face ➡️", callback_data=f"edit:av_next:{current_idx}")
    )
    markup.add(types.InlineKeyboardButton("🔙 Close", callback_data="edit:close"))
    
    try:
        bot.send_photo(chat_id, user['avatar_id'], caption=caption, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"[IronDominion] show_my_profile photo failed: {e}")
        bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)

def refresh_attack_ui(user_id, state):
    """Builds the troop selection matrix with steppers + exact-type option."""
    user_units = database.get_units(user_id)
    selections = state['selections']
    
    markup = types.InlineKeyboardMarkup(row_width=4)
    
    for u_key, u_data in config.UNITS.items():
        if not u_data['combat_valid']: continue
        owned = user_units.get(u_key, 0)
        
        # Only show troops user owns (or has selected)
        if owned > 0:
            current_sel = selections.get(u_key, 0)
            
            markup.row(types.InlineKeyboardButton(
                f"{u_data['name']}: {current_sel}/{owned}", callback_data=f"atk_hint:{u_key}"))
            markup.row(
                types.InlineKeyboardButton("➖10", callback_data=f"atk_inc:{u_key}:-10"),
                types.InlineKeyboardButton("➖1", callback_data=f"atk_inc:{u_key}:-1"),
                types.InlineKeyboardButton("➕1", callback_data=f"atk_inc:{u_key}:1"),
                types.InlineKeyboardButton("➕10", callback_data=f"atk_inc:{u_key}:10")
            )
            markup.row(
                types.InlineKeyboardButton("Max", callback_data=f"atk_inc:{u_key}:max"),
                types.InlineKeyboardButton("Reset", callback_data=f"atk_inc:{u_key}:zero"),
                types.InlineKeyboardButton("✏️ Type exact", callback_data=f"atk_set:{u_key}")
            )
            
    markup.row(
        types.InlineKeyboardButton("❌ Cancel", callback_data="atk_cancel"),
        types.InlineKeyboardButton("➡️ Select Tactics", callback_data="atk_tactics")
    )
    
    try:
        bot.edit_message_reply_markup(user_id, state['ui_msg_id'], reply_markup=markup)
    except Exception as e:
        print(f"UI Update failed: {e}")

# --- SETUP FLOW ---
def send_tribe_selection(chat_id):
    markup = types.InlineKeyboardMarkup()
    for key, data in config.TRIBES.items():
        markup.add(types.InlineKeyboardButton(f"{data['name']} ({data['desc']})", callback_data=f"setup:tribe:{key}"))
    bot.send_message(chat_id, "📜 <b>DECLARATION OF LINEAGE</b>\n\nBefore you claim your land, you must declare your heritage. Choose wisely, for this cannot be changed.", parse_mode="HTML", reply_markup=markup)

def send_avatar_selection(chat_id, index=None):
    avatar_ids = database.get_avatars()
    if index is None:
        index = random.randint(0, len(avatar_ids) - 1)
    if index >= len(avatar_ids): index = 0
    if index < 0: index = 0
    file_id = avatar_ids[index]
    markup = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    if index > 0:
        btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"setup:av:move:{index-1}"))
    else:
        btns.append(types.InlineKeyboardButton("⬛", callback_data="ignore"))
    btns.append(types.InlineKeyboardButton("✅ Select This Face", callback_data=f"setup:av:sel:{index}"))
    if index < len(avatar_ids) - 1:
        btns.append(types.InlineKeyboardButton("➡️", callback_data=f"setup:av:move:{index+1}"))
    else:
        btns.append(types.InlineKeyboardButton("⬛", callback_data="ignore"))
    markup.add(*btns)
    caption = f"👤 <b>CHOOSE YOUR AVATAR</b>\nImage {index + 1} of {len(avatar_ids)}"
    return file_id, caption, markup

# Remembers whether we've already warned the admin that avatar images can't be sent.
_avatar_warned = {"done": False}

def render_avatar_picker(chat_id, index=None, edit_msg_id=None):
    """Show the avatar carousel resiliently. Tries the PHOTO carousel; if Telegram rejects
    the stored file_id (e.g. the images were uploaded by a different bot, or the DB was
    reset), falls back to a TEXT picker with the SAME ⬅️/✅ Select/➡️ buttons so a new lord
    can ALWAYS finish setup. Returns True if any picker was shown, False otherwise."""
    fid, cap, markup = send_avatar_selection(chat_id, index)
    # 1) Happy path: real photo carousel (unchanged behaviour when file_ids are valid).
    try:
        if edit_msg_id is not None:
            media = types.InputMediaPhoto(fid, caption=cap, parse_mode="HTML")
            bot.edit_message_media(media=media, chat_id=chat_id, message_id=edit_msg_id, reply_markup=markup)
        else:
            bot.send_photo(chat_id, fid, caption=cap, parse_mode="HTML", reply_markup=markup)
        return True
    except Exception as e:
        print(f"[IronDominion] avatar photo unavailable, using text picker: {e}")
        if not _avatar_warned["done"]:
            _avatar_warned["done"] = True
            try:
                bot.send_message(config.ADMIN_ID,
                                 "⚠️ <b>This bot can't send the avatar images.</b>\nNew lords are "
                                 "using the text avatar picker. Re-upload images via Admin Console → "
                                 "Manage Bot Images to restore the photo carousel.",
                                 parse_mode="HTML")
            except Exception:
                pass
    # 2) Text fallback: same caption text + same nav/select buttons, no photo.
    text = ("👤 <b>CHOOSE YOUR AVATAR</b>\n" + cap.split("\n", 1)[-1] +
            "\n\n<i>(Avatar images unavailable right now — pick a slot to continue; "
            "you can change your face later from your profile.)</i>")
    try:
        if edit_msg_id is not None:
            bot.edit_message_text(text, chat_id, edit_msg_id, parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
        return True
    except Exception as e:
        print(f"[IronDominion] avatar text picker failed: {e}")
        return False

def send_admin_image_view(chat_id, index=0, edit_msg_id=None):
    """Admin carousel for the bot's avatar images — same look as the player avatar
    picker (⬅️ / ✅ select / ➡️). Selecting a slot opens the replace flow."""
    avatar_ids = database.get_avatars()
    if not avatar_ids:
        bot.send_message(chat_id, "⚠️ No bot images configured.")
        return
    if index >= len(avatar_ids): index = 0
    if index < 0: index = len(avatar_ids) - 1
    file_id = avatar_ids[index]
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("⬅️", callback_data=f"aimg:move:{index-1}"),
        types.InlineKeyboardButton("✅ Replace This Image", callback_data=f"aimg:sel:{index}"),
        types.InlineKeyboardButton("➡️", callback_data=f"aimg:move:{index+1}")
    )
    markup.add(types.InlineKeyboardButton("🔙 Close", callback_data="aimg:close"))
    caption = (f"🖼️ <b>BOT IMAGE LIBRARY</b>\nImage {index + 1} of {len(avatar_ids)}\n"
               f"<code>{esc(file_id)}</code>")
    if edit_msg_id:
        try:
            media = types.InputMediaPhoto(file_id, caption=caption, parse_mode="HTML")
            bot.edit_message_media(media=media, chat_id=chat_id, message_id=edit_msg_id, reply_markup=markup)
            return
        except Exception as e:
            print(f"[IronDominion] admin image nav failed: {e}")
    try:
        bot.send_photo(chat_id, file_id, caption=caption, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"[IronDominion] admin image view failed: {e}")
        bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    if database.is_banned(message.chat.id) and message.chat.id != config.ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ You have been banned from Iron Dominion.")
        return
    user = database.get_user(message.chat.id, message.from_user.first_name)
    if user['setup_complete'] == 0:
        send_tribe_selection(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Welcome back, My Lord.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == config.ADMIN_TRIGGER)
def admin_panel(message):
    # Security Check: If ID doesn't match, ignore completely.
    if message.from_user.id != config.ADMIN_ID:
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💰 Send Gold to Player", callback_data="admin:start_gold"))
    markup.add(types.InlineKeyboardButton("📢 Broadcast to All", callback_data="admin:broadcast"))
    markup.add(types.InlineKeyboardButton("✉️ Message a Player", callback_data="admin:msg_player"))
    markup.add(types.InlineKeyboardButton("🤝 Message an Alliance", callback_data="admin:msg_alliance"))
    markup.row(
        types.InlineKeyboardButton("🚫 Ban Player", callback_data="admin:ban"),
        types.InlineKeyboardButton("✅ Unban Player", callback_data="admin:unban")
    )
    markup.add(types.InlineKeyboardButton("🖼️ Manage Bot Images", callback_data="admin:images"))
    markup.add(types.InlineKeyboardButton("♻️ Re-upload All Avatars", callback_data="admin:bulk_avatars"))
    markup.add(types.InlineKeyboardButton("👁️ Preview Avatars", callback_data="admin:preview_avatars"))
    markup.add(types.InlineKeyboardButton("🆔 Get Media ID", callback_data="admin:get_media"))
    markup.add(types.InlineKeyboardButton("🏆 Start New Season", callback_data="admin:new_season"))

    bot.send_message(message.chat.id, "🕵️‍♂️ <b>ADMIN CONSOLE</b>\nSelect an operation:", 
                     parse_mode="HTML", reply_markup=markup)

# --- TEXT HANDLER ---
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_text(message):
    user_id = message.chat.id
    # Full lockout: banned lords get no response (the admin is never locked out).
    if database.is_banned(user_id) and user_id != config.ADMIN_ID:
        return
    user = database.get_user(user_id, message.from_user.first_name)

    # 1. SETUP CHECK (must run before menu routing so un-set-up users can't trigger views)
    if user['setup_complete'] == 0:
        if not user['tribe']:
            send_tribe_selection(user_id)
        else:
            fid, cap, markup = send_avatar_selection(user_id)
            try:
                bot.send_photo(user_id, fid, caption=cap, parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                print(f"[IronDominion] avatar selection load failed: {e}")
                bot.send_message(user_id, "⚠️ Couldn't load the avatar right now. Please try /start again.")
        return

    # 2. MENU BUTTONS (Global Escape Hatch)
    text = message.text
    if text == "🏰 Fiefdom": 
        set_state(user_id, None) # Clear any stuck state
        return view_city(message)
    if text == "⚔️ Army": 
        set_state(user_id, None)
        return view_army(message)
    if text == "🗺️ War Map": 
        set_state(user_id, None)
        return view_map(message)
    if text == "📜 Reports": 
        set_state(user_id, None)
        return view_reports(message)
    if text == "👤 My Profile":
        set_state(user_id, None)
        return show_my_profile(user_id)
    if text == "🍻 Tavern (Global Chat)": 
        return enter_tavern(message) # Tavern handles its own state
    if text == "🤝 Alliance":
        set_state(user_id, None)
        return view_alliance(message)
    if text == "🏆 Leaderboard":
        set_state(user_id, None)
        return view_leaderboard(message)
    if text == "🔍 Search Player":
        set_state(user_id, "search_player")
        bot.send_message(user_id, "🔍 <b>FIND LORD</b>\nEnter the Game ID (Format: XXX-XXX):", parse_mode="HTML")
        return
    if text == "📊 Status":
        set_state(user_id, None)
        return show_status(message)

    # 3. STATE HANDLING
    state = get_state(user_id)
    # --- ADMIN FLOW ---
    if isinstance(state, dict) and state.get("action") == "admin_find_user":
        if user_id != config.ADMIN_ID: return # Security
        
        target_game_id = text.strip().upper()
        target_user = database.get_user_by_game_id(target_game_id)
        
        if not target_user:
            bot.send_message(user_id, f"❌ User {target_game_id} not found.")
            set_state(user_id, None)
        else:
            # Found user, now ask for gold amount
            bot.send_message(user_id, f"✅ Found: {esc(target_user['username'])}\nCurrent Gold: {int(target_user['gold'])}\n\n<b>How much gold to add?</b>", parse_mode="HTML")
            # Update state to wait for amount, saving the target's internal ID
            set_state(user_id, {"action": "admin_add_gold", "target_uid": target_user['user_id']})
        return

    elif isinstance(state, dict) and state.get("action") == "admin_add_gold":
        if user_id != config.ADMIN_ID: return # Security
        
        try:
            amount = int(text)
            target_uid = state["target_uid"]
            
            # Execute the Gold Update
            # OUT-OF-ECONOMY SOURCE (MG4): admin-minted gold. Not part of the
            # closed loop; admin-only and excluded from conservation accounting.
            conn = database.get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET gold = gold + ? WHERE user_id = ?", (amount, target_uid))
            conn.commit()
            conn.close()
            
            bot.send_message(user_id, f"✅ Successfully added {amount} Gold.")
            
            # Optional: Notify the user they received gold
            try:
                bot.send_message(target_uid, f"💰 <b>THE GODS BLESS YOU!</b>\nYou have received {amount} Gold.", parse_mode="HTML")
            except:
                pass # User might have blocked bot, ignore
            
        except ValueError:
            bot.send_message(user_id, "❌ Invalid amount. Operation cancelled.")
        
        set_state(user_id, None)
        return

    # --- ADMIN: BROADCAST TO ALL ---
    elif isinstance(state, dict) and state.get("action") == "admin_broadcast":
        if user_id != config.ADMIN_ID: return  # Security
        set_state(user_id, None)
        announce = f"📢 <b>ROYAL DECREE</b>\n\n<i>{esc(text)}</i>"
        sent = failed = 0
        for uid in database.get_all_user_ids():
            try:
                bot.send_message(uid, announce, parse_mode="HTML")
                sent += 1
            except Exception:
                failed += 1
        bot.send_message(user_id, f"✅ Broadcast delivered to {sent} lords ({failed} unreachable).")
        return

    # --- ADMIN: MESSAGE A PLAYER (find) ---
    elif isinstance(state, dict) and state.get("action") == "admin_dm_find":
        if user_id != config.ADMIN_ID: return  # Security
        target_user = database.get_user_by_game_id(text.strip().upper())
        if not target_user:
            bot.send_message(user_id, f"❌ User {esc(text.strip().upper())} not found.")
            set_state(user_id, None)
        else:
            set_state(user_id, {"action": "admin_dm_send", "target_uid": target_user['user_id']})
            bot.send_message(user_id,
                             f"✅ Found: {esc(get_lord_name(target_user))}\n\n<b>Type the message to send:</b>",
                             parse_mode="HTML")
        return

    # --- ADMIN: MESSAGE A PLAYER (send) ---
    elif isinstance(state, dict) and state.get("action") == "admin_dm_send":
        if user_id != config.ADMIN_ID: return  # Security
        target_uid = state["target_uid"]
        set_state(user_id, None)
        try:
            bot.send_message(target_uid,
                             f"👑 <b>MESSAGE FROM THE CROWN</b>\n\n<i>{esc(text)}</i>",
                             parse_mode="HTML")
            bot.send_message(user_id, "✅ Message delivered.")
        except Exception:
            bot.send_message(user_id, "❌ Could not deliver. The lord may have blocked the bot.")
        return

    # --- ADMIN: MESSAGE AN ALLIANCE (find) ---
    elif isinstance(state, dict) and state.get("action") == "admin_alliance_find":
        if user_id != config.ADMIN_ID: return  # Security
        tag = re.sub(r'[^A-Za-z0-9]', '', text.strip()).upper()
        alliance = database.get_alliance_by_tag(tag)
        if not alliance:
            bot.send_message(user_id, f"❌ No alliance with tag <code>{esc(tag)}</code>.", parse_mode="HTML")
            set_state(user_id, None)
        else:
            set_state(user_id, {"action": "admin_alliance_send", "alliance_id": alliance['id'],
                                "alliance_name": alliance['name']})
            bot.send_message(user_id,
                             f"✅ Found: <b>{esc(alliance['name'])}</b> [{esc(alliance['tag'])}]\n\n"
                             f"<b>Type the message to send to all members:</b>",
                             parse_mode="HTML")
        return

    # --- ADMIN: MESSAGE AN ALLIANCE (send) ---
    elif isinstance(state, dict) and state.get("action") == "admin_alliance_send":
        if user_id != config.ADMIN_ID: return  # Security
        alliance_id = state["alliance_id"]
        alliance_name = state.get("alliance_name", "your alliance")
        set_state(user_id, None)
        announce = (f"🤝 <b>WORD TO {esc(alliance_name).upper()}</b>\n"
                    f"<i>(A message from the Crown to your alliance)</i>\n\n<i>{esc(text)}</i>")
        sent = failed = 0
        for m in database.get_alliance_members(alliance_id):
            try:
                bot.send_message(m['user_id'], announce, parse_mode="HTML")
                sent += 1
            except Exception:
                failed += 1
        bot.send_message(user_id, f"✅ Delivered to {sent} members ({failed} unreachable).")
        return

    # --- ADMIN: BAN PLAYER ---
    elif isinstance(state, dict) and state.get("action") == "admin_ban_find":
        if user_id != config.ADMIN_ID: return  # Security
        target_user = database.get_user_by_game_id(text.strip().upper())
        set_state(user_id, None)
        if not target_user:
            bot.send_message(user_id, f"❌ User {esc(text.strip().upper())} not found.")
        elif target_user['user_id'] == config.ADMIN_ID:
            bot.send_message(user_id, "❌ You cannot ban yourself.")
        else:
            database.set_banned(target_user['user_id'], True)
            bot.send_message(user_id, f"🚫 Banned <b>{esc(get_lord_name(target_user))}</b> "
                                      f"(<code>{esc(target_user['game_id'])}</code>).", parse_mode="HTML")
            try:
                bot.send_message(target_user['user_id'], "⛔ You have been banned from Iron Dominion.")
            except Exception:
                pass
        return

    # --- ADMIN: UNBAN PLAYER ---
    elif isinstance(state, dict) and state.get("action") == "admin_unban_find":
        if user_id != config.ADMIN_ID: return  # Security
        target_user = database.get_user_by_game_id(text.strip().upper())
        set_state(user_id, None)
        if not target_user:
            bot.send_message(user_id, f"❌ User {esc(text.strip().upper())} not found.")
        else:
            database.set_banned(target_user['user_id'], False)
            bot.send_message(user_id, f"✅ Unbanned <b>{esc(get_lord_name(target_user))}</b> "
                                      f"(<code>{esc(target_user['game_id'])}</code>).", parse_mode="HTML")
            try:
                bot.send_message(target_user['user_id'], "✅ Your ban has been lifted. Welcome back, My Lord.")
            except Exception:
                pass
        return

    # A. TAVERN
    if state == "chatting":
        if text == "🔙 Exit Tavern":
            set_state(user_id, None)
            bot.send_message(user_id, "You leave the tavern.", reply_markup=main_menu())
        else:
            validation_error = tavern_validation_error(text)
            if validation_error:
                bot.send_message(user_id, validation_error)
                return
            database.add_chat_message(user_id, get_lord_name(user), user['game_id'], text)
            send_tavern_message_to_active_lords(user, text)

    # B. SEARCH PLAYER
    elif state == "search_player":
        clean_id = text.strip().upper()
        if not re.match(r'^[A-Z0-9]{3}-[A-Z0-9]{3}$', clean_id):
            bot.send_message(user_id, "❌ Invalid format. Use XXX-XXX (e.g., AKL-0H2).")
            return
        
        target = database.get_user_by_game_id(clean_id)
        if not target:
            bot.send_message(user_id, f"❌ No lord found with ID: <code>{clean_id}</code>")
            set_state(user_id, None)
        else:
            set_state(user_id, None)
            send_profile_view(user_id, target)

    # C. DM WRITING
    elif isinstance(state, dict) and state.get("action") == "dm_write":
        recipient_id = state["target_id"]
        if len(text) > config.MAX_DM_LENGTH:
            bot.send_message(user_id, f"❌ Message too long! ({len(text)}/{config.MAX_DM_LENGTH})")
            return
        
        try:
            sender_name = f"{esc(user['username'])} (<code>{user['game_id']}</code>)"
            msg_text = f"📨 <b>PRIVATE MESSAGE</b>\nFrom: {sender_name}\n\n<i>{esc(text)}</i>"
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("💬 Reply", callback_data=f"dm:{user_id}"),
                types.InlineKeyboardButton("👤 Profile", callback_data=f"profile:{user_id}")
            )
            bot.send_message(recipient_id, msg_text, parse_mode="HTML", reply_markup=markup)
            bot.send_message(user_id, "✅ Message sent!")
        except:
            bot.send_message(user_id, "❌ Could not deliver. User may have blocked the bot.")
        
        set_state(user_id, None)
    # E. PROFILE RENAME
    elif isinstance(state, dict) and state.get("action") == "rename_profile":
        new_name = text.strip()[:20]  # Maximum 20 characters
        
        # Validation
        if len(new_name) < 2:
            bot.send_message(user_id, "❌ Name too short! Minimum 2 characters.")
            return
        
        # Sanitize: Remove any problematic characters
        new_name = re.sub(r'[<>]', '', new_name)
        
        conn = database.get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET display_name = ? WHERE user_id = ?", (new_name, user_id))
        conn.commit()
        conn.close()
        
        set_state(user_id, None)
        bot.send_message(user_id, f"✅ Your title is now: <b>{esc(new_name)}</b>", parse_mode="HTML")
        show_my_profile(user_id)

    # F. ESPIONAGE INPUT
    elif isinstance(state, dict) and state.get("action") == "spy_input":
        try:
            spies_to_send = int(text)
            
            if spies_to_send < 1:
                bot.send_message(user_id, "❌ You must send at least 1 rogue.")
                return
                
            user_units = database.get_units(user_id)
            available_spies = user_units.get("spy", 0)
            
            if spies_to_send > available_spies:
                bot.send_message(user_id, f"❌ You only have {available_spies} rogues available!")
                return
            
            target_id = state["target_id"]
            mission = state["mission"]
            
            # Gather all data needed for espionage calculation
            target = database.get_user(target_id)
            def_units = database.get_units(target_id)
            def_buildings = database.get_buildings(target_id)
            
            # Execute the espionage mission
            success, user_msg, target_alert, spies_died, stolen_gold, building_damaged = game_logic.run_espionage(
                user, target, spies_to_send, mission, user_units, def_units, def_buildings
            )
            
            # Apply results to database
            conn = database.get_db()
            c = conn.cursor()
            
            # Remove dead spies from attacker
            if spies_died > 0:
                c.execute("UPDATE units SET count = MAX(0, count - ?) WHERE user_id = ? AND u_type = 'spy'", 
                          (spies_died, user_id))
            
            # Transfer gold if heist was successful (atomic: clamp to target's current gold)
            if stolen_gold > 0:
                c.execute("SELECT gold FROM users WHERE user_id = ?", (target_id,))
                trow = c.fetchone()
                target_gold = trow['gold'] if trow else 0
                stolen_gold = int(min(stolen_gold, target_gold))
                if stolen_gold > 0:
                    c.execute("UPDATE users SET gold = gold + ? WHERE user_id = ?", (stolen_gold, user_id))
                    c.execute("UPDATE users SET gold = MAX(0, gold - ?) WHERE user_id = ?", (stolen_gold, target_id))
            
            # Damage building if sabotage succeeded
            if building_damaged:
                c.execute("UPDATE buildings SET level = level - 1 WHERE user_id = ? AND b_type = ? AND level > 0",
                          (target_id, building_damaged))
            
            # Set espionage cooldown (namespaced from attacks via -target_id)
            c.execute("REPLACE INTO cooldowns (user_id, target_id, timestamp) VALUES (?, ?, ?)",
                      (user_id, -target_id, time.time()))
            
            conn.commit()
            conn.close()

            # MG2 Renown: a successful heist awards lifetime renown scaled by
            # the gold actually stolen (done after the transaction closes).
            if stolen_gold > 0:
                database.award_renown(user_id, max(1, stolen_gold // config.RENOWN_HEIST_DIVISOR))

            # Clean up the prompt message
            try:
                bot.delete_message(user_id, state.get("prompt_id"))
            except:
                pass
            
            set_state(user_id, None)
            bot.send_message(user_id, user_msg, parse_mode="HTML", reply_markup=main_menu())
            
            # Send alert to defender (if applicable)
            if target_alert:
                try:
                    alert_markup = types.InlineKeyboardMarkup()
                    alert_markup.add(
                        types.InlineKeyboardButton("👤 Who?", callback_data=f"profile:{user_id}"),
                        types.InlineKeyboardButton("⚔️ Retaliate", callback_data=f"pre_attack:{user_id}")
                    )
                    bot.send_message(target_id, target_alert, parse_mode="HTML", reply_markup=alert_markup)
                except:
                    pass  # Target may have blocked bot
                    
        except ValueError:
            bot.send_message(user_id, "❌ Please enter a valid number.")

    # D. ATTACK TROOP INPUT
    elif isinstance(state, dict) and state.get("action") == "attack_select":
        unit_key = state.get("awaiting_unit")
        if unit_key:
            try:
                count = int(text)
                user_units = database.get_units(user_id)
                max_avail = user_units.get(unit_key, 0)
                
                if count < 0: count = 0
                if count > max_avail: count = max_avail
                
                state["selections"][unit_key] = count
                state["awaiting_unit"] = None
                
                try:
                    bot.delete_message(user_id, message.message_id)
                    if state.get("prompt_msg_id"):
                        bot.delete_message(user_id, state["prompt_msg_id"])
                except: pass

                refresh_attack_ui(user_id, state)
                set_state(user_id, state)
                
            except ValueError:
                bot.send_message(user_id, "❌ Please enter a number.")

    # E. RECRUITING (NEW UX)
    elif isinstance(state, dict) and state.get("action") == "recruit_input":
        unit_key = state["unit"]
        try:
            amount = int(text)
            if amount <= 0: raise ValueError
            cost = game_logic.recruit_cost(unit_key, amount)  # {'gold','iron'}

            # DECLARED SINK (MG4): recruitment gold + iron are destroyed (verified
            # affordable atomically across both currencies before debiting).
            ok, msg = database.spend_resources(user_id, gold=cost["gold"], iron=cost["iron"])
            if ok:
                conn = database.get_db()
                c = conn.cursor()
                c.execute("UPDATE units SET count = count + ? WHERE user_id = ? AND u_type = ?", (amount, user_id, unit_key))
                conn.commit()
                conn.close()

                # UX Cleanup: Delete user input and prompt
                try:
                    bot.delete_message(user_id, message.message_id)
                    bot.delete_message(user_id, state["prompt_id"])
                except: pass

                # Update the original Army Menu instead of sending a new message
                view_army(message, edit_msg_id=state["origin_id"])

                set_state(user_id, None)
            else:
                bot.send_message(user_id, f"❌ {msg}")
                # Don't delete state, let them try again
        except ValueError:
            bot.send_message(user_id, "❌ Invalid number.")

    # G. ALLIANCE — CREATE (NAME)
    elif state == "alliance_create_name":
        name = re.sub(r'[<>]', '', text.strip())[:24]
        if len(name) < 3:
            bot.send_message(user_id, "❌ Name too short! Minimum 3 characters.")
            return
        set_state(user_id, {"action": "alliance_create_tag", "name": name})
        bot.send_message(user_id,
                         f"🏷️ Now choose a short <b>TAG</b> (2-{config.ALLIANCE_TAG_LEN} letters/numbers), e.g. <code>IRON</code>:",
                         parse_mode="HTML")

    # H. ALLIANCE — CREATE (TAG)
    elif isinstance(state, dict) and state.get("action") == "alliance_create_tag":
        tag = re.sub(r'[^A-Za-z0-9]', '', text.strip()).upper()
        if not (2 <= len(tag) <= config.ALLIANCE_TAG_LEN):
            bot.send_message(user_id, f"❌ Tag must be 2-{config.ALLIANCE_TAG_LEN} letters/numbers.")
            return
        ok, result = database.create_alliance(user_id, state["name"], tag)
        set_state(user_id, None)
        if ok:
            bot.send_message(user_id,
                             f"✅ <b>Alliance founded!</b>\n🏰 {esc(state['name'])} [{esc(tag)}]\n\nYou are the leader.",
                             parse_mode="HTML", reply_markup=main_menu())
        else:
            bot.send_message(user_id, f"❌ {result}", reply_markup=main_menu())

    # I. ALLIANCE — JOIN (BY TAG)
    elif state == "alliance_join":
        tag = re.sub(r'[^A-Za-z0-9]', '', text.strip()).upper()
        target = database.get_alliance_by_tag(tag)
        set_state(user_id, None)
        if not target:
            bot.send_message(user_id, f"❌ No alliance with tag <code>{tag}</code>.", parse_mode="HTML", reply_markup=main_menu())
            return
        ok, msg = database.join_alliance(user_id, target['id'])
        if ok:
            bot.send_message(user_id, f"✅ You joined <b>{esc(target['name'])}</b> [{esc(target['tag'])}]!",
                             parse_mode="HTML", reply_markup=main_menu())
        else:
            bot.send_message(user_id, f"❌ {msg}", reply_markup=main_menu())

# --- ADMIN MEDIA HANDLER ---
def _extract_file_id(message):
    """Returns (file_id, kind) for the media in a message, or (None, None)."""
    if message.content_type == "photo" and message.photo:
        return message.photo[-1].file_id, "photo"
    if message.content_type == "document" and message.document:
        return message.document.file_id, "document"
    if message.content_type == "video" and message.video:
        return message.video.file_id, "video"
    if message.content_type == "animation" and message.animation:
        return message.animation.file_id, "animation"
    return None, None

@bot.message_handler(content_types=['photo', 'document', 'video', 'animation'])
def handle_admin_media(message):
    """Admin-only: powers 'Get Media ID' and the bot-image replacement flow."""
    user_id = message.chat.id
    if user_id != config.ADMIN_ID:
        return
    state = get_state(user_id)
    if not (isinstance(state, dict) and state.get("action") in ("admin_get_media", "admin_set_image", "admin_bulk_avatars")):
        return

    file_id, kind = _extract_file_id(message)
    if not file_id:
        bot.send_message(user_id, "❌ Couldn't read a file_id from that media.")
        return

    if state.get("action") == "admin_get_media":
        set_state(user_id, None)
        bot.send_message(user_id,
                         f"🆔 <b>{kind} file_id:</b>\n<code>{esc(file_id)}</code>",
                         parse_mode="HTML")
        return

    if state.get("action") == "admin_bulk_avatars":
        # Bulk re-upload: collect each photo's file_id; admin taps Finish to install.
        if kind != "photo":
            bot.send_message(user_id, "❌ Avatars must be <b>photos</b>. Send a photo.", parse_mode="HTML")
            return
        collected = state.get("collected", [])
        collected.append(file_id)
        state["collected"] = collected
        set_state(user_id, state)
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("✅ Finish & Install", callback_data="admin:bulk_finish"))
        mk.add(types.InlineKeyboardButton("❌ Cancel", callback_data="admin:bulk_cancel"))
        bot.send_message(user_id,
                         f"📸 Captured <b>{len(collected)}</b> avatar(s). Send more, or tap "
                         f"✅ Finish &amp; Install.", parse_mode="HTML", reply_markup=mk)
        return

    # admin_set_image: must be a photo (bot avatars are sent via send_photo)
    if kind != "photo":
        bot.send_message(user_id, "❌ Bot images must be a <b>photo</b>. Please send a photo.", parse_mode="HTML")
        return
    slot = state.get("slot")
    set_state(user_id, None)
    if database.set_avatar(slot, file_id):
        bot.send_message(user_id,
                         f"✅ Bot image #{slot + 1} replaced. It will be used from now on.\n"
                         f"<code>{esc(file_id)}</code>", parse_mode="HTML")
    else:
        bot.send_message(user_id, "❌ Could not replace that image slot.")

# --- VIEWS ---
def view_city(message, edit_msg_id=None):
    user = database.get_user(message.chat.id)
    buildings = database.get_buildings(message.chat.id)
    castle_lvl = buildings.get("castle", 1)
    max_slots = castle_lvl * 5
    used_slots = sum([config.BUILDINGS[k]["slots"] * lvl for k, lvl in buildings.items()])
    t_name = config.TRIBES[user['tribe']]['name']
    txt = (f"<b>🏰 FIEFDOM OVERVIEW</b>\n"
           f"👤 Lord: {esc(get_lord_name(user))} (<code>{user['game_id']}</code>)\n"
           f"🚩 Tribe: {t_name}\n"
           f"{resource_line(user)}\n"
           f"🏗️ Slots: {used_slots}/{max_slots}")
    markup = types.InlineKeyboardMarkup()
    for k, b in config.BUILDINGS.items():
        lvl = buildings.get(k, 0)
        # MG0: show MAX (no cost) once a building hits the level cap.
        if lvl >= config.MAX_BUILDING_LEVEL:
            markup.add(types.InlineKeyboardButton(f"{b['name']} Lv {lvl} (🏛️ MAX)", callback_data=f"build:{k}"))
            continue
        cost = int(b["cost"] * (1.6 ** lvl))
        if user['tribe'] == 'builder': cost = int(cost * config.TRIBES['builder']['value'])
        markup.add(types.InlineKeyboardButton(f"{b['name']} Lv {lvl} (⬆️ {cost}G)", callback_data=f"build:{k}"))
    markup.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh:city"))
    safe_render(message.chat.id, txt, markup, edit_msg_id)

def view_army(message, edit_msg_id=None):
    user = database.get_user(message.chat.id)
    units = database.get_units(message.chat.id)
    buildings = database.get_buildings(message.chat.id)
    
    # Requirements that gate recruitment (mirrors the recruit callback checks).
    def unit_lock(u_key):
        if u_key == "knight" and buildings.get("blacksmith", 0) < 1:
            return "Blacksmith"
        if u_key in ("man_at_arms", "pikeman") and buildings.get("barracks", 0) < 1:
            return "Barracks"
        if u_key == "spy" and buildings.get("castle", 0) < 2:
            return "Castle Lv2"
        return None
    
    # Get current stance (default to standard if missing)
    current_stance = user.get('stance', 'standard')
    stance_name = config.STANCE_STATS.get(current_stance, {}).get('name', 'Standard')

    txt = f"<b>⚔️ BARRACKS</b>\n{resource_line(user)}\n\n"
    txt += f"🛡️ <b>Defensive Stance:</b> {stance_name}\n"
    txt += "<i>(This tactic is used when you are attacked)</i>\n\n"
    txt += "Forces:\n"
    for k, v in units.items():
        if v > 0: txt += f"- {config.UNITS[k]['name']}: {v}\n"
        
    markup = types.InlineKeyboardMarkup()
    # Stance Switcher Row
    markup.row(
        types.InlineKeyboardButton("🛡️ Phalanx", callback_data="set_stance:defensive"),
        types.InlineKeyboardButton("⚔️ Aggressive", callback_data="set_stance:aggressive")
    )
    markup.row(
        types.InlineKeyboardButton("⚖️ Standard", callback_data="set_stance:standard"),
        types.InlineKeyboardButton("🐎 Skirmish", callback_data="set_stance:mobile")
    )
    
    # Recruit Rows — show gold (and iron, where applicable) cost.
    for k, u in config.UNITS.items():
        lock = unit_lock(k)
        if lock:
            label = f"🔒 {u['name']} — needs {lock}"
        else:
            iron_c = config.IRON_COST_PER_UNIT.get(k, 0)
            cost_str = f"{u['cost']}G" + (f" + {iron_c}⛓️" if iron_c else "")
            label = f"Recruit {u['name']} ({cost_str})"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"recruit:{k}"))
    markup.add(types.InlineKeyboardButton("✝️ Blessings", callback_data="blessings:menu"))
    markup.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh:army"))
    
    safe_render(message.chat.id, txt, markup, edit_msg_id)

def view_map(message, edit_msg_id=None):
    conn = database.get_db()
    c = conn.cursor()
    c.execute("SELECT user_id, username, game_id, tribe FROM users WHERE user_id != ? AND setup_complete = 1 ORDER BY RANDOM() LIMIT 5", (message.chat.id,))
    targets = c.fetchall()
    conn.close()
    markup = types.InlineKeyboardMarkup()
    if not targets:
        markup.add(types.InlineKeyboardButton("No other lords found.", callback_data="none"))
    else:
        for t in targets:
            markup.add(
                types.InlineKeyboardButton(f"📜 {t['username']} ({t['game_id']})", callback_data=f"profile:{t['user_id']}"),
                types.InlineKeyboardButton(f"⚔️ ATTACK", callback_data=f"pre_attack:{t['user_id']}")
            )
    markup.add(types.InlineKeyboardButton("🔄 Refresh Map", callback_data="refresh:map"))
    safe_render(message.chat.id, "<b>🗺️ WAR MAP</b>", markup, edit_msg_id)

def view_reports(message):
    conn = database.get_db()
    c = conn.cursor()
    c.execute("SELECT id, text FROM reports WHERE user_id = ? ORDER BY id DESC LIMIT 5", (message.chat.id,))
    reports = c.fetchall()
    conn.close()
    if not reports:
        bot.send_message(message.chat.id, "No new intelligence.")
    else:
        for r in reports:
            bot.send_message(message.chat.id, r['text'], parse_mode="HTML")
        # Reports are NOT auto-deleted, so players can re-read them.
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑️ Clear Reports", callback_data="reports_clear"))
        bot.send_message(message.chat.id,
                         "📜 <i>End of reports. They stay here until you clear them.</i>",
                         parse_mode="HTML", reply_markup=markup)

def enter_tavern(message):
    set_state(message.chat.id, "chatting")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 Exit Tavern")
    bot.send_message(
        message.chat.id,
        "<b>🍻 THE TAVERN</b>\n<i>You will receive Tavern messages until you leave.</i>",
        parse_mode="HTML",
        reply_markup=markup
    )

    msgs = database.get_chat_messages(limit=5)
    if msgs:
        bot.send_message(message.chat.id, "<i>Last 5 Tavern messages:</i>", parse_mode="HTML")
        for m in msgs:
            bot.send_message(
                message.chat.id,
                format_tavern_message(m, m['message']),
                parse_mode="HTML",
                disable_web_page_preview=True
            )

def view_alliance(message, edit_msg_id=None):
    user_id = message.chat.id
    user = database.get_user(user_id)
    markup = types.InlineKeyboardMarkup()

    if user.get('alliance_id'):
        alliance = database.get_alliance(user['alliance_id'])
        if not alliance:
            # Stale reference (alliance disbanded); clear it
            conn = database.get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET alliance_id = NULL WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return view_alliance(message, edit_msg_id)

        members = database.get_alliance_members(alliance['id'])
        is_leader = alliance['leader_id'] == user_id
        txt = (f"🤝 <b>{esc(alliance['name'])}</b> [{esc(alliance['tag'])}]\n"
               f"👑 Leader: {'You' if is_leader else 'Another Lord'}\n"
               f"👥 Members: {len(members)}/{config.MAX_ALLIANCE_MEMBERS}\n\n"
               f"<b>Roster:</b>\n")
        for m in members:
            name = esc(m['display_name'] or m['username'])
            crown = "👑 " if m['user_id'] == alliance['leader_id'] else "• "
            txt += f"{crown}{name} (<code>{m['game_id']}</code>)\n"
        leave_label = "💥 Disband Alliance" if is_leader else "🚪 Leave Alliance"
        markup.add(types.InlineKeyboardButton(leave_label, callback_data="alliance:leave"))
    else:
        txt = ("🤝 <b>ALLIANCES</b>\n\n"
               "You are not part of any alliance.\n\n"
               "Band together with other lords for glory. Alliance members "
               "cannot attack or spy on each other.\n\n"
               f"💰 Founding cost: {config.ALLIANCE_CREATE_COST} Gold")
        markup.add(types.InlineKeyboardButton("⚔️ Found Alliance", callback_data="alliance:create"))
        markup.add(types.InlineKeyboardButton("🔗 Join by Tag", callback_data="alliance:join"))

    safe_render(user_id, txt, markup, edit_msg_id)

def view_leaderboard(message, edit_msg_id=None):
    user_id = message.chat.id
    season = database.get_current_season()
    leaders = database.get_leaderboard(limit=10)

    txt = f"🏆 <b>LEADERBOARD — Season {season}</b>\n\n"
    if not leaders or all(l['season_score'] <= 0 for l in leaders):
        txt += "<i>No glory has been earned yet this season. Win battles to climb!</i>\n"
    else:
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        rank = 0
        for l in leaders:
            if l['season_score'] <= 0:
                continue
            badge = medals.get(rank, f"{rank + 1}.")
            name = esc(l['display_name'] or l['username'])
            you = " (You)" if l['user_id'] == user_id else ""
            txt += (f"{badge} <b>{name}</b>{you} — {l['season_score']} pts "
                    f"(W{l['wins']}/L{l['losses']})\n")
            rank += 1

    hof = database.get_hall_of_fame(limit=3)
    if hof:
        txt += "\n<b>🏛️ Hall of Fame</b>\n"
        for h in hof:
            txt += f"S{h['season']}: {esc(h['display_name'])} ({h['score']} pts)\n"

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh:leaderboard"),
        types.InlineKeyboardButton("🎖️ Renown", callback_data="refresh:renown")
    )
    safe_render(user_id, txt, markup, edit_msg_id)

def view_renown_leaderboard(message, edit_msg_id=None):
    """All-time Renown standings (MG2 prestige track — never resets)."""
    user_id = message.chat.id
    leaders = database.get_renown_leaderboard(limit=10)

    txt = "🎖️ <b>RENOWN — All-Time Glory</b>\n<i>Earned from real battles &amp; heists. Never resets.</i>\n\n"
    if not leaders or all(l['renown'] <= 0 for l in leaders):
        txt += "<i>No renown earned yet. Defeat worthy foes to make your name!</i>\n"
    else:
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        rank = 0
        for l in leaders:
            if l['renown'] <= 0:
                continue
            badge = medals.get(rank, f"{rank + 1}.")
            name = esc(l['display_name'] or l['username'])
            you = " (You)" if l['user_id'] == user_id else ""
            txt += f"{badge} <b>{name}</b>{you} — {l['renown']} 🎖️\n"
            rank += 1

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh:renown"),
        types.InlineKeyboardButton("🏆 Season", callback_data="refresh:leaderboard")
    )
    safe_render(user_id, txt, markup, edit_msg_id)

def show_status(message):
    """Quick, always-current snapshot (gold/army/castle/shield) since the
    bottom keyboard cannot display live data."""
    user_id = message.chat.id
    user = database.get_user(user_id)
    units = database.get_units(user_id)
    buildings = database.get_buildings(user_id)

    army_size = sum(v for v in units.values() if v > 0)
    upkeep = sum(units.get(k, 0) * rate for k, rate in config.UPKEEP_PER_UNIT.items())
    grain_upkeep = sum(units.get(k, 0) * rate for k, rate in config.GRAIN_UPKEEP_PER_UNIT.items())

    txt = (f"📊 <b>STATUS</b>\n\n"
           f"👤 {esc(get_lord_name(user))}\n"
           f"{resource_line(user)}\n"
           f"🏰 Castle Lv: {buildings.get('castle', 1)}\n"
           f"⚔️ Total Troops: {army_size}\n"
           f"💸 Upkeep: {upkeep:.1f} gold/min · {grain_upkeep:.1f} 🌾/min")

    shield = protection_remaining(user)
    if shield > 0:
        txt += f"\n🛡️ Newbie Protection: {fmt_duration(shield)} left"

    bot.send_message(user_id, txt, parse_mode="HTML")

def send_mode_choice(chat_id, target_id):
    """After PvP checks pass, let the attacker choose RAID (instant field battle) or
    SIEGE (multi-phase assault that can crack walls). See game_logic.resolve_siege."""
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⚔️ Raid (instant)", callback_data=f"mode:raid:{target_id}"),
        types.InlineKeyboardButton("🏰 Lay Siege", callback_data=f"mode:siege:{target_id}")
    )
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="atk_cancel"))
    bot.send_message(chat_id,
                     "Choose your assault:\n\n"
                     "⚔️ <b>Raid</b> — straight to the field battle (the defender's "
                     "Watchtower fortifies them).\n"
                     "🏰 <b>Siege</b> — build engines (Gold+Iron+Grain) to smash the "
                     "walls first; breach to nullify the fortification and <b>sack</b> for "
                     "extra loot.",
                     parse_mode="HTML", reply_markup=markup)

def render_siege_workshop(chat_id, state, edit_msg_id=None):
    """Engine-funding UI for a siege. Reads state['engines'] and the lord's resources."""
    user = database.get_user(chat_id)
    engines = state.get("engines", {})
    cost = game_logic.siege_cost(engines)
    txt = (f"🏗️ <b>SIEGE WORKSHOP</b>\n{resource_line(user)}\n\n"
           f"Build engines to batter the walls (consumed in the assault):\n\n")
    for ek, e in config.SIEGE_ENGINES.items():
        n = engines.get(ek, 0)
        txt += (f"{e['name']} ×<b>{n}</b> — {e['gold']}💰 {e['iron']}⛓️ {e['grain']}🌾 each "
                f"(wall dmg {e['wall_dmg']})\n")
    txt += (f"\n<b>Total cost:</b> {cost['gold']}💰 {cost['iron']}⛓️ {cost['grain']}🌾\n"
            f"<i>Engines have no field value — bring an army too, then Muster.</i>")
    markup = types.InlineKeyboardMarkup()
    for ek, e in config.SIEGE_ENGINES.items():
        markup.row(
            types.InlineKeyboardButton(f"➖ {e['name']}", callback_data=f"siege_eng:{ek}:-1"),
            types.InlineKeyboardButton(f"➕ {e['name']}", callback_data=f"siege_eng:{ek}:1")
        )
    markup.add(types.InlineKeyboardButton("➡️ Muster Army", callback_data="siege_muster"))
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="atk_cancel"))
    safe_render(chat_id, txt, markup, edit_msg_id)

def begin_siege(chat_id, target_id):
    """Starts the siege flow: army/cooldown checks, then the engine workshop."""
    user_units = database.get_units(chat_id)
    total_power = sum(v for k, v in user_units.items() if config.UNITS[k]['combat_valid'])
    if total_power == 0:
        bot.send_message(chat_id, "❌ You have no army to lead!")
        return
    conn = database.get_db()
    c = conn.cursor()
    c.execute("SELECT timestamp FROM cooldowns WHERE user_id = ? AND target_id = ?", (chat_id, target_id))
    cd = c.fetchone()
    conn.close()
    if cd and (time.time() - cd['timestamp']) < config.ATTACK_COOLDOWN:
        rem = int((config.ATTACK_COOLDOWN - (time.time() - cd['timestamp'])) / 60)
        bot.send_message(chat_id, f"❌ Cooldown! Wait {rem} mins.")
        return
    msg = bot.send_message(chat_id, "🏗️ Mustering siege...", parse_mode="HTML")
    state = {
        "action": "siege_workshop",
        "target_id": target_id,
        "ui_msg_id": msg.message_id,
        "engines": {ek: 0 for ek in config.SIEGE_ENGINES},
    }
    set_state(chat_id, state)
    render_siege_workshop(chat_id, state, edit_msg_id=msg.message_id)

def begin_attack(chat_id, target_id):
    """Opens the troop-selection UI for an attack. Assumes PvP rules have already
    been checked by the caller. Reports army/cooldown problems via a message."""
    user_units = database.get_units(chat_id)
    total_power = sum(v for k, v in user_units.items() if config.UNITS[k]['combat_valid'])
    if total_power == 0:
        bot.send_message(chat_id, "❌ You have no army to lead!")
        return

    conn = database.get_db()
    c = conn.cursor()
    c.execute("SELECT timestamp FROM cooldowns WHERE user_id = ? AND target_id = ?", (chat_id, target_id))
    cd = c.fetchone()
    conn.close()
    if cd and (time.time() - cd['timestamp']) < config.ATTACK_COOLDOWN:
        rem = int((config.ATTACK_COOLDOWN - (time.time() - cd['timestamp'])) / 60)
        bot.send_message(chat_id, f"❌ Cooldown! Wait {rem} mins.")
        return

    msg = bot.send_message(chat_id, "⚔️ <b>PREPARE ATTACK</b>\nSelect your forces:", parse_mode="HTML")
    initial_state = {
        "action": "attack_select",
        "target_id": target_id,
        "ui_msg_id": msg.message_id,
        "selections": {k: 0 for k in config.UNITS},
        "awaiting_unit": None
    }
    set_state(chat_id, initial_state)
    refresh_attack_ui(chat_id, initial_state)

def render_spy_menu(chat_id, target_id, edit_msg_id=None):
    """Renders the espionage mission menu. Assumes PvP rules already checked.
    Edits the given message in place if possible, otherwise sends a new one."""
    user_units = database.get_units(chat_id)
    spy_count = user_units.get("spy", 0)
    if spy_count == 0:
        bot.send_message(chat_id,
            "❌ You have no Rogues! Recruit them in the ⚔️ Army menu (requires Castle Lv2).")
        return False

    target = database.get_user(target_id)
    target_buildings = database.get_buildings(target_id)
    watchtower_lvl = target_buildings.get("watchtower", 0)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👁️ Scout (Gather Intel)", callback_data=f"spy_run:scout:{target_id}"))
    markup.add(types.InlineKeyboardButton("💰 Heist (Steal Gold)", callback_data=f"spy_run:heist:{target_id}"))
    markup.add(types.InlineKeyboardButton("🔥 Sabotage (Damage Building)", callback_data=f"spy_run:sabotage:{target_id}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"profile:{target_id}"))

    defense_hint = "Low" if watchtower_lvl == 0 else ("Medium" if watchtower_lvl < 3 else "High")
    txt = (f"🕵️ <b>ESPIONAGE OPERATIONS</b>\n\n"
           f"Target: <b>{esc(get_lord_name(target))}</b>\n"
           f"Your Rogues: {spy_count}\n"
           f"Enemy Defenses: {defense_hint}\n\n"
           f"<b>Available Missions:</b>\n"
           f"👁️ <b>Scout</b> - Reveal their gold, army, and buildings.\n"
           f"💰 <b>Heist</b> - Steal gold (limited by spy count).\n"
           f"🔥 <b>Sabotage</b> - Attempt to destroy a building.\n\n"
           f"<i>Success depends on your spies vs their Watchtower + counter-spies.</i>")

    if edit_msg_id:
        try:
            bot.edit_message_caption(caption=txt, chat_id=chat_id,
                                     message_id=edit_msg_id, parse_mode="HTML", reply_markup=markup)
            return True
        except Exception:
            pass
    bot.send_message(chat_id, txt, parse_mode="HTML", reply_markup=markup)
    return True

# --- CALLBACK HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        # Full lockout: banned lords get no response (the admin is never locked out).
        if database.is_banned(call.message.chat.id) and call.message.chat.id != config.ADMIN_ID:
            try:
                bot.answer_callback_query(call.id, "⛔ You are banned.", show_alert=True)
            except Exception:
                pass
            return
        parts = call.data.split(':')
        if parts[0] == "admin":
            if call.message.chat.id != config.ADMIN_ID: return # Double security
            
            if parts[1] == "start_gold":
                # Set state to wait for Game ID input
                set_state(call.message.chat.id, {"action": "admin_find_user"})
                bot.send_message(call.message.chat.id, "📝 Enter the target <b>Game ID</b> (e.g. XXX-XXX):", parse_mode="HTML")
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "broadcast":
                set_state(call.message.chat.id, {"action": "admin_broadcast"})
                bot.send_message(call.message.chat.id,
                                 "📢 <b>BROADCAST</b>\nType the message to send to <b>all lords</b>:",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "msg_player":
                set_state(call.message.chat.id, {"action": "admin_dm_find"})
                bot.send_message(call.message.chat.id,
                                 "✉️ <b>MESSAGE A PLAYER</b>\nEnter the target <b>Game ID</b> (e.g. XXX-XXX):",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "msg_alliance":
                set_state(call.message.chat.id, {"action": "admin_alliance_find"})
                bot.send_message(call.message.chat.id,
                                 "🤝 <b>MESSAGE AN ALLIANCE</b>\nEnter the alliance <b>TAG</b>:",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "ban":
                set_state(call.message.chat.id, {"action": "admin_ban_find"})
                bot.send_message(call.message.chat.id,
                                 "🚫 <b>BAN PLAYER</b>\nEnter the target <b>Game ID</b> to ban:",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "unban":
                set_state(call.message.chat.id, {"action": "admin_unban_find"})
                bot.send_message(call.message.chat.id,
                                 "✅ <b>UNBAN PLAYER</b>\nEnter the target <b>Game ID</b> to unban:",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "get_media":
                set_state(call.message.chat.id, {"action": "admin_get_media"})
                bot.send_message(call.message.chat.id,
                                 "🆔 <b>GET MEDIA ID</b>\nSend me any photo (or media). I'll reply with its "
                                 "<code>file_id</code> — useful for swapping bot images.",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "images":
                set_state(call.message.chat.id, None)
                send_admin_image_view(call.message.chat.id, 0)
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "bulk_avatars":
                set_state(call.message.chat.id, {"action": "admin_bulk_avatars", "collected": []})
                mk = types.InlineKeyboardMarkup()
                mk.add(types.InlineKeyboardButton("✅ Finish & Install", callback_data="admin:bulk_finish"))
                mk.add(types.InlineKeyboardButton("❌ Cancel", callback_data="admin:bulk_cancel"))
                bot.send_message(call.message.chat.id,
                                 "♻️ <b>RE-UPLOAD ALL AVATARS</b>\n\nSend me the avatar photos "
                                 "<b>one at a time</b> (each as a photo). I'll collect them in order.\n\n"
                                 "Tap <b>✅ Finish &amp; Install</b> when done — this <b>replaces the entire</b> "
                                 "avatar gallery shown at signup.\n\nCollected so far: <b>0</b>",
                                 parse_mode="HTML", reply_markup=mk)
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "bulk_finish":
                st = get_state(call.message.chat.id)
                collected = st.get("collected", []) if isinstance(st, dict) else []
                if not collected:
                    bot.answer_callback_query(call.id, "Send at least one photo first.", show_alert=True)
                    return
                n = database.replace_all_avatars(collected)
                set_state(call.message.chat.id, None)
                bot.answer_callback_query(call.id)
                bot.send_message(call.message.chat.id,
                                 f"✅ Installed <b>{n}</b> new avatar(s). New lords will see them at signup.",
                                 parse_mode="HTML", reply_markup=main_menu())
                return

            if parts[1] == "bulk_cancel":
                set_state(call.message.chat.id, None)
                bot.answer_callback_query(call.id, "Cancelled.")
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                return

            if parts[1] == "preview_avatars":
                # Send every current avatar so the admin can confirm this bot can render them.
                set_state(call.message.chat.id, None)
                bot.answer_callback_query(call.id)
                avatars = database.get_avatars()
                ok = fail = 0
                for i, fid in enumerate(avatars):
                    try:
                        bot.send_photo(call.message.chat.id, fid, caption=f"Avatar #{i + 1} of {len(avatars)}")
                        ok += 1
                    except Exception as e:
                        fail += 1
                        print(f"[IronDominion] preview avatar #{i+1} failed: {e}")
                if fail == 0:
                    summary = f"✅ All <b>{ok}</b> avatars sent fine — the signup carousel will work."
                else:
                    summary = (f"⚠️ <b>{ok}</b> sent, <b>{fail}</b> failed. The failed ones can't be rendered "
                               f"by this bot — use <b>♻️ Re-upload All Avatars</b> to replace them.")
                bot.send_message(call.message.chat.id, summary, parse_mode="HTML")
                return

            if parts[1] == "new_season":
                season = database.get_current_season()
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("✅ Confirm Reset", callback_data="admin:new_season_confirm"),
                    types.InlineKeyboardButton("❌ Cancel", callback_data="admin:new_season_cancel")
                )
                bot.send_message(call.message.chat.id,
                                 f"🏆 <b>START SEASON {season + 1}?</b>\n\n"
                                 f"This archives the current top 3 into the Hall of Fame and "
                                 f"resets all season scores, wins and losses.\n"
                                 f"<i>Kingdoms (gold, buildings, army) are NOT affected.</i>",
                                 parse_mode="HTML", reply_markup=markup)
                bot.answer_callback_query(call.id)
                return

            if parts[1] == "new_season_cancel":
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass
                bot.answer_callback_query(call.id, "Cancelled.")
                return

            if parts[1] == "new_season_confirm":
                new_season, leaders = database.start_new_season()
                champ = ""
                if leaders and leaders[0]['season_score'] > 0:
                    top = leaders[0]
                    champ = f"\n🥇 Champion: {top['display_name'] or top['username']} ({top['season_score']} pts)"
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass
                bot.send_message(call.message.chat.id,
                                 f"✅ <b>Season {new_season} has begun!</b>{champ}",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
                return
        action = parts[0]

        if action == "setup":
            sub_action = parts[1]
            if sub_action == "tribe":
                tribe_key = parts[2]
                conn = database.get_db()
                c = conn.cursor()
                c.execute("UPDATE users SET tribe = ? WHERE user_id = ?", (tribe_key, call.message.chat.id))
                conn.commit()
                conn.close()
                # Resilient avatar step: photo carousel if images load, else a text picker,
                # so a new lord is NEVER hard-blocked at setup.
                if render_avatar_picker(call.message.chat.id):
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except Exception:
                        pass
                else:
                    bot.send_message(call.message.chat.id, "⚠️ Couldn't open the avatar picker. Please try /start again.")

            elif sub_action == "av":
                move_type = parts[2]
                index = int(parts[3])
                if move_type == "move":
                    # Same resilient renderer (handles photo OR text-mode messages).
                    render_avatar_picker(call.message.chat.id, index, edit_msg_id=call.message.message_id)
                elif move_type == "sel":
                    sel_fid = database.get_avatars()[index]
                    conn = database.get_db()
                    c = conn.cursor()
                    c.execute("UPDATE users SET avatar_id = ?, setup_complete = 1 WHERE user_id = ?", (sel_fid, call.message.chat.id))
                    conn.commit()
                    conn.close()
                    try:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                    except Exception:
                        pass
                    bot.send_message(call.message.chat.id, "✅ <b>Identity Established.</b>\nWelcome to your lands, My Lord.", parse_mode="HTML", reply_markup=main_menu())

        elif action == "aimg":
            # Admin-only bot image library (carousel + replace flow).
            if call.message.chat.id != config.ADMIN_ID:
                bot.answer_callback_query(call.id)
                return
            sub = parts[1]
            if sub == "move":
                send_admin_image_view(call.message.chat.id, int(parts[2]),
                                      edit_msg_id=call.message.message_id)
                bot.answer_callback_query(call.id)
            elif sub == "sel":
                slot = int(parts[2])
                set_state(call.message.chat.id, {"action": "admin_set_image", "slot": slot})
                cancel_markup = types.InlineKeyboardMarkup()
                cancel_markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="aimg:cancel"))
                bot.send_message(call.message.chat.id,
                                 f"🖼️ <b>REPLACE IMAGE #{slot + 1}</b>\n\n"
                                 f"Send me the new photo. It will be used from now on instead of the "
                                 f"current image #{slot + 1}.",
                                 parse_mode="HTML", reply_markup=cancel_markup)
                bot.answer_callback_query(call.id)
            elif sub == "cancel":
                set_state(call.message.chat.id, None)
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                bot.answer_callback_query(call.id, "Cancelled.")
            elif sub == "close":
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                bot.answer_callback_query(call.id)

        elif action == "reports_clear":
            conn = database.get_db()
            c = conn.cursor()
            c.execute("DELETE FROM reports WHERE user_id = ?", (call.message.chat.id,))
            conn.commit()
            conn.close()
            try:
                bot.edit_message_text("📜 <i>Reports cleared.</i>", call.message.chat.id,
                                      call.message.message_id, parse_mode="HTML")
            except:
                pass
            bot.answer_callback_query(call.id, "Reports cleared.")

        elif action == "refresh":
            if parts[1] == "city":
                view_city(call.message, edit_msg_id=call.message.message_id)
            elif parts[1] == "army":
                view_army(call.message, edit_msg_id=call.message.message_id)
            elif parts[1] == "map":
                view_map(call.message, edit_msg_id=call.message.message_id)
            elif parts[1] == "leaderboard":
                view_leaderboard(call.message, edit_msg_id=call.message.message_id)
            elif parts[1] == "renown":
                view_renown_leaderboard(call.message, edit_msg_id=call.message.message_id)

        elif action == "alliance":
            sub = parts[1]
            user_id = call.message.chat.id
            if sub == "create":
                set_state(user_id, "alliance_create_name")
                bot.send_message(user_id,
                                 "🤝 <b>FOUND AN ALLIANCE</b>\n\nEnter a name (3-24 characters):",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
            elif sub == "join":
                set_state(user_id, "alliance_join")
                bot.send_message(user_id,
                                 "🔗 <b>JOIN ALLIANCE</b>\n\nEnter the alliance TAG:",
                                 parse_mode="HTML")
                bot.answer_callback_query(call.id)
            elif sub == "leave":
                ok, msg = database.leave_alliance(user_id)
                bot.answer_callback_query(call.id)
                try:
                    bot.delete_message(user_id, call.message.message_id)
                except:
                    pass
                if ok and msg == "disbanded":
                    bot.send_message(user_id, "💥 Your alliance has been disbanded.", reply_markup=main_menu())
                elif ok:
                    bot.send_message(user_id, "🚪 You have left your alliance.", reply_markup=main_menu())
                else:
                    bot.send_message(user_id, f"❌ {msg}", reply_markup=main_menu())

        elif action == "set_stance":
            new_stance = parts[1]
            conn = database.get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET stance = ? WHERE user_id = ?", (new_stance, call.message.chat.id))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, f"Stance set to {new_stance.title()}")
            view_army(call.message, edit_msg_id=call.message.message_id)
        elif action == "profile":
            target_id = int(parts[1])
            target = database.get_user(target_id)
            if target:
                send_profile_view(call.message.chat.id, target)
            else:
                bot.answer_callback_query(call.id, "User not found.")

        elif action == "dm":
            target_id = int(parts[1])
            set_state(call.message.chat.id, {"action": "dm_write", "target_id": target_id})
            
            # Add Cancel Button
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="dm_cancel"))
            
            bot.send_message(call.message.chat.id, "📝 <b>COMPOSE MESSAGE</b>\nWrite your message below:", parse_mode="HTML", reply_markup=markup)
            bot.answer_callback_query(call.id)
        elif action == "dm_cancel":
            set_state(call.message.chat.id, None)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "Message cancelled.")
        elif action == "edit":
            sub = parts[1]
            user_id = call.message.chat.id
            user = database.get_user(user_id)
            
            if sub == "name":
                # Start the rename flow
                set_state(user_id, {"action": "rename_profile"})
                bot.send_message(user_id, 
                                "✏️ <b>CHANGE TITLE</b>\n\nEnter your new Lord name (2-20 characters):", 
                                parse_mode="HTML")
                bot.answer_callback_query(call.id)
                
            elif sub == "av_prev" or sub == "av_next":
                current_idx = int(parts[2])
                avatar_ids = database.get_avatars()

                # Calculate new index with wraparound
                if sub == "av_prev":
                    new_idx = current_idx - 1
                    if new_idx < 0:
                        new_idx = len(avatar_ids) - 1
                else:
                    new_idx = current_idx + 1
                    if new_idx >= len(avatar_ids):
                        new_idx = 0

                new_avatar = avatar_ids[new_idx]
                
                # Save new avatar to database
                conn = database.get_db()
                c = conn.cursor()
                c.execute("UPDATE users SET avatar_id = ? WHERE user_id = ?", (new_avatar, user_id))
                conn.commit()
                conn.close()
                
                # Rebuild the profile caption with fresh data
                user = database.get_user(user_id)
                buildings = database.get_buildings(user_id)
                units = database.get_units(user_id)
                power = game_logic.calculate_power_score(buildings)
                castle_lvl = buildings.get('castle', 1)
                t_name = config.TRIBES[user['tribe']]['name']
                lord_name = get_lord_name(user)
                join_dt = datetime.fromtimestamp(user['joined_date'])
                date_str = join_dt.strftime("%b %Y")
                total_troops = sum(v for k, v in units.items() if config.UNITS[k]['combat_valid'])
                spy_count = units.get('spy', 0)
                current_stance = config.STANCE_STATS.get(user.get('stance', 'standard'), {}).get('name', 'Standard')

                caption = (f"👤 <b>MY PROFILE</b>\n\n"
                           f"⚜️ <b>{lord_name}</b>\n"
                           f"🆔 ID: <code>{user['game_id']}</code>\n"
                           f"🚩 Tribe: {t_name}\n"
                           f"📅 Joined: {date_str}\n\n"
                           f"<b>Kingdom Status:</b>\n"
                           f"💰 Gold: {int(user['gold'])}\n"
                           f"🏰 Castle Level: {castle_lvl}\n"
                           f"⚔️ Army Size: {total_troops}\n"
                           f"🕵️ Rogues: {spy_count}\n"
                           f"🛡️ Stance: {current_stance}\n"
                           f"📈 Power Score: {power}")
                
                # Rebuild markup with updated index
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("✏️ Change Name", callback_data="edit:name"))
                markup.row(
                    types.InlineKeyboardButton("⬅️ Prev Face", callback_data=f"edit:av_prev:{new_idx}"),
                    types.InlineKeyboardButton("Next Face ➡️", callback_data=f"edit:av_next:{new_idx}")
                )
                markup.add(types.InlineKeyboardButton("🔙 Close", callback_data="edit:close"))
                
                # Update the photo in-place
                try:
                    media = types.InputMediaPhoto(new_avatar, caption=caption, parse_mode="HTML")
                    bot.edit_message_media(media=media, chat_id=user_id, 
                                           message_id=call.message.message_id, reply_markup=markup)
                    bot.answer_callback_query(call.id, "✅ Avatar updated!")
                except Exception as e:
                    print(f"[IronDominion] avatar update failed: {e}")
                    bot.answer_callback_query(call.id, "⚠️ Couldn't update your avatar. Please try again.", show_alert=True)
                
            elif sub == "close":
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id)

        elif action == "spy_menu":
            target_id = int(parts[1])
            user_id = call.message.chat.id

            allowed, reason, code = check_pvp_allowed(user_id, target_id)
            if not allowed:
                if code == "self_shield":
                    send_waive_prompt(user_id, target_id, "spy")
                    bot.answer_callback_query(call.id)
                else:
                    bot.answer_callback_query(call.id, reason, show_alert=True)
                return

            render_spy_menu(user_id, target_id, edit_msg_id=call.message.message_id)
            bot.answer_callback_query(call.id)

        elif action == "spy_run":
            mission = parts[1]  # scout, heist, or sabotage
            target_id = int(parts[2])
            user_id = call.message.chat.id

            allowed, reason, code = check_pvp_allowed(user_id, target_id)
            if not allowed:
                bot.answer_callback_query(call.id, reason, show_alert=True)
                return

            # Espionage cooldown (namespaced from attacks via -target_id)
            conn = database.get_db()
            c = conn.cursor()
            c.execute("SELECT timestamp FROM cooldowns WHERE user_id = ? AND target_id = ?", (user_id, -target_id))
            scd = c.fetchone()
            conn.close()
            if scd and (time.time() - scd['timestamp']) < config.SPY_COOLDOWN:
                rem = int((config.SPY_COOLDOWN - (time.time() - scd['timestamp'])) / 60)
                bot.answer_callback_query(call.id, f"❌ Spies recovering! Wait {rem} mins.", show_alert=True)
                return

            user_units = database.get_units(user_id)
            spy_count = user_units.get("spy", 0)
            
            mission_names = {
                "scout": "👁️ Scout Mission",
                "heist": "💰 Heist Mission", 
                "sabotage": "🔥 Sabotage Mission"
            }
            
            mission_desc = {
                "scout": "Gather intelligence on the target.",
                "heist": f"Each surviving spy can carry up to {config.SPY_CARRY_CAP} gold.",
                "sabotage": f"{config.SABOTAGE_CHANCE}% chance to destroy a random building."
            }
            
            prompt = bot.send_message(
                user_id,
                f"🕵️ <b>{mission_names[mission]}</b>\n\n"
                f"{mission_desc[mission]}\n\n"
                f"Available Rogues: <code>{spy_count}</code>\n\n"
                f"✏️ Reply with how many rogues to send:",
                parse_mode="HTML"
            )
            
            set_state(user_id, {
                "action": "spy_input",
                "mission": mission,
                "target_id": target_id,
                "prompt_id": prompt.message_id
            })
            
            # Clean up the menu message
            try:
                bot.delete_message(user_id, call.message.message_id)
            except:
                pass
            
            bot.answer_callback_query(call.id)

        elif action == "build":
            b_key = parts[1]
            user = database.get_user(call.message.chat.id)
            buildings = database.get_buildings(call.message.chat.id)
            allowed, msg = game_logic.can_build(user['gold'], buildings, b_key, user['tribe'])
            if allowed:
                cost = msg
                conn = database.get_db()
                c = conn.cursor()
                # DECLARED SINK (MG4): building cost gold is destroyed, not transferred.
                c.execute("UPDATE users SET gold = gold - ? WHERE user_id = ?", (cost, call.message.chat.id))
                c.execute("UPDATE buildings SET level = level + 1 WHERE user_id = ? AND b_type = ?", (call.message.chat.id, b_key))
                conn.commit()
                conn.close()
                bot.answer_callback_query(call.id, "Construction complete!")
                bot.delete_message(call.message.chat.id, call.message.message_id)
                view_city(call.message)
            else:
                bot.answer_callback_query(call.id, f"❌ {msg}", show_alert=True)

        elif action == "recruit":
            u_key = parts[1]
            buildings = database.get_buildings(call.message.chat.id)
            if u_key == "knight" and buildings.get("blacksmith", 0) < 1:
                bot.answer_callback_query(call.id, "❌ Requires Blacksmith!", show_alert=True)
                return
            if u_key in ("man_at_arms", "pikeman") and buildings.get("barracks", 0) < 1:
                bot.answer_callback_query(call.id, "❌ Requires Barracks!", show_alert=True)
                return
            if u_key == "spy" and buildings.get("castle", 0) < 2:
                bot.answer_callback_query(call.id, "❌ Requires Castle Lv 2!", show_alert=True)
                return
            
            # Calculate Max (limited by BOTH gold and iron)
            user = database.get_user(call.message.chat.id)
            unit_cost = game_logic.recruit_cost(u_key, 1)
            max_by_gold = int(user['gold'] // unit_cost["gold"]) if unit_cost["gold"] else 999999
            cur_iron = user['iron'] if 'iron' in user.keys() and user['iron'] is not None else 0
            max_by_iron = int(cur_iron // unit_cost["iron"]) if unit_cost["iron"] else 999999
            max_amt = max(0, min(max_by_gold, max_by_iron))
            cost_str = f"{unit_cost['gold']}G" + (f" + {unit_cost['iron']}⛓️" if unit_cost["iron"] else "")

            prompt = bot.send_message(
                call.message.chat.id, 
                f"Recruiting <b>{config.UNITS[u_key]['name']}</b> ({cost_str} each).\nMax: <code>{max_amt}</code>\n\n✏️ Reply with how many to recruit:", 
                parse_mode="HTML"
            )
            
            # Save state as dict to store message IDs for deletion later
            set_state(call.message.chat.id, {
                "action": "recruit_input", 
                "unit": u_key, 
                "prompt_id": prompt.message_id,
                "origin_id": call.message.message_id
            })
            bot.answer_callback_query(call.id)

        # --- BLESSINGS (Faith sink) ---
        elif action == "blessings":
            user = database.get_user(call.message.chat.id)
            cur_faith = int(user['faith']) if 'faith' in user.keys() and user['faith'] is not None else 0
            active = database.get_active_blessings(call.message.chat.id)
            txt = (f"✝️ <b>BLESSINGS</b>\nYour Faith: {cur_faith} ✝️\n\n"
                   f"Spend Faith on a temporary blessing. Build a <b>Chapel</b> to "
                   f"generate Faith. Each blessing lasts 1h; only one of each effect.\n")
            markup = types.InlineKeyboardMarkup()
            for bkey, bdef in config.BLESSING_DEFS.items():
                act = "✅ " if bdef['effect'] in active else ""
                markup.add(types.InlineKeyboardButton(
                    f"{act}{bdef['name']} — {bdef['faith']}✝️  ({bdef['desc']})",
                    callback_data=f"bless_buy:{bkey}"))
            markup.add(types.InlineKeyboardButton("🔙 Back to Army", callback_data="refresh:army"))
            safe_render(call.message.chat.id, txt, markup, call.message.message_id)
            bot.answer_callback_query(call.id)

        elif action == "bless_buy":
            bkey = parts[1]
            ok, msg = database.buy_blessing(call.message.chat.id, bkey)
            bot.answer_callback_query(call.id, msg, show_alert=not ok)
            if ok:
                # Refresh the blessings menu in place.
                user = database.get_user(call.message.chat.id)
                cur_faith = int(user['faith']) if 'faith' in user.keys() and user['faith'] is not None else 0
                active = database.get_active_blessings(call.message.chat.id)
                txt = (f"✝️ <b>BLESSINGS</b>\nYour Faith: {cur_faith} ✝️\n\n"
                       f"Spend Faith on a temporary blessing. Build a <b>Chapel</b> to "
                       f"generate Faith. Each blessing lasts 1h; only one of each effect.\n")
                markup = types.InlineKeyboardMarkup()
                for k2, bdef in config.BLESSING_DEFS.items():
                    act = "✅ " if bdef['effect'] in active else ""
                    markup.add(types.InlineKeyboardButton(
                        f"{act}{bdef['name']} — {bdef['faith']}✝️  ({bdef['desc']})",
                        callback_data=f"bless_buy:{k2}"))
                markup.add(types.InlineKeyboardButton("🔙 Back to Army", callback_data="refresh:army"))
                safe_render(call.message.chat.id, txt, markup, call.message.message_id)

        # --- NEW ATTACK LOGIC ---
        elif action == "pre_attack":
            target_id = int(parts[1])

            allowed, reason, code = check_pvp_allowed(call.message.chat.id, target_id)
            if not allowed:
                if code == "self_shield":
                    send_waive_prompt(call.message.chat.id, target_id, "attack")
                    bot.answer_callback_query(call.id)
                else:
                    bot.answer_callback_query(call.id, reason, show_alert=True)
                return

            send_mode_choice(call.message.chat.id, target_id)
            bot.answer_callback_query(call.id)

        elif action == "mode":
            sub = parts[1]
            target_id = int(parts[2])
            allowed, reason, code = check_pvp_allowed(call.message.chat.id, target_id)
            if not allowed:
                bot.answer_callback_query(call.id, reason, show_alert=True)
                return
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            if sub == "siege":
                begin_siege(call.message.chat.id, target_id)
            else:
                begin_attack(call.message.chat.id, target_id)
            bot.answer_callback_query(call.id)

        elif action == "siege_eng":
            user_id = call.message.chat.id
            state = get_state(user_id)
            if not state or state.get("action") != "siege_workshop":
                bot.answer_callback_query(call.id)
                return
            ek = parts[1]
            delta = int(parts[2])
            cur = state["engines"].get(ek, 0)
            state["engines"][ek] = max(0, cur + delta)
            set_state(user_id, state)
            render_siege_workshop(user_id, state, edit_msg_id=state.get("ui_msg_id"))
            bot.answer_callback_query(call.id)

        elif action == "siege_muster":
            user_id = call.message.chat.id
            state = get_state(user_id)
            if not state or state.get("action") != "siege_workshop":
                bot.answer_callback_query(call.id)
                return
            if sum(state["engines"].values()) == 0:
                bot.answer_callback_query(call.id, "❌ Build at least one engine (or Cancel and Raid instead).", show_alert=True)
                return
            # Verify the lord can afford the engines now (final debit happens at resolution).
            cost = game_logic.siege_cost(state["engines"])
            u = database.get_user(user_id)
            have = {k: (u[k] if k in u.keys() and u[k] is not None else 0) for k in ("gold", "iron", "grain")}
            if have["gold"] < cost["gold"] or have["iron"] < cost["iron"] or have["grain"] < cost["grain"]:
                bot.answer_callback_query(call.id, f"❌ Can't afford engines: {cost['gold']}💰 {cost['iron']}⛓️ {cost['grain']}🌾.", show_alert=True)
                return
            # Transition to the shared troop-selection UI, carrying the siege payload.
            new_state = {
                "action": "attack_select",
                "target_id": state["target_id"],
                "ui_msg_id": state.get("ui_msg_id"),
                "selections": {k: 0 for k in config.UNITS},
                "awaiting_unit": None,
                "siege": True,
                "engines": state["engines"],
            }
            set_state(user_id, new_state)
            refresh_attack_ui(user_id, new_state)
            bot.answer_callback_query(call.id)

        elif action == "waive":
            context = parts[1]
            target_id = int(parts[2])
            user_id = call.message.chat.id
            database.waive_protection(user_id)
            try:
                bot.delete_message(user_id, call.message.message_id)
            except Exception:
                pass
            # Re-validate now that the shield is gone (target could still be shielded/ally).
            allowed, reason, code = check_pvp_allowed(user_id, target_id)
            if not allowed:
                bot.answer_callback_query(call.id, reason, show_alert=True)
                return
            bot.answer_callback_query(call.id, "🛡️ Shield lifted.")
            if context == "attack":
                send_mode_choice(user_id, target_id)
            else:
                render_spy_menu(user_id, target_id)

        elif action == "waive_cancel":
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.answer_callback_query(call.id, "🛡️ Shield kept.")

        elif action == "atk_hint":
            bot.answer_callback_query(call.id, "Use ➖ / ➕ / Max or ✏️ Type exact to set the amount.")

        elif action in ("ignore", "none"):
            bot.answer_callback_query(call.id)

        elif action == "atk_inc":
            u_key = parts[1]
            delta = parts[2]
            user_id = call.message.chat.id
            state = get_state(user_id)
            if not state or state.get("action") != "attack_select":
                bot.answer_callback_query(call.id)
                return
            
            units = database.get_units(user_id)
            max_amt = units.get(u_key, 0)
            current = state["selections"].get(u_key, 0)
            
            if delta == "max":
                new_val = max_amt
            elif delta == "zero":
                new_val = 0
            else:
                new_val = current + int(delta)
            
            new_val = max(0, min(new_val, max_amt))
            state["selections"][u_key] = new_val
            set_state(user_id, state)
            refresh_attack_ui(user_id, state)
            bot.answer_callback_query(call.id)

        elif action == "atk_set":
            u_key = parts[1]
            user_id = call.message.chat.id
            state = get_state(user_id)
            if not state or state.get("action") != "attack_select":
                bot.answer_callback_query(call.id)
                return
            
            units = database.get_units(user_id)
            max_amt = units.get(u_key, 0)
            
            # Plain prompt (NOT ForceReply) so the bottom menu keyboard is never removed.
            prompt = bot.send_message(
                user_id, 
                f"✏️ Reply with the number of <b>{config.UNITS[u_key]['name']}</b> to send.\nMax: <code>{max_amt}</code>", 
                parse_mode="HTML"
            )
            
            state["awaiting_unit"] = u_key
            state["prompt_msg_id"] = prompt.message_id
            set_state(user_id, state)
            bot.answer_callback_query(call.id)

        elif action == "atk_cancel":
            set_state(call.message.chat.id, None)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            bot.send_message(call.message.chat.id, "Attack cancelled.", reply_markup=main_menu())
            bot.answer_callback_query(call.id)

        elif action == "atk_tactics":
            # Show Stance Selection Menu
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🤖 Auto-Command (Standard)", callback_data="atk_final:standard"),
                types.InlineKeyboardButton("⚔️ Aggressive", callback_data="atk_final:aggressive"),
                types.InlineKeyboardButton("🛡️ Phalanx", callback_data="atk_final:defensive"),
                types.InlineKeyboardButton("🐎 Skirmish", callback_data="atk_final:mobile")
            )
            markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="atk_back"))
            
            bot.edit_message_text("<b>⚔️ WAR COUNCIL</b>\nChoose your Battle Stance:", 
                                  call.message.chat.id, call.message.message_id, 
                                  parse_mode="HTML", reply_markup=markup)

        elif action == "atk_back":
            # Go back to unit selection
            user_id = call.message.chat.id
            state = get_state(user_id)
            refresh_attack_ui(user_id, state)

        elif action == "atk_final":
            atk_stance = parts[1] # Get the stance chosen by button
            
            user_id = call.message.chat.id
            state = get_state(user_id)
            if not state or state.get("action") != "attack_select": return

            selections = state["selections"]
            if sum(selections.values()) == 0:
                bot.answer_callback_query(call.id, "❌ Select at least 1 unit!", show_alert=True)
                return
            
            target_id = state["target_id"]

            allowed, reason, code = check_pvp_allowed(user_id, target_id)
            if not allowed:
                bot.answer_callback_query(call.id, reason, show_alert=True)
                set_state(user_id, None)
                try:
                    bot.delete_message(user_id, call.message.message_id)
                except:
                    pass
                return

            attacker = database.get_user(user_id)
            defender = database.get_user(target_id)
            def_units = database.get_units(target_id)
            atk_buildings = database.get_buildings(user_id)
            def_buildings = database.get_buildings(target_id)

            # Get Defender's Stance from DB
            def_stance = defender.get('stance', 'standard')

            # Blessing multipliers (temporary Faith buffs) for both sides.
            atk_combat = database.get_blessing_combat_mult(user_id)
            def_combat = database.get_blessing_combat_mult(target_id)
            def_ward   = database.get_blessing_defense_mult(target_id)

            is_siege = bool(state.get("siege"))
            engines = state.get("engines", {})
            breached = False
            engine_losses = {}

            if is_siege:
                # DECLARED SINK (MG4): pay for the engines now (atomic, re-checked).
                cost = game_logic.siege_cost(engines)
                ok, msg = database.spend_resources(user_id, gold=cost["gold"], iron=cost["iron"], grain=cost["grain"])
                if not ok:
                    bot.answer_callback_query(call.id, f"❌ {msg}", show_alert=True)
                    set_state(user_id, None)
                    try: bot.delete_message(user_id, call.message.message_id)
                    except: pass
                    return
                # PHASE 1-2: bombardment then field battle (fortify nullified if breached).
                winner, breached, log, atk_loss_dict, def_loss_dict, engine_losses = game_logic.resolve_siege(
                    selections, def_units,
                    engines, attacker['tribe'], defender['tribe'],
                    atk_stance, def_stance,
                    def_buildings=def_buildings, atk_buildings=atk_buildings,
                    atk_combat_mult=atk_combat, def_combat_mult=def_combat, def_ward_keep=def_ward
                )
            else:
                # --- RAID: straight to the field battle ---
                # MG6: defender's buildings (watchtower) fortify them in battle.
                winner, log, atk_loss_dict, def_loss_dict = game_logic.simulate_battle(
                    selections, def_units, 
                    attacker['tribe'], defender['tribe'],
                    atk_stance, def_stance,
                    def_buildings=def_buildings, atk_buildings=atk_buildings,
                    atk_combat_mult=atk_combat, def_combat_mult=def_combat, def_ward_keep=def_ward
                )
            
            conn = database.get_db()
            c = conn.cursor()
            
            total_atk_dead = 0
            for u_key, died in atk_loss_dict.items():
                c.execute("UPDATE units SET count = MAX(0, count - ?) WHERE user_id = ? AND u_type = ?", (died, user_id, u_key))
                total_atk_dead += died
                
            total_def_dead = 0
            for u_key, died in def_loss_dict.items():
                c.execute("UPDATE units SET count = MAX(0, count - ?) WHERE user_id = ? AND u_type = ?", (died, target_id, u_key))
                total_def_dead += died

            loot = 0
            if winner == "Attacker":
                # Re-read defender gold inside the transaction (atomic) and apply Vault protection
                c.execute("SELECT gold FROM users WHERE user_id = ?", (target_id,))
                row = c.fetchone()
                cur_gold = row['gold'] if row else 0
                def_buildings = database.get_buildings(target_id)
                castle_lvl = def_buildings.get('castle', 1)
                # A successful SIEGE BREACH halves the vault and loots a bigger share.
                if is_siege and breached:
                    safe_gold = int(castle_lvl * config.SAFE_GOLD_PER_LEVEL * config.SIEGE_SACK_VAULT_MULT)
                    loot_pct = config.SIEGE_SACK_LOOT_PCT
                else:
                    safe_gold = castle_lvl * config.SAFE_GOLD_PER_LEVEL
                    loot_pct = config.LOOT_PERCENTAGE
                exposed = max(0, cur_gold - safe_gold)
                loot = int(exposed * loot_pct)
                if loot > 0:
                    c.execute("UPDATE users SET gold = MAX(0, gold - ?) WHERE user_id = ?", (loot, target_id))
                    c.execute("UPDATE users SET gold = gold + ? WHERE user_id = ?", (loot, user_id))
            
            now = time.time()
            
            # --- NEW REPORT LOGIC ---
            log_text = "\n".join(log)
            
            # 1. Attacker Report
            if winner == "Attacker":
                atk_header = "🏆 <b>VICTORY!</b>"
                atk_body = f"You crushed the forces of {esc(defender['username'])}!"
            else:
                atk_header = "💀 <b>DEFEAT!</b>"
                atk_body = f"Your army was broken by {esc(defender['username'])}."

            atk_rep = f"{atk_header}\n\n{atk_body}\n{log_text}\n\n💀 Your Losses: {total_atk_dead}\n💰 Loot: {loot}"
            c.execute("INSERT INTO reports (user_id, text, timestamp) VALUES (?, ?, ?)", (user_id, atk_rep, now))
            
            # 2. Defender Report
            if winner == "Defender":
                def_header = "🛡️ <b>DEFENSE SUCCESSFUL!</b>"
                def_body = f"You held the line against {esc(attacker['username'])}!"
            else:
                def_header = "🔥 <b>CITY SACKED!</b>"
                def_body = f"Your defenses failed against {esc(attacker['username'])}."

            def_rep = f"{def_header}\n\n{def_body}\n{log_text}\n\n💀 Your Losses: {total_def_dead}\n📉 Gold Lost: {loot}"
            c.execute("INSERT INTO reports (user_id, text, timestamp) VALUES (?, ?, ?)", (target_id, def_rep, now))
            
            # 1. Restore Cooldown (Prevents infinite attacks)
            c.execute("REPLACE INTO cooldowns (user_id, target_id, timestamp) VALUES (?, ?, ?)", (user_id, target_id, now))
            # 2. CRITICAL: Save and Close (Fixes the freezing/lag)
            conn.commit()
            conn.close()
            # Record battle result for leaderboard / season standings
            # MG2 Renown: award the winner lifetime renown scaled by the
            # DEFEATED army's gold value (so beating real opponents pays,
            # farming tiny armies does not).
            def _army_value(army):
                return sum(config.UNITS[k]['cost'] * cnt
                           for k, cnt in army.items()
                           if cnt > 0 and config.UNITS[k]['combat_valid'])
            if winner == "Attacker":
                renown_gain = max(1, _army_value(def_units) // config.RENOWN_WIN_DIVISOR)
                if is_siege and breached:
                    renown_gain = int(renown_gain * config.SIEGE_BREACH_RENOWN_MULT)
                database.record_battle_result(user_id, target_id, renown_gain=renown_gain)
            else:
                renown_gain = max(1, _army_value(selections) // config.RENOWN_WIN_DIVISOR)
                database.record_battle_result(target_id, user_id, renown_gain=renown_gain)
            # 3. Show result to Attacker and reset their menu
            bot.delete_message(user_id, call.message.message_id)
            set_state(user_id, None)
            bot.send_message(user_id, atk_rep, parse_mode="HTML", reply_markup=main_menu())
            
            # 3. Alert Message (Immediate Notification)
            try:
                alert_text = f"{def_header}\n\nAttacker: {esc(attacker['username'])} (<code>{attacker['game_id']}</code>)\n💀 You lost {total_def_dead} troops.\n💰 Gold lost: {loot}"
                
                alert_markup = types.InlineKeyboardMarkup()
                alert_markup.add(
                    types.InlineKeyboardButton("📜 View Profile", callback_data=f"profile:{user_id}"),
                    types.InlineKeyboardButton("⚔️ Retaliate", callback_data=f"pre_attack:{user_id}")
                )
                bot.send_message(target_id, alert_text, parse_mode="HTML", reply_markup=alert_markup)
            except:
                pass
    except Exception as e:
        print(f"[IronDominion] Callback error on '{call.data}': {e}")
        try:
            bot.answer_callback_query(call.id, "⚠️ Something went wrong. Please try again.", show_alert=True)
        except:
            pass