# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sets the sys path for the libraries within the folder lib."""

__author__ = 'kbrisbin@google.com (Kathryn Hurley)'

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'libraries'))

sys.path.append(os.path.join(os.path.dirname(__file__), 'application'))

# sys.path.append(os.path.join(os.path.dirname(__file__),
#                              'libraries',
#                              'google_cloud'))

sys.path.append(os.path.join(os.path.dirname(__file__),
                             'libraries',
                             'httplib2-0.8',
                             'python2'))

sys.path.append(os.path.join(os.path.dirname(__file__),
                             'libraries',
                             'google-api-python-client-1.1'))

sys.path.append(os.path.join(os.path.dirname(__file__),
                             'libraries',
                             'oauth2client-1.0'))
                            
sys.path.append(os.path.join(os.path.dirname(__file__),
                             'libraries',
                             'python-gflags-2.0'))
