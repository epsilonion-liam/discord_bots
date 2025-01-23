import logging
from nextcord.ext import commands
from nextcord import Guild
import aiohttp
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levellevel)s - %(message)s')
logger = logging.getLogger(__name__)

DISCORD_API_BASE_URL = "https://discord.com/api/v10"
SKU_ID = "############"  # Your specific SKU ID

class SubscriptionManager(commands.Cog):
    def __init__(self, bot: commands.Bot, db_pool, bot_token, application_id):
        self.bot = bot
        self.db_pool = db_pool
        self.bot_token = bot_token
        self.application_id = application_id

        if not self.bot_token:
            raise ValueError("No BOT_TOKEN found in environment variables")
        if not self.application_id:
            raise ValueError("No APPLICATION_ID found in environment variables")

        # Mask the bot token for logging
        masked_bot_token = self.bot_token[:4] + '...' + self.bot_token[-4:]
        logger.debug(f"Bot Token: {masked_bot_token}")
        logger.debug(f"Application ID: {self.application_id}")

    async def create_test_entitlement(self, owner_id: str, owner_type: int) -> dict:
        """Create a test entitlement to a given SKU for a guild or user."""
        url = f"{DISCORD_API_BASE_URL}/applications/{self.application_id}/entitlements"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        data = {
            "sku_id": SKU_ID,
            "owner_id": owner_id,
            "owner_type": owner_type
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                logger.debug(f"Request URL: {url}")
                logger.debug(f"Request Headers: {headers}")
                logger.debug(f"Request Data: {data}")
                logger.debug(f"Response Status: {response.status}")
                logger.debug(f"Response Text: {await response.text()}")
                if response.status == 200 or response.status == 201:
                    result = await response.json()
                    logger.debug(f"Response JSON: {result}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create test entitlement: {error_text}")
                    raise Exception(f"Failed to create test entitlement: {error_text}")

    async def delete_test_entitlement(self, entitlement_id: str) -> None:
        """Delete a currently-active test entitlement."""
        url = f"{DISCORD_API_BASE_URL}/applications/{self.application_id}/entitlements/{entitlement_id}"
        headers = {"Authorization": f"Bot {self.bot_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                logger.debug(f"Request URL: {url}")
                logger.debug(f"Request Headers: {headers}")
                logger.debug(f"Response Status: {response.status}")
                logger.debug(f"Response Text: {await response.text()}")
                if response.status == 204:
                    logger.debug(f"Test entitlement deleted successfully.")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to delete test entitlement: {error_text}")
                    raise Exception(f"Failed to delete test entitlement: {error_text}")

    @commands.command(name="add_test_entitlement")
    @commands.has_permissions(administrator=True)
    async def add_test_entitlement(self, ctx: commands.Context, guild: Optional[Guild] = None) -> None:
        """Add a test entitlement to the guild."""
        guild = guild or ctx.guild
        try:
            entitlement = await self.create_test_entitlement(str(guild.id), 1)
            await ctx.send(f"Test entitlement created for {guild.name}: {entitlement}")
            logger.info(f"Created test entitlement for {guild.name}: {entitlement}")
        except Exception as e:
            logger.error(f"Failed to create test entitlement: {e}")
            await ctx.send(f"Failed to create test entitlement for {guild.name}")

    @commands.command(name="remove_test_entitlement")
    @commands.has_permissions(administrator=True)
    async def remove_test_entitlement(self, ctx: commands.Context, entitlement_id: str, guild: Optional[Guild] = None) -> None:
        """Remove a test entitlement from the guild."""
        guild = guild or ctx.guild
        try:
            await self.delete_test_entitlement(entitlement_id)
            await ctx.send(f"Test entitlement removed for {guild.name}.")
            logger.info(f"Removed test entitlement for {guild.name}.")
        except Exception as e:
            logger.error(f"Failed to remove test entitlement: {e}")
            await ctx.send(f"Failed to remove test entitlement for {guild.name}.")

# Setup function to load the cog
def setup(bot: commands.Bot, bot_token, application_id):
    bot.add_cog(SubscriptionManager(bot, bot.db_pool, bot_token, application_id))
