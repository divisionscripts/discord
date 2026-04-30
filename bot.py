import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import datetime
 
# ─────────────────────────────────────────────
#  CONFIGURATION  ← Edit these values
# ─────────────────────────────────────────────
 
BOT_TOKEN = "MTQ4ODMyNTYxMzYwMDM3ODkwMA.GApypM.Om7Yf0I2vZ8YEigq0EsvjKXgdVil0P4E3gi5A8"          # ← Paste your bot token here
 
OWNER_IDS = [123456789012345678]            # ← Your Discord user ID(s)
 
TICKET_CATEGORY_NAME = "🎫 Purchase Tickets"
TICKET_LOG_CHANNEL   = "ticket-logs"
ANNOUNCEMENTS_CHANNEL = "announcements"
 
# ─────────────────────────────────────────────
#  CLOTHING DATABASE  (persistent JSON file)
# ─────────────────────────────────────────────
 
DB_FILE = "th_customs_db.json"
 
DEFAULT_DB = {
    "clothing": {
        "MC": [
            {"name": "Iron Reaper Cut",        "creator": "Kezh",  "price": "$15",  "description": "Full MC cut with custom patches & back piece"},
            {"name": "Devil's Road Set",       "creator": "Fazh",  "price": "$20",  "description": "Leather jacket + jeans combo with MC branding"},
            {"name": "Outlaw Prospect Fit",    "creator": "Kezh",  "price": "$12",  "description": "Prospect vest with side patches"},
            {"name": "Chrome Kings Pack",      "creator": "Fazh",  "price": "$18",  "description": "Full chrome-themed MC outfit set"},
        ],
        "Street": [
            {"name": "Eastside Drip Pack",     "creator": "Kezh",  "price": "$10",  "description": "Hoodie, cargo pants & fresh kicks"},
            {"name": "Corner Boy Fit",         "creator": "Fazh",  "price": "$8",   "description": "Streetwear essentials – tee, joggers & cap"},
            {"name": "Hustle Season Set",      "creator": "Kezh",  "price": "$14",  "description": "Full drip street package with 3 outfit variants"},
            {"name": "Urban Legend Bundle",    "creator": "Fazh",  "price": "$16",  "description": "Premium streetwear with exclusive colourways"},
        ],
        "Formal": [
            {"name": "Midnight Suit",          "creator": "Fazh",  "price": "$18",  "description": "Sharp all-black formal suit with tie options"},
            {"name": "Classic Gentleman Pack", "creator": "Kezh",  "price": "$20",  "description": "Full formal set: suit, shirt, tie & shoes"},
            {"name": "Boardroom Bundle",       "creator": "Fazh",  "price": "$22",  "description": "Grey & navy suits with multiple shirt combos"},
        ],
        "Business": [
            {"name": "CEO Starter Pack",       "creator": "Kezh",  "price": "$16",  "description": "Smart-casual business look with blazer"},
            {"name": "Executive Suite Set",    "creator": "Fazh",  "price": "$24",  "description": "Premium business wardrobe – 4 full outfits"},
            {"name": "Casual Friday Pack",     "creator": "Kezh",  "price": "$12",  "description": "Smart-casual hybrid for relaxed business days"},
        ],
    },
    "stats": {
        "total_purchases": 0,
        "purchases_by_category": {"MC": 0, "Street": 0, "Formal": 0, "Business": 0}
    }
}
 
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump(DEFAULT_DB, f, indent=2)
    with open(DB_FILE, "r") as f:
        return json.load(f)
 
def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)
 
# ─────────────────────────────────────────────
#  COLOURS & EMOJIS
# ─────────────────────────────────────────────
 
BRAND_COLOR  = 0xFF6B00   # Orange — TH Customs brand
SUCCESS      = 0x2ECC71
ERROR        = 0xE74C3C
INFO         = 0x3498DB
 
CAT_EMOJI = {"MC": "🏍️", "Street": "🧢", "Formal": "👔", "Business": "💼"}
CAT_COLOR = {"MC": 0xC0392B, "Street": 0x8E44AD, "Formal": 0x2C3E50, "Business": 0x1A5276}
 
# ─────────────────────────────────────────────
#  BOT SETUP
# ─────────────────────────────────────────────
 
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
 
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
 
# ─────────────────────────────────────────────
#  VIEWS & UI COMPONENTS
# ─────────────────────────────────────────────
 
