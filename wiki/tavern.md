# Tavern (Global Chat)

The 🍻 **Tavern** is the game's global chat where all lords can talk.

- Entering sets your state to `chatting`; any text you send (that isn't a menu
  button) is posted to the shared log.
- Messages are capped at **`MAX_CHAT_LENGTH` = 200** characters and are stored in
  the `chat` table with your name and [game ID](profiles.md).
- The view shows the most recent messages (newest last). Leave with
  "🔙 Exit Tavern".

> Private messages between lords (the "💬 Message" button on a [profile](profiles.md))
> are separate and capped at `MAX_DM_LENGTH` = 500.

## See also
[Profiles](profiles.md) · [Architecture: Commands](arch_commands.md) · [Architecture: State machine](arch_state_machine.md)

---
Source: `config.py` (MAX_CHAT_LENGTH, MAX_DM_LENGTH), `database.py` (`add_chat_message`, `get_chat_messages`, `chat` table), `bot.py` (`enter_tavern`, DM flow).
