import discord
from discord.ext import tasks, commands
import json
import os
import feedparser

ARTICLES_FILE = "articles.json"

def load_articles():
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_articles(articles):
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

def scrape_techcrunch_rss(max_articles=100):
    feed_url = "https://techcrunch.com/feed/"
    feed = feedparser.parse(feed_url)

    articles = load_articles()
    existing_links = {article["link"] for article in articles}

    new_articles = []
    count = 0

    for entry in feed.entries:
        if count >= max_articles:
            break
        link = entry.link
        title = entry.title

        if link not in existing_links:
            article = {'title': title, 'link': link}
            articles.append(article)
            new_articles.append(article)
        count += 1

    if new_articles:
        save_articles(articles)

    return new_articles

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@tasks.loop(minutes=1)
async def fetch_and_store_articles():
    print("جمع المقالات الجديدة...")
    new_articles = scrape_techcrunch_rss(100)
    if new_articles:
        print(f"تم إضافة {len(new_articles)} مقال جديد.")
    else:
        print("لا مقالات جديدة.")

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول كبوت: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"تم مزامنة أوامر السلاش: {len(synced)} أمر.")
    except Exception as e:
        print(f"خطأ أثناء مزامنة أوامر السلاش: {e}")
    fetch_and_store_articles.start()

@bot.tree.command(name="articles_count", description="يعرض عدد المقالات المخزنة")
async def articles_count(interaction: discord.Interaction):
    articles = load_articles()
    await interaction.response.send_message(f"عدد المقالات المخزنة: {len(articles)}")

@bot.tree.command(name="search_article", description="ابحث عن مقال بواسطة كلمة مفتاحية")
@discord.app_commands.describe(keyword="كلمة البحث")
async def search_article(interaction: discord.Interaction, keyword: str):
    articles = load_articles()
    keyword_lower = keyword.lower()

    matched = [a for a in articles if keyword_lower in a["title"].lower()]

    if not matched:
        await interaction.response.send_message("لم أجد أي مقال يحتوي على هذه الكلمة المفتاحية.", ephemeral=True)
        return

    options = []
    for i, article in enumerate(matched[:25]):
        options.append(discord.SelectOption(label=article["title"][:100], description=article["link"][:100], value=str(i)))

    select = discord.ui.Select(placeholder="اختر مقالاً من القائمة", options=options)

    async def select_callback(select_interaction: discord.Interaction):
        selected_index = int(select.values[0])
        chosen_article = matched[selected_index]
        await select_interaction.response.edit_message(content=f"**{chosen_article['title']}**\n{chosen_article['link']}", view=None)

    select.callback = select_callback

    view = discord.ui.View()
    view.add_item(select)

    await interaction.response.send_message("اختر مقال من القائمة:", view=view, ephemeral=True)


bot.run("Token-bot")