from django import forms
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML

class VideoSearchForm(forms.Form):
    youtube_url = forms.URLField(label='', max_length=200)

    def __init__(self, *args, **kwargs):
        super(VideoSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FieldWithButtons('youtube_url', Submit('search', 'SEARCH')),
            HTML("""
            <p>Accepts youtube.com, youtu.be, and embedded html links.</p>
            """),
        )