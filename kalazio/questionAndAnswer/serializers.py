from rest_framework import serializers
from .models import QuestionAndAnswer, LikeQuestionAndAnswer
from product.serializers import ProductSerializerForComments


class LikeQuestionAndAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikeQuestionAndAnswer
        exclude = ("user",)


class QuestionAndAnswerSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = QuestionAndAnswer
        exclude = ("user",)


class QuestionAndAnswerSerializerForEdit(serializers.ModelSerializer):
    class Meta:
        model = QuestionAndAnswer
        fields = ("content",)


class QuestionAndAnswerSerializerForDisable(serializers.ModelSerializer):
    class Meta:
        model = QuestionAndAnswer
        fields = ("confirm",)


class QuestionAndAnswerForParentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = QuestionAndAnswer
        exclude = ("confirm", "likeNumber", "product", "parent")

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class QuestionAndAnswerSerializerForQuestion(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    answer_count = serializers.SerializerMethodField()

    class Meta:
        model = QuestionAndAnswer
        exclude = ("confirm", "likeNumber", "parent", "editNumber")

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_product(self, obj):
        return {
            "id": obj.product.id,
            "name": obj.product.name,
            "image": obj.product.get_absolute_url(),
        }

    def get_answer_count(self, obj):
        return QuestionAndAnswer.objects.filter(parent=obj).count()


class QuestionAndAnswerSerializerForAnswer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    class Meta:
        model = QuestionAndAnswer
        exclude = ("confirm", "likeNumber", "parent", "editNumber")

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_product(self, obj):
        return {
            "id": obj.product.id,
            "name": obj.product.name,
            "image": obj.product.get_absolute_url(),
        }

    def get_question(self, obj):
        try:
            return {
                "user": obj.parent.user.first_name + " " + obj.parent.user.last_name,
                "title": obj.parent.title,
                "content": obj.parent.content,
                "date": str(obj.parent.date),
            }
        except:
            return {
                "user": obj.parent.user.username,
                "title": obj.parent.title,
                "content": obj.parent.content,
                "date": str(obj.parent.date),
            }


class QuestionAndAnswerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    childs = serializers.SerializerMethodField()
    answer_count = serializers.SerializerMethodField()
    parent = QuestionAndAnswerForParentSerializer()

    class Meta:
        model = QuestionAndAnswer
        exclude = ("confirm", "likeNumber")

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else ""

    def get_answer_count(self, obj):
        return QuestionAndAnswer.objects.filter(parent=obj, confirm=True).count()

    def get_childs(self, obj):
        list = []
        objects = QuestionAndAnswer.objects.filter(parent=obj, confirm=True)
        for obj in objects:
            count = LikeQuestionAndAnswer.objects.filter(questionAndAnswer=obj).count()
            list.append(
                {
                    "like_count": count,
                    "id": obj.id,
                    "user": obj.user.first_name + " " + obj.user.last_name,
                    "title": obj.title,
                    "content": obj.content,
                    "date": str(obj.date),
                }
            )
        return list
