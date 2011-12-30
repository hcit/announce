# vim: sw=4 ts=4 noexpandtab
# For Python 2.6 with scapy

import sys
import string
import pprint
import json
import dateutil.parser
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
		pprint.pprint(self.people)

	def load_people(self):
		try:
			with open('people.json', 'r') as f:
				self.people = json.load(f)
		except:
			print 'Could not load people database.'
			pprint.pprint(sys.exc_info[1])

		for person in self.people:
			self.name[person['name']] = person
			for mac_address in person['mac_addresses']:
				self.mac[mac_address] = person

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
		self.name[person['name']]['last_seen'] = datetime.now().isoformat(' ')

		try:
			with open('people.json', 'w') as f:
				f.write(json.dumps(self.people, sort_keys=True, indent=4))
		except:
			print 'Could not persist last seen datetime.'
			pprint.pprint(sys.exc_info[1])

	def announce(self, person):
		pass

announcer = Announcer();
announcer.detect();
