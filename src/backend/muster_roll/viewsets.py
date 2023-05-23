from datetime import datetime, timedelta
import pandas as pd
from ..accounts.serializers import TaskUserSerializer
from ..base import response
from ..base.api.pagination import StandardResultsSetPagination
from ..base.api.viewsets import ModelViewSet
from ..constants import CONST_GLOBAL_PRACTICE, CONFIG, CONST_STAFF, CONST_ADVISOR
from .constants import HR_SETTINGS, CONST_PROJECT
from .models import HrSettings, UserTasks, TaskStatus, TaskComments, TaskTemplates, ManagerRating, \
    UserTarget, TargetHeads, MonthlyTarget
from .permissions import HrSettingsPermissions, TasksPermissions
from .serializers import HrSettingsSerializer, UserTasksSerializer, UserTasksDetailSerializer, \
    TaskTemplatesSerializer, ManagerRatingSerializer, UserTargetSerializer, UserTargetDataSerializer, \
    TargetHeadsSerializer, TargetHeadsDataSerializer, MonthlyTargetSerializer, MonthlyTargetDataSerializer, \
    MonthlyTargetHeadsSerializer, UserTargetHeadsSerializer
from .services import create_update_multiple_record
from ..patients.models import Patients
from ..patients.services import create_update_record
from ..practice.models import PracticeStaff
from ..practice.serializers import PracticeStaffBasicSerializer
from ..practice.services import dict_to_mail, send_notification
from ..utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import F, Avg, Count
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser


