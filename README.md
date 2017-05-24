# kube-control interface

This interface provides communication between master and workers in a
Kubernetes cluster.


## Provides (kubernetes-master side)


### States

* `kube-control.connected`

  Enabled when a worker has joined the relation.

* `kube-control.gpu.available`

  Enabled when any worker has indicated that it is running in gpu mode.

* `kube-control.departed`

  Enabled when any worker has indicated that it is leaving the cluster.


* `kube-control.auth.requested`

  Enabled when an authentication credential is requested. This state is
  temporary and will be removed once the units authentication request has
  been fulfilled.

### Methods

* `kube_control.set_dns(port, domain, sdn_ip)`

  Sends DNS info to the connected worker(s).


* `kube_control.auth_user()`

  Returns the requested username and group requested for authentication.

* `kube_control.sign_auth_request(kubelet_token, proxy_token, client_token)`

  Sends authentication tokens to the requesting unit for the requested user
  and kube-proxy services.

* `kube_control.flush_departed()`

  Returns the unit departing the kube_control relationship so you can do any
  post removal cleanup. Such as removing authentication tokens for the unit.
  Invoking this method will also remove the `kube-control.departed` state

### Examples

```python

@when('kube-control.connected')
def send_dns(kube_control):
    # send port, domain, sdn_ip to the remote side
    kube_control.set_dns(53, "cluster.local", "10.1.0.10")

@when('kube-control.gpu.available')
def on_gpu_available(kube_control):
    # The remote side is gpu-enable, handle it somehow
    assert kube_control.get_gpu() == True


@when('kube-control.departed')
@when('leadership.is_leader')
def flush_auth_for_departed(kube_control):
    ''' Unit has left the cluster and needs to have its authentication
    tokens removed from the token registry '''
    departing_unit = kube_control.flush_departed()

```

## Requires (kubernetes-worker side)


### States

* `kube-control.connected`

  Enabled when a master has joined the relation.

* `kube-control.dns.available`

  Enabled when DNS info is available from the master.

* `kube-control.auth.available`

  Enabled when authentication credentials are present from the master.

### Methods

* `kube_control.get_dns()`

  Returns a dictionary of DNS info sent by the master. The keys in the
  dict are: domain, private-address, sdn-ip, port.

* `kube_control.set_gpu(enabled=True)`

  Tell the master that we are gpu-enabled.

*  `kube_control.get_auth_credentials()`

  Returns a dict with the returned authentication credentials.

*  `set_auth_request(kubelet, group='system:nodes')`

  Issue an authentication request against the master to receive token based
  auth credentials in return.

### Examples

```python

@when('kube-control.dns.available')
def on_dns_available(kube_control):
    # Remote side has sent DNS info
    dns = kube_control.get_dns()
    print(context['domain'])
    print(context['private-address'])
    print(context['sdn-ip'])
    print(context['port'])

@when('kube-control.connected')
def send_gpu(kube_control):
    # Tell the master that we're gpu-enabled
    kube_control.set_gpu(True)

@when('kube-control.auth.available')
def display_auth_tokens(kube_control):
    # Remote side has sent auth info
    auth = kube_control.get_auth_credentials()
    print(auth['kubelet_token'])
    print(auth['proxy_token'])
    print(auth['client_token'])

@when('kube-control.connected')
@when_not('kube-control.auth.available')
def request_auth_credentials(kube_control):
    # Request an admin user with sudo level access named 'root'
    kube_control.set_auth_request('root', group='system:masters')

```
