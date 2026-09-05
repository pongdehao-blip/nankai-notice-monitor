import json
import time
from urllib.parse import urlsplit
import requests
from ..models import WatchError


class FeishuClient:
    def __init__(self,webhook,session=None,sleep=time.sleep):
        u=urlsplit(webhook or '')
        if u.scheme!='https' or u.hostname!='open.feishu.cn' or u.username or u.port or u.query or u.fragment or not u.path.startswith('/open-apis/bot/v2/hook/') or not u.path.rsplit('/',1)[-1]:
            raise WatchError('DELIVERY_ERROR','FEISHU_WEBHOOK missing or invalid; configure repository secret')
        self._webhook=webhook
        self.session=session or requests.Session()
        self.session.trust_env=False
        self.sleep=sleep

    def send(self,payloads):
        for index,message in enumerate(payloads):
            if index:
                self.sleep(1.1)
            try:
                self.session.cookies.clear()
                # Send actual UTF-8 bytes matching the builder's byte-size validation.
                response=self.session.post(self._webhook,data=json.dumps(message,ensure_ascii=False,separators=(',',':')).encode('utf-8'),headers={'Content-Type':'application/json; charset=utf-8'},timeout=(15,15),allow_redirects=False)
                with response:
                    if response.status_code!=200:
                        raise WatchError('DELIVERY_ERROR','Feishu HTTP delivery failed')
                    body=response.json()
                    if not isinstance(body,dict):
                        raise ValueError()
                    codes=[body[k] for k in ('code','StatusCode') if k in body]
                    if not codes or any(type(code) is not int or code!=0 for code in codes):
                        raise WatchError('DELIVERY_ERROR','Feishu rejected report')
            except WatchError:
                raise
            except (requests.RequestException,ValueError):
                # Never include exception URLs, response text or webhook in logs.
                raise WatchError('DELIVERY_ERROR','Feishu delivery failed or acknowledgement is invalid') from None

    def close(self):
        self.session.close()
