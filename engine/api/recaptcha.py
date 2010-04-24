from django.conf import settings

def get_captcha_html(api_server):
    return """
<script type="text/javascript">
    var RecaptchaOptions={theme:'white', lang:'en', tabindex:'0', custom_theme_widget:'null'};
</script>
<script type="text/javascript" src="%(ApiServer)s/challenge?k=%(PublicKey)s"></script>

<noscript>
  <div><object data="%(ApiServer)s/noscript?k=%(PublicKey)s" type="text/html" height="300px" width="100%%"></object></div>
  <p><textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea></p>
  <p><input type='hidden' name='recaptcha_response_field' value='manual_challenge' /></p>
</noscript>
""" % {
        'ApiServer' : api_server,
        'PublicKey' : settings.RECAPTCHA_PUB_KEY
        }

