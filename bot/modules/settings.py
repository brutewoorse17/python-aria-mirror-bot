from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
import bot
from bot import application, LOGGER
from bot.helper.telegram_helper.filters import CustomFilters


def _settings_text() -> str:
	index_url = bot.INDEX_URL if bot.INDEX_URL else 'None'
	return (
		"<b>Bot Settings</b>\n\n"
		f"Team Drive: <code>{bot.IS_TEAM_DRIVE}</code>\n"
		f"Use Service Accounts: <code>{bot.USE_SERVICE_ACCOUNTS}</code>\n"
		f"Status Update Interval: <code>{bot.DOWNLOAD_STATUS_UPDATE_INTERVAL}s</code>\n"
		f"Auto Delete Duration: <code>{bot.AUTO_DELETE_MESSAGE_DURATION}</code> (−1 disables)\n"
		f"Index URL: <code>{index_url}</code>\n"
	)


def _settings_keyboard() -> InlineKeyboardMarkup:
	rows = [
		[
			InlineKeyboardButton(
				f"Team Drive: {'ON' if bot.IS_TEAM_DRIVE else 'OFF'}",
				callback_data="settings:toggle_teamdrive",
			),
			InlineKeyboardButton(
				f"SA: {'ON' if bot.USE_SERVICE_ACCOUNTS else 'OFF'}",
				callback_data="settings:toggle_sa",
			),
		],
		[
			InlineKeyboardButton("DS Update −", callback_data="settings:dsui_dec"),
			InlineKeyboardButton("DS Update +", callback_data="settings:dsui_inc"),
		],
		[
			InlineKeyboardButton("AutoDelete −", callback_data="settings:ad_dec"),
			InlineKeyboardButton("AutoDelete +", callback_data="settings:ad_inc"),
			InlineKeyboardButton(
				"Disable" if bot.AUTO_DELETE_MESSAGE_DURATION != -1 else "Enable",
				callback_data="settings:ad_toggle",
			),
		],
		[
			InlineKeyboardButton("Refresh", callback_data="settings:refresh"),
		]
	]
	return InlineKeyboardMarkup(rows)


async def show_settings(update, context):
	await context.bot.send_message(
		chat_id=update.effective_chat.id,
		reply_to_message_id=update.effective_message.message_id,
		text=_settings_text(),
		parse_mode='HTML',
		reply_markup=_settings_keyboard(),
	)


async def settings_callback(update, context):
	query = update.callback_query
	user_id = update.effective_user.id if update.effective_user else None
	if user_id != bot.OWNER_ID:
		await query.answer("Not authorized", show_alert=True)
		return
	await query.answer()
	data = query.data or ""
	try:
		if data == "settings:toggle_teamdrive":
			bot.IS_TEAM_DRIVE = not bot.IS_TEAM_DRIVE
		elif data == "settings:toggle_sa":
			bot.USE_SERVICE_ACCOUNTS = not bot.USE_SERVICE_ACCOUNTS
		elif data == "settings:dsui_inc":
			bot.DOWNLOAD_STATUS_UPDATE_INTERVAL = max(1, bot.DOWNLOAD_STATUS_UPDATE_INTERVAL + 1)
		elif data == "settings:dsui_dec":
			bot.DOWNLOAD_STATUS_UPDATE_INTERVAL = max(1, bot.DOWNLOAD_STATUS_UPDATE_INTERVAL - 1)
		elif data == "settings:ad_inc":
			if bot.AUTO_DELETE_MESSAGE_DURATION == -1:
				bot.AUTO_DELETE_MESSAGE_DURATION = 20
			else:
				bot.AUTO_DELETE_MESSAGE_DURATION = min(3600, bot.AUTO_DELETE_MESSAGE_DURATION + 5)
		elif data == "settings:ad_dec":
			if bot.AUTO_DELETE_MESSAGE_DURATION == -1:
				bot.AUTO_DELETE_MESSAGE_DURATION = 20
			else:
				bot.AUTO_DELETE_MESSAGE_DURATION = max(0, bot.AUTO_DELETE_MESSAGE_DURATION - 5)
		elif data == "settings:ad_toggle":
			bot.AUTO_DELETE_MESSAGE_DURATION = -1 if bot.AUTO_DELETE_MESSAGE_DURATION != -1 else 20
		# refresh or after any change
		await query.edit_message_text(
			text=_settings_text(), parse_mode='HTML', reply_markup=_settings_keyboard()
		)
	except Exception as e:
		LOGGER.error(str(e))
		await query.edit_message_text(
			text=_settings_text(), parse_mode='HTML', reply_markup=_settings_keyboard()
		)


settings_handler = CommandHandler('settings', show_settings, filters=CustomFilters.owner_filter)
settings_cb_handler = CallbackQueryHandler(settings_callback, pattern=r"^settings:")
application.add_handler(settings_handler)
application.add_handler(settings_cb_handler)