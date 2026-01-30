
import os
import traceback
import discord
from discord.ext import commands

print("STARTING BOT.PY")


FAQ_CHANNEL_ID = 1465977472125374527  # <-- replace with your #faq channel ID

TOKEN = os.getenv("BOT")

if not TOKEN or len(TOKEN) < 50:
    raise ValueError("Missing/invalid token. Set BOT env var.")

FAQ_CONTENT = (
    "**Metryc FAQ**\n"
    "Use the menu below to get quick answers to common questions.\n\n"
    "If your question isn’t listed, check out the Help Center."
)
# ==================


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

FAQ_ANSWERS = {
    "what_is_metryc": (
        "**What is Metryc?**\n\n"
        "Metryc is a conversational AI nutrition and fitness coach designed to help you stay consistent in real life. "
        "You can talk to Metryc just like a normal coach—plan workouts and meals, log what you actually do (by text, photo, barcode, or voice), "
        "and get guidance without rigid flows or manual tracking.\n\n"
        "**Why choose Metryc?**\n"
        "There are fitness and nutrition apps, and then there’s Metryc. Here’s what makes it different:\n"
        "• **A coach you can actually talk to**\n"
        "  Chat like a real coach—ask questions, explain what happened, and get clear guidance in natural language.\n"
        "• **Plan, log, and adjust in one place**\n"
        "  Planning and tracking aren’t separate modes. As you talk about meals or workouts, Metryc updates your plan automatically.\n"
        "• **Less friction, more consistency**\n"
        "  Metryc remembers context, uses reliable nutrition data, and reduces the need to fix or re-enter information.\n"
        "• **Coaching, not just logging**\n"
        "  Metryc helps you decide what to do next, not just record what already happened."
    ),
    "discord_roles":(
    "**What do the Discord roles mean?**\n"
    "Here’s how you can earn different community roles on the Metryc Discord. "
    "These are badges of appreciation — not staff roles — and reflect your contributions or engagement!\n\n"

    "🌐 **Pro**\n"
    "If you’re a Metryc Pro subscriber, click the **Go to Discord** button in your Metryc settings to receive the **@Pro** role.\n"
    "If it doesn’t sync, tag a moderator for help.\n\n"

    "🧭 **Pathfinder**\n"
    "Receive **5 ⭐ reactions** on a message or thread to earn the **@Pathfinder** role.\n"
    "Your post will be featured in **#⭐starred**.\n\n"

    "🐛 **Bug Sniper**\n"
    "Report **5 confirmed bugs** in **#🐛bug-reports** and we’ll assign the **@Bug Sniper** role once your reports are reviewed.\n\n"

    "💡 **Visionary**\n"
    "The **@Visionary** role is for members who share standout product ideas, feature suggestions, or thoughtful feedback.\n"
    "**This role is hand-picked by the Metryc team for creativity and impact.**\n\n"

    "📏 **Metryst**\n"
    "Share a Metryc thread link in **#💌sharing** and you'll automatically be assigned **@Metryst**.\n\n"

    "**Let a moderator know if you believe you earned a role but didn't receive it!**"
),
    "workout_planning": "**Workout planning**\nSet a plan once. Metryc adjusts future sessions as you log.",
    "food_logging": "**Food logging**\nLog by text, photo, barcode, or voice. Metryc keeps context.",
    "pricing": "**Pricing & free trial**\nFree trial, then monthly or yearly plans."
}

class FAQSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="What is Metryc?",description="Learn what Metryc does and why it’s different", value="what_is_metryc"),
            discord.SelectOption(
            label="What do the Discord roles mean?",
            description="A guide to some roles in the Metryc Discord",
            value="discord_roles",
            ),
            discord.SelectOption(label="Workout planning", value="workout_planning"),
            discord.SelectOption(label="Food logging", value="food_logging"),
            discord.SelectOption(label="Pricing & free trial", value="pricing"),
        ]
        super().__init__(
            placeholder="Select a topic to get quick answers",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        key = self.values[0]
        await interaction.followup.send(FAQ_ANSWERS[key], ephemeral=True)

class FAQView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FAQSelect())

FAQ_MESSAGE_ID_FILE = "/tmp/faq_message_id.txt"  

async def get_saved_message_id() -> int | None:
    try:
        with open(FAQ_MESSAGE_ID_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None

def save_message_id(msg_id: int) -> None:
    try:
        with open(FAQ_MESSAGE_ID_FILE, "w") as f:
            f.write(str(msg_id))
    except Exception:
        pass


@bot.event
async def on_ready():
    print(f"LOGGED IN AS: {bot.user} (id={bot.user.id})")

    channel = bot.get_channel(FAQ_CHANNEL_ID)
    if channel is None:
        print("Could not find FAQ channel. Check FAQ_CHANNEL_ID and bot permissions.")
        return

    # 1) Try to refresh the same message by ID (most reliable)
    msg_id = await get_saved_message_id()
    if msg_id:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(content=FAQ_CONTENT, view=FAQView())
            print("Refreshed FAQ message by saved ID.")
            return
        except Exception as e:
            print(f"Could not fetch/edit saved FAQ message (will recover): {e}")

    # 2) Recovery: find an existing bot FAQ message by content prefix
    existing = None
    try:
        async for msg in channel.history(limit=50):
            if msg.author == bot.user and (msg.content or "").startswith("**Metryc FAQ**"):
                existing = msg
                break
    except discord.Forbidden:
        print("Missing Read Message History permission in #faq.")
        return

    # 3) Edit if found, otherwise post once
    try:
        if existing:
            await existing.edit(content=FAQ_CONTENT, view=FAQView())
            save_message_id(existing.id)
            print("Refreshed existing FAQ message (found by content).")
        else:
            sent = await channel.send(FAQ_CONTENT, view=FAQView())
            save_message_id(sent.id)
            print("Posted FAQ message (new) and saved ID.")
    except discord.Forbidden:
        print("Missing Send Messages permission in #faq.")
    except Exception as e:
        print(f"Could not post/refresh FAQ: {e}")


@bot.event
async def on_message(message: discord.Message):
    # Keep #faq clean: delete anything users post there
    if message.channel.id == FAQ_CHANNEL_ID and message.author != bot.user:
        try:
            await message.delete()
        except discord.Forbidden:
            pass

    # Let other commands/events still work
    await bot.process_commands(message)
    




    

@bot.slash_command(description="Show the Metryc FAQ menu (ephemeral)")
async def faq(ctx: discord.ApplicationContext):
    await ctx.respond(FAQ_CONTENT, view=FAQView(), ephemeral=True)


if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception:
        print("BOT CRASHED WITH ERROR:")
        traceback.print_exc()
