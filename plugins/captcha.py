from twocaptcha import TwoCaptcha
import os

class CaptchaSolver:
    def __init__(self):
        self.solver = TwoCaptcha(os.getenv('CAPTCHA_API_KEY'))

    async def solve_recaptcha(self, sitekey, url):
        result = self.solver.recaptcha(sitekey, url)
        return result['code']
