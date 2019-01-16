import datetime
from collections import OrderedDict, Counter

from helpers import State, StatePriority


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
                 'last_reachable', 'state_type', 'last_state_change',
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
            elif obj['attrs']['state_type'] != 0:
                host_counts['down'] += 1

            if int(obj['attrs']['state']) != State.OK.value \
                    and not obj['attrs']['acknowledgement'] \
                    and not obj['attrs']['downtime_depth']:
                host_counts['unhandled'] += 1

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

        nested_services = {}
        valid_services = self.apiclient.objects.list(
            'Service', filters='service.state==ServiceOK',
            attrs=['name'])
        services_counts = self._service_counts
        services_counts['ok'] = len(valid_services)

        attrs = ['state', 'downtime_depth', 'acknowledgement',
                 'last_reachable', 'state_type', 'last_state_change',
                 'last_check_result',
                 'check_attempt', 'max_check_attempts',
                 'name', 'host_name', '__name']
        for obj in self.apiclient.objects.list(
                'Service',
                filters='service.state!=ServiceOK',
                attrs=attrs):
            service = Service(obj)
            host = service.host_name
            if host not in nested_services.keys():
                nested_services[host] = dict(items=[],
                                             state_priority=StatePriority.OK.value)
            nested_services[host]['items'].append(service)
            nested_services[host]['state_priority'] = min(
                nested_services[host]['state_priority'],
                service.state_priority)

            if obj['attrs']['downtime_depth']:
                services_counts['downtime'] += 1
            elif obj['attrs']['acknowledgement']:
                services_counts['acknowledged'] += 1
            elif not obj['attrs']['last_reachable']:
                services_counts['unreachable'] += 1
            elif obj['attrs']['state'] == State.WARNING.value:
                services_counts['warning'] += 1
            elif obj['attrs']['state'] == State.CRITICAL.value:
                services_counts['critical'] += 1
            elif obj['attrs']['state'] == State.UNKNOWN.value:
                services_counts['unknown'] += 1

            if int(obj['attrs']['state']) != State.OK.value \
                    and not obj['attrs']['acknowledgement'] \
                    and not obj['attrs']['downtime_depth']:
                services_counts['unhandled'] += 1

        nested_services = OrderedDict(
            sorted(nested_services.items(),
                   key=lambda item: item[1]['state_priority']))

        services = {}
        for _, host_services in nested_services.items():
            for s in sorted(host_services['items'],
                            key=lambda item: item.state_priority):
                services[s.service_key] = s

        self._services_cache = OrderedDict(services.items())
        return self._services_cache

    def service_count(self, status):
        if self._services_cache is None:
            self._services()
        if not self._service_counts[status]:
            return None
        return self._service_counts[status]

    def all_hosts(self):
        return self._hosts().values()

    def problem_hosts(self, acknowledged=None, unhandled=None, downtime=None):
        for obj in self._hosts().values():
            if int(obj['state']) == State.OK.value:
                continue
            if acknowledged is not None:
                if int(obj['acknowledgement']) != int(acknowledged):
                    continue
            if unhandled:
                if int(obj['acknowledgement']):
                    continue
                if int(obj['downtime_depth']):
                    continue
            if downtime:
                if int(obj['downtime_depth']) == 0:
                    continue
            yield obj

    def problem_services(self, acknowledged=None, unhandled=None, downtime=None):
        for obj in self._services().values():
            if int(obj['state']) == State.OK.value:
                continue
            if acknowledged is not None:
                if int(obj['acknowledgement']) != int(acknowledged):
                    continue
            if unhandled:
                if int(obj['acknowledgement']):
                    continue
                if int(obj['downtime_depth']):
                    continue
            if downtime:
                if int(obj['downtime_depth']) == 0:
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

    # Shortcut for people which prefer singular version
    check_attempt = check_attempts


    @property
    def max_check_attempts(self):
        return int(self['max_check_attempts'])

    @property
    def is_soft_state(self):
        return self['state_type'] == 0

    @property
    def duration(self):
        ts = float(self['last_state_change'])
        event_time = datetime.datetime.fromtimestamp(ts)
        duration = datetime.datetime.now() - event_time
        return duration

    @property
    def state_priority(self):
        return getattr(StatePriority, State(int(self['state'])).name).value

    @property
    def check_output_long(self):
        "Get full check command output"
        return self._data['attrs']['last_check_result']['output']

    @property
    def check_output(self):
        "Return short check command output"
        return self._data['attrs']['last_check_result']['output'].split('\n')[0]

    def __getitem__(self, item):
        assert item != 'output'
        return self._data['attrs'][item]


class Host(Status):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self._data['type'] == 'Host', self._data

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

    @property
    def service_name(self):
        return self._data['attrs']['name']

    @property
    def service_key(self):
        return self._data['attrs']['__name']
