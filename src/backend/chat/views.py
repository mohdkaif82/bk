from django.shortcuts import render, redirect

from django.http import HttpResponse, JsonResponse
from .models import Room, ActiveUser, TextMessage
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.contrib.auth import logout


def index(request):
    print("_" * 1000)
    if request.user.is_authenticated:
        print("auth")
        try:
            context = {}
            r = Room.objects.filter(id=1).first()
            print("r")
            active_user_obj = (
                ActiveUser.objects.all().select_related("room").get(room__id=r.id)
            )
            print("active_user_obj", active_user_obj)
            all_active_user_in_room = active_user_obj.get_queryset_of_active_user()
            print("all_active_user_in_room", all_active_user_in_room)
            context["users"] = []
            for user in all_active_user_in_room:
                try:
                    t = (
                        TextMessage.objects.filter(
                            sender_id=user["id"], receiver=request.user
                        )
                        .select_related("room")
                        .filter(room__id=r.id)
                        .order_by("-datetime")
                        .first()
                    )
                    d = {"text": t.text, "time": (t.datetime)}
                    context["users"].append({**user, **d})

                except Exception as e:
                    print("exception in TextMessage block")
            print("usewr yaha h", context["users"])
            # context['active_users_count'] = active_user_obj.get_count_of_active_user()
            context["room"] = r.name
            context["user_id"] = request.user.id
            print(request.user.id, "pppppppppppppppppppppppppppppppppppppppppp")
            context["user_name"] = request.user.email
            # active_user_inside_room = Room.objects.prefetch_related('room_set').get(room__id=r.id)
            # print(active_user_inside_room)

            return render(request, "chat/index.html", context=context)
        except ObjectDoesNotExist as e:
            print("not found")
    return HttpResponse("user is not login or unauthorized")


def get_messages(request, sender_id):
    receiver = request.user
    r = Room.objects.filter(id=1).first()
    all_texts = (
        TextMessage.objects.filter(
            sender_id__in=[sender_id, receiver.id],
            receiver_id__in=[receiver.id, sender_id],
        )
        .select_related("room")
        .filter(room__id=r.id)
        .select_related("sender")
        .order_by("datetime")
    )

    temp = []
    for text in all_texts:
        temp.append(
            {
                "msg": text.text,
                "datetime": text.datetime.strftime("%d/%m/%Y, %H:%M:%S"),
                "sender": text.sender.username,
                "receiver": text.receiver.username,
                "sender_id": text.sender_id,
            }
        )
    print(temp)
    return JsonResponse(list(temp), safe=False)


def logout_view(request, user_id):
    try:
        # active_users = ActiveUser.objects.get(room_id=1)
        # active_users.user.remove(User.objects.get(id=user_id))
        print("logging out")
        logout(request)
    except:
        print("user not found in room")
    return render(request, "chat/index.html")
