from users.models import UserEducation


def get_college_user(request):
    college = request.user.get_college_obj()
    college_user = UserEducation.objects.filter(college=college)
    users = []
    for item in college_user:
        user = item.user
        if user.is_active and user.is_verified and user.user_type == 'student' and user.is_declined == False:
            users.append(user)
    return users


def is_college_student(request, user):
    college = request.user.get_college_obj()
    college_user = UserEducation.objects.filter(college=college, user=user).last()
    if college_user:
        return True
    return False
