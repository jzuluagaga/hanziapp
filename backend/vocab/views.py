from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import Deck, DeckFolder, Word
from .serializers import DeckFolderSerializer, DeckSerializer, WordSerializer


class WordViewSet(ReadOnlyModelViewSet):
    queryset = Word.objects.all()
    serializer_class = WordSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['hsk_level']


class DeckFolderViewSet(ModelViewSet):
    serializer_class = DeckFolderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DeckFolder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DeckViewSet(ModelViewSet):
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deck.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
