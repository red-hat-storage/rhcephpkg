# Parts of this file are from the python-jenkins project.

# The purpose of this custom module is to provide methods that are not yet in
# python-jenkins upstream: https://launchpad.net/bugs/1724932
# This allows the "rhcephpkg build" command to log detailed information about
# the Jenkins builds it initiates.


# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import

import json
import six
import socket
from jenkins import Jenkins
from jenkins import JenkinsException
from jenkins import EmptyResponseException, NotFoundException, TimeoutException
from six.moves.urllib.error import HTTPError
from six.moves.urllib.error import URLError
from six.moves.urllib.request import Request, urlopen

Q_ITEM = 'queue/item/%(number)d/api/json'


class RhcephpkgJenkins(Jenkins):
    """ Custom behavior for python-jenkins.

    * Add new .jenkins_urlopen() method.
    * Modify .jenkins_open() method to use .jenkins_urlopen().
    * Modify .build_job() method to return a queue ID number.
      (and ensure https://bugs.launchpad.net/bugs/1177831 is resolved.)
    * Add new .get_queue_item() method.
    """

    def jenkins_urlopen(self, req, add_crumb=True):
        '''Utility routine for opening an HTTP request to a Jenkins server.

        This should only be used to extends the :class:`Jenkins` API.

        :param req: A ``six.moves.urllib.request.Request`` to submit.
        :param add_crumb: If True, try to add a crumb header to this ``req``
                          before submitting. Defaults to ``True``.
        :returns: A file-like object from urlopen()
        '''
        try:
            if self.auth:
                req.add_header('Authorization', self.auth)
            if add_crumb:
                self.maybe_add_crumb(req)
            response = urlopen(req, timeout=self.timeout)
            if response is None:
                raise EmptyResponseException(
                    "Error communicating with server[%s]: "
                    "empty response" % self.server)
            return response
        except HTTPError as e:
            # Jenkins's funky authentication means its nigh impossible to
            # distinguish errors.
            if e.code in [401, 403, 500]:
                # six.moves.urllib.error.HTTPError provides a 'reason'
                # attribute for all python version except for ver 2.6
                # Falling back to HTTPError.msg since it contains the
                # same info as reason
                raise JenkinsException(
                    'Error in request. ' +
                    'Possibly authentication failed [%s]: %s' % (
                        e.code, e.msg)
                )
            elif e.code == 404:
                raise NotFoundException('Requested item could not be found')
            else:
                raise
        except socket.timeout as e:
            raise TimeoutException('Error in request: %s' % (e))
        except URLError as e:
            # python 2.6 compatibility to ensure same exception raised
            # since URLError wraps a socket timeout on python 2.6.
            if str(e.reason) == "timed out":
                raise TimeoutException('Error in request: %s' % (e.reason))
            raise JenkinsException('Error in request: %s' % (e.reason))

    def jenkins_open(self, req, add_crumb=True):
        '''Return the HTTP response body from an HTTP ``Request``.

        This should only be used to extends the :class:`Jenkins` API.
        '''
        response = self.jenkins_urlopen(req, add_crumb)
        content = response.read()
        if content is None:
            raise EmptyResponseException(
                "Error communicating with server[%s]: "
                "empty response" % self.server)
        return content.decode('utf-8')

    def get_queue_item(self, number):
        '''Get information about a queued item (to-be-created job).

        The returned dict will have a "why" key if the queued item is still
        waiting for an executor.

        The returned dict will have an "executable" key if the queued item is
        running on an executor, or has completed running. Use this to
        determine the job number / URL.

        :param name: queue number, ``int``
        :returns: dictionary of queued information, ``dict``
        '''
        try:
            url = self._build_url(Q_ITEM, locals())
            response = self.jenkins_open(Request(url))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('queue number[%d] does not exist'
                                       % number)
        except HTTPError:
            raise JenkinsException('queue number[%d] does not exist' % number)
        except ValueError:
            raise JenkinsException(
                'Could not parse JSON info for queue number[%d]' % number
            )

    def build_job(self, name, parameters=None, token=None):
        '''Trigger build job.

        This method returns a queue item number that you can pass to
        :meth:`Jenkins.get_queue_item`. Note that this queue number is only
        valid for about five minutes after the job completes, so you should
        get/poll the queue information as soon as possible to determine the
        job's URL.

        :param name: name of job
        :param parameters: parameters for job, or ``None``, ``dict``
        :param token: Jenkins API token
        :returns: ``int`` queue item
        '''
        response = self.jenkins_urlopen(Request(
            self.build_job_url(name, parameters, token), b''))
        if six.PY2:
            location = response.info().getheader('location')
        if six.PY3:
            location = response.getheader('location')
        # location is a queue item, eg. "http://jenkins/queue/item/25/"
        if location.endswith('/'):
            location = location[:-1]
        parts = location.split('/')
        number = int(parts[-1])
        return number
