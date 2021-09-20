# coding=utf-8


class ImooseAPIException(Exception):

    def __init__(self, response):
        self.code = 0
        try:
            json_res = response.json()
        except ValueError:
            self.message = 'Invalid JSON error message from imoose: {}'.format(response.text)
        else:
            self.message = ",".join(json_res['errors'])
        self.status_code = response.status_code
        self.response = response
        self.request = getattr(response, 'request', None)

    def __str__(self):  # pragma: no cover
        return 'APIError(status=%s): %s' % (self.status_code, self.message)
