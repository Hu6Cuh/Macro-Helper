import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable voice features to avoid audioop issues
try:
    discord.opus._load_default = lambda: None
except:
    pass

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix='!!', intents=intents, help_command=None)

# Configuration
MACRO_KEYWORDS = ['help', 'macro', 'issue', 'problem', 'bug', 'error']
VERIFY_ROLE_NAME = "Verified"  # Change this to your desired role name
VERIFY_EMOJI = "✅"

# Macro help response
MACRO_HELP_MESSAGE = """
**🔧 Macro Help & Troubleshooting**

**Common Macro Issues:**
• **Macro not running**: Check if macros are enabled in your application settings
• **Permission errors**: Run your application as administrator
• **Syntax errors**: Review your macro code for typos or missing brackets
• **Variable issues**: Ensure all variables are properly declared and initialized

**Quick Fixes:**
1. Restart your application
2. Clear macro cache/temp files
3. Check for conflicting macros
4. Verify file permissions

**Need more help?** Please share:
- What application you're using
- Error message (if any)  
- What you're trying to accomplish
- Steps you've already tried

*Our community is here to help! 💪*
"""

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} servers')

@bot.event
async def on_message(message):
    # Don't respond to bot messages
    if message.author.bot:
        return
    
    # Check for macro help keywords
    message_content = message.content.lower()
    if any(keyword in message_content for keyword in MACRO_KEYWORDS):
        # Don't trigger on commands
        if not message.content.startswith('!!'):
            embed = discord.Embed(
                title="🔧 Macro Help",
                description=MACRO_HELP_MESSAGE,
                color=0x00ff00
            )
            embed.set_footer(text="Need more specific help? Ask in detail!")
            await message.reply(embed=embed)
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='verify')
@commands.has_permissions(administrator=True)
async def verify_command(ctx):
    """Admin command to send verification message"""
    embed = discord.Embed(
        title="🔐 Server Verification",
        description=f"React with {VERIFY_EMOJI} to get verified and access all channels!",
        color=0x0099ff
    )
    embed.add_field(
        name="Why verify?",
        value="Verification helps keep our server secure and ensures you're a real person.",
        inline=False
    )
    embed.set_footer(text="Click the reaction below to verify!")
    
    message = await ctx.send(embed=embed)
    await message.add_reaction(VERIFY_EMOJI)
    
    # Delete the command message
    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

@bot.event
async def on_reaction_add(reaction, user):
    """Handle verification reactions"""
    # Don't process bot reactions
    if user.bot:
        return
    
    # Check if it's the verify emoji
    if str(reaction.emoji) == VERIFY_EMOJI:
        guild = reaction.message.guild
        
        # Check if message is a verification embed
        if (reaction.message.author == bot.user and 
            reaction.message.embeds and 
            "Server Verification" in reaction.message.embeds[0].title):
            
            # Find or create the verified role
            verified_role = discord.utils.get(guild.roles, name=VERIFY_ROLE_NAME)
            
            if not verified_role:
                try:
                    verified_role = await guild.create_role(
                        name=VERIFY_ROLE_NAME,
                        color=discord.Color.green(),
                        reason="Auto-created for verification system"
                    )
                    print(f"Created {VERIFY_ROLE_NAME} role in {guild.name}")
                except discord.Forbidden:
                    print(f"Unable to create role in {guild.name} - insufficient permissions")
                    return
            
            # Add role to user
            member = guild.get_member(user.id)
            if member and verified_role not in member.roles:
                try:
                    await member.add_roles(verified_role, reason="User verified via reaction")
                    
                    # Send confirmation DM
                    try:
                        await user.send(f"✅ You've been verified in **{guild.name}**! Welcome!")
                    except discord.Forbidden:
                        pass  # User has DMs disabled
                    
                    print(f"Verified user {user.name} in {guild.name}")
                except discord.Forbidden:
                    print(f"Unable to add role to {user.name} in {guild.name}")

@bot.event
async def on_reaction_remove(reaction, user):
    """Handle verification reaction removal"""
    # Don't process bot reactions
    if user.bot:
        return
    
    # Check if it's the verify emoji being removed
    if str(reaction.emoji) == VERIFY_EMOJI:
        guild = reaction.message.guild
        
        # Check if message is a verification embed
        if (reaction.message.author == bot.user and 
            reaction.message.embeds and 
            "Server Verification" in reaction.message.embeds[0].title):
            
            verified_role = discord.utils.get(guild.roles, name=VERIFY_ROLE_NAME)
            
            if verified_role:
                member = guild.get_member(user.id)
                if member and verified_role in member.roles:
                    try:
                        await member.remove_roles(verified_role, reason="User removed verification reaction")
                        print(f"Removed verification from {user.name} in {guild.name}")
                    except discord.Forbidden:
                        print(f"Unable to remove role from {user.name} in {guild.name}")

@verify_command.error
async def verify_error(ctx, error):
    """Handle verification command errors"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need administrator permissions to use this command!", delete_after=10)

# Additional utility commands
@bot.command(name='bothelp')
async def bot_help_command(ctx):
    """Show bot help"""
    embed = discord.Embed(
        title="🤖 Bot Commands",
        color=0x0099ff
    )
    embed.add_field(
        name="Bot Commands",
        value="`!!bothelp` - Show this help message\n`!!ping` - Check bot latency",
        inline=False
    )
    embed.add_field(
        name="Admin Commands",
        value="`!!verify` - Send verification message (Admin only)",
        inline=False
    )
    embed.add_field(
        name="Auto Features",
        value="• Responds to macro help keywords automatically\n• Gives roles when users react to verification messages",
        inline=False
    )
    embed.add_field(
        name="Macro Keywords",
        value=", ".join(MACRO_KEYWORDS),
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: {latency}ms")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!", delete_after=10)
    else:
        print(f"Error: {error}")

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Make sure to set your bot token in the environment variables")
    else:
        bot.run(TOKEN)
