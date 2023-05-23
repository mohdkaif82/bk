import time

import pandas as pd
from ..accounts.serializers import UserRegistrationSerializer
from ..base.serializers import ModelSerializer, serializers
from ..constants import CONST_STAFF, CONST_ADVISOR
from .models import HrSettings, UserTasks, TaskComments, TaskStatus, TaskTemplates, ManagerRating, \
    TargetHeads, MonthlyTarget, UserTarget
from django.contrib.auth import get_user_model


class HrSettingsSerializer(ModelSerializer):
    class Meta:
        model = HrSettings
        fields = '__all__'


class HrSettingsBasicSerializer(ModelSerializer):
    class Meta:
        model = HrSettings
        fields = '__all__'


class TaskTemplatesSerializer(ModelSerializer):
    department_data = serializers.SerializerMethodField()
    designation_data = serializers.SerializerMethodField()
    priority_data = serializers.SerializerMethodField()

    class Meta:
        model = TaskTemplates
        fields = '__all__'

    @staticmethod
    def get_department_data(obj):
        return HrSettingsBasicSerializer(obj.department).data if obj.department else None

    @staticmethod
    def get_designation_data(obj):
        return HrSettingsBasicSerializer(obj.designation).data if obj.designation else None

    @staticmethod
    def get_priority_data(obj):
        return HrSettingsBasicSerializer(obj.priority).data if obj.priority else None


