# kube-control interface

This interface provides communication between master and workers in a
Kubernetes cluster.


## Provides (kubernetes-master side)


### States

* `kube-control.connected`

  Enabled when a worker has joined the relation.

* `kube-control.gpu.available`

  Enabled when any worker has indicated that it is running in gpu mode.


### Methods

* `kube_control.set_dns(port, domain, sdn_ip)`

  Sends DNS info to the connected worker(s).


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

```

## Requires (kubernetes-worker side)


### States

* `kube-control.connected`

  Enabled when a master has joined the relation.

* `kube-control.dns.available`

  Enabled when DNS info is available from the master.


### Methods

* `kube_control.get_dns()`

  Returns a dictionary of DNS info sent by the master. The keys in the
  dict are: domain, private-address, sdn-ip, port.

* `kube_control.set_gpu(enabled=True)`

  Tell the master that we are gpu-enabled.


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

```
