# Common Linux service image

From a lab directory such as `labs/lab12`, build the adjacent common context:

```sh
docker build -t netbook-services:20260916 ../common
docker image inspect netbook-services:20260916
docker run --rm netbook-services:20260916 cat /netbook-package-versions.txt
```

The Dockerfile uses Ubuntu 24.04 and installs the tools needed by the revised
Linux service labs. The local tag identifies this recipe; it is not a public
registry image or an immutable digest. The base tag and apt repositories can
change. Retain the resolved base/image digests, build output and package list
with each run. A later rebuild is a new validation environment.

Docker shares the host kernel: record `uname -r` as well as package versions.
Do not infer the host's namespace, bridge or timing capabilities from the
container's Ubuntu version. Inspect the relevant lab README before deploying.

Current review evidence used separately extracted Ubuntu 26.04 tools in WSL
Linux namespaces. Docker is unavailable on that review host, so the common
image build and Containerlab deployment are pending. Source checks and those
namespace measurements do not establish an image-build or vendor-NOS result.
