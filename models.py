import json
import datetime
from collections import OrderedDict, Counter
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
        self._services_cache = None
        self._host_counts = Counter()
        self._service_counts = Counter()

    def _hosts(self):
        # TODO: this should probably use some thread lock and/or cache.
        if self._hosts_cache is not None:
            return self._hosts_cache

        host_counts = self._host_counts
        hosts = {}
        for obj in self.apiclient.objects.list('Host'):
            k = obj['attrs']['__name']
            hosts[k] = Host(obj)
            
            if obj['attrs']['state'] == 0:
                host_counts['ok'] += 1
            elif obj['attrs']['downtime_depth']:
                host_counts['downtime'] += 1
            elif not obj['attrs']['last_reachable']:
                host_counts['unreachable'] += 1
            elif obj['attrs']['last_state_type'] != 0:
                host_counts['critical'] += 1

        self._hosts_cache = OrderedDict(sorted(hosts.items()))

        return self._hosts_cache

    def host_counts(self):
        return self._host_counts

    def _services(self):
        # TODO: this should probably use some thread lock and/or cache.
        if self._services_cache is not None:
            return self._services_cache

        services = {}
        filters = 'service.state!=ServiceOK'

        for obj in self.apiclient.objects.list(
                'Service', filters='service.state!=ServiceOK'):
            k = obj['attrs']['__name']
            services[k] = Service(obj)

        self._services_cache = OrderedDict(sorted(services.items()))
        return self._services_cache

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
        for obj in self._services().values():
            if int(obj['state']) == 0:  # OK
                continue
            if acknowledged is not None:
                if int(obj['acknowledgement']) != int(acknowledged):
                    continue
            yield obj


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
        return int(self['check_attempt'])

    @property
    def max_check_attempts(self):
        return int(self['max_check_attempts'])

    @property
    def is_soft_state(self):
        return self['check_attempts'] != self['max_check_attempts']

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