class UserTasksSerializer(ModelSerializer):
    assignee_data = serializers.SerializerMethodField()
    reporter_data = serializers.SerializerMethodField()
    priority_data = serializers.SerializerMethodField()
    task_status = serializers.SerializerMethodField()

    class Meta:
        model = UserTasks
        fields = '__all__'

    @staticmethod
    def get_assignee_data(obj):
        return UserRegistrationSerializer(obj.assignee).data if obj.assignee else None

    @staticmethod
    def get_reporter_data(obj):
        return UserRegistrationSerializer(obj.reporter).data if obj.reporter else None

    @staticmethod
    def get_priority_data(obj):
        return HrSettingsBasicSerializer(obj.priority).data if obj.priority else None

    @staticmethod
    def get_task_status(obj):
        if obj.completed_on:
            return "Completed"
        elif not TaskStatus.objects.filter(task=obj.id).exists():
            return "Open"
        elif TaskStatus.objects.filter(task=obj.id, stop=None).exists():
            return "In Progress"
        else:
            return "Paused"

    @staticmethod
    def create(validated_data):
        from ..practice.services import send_notification
        task = UserTasks.objects.create(**validated_data)
        title = "New Task Created"
        body = task.name + "\nFor: " + task.assignee.first_name if task.assignee else task.name
        send_notification(task.reporter, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
        send_notification(task.assignee, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
        send_notification(task.assignee, None, CONST_ADVISOR, title, body, "TaskDescription", str(task.pk))
        return task

    def update(self, instance, validated_data):
        from ..practice.services import send_notification
        UserTasks.objects.filter(id=instance.id).update(**validated_data)
        instance.save()
        task = UserTasks.objects.get(id=instance.id)
        title = "Task Modified"
        body = task.name + "\nFor: " + task.assignee.first_name if task.assignee else task.name
        send_notification(task.reporter, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
        send_notification(task.assignee, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
        send_notification(task.assignee, None, CONST_ADVISOR, title, body, "TaskDescription", str(task.pk))
        return instance


class TaskCommentsSerializer(ModelSerializer):
    comment_by = serializers.SerializerMethodField()

    class Meta:
        model = TaskComments
        fields = '__all__'

    @staticmethod
    def get_comment_by(obj):
        return obj.created_by.first_name if obj.created_by else None


class ManagerRatingSerializer(ModelSerializer):
    user_data = serializers.SerializerMethodField()
    rating_by_data = serializers.SerializerMethodField()

    class Meta:
        model = ManagerRating
        fields = '__all__'

    @staticmethod
    def get_user_data(obj):
        return UserRegistrationSerializer(obj.user).data if obj.user else None

    @staticmethod
    def get_rating_by_data(obj):
        return UserRegistrationSerializer(obj.created_by).data if obj.created_by else None


class TaskStatusSerializer(ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = '__all__'


class TargetHeadsSerializer(ModelSerializer):
    class Meta:
        model = TargetHeads
        fields = '__all__'


class TargetHeadsDataSerializer(ModelSerializer):
    department = HrSettingsBasicSerializer(required=False)
    designation = HrSettingsBasicSerializer(required=False)
    project = HrSettingsBasicSerializer(required=False)

    class Meta:
        model = TargetHeads
        fields = '__all__'


class MonthlyTargetSerializer(ModelSerializer):
    class Meta:
        model = MonthlyTarget
        fields = '__all__'


class MonthlyTargetDataSerializer(ModelSerializer):
    head = TargetHeadsDataSerializer(required=False)

    class Meta:
        model = MonthlyTarget
        fields = '__all__'


class MonthlyTargetHeadsSerializer(ModelSerializer):
    department = HrSettingsBasicSerializer(required=False)
    designation = HrSettingsBasicSerializer(required=False)
    project = HrSettingsBasicSerializer(required=False)
    month_target = serializers.SerializerMethodField(required=False)

    class Meta:
        model = TargetHeads
        fields = '__all__'

    def get_month_target(self, obj):
        month = self.context.get('month', None)
        year = self.context.get('year', None)
        target = None
        if month and year:
            target = MonthlyTarget.objects.filter(head=obj.id, month=month, year=year, is_active=True).first()
        return MonthlyTargetDataSerializer(target).data if target else None


class UserTargetHeadsSerializer(ModelSerializer):
    department = HrSettingsBasicSerializer(required=False)
    designation = HrSettingsBasicSerializer(required=False)
    project = HrSettingsBasicSerializer(required=False)
    date_target = serializers.SerializerMethodField(required=False)
    month_target = serializers.SerializerMethodField(required=False)

    class Meta:
        model = TargetHeads
        fields = '__all__'

    def get_date_target(self, obj):
        date = self.context.get('date', None)
        user = self.context.get('user', None)
        target = None
        if date and user:
            target = UserTarget.objects.filter(head=obj.id, date=date, user=user, is_active=True).first()
        return UserTargetDataSerializer(target).data if target else None

    def get_month_target(self, obj):
        date = pd.to_datetime(self.context.get('date', None))
        target = 1
        if date:
            target = MonthlyTarget.objects.filter(head=obj.id, year=date.year, month=date.month, is_active=True).first()
        return MonthlyTargetSerializer(target).data if target else None


class UserTargetSerializer(ModelSerializer):
    class Meta:
        model = UserTarget
        fields = '__all__'


class UserTargetDataSerializer(ModelSerializer):
    head = TargetHeadsDataSerializer(required=False)

    class Meta:
        model = UserTarget
        fields = '__all__'


class UserTasksDetailSerializer(ModelSerializer):
    assignee_data = serializers.SerializerMethodField()
    reporter_data = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    work_time = serializers.SerializerMethodField()
    work_log = serializers.SerializerMethodField()
    task_status = serializers.SerializerMethodField()
    priority_data = serializers.SerializerMethodField()

    class Meta:
        model = UserTasks
        fields = '__all__'

    @staticmethod
    def get_assignee_data(obj):
        return UserRegistrationSerializer(obj.assignee).data if obj.assignee else None

    @staticmethod
    def get_reporter_data(obj):
        return UserRegistrationSerializer(obj.reporter).data if obj.reporter else None

    @staticmethod
    def get_comments(obj):
        comments = TaskComments.objects.filter(task=obj.id, is_active=True)
        return TaskCommentsSerializer(comments, many=True).data if len(comments) > 0 else []

    @staticmethod
    def get_work_time(obj):
        logs = TaskStatus.objects.filter(task=obj.id)
        total = 0
        for log in logs:
            if log.start and log.stop:
                total += (log.stop - log.start).total_seconds()
        return time.strftime('%H:%M:%S', time.gmtime(total))

    @staticmethod
    def get_work_log(obj):
        logs = TaskStatus.objects.filter(task=obj.id)
        return TaskStatusSerializer(logs, many=True).data if len(logs) > 0 else []

    @staticmethod
    def get_priority_data(obj):
        return HrSettingsBasicSerializer(obj.priority).data if obj.priority else None

    @staticmethod
    def get_task_status(obj):
        if obj.completed_on:
            return "Completed"
        elif not TaskStatus.objects.filter(task=obj.id).exists():
            return "Open"
        elif TaskStatus.objects.filter(task=obj.id, stop=None).exists():
            return "In Progress"
        else:
            return "Paused"
