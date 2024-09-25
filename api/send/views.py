from rest_framework import generics, permissions
from django.db.models import Count
from django.shortcuts import get_object_or_404
from .serializers import SendList, SendDetail
from .models import Send
from ..auth.models import Person
from ..boulder.models import Boulder
from ...utils.constants import grade_labels
from decimal import Decimal

class SendList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SendList

    def get_object(self):
        return get_object_or_404(Boulder, id=self.kwargs['boulder_id'])
    
    @staticmethod
    def grade_mode(self, boulder, suggested_grade) -> int:
        """
        Calculate the boulder grade mode from every send of this boulder including the new suggested grade.
        If mode lands in between two grades, return either grade. We want to find the grade consensus.

        Args:
            boulder: Boulder
            suggested_grade: str

        Returns:
            grade: int. Returns most common grade as type int.
        """
        # convert given grade argument to its index counterpart if the grade given is the human readable grade string
        if isinstance(suggested_grade, str):
            suggested_grade: int = grade_labels.index(suggested_grade)
        # Aggregate suggested grades and get the most common one
        suggested_grade_counts_queryset = (
            Send.objects
            .filter(boulder=boulder.id)
            .values('suggested_grade')
            .annotate(count=Count('suggested_grade'))
            .order_by('-count')
        )
        # Convert the queryset to a dictionary with grades as keys and their counts as values
        suggested_grade_counts: dict[int, int] = {item['suggested_grade']: item['count'] for item in suggested_grade_counts_queryset}
        # Manually include the passed grade in the count
        if suggested_grade in suggested_grade_counts:
            suggested_grade_counts[suggested_grade] += 1
        else:
            suggested_grade_counts[suggested_grade] = 1
        # Determine the most common grade including the passed grade
        most_common_grade: int = max(suggested_grade_counts, key=suggested_grade_counts.get)
        return most_common_grade
    
    @staticmethod
    def quality_mean(self, current_mean_score, num_existing_scores, new_score) -> Decimal:
        """
        Calculates new quality rating mean after adding user's new quality rating score.
        If the current mean score is None, then make it a 0 of type Decimal.

        Args:
        current_mean_score = current mean percentage of all scores.
        num_existing_scores = number of existing scores before adding the new score.
        new_score = user's quality rating score to be included in the mean.

        Returns:
        Return new quality rating mean of type Decimal
        """
        if current_mean_score is None:
            current_mean_score = Decimal(0)
        return ((num_existing_scores * current_mean_score) + new_score) / (num_existing_scores + 1)
  
    def post(self, request, *args, **kwargs):
        boulder = self.get_object()
        current_send_count = boulder.sends_count
        boulder.sends_count = current_send_count + 1
        boulder.grade = self.grade_mode(boulder, request.data.get('suggestedGrade'))
        boulder.quality = self.quality_mean(boulder.quality, current_send_count, request.data.get('quality'))
        if boulder.first_ascensionist is None:
            user_instance = Person.objects.get(id=self.request.user.id)
            boulder.first_ascensionist = user_instance
        boulder.save()
        return self.create(request, *args, **kwargs)
    
class SendDetail(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SendDetail

    def get_object(self):
        return get_object_or_404(Send, id=self.kwargs['pk'])

    @staticmethod
    def grade_mode(self, boulder, send_id) -> int:
        """
        Calculate the boulder grade mode from every send of this boulder excluding the send from which the user wants to delete.
        If mode lands in between two grades, return either grade. We want to find the grade consensus.

        Args:
            boulder: Boulder
            send_id: int

        Returns:
            grade: int. Returns most common grade as type int.
        """
        # Aggregate suggested grades and get the most common one
        suggested_grade_counts_queryset = (
            Send.objects
            .filter(boulder=boulder.id)
            .exclude(id=send_id)  # Exclude the specific send object with send_id
            .values('suggested_grade')
            .annotate(count=Count('suggested_grade'))
            .order_by('-count')
        )
        # Convert the queryset to a dictionary with grades as keys and their counts as values
        suggested_grade_counts: dict[int, int] = {item['suggested_grade']: item['count'] for item in suggested_grade_counts_queryset}
        # Determine the most common grade including the passed grade
        most_common_grade: int = max(suggested_grade_counts, key=suggested_grade_counts.get)
        return most_common_grade
    
    @staticmethod
    def quality_mean(self, current_mean_score, num_existing_scores, remove_score) -> Decimal | None:
        """
        Calculates new quality rating mean after removing user's quality rating score.

        Args:
        current_mean_score = current mean percentage of all scores.
        num_existing_scores = number of existing scores before removing the score.
        remove_score = user's quality rating score to be removed

        Returns:
        If the number of existing scores is 0 after removing the score, return None.
        Else return new quality rating mean of type Decimal
        """
        if num_existing_scores - 1 == 0:
            return None
        else:
            return ((num_existing_scores * current_mean_score) - remove_score) / (num_existing_scores - 1)

    def delete(self, request, *args, **kwargs):
        send_instance = self.get_object()  # Get the send object
        boulder = send_instance.boulder
        sends_count = boulder.sends_count
        current_send_count = boulder.sends_count
        boulder.sends_count = current_send_count - 1
        boulder.grade = self.grade_mode(boulder, self.kwargs['pk'])
        boulder.quality = self.quality_mean(boulder.quality, current_send_count, send_instance.quality)
        if boulder.first_ascensionist:
            if sends_count == 1 and boulder.first_ascensionist.id is self.request.user.id:
                boulder.first_ascensionist = None
        boulder.save()
        return self.destroy(request, *args, **kwargs)
