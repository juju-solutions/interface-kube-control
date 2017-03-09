# kube-control interface

This interface provides communication between master and workers in a
Kubernetes cluster.


# Provides (master)

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

# Requires

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