class TasksViewSet(ModelViewSet):
    serializer_class = UserTasksSerializer
    queryset = UserTasks.objects.all()
    permission_classes = (TasksPermissions,)
    parser_classes = (JSONParser, MultiPartParser)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        print("Vnod1", self.request.query_params.get('deadline_gte', None))
        assignees = self.request.query_params.get('assignee', None)
        reporters = self.request.query_params.get('reporter', None)
        deadline_gte = self.request.query_params.get('deadline_gte', None)
        deadline_lte = self.request.query_params.get('deadline_lte', None)
        designation = self.request.query_params.get('designation', None)
        priorities = self.request.query_params.get('priority', None)
        department = self.request.query_params.get('department', None)
        incomplete = self.request.query_params.get('incomplete', None)
        overdue = self.request.query_params.get('overdue', None)
        mail_to = self.request.query_params.get('mail_to', None)
        queryset = super(TasksViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        start_date = datetime.now()
        end_date = datetime.now()
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        print("Vnod2", deadline_gte)
        if deadline_gte and deadline_lte:
            print("Vnod3", queryset.filter(deadline__lte=F('completed_on')))
            queryset = queryset.filter(deadline__range=[deadline_gte, deadline_lte])
            print("Vnod4", queryset)
            start_date = pd.to_datetime(deadline_gte)
            print("Vnod5", start_date)
            end_date = pd.to_datetime(deadline_lte)
        if designation == CONFIG["config_advisor_designation"] and department == CONFIG["config_advisor_department"]:
            queryset = queryset.exclude(assignee__patients=None).filter(assignee__patients__is_agent=True,
                                                                        assignee__patients__is_approved=True)
        if department and not department == CONFIG["config_advisor_department"]:
            department_employees = PracticeStaff.objects.filter(is_active=True, department=department).values_list(
                'user')
            queryset = queryset.filter(assignee__in=department_employees)
        if designation and not designation == CONFIG["config_advisor_designation"]:
            designation_employees = PracticeStaff.objects.filter(is_active=True, designation=designation).values_list(
                'user')
            queryset = queryset.filter(assignee__in=designation_employees)
        if assignees:
            print("vinod 10",assignees)
            assignee_list = assignees.split(",")
            print("vinod 11",assignee_list)
            queryset = queryset.filter(assignee__in=assignee_list)
            print("vinod 12",assignees)
        if reporters:
            reporter_list = reporters.split(",")
            queryset = queryset.filter(reporter__in=reporter_list)
        if overdue and overdue == "true":
            queryset = queryset.filter(deadline__lte=F('completed_on'))
        if overdue and overdue == "false":
            queryset = queryset.filter(deadline__gte=F('completed_on'))
        if deadline_gte:
            print("Vnod6", deadline_gte)
            queryset = queryset.filter(deadline__gte=deadline_gte)
            print("Vnod7", queryset)
        if deadline_lte:
            queryset = queryset.filter(deadline__lte=deadline_lte)
        if incomplete and incomplete == "true":
            queryset = queryset.filter(completed_on=None)
        elif incomplete and incomplete == "false":
            queryset = queryset.exclude(completed_on=None)
        if priorities:
            priority_list = priorities.split(",")
            queryset = queryset.filter(priority__in=priority_list)
        if mail_to:
            for item in queryset:
                item = UserTasksSerializer(queryset.objects.get(id=item['id'])).data
                if (item["deadline"] and item["task_status"] != "Completed" and item["deadline"] >= datetime.now()):
                    delta=pd.to_timedelta(item["deadline"] - datetime.now())
                elif (item["deadline"] and item["deadline"]<=datetime.now()):
                    delta="delayed by" + str(pd.to_timedelta(datetime.now() - item["deadline"]))
                else:
                    delta="--"

                ready_data.append({
                    "Task Name": item["name"],
                    "Assignee": item["assignee_data"]["first_name"] if item["assignee_data"]["first_name"] else "--",
                    "Assigner": item["reporter_data"]["first_name"] if item["reporter_data"]["first_name"] else "--",
                    "Priority": item["priority_data"]["value"] if item["priority_data"]["value"] else "--",
                    "Status": item["task_status"] if item["task_status"] else "--",
                    "Time Remaining": delta
                })
            subject = "All Tasks Report from " + start_date.strftime("%d/%m/%Y") + " to " + end_date.strftime(
                "%d/%m/%Y")
            body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                   + "<br/><b>" + practice_name + "</b>"
            error, msg = dict_to_mail(ready_data, "All_Tasks_Report_" + start + "_" + end, mail_to,
                                      subject, body)
        return queryset.order_by('-id')

    @action(methods=['GET'], detail=False)
    def assignee(self, request, *args, **kwargs):
        user = request.user if request.user and not request.user.is_anonymous else None
        if user:
            emp = PracticeStaff.objects.filter(user=user, is_active=True).first()
            adv = Patients.objects.filter(user=user, is_active=True).first()
            emp_id = emp.emp_id if emp else adv.custom_id if adv else None
            result = []
            result += [{"first_name": user.first_name, "id": user.id, "emp_id": emp_id}]
            is_manager = PracticeStaff.objects.filter(is_active=True, user=user, is_manager=True)
            if user.is_superuser:
                all_advisors = Patients.objects.filter(is_agent=True, is_active=True, is_approved=True) \
                    .exclude(user__id=None).values('user__first_name', 'user__id', 'custom_id') \
                    .annotate(emp_id=F('custom_id'), id=F('user__id'), first_name=F('user__first_name')) \
                    .values('first_name', 'id', 'emp_id')
                all_staff = get_user_model().objects.filter(is_active=True).exclude(practicestaff=None) \
                    .values('first_name', 'id', 'practicestaff__emp_id').distinct('id').annotate(
                    emp_id=F('practicestaff__emp_id')).values('first_name', 'id', 'emp_id')
                result += list(all_staff) + list(all_advisors)
            elif is_manager.exists():
                all_advisors = Patients.objects.filter(id__in=is_manager.first().advisors.all()) \
                    .exclude(user__id=None).values('user__first_name', 'user__id', 'custom_id') \
                    .annotate(emp_id=F('custom_id'), id=F('user__id'), first_name=F('user__first_name')) \
                    .values('first_name', 'id', 'emp_id')
                all_staff = PracticeStaff.objects.filter(id__in=is_manager.first().employees.all()) \
                    .values('user__id', 'user__first_name', 'emp_id') \
                    .annotate(id=F('user__id'), first_name=F('user__first_name')).values('first_name', 'id', 'emp_id')
                result += list(all_staff) + list(all_advisors)
            res_list = []
            for i in range(len(result)):
                if result[i]["id"] not in [x["id"] for x in result[i + 1:]]:
                    res_list.append(result[i])
            return response.Ok(res_list)
        else:
            return response.BadRequest({"detail": "Invalid User"})

    @action(methods=['GET'], detail=False)
    def datewise_ratings(self, request, *args, **kwargs):
        user = request.user if request.user and not request.user.is_anonymous else None
        if user:
            date = request.query_params.get("date", None)
            result = []
            is_manager = PracticeStaff.objects.filter(is_active=True, user=user, is_manager=True)
            if is_manager.exists():
                all_staff = PracticeStaff.objects.filter(id__in=is_manager.first().employees.all()) \
                    .values('user__id', 'user__first_name', 'emp_id') \
                    .annotate(id=F('user__id'), first_name=F('user__first_name')).values('first_name', 'id', 'emp_id')
                all_advisors = Patients.objects.filter(id__in=is_manager.first().advisors.all()) \
                    .exclude(user__id=None).values('user__first_name', 'user__id', 'custom_id') \
                    .annotate(emp_id=F('custom_id'), id=F('user__id'), first_name=F('user__first_name')) \
                    .values('first_name', 'id', 'emp_id')
                result += list(all_staff) + list(all_advisors)
            res_list = []
            id_list = []
            for i in range(len(result)):
                if result[i]["id"] not in [x["id"] for x in result[i + 1:]]:
                    res_list.append(result[i])
                    id_list.append(result[i]["id"])
            ratings = ManagerRating.objects.filter(date=date, user__in=id_list, is_active=True)
            for rating in ratings:
                try:
                    res_list[id_list.index(rating.user.pk)]["rating"] = ManagerRatingSerializer(rating).data
                except ValueError:
                    print("Invalid Key")
            return response.Ok(res_list)
        else:
            return response.BadRequest({"detail": "Invalid User"})

    @action(methods=['GET'], detail=False)
    def reporter(self, request, *args, **kwargs):
        user = request.query_params.get("user", None)
        staff = PracticeStaff.objects.filter(user=user, is_active=True).first()
        advisor = Patients.objects.filter(user=user, is_approved=True, is_agent=True, is_active=True).first()
        super_users = PracticeStaff.objects.filter(user__is_superuser=True) \
            .values('user__id', 'user__first_name', 'emp_id') \
            .annotate(id=F('user__id'), first_name=F('user__first_name')).values('first_name', 'id', 'emp_id')
        managers = []
        if staff:
            managers += list(PracticeStaff.objects.filter(is_active=True, employees=staff).values_list('id', flat=True))
        if advisor:
            managers += list(
                PracticeStaff.objects.filter(is_active=True, advisors=advisor).values_list('id', flat=True))
        all_managers = PracticeStaff.objects.filter(id__in=managers, is_active=True) \
            .values('user__id', 'user__first_name', 'emp_id') \
            .annotate(id=F('user__id'), first_name=F('user__first_name')).values('first_name', 'id', 'emp_id')
        result = list(all_managers) + list(super_users)
        res_list = []
        for i in range(len(result)):
            if result[i] not in result[i + 1:]:
                res_list.append(result[i])
        return response.Ok(res_list)

    @action(methods=['GET'], detail=True)
    def details(self, request, *args, **kwargs):
        task = self.get_object()
        task_data = UserTasksDetailSerializer(task).data
        return response.Ok(task_data)

    @action(methods=['GET', 'POST'], detail=False)
    def heads(self, request, *args, **kwargs):
        if request.method == "GET":
            department = request.query_params.get("department", None)
            designation = request.query_params.get("designation", None)
            project = request.query_params.get("project", None)
            queryset = TargetHeads.objects.filter(is_active=True)
            if department:
                queryset = queryset.filter(department=department)
            if designation:
                queryset = queryset.filter(designation=designation)
            if project:
                queryset = queryset.filter(project=project)
            return response.Ok(TargetHeadsDataSerializer(queryset, many=True).data)
        else:
            return response.Ok(create_update_record(request, TargetHeadsSerializer, TargetHeads))

    @action(methods=['GET', 'POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def monthly_targets(self, request, *args, **kwargs):
        if request.method == "GET":
            department = request.query_params.get("department", None)
            designation = request.query_params.get("designation", None)
            project = request.query_params.get("project", None)
            head = request.query_params.get("head", None)
            queryset = MonthlyTarget.objects.filter(is_active=True)
            if department:
                queryset = queryset.filter(head__department=department)
            if designation:
                queryset = queryset.filter(head__designation=designation)
            if project:
                queryset = queryset.filter(head__project=project)
            if head:
                queryset = queryset.filter(head=head)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(MonthlyTargetDataSerializer(page, many=True).data)
            return response.Ok(MonthlyTargetDataSerializer(queryset, many=True).data)
        else:
            return response.Ok(
                create_update_multiple_record(request.data.copy(), MonthlyTargetSerializer, MonthlyTarget))

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def month_target_status(self, request, *args, **kwargs):
        month = request.query_params.get("month", None)
        year = request.query_params.get("year", None)
        department = request.query_params.get("department", None)
        designation = request.query_params.get("designation", None)
        if month and year:
            queryset = TargetHeads.objects.filter(is_active=True)
            if department:
                queryset = queryset.filter(department=department)
            if designation:
                queryset = queryset.filter(designation=designation)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(
                    MonthlyTargetHeadsSerializer(page, many=True, context={'month': month, 'year': year}).data)
            return response.Ok(
                MonthlyTargetHeadsSerializer(queryset, many=True, context={'month': month, 'year': year}).data)
        else:
            return response.BadRequest({"detail": "Invalid Month/Year"})

    @action(methods=['GET', 'POST'], detail=False)
    def user_targets(self, request, *args, **kwargs):
        if request.method == "GET":
            queryset = UserTarget.objects.filter(is_active=True)
            return response.Ok(UserTargetDataSerializer(queryset, many=True).data)
        else:
            return response.Ok(create_update_multiple_record(request.data.copy(), UserTargetSerializer, UserTarget))

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def user_target_status(self, request, *args, **kwargs):
        date = request.query_params.get("date", None)
        user = request.query_params.get("user", None)
        department = request.query_params.get("department", None)
        designation = request.query_params.get("designation", None)
        if date:
            queryset = TargetHeads.objects.filter(is_active=True)
            if department:
                queryset = queryset.filter(department=department)
            if designation:
                queryset = queryset.filter(designation=designation)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(UserTargetHeadsSerializer(page, many=True,
                                                                             context={'date': date, 'user': user}).data)
            return response.Ok(UserTargetHeadsSerializer(queryset, many=True,
                                                         context={'date': date, 'user': user}).data)
        else:
            return response.BadRequest({"detail": "Invalid Date"})

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def department_target_status(self, request, *args, **kwargs):
        date = request.query_params.get("date", None)
        department = request.query_params.get("user", None)
        result = []
        if date:
            queryset = PracticeStaff.objects.filter(is_active=True)
            if department:
                queryset = queryset.filter(department=department)
            page = self.paginate_queryset(queryset)
            if page is not None:
                for staff in page:
                    targets = TargetHeads.objects.filter(is_active=True, department=staff.department,
                                                         designation=staff.designation)
                    for target in targets:
                        result.append({"staff": PracticeStaffBasicSerializer(staff).data,
                                       "targets": UserTargetHeadsSerializer(target,
                                                                            context={'date': date,
                                                                                     'user': staff.user.pk}).data})
                return self.get_paginated_response(result)
            return response.Ok([])
        else:
            return response.BadRequest({"detail": "Invalid Date"})

    @action(methods=['GET'], detail=False)
    def day_summary(self, request, *args, **kwargs):
        user = request.query_params.get("user", None)
        date = timezone.from_str(request.query_params.get("date"))
        start = timezone.get_day_start(date)
        end = timezone.get_day_end(date)
        comments = TaskComments.objects.filter(created_at__range=[start, end], created_by=user, is_active=True)
        work_logs = TaskStatus.objects.filter(created_at__range=[start, end], created_by=user, is_active=True)
        tasks = UserTasks.objects.filter(created_at__range=[start, end], assignee=user, is_active=True)
        result = []
        for task in tasks:
            result.append({
                "time": task.created_at,
                "log": "New Task Assigned: " + task.name
            })
        for comment in comments:
            result.append({
                "time": comment.created_at,
                "log": "New Comment: " + comment.comment + "\n On Task: " + comment.task.name
            })
        for log in work_logs:
            result.append({
                "time": log.start,
                "log": "Work Started on Task: " + log.task.name
            })
            if log.stop:
                result.append({
                    "time": log.stop,
                    "log": "Work Stopped on Task: " + log.task.name
                })
        result = sorted(result, key=lambda i: i['time'])
        return response.Ok(result)

    @action(methods=['POST'], detail=True)
    def start_task(self, request, *args, **kwargs):
        task = self.get_object()
        if TaskStatus.objects.filter(task=task, is_active=True, stop=None).exists():
            return response.BadRequest({"detail": "This task is already started"})
        else:
            TaskStatus.objects.create(task=task, start=datetime.now())
            title = "Work Started"
            body = "On:" + task.name + "\nBy: " + \
                   request.user.first_name if request.user and not request.user.is_anonymous else task.name
            if not request.user == task.reporter:
                send_notification(task.reporter, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
            if not request.user == task.assignee:
                send_notification(task.assignee, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
                send_notification(task.assignee, None, CONST_ADVISOR, title, body, "TaskDescription", str(task.pk))
            return response.Ok({"detail": "Work Started on this Task"})

    @action(methods=['POST'], detail=True)
    def stop_task(self, request, *args, **kwargs):
        task = self.get_object()
        if not TaskStatus.objects.filter(task=task, is_active=True, stop=None).exists():
            return response.BadRequest({"detail": "This task is not yet started"})
        else:
            status = TaskStatus.objects.get(task=task, is_active=True, stop=None)
            status.stop = datetime.now()
            status.save()
            title = "Work Stopped"
            body = "On:" + task.name + "\nBy: " + \
                   request.user.first_name if request.user and not request.user.is_anonymous else task.name
            if not request.user == task.reporter:
                send_notification(task.reporter, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
            if not request.user == task.assignee:
                send_notification(task.assignee, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
                send_notification(task.assignee, None, CONST_ADVISOR, title, body, "TaskDescription", str(task.pk))
            return response.Ok({"detail": "Work Stopped on this Task"})

    @action(methods=['POST'], detail=True)
    def complete_task(self, request, *args, **kwargs):
        task = self.get_object()
        complete_remark = request.data.get("complete_remark", None)
        if TaskStatus.objects.filter(task=task, is_active=True, stop=None).exists():
            status = TaskStatus.objects.get(task=task, is_active=True, stop=None)
            status.stop = datetime.now()
            status.save()
        task.completed_on = datetime.now()
        task.completed_by = request.user if request.user and not request.user.is_anonymous else None
        completed_user = request.user.first_name if request.user and not request.user.is_anonymous else None
        task.complete_remark = complete_remark
        task.save()
        title = "Task Completed"
        body = task.name + "\nCompleted By: " + completed_user if completed_user else task.name
        if not request.user == task.reporter:
            send_notification(task.reporter, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
        if not request.user == task.assignee:
            send_notification(task.assignee, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
            send_notification(task.assignee, None, CONST_ADVISOR, title, body, "TaskDescription", str(task.pk))
        return response.Ok({"detail": "Task Completed Successfully"})

    @action(methods=['POST', 'PUT'], detail=True)
    def comment(self, request, *args, **kwargs):
        task = self.get_object()
        comment = request.data.get("comment", None)
        comment_id = request.data.pop("id", None)
        is_active = request.data.get("is_active", None)
        username = request.user.first_name if request.user and not request.user.is_anonymous else None
        if request.method == "POST":
            TaskComments.objects.create(task=task, comment=comment)
            msg = "Comment added Successfully"
            title = "Comment Added"
        else:
            comment_obj = TaskComments.objects.get(id=comment_id)
            if comment:
                comment_obj.comment = comment
            if is_active is not None:
                comment_obj.is_active = is_active
            comment_obj.save()
            msg = "Comment modified Successfully"
            title = "Comment Modified"
        body = "On: " + task.name + "\nModified By: " + username if username else "On: " + task.name
        if not request.user == task.reporter:
            send_notification(task.reporter, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
        if not request.user == task.assignee:
            send_notification(task.assignee, None, CONST_STAFF, title, body, "TaskDescription", str(task.pk))
            send_notification(task.assignee, None, CONST_ADVISOR, title, body, "TaskDescription", str(task.pk))
        return response.Ok({"detail": msg})

    @action(methods=['GET', 'POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def templates(self, request, *args, **kwargs):
        if request.method == "GET":
            template_id = request.query_params.get('id', None)
            department = request.query_params.get('department', None)
            designation = request.query_params.get('designation', None)
            queryset = TaskTemplates.objects.filter(is_active=True)
            if template_id:
                queryset = queryset.filter(id=template_id)
            if designation:
                queryset = queryset.filter(designation=designation)
            if department:
                queryset = queryset.filter(department=department)
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(TaskTemplatesSerializer(page, many=True).data)
            response.Ok(TaskTemplatesSerializer(queryset, many=True).data)
        else:
            return response.Ok(create_update_record(request, TaskTemplatesSerializer, TaskTemplates))

    @action(methods=['POST'], detail=False)
    def assign_template(self, request):
        request_data = request.data.copy()
        templates = request_data.pop("template", [])
        templates = templates if type(templates) == type(list()) else [templates]
        result = []
        for template in templates:
            try:
                template_obj = TaskTemplates.objects.get(id=template, is_active=True)
            except:
                return response.BadRequest({"detail": "Invalid Recurring Task"})
            request_data["template"] = template
            request_data["name"] = template_obj.name
            request_data["priority"] = template_obj.priority.pk
            request_data["description"] = template_obj.description
            request_data["remark"] = template_obj.remark
            request_data["is_recurring"] = True
            request_data["deadline"] = datetime.now() + timedelta(
                days=template_obj.days) if template_obj.days else datetime.now()
            serializer = UserTasksSerializer(data=request_data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_object = serializer.save()
            result.append(update_object)
        return response.Created(UserTasksSerializer(result, many=True).data)

    @action(methods=['GET', 'POST'], detail=False)
    def rating(self, request):
        if request.method == "GET":
            user = request.query_params.get('user', None)
            created_by = request.query_params.get('created_by', None)
            start = request.query_params.get('start', None)
            end = request.query_params.get('end', None)
            queryset = ManagerRating.objects.filter(is_active=True)
            if user:
                queryset = queryset.filter(user=user)
            if created_by:
                queryset = queryset.filter(created_by=created_by)
            if start and end:
                queryset = queryset.filter(date__range=[start, end])
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(ManagerRatingSerializer(page, many=True).data)
            response.Ok(ManagerRatingSerializer(queryset, many=True).data)
        else:
            rating_by = request.user if request.user and not request.user.is_anonymous else None
            data = request.data.copy()
            user = data.get('user', None)
            date = data.get('date', None)
            rating_id = data.get('id', None)
            if user and rating_by and date and not rating_id:
                try:
                    ManagerRating.objects.get(user=user, created_by=rating_by, date=date, is_active=True)
                    return response.BadRequest({"detail": "Rating already given for this date."})
                except:
                    res = create_update_record(request, ManagerRatingSerializer, ManagerRating)
                    return response.Ok(res) if rating_id else response.Created(res)
            elif user and rating_by and date and rating_id:
                res = create_update_record(request, ManagerRatingSerializer, ManagerRating)
                return response.Ok(res) if rating_id else response.Created(res)
            else:
                response.BadRequest({"detail": "Invalid Manager Login"})

    @action(methods=['GET'], detail=False)
    def rating_reports(self, request):
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        user = request.query_params.get('user', None)
        manager = request.query_params.get('manager', None)
        department = request.query_params.get('department', None)
        designation = request.query_params.get('designation', None)
        mail_to = request.query_params.get('mail_to', None)
        report_type = request.query_params.get('type', None)
        queryset = ManagerRating.objects.filter(is_active=True)
        start_date = datetime.now()
        end_date = datetime.now()
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        if start and end:
            queryset = queryset.filter(date__range=[start, end])
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
        if user:
            queryset = queryset.filter(user=user)
        if manager:
            queryset = queryset.filter(created_by=manager)
        if designation == CONFIG["config_advisor_designation"] and department == CONFIG["config_advisor_department"]:
            user_ids = Patients.objects.filter(is_active=True, is_agent=True, is_approved=True).values_list('user',
                                                                                                            flat=True)
            queryset = queryset.filter(user__in=user_ids)
        if department and not department == CONFIG["config_advisor_department"]:
            user_ids = PracticeStaff.objects.filter(department=department, is_active=True).values_list('user',
                                                                                                       flat=True)
            queryset = queryset.filter(user__in=user_ids)
        if designation and not designation == CONFIG["config_advisor_designation"]:
            user_ids = PracticeStaff.objects.filter(designation=designation, is_active=True).values_list('user',
                                                                                                         flat=True)
            queryset = queryset.filter(user__in=user_ids)
        queryset = queryset.exclude(rating=None)
        if report_type == "AVERAGE":
            queryset = queryset.values('user').annotate(avg_rating=Avg('rating'))
            for data in queryset:
                data['user'] = TaskUserSerializer(get_user_model().objects.get(id=data['user'])).data
            if mail_to:
                for item in queryset:
                    ready_data.append({
                        "Name": item['user']['first_name'],
                        "Emp ID": item['user']['detail']['emp_id'] if item['user']['detail']['emp_id'] else "--",
                        "Department": item['user']['detail']['department'] if item['user']['detail'][
                            'department'] else "--",
                        "Designation": item['user']['detail']['designation'] if item['user']['detail'][
                            'designation'] else "--",
                        "Average Rating": item['avg_rating'] if item['avg_rating'] else 0
                    })
                subject = "Average Rating Report from " + start_date.strftime("%d/%m/%Y") + " to " + end_date.strftime(
                    "%d/%m/%Y")
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Avg_Rating_Report_" + start + "_" + end, mail_to,
                                          subject, body)
                queryset = {"detail": msg, "error": error}

            if "error" in queryset and queryset["error"]:
                return response.BadRequest(queryset)
            return response.Ok(queryset)
        else:
            return response.BadRequest({"detail": "Invalid type sent"})

    @action(methods=['GET'], detail=False)
    def task_reports(self, request):
        start = request.query_params.get('start', None)
        end = request.query_params.get('end', None)
        mail_to = request.query_params.get('mail_to', None)
        incomplete = request.query_params.get('incomplete', None)
        report_type = request.query_params.get('type', None)
        queryset = UserTasks.objects.filter(is_active=True, completed_on=None)
        practice_name = CONST_GLOBAL_PRACTICE
        ready_data = []
        if start and end:
            queryset = queryset.filter(created_at__range=[start, end])
        if incomplete and incomplete == "true":
            queryset = queryset.filter(completed_on=None)
        elif incomplete and incomplete == "false":
            queryset = queryset.exclude(completed_on=None)
        if report_type == "DEPARTMENT":
            result = {}
            priorities = []
            queryset = queryset.values('assignee', 'priority', 'priority__value').annotate(count=Count('id'))
            for data in queryset:
                assignee = TaskUserSerializer(get_user_model().objects.get(id=data['assignee'])).data
                dept = assignee["details"]["department"] if assignee["details"][
                    "department"] else "No Department Assigned"
                priority = data["priority__value"]
                priorities.append(priority) if priority not in priorities else None
                if dept in result and priority in result[dept]:
                    result[dept][priority] += data["count"] if data["count"] else 0
                if dept in result and priority not in result[dept]:
                    result[dept][priority] = data["count"] if data["count"] else 0
                else:
                    result[dept] = {}
                    result[dept][priority] = data["count"] if data["count"] else 0
            result["priorities"] = priorities
            if mail_to:
                for item in result.keys():
                    priority_data = result[item]
                    item_data = {
                        "Department": item
                    }
                    for priority in priorities:
                        item_data[priority] = 0
                    for priority in priority_data.keys():
                        item_data[priority] = priority_data[priority]
                    ready_data.append(item_data)
                subject = "Current Department Wise Report"
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Department_Task_Report", mail_to, subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        else:
            return response.BadRequest({"detail": "Invalid type sent"})

    @action(methods=['GET'], detail=False)
    def user_target_report(self, request):
        month = request.query_params.get('month', None)
        year = request.query_params.get('year', None)
        mail_to = request.query_params.get('mail_to', None)
        user = request.query_params.get('user', None)
        projects = HrSettings.objects.filter(name=CONST_PROJECT, is_active=True)
        result = []
        if user and year and month:
            queryset = UserTarget.objects.filter(is_active=True, user=user, date__year=year, date__month=month)
            for project in projects:
                data = {}
                project_heads = queryset.filter(head__project=project).distinct('head').values_list('head', flat=True)
                heads = TargetHeads.objects.filter(id__in=project_heads)
                data["heads"] = TargetHeadsSerializer(heads, many=True).data
            for data in queryset:
                assignee = TaskUserSerializer(get_user_model().objects.get(id=data['assignee'])).data
                dept = assignee["details"]["department"] if assignee["details"][
                    "department"] else "No Department Assigned"
                priority = data["priority__value"]
                priorities.append(priority) if priority not in priorities else None
                if dept in result and priority in result[dept]:
                    result[dept][priority] += data["count"] if data["count"] else 0
                if dept in result and priority not in result[dept]:
                    result[dept][priority] = data["count"] if data["count"] else 0
                else:
                    result[dept] = {}
                    result[dept][priority] = data["count"] if data["count"] else 0
            result["priorities"] = priorities
            if mail_to:
                for item in result.keys():
                    priority_data = result[item]
                    item_data = {
                        "Department": item
                    }
                    for priority in priorities:
                        item_data[priority] = 0
                    for priority in priority_data.keys():
                        item_data[priority] = priority_data[priority]
                    ready_data.append(item_data)
                subject = "Current Department Wise Report"
                body = "As Requested on ERP System, Please find the report in the attachment. <br><br> Thanks & Regards," \
                       + "<br/><b>" + practice_name + "</b>"
                error, msg = dict_to_mail(ready_data, "Department_Task_Report", mail_to, subject, body)
                result = {"detail": msg, "error": error}
            if "error" in result and result["error"]:
                return response.BadRequest(result)
            return response.Ok(result)
        else:
            return response.BadRequest({"detail": "Invalid data sent"})


class HrSettingsViewSet(ModelViewSet):
    serializer_class = HrSettingsSerializer
    queryset = HrSettings.objects.all()
    permission_classes = (HrSettingsPermissions,)
    parser_classes = (JSONParser, MultiPartParser)

    def get_queryset(self):
        queryset = super(HrSettingsViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True, parent=None)
        name = self.request.query_params.get('name', None)
        value = self.request.query_params.get('value', None)
        name_contains = self.request.query_params.get('name_contains', None)
        value_contains = self.request.query_params.get('value_contains', None)
        if name:
            queryset = queryset.filter(name=name)
        if value:
            queryset = queryset.filter(value=value)
        if name_contains:
            queryset = queryset.filter(name__icontains=name_contains)
        if value_contains:
            queryset = queryset.filter(value__icontains=value_contains)
        return queryset

    @action(methods=['GET'], detail=False)
    def dropdown(self, request):
        dropdown_list = HR_SETTINGS
        return response.Ok(dropdown_list)
