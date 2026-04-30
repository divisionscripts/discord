from flask import Flask, request, redirect, jsonify
import requests
from flask_cors import CORS
import discord
from discord.ext import commands

app = Flask(__name__)
CORS(app)

# CONFIG
CLIENT_ID = "1488325613600378900"
CLIENT_SECRET = "sGnfa2gdz5MmqvG39glQ6f5bJ11M-uqJ"
REDIRECT_URI = "https://divisioncustoms.kesug.com"
BOT_TOKEN = "MTQ4ODMyNTYxMzYwMDM3ODkwMA.GApypM.Om7Yf0I2vZ8YEigq0EsvjKXgdVil0P4E3gi5A8"
GUILD_ID = 1093698141095723061

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# STORE LOGGED IN USERS (basic)
users = {}

# 🔐 DISCORD LOGIN
@app.route("/login")
def login():
    return redirect(
        f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=identify%20guilds"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers).json()

    user = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {token['access_token']}"}
    ).json()

    users[user["id"]] = user
    return jsonify(user)

# 👤 PROFILE
@app.route("/user/<user_id>")
def get_user(user_id):
    return jsonify(users.get(user_id, {}))

# 🎭 ROLE CHECK
@app.route("/roles/<user_id>")
async def get_roles(user_id):
    guild = bot.get_guild(GUILD_ID)
    member = await guild.fetch_member(int(user_id))
    roles = [role.name for role in member.roles]
    return jsonify({"roles": roles})

# 🎫 CREATE TICKET
@app.route("/ticket/<user_id>")
async def create_ticket(user_id):
    guild = bot.get_guild(GUILD_ID)

    category = discord.utils.get(guild.categories, name="Tickets")

    channel = await guild.create_text_channel(
        name=f"ticket-{user_id}",
        category=category
    )

    await channel.send(f"<@{user_id}> support will be with you shortly.")

    return jsonify({"status": "created"})

# RUN BOT + API
import threading

def run_bot():
    bot.run(BOT_TOKEN)

threading.Thread(target=run_bot).start()

app.run(host="0.0.0.0", port=3000)
```