class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="MC Clothing",       value="MC",       emoji="🏍️", description="Motorcycle club cuts, leathers & patches"),
            discord.SelectOption(label="Street Clothing",   value="Street",   emoji="🧢", description="Drip fits, hoodies, streetwear & more"),
            discord.SelectOption(label="Formal Clothing",   value="Formal",   emoji="👔", description="Suits, dress shirts & smart attire"),
            discord.SelectOption(label="Business Clothing", value="Business", emoji="💼", description="Smart-casual & corporate bundles"),
        ]
        super().__init__(placeholder="🛍️  Choose a clothing category...", options=options, min_values=1, max_values=1)
 
    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        db  = load_db()
        items = db["clothing"].get(cat, [])
 
        embed = discord.Embed(
            title=f"{CAT_EMOJI[cat]}  {cat} Clothing — TH Customs",
            description=f"Select an item below to purchase.\n*All clothing is custom-made for FiveM.*",
            color=CAT_COLOR[cat],
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="TH Customs Shop", icon_url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty)
        embed.set_footer(text="TH Customs | Made by Kezh & Fazh | Co-Owner: Kozh")
 
        if not items:
            embed.description = "No items available in this category yet. Check back soon!"
        else:
            for i, item in enumerate(items, 1):
                embed.add_field(
                    name=f"**{item['name']}**  ·  {item['price']}",
                    value=f"🎨 Creator: **{item['creator']}**\n📦 {item['description']}",
                    inline=False
                )
 
        view = ItemPurchaseView(cat, items)
        await interaction.response.edit_message(embed=embed, view=view)
 
 
class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(CategorySelect())
 
    @discord.ui.button(label="Back to Categories", style=discord.ButtonStyle.secondary, emoji="⬅️", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = main_catalog_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=CategoryView())
 
 
class ItemSelect(discord.ui.Select):
    def __init__(self, category: str, items: list):
        self.category = category
        self.items_data = items
        options = [
            discord.SelectOption(
                label=item["name"][:100],
                value=str(i),
                description=f"{item['price']} · by {item['creator']}"[:100],
                emoji="🛒"
            )
            for i, item in enumerate(items)
        ]
        if not options:
            options = [discord.SelectOption(label="No items available", value="none")]
        super().__init__(placeholder="🛒  Pick an item to purchase...", options=options, disabled=not items)
 
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("No items available right now.", ephemeral=True)
            return
        idx  = int(self.values[0])
        item = self.items_data[idx]
        view = ConfirmPurchaseView(self.category, item)
        embed = discord.Embed(
            title="🛒  Confirm Your Purchase",
            description=f"You're about to purchase:\n\n**{item['name']}**",
            color=BRAND_COLOR
        )
        embed.add_field(name="Category",  value=self.category,        inline=True)
        embed.add_field(name="Price",     value=f"**{item['price']}**", inline=True)
        embed.add_field(name="Creator",   value=f"**{item['creator']}**", inline=True)
        embed.add_field(name="Details",   value=item["description"],   inline=False)
        embed.set_footer(text="Click Confirm Purchase to proceed or Cancel to go back.")
        await interaction.response.edit_message(embed=embed, view=view)
 
 
class ItemPurchaseView(discord.ui.View):
    def __init__(self, category: str, items: list):
        super().__init__(timeout=300)
        self.add_item(ItemSelect(category, items))
        self.category = category
 
    @discord.ui.button(label="Back to Categories", style=discord.ButtonStyle.secondary, emoji="⬅️", row=1)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = main_catalog_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=CategoryView())
 
 
