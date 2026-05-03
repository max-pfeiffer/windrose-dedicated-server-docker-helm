# Windrose Helm Chart
A [Helm chart](https://helm.sh/) for running a Windrose dedicated server. It supports running multiple
server instances using one StatefulSet. 

This Helm chart is running the server with `USE_DIRECT_CONNECTION=true` and refrains from using ICE protocol to
establish P2P connection. Doing so would result in dynamic ports being used by the server for exposing connections.
This is not compatible with Kubernetes networking and also a security hazard.

## Installation
If you want to run Windrose on a bare metal Kubernetes cluster, I recommend reading
[my blog post](https://max-pfeiffer.github.io/hosting-game-servers-on-bare-metal-kubernetes-with-cilium-as-cni.html)
about that topic.

### Helm
You can run multiple server instance with each Helm installation. Please be aware that with a StatefulSet Kubernetes
starts additional instances only after the first instance is in ready state. And Windrose server startup is slow,
so it might take a while until your Windrose server fleet is up and running completely.
It might better suit your needs to install multiple StatefulSets with separate Helm releases.

The installation is done as follows:
```shell
$ helm repo add windrose https://max-pfeiffer.github.io/windrose-dedicated-server-docker-helm
$ helm install windrose windrose/windrose --values your_values.yaml --namespace yournamespace 
```

### Argo CD
I recommend deploying and running the Windrose dedicated server with [Argo CD](https://argoproj.github.io/cd/). This way
you have a declarative installation of your server. It's very easy to manage and update it that way.
A big plus is also the [Argo CD Image Updater](https://github.com/argoproj-labs/argocd-image-updater). This tool can
monitor the [Windrose Docker Image](https://hub.docker.com/r/pfeiffermax/windrose-dedicated-server) and will update your
Windrose installation automatically when a new image is released.

## Configuration options
### Security Context
As the `pfeiffermax/windrose-dedicated-server` image runs the Rust server with an unprivileged user since V2.0.0,
secure default values for `podSecurityContext` and `securityContext` were added.
```yaml
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```
If that doesn't suit your needs, just override these defaults.

### Resources
Make sure to get the resource specs right. You will need at least two CPU cores and 8GB of RAM.
[Using 2 cores and 12GB of RAM is recommended for 4 players](https://playwindrose.com/dedicated-server-guide/):
```yaml
resources:
  limits:
    cpu: 3
    memory: 14Gi
  requests:
    cpu: 2
    memory: 12Gi
```
Especially RAM is quite critical as Kubernetes is evicting/kills the Pod when it overshoots that resource limit. So
you want to check your monitoring and adjust `resource.limits.memory` when you see that happening. It's generally a
good idea to set the limit a bit higher than what you think the Windrose server will request.

### Startup Probe
Windrose server startup is rather slow. This is mainly due to generating the world. So you might need to raise the
`failureThreshold` when you see the startup probe failing. Multiply `periodSeconds` with `failureThreshold` to get
the maximum time for startup. These settings did work for me:
```yaml
startupProbe:
  periodSeconds: 10
  failureThreshold: 100
```

### Windrose server config
Tweak the Windrose server config to your liking. You can add a list of server to `instances`. Please be aware that the
configuration of resources and ports are shared by these instances.
```yaml
# You can choose to run multiple instances of Windrose dedicated servers here.
# For a new instance add another entry to this list.
instances:
    # Name of your server. Helpful if invite codes look similar
  - name: "WindroseServer"
    # Server password
    password: "supersecret"
    # Invite code to find your server. 0-9, a-z and A-Z symbols are allowed. Should contain at least 6 symbols.
    # Case sensitive.
    inviteCode: ""
    # Maximum number of simultaneous players on your server.
    maxPlayerCount: "5"
    # Specifies the region for the Connection Service. Supported options: SEA, CIS, EU (EU covers both EU & NA).
    # If left empty, the server will automatically detect and select the optimal region based on latency. If desired
    # region is specified (for example, EU), the server will use that region exclusively.
    userSelectedRegion: ""
    # Service configuration for this instance
    service:
      type: LoadBalancer
      externalTrafficPolicy: Cluster
      metadata:
        labels: {}
        annotations: {}
```