import logging
from config import Config
from pyrogram import Client, filters
from pyrogram.types import Message
from bot.helpers.translations import lang
from bot.helpers.utils.auth_check import check_id
from bot.helpers.utils.check_link import check_link
from bot.helpers.tidal_func.events import checkLogin, start

# Logger Configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("charset_normalizer").setLevel(logging.WARNING)

# Bot Commands Class
bot = Config.BOT_USERNAME

class CMD(object):
    START = ["start", f"start@{bot}"]
    HELP = ["help", f"help@{bot}"]
    SETTINGS = ["settings", f"settings@{bot}"]
    DOWNLOAD = ["download", f"download@{bot}"]
    AUTH = ["auth", f"auth@{bot}"]
    ADD_ADMIN = ["add_sudo", f"add_sudo@{bot}"]
    SHELL = ["shell", f"shell@{bot}"]
    INDEX = ["index", f"index@{bot}"]

# Pyrogram Client Initialization
USER = Client(
    name="TidalDlUser",
    session_string=Config.USER_SESSION,
    api_id=Config.APP_ID,
    api_hash=Config.API_HASH
)

# Link Handling Function
@Client.on_message(filters.text & ~filters.command)  # Match text messages but exclude commands
async def handle_links(bot, update: Message):
    if check_id(message=update):  # Check if the user is authorized
        try:
            link = None
            reply_to_id = None

            # Extract link from message or reply
            if update.reply_to_message and update.reply_to_message.text:
                link = update.reply_to_message.text
                reply_to_id = update.reply_to_message.id
            elif update.text:
                link = update.text
                reply_to_id = update.id

            # Validate the link if ALLOW_OTHER_LINKS is enabled
            if Config.ALLOW_OTHER_LINKS == "True":
                link = await check_link(link)

            if link:
                LOGGER.info(f"Download Initiated By - {update.from_user.first_name}")
                msg = await bot.send_message(
                    chat_id=update.chat.id,
                    text=lang.select.INIT_DOWNLOAD,
                    reply_to_message_id=update.id
                )
                botmsg_id = msg.id

                # Check authentication with Tidal
                auth, err = await checkLogin()
                if auth:
                    await start(link, bot, update, update.chat.id, reply_to_id, update.from_user.id)
                else:
                    await bot.edit_message_text(
                        chat_id=update.chat.id,
                        message_id=botmsg_id,
                        text=lang.select.ERR_AUTH_CHECK.format(err),
                    )
                    return

                # Cleanup initial message
                await bot.delete_messages(
                    chat_id=update.chat.id,
                    message_ids=msg.id
                )
            else:
                await bot.send_message(
                    chat_id=update.chat.id,
                    text=lang.select.ERR_NO_LINK,
                    reply_to_message_id=update.id
                )
        except Exception as e:
            LOGGER.error(f"Error handling link: {e}")
            await bot.send_message(
                chat_id=update.chat.id,
                text=lang.select.ERR_UNKNOWN_ERROR,
                reply_to_message_id=update.id
            )

# Start the bot if running as a script
if __name__ == "__main__":
    USER.run()