class ConfirmPurchaseView(discord.ui.View):
    def __init__(self, category: str, item: dict):
        super().__init__(timeout=120)
        self.category = category
        self.item = item
 
    @discord.ui.button(label="✅  Confirm Purchase", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update stats
        db = load_db()
        db["stats"]["total_purchases"] += 1
        db["stats"]["purchases_by_category"][self.category] = \
            db["stats"]["purchases_by_category"].get(self.category, 0) + 1
        save_db(db)
 
        # DM the buyer
        dm_embed = discord.Embed(
            title="🧾  Purchase Confirmation — TH Customs",
            description=(
                "**Thank You For Purchasing with TH Customs!**\n\n"
                "Your clothing will be provided soon!\n"
                "Our team will reach out to deliver your package. "
                "If you have any questions feel free to open a support ticket in the server."
            ),
            color=SUCCESS,
            timestamp=datetime.utcnow()
        )
        dm_embed.add_field(name="Item",     value=f"**{self.item['name']}**",    inline=True)
        dm_embed.add_field(name="Category", value=self.category,                  inline=True)
        dm_embed.add_field(name="Price",    value=f"**{self.item['price']}**",    inline=True)
        dm_embed.add_field(name="Creator",  value=f"**{self.item['creator']}**",  inline=True)
        dm_embed.set_footer(text="TH Customs | Made by Kezh & Fazh | Co-Owner: Kozh")
 
        try:
            await interaction.user.send(embed=dm_embed)
            dm_status = "✅ A confirmation DM has been sent to you!"
        except discord.Forbidden:
            dm_status = "⚠️ Couldn't send you a DM — please open your DMs and try again."
 
        # Success embed in channel
        success_embed = discord.Embed(
            title="✅  Purchase Submitted!",
            description=(
                f"Thanks, **{interaction.user.display_name}**! "
                f"Your order for **{self.item['name']}** has been received.\n\n"
                f"{dm_status}\n\n"
                "Our team will deliver your clothing soon. 🎉"
            ),
            color=SUCCESS
        )
        success_embed.set_footer(text="TH Customs | Made by Kezh & Fazh | Co-Owner: Kozh")
 
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=success_embed, view=self)
 
        # Log to ticket-logs if channel exists
        log_ch = discord.utils.get(interaction.guild.text_channels, name=TICKET_LOG_CHANNEL)
        if log_ch:
            log_embed = discord.Embed(
                title="📋  New Purchase",
                color=INFO,
                timestamp=datetime.utcnow()
            )
            log_embed.add_field(name="Buyer",    value=f"{interaction.user.mention} (`{interaction.user}`)", inline=False)
            log_embed.add_field(name="Item",     value=self.item["name"],       inline=True)
            log_embed.add_field(name="Category", value=self.category,            inline=True)
            log_embed.add_field(name="Price",    value=self.item["price"],       inline=True)
            log_embed.add_field(name="Creator",  value=self.item["creator"],     inline=True)
            await log_ch.send(embed=log_embed)
 
    @discord.ui.button(label="❌  Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        db   = load_db()
        items = db["clothing"].get(self.category, [])
        embed = discord.Embed(
            title=f"{CAT_EMOJI[self.category]}  {self.category} Clothing — TH Customs",
            description="Purchase cancelled. Browse below:",
            color=CAT_COLOR[self.category]
        )
        for item in items:
            embed.add_field(
                name=f"**{item['name']}**  ·  {item['price']}",
                value=f"🎨 Creator: **{item['creator']}**\n📦 {item['description']}",
                inline=False
            )
        embed.set_footer(text="TH Customs | Made by Kezh & Fazh | Co-Owner: Kozh")
        await interaction.response.edit_message(embed=embed, view=ItemPurchaseView(self.category, items))
 
 
# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────
 
def main_catalog_embed(guild):
    db = load_db()
    total_items = sum(len(v) for v in db["clothing"].values())
    embed = discord.Embed(
        title="🛍️  TH Customs — Clothing Shop",
        description=(
            "Welcome to **TH Customs** — your #1 source for custom FiveM clothing!\n\n"
            "Browse our categories below and click to view items & purchase.\n"
            "All outfits are hand-crafted by our talented designers."
        ),
        color=BRAND_COLOR,
        timestamp=datetime.utcnow()
    )
    for cat, emoji in CAT_EMOJI.items():
        items = db["clothing"].get(cat, [])
        names = " · ".join(f"**{i['name']}**" for i in items) or "Coming soon..."
        embed.add_field(
            name=f"{emoji}  {cat}  ({len(items)} items)",
            value=names,
            inline=False
        )
    embed.add_field(name="\u200b", value=f"📦 **{total_items}** total items available", inline=False)
    embed.set_footer(text="TH Customs | Made by Kezh & Fazh | Co-Owner: Kozh")
    if guild and guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    return embed
 
 
def is_admin():
    async def predicate(interaction: discord.Interaction):
        return (
            interaction.user.guild_permissions.administrator
            or interaction.user.id in OWNER_IDS
        )
    return app_commands.check(predicate)
 
 
# ─────────────────────────────────────────────
#  SLASH COMMANDS
# ─────────────────────────────────────────────
 
@tree.command(name="about", description="Learn about TH Customs and our team")
async def about(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🧵  About TH Customs",
        description=(
            "**TH Customs** is a premium FiveM clothing studio specialising in "
            "hand-crafted, fully custom clothing packages.\n\n"
            "Whether you're rolling with an MC, repping your street set, suiting up "
            "for court, or dressing for the boardroom — we've got you covered.\n\n"
            "Every piece is uniquely designed to make your character stand out on the server."
        ),
        color=BRAND_COLOR,
        timestamp=datetime.utcnow()
    )
    embed.add_field(
        name="👨‍🎨  Our Designers",
        value=(
            "🎨 **Kezh** — Co-Founder & Lead Designer\n"
            "🎨 **Fazh** — Co-Founder & Lead Designer"
        ),
        inline=False
    )
    embed.add_field(
        name="👑  Management",
        value="🛡️ **Kozh** — Co-Owner",
        inline=False
    )
    embed.add_field(
        name="📦  What We Offer",
        value=(
            "🏍️ MC Cuts & Leather Sets\n"
            "🧢 Street & Drip Packages\n"
            "👔 Formal Suits & Attire\n"
            "💼 Business & Smart-Casual Looks"
        ),
        inline=True
    )
    embed.add_field(
        name="⚙️  Platform",
        value=(
            "🖥️ FiveM (GTA V)\n"
            "✅ All resources included\n"
            "🚀 Fast delivery"
        ),
        inline=True
    )
    embed.set_footer(text="TH Customs | Quality. Style. Reputation.")
    if interaction.guild and interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
    await interaction.response.send_message(embed=embed)
 
 
@tree.command(name="catalog", description="Browse and purchase TH Customs clothing")
async def catalog(interaction: discord.Interaction):
    embed = main_catalog_embed(interaction.guild)
    await interaction.response.send_message(embed=embed, view=CategoryView(), ephemeral=False)
 
 
@tree.command(name="stats", description="View TH Customs shop statistics")
async def stats(interaction: discord.Interaction):
    db = load_db()
    s  = db["stats"]
    embed = discord.Embed(title="📊  TH Customs — Shop Stats", color=BRAND_COLOR, timestamp=datetime.utcnow())
    embed.add_field(name="Total Purchases", value=f"**{s['total_purchases']}**", inline=True)
    total_items = sum(len(v) for v in db["clothing"].values())
    embed.add_field(name="Total Items",     value=f"**{total_items}**",           inline=True)
    embed.add_field(name="\u200b",          value="\u200b",                        inline=True)
    for cat, emoji in CAT_EMOJI.items():
        count = s["purchases_by_category"].get(cat, 0)
        items = len(db["clothing"].get(cat, []))
        embed.add_field(name=f"{emoji} {cat}", value=f"**{count}** purchases · **{items}** items", inline=True)
    embed.set_footer(text="TH Customs | Made by Kezh & Fazh | Co-Owner: Kozh")
    await interaction.response.send_message(embed=embed)
 
 
@tree.command(name="help", description="View all TH Customs bot commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖  TH Customs — Command List",
        description="Here's everything this bot can do:",
        color=BRAND_COLOR
    )
    embed.add_field(
        name="🛍️  Shopping",
        value=(
            "`/catalog` — Browse & purchase clothing\n"
            "`/about` — Info about TH Customs & team\n"
            "`/stats` — View shop statistics"
        ),
        inline=False
    )
    embed.add_field(
        name="⚙️  Admin Commands",
        value=(
            "`/setup` — First-time server setup (creates channels/roles)\n"
            "`/addclothing` — Add a new clothing item to a category\n"
            "`/removeclothing` — Remove a clothing item by name\n"
            "`/listclothing` — List all clothing in all categories\n"
            "`/announce` — Send an announcement to the announcements channel"
        ),
        inline=False
    )
    embed.add_field(
        name="ℹ️  Info",
        value="`/help` — This command",
        inline=False
    )
    embed.set_footer(text="TH Customs | Admin commands require Administrator permission.")
    await interaction.response.send_message(embed=embed, ephemeral=True)
 
 
# ── ADMIN: Setup ──────────────────────────────
 
@tree.command(name="setup", description="[Admin] Run first-time server setup for TH Customs")
@is_admin()
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    created = []
 
    # Channels to create if they don't exist
    channel_configs = [
        ("🏠│welcome",       "Welcome to TH Customs!", None),
        ("📢│announcements", "TH Customs announcements", None),
        ("🛍️│shop",          "Browse and purchase clothing here", None),
        ("🎫│open-ticket",   "Open a purchase ticket here", None),
        (TICKET_LOG_CHANNEL, "Purchase logs", None),
        ("💬│general",       "General chat", None),
        ("❓│support",        "Get support here", None),
    ]
 
    # Create ticket category
    ticket_cat = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
    if not ticket_cat:
        ticket_cat = await guild.create_category(TICKET_CATEGORY_NAME)
        created.append(f"📁 Category: **{TICKET_CATEGORY_NAME}**")
 
    for name, topic, _ in channel_configs:
        clean = name.split("│")[-1] if "│" in name else name
        existing = discord.utils.get(guild.text_channels, name=clean)
        if not existing:
            await guild.create_text_channel(name, topic=topic)
            created.append(f"💬 Channel: **{name}**")
 
    # Send catalog to shop channel
    shop_ch = discord.utils.get(guild.text_channels, name="shop")
    if shop_ch:
        shop_embed = main_catalog_embed(guild)
        shop_embed.description = (
            "**Welcome to the TH Customs Shop!**\n\n"
            "Use the dropdown below to browse categories and purchase clothing.\n"
            "All outfits are custom-made for FiveM by our designers."
        )
        await shop_ch.send(embed=shop_embed, view=CategoryView())
        created.append("🛍️ Posted catalog to **#shop**")
 
    # Welcome message
    welcome_ch = discord.utils.get(guild.text_channels, name="welcome")
    if welcome_ch:
        w_embed = discord.Embed(
            title="👋  Welcome to TH Customs!",
            description=(
                "We're a custom FiveM clothing studio bringing you the freshest fits.\n\n"
                "• Browse our shop with `/catalog`\n"
                "• Learn about us with `/about`\n"
                "• Open a ticket to purchase or get support"
            ),
            color=BRAND_COLOR
        )
        w_embed.set_footer(text="TH Customs | Made by Kezh & Fazh | Co-Owner: Kozh")
        await welcome_ch.send(embed=w_embed)
 
    summary = "\n".join(created) if created else "Everything was already set up! ✅"
    result_embed = discord.Embed(
        title="✅  Setup Complete",
        description=f"TH Customs server setup finished!\n\n**Created:**\n{summary}",
        color=SUCCESS
    )
    await interaction.followup.send(embed=result_embed, ephemeral=True)
 
 
# ── ADMIN: Add Clothing ───────────────────────
 
@tree.command(name="addclothing", description="[Admin] Add a new clothing item to the shop")
@app_commands.describe(
    category="Category to add to",
    name="Name of the clothing item",
    creator="Who made it (e.g. Kezh or Fazh)",
    price="Price (e.g. $15)",
    description="Short description of the item"
)
@app_commands.choices(category=[
    app_commands.Choice(name="MC",       value="MC"),
    app_commands.Choice(name="Street",   value="Street"),
    app_commands.Choice(name="Formal",   value="Formal"),
    app_commands.Choice(name="Business", value="Business"),
])
@is_admin()
async def add_clothing(
    interaction: discord.Interaction,
    category: str,
    name: str,
    creator: str,
    price: str,
    description: str
):
    db = load_db()
    if category not in db["clothing"]:
        db["clothing"][category] = []
    # Check duplicate
    existing_names = [i["name"].lower() for i in db["clothing"][category]]
    if name.lower() in existing_names:
        await interaction.response.send_message(
            f"❌ An item named **{name}** already exists in **{category}**.", ephemeral=True)
        return
    db["clothing"][category].append({
        "name": name, "creator": creator, "price": price, "description": description
    })
    save_db(db)
    embed = discord.Embed(
        title="✅  Clothing Added",
        color=SUCCESS
    )
    embed.add_field(name="Name",        value=f"**{name}**",   inline=True)
    embed.add_field(name="Category",    value=category,         inline=True)
    embed.add_field(name="Creator",     value=f"**{creator}**", inline=True)
    embed.add_field(name="Price",       value=price,            inline=True)
    embed.add_field(name="Description", value=description,      inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)
 
 
# ── ADMIN: Remove Clothing ────────────────────
 
@tree.command(name="removeclothing", description="[Admin] Remove a clothing item from the shop")
@app_commands.describe(
    category="Category to remove from",
    name="Exact name of the item to remove"
)
@app_commands.choices(category=[
    app_commands.Choice(name="MC",       value="MC"),
    app_commands.Choice(name="Street",   value="Street"),
    app_commands.Choice(name="Formal",   value="Formal"),
    app_commands.Choice(name="Business", value="Business"),
])
@is_admin()
async def remove_clothing(interaction: discord.Interaction, category: str, name: str):
    db = load_db()
    items = db["clothing"].get(category, [])
    match = next((i for i in items if i["name"].lower() == name.lower()), None)
    if not match:
        await interaction.response.send_message(
            f"❌ No item named **{name}** found in **{category}**.", ephemeral=True)
        return
    db["clothing"][category].remove(match)
    save_db(db)
    await interaction.response.send_message(
        f"✅ Removed **{match['name']}** from **{category}**.", ephemeral=True)
 
 
# ── ADMIN: List Clothing ──────────────────────
 
@tree.command(name="listclothing", description="[Admin] List all clothing items in the shop")
@is_admin()
async def list_clothing(interaction: discord.Interaction):
    db = load_db()
    embed = discord.Embed(title="📋  TH Customs — Full Clothing List", color=BRAND_COLOR)
    for cat, emoji in CAT_EMOJI.items():
        items = db["clothing"].get(cat, [])
        if items:
            val = "\n".join(
                f"• **{i['name']}** · {i['price']} · by {i['creator']}" for i in items
            )
        else:
            val = "*No items*"
        embed.add_field(name=f"{emoji}  {cat}", value=val, inline=False)
    embed.set_footer(text=f"Total: {sum(len(v) for v in db['clothing'].values())} items")
    await interaction.response.send_message(embed=embed, ephemeral=True)
 
 
# ── ADMIN: Announce ───────────────────────────
 
@tree.command(name="announce", description="[Admin] Send an announcement to the announcements channel")
@app_commands.describe(
    title="Announcement title",
    message="The announcement message",
    ping="Ping @everyone? (yes/no)"
)
@is_admin()
async def announce(interaction: discord.Interaction, title: str, message: str, ping: str = "no"):
    ch = discord.utils.get(interaction.guild.text_channels, name=ANNOUNCEMENTS_CHANNEL)
    if not ch:
        await interaction.response.send_message(
            f"❌ No channel named `{ANNOUNCEMENTS_CHANNEL}` found. Run `/setup` first.", ephemeral=True)
        return
    embed = discord.Embed(
        title=f"📢  {title}",
        description=message,
        color=BRAND_COLOR,
        timestamp=datetime.utcnow()
    )
    embed.set_author(name="TH Customs Announcement")
    embed.set_footer(text=f"Posted by {interaction.user.display_name} | TH Customs")
    content = "@everyone" if ping.lower() == "yes" else None
    await ch.send(content=content, embed=embed)
    await interaction.response.send_message(f"✅ Announcement sent to {ch.mention}!", ephemeral=True)
 
 
# ─────────────────────────────────────────────
#  ERROR HANDLING
# ─────────────────────────────────────────────
 
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        embed = discord.Embed(
            title="❌  Access Denied",
            description="You need **Administrator** permission to use this command.",
            color=ERROR
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="⚠️  Error",
            description=f"Something went wrong: `{error}`",
            color=ERROR
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(embed=embed, ephemeral=True)
        raise error
 
 
# ─────────────────────────────────────────────
#  BOT EVENTS
# ─────────────────────────────────────────────
 
@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="TH Customs 🧵 | /catalog"
        )
    )
    print("=" * 50)
    print(f"  TH Customs Bot — Online!")
    print(f"  Logged in as: {bot.user} (ID: {bot.user.id})")
    print(f"  Serving {len(bot.guilds)} server(s)")
    print(f"  Slash commands synced ✅")
    print("=" * 50)
 
 
@bot.event
async def on_guild_join(guild: discord.Guild):
    # Try to find a general or system channel to send welcome
    ch = guild.system_channel or discord.utils.get(guild.text_channels, name="general")
    if ch:
        embed = discord.Embed(
            title="👋  TH Customs Bot is here!",
            description=(
                "Thanks for adding **TH Customs** to your server!\n\n"
                "**Get started:**\n"
                "• Run `/setup` (Admin) to create channels and post the shop\n"
                "• Use `/catalog` to browse clothing\n"
                "• Use `/about` to learn about the team\n"
                "• Use `/help` for all commands"
            ),
            color=BRAND_COLOR
        )
        embed.set_footer(text="TH Customs | Made by Kezh & Fazh | Co-Owner: Kozh")
        await ch.send(embed=embed)
 
 
# ─────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────
 
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Please set your BOT_TOKEN at the top of this file before running!")
        print("   Get your token at: https://discord.com/developers/applications")
    else:
        bot.run(BOT_TOKEN)
