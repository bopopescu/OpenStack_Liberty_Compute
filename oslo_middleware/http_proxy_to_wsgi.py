# -*- encoding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing permissions and
# limitations under the License.
from debtcollector import removals
from oslo_middleware import base


class HTTPProxyToWSGI(base.ConfigurableMiddleware):
    """HTTP proxy to WSGI termination middleware.

    This middleware overloads WSGI environment variables with the one provided
    by the remote HTTP reverse proxy.

    """

    @staticmethod
    def _parse_rfc7239_header(header):
        """Parses RFC7239 Forward headers.

        e.g. for=192.0.2.60;proto=http, for=192.0.2.60;by=203.0.113.43

        """
        result = []
        for proxy in header.split(","):
            entry = {}
            for d in proxy.split(";"):
                key, _, value = d.partition("=")
                entry[key.lower()] = value
            result.append(entry)
        return result

    def process_request(self, req):
        fwd_hdr = req.environ.get("HTTP_FORWARDED")
        if fwd_hdr:
            proxies = self._parse_rfc7239_header(fwd_hdr)
            # Let's use the value from the first proxy
            if proxies:
                proxy = proxies[0]

                forwarded_proto = proxy.get("proto")
                if forwarded_proto:
                    req.environ['wsgi.url_scheme'] = forwarded_proto

                forwarded_host = proxy.get("host")
                if forwarded_host:
                    req.environ['HTTP_HOST'] = forwarded_host

        else:
            # World before RFC7239
            forwarded_proto = req.environ.get("HTTP_X_FORWARDED_PROTO")
            if forwarded_proto:
                req.environ['wsgi.url_scheme'] = forwarded_proto

            forwarded_host = req.environ.get("HTTP_X_FORWARDED_HOST")
            if forwarded_host:
                req.environ['HTTP_HOST'] = forwarded_host

        v = req.environ.get("HTTP_X_FORWARDED_PREFIX")
        if v:
            req.environ['SCRIPT_NAME'] = v + req.environ['SCRIPT_NAME']


@removals.remove
class HTTPProxyToWSGIMiddleware(HTTPProxyToWSGI):
    """Placeholder for backward compatibility"""