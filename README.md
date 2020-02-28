# panel app examples

To run this panel app using Red Hat's OpenShift platform, in the DeploymentConfig, define the command to be:
panel serve your_app.py --address 0.0.0.0 --allow-websocket-origin=[your_openshift_cluster_route.com]
