from rest_framework import serializers

from .models import Deck, DeckFolder, Example, Meaning, Word


class ExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Example
        fields = ['id', 'sentence_zh', 'sentence_es', 'pinyin', 'order']


class MeaningSerializer(serializers.ModelSerializer):
    examples = ExampleSerializer(many=True, read_only=True)

    class Meta:
        model = Meaning
        # `translation_en` es una glosa de terceros: nunca se muestra a un
        # estudiante (Docs R-CON-02, D-09), así que no sale por la API.
        fields = [
            'id',
            'sense_index',
            'meaning_es',
            'pos_raw',
            'validated',
            'examples',
        ]


class WordSerializer(serializers.ModelSerializer):
    meanings = MeaningSerializer(many=True, read_only=True)

    class Meta:
        model = Word
        fields = ['id', 'hanzi', 'pinyin_tonal', 'pinyin_numbered', 'hsk_level', 'meanings']


class WordSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['id', 'hanzi', 'pinyin_tonal', 'hsk_level']


class DeckSerializer(serializers.ModelSerializer):
    words = serializers.PrimaryKeyRelatedField(many=True, queryset=Word.objects.all(), required=False)
    words_detail = WordSummarySerializer(source='words', many=True, read_only=True)
    word_count = serializers.IntegerField(source='words.count', read_only=True)

    class Meta:
        model = Deck
        fields = [
            'id', 'name', 'folder', 'words', 'words_detail', 'word_count', 'created_at',
        ]
        read_only_fields = ['id', 'word_count', 'created_at']

    def validate_folder(self, folder):
        if folder is not None:
            request = self.context['request']
            if folder.user_id != request.user.id:
                raise serializers.ValidationError('La carpeta no existe.')
        return folder


class DeckFolderSerializer(serializers.ModelSerializer):
    deck_count = serializers.IntegerField(source='decks.count', read_only=True)

    class Meta:
        model = DeckFolder
        fields = ['id', 'name', 'deck_count', 'created_at']
        read_only_fields = ['id', 'deck_count', 'created_at']
