# Valheim Helm Chart
A [Helm chart](https://helm.sh/) for running a Valheim dedicated server. Since v1.0.0 this Helm chart supports running multiple
server instances using one StatefulSet. 

## Installation
If you want to run Valheim on a bare metal Kubernetes cluster, I recommend reading
[my blog post](https://max-pfeiffer.github.io/blog/hosting-game-servers-on-bare-metal-kubernetes-with-kube-vip.html)
about that topic.

### Helm
You can run multiple server instance with each Helm installation. Please be aware that with a StatefulSet Kubernetes
starts additional instances only after the first instance is in ready state. And Valheim server startup is slow,
so it might take a while until your Valheim server fleet is up and running completely.
It might better suit your needs to install multiple StatefulSets with separate Helm releases.

The installation is done as follows:
```shell
$ helm repo add valheim https://max-pfeiffer.github.io/valheim-dedicated-server-docker-helm
$ helm install valheim valheim/valheim --values your_values.yaml --namespace yournamespace 
```

### Argo CD
I recommend deploying and running the Valheim dedicated server with [Argo CD](https://argoproj.github.io/cd/). This way
you have a declarative installation of your server. It's very easy to manage and update it that way.
A big plus is also the [Argo CD Image Updater](https://github.com/argoproj-labs/argocd-image-updater). This tool can
monitor the [Valheim Docker Image](https://hub.docker.com/r/pfeiffermax/valheim-dedicated-server) and will update your
Valheim installation automatically when a new image is released.

## Configuration options
### Security Context
As the `pfeiffermax/valheim-dedicated-server` image runs the Rust server with an unprivileged user since V2.0.0,
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
Make sure to get the resource specs right. You will need at least two CPU cores and 2GB of RAM.
[Using 4GB of RAM is recommended](https://valheim.fandom.com/wiki/Dedicated_servers#Requirements):
```yaml
resources:
  limits:
    cpu: 3
    memory: 5Gi
  requests:
    cpu: 2
    memory: 4Gi
```
Especially RAM is quite critical as Kubernetes is evicting/kills the Pod when it overshoots that resource limit. So
you want to check your monitoring and adjust `resource.limits.memory` when you see that happening. It's generally a
good idea to set the limit a bit higher than what you think the Valheim server will request.

### Startup Probe
Valheim server startup is rather slow. This is mainly due to generating the world. So you might need to raise the
`failureThreshold` when you see the startup probe failing. Multiply `periodSeconds` with `failureThreshold` to get
the maximum time for startup. These settings did work for me:
```yaml
startupProbe:
  periodSeconds: 10
  failureThreshold: 100
```

### Valheim server config
Tweak the Valheim server config to your liking. You can add a list of server to `instances`. Please be aware that the
configuration of resources and ports are shared by these instances.
```yaml
# You can choose to run multiple instances of Rust dedicated servers here.
# For a new instance add another entry to this list.
instances:
    # Name of your server that will be visible in the Server list.
    # You can use just one single string without any spaces as this is specified as command line option.
  - name: "ValheimServer"
    # A World with the name entered will be created. You may also choose an already existing World by entering its name.
    world: "NewWorld"
    # Server password
    # ATTENTION: needs to be at least 5 characters long, otherwise the server startup fails!
    password: "supersecret"
    # Set the visibility of your server. 1 is default and will make the server visible in the browser.
    # Set it to 0 to make the server invisible and only joinable via the ‘Join IP’-button.
    public: "1"
    # Runs the Server on the Crossplay backend (PlayFab), which lets users from any platform join.
    # If you set it to false, the Steam backend is used, which means only Steam users can see and join the Server.
    crossPlay: false
    # How often the world will save in seconds.
    saveInterval: "1800"
    # Sets how many automatic backups will be kept. The first is the ‘short’ backup length,
    # and the rest are the ‘long’ backup length.
    # By default, that means one backup that is 2 hours old, and 3 backups that are 12 hours apart.
    backups: "4"
    # Sets the interval between the first automatic backups.
    backupShort: "7200"
    # Sets the interval between the subsequent automatic backups.
    backupLong: "43200"
    # Pod specific service
    service:
      type: LoadBalancer
      externalTrafficPolicy: Cluster
      metadata:
        annotations: {}
```