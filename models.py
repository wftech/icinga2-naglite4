import json
import datetime
from collections import OrderedDict, Counter
from pprint import pprint


class MonitoringStatus:
    def __init__(self, apiclient):
        """
        This objects represents current status of monitoring system.

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
        attrs = ['state', 'downtime_depth', 'acknowledgement',
                 'last_reachable', 'last_state_type', 'last_state_change',
                 'last_check_result',
                 'check_attempt', 'max_check_attempts',
                 'address', 'name', '__name']
        for obj in self.apiclient.objects.list('Host', attrs=attrs):
            k = obj['attrs']['__name']
            hosts[k] = Host(obj)
            if obj['attrs']['state'] == 0:
                host_counts['ok'] += 1
            elif obj['attrs']['downtime_depth']:
                host_counts['downtime'] += 1
            elif obj['attrs']['acknowledgement']:
                host_counts['acknowledged'] += 1
            elif not obj['attrs']['last_reachable']:
                host_counts['unreachable'] += 1
            elif obj['attrs']['last_state_type'] != 0:
                host_counts['down'] += 1

        self._hosts_cache = OrderedDict(sorted(hosts.items()))

        return self._hosts_cache

    def host_count(self, status):
        if self._hosts_cache is None:
            self._hosts()
        if not self._host_counts[status]:
            return None
        return self._host_counts[status]

    def _services(self):
        # TODO: this should probably use some thread lock and/or cache.
        if self._services_cache is not None:
            return self._services_cache

        services = {}
        valid_services = self.apiclient.objects.list(
            'Service', filters='service.state==ServiceOK',
            attrs=['name'])
        services_counts = self._service_counts
        services_counts['ok'] = len(valid_services)

        attrs = ['state', 'downtime_depth', 'acknowledgement',
                 'last_reachable', 'last_state_type', 'last_state_change',
                 'last_check_result',
                 'check_attempt', 'max_check_attempts',
                 'name', 'host_name', '__name']
        for obj in self.apiclient.objects.list(
                'Service',
                filters='service.state!=ServiceOK',
                attrs=attrs):
            k = obj['attrs']['__name']
            services[k] = Service(obj)

            if obj['attrs']['downtime_depth']:
                services_counts['downtime'] += 1
            elif obj['attrs']['acknowledgement']:
                services_counts['acknowledged'] += 1
            elif not obj['attrs']['last_reachable']:
                services_counts['unreachable'] += 1
            elif obj['attrs']['last_state_type'] != 0:
                services_counts['critical'] += 1

        self._services_cache = OrderedDict(sorted(services.items()))
        return self._services_cache


    def service_count(self, status):
        if self._services_cache is None:
            self._services()
        if not self._service_counts[status]:
            return None
        return self._service_counts[status]

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
        return self['host_name']

    @property
    def check_result(self):
        return self['last_check_result']

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
        ts = float(self['last_state_change'])
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
