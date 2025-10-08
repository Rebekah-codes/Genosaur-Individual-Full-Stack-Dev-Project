
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Egg, Trait, Dinosaur

class EggModelTest(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(username='tester', password='pass')
		self.egg = Egg.objects.create(
			name='Test Egg',
			species_name='Green Rex',
			element_type='Earth',
			rarity='Common',
			owner=self.user,
			twigs=3,
			leaves=2
		)

	def test_egg_str(self):
		self.assertIn('Green Rex', str(self.egg))
		self.assertIn('Common', str(self.egg))

	def test_egg_owner(self):
		self.assertEqual(self.egg.owner.username, 'tester')

class TraitModelTest(TestCase):
	def setUp(self):
		self.trait = Trait.objects.create(
			name='Strong Bite',
			description='Can bite through stone',
			mood_impact='+Playful'
		)

	def test_trait_str(self):
		self.assertIn('Strong Bite', str(self.trait))
		self.assertIn('+Playful', str(self.trait))

class DinosaurModelTest(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(username='dino_user', password='pass')
		self.trait = Trait.objects.create(name='Fast Runner', description='Runs quickly')
		self.egg = Egg.objects.create(
			name='Eggy',
			species_name='Blue Spino',
			element_type='Water',
			rarity='Rare',
			owner=self.user
		)
		self.dino = Dinosaur.objects.create(
			name='Spino',
			species_name='Blue Spino',
			stage='juvenile',
			mood='happy',
			egg=self.egg,
			owner=self.user,
			level=1
		)
		self.dino.traits.add(self.trait)

	def test_dinosaur_str(self):
		self.assertIn('Spino', str(self.dino))
		self.assertIn('juvenile', str(self.dino))

	def test_dinosaur_traits(self):
		self.assertEqual(self.dino.traits.count(), 1)
		self.assertEqual(self.dino.traits.first().name, 'Fast Runner')
