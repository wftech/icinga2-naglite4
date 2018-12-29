import json
import datetime
from collections import OrderedDict
from pprint import pprint

from redis import StrictRedis


class MonitoringStatus:
    def __init__(self, apiclient):
        """
        This objects Representing monitoring status.

        :param apiclient: Provide Icinga2API client
        """

        self.apiclient = apiclient
        self._hosts_cache = None

    def _hosts(self):

        # TODO: this should probably use some thread lock and/or cache.
        if self._hosts_cache is not None:
            return self._hosts_cache

        hosts = {}
        for obj in self.apiclient.objects.list('Host'):
            k = obj['attrs']['__name']
            hosts[k] = Host(obj)

        self._hosts_cache = OrderedDict(sorted(hosts.items()))
        return self._hosts_cache

    def all_hosts(self):
        return self._hosts().values()

    def problem_hosts(self, acknowledged=None):
        for obj in self._hosts().values():
            if int(obj['state']) == 0:  # OK
                continue
            if acknowledged is not None:
                if int(obj['acknowledgement']) != int(acknowledged):
                    continue
            yield obj

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
        for k, v in sorted(retv.items()):
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

    def __getitem__(self, item):
        return self._data['attrs'][item]


class Host(Status):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self._data['type'] == 'Host', self._data

    #        pprint(self._data)

    @property
    def host_name(self):
        return self['name']

    @property
    def host_address(self):
        return self['address']


class Service(Status):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self._data['type'] == 'Service', self._data

    #        pprint(self._data)

    @property
    def service_name(self):
        return self._data['attrs']['name']
