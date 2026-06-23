# Tavern (Global Chat)

The 🍻 **Tavern** is the game's global chat where all lords who are currently in
Tavern can talk.

- Entering sets your state to `chatting`; you keep receiving Tavern messages until
  you leave with "🔙 Exit Tavern" or choose another main menu view.
- When a lord sends a Tavern message, the bot stores it and sends that exact text
  to every other lord whose state is still `chatting`. Messages are not forwarded,
  bundled into a refreshed log, or timestamped.
- Each delivered line is prefixed with the sender as a Telegram profile hyperlink
  in the form `PlayerName(XXX-XXX): message`, using the sender's [game ID](profiles.md).
- Tavern guard rails reject messages over **`MAX_CHAT_LENGTH` = 200** characters,
  messages containing `@`, and messages containing links.
- On entry, the arriving lord receives the last **5** stored Tavern messages,
  newest last, before participating in live Tavern delivery.

> Private messages between lords (the "💬 Message" button on a [profile](profiles.md))
> are separate and capped at `MAX_DM_LENGTH` = 500.

## See also
[Profiles](profiles.md) · [Architecture: Commands](arch_commands.md) · [Architecture: State machine](arch_state_machine.md)

---
Source: `config.py` (MAX_CHAT_LENGTH, MAX_DM_LENGTH), `database.py` (`add_chat_message`, `get_chat_messages`, `get_tavern_user_ids`, `chat` table), `bot.py` (`enter_tavern`, Tavern live delivery, DM flow).
