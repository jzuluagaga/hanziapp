from django.conf import settings
from django.db import models


class Word(models.Model):
    hanzi = models.CharField(max_length=20)
    pinyin_tonal = models.CharField(max_length=100)
    pinyin_numbered = models.CharField(max_length=100)
    hsk_level = models.IntegerField()
    source_no = models.IntegerField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.hanzi


class Meaning(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='meanings')
    meaning_es = models.CharField(max_length=255)
    validated = models.BooleanField(default=False)
    sense_index = models.IntegerField(default=0)
    pos_raw = models.CharField(max_length=50, blank=True)
    translation_en = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['sense_index']

    def __str__(self):
        return f"{self.word.hanzi} - {self.meaning_es}"


class Example(models.Model):
    meaning = models.ForeignKey(Meaning, on_delete=models.CASCADE, related_name='examples')
    sentence_zh = models.CharField(max_length=500)
    sentence_es = models.CharField(max_length=500)
    pinyin = models.CharField(max_length=500, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.sentence_zh


class DeckFolder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deck_folders')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Deck(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='decks')
    folder = models.ForeignKey(
        DeckFolder, on_delete=models.SET_NULL, related_name='decks', null=True, blank=True
    )
    name = models.CharField(max_length=100)
    words = models.ManyToManyField(Word, related_name='decks', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
