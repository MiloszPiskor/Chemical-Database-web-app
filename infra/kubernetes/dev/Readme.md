# Local Kubernetes Cluster Setup (Development Environment)

This is the instruction file for a **fully local kubernetes cluster** setup.
This setup primarily serves a role of a development/ testing local environment
where one can test or experiment with the cluster without the need for a cloud service, 
which may be costly ,and its setup more complex. Please follow these steps in order to set up the local cluster.

Step 1.
Kubernetes needs a local container registry to pull images for deployment. If a local registry is not already running, 
start one with:
```sh
docker run -d -p 5001:5000 --name registry registry:2
```

Step 2.
Build a Docker image for the Python Flask Backend API (remember to run this command from 
a project's root directory, or wherever the Dockerfile is located) and tag it along with 
pushing it to the local repository:
```sh
docker build -t chemical-db:latest .
docker tag chemical-db:latest localhost:5001/chemical-db:latest
docker push localhost:5001/chemical-db:latest
```

Step 3.
Build a Docker image for the React- Vite Frontend served by Nginx (remember to run this command from 
a project's root directory, or wherever the Dockerfile is located) and tag it along with 
pushing it to the local repository:
```sh
docker build -t react-frontend:latest .
docker tag react-frontend:latest localhost:5001/react-frontend:latest
docker push localhost:5001/react-frontend:latest
```

Step 4. 
Apply the Kubernetes configuration files to make sure the whole application is comprehensively
served through the local Node. However, while executing the following commands, make sure
to navigate to the /infra/kubernetes/dev directory. The following K8 manifests need to be applied (in the correct order):
```sh
kubectl apply -f database-secret.yaml
kubectl apply -f pv.yaml
kubectl apply -f pvc.yaml
kubectl apply -f postgres-configmap.yaml
kubectl apply -f database.yaml
kubectl apply -f backend-api.yaml
kubectl apply -f frontend.yaml
```

Quick comment regarding the above configuration choices: 
- Due to the fact that this is a local development environment ->  there are no cloud resources (managed database, 
LoadBalancer etc.)
- The traffic is handled within the local cluster -> no Load Balancer/Reverse Proxy
- For simplicity reasons there is a single database replica -> no Postgres sidecars or read replicas configured
- Regarding the persistent storage -> there is a persistent volume defined for which the persistent volume claim 
is directly applied in the Postgresql Stateful Set. I haven't used volumeClaimTemplates in this setup to keep it lightweight
- The Database credentials -> safely stored in the Kubernetes Secrets

To access the backend API and make HTTP calls: 
- There is no need for port forwarding hence the service configured for the backend-api Deployment is 
running a NodePort, which effectively forwards the traffic to the exposed port directly on the host.
- There is also a very good web UI for Kubernetes management called Kubernetes Dashboard, however it requires several
steps for deployment, like creating a User and logging in with a Bearer Token. Very good documentation on how to achieve
this is available under this link: https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/

Happy Coding!!!
 
