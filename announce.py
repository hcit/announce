# vim: sw=4 ts=4 noexpandtab
#
# For Python 2.6+
#
# Dependencies:
#  - scapy
#  - dateutil
#  - pygame

import sys
import string
import pprint
import json
import dateutil.parser
import pygame
from datetime import datetime
from scapy.all import *

class Announcer:
	""" Announces people as they request their first DHCP lease of the day """

	people = []
	mac = dict()
	name = dict()

	def __init__(self):
		self.load_people()

		print 'Loaded people:'
		pprint.pprint([p['name'] for p in self.people])

		self.setup_audio()

	def load_people(self):
		try:
			with open('people.json', 'r') as f:
				self.people = json.load(f)
		except:
			print 'Could not load people database.'
			pprint.pprint(sys.exc_info[1])

		for person in self.people:
			# Optional parameters
			if not 'seek' in person:
				person['seek'] = 0

			if not 'duration' in person:
				person['duration'] = 20

			if not 'fade' in person:
				person['fade'] = 10

			self.name[person['name']] = person
			for mac_address in person['mac_addresses']:
				self.mac[mac_address] = person


	def setup_audio(self):
		pygame.mixer.init(44100, -16, 2, 2048)
		pygame.mixer.music.set_volume(1.0)


	def detect(self):
		sniff(filter='arp or (udp and (port 67 or 68))', prn=self.check_packet, store=0)

	def check_packet(self, packet):
		if DHCP in packet:
			source = packet[Ether].src
			print 'Found DHCP request for MAC address: ', source

			if source in self.mac:
				person = self.mac[source]
				print 'And it is one we are interested in, belonging to: ',
				print person['name']

				if self.not_seen_today(person):
					print 'And they have not been seen today. Play the damn music!'
					self.announce(person)
				else:
					print 'But they have already been seen.'

				self.save_seen(person)


	def not_seen_today(self, person):
		not_seen_in = datetime.now() - dateutil.parser.parse(person['last_seen'])
		return not_seen_in.days > 0 or not_seen_in.seconds > (10 * 60 * 60)


	def save_seen(self, person):
		person['last_seen'] = datetime.now().isoformat(' ')

		try:
			with open('people.json', 'w') as f:
				f.write(json.dumps(self.people, sort_keys=True, indent=4))
		except:
			print 'Could not persist last seen datetime.'
			pprint.pprint(sys.exc_info[1])


	def announce(self, person):
		clock = pygame.time.Clock()

		try:
			pygame.mixer.music.load(person['audio'])
			print "Music file %s loaded!" % music_file
		except pygame.error:
			print "Could not open audio file (%s)" % (music_file, pygame.get_error())

		pygame.mixer.music.play()

		#sleep(person['duration'])

		while pygame.mixer.music.get_busy():
			# check if playback has finished
			clock.tick(1 / 10)

announcer = Announcer();
announcer.detect();
