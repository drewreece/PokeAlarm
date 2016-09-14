#Setup Logging
import logging
log = logging.getLogger(__name__)

#Python modules

#Local modules
from ..alarm import Alarm
from ..utils import *
from telegram_stickers import stickerlist

#External modules
import telepot
 
class Telegram_Alarm(Alarm):
 	
	_defaults = {
		'pokemon':{
			#'chat_id': If no default, required
			'title': "A wild <pkmn> has appeared!",
			'body': "<gmaps> \n Available until <24h_time> (<time_left>).",
			'location': "True",
			'sticker_id':'none' #<<- seems wrong!
		},
		'pokestop':{
			#'chat_id': If no default, required
			'title':"Someone has placed a lure on a Pokestop!",
			'body': "<gmaps> \n Lure will expire at <24h_time> (<time_left>).",
			'location': "True",
			'sticker_id':'BQADBAADFwADjGt_DaQ-N7VAroZ7Ag'
		},
		'gym':{
			#'chat_id': If no default, required
			'title':"A Team <old_team> gym has fallen!",
			'body': "<gmaps> \n It is now controlled by <new_team>.",
			'location': "True",
			'sticker_id':'BQADBAADEwADjGt_DcvoR3XehWjEAg'
		}
	}
	
	#Gather settings and create alarm
	def __init__(self, settings):
		#Service Info
		self.bot_token = settings['bot_token']
		self.chat_id = settings.get('chat_id')
		self.startup_message = settings.get('startup_message', "True")
		
		#Set Alerts
		self.pokemon = self.set_alert(settings.get('pokemon', {}), self._defaults['pokemon'])
		self.pokestop = self.set_alert(settings.get('pokestop', {}), self._defaults['pokestop'])
		self.gym = self.set_alert(settings.get('gym', {}), self._defaults['gym'])
		
		self.stickers = parse_boolean(settings.get('send_stickers', 'True'))

		#Connect and send startup message
 		self.connect()
		if parse_boolean(self.startup_message):
			self.client.sendMessage(self.pokemon['chat_id'], 'PokeAlarm activated! We will alert this chat about pokemon.')
		log.info("Telegram Alarm intialized.")

	#(Re)establishes Telegram connection
	def connect(self):
		self.client = telepot.Bot(self.bot_token) 
		
	#Set the appropriate settings for each alert
	def set_alert(self, settings, default):
		alert = {}
		alert['chat_id'] = settings.get('chat_id', self.chat_id)
		
		alert['title'] = settings.get('title', default['title'])
		alert['body'] = settings.get('body', default['body'])
		alert['location'] = parse_boolean(settings.get('location', default['location']))
		alert['sticker_id'] = settings.get('send_stickers', default['sticker_id'])
		return alert
 		
	#Send Alert to Telegram
 	def send_alert(self, alert, info):
		if self.stickers:
			#Use id for pokemon sticker
			if info['id'] in stickerlist:
				stickerargs = {
					'chat_id': alert['chat_id'],
					'sticker': stickerlist[info['id']],
					'disable_notification': 'True'
				}
			#Using hardcoded file_id in _defaults for stops & gyms
			else:
				stickerargs = {
					'chat_id': alert['chat_id'],
					'sticker': alert['sticker_id'],
					'disable_notification': 'True'
				}
			try_sending(log, self.connect, 'Telegram', self.client.sendSticker, stickerargs)

		args = {
			'chat_id': alert['chat_id'],
			'text': '<b>' + replace(alert['title'], info) + '</b> \n' + replace(alert['body'], info),
			'parse_mode': 'HTML',
			'disable_web_page_preview': 'False',
		}
		try_sending(log, self.connect, "Telegram", self.client.sendMessage, args)
		
		if alert['location']:
			locargs = { 
				'chat_id': alert['chat_id'],
				'latitude': info['lat'],
				'longitude':  info['lng'],
				'disable_notification': 'True'
			}
			try_sending(log, self.connect, "Telegram (Loc)", self.client.sendLocation, locargs)

	#Trigger an alert based on Pokemon info
	def pokemon_alert(self, pokemon_info):
		self.send_alert(self.pokemon, pokemon_info)
		
	#Trigger an alert based on Pokestop info
	def pokestop_alert(self, pokestop_info):
		self.send_alert(self.pokestop, pokestop_info)
		
	#Trigger an alert based on Pokestop info
	def gym_alert(self, gym_info):
		self.send_alert(self.gym, gym_info)
