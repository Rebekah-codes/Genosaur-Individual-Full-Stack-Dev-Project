from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Egg(models.Model):
    name = models.CharField(max_length=100, blank=True)
    species_name = models.CharField(max_length=100)
    element_type = models.CharField(max_length=50)   # e.g. Fire, Water, Earth
    rarity = models.CharField(max_length=50)         # e.g. Common, Rare, Legendary
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='eggs'
    )
    is_hatched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Nest materials for hatching
    twigs = models.PositiveIntegerField(default=0)
    leaves = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"🥚 {self.species_name} Egg ({self.rarity})"


class Trait(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    mood_impact = models.CharField(
        max_length=50,
        blank=True,
        help_text="How this trait influences mood (e.g. +Playful, -Calm)"
    )

    def __str__(self):
        return f"{self.name} ({self.mood_impact})" if self.mood_impact else self.name


class Dinosaur(models.Model):
    STAGE_CHOICES = [
        ('juvenile', 'Juvenile'),
        ('adult', 'Adult'),
    ]

    MOOD_CHOICES = [
        ('happy', 'Happy'),
        ('hungry', 'Hungry'),
        ('playful', 'Playful'),
        ('tired', 'Tired'),
    ]

    name = models.CharField(max_length=100)
    species_name = models.CharField(max_length=100)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='juvenile')
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='happy')
    traits = models.ManyToManyField(Trait, blank=True, related_name='dinosaurs')
    egg = models.OneToOneField(
        Egg,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dinosaur'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dinosaurs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    level = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"🦕 {self.name} ({self.stage}, {self.mood})"

    def get_sprite(self):
        """Return the relative static path for the dino's current stage sprite."""
        color = self.species_name.split()[0].lower()
        if self.stage == "juvenile":
            image_map = {
                'green': 'green_rex_juvie.png',
                'blue': 'blue_spino_juvie.png',
                'orange': 'orange_trike_juvie.png',
            }
            return f"images/juvenile dinos/{image_map.get(color, 'green_rex_juvie.png')}"
        elif self.stage == "adult":
            image_map = {
                'green': 'green_rex_adult.png',
                'blue': 'blue_spino_adult.png',
                'orange': 'orange_trike_adult.png',
            }
            return f"images/adult dinos/{image_map.get(color, 'green_rex_adult.png')}"
        else:
            return "images/juvenile dinos/green_rex_juvie.png"

    def level_up(self, amount=1):
        """Increase level but cap at 100."""
        self.level = min(self.level + amount, 100)
        self.save()


class RaiseAction(models.Model):
    ACTION_CHOICES = [
        ('feed', 'Feed'),
        ('play', 'Play'),
        ('train', 'Train'),
    ]

    dinosaur = models.ForeignKey(Dinosaur, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    outcome = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} → {self.dinosaur.name}"


class Trade(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_trades'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_trades'
    )
    sender_egg = models.ForeignKey(Egg, null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_trades')
    sender_dinosaur = models.ForeignKey(Dinosaur, null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_dino_trades')
    receiver_egg = models.ForeignKey(Egg, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_trades')
    receiver_dinosaur = models.ForeignKey(Dinosaur, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_dino_trades')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Enforce 1-for-1 trade: only one item per side
        sender_items = [self.sender_egg, self.sender_dinosaur]
        receiver_items = [self.receiver_egg, self.receiver_dinosaur]
        if sum([item is not None for item in sender_items]) != 1:
            raise ValidationError('Sender must offer exactly one item (egg or dinosaur).')
        if sum([item is not None for item in receiver_items]) != 1:
            raise ValidationError('Receiver must offer exactly one item (egg or dinosaur).')

    def __str__(self):
        sender_item = self.sender_egg or self.sender_dinosaur
        receiver_item = self.receiver_egg or self.receiver_dinosaur
        return f"Trade: {sender_item} for {receiver_item} ({self.status})"
