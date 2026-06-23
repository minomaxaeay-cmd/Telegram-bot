# Tavern (Global Chat)

The 🍻 **Tavern** is the game's global chat where all lords can talk live.

- Entering sets your state to `chatting`; you receive every new Tavern message
  from other lords until you leave with "🔙 Exit Tavern".
- On entry, the bot sends the most recent **5** stored Tavern messages to the
  arriving lord.
- Sending a valid Tavern message stores it in the `chat` table and immediately
  sends that exact message text to every other lord currently in the Tavern.
  Tavern messages are not forwarded Telegram messages, are not grouped into one
  chat-log message, and do not include timestamps.
- Each delivered message is prefixed with the sender in clickable profile-link
  form: `Player1(AXY-UAO): message`. The link uses the sender's Telegram user ID
  so other players can tap it to open that player's Telegram profile.
- Guard rails: messages are capped at **`MAX_CHAT_LENGTH` = 200** characters,
  cannot contain `@` mentions, and cannot contain links such as `http://`,
  `https://`, `www.`, `t.me/`, or `telegram.me/`.

> Private messages between lords (the "💬 Message" button on a [profile](profiles.md))
> are separate and capped at `MAX_DM_LENGTH` = 500.

## See also
[Profiles](profiles.md) · [Architecture: Commands](arch_commands.md) · [Architecture: State machine](arch_state_machine.md)

---
Source: `config.py` (MAX_CHAT_LENGTH, MAX_DM_LENGTH), `database.py` (`add_chat_message`, `get_chat_messages`, `get_tavern_user_ids`, `chat` table), `bot.py` (`enter_tavern`, Tavern validation/broadcast helpers, DM flow).
