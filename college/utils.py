from users.models import UserEducation


def get_college_user(request):
    college = request.user.get_college_obj()
    college_user = UserEducation.objects.filter(college=college)#.exclude(user__is_active=True, user__is_verified=False, user__user_type='student', user__is_declined=False)
    users = []
    college_user_final = []
    for item in college_user:
        user = item.user
        if user.is_active and not user.is_verified and user.user_type == 'student' and not user.is_declined:
            users.append(user)
            college_user_final.append(item)
    return college_user_final, users

def get_college_all_users(request):
    college = request.user.get_college_obj()
    college_user = UserEducation.objects.filter(college=college).select_related('user')
    print(college_user)
    users = []
    college_users_final = []
    for item in college_user:
        user = item.user
        if user.is_active and user.user_type == 'student':
            users.append(user)
            college_users_final.append(item)
    return users


def is_college_student(request, user):
    college = request.user.get_college_obj()
    college_user = UserEducation.objects.filter(college=college, user=user).last()
    if college_user:
        return True
    return False
