import json
import datetime
from pprint import pprint

from redis import StrictRedis



class MonitoringStatus:
    def __init__(self, apiclient):
        """
        Host representing monitoring status

        :param storage: Redis storage used for retrieving data
        """

        self.apiclient = apiclient

    def problem_hosts(self, acknowledged=None):
        api = self.apiclient
        filters = 'host.state!=ServiceOK'
        retv = {}
        for obj in api.objects.list('Host', filters=filters):
            if acknowledged is not None:
                if int(obj['attrs']['acknowledgement']) != int(acknowledged):
                    continue
            n = obj['attrs']['__name']
            retv[n] = Host(obj)

        for k,v in sorted(retv.items()):
            yield v


    @property
    def problem_services(self, acknowledged=None):
        api = self.apiclient
        filters = 'service.state!=ServiceOK'
        retv = {}
        for obj in api.objects.list('Service', filters=filters):
            if acknowledged is not None:
                if int(obj['attrs']['acknowledgement']) != int(acknowledged):
                    continue
            n = obj['attrs']['__name']
            retv[n] = Service(obj)
        for k,v in sorted(retv.items()):
            yield v


class Status:
    "One Status object"

    def __init__(self, data_dict=None):
        self._data = data_dict

    @property
    def host_name(self):
        return self._data['attrs']['host_name']

    @property
    def check_result(self):
        return self._data['attrs']['last_check_result']

    @property
    def check_attempts(self):
        return int(self._data['attrs']['check_attempt'])

    @property
    def max_check_attempts(self):
        return int(self._data['attrs']['max_check_attempts'])

    @property
    def duration(self):
        ts = float(self._data['attrs']['last_state_change'])
        event_time = datetime.datetime.fromtimestamp(ts)
        duration = datetime.datetime.now() - event_time
        return duration


class Host(Status):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self._data['type'] == 'Host', self._data
#        pprint(self._data)

    @property
    def host_name(self):
        return self._data['attrs']['name']

    @property
    def host_address(self):
        return self._data['attrs']['address']


class Service(Status):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self._data['type'] == 'Service', self._data
#        pprint(self._data)


    @property
    def service_name(self):
        return self._data['attrs']['name']
