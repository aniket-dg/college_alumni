from django import forms

from users.models import CollegeName


class CollegeForm(forms.ModelForm):
    class Meta:
        model = CollegeName
        fields = ['about_us', 'profile_img', 'phone_number', 'website']