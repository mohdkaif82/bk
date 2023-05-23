from ..base.serializers import ModelSerializer
from .models import ArogyamPost, ArogyamVideoFile, ArogyamDisease, ArogyamEvents, \
    ArogyamContactUs, ArogyamPageSEO, ArogyamSlider, ArogyamSuggestionBox, ArogyamComment, ArogyamRating, \
    ArogyamContactUsForm
from ..utils.email import send


class PostSerializer(ModelSerializer):
    class Meta:
        model = ArogyamPost
        fields = '__all__'


class VideoFileSerializer(ModelSerializer):
    class Meta:
        model = ArogyamVideoFile
        fields = '__all__'


class DiseaseSerializer(ModelSerializer):
    class Meta:
        model = ArogyamDisease
        fields = '__all__'


class EventsSerializer(ModelSerializer):
    class Meta:
        model = ArogyamEvents
        fields = '__all__'


class ContactUsSerializer(ModelSerializer):
    class Meta:
        model = ArogyamContactUs
        fields = '__all__'


class PageSEOSerializer(ModelSerializer):
    class Meta:
        model = ArogyamPageSEO
        fields = '__all__'


class SliderSerializer(ModelSerializer):
    class Meta:
        model = ArogyamSlider
        fields = '__all__'


class CommentSerializer(ModelSerializer):
    class Meta:
        model = ArogyamComment
        fields = '__all__'


class RatingSerializer(ModelSerializer):
    class Meta:
        model = ArogyamRating
        fields = '__all__'


class ContactUsFormSerializer(ModelSerializer):
    class Meta:
        model = ArogyamContactUsForm
        fields = '__all__'

    def create(self, validated_data):
        """
         We will create the userprofile object here. If secondary address present then only create
         secondary_address instance and assign it to userprofile object.
        """

        contact_obj = ArogyamContactUsForm.objects.create(**validated_data)
        if contact_obj.email:
            subject = "Contact Us Email"
            text_body = str(contact_obj.mobile) + " . " + str(contact_obj.name) + '. Description ' + str(
                contact_obj.description)
            send(contact_obj.email, contact_obj.subject, '', text_body=text_body)
        return contact_obj


class SuggestionBoxSerializer(ModelSerializer):
    class Meta:
        model = ArogyamSuggestionBox
        fields = '__all__'
