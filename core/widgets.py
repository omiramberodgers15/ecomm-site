from django import forms


class VoiceRecorderWidget(forms.ClearableFileInput):
    template_name = "core/widgets/voice_recorder.html"

    class Media:
        js = ("core/js/voice_recorder.js",)