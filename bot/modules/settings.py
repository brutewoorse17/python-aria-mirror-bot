from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
import bot
from bot import application, LOGGER
from bot.helper.telegram_helper.filters import CustomFilters
import os
from telegram.error import BadRequest


def _settings_text() -> str:
	index_url = bot.INDEX_URL if bot.INDEX_URL else 'None'
	token_status = 'Present' if os.path.exists('token.pickle') else 'Missing'
	thumb = bot.VIDEO_THUMB_PATH if bot.VIDEO_THUMB_PATH else 'None'
	return (
		"<b>Bot Settings</b>\n\n"
		f"Team Drive: <code>{bot.IS_TEAM_DRIVE}</code>\n"
		f"Use Service Accounts: <code>{bot.USE_SERVICE_ACCOUNTS}</code>\n"
		f"Status Update Interval: <code>{bot.DOWNLOAD_STATUS_UPDATE_INTERVAL}s</code>\n"
		f"Auto Delete Duration: <code>{bot.AUTO_DELETE_MESSAGE_DURATION}</code> (−1 disables)\n"
		f"Index URL: <code>{index_url}</code>\n"
		f"Upload as Video: <code>{bot.UPLOAD_AS_VIDEO}</code>\n"
		f"Use Custom Thumb: <code>{bot.USE_CUSTOM_THUMB}</code>\n"
		f"Thumb Path: <code>{thumb}</code>\n"
		f"Drive token.pickle: <code>{token_status}</code>\n"
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
			InlineKeyboardButton(
				f"Upload as Video: {'ON' if bot.UPLOAD_AS_VIDEO else 'OFF'}",
				callback_data="settings:toggle_upload_video",
			)
		],
		[
			InlineKeyboardButton(
				f"Use Custom Thumb: {'ON' if bot.USE_CUSTOM_THUMB else 'OFF'}",
				callback_data="settings:toggle_thumb",
			)
		],
		[
			InlineKeyboardButton("Upload token.pickle", callback_data="settings:upload_token"),
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
		prev_text = query.message.text or ""
		prev_markup = query.message.reply_markup
		changed = False
		if data == "settings:toggle_teamdrive":
			bot.IS_TEAM_DRIVE = not bot.IS_TEAM_DRIVE
			changed = True
		elif data == "settings:toggle_sa":
			bot.USE_SERVICE_ACCOUNTS = not bot.USE_SERVICE_ACCOUNTS
			changed = True
		elif data == "settings:dsui_inc":
			bot.DOWNLOAD_STATUS_UPDATE_INTERVAL = max(1, bot.DOWNLOAD_STATUS_UPDATE_INTERVAL + 1)
			changed = True
		elif data == "settings:dsui_dec":
			bot.DOWNLOAD_STATUS_UPDATE_INTERVAL = max(1, bot.DOWNLOAD_STATUS_UPDATE_INTERVAL - 1)
			changed = True
		elif data == "settings:ad_inc":
			if bot.AUTO_DELETE_MESSAGE_DURATION == -1:
				bot.AUTO_DELETE_MESSAGE_DURATION = 20
			else:
				bot.AUTO_DELETE_MESSAGE_DURATION = min(3600, bot.AUTO_DELETE_MESSAGE_DURATION + 5)
			changed = True
		elif data == "settings:ad_dec":
			if bot.AUTO_DELETE_MESSAGE_DURATION == -1:
				bot.AUTO_DELETE_MESSAGE_DURATION = 20
			else:
				bot.AUTO_DELETE_MESSAGE_DURATION = max(0, bot.AUTO_DELETE_MESSAGE_DURATION - 5)
			changed = True
		elif data == "settings:ad_toggle":
			bot.AUTO_DELETE_MESSAGE_DURATION = -1 if bot.AUTO_DELETE_MESSAGE_DURATION != -1 else 20
			changed = True
		elif data == "settings:toggle_upload_video":
			bot.UPLOAD_AS_VIDEO = not bot.UPLOAD_AS_VIDEO
			changed = True
		elif data == "settings:toggle_thumb":
			bot.USE_CUSTOM_THUMB = not bot.USE_CUSTOM_THUMB
			changed = True
		elif data == "settings:upload_token":
			bot.WAITING_FOR_TOKEN_PICKLE = True
			new_text = "Please send token.pickle as a document in this chat (owner only)."
			try:
				if new_text != prev_text:
					await query.edit_message_text(text=new_text, parse_mode='HTML', reply_markup=_settings_keyboard())
			except BadRequest as br:
				LOGGER.error(str(br))
			return
		# refresh only if changed or explicit refresh
		if changed or data == "settings:refresh":
			new_text = _settings_text()
			try:
				if new_text != prev_text:
					await query.edit_message_text(text=new_text, parse_mode='HTML', reply_markup=_settings_keyboard())
			except BadRequest as br:
				LOGGER.error(str(br))
	except Exception as e:
		LOGGER.error(str(e))
		try:
			await query.edit_message_text(
				text=_settings_text(), parse_mode='HTML', reply_markup=_settings_keyboard()
			)
		except BadRequest as br:
			LOGGER.error(str(br))


async def _handle_token_upload(update, context):
	if update.effective_user.id != bot.OWNER_ID:
		return
	if not getattr(bot, 'WAITING_FOR_TOKEN_PICKLE', False):
		return
	doc = update.effective_message.document if update.effective_message else None
	if not doc:
		return
	file_name = doc.file_name or ''
	if not file_name.endswith('.pickle'):
		await context.bot.send_message(chat_id=update.effective_chat.id,
									  reply_to_message_id=update.effective_message.message_id,
									  text='Please upload a .pickle file named token.pickle', parse_mode='HTML')
		return
	# download file
	file = await context.bot.get_file(doc.file_id)
	await file.download_to_drive(custom_path='token.pickle')
	bot.WAITING_FOR_TOKEN_PICKLE = False
	await context.bot.send_message(chat_id=update.effective_chat.id,
								  reply_to_message_id=update.effective_message.message_id,
								  text='token.pickle saved. You can now use Google Drive without re-auth.', parse_mode='HTML')


settings_handler = CommandHandler('settings', show_settings, filters=CustomFilters.owner_filter)
settings_cb_handler = CallbackQueryHandler(settings_callback, pattern=r"^settings:")
settings_token_handler = MessageHandler(filters.Document.ALL & CustomFilters.owner_filter, _handle_token_upload)
application.add_handler(settings_handler)
application.add_handler(settings_cb_handler)
application.add_handler(settings_token_handler)