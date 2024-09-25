from climbers_eye_backend.models import Boulder, Send

class BoulderMixin:
    def get_userSendsCount(self, obj: Boulder):
        user_id = self.context['request'].user.id
        return Send.objects.filter(boulder=obj, person_id=user_id).count()